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
from PyQt4.QtCore import QDate, pyqtSignature, QModelIndex, QString

from library.Utils       import forceInt, forceString, forceDouble, forceRef, forceStringEx, formatNameInt
from Events.Utils       import CFinanceType, getActionTypeDescendants
from Reports.Report     import CReport
from Reports.ReportView import CPageFormat
from Reports.ReportBase import CReportBase, createTable
from Reports.Utils      import dateRangeAsStr

from Reports.ActionStatusListDialog import CActionStatusListDialog
from Events.ActionStatus             import CActionStatus

from Reports.Ui_ReportUETActions import Ui_ReportUETActions


def selectData(params, byPersons=False):
    begDate = params.get('begDate', QDate())
    endDate = params.get('endDate', QDate())
    orgStructureId        = params.get('orgStructureId', None)
    financeId             = params.get('financeId', None)
    medicalAidKindId      = params.get('medicalAidKindId', None)
    detailByOrgStructures = params.get('detailByOrgStructures', 0)
    detailByFinance        = params.get('detailByFinance', 0)
    detailByMedicalAidKind = params.get('detailByMedicalAidKind', 0)
    actionStatusList       = params.get('actionStatusList', [])
    personParam            = params.get('personParam', 0)
    postParam              = params.get('postParam', 0)
    chkActionTypeClass     = params.get('chkActionTypeClass', False)
    actionTypeClass        = params.get('actionTypeClass', None)
    actionTypeId           = params.get('actionTypeId', None)

    db = QtGui.qApp.db
    tableAction        = db.table('Action')
    tableActionType    = db.table('ActionType')
    tableEvent        = db.table('Event')
    tableClient = db.table('Client')
    tablePerson = db.table('Person')
    tableAPerson = db.table('Person').alias('APerson')
    tableRBPost = db.table('rbPost')
    tableAssistantPost = db.table('rbPost').alias('AssistantPost')
    tableRBSpeciality = db.table('rbSpeciality')
    tableRBFinance = db.table('rbFinance')
    tableContractAction = db.table('Contract').alias('ContractAction')
    tableRBFinanceContract = db.table('rbFinance').alias('rbFinanceContract')
    tableContract = db.table('Contract')
    tableRBEventFinance = db.table('rbFinance').alias('rbEventFinance')
    tableOrgStructure = db.table('OrgStructure')
    tableEventType = db.table('EventType')
    tableRBMedicalAidKind = db.table('rbMedicalAidType')
    tableActionTypeUET = db.table('ActionType_UETActionSpecification')

    cond = [tableAction['deleted'].eq(0),
            tableActionType['deleted'].eq(0)
            ]

    cols = [tableActionType['code'],
            tableOrgStructure['name'].alias('orgStructureName'),
            tableActionType['name'].alias('actionTypeName'),
            tableActionType['code'].alias('actionTypeCode'),
            tableRBMedicalAidKind['name'].alias('medicalAidKindName'),
            u'''IF(rbFinance.name IS NOT NULL, rbFinance.name, (IF(rbFinanceContract.name IS NOT NULL, rbFinanceContract.name, rbEventFinance.name))) AS financeName''',
            tableAction['actionSpecification_id'].alias('actionSpecification'),
            tableActionType['id'].alias('actionTypeId'),
            u'''SUM(IF(Action.amount = 0, 1, Action.amount)) AS amount''',
            u'''SUM((IF(AGE(Client.birthDate, Action.begDate) >= 18,
                ActionType.adultUetDoctor,
                ActionType.childUetDoctor))*(IF(Action.amount = 0, 1, Action.amount))) AS uetDoctor''',
            u'''SUM((IF(AGE(Client.birthDate, Action.begDate) >= 18,
                ActionType.adultUetAverageMedWorker,
                ActionType.childUetAverageMedWorker))*(IF(Action.amount = 0, 1, Action.amount))) AS uetAverageMedWorker''',
            u'''SUM((IF(AGE(Client.birthDate, Action.begDate) >= 18,
                ActionType.assistantAdultUetDoctor,
                ActionType.assistantChildUetDoctor))*(IF(Action.amount = 0, 1, Action.amount))) AS uetAssistantDoctor''',
            u'''SUM((IF(AGE(Client.birthDate, Action.begDate) >= 18,
                ActionType.assistantAdultUetAverageMedWorker,
                ActionType.assistantChildUetAverageMedWorker))*(IF(Action.amount = 0, 1, Action.amount))) AS uetAssistantAverageMedWorker''',
            u'''SUM((IF(AGE(Client.birthDate, Action.begDate) >= 18,
                (SELECT
                        ActionType_UETActionSpecification.adultUetDoctor
                    FROM
                        ActionType_UETActionSpecification
                    WHERE
                        ActionType_UETActionSpecification.master_id = ActionType.id
                            AND ActionType_UETActionSpecification.actionSpecification_id = Action.actionSpecification_id
                            AND ActionType_UETActionSpecification.isAssistant = 0
                    LIMIT 1),
                (SELECT
                        ActionType_UETActionSpecification.childUetDoctor
                    FROM
                        ActionType_UETActionSpecification
                    WHERE
                        ActionType_UETActionSpecification.master_id = ActionType.id
                            AND ActionType_UETActionSpecification.actionSpecification_id = Action.actionSpecification_id
                            AND ActionType_UETActionSpecification.isAssistant = 0
                    LIMIT 1)))*(IF(Action.amount = 0, 1, Action.amount))) AS specificationUetDoctor''',
            u'''SUM((IF(AGE(Client.birthDate, Action.begDate) >= 18,
                (SELECT
                        ActionType_UETActionSpecification.adultUetAverageMedWorker
                    FROM
                        ActionType_UETActionSpecification
                    WHERE
                        ActionType_UETActionSpecification.master_id = ActionType.id
                            AND ActionType_UETActionSpecification.actionSpecification_id = Action.actionSpecification_id
                            AND ActionType_UETActionSpecification.isAssistant = 0
                    LIMIT 1),
                (SELECT
                        ActionType_UETActionSpecification.childUetAverageMedWorker
                    FROM
                        ActionType_UETActionSpecification
                    WHERE
                        ActionType_UETActionSpecification.master_id = ActionType.id
                            AND ActionType_UETActionSpecification.actionSpecification_id = Action.actionSpecification_id
                            AND ActionType_UETActionSpecification.isAssistant = 0
                    LIMIT 1)))*(IF(Action.amount = 0, 1, Action.amount))) AS specificationUetAverageMedWorker''',
            u'''SUM((IF(AGE(Client.birthDate, Action.begDate) >= 18,
                (SELECT
                        ActionType_UETActionSpecification.adultUetDoctor
                    FROM
                        ActionType_UETActionSpecification
                    WHERE
                        ActionType_UETActionSpecification.master_id = ActionType.id
                            AND ActionType_UETActionSpecification.actionSpecification_id = Action.actionSpecification_id
                            AND ActionType_UETActionSpecification.isAssistant = 1
                    LIMIT 1),
                (SELECT
                        ActionType_UETActionSpecification.childUetDoctor
                    FROM
                        ActionType_UETActionSpecification
                    WHERE
                        ActionType_UETActionSpecification.master_id = ActionType.id
                            AND ActionType_UETActionSpecification.actionSpecification_id = Action.actionSpecification_id
                            AND ActionType_UETActionSpecification.isAssistant = 1
                    LIMIT 1)))*(IF(Action.amount = 0, 1, Action.amount))) AS specificationUetAssistantDoctor''',
            u'''SUM((IF(AGE(Client.birthDate, Action.begDate) >= 18,
                (SELECT
                        ActionType_UETActionSpecification.adultUetAverageMedWorker
                    FROM
                        ActionType_UETActionSpecification
                    WHERE
                        ActionType_UETActionSpecification.master_id = ActionType.id
                            AND ActionType_UETActionSpecification.actionSpecification_id = Action.actionSpecification_id
                            AND ActionType_UETActionSpecification.isAssistant = 1
                    LIMIT 1),
                (SELECT
                        ActionType_UETActionSpecification.childUetAverageMedWorker
                    FROM
                        ActionType_UETActionSpecification
                    WHERE
                        ActionType_UETActionSpecification.master_id = ActionType.id
                            AND ActionType_UETActionSpecification.actionSpecification_id = Action.actionSpecification_id
                            AND ActionType_UETActionSpecification.isAssistant = 1
                    LIMIT 1)))*(IF(Action.amount = 0, 1, Action.amount))) AS specificationUetAssistantAverageMedWorker''',
            u'''IF(rbPost.id, IF(LEFT(rbPost.code, 1) <= 3, 1, 0), NULL) isDoctor''',
            u'''IF(AssistantPost.id, IF(LEFT(AssistantPost.code, 1) <= 3, 1, 0), NULL) isAssistantDoctor'''
            ]

    if begDate and endDate:
        cond.append(tableAction['begDate'].ge(begDate))
        cond.append(tableAction['begDate'].lt(endDate.addDays(1)))

    if financeId:
        cond.append(db.joinOr([tableAction['finance_id'].eq(financeId),
                               db.joinAnd([tableAction['finance_id'].isNull(), tableContractAction['finance_id'].eq(financeId)]),
                               db.joinAnd([tableAction['finance_id'].isNull(), tableContractAction['finance_id'].isNull(), tableContract['finance_id'].eq(financeId)])
                              ]))

    if medicalAidKindId:
        cond.append(tableEventType['medicalAidType_id'].eq(medicalAidKindId))

    if orgStructureId:
        orgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', orgStructureId) if orgStructureId else []
        cond.append(tablePerson['orgStructure_id'].inlist(orgStructureIdList))

    if chkActionTypeClass:
        if actionTypeClass is not None:
            cond.append(tableActionType['class'].eq(actionTypeClass))
        if actionTypeId:
            cond.append(tableActionType['id'].inlist(getActionTypeDescendants(actionTypeId, actionTypeClass)))

    if actionStatusList:
        cond.append(tableAction['status'].inlist(actionStatusList))

    queryTable = tableAction
    queryTable = queryTable.leftJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
    queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
    queryTable = queryTable.leftJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
    queryTable = queryTable.leftJoin(tableContractAction, db.joinAnd([tableContractAction['id'].eq(tableAction['contract_id']), tableContractAction['deleted'].eq(0)]))
    queryTable = queryTable.leftJoin(tableRBFinanceContract, tableRBFinanceContract['id'].eq(tableContractAction['finance_id']))
    queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
    queryTable = queryTable.leftJoin(tableRBEventFinance, tableRBEventFinance['id'].eq(tableContract['finance_id']))
    queryTable = queryTable.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
    queryTable = queryTable.leftJoin(tableRBMedicalAidKind, tableRBMedicalAidKind['id'].eq(tableEventType['medicalAidType_id']))
    queryTable = queryTable.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
    queryTable = queryTable.leftJoin(tableAPerson, tableAPerson['id'].eq(tableAction['assistant_id']))
    queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(tableAction['person_id']))
    if personParam:
        queryTable = queryTable.leftJoin(tableRBSpeciality, tableRBSpeciality['id'].eq(tableAPerson['speciality_id']))
    else:
        queryTable = queryTable.leftJoin(tableRBSpeciality, tableRBSpeciality['id'].eq(tablePerson['speciality_id']))
    queryTable = queryTable.leftJoin(tableRBPost, tableRBPost['id'].eq(tablePerson['post_id']))
    queryTable = queryTable.leftJoin(tableAssistantPost, tableAssistantPost['id'].eq(tableAPerson['post_id']))
    if personParam:
        queryTable = queryTable.leftJoin(tableOrgStructure, tableOrgStructure['id'].eq(tableAPerson['orgStructure_id']))
    else:
        queryTable = queryTable.leftJoin(tableOrgStructure, tableOrgStructure['id'].eq(tablePerson['orgStructure_id']))
    queryTable = queryTable.leftJoin(tableActionTypeUET, db.joinAnd([tableActionTypeUET['master_id'].eq(tableActionType['id']),
                                                                    tableActionTypeUET['actionSpecification_id'].eq(tableAction['actionSpecification_id'])]))

    if postParam:
        postHaving = u' AND %s = 0 '%(u'isAssistantDoctor' if personParam else u'isDoctor')
    else:
        postHaving = u' AND %s = 1 '%(u'isAssistantDoctor' if personParam else u'isDoctor')

    groupBy = u'''ActionType.id, Action.actionSpecification_id, %s'''%(u'isAssistantDoctor' if personParam else u'isDoctor')
    if detailByOrgStructures:
        groupBy += u', OrgStructure.id'
    if detailByFinance:
        groupBy += u', IF(rbFinance.id IS NOT NULL, rbFinance.id, (IF(rbFinanceContract.id IS NOT NULL, rbFinanceContract.id, rbEventFinance.id)))'
    if detailByMedicalAidKind:
        groupBy += u', rbMedicalAidType.id'
    if byPersons:
        if personParam:
            cols.append(u'''APerson.id as personId''')
            cols.append(u'''Person.id as assistantId''')
            cols.append(u'''CONCAT(APerson.lastName, ' ', APerson.firstName, ' ', APerson.patrName) as personName''')
            cols.append(u'''CONCAT(Person.lastName, ' ', Person.firstName, ' ', Person.patrName) as assistantName''')
        else:
            cols.append(u'''Person.id as personId''')
            cols.append(u'''APerson.id as assistantId''')
            cols.append(u'''CONCAT(Person.lastName, ' ', Person.firstName, ' ', Person.patrName) as personName''')
            cols.append(u'''CONCAT(APerson.lastName, ' ', APerson.firstName, ' ', APerson.patrName) as assistantName''')
        cols.append(u'''rbSpeciality.name as specialityName''')
        groupBy += u', Action.person_id'
        if params.get('detailByClient', False):
            cols.append(tableClient['id'].alias('clientId'))
            cols.append(tableClient['lastName'])
            cols.append(tableClient['firstName'])
            cols.append(tableClient['patrName'])
            groupBy += u', Client.id'
        if params.get('detailByActionTypeVisible', False):
            groupBy += u', ActionType.id'

    groupBy += u''' HAVING ((uetDoctor IS NOT NULL AND uetDoctor != 0)
                            OR (uetAverageMedWorker IS NOT NULL
                            AND uetAverageMedWorker != 0)
                            OR (uetAssistantDoctor IS NOT NULL
                            AND uetAssistantDoctor != 0)
                            OR (uetAssistantAverageMedWorker IS NOT NULL
                            AND uetAssistantAverageMedWorker != 0)
                            OR (SELECT
                                ActionType_UETActionSpecification.id
                            FROM
                                ActionType_UETActionSpecification
                            WHERE
                                ActionType_UETActionSpecification.master_id = actionTypeId
                            LIMIT 1) IS NOT NULL) %s'''%postHaving

    stmt = db.selectStmtGroupBy(queryTable, cols, cond, groupBy)
    query = db.query(stmt)
    return query


def selectActionData(params):
    begDate = params.get('begDate', QDate())
    endDate = params.get('endDate', QDate())
    orgStructureId        = params.get('orgStructureId', None)
    financeId             = params.get('financeId', None)
    medicalAidTypeId      = params.get('medicalAidTypeId', None)
    detailByOrgStructures = params.get('detailByOrgStructures', 0)
    detailByFinance       = params.get('detailByFinance', 0)
    detailByMedicalAidType = params.get('detailByMedicalAidType', 0)
    actionStatusList       = params.get('actionStatusList', [])
    personParam            = params.get('personParam', 0)
    detailByActionTypeGroup   = params.get('detailByActionTypeGroup', 0)
    postParam                 = params.get('postParam', 0)
    chkActionTypeClass        = params.get('chkActionTypeClass', False)
    actionTypeClass           = params.get('actionTypeClass', None)
    actionTypeId              = params.get('actionTypeId', None)

    db = QtGui.qApp.db
    tableAction        = db.table('Action')
    tableActionType    = db.table('ActionType')
    tableEvent        = db.table('Event')
    tableClient = db.table('Client')
    tablePerson = db.table('Person')
    tableAssistant = db.table('Person').alias('Assistant')
    tablePost = db.table('rbPost')
    tableAssistantPost = db.table('rbPost').alias('AssistantPost')
    tableFinance = db.table('rbFinance')
    tableContract   = db.table('Contract')
    tableContractAction = db.table('Contract').alias('ContractAction')
    tableRBFinanceContract = db.table('rbFinance').alias('rbFinanceContract')
    tableRBEventFinance = db.table('rbFinance').alias('rbEventFinance')
    tableOrgStructure = db.table('OrgStructure')
    tableAssistantOrgStructure = db.table('OrgStructure').alias('AssistantOrgStructure')
    tableEventType = db.table('EventType')
    tableMedicalAidType = db.table('rbMedicalAidType')
    tableActionTypeUET = db.table('ActionType_UETActionSpecification')

    cols = [tableOrgStructure['id'].alias('orgStructureId'),
            tableOrgStructure['name'].alias('orgStrName'),
            tableAssistantOrgStructure['id'].alias('assistantOrgStructureId'),
            tableAssistantOrgStructure['name'].alias('assistantOrgStrName'),
            u'''IF(rbFinance.name IS NOT NULL, rbFinance.name, (IF(rbFinanceContract.name IS NOT NULL, rbFinanceContract.name, rbEventFinance.name))) AS financeName''',
            tableActionType['class'].alias('actionTypeClass'),
            tableActionType['code'].alias('actionTypeCode'),
            tableActionType['name'].alias('actionTypeName'),
            tableActionType['id'].alias('actionTypeId'),
            tableMedicalAidType['name'].alias('medicalAidTypeName'),
            tableAction['actionSpecification_id'].alias('actionSpecification'),
            u'''SUM(IF(Action.amount = 0, 1, Action.amount)) AS amount''',
            u'''SUM((IF(AGE(Client.birthDate, Action.begDate) >= 18,
                ActionType.adultUetDoctor,
                ActionType.childUetDoctor))*(IF(Action.amount = 0, 1, Action.amount))) AS uetDoctor''',
            u'''SUM((IF(AGE(Client.birthDate, Action.begDate) >= 18,
                ActionType.adultUetAverageMedWorker,
                ActionType.childUetAverageMedWorker))*(IF(Action.amount = 0, 1, Action.amount))) AS uetAverageMedWorker''',
            u'''SUM((IF(AGE(Client.birthDate, Action.begDate) >= 18,
                ActionType.assistantAdultUetDoctor,
                ActionType.assistantChildUetDoctor))*(IF(Action.amount = 0, 1, Action.amount))) AS uetAssistantDoctor''',
            u'''SUM((IF(AGE(Client.birthDate, Action.begDate) >= 18,
                ActionType.assistantAdultUetAverageMedWorker,
                ActionType.assistantChildUetAverageMedWorker))*(IF(Action.amount = 0, 1, Action.amount))) AS uetAssistantAverageMedWorker''',
            u'''SUM((IF(AGE(Client.birthDate, Action.begDate) >= 18,
                (SELECT
                        ActionType_UETActionSpecification.adultUetDoctor
                    FROM
                        ActionType_UETActionSpecification
                    WHERE
                        ActionType_UETActionSpecification.master_id = ActionType.id
                            AND ActionType_UETActionSpecification.actionSpecification_id = Action.actionSpecification_id
                            AND ActionType_UETActionSpecification.isAssistant = 0
                    LIMIT 1),
                (SELECT
                        ActionType_UETActionSpecification.childUetDoctor
                    FROM
                        ActionType_UETActionSpecification
                    WHERE
                        ActionType_UETActionSpecification.master_id = ActionType.id
                            AND ActionType_UETActionSpecification.actionSpecification_id = Action.actionSpecification_id
                            AND ActionType_UETActionSpecification.isAssistant = 0
                    LIMIT 1)))*(IF(Action.amount = 0, 1, Action.amount))) AS specificationUetDoctor''',
            u'''SUM((IF(AGE(Client.birthDate, Action.begDate) >= 18,
                (SELECT
                        ActionType_UETActionSpecification.adultUetAverageMedWorker
                    FROM
                        ActionType_UETActionSpecification
                    WHERE
                        ActionType_UETActionSpecification.master_id = ActionType.id
                            AND ActionType_UETActionSpecification.actionSpecification_id = Action.actionSpecification_id
                            AND ActionType_UETActionSpecification.isAssistant = 0
                    LIMIT 1),
                (SELECT
                        ActionType_UETActionSpecification.childUetAverageMedWorker
                    FROM
                        ActionType_UETActionSpecification
                    WHERE
                        ActionType_UETActionSpecification.master_id = ActionType.id
                            AND ActionType_UETActionSpecification.actionSpecification_id = Action.actionSpecification_id
                            AND ActionType_UETActionSpecification.isAssistant = 0
                    LIMIT 1)))*(IF(Action.amount = 0, 1, Action.amount))) AS specificationUetAverageMedWorker''',
            u'''SUM((IF(AGE(Client.birthDate, Action.begDate) >= 18,
                (SELECT
                        ActionType_UETActionSpecification.adultUetDoctor
                    FROM
                        ActionType_UETActionSpecification
                    WHERE
                        ActionType_UETActionSpecification.master_id = ActionType.id
                            AND ActionType_UETActionSpecification.actionSpecification_id = Action.actionSpecification_id
                            AND ActionType_UETActionSpecification.isAssistant = 1
                    LIMIT 1),
                (SELECT
                        ActionType_UETActionSpecification.childUetDoctor
                    FROM
                        ActionType_UETActionSpecification
                    WHERE
                        ActionType_UETActionSpecification.master_id = ActionType.id
                            AND ActionType_UETActionSpecification.actionSpecification_id = Action.actionSpecification_id
                            AND ActionType_UETActionSpecification.isAssistant = 1
                    LIMIT 1)))*(IF(Action.amount = 0, 1, Action.amount))) AS specificationUetAssistantDoctor''',
            u'''SUM((IF(AGE(Client.birthDate, Action.begDate) >= 18,
                (SELECT
                        ActionType_UETActionSpecification.adultUetAverageMedWorker
                    FROM
                        ActionType_UETActionSpecification
                    WHERE
                        ActionType_UETActionSpecification.master_id = ActionType.id
                            AND ActionType_UETActionSpecification.actionSpecification_id = Action.actionSpecification_id
                            AND ActionType_UETActionSpecification.isAssistant = 1
                    LIMIT 1),
                (SELECT
                        ActionType_UETActionSpecification.childUetAverageMedWorker
                    FROM
                        ActionType_UETActionSpecification
                    WHERE
                        ActionType_UETActionSpecification.master_id = ActionType.id
                            AND ActionType_UETActionSpecification.actionSpecification_id = Action.actionSpecification_id
                            AND ActionType_UETActionSpecification.isAssistant = 1
                    LIMIT 1)))*(IF(Action.amount = 0, 1, Action.amount))) AS specificationUetAssistantAverageMedWorker''',
            u'''IF(rbPost.id, IF(LEFT(rbPost.code, 1) <= 3, 1, 0), NULL) isDoctor''',
            u'''IF(AssistantPost.id, IF(LEFT(AssistantPost.code, 1) <= 3, 1, 0), NULL) isAssistantDoctor''']

    cond = [tableActionType['deleted'].eq(0),
            tableAction['deleted'].eq(0)
            ]

    if begDate and endDate:
        cond.append(tableAction['begDate'].ge(begDate))
        cond.append(tableAction['begDate'].lt(endDate.addDays(1)))

    if financeId:
        cond.append(db.joinOr([tableAction['finance_id'].eq(financeId),
                               db.joinAnd([tableAction['finance_id'].isNull(), tableContractAction['finance_id'].eq(financeId)]),
                               db.joinAnd([tableAction['finance_id'].isNull(), tableContractAction['finance_id'].isNull(), tableContract['finance_id'].eq(financeId)])
                              ]))

    if medicalAidTypeId:
        cond.append(tableEventType['medicalAidType_id'].eq(medicalAidTypeId))

    if orgStructureId:
        orgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', orgStructureId) if orgStructureId else []
        if personParam:
            cond.append(tableAssistant['orgStructure_id'].inlist(orgStructureIdList))
        else:
            cond.append(tablePerson['orgStructure_id'].inlist(orgStructureIdList))

    if chkActionTypeClass:
        if actionTypeClass is not None:
            cond.append(tableActionType['class'].eq(actionTypeClass))
        if actionTypeId:
            cond.append(tableActionType['id'].inlist(getActionTypeDescendants(actionTypeId, actionTypeClass)))

    if actionStatusList:
        cond.append(tableAction['status'].inlist(actionStatusList))

    queryTable = tableAction
    queryTable = queryTable.leftJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
    queryTable = queryTable.leftJoin(tableFinance, tableFinance['id'].eq(tableAction['finance_id']))
    queryTable = queryTable.leftJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
    queryTable = queryTable.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
    queryTable = queryTable.leftJoin(tableContractAction, db.joinAnd([tableContractAction['id'].eq(tableAction['contract_id']), tableContractAction['deleted'].eq(0)]))
    queryTable = queryTable.leftJoin(tableRBFinanceContract, tableRBFinanceContract['id'].eq(tableContractAction['finance_id']))
    queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
    queryTable = queryTable.leftJoin(tableRBEventFinance, tableRBEventFinance['id'].eq(tableContract['finance_id']))
    queryTable = queryTable.leftJoin(tableMedicalAidType, tableMedicalAidType['id'].eq(tableEventType['medicalAidType_id']))
    queryTable = queryTable.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
    queryTable = queryTable.leftJoin(tableAssistant, tableAssistant['id'].eq(tableAction['assistant_id']))
    queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(tableAction['person_id']))
    queryTable = queryTable.leftJoin(tablePost, tablePost['id'].eq(tablePerson['post_id']))
    queryTable = queryTable.leftJoin(tableAssistantPost, tableAssistantPost['id'].eq(tableAssistant['post_id']))
    queryTable = queryTable.leftJoin(tableOrgStructure, tableOrgStructure['id'].eq(tablePerson['orgStructure_id']))
    queryTable = queryTable.leftJoin(tableAssistantOrgStructure, tableAssistantOrgStructure['id'].eq(tableAssistant['orgStructure_id']))
    queryTable = queryTable.leftJoin(tableActionTypeUET, db.joinAnd([tableActionTypeUET['master_id'].eq(tableActionType['id']),
                                                                     tableActionTypeUET['actionSpecification_id'].eq(tableAction['actionSpecification_id'])]))
    if detailByOrgStructures:
        orgStrGrouping = u'AssistantOrgStructure.name ,' if personParam else u'OrgStructure.name ,'
    else:
        orgStrGrouping = u''
    groupBy = u'''%s %s ActionType.class, ActionType.code, Action.actionSpecification_id, %s
    IF(rbFinance.id IS NOT NULL, rbFinance.id, (IF(rbFinanceContract.id IS NOT NULL, rbFinanceContract.id, rbEventFinance.id)))'''%(orgStrGrouping, u'rbMedicalAidType.id ,' if detailByMedicalAidType else u'', u'isAssistantDoctor,' if personParam else u'isDoctor,')
    if postParam:
        postHaving = u' AND %s = 0 '%(u'isAssistantDoctor' if personParam else u'isDoctor')
    else:
        postHaving = u' AND %s = 1 '%(u'isAssistantDoctor' if personParam else u'isDoctor')
    if detailByActionTypeGroup:
        tableActionTypeGroup = db.table('ActionType').alias('ActionTypeGroup')
        cols.append(tableActionType['group_id'].alias('actionTypeGroupId'))
        cols.append(tableActionTypeGroup['name'].alias('actionTypeGroupName'))
        queryTable = queryTable.leftJoin(tableActionTypeGroup, db.joinAnd([tableActionTypeGroup['id'].eq(tableActionType['group_id']), tableActionTypeGroup['deleted'].eq(0)]))
        groupBy += u''', ActionType.group_id '''
    groupBy += u''' HAVING ((uetDoctor IS NOT NULL AND uetDoctor != 0)
                            OR (uetAverageMedWorker IS NOT NULL
                            AND uetAverageMedWorker != 0)
                            OR (uetAssistantDoctor IS NOT NULL
                            AND uetAssistantDoctor != 0)
                            OR (uetAssistantAverageMedWorker IS NOT NULL
                            AND uetAssistantAverageMedWorker != 0)
                            OR (SELECT
                                ActionType_UETActionSpecification.id
                            FROM
                                ActionType_UETActionSpecification
                            WHERE
                                ActionType_UETActionSpecification.master_id = actionTypeId
                            LIMIT 1) IS NOT NULL) %s'''%postHaving

    groupBy += u''' ORDER BY OrgStructure.name , %s ActionType.class , ActionType.code'''%(u'IF(rbFinance.id IS NOT NULL, rbFinance.id, (IF(rbFinanceContract.id IS NOT NULL, rbFinanceContract.id, rbEventFinance.id))),' if detailByFinance else u'')
    stmt = db.selectStmtGroupBy(queryTable, cols, cond, groupBy)
    query = db.query(stmt)
    return query


def selectGroupingData(params, byPersons=False):
    begDate          = params.get('begDate', QDate())
    endDate          = params.get('endDate', QDate())
    orgStructureId   = params.get('orgStructureId', None)
    financeId        = params.get('financeId', None)
    medicalAidKindId = params.get('medicalAidKindId', None)
    actionStatusList = params.get('actionStatusList', [])
    detailByClient   = params.get('detailByClient', False)
    personParam      = params.get('personParam', 0)
    postParam        = params.get('postParam', 0)
    chkActionTypeClass = params.get('chkActionTypeClass', False)
    actionTypeClass    = params.get('actionTypeClass', None)
    actionTypeId       = params.get('actionTypeId', None)

    db = QtGui.qApp.db
    tableAction     = db.table('Action')
    tableActionType = db.table('ActionType')
    tableEvent      = db.table('Event')
    tableClient     = db.table('Client')
    tablePerson     = db.table('Person')
    tableAPerson    = db.table('Person').alias('APerson')
    tableRBPost     = db.table('rbPost')
    tableAssistantPost = db.table('rbPost').alias('AssistantPost')
    tableRBSpeciality = db.table('rbSpeciality')
    tableRBFinance  = db.table('rbFinance')
    tableContractAction = db.table('Contract').alias('ContractAction')
    tableRBFinanceContract = db.table('rbFinance').alias('rbFinanceContract')
    tableContract   = db.table('Contract')
    tableRBEventFinance = db.table('rbFinance').alias('rbEventFinance')
    tableOrgStructure   = db.table('OrgStructure')
    tableEventType      = db.table('EventType')
    tableRBMedicalAidKind = db.table('rbMedicalAidType')
    tableActionTypeUET    = db.table('ActionType_UETActionSpecification')

    cond = [tableAction['deleted'].eq(0),
            tableActionType['deleted'].eq(0)
            ]

    cols = [tableRBMedicalAidKind['name'].alias('medicalAidKindName'),
            tableOrgStructure['name'].alias('orgStructureName'),
            tableRBSpeciality['name'].alias('specialityName'),
            u'''IF(rbFinance.name IS NOT NULL, rbFinance.name, (IF(rbFinanceContract.name IS NOT NULL, rbFinanceContract.name, rbEventFinance.name))) AS financeName''',
            tableActionType['id'].alias('actionTypeId'),
            tableActionType['name'].alias('actionTypeName'),
            tableActionType['code'].alias('actionTypeCode'),
            tableAction['actionSpecification_id'].alias('actionSpecification'),
            u'''SUM(IF(Action.amount = 0, 1, Action.amount)) AS amount''',
            u'''SUM((IF(AGE(Client.birthDate, Action.begDate) >= 18,
                ActionType.adultUetDoctor,
                ActionType.childUetDoctor))*(IF(Action.amount = 0, 1, Action.amount))) AS uetDoctor''',
            u'''SUM((IF(AGE(Client.birthDate, Action.begDate) >= 18,
                ActionType.adultUetAverageMedWorker,
                ActionType.childUetAverageMedWorker))*(IF(Action.amount = 0, 1, Action.amount))) AS uetAverageMedWorker''',
            u'''SUM((IF(AGE(Client.birthDate, Action.begDate) >= 18,
                ActionType.assistantAdultUetDoctor,
                ActionType.assistantChildUetDoctor))*(IF(Action.amount = 0, 1, Action.amount))) AS uetAssistantDoctor''',
            u'''SUM((IF(AGE(Client.birthDate, Action.begDate) >= 18,
                ActionType.assistantAdultUetAverageMedWorker,
                ActionType.assistantChildUetAverageMedWorker))*(IF(Action.amount = 0, 1, Action.amount))) AS uetAssistantAverageMedWorker''',
            u'''SUM((IF(AGE(Client.birthDate, Action.begDate) >= 18,
                (SELECT
                        ActionType_UETActionSpecification.adultUetDoctor
                    FROM
                        ActionType_UETActionSpecification
                    WHERE
                        ActionType_UETActionSpecification.master_id = ActionType.id
                            AND ActionType_UETActionSpecification.actionSpecification_id = Action.actionSpecification_id
                            AND ActionType_UETActionSpecification.isAssistant = 0
                    LIMIT 1),
                (SELECT
                        ActionType_UETActionSpecification.childUetDoctor
                    FROM
                        ActionType_UETActionSpecification
                    WHERE
                        ActionType_UETActionSpecification.master_id = ActionType.id
                            AND ActionType_UETActionSpecification.actionSpecification_id = Action.actionSpecification_id
                            AND ActionType_UETActionSpecification.isAssistant = 0
                    LIMIT 1)))*(IF(Action.amount = 0, 1, Action.amount))) AS specificationUetDoctor''',
            u'''SUM((IF(AGE(Client.birthDate, Action.begDate) >= 18,
                (SELECT
                        ActionType_UETActionSpecification.adultUetAverageMedWorker
                    FROM
                        ActionType_UETActionSpecification
                    WHERE
                        ActionType_UETActionSpecification.master_id = ActionType.id
                            AND ActionType_UETActionSpecification.actionSpecification_id = Action.actionSpecification_id
                            AND ActionType_UETActionSpecification.isAssistant = 0
                    LIMIT 1),
                (SELECT
                        ActionType_UETActionSpecification.childUetAverageMedWorker
                    FROM
                        ActionType_UETActionSpecification
                    WHERE
                        ActionType_UETActionSpecification.master_id = ActionType.id
                            AND ActionType_UETActionSpecification.actionSpecification_id = Action.actionSpecification_id
                            AND ActionType_UETActionSpecification.isAssistant = 0
                    LIMIT 1)))*(IF(Action.amount = 0, 1, Action.amount))) AS specificationUetAverageMedWorker''',
            u'''SUM((IF(AGE(Client.birthDate, Action.begDate) >= 18,
                (SELECT
                        ActionType_UETActionSpecification.adultUetDoctor
                    FROM
                        ActionType_UETActionSpecification
                    WHERE
                        ActionType_UETActionSpecification.master_id = ActionType.id
                            AND ActionType_UETActionSpecification.actionSpecification_id = Action.actionSpecification_id
                            AND ActionType_UETActionSpecification.isAssistant = 1
                    LIMIT 1),
                (SELECT
                        ActionType_UETActionSpecification.childUetDoctor
                    FROM
                        ActionType_UETActionSpecification
                    WHERE
                        ActionType_UETActionSpecification.master_id = ActionType.id
                            AND ActionType_UETActionSpecification.actionSpecification_id = Action.actionSpecification_id
                            AND ActionType_UETActionSpecification.isAssistant = 1
                    LIMIT 1)))*(IF(Action.amount = 0, 1, Action.amount))) AS specificationUetAssistantDoctor''',
            u'''SUM((IF(AGE(Client.birthDate, Action.begDate) >= 18,
                (SELECT
                        ActionType_UETActionSpecification.adultUetAverageMedWorker
                    FROM
                        ActionType_UETActionSpecification
                    WHERE
                        ActionType_UETActionSpecification.master_id = ActionType.id
                            AND ActionType_UETActionSpecification.actionSpecification_id = Action.actionSpecification_id
                            AND ActionType_UETActionSpecification.isAssistant = 1
                    LIMIT 1),
                (SELECT
                        ActionType_UETActionSpecification.childUetAverageMedWorker
                    FROM
                        ActionType_UETActionSpecification
                    WHERE
                        ActionType_UETActionSpecification.master_id = ActionType.id
                            AND ActionType_UETActionSpecification.actionSpecification_id = Action.actionSpecification_id
                            AND ActionType_UETActionSpecification.isAssistant = 1
                    LIMIT 1)))*(IF(Action.amount = 0, 1, Action.amount))) AS specificationUetAssistantAverageMedWorker''',
            u'''IF(rbPost.id, IF(LEFT(rbPost.code, 1) <= 3, 1, 0), NULL) isDoctor''',
            u'''IF(AssistantPost.id, IF(LEFT(AssistantPost.code, 1) <= 3, 1, 0), NULL) isAssistantDoctor'''
                ]

    if byPersons:
        if personParam:
            cols.append(u'''APerson.id as personId''')
            cols.append(u'''Person.id as assistantId''')
            cols.append(u'''CONCAT(APerson.lastName, ' ', APerson.firstName, ' ', APerson.patrName) as personName''')
            cols.append(u'''CONCAT(Person.lastName, ' ', Person.firstName, ' ', Person.patrName) as assistantName''')
        else:
            cols.append(u'''Person.id as personId''')
            cols.append(u'''APerson.id as assistantId''')
            cols.append(u'''CONCAT(Person.lastName, ' ', Person.firstName, ' ', Person.patrName) as personName''')
            cols.append(u'''CONCAT(APerson.lastName, ' ', APerson.firstName, ' ', APerson.patrName) as assistantName''')
        if detailByClient:
            cols.append(tableClient['id'].alias('clientId'))
            cols.append(tableClient['lastName'])
            cols.append(tableClient['firstName'])
            cols.append(tableClient['patrName'])

    if begDate and endDate:
        cond.append(tableAction['begDate'].ge(begDate))
        cond.append(tableAction['begDate'].lt(endDate.addDays(1)))

    if financeId:
        cond.append(db.joinOr([tableAction['finance_id'].eq(financeId),
                               db.joinAnd([tableAction['finance_id'].isNull(), tableContractAction['finance_id'].eq(financeId)]),
                               db.joinAnd([tableAction['finance_id'].isNull(), tableContractAction['finance_id'].isNull(), tableContract['finance_id'].eq(financeId)])
                              ]))

    if medicalAidKindId:
        cond.append(tableEventType['medicalAidType_id'].eq(medicalAidKindId))

    if orgStructureId:
        orgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', orgStructureId) if orgStructureId else []
        cond.append(tablePerson['orgStructure_id'].inlist(orgStructureIdList))

    if chkActionTypeClass:
        if actionTypeClass is not None:
            cond.append(tableActionType['class'].eq(actionTypeClass))
        if actionTypeId:
            cond.append(tableActionType['id'].inlist(getActionTypeDescendants(actionTypeId, actionTypeClass)))

    if actionStatusList:
        cond.append(tableAction['status'].inlist(actionStatusList))

    queryTable = tableAction
    queryTable = queryTable.leftJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
    queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
    queryTable = queryTable.leftJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
    queryTable = queryTable.leftJoin(tableContractAction, db.joinAnd([tableContractAction['id'].eq(tableAction['contract_id']), tableContractAction['deleted'].eq(0)]))
    queryTable = queryTable.leftJoin(tableRBFinanceContract, tableRBFinanceContract['id'].eq(tableContractAction['finance_id']))
    queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
    queryTable = queryTable.leftJoin(tableRBEventFinance, tableRBEventFinance['id'].eq(tableContract['finance_id']))
    queryTable = queryTable.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
    queryTable = queryTable.leftJoin(tableRBMedicalAidKind, tableRBMedicalAidKind['id'].eq(tableEventType['medicalAidType_id']))
    queryTable = queryTable.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
    queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(tableAction['person_id']))
    queryTable = queryTable.leftJoin(tableAPerson, tableAPerson['id'].eq(tableAction['assistant_id']))
    if personParam:
        queryTable = queryTable.leftJoin(tableRBSpeciality, tableRBSpeciality['id'].eq(tableAPerson['speciality_id']))
    else:
        queryTable = queryTable.leftJoin(tableRBSpeciality, tableRBSpeciality['id'].eq(tablePerson['speciality_id']))
    queryTable = queryTable.leftJoin(tableRBPost, tableRBPost['id'].eq(tablePerson['post_id']))
    queryTable = queryTable.leftJoin(tableAssistantPost, tableAssistantPost['id'].eq(tableAPerson['post_id']))
    if personParam:
        queryTable = queryTable.leftJoin(tableOrgStructure, tableOrgStructure['id'].eq(tableAPerson['orgStructure_id']))
    else:
        queryTable = queryTable.leftJoin(tableOrgStructure, tableOrgStructure['id'].eq(tablePerson['orgStructure_id']))
    queryTable = queryTable.leftJoin(tableActionTypeUET, db.joinAnd([tableActionTypeUET['master_id'].eq(tableActionType['id']),
                                                                     tableActionTypeUET['actionSpecification_id'].eq(tableAction['actionSpecification_id'])]))

    if postParam:
        postHaving = u' AND %s = 0 '%(u'isAssistantDoctor' if personParam else u'isDoctor')
    else:
        postHaving = u' AND %s = 1 '%(u'isAssistantDoctor' if personParam else u'isDoctor')

    if byPersons:
        groupBy = u'''OrgStructure.id,
                      Person.id,
                      APerson.id,
                      IF(rbFinance.id IS NOT NULL, rbFinance.id, (IF(rbFinanceContract.id IS NOT NULL, rbFinanceContract.id, rbEventFinance.id))),
                      rbMedicalAidType.id'''
    else:
        groupBy = u'''ActionType.id,
                      OrgStructure.id,
                      IF(rbFinance.id IS NOT NULL, rbFinance.id, (IF(rbFinanceContract.id IS NOT NULL, rbFinanceContract.id, rbEventFinance.id))),
                      rbMedicalAidType.id'''
        groupBy += u', isAssistantDoctor' if personParam else u', isDoctor'
    groupBy += u''' HAVING ((uetDoctor IS NOT NULL AND uetDoctor != 0)
                            OR (uetAverageMedWorker IS NOT NULL
                            AND uetAverageMedWorker != 0)
                            OR (uetAssistantDoctor IS NOT NULL
                            AND uetAssistantDoctor != 0)
                            OR (uetAssistantAverageMedWorker IS NOT NULL
                            AND uetAssistantAverageMedWorker != 0)
                            OR (SELECT
                                ActionType_UETActionSpecification.id
                            FROM
                                ActionType_UETActionSpecification
                            WHERE
                                ActionType_UETActionSpecification.master_id = actionTypeId
                            LIMIT 1) IS NOT NULL) %s'''%postHaving
    stmt = db.selectStmtGroupBy(queryTable, cols, cond, groupBy)
    query = db.query(stmt)
    return query


class CReportUETActionByActions(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Сводка УЕТ по мероприятиям')
        self.orientation = CPageFormat.Landscape


    def getSetupDialog(self, parent):
        result = CReportUETActionsSetup(parent)
        result.setDetailByActionTypeClassesVisible(True)
        result.setDetailByActionTypeGroupVisible(True)
        result.setTitle(self.title())
        return result


    def dumpParams(self, cursor, params):
        db = QtGui.qApp.db
        self.params = params
        nameList = []
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        financeId        = params.get('financeId', None)
        medicalAidTypeId = params.get('medicalAidTypeId', None)
        orgStructureId   = params.get('orgStructureId', None)
        actionStatusList = params.get('actionStatusList', [])
        description = []
        if begDate and endDate:
            description.append(dateRangeAsStr(u'', begDate, endDate))
        if orgStructureId:
            orgStrName = getOrgStructureName(orgStructureId)
            description.append(u'Подразделение: %s'%orgStrName)
        if financeId:
            financeName = CFinanceType.getNameById(financeId)
            description.append(u'Тип финансирования: %s'%financeName)
        if medicalAidTypeId:
            medicalAidTypeName = getMedicalAidTypeName(medicalAidTypeId)
            description.append(u'Тип мед помощи: %s'%medicalAidTypeName)
        if actionStatusList:
            for i, name in enumerate(actionStatusList):
                    nameList.append(CActionStatus.names[name])
            description.append(u'Статус действия: ' + u','.join(name for name in nameList if name))
        chkActionTypeClass = params.get('chkActionTypeClass', False)
        actionTypeClass = params.get('actionTypeClass', None)
        actionTypeId = params.get('actionTypeId', None)
        if chkActionTypeClass:
            if actionTypeClass is not None:
                description.append(u'Класс действия: %s'%{0: u'Статус',
                                                   1: u'Диагностика',
                                                   2: u'Лечение',
                                                   3: u'Прочие мероприятия'}.get(actionTypeClass, u'Статус'))

            if actionTypeId:
                description.append(u'Тип действия: %s'%forceString(db.translate('ActionType', 'id', actionTypeId, 'CONCAT_WS(\' | \', code,name)')))
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertBlock(CReportBase.AlignCenter)
        cursor.movePosition(QtGui.QTextCursor.End)
        columns = [ ('100%', [], CReportBase.AlignLeft)]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)


    def build(self, params):
        detailByOrgStructures     = params.get('detailByOrgStructures', 0)
        detailByFinance           = params.get('detailByFinance', 0)
        detailByMedicalAidType    = params.get('detailByMedicalAidType', 0)
        detailByActionTypeClasses = params.get('detailByActionTypeClasses', 0)
        detailByActionTypeGroup   = params.get('detailByActionTypeGroup', 0)
        personParam               = params.get('personParam', 0)
        postParam                 = params.get('postParam', 0)
        financeList = []
        orgStructureList = []
        medicalAidTypeList = []
        actionTypeClassesList = []
        doc = QtGui.QTextDocument()

        query = selectActionData(params)
        if query is None:
            return doc

        dataDict = {}
        while query.next():
            record = query.record()
            actionTypeId = forceString(record.value('actionTypeId'))
            #orgStructureId = forceRef(record.value('assistantOrgStructureId')) if personParam else forceRef(record.value('orgStructureId'))
            orgStructureName = forceString(record.value('assistantOrgStrName')) if personParam else forceString(record.value('orgStrName'))
            financeName = forceString(record.value('financeName'))
            actionTypeGroupId = forceRef(record.value('actionTypeGroupId'))
            actionTypeGroupName = forceString(record.value('actionTypeGroupName'))
            actionTypeClass = forceInt(record.value('actionTypeClass'))
            actionTypeCode = forceString(record.value('actionTypeCode'))
            actionTypeName = forceString(record.value('actionTypeName'))
            amount = forceInt(record.value('amount'))
            medicalAidTypeName = forceString(record.value('medicalAidTypeName'))
            actionSpecification = forceRef(record.value('actionSpecification_id'))
            uetDoctor = forceDouble(record.value('uetDoctor'))
            uetAverageMedWorker = forceDouble(record.value('uetAverageMedWorker'))
            uetAssistantDoctor = forceDouble(record.value('uetAssistantDoctor'))
            uetAssistantAverageMedWorker = forceDouble(record.value('uetAssistantAverageMedWorker'))
            specificationUetDoctor = forceDouble(record.value('specificationUetDoctor'))
            specificationUetAverageMedWorker = forceDouble(record.value('specificationUetAverageMedWorker'))
            specificationUetAssistantDoctor = forceDouble(record.value('specificationUetAssistantDoctor'))
            specificationUetAssistantAverageMedWorker = forceDouble(record.value('specificationUetAssistantAverageMedWorker'))

            if financeName not in financeList:
                financeList.append(financeName)

            if medicalAidTypeName not in medicalAidTypeList:
                medicalAidTypeList.append(medicalAidTypeName)

            if orgStructureName not in orgStructureList:
                orgStructureList.append(orgStructureName)

            if actionTypeClass not in actionTypeClassesList:
                actionTypeClassesList.append(actionTypeClass)

            if actionSpecification:
                if personParam:
                    if postParam: #ассистент+средний мед персонал
                        uet = specificationUetAssistantAverageMedWorker
                    else: #ассистент+врач
                        uet = specificationUetAssistantDoctor
                else:
                    if postParam: #исполнитель+средний мед персонал
                        uet = specificationUetAverageMedWorker
                    else: #исполнитель+врач
                        uet = specificationUetDoctor
            else:
                if personParam:
                    if postParam: #ассистент+средний мед персонал
                        uet = uetAssistantAverageMedWorker
                    else: #ассистент+врач
                        uet = uetAssistantDoctor
                else:
                    if postParam: #исполнитель+средний мед персонал
                        uet = uetAverageMedWorker
                    else: #исполнитель+врач
                        uet = uetDoctor

            if detailByActionTypeClasses:
                keyActionType = (actionTypeId, (actionTypeCode, actionTypeName))
                if detailByActionTypeGroup:
                    if detailByOrgStructures:
                        if detailByFinance and detailByMedicalAidType:
                            if orgStructureName not in dataDict.keys():
                                dataDict[orgStructureName] = {}
                            if actionTypeClass not in dataDict[orgStructureName].keys():
                                dataDict[orgStructureName][actionTypeClass] = {}
                            if (actionTypeGroupName, actionTypeGroupId) not in dataDict[orgStructureName][actionTypeClass].keys():
                                dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)] = {}
                            if keyActionType not in dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)].keys():
                                dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType] = {}
                            if financeName not in dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType].keys():
                                dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType][financeName] = {}
                            if medicalAidTypeName not in dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType][financeName].keys():
                                dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType][financeName][medicalAidTypeName] = [0]*2
                            dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType][financeName][medicalAidTypeName][0] += amount
                            dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType][financeName][medicalAidTypeName][1] += uet
                        elif detailByFinance:
                            if orgStructureName not in dataDict.keys():
                                dataDict[orgStructureName] = {}
                            if actionTypeClass not in dataDict[orgStructureName].keys():
                                dataDict[orgStructureName][actionTypeClass] = {}
                            if (actionTypeGroupName, actionTypeGroupId) not in dataDict[orgStructureName][actionTypeClass].keys():
                                dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)] = {}
                            if keyActionType not in dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)].keys():
                                dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType] = {}
                            if financeName not in dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType].keys():
                                dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType][financeName] = [0]*2
                            dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType][financeName][0] += amount
                            dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType][financeName][1] += uet
                        elif detailByMedicalAidType:
                            if orgStructureName not in dataDict.keys():
                                dataDict[orgStructureName] = {}
                            if actionTypeClass not in dataDict[orgStructureName].keys():
                                dataDict[orgStructureName][actionTypeClass] = {}
                            if (actionTypeGroupName, actionTypeGroupId) not in dataDict[orgStructureName][actionTypeClass].keys():
                                dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)] = {}
                            if keyActionType not in dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)].keys():
                                dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType] = {}
                            if medicalAidTypeName not in dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType].keys():
                                dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType][medicalAidTypeName] = [0]*2
                            dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType][medicalAidTypeName][0] += amount
                            dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType][medicalAidTypeName][1] += uet
                        else:
                            if orgStructureName not in dataDict.keys():
                                dataDict[orgStructureName] = {}
                            if actionTypeClass not in dataDict[orgStructureName].keys():
                                dataDict[orgStructureName][actionTypeClass] = {}
                            if (actionTypeGroupName, actionTypeGroupId) not in dataDict[orgStructureName][actionTypeClass].keys():
                                dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)] = {}
                            if keyActionType not in dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)].keys():
                                dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType] = [0]*2
                            dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType][0] += amount
                            dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType][1] += uet
                    else: # not detailByOrgStructures
                        if detailByFinance and detailByMedicalAidType:
                            if actionTypeClass not in dataDict.keys():
                                dataDict[actionTypeClass] = {}
                            if (actionTypeGroupName, actionTypeGroupId) not in dataDict[actionTypeClass].keys():
                                dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)] = {}
                            if keyActionType not in dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)].keys():
                                dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType] = {}
                            if financeName not in dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType].keys():
                                dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType][financeName] = {}
                            if medicalAidTypeName not in dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType][financeName].keys():
                                dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType][financeName][medicalAidTypeName] = [0]*2
                            dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType][financeName][medicalAidTypeName][0] += amount
                            dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType][financeName][medicalAidTypeName][1] += uet
                        elif detailByFinance:
                            if actionTypeClass not in dataDict.keys():
                                dataDict[actionTypeClass] = {}
                            if (actionTypeGroupName, actionTypeGroupId) not in dataDict[actionTypeClass].keys():
                                dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)] = {}
                            if keyActionType not in dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)].keys():
                                dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType] = {}
                            if financeName not in dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType].keys():
                                dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType][financeName] = [0]*2
                            dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType][financeName][0] += amount
                            dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType][financeName][1] += uet
                        elif detailByMedicalAidType:
                            if actionTypeClass not in dataDict.keys():
                                dataDict[actionTypeClass] = {}
                            if (actionTypeGroupName, actionTypeGroupId) not in dataDict[actionTypeClass].keys():
                                dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)] = {}
                            if keyActionType not in dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)].keys():
                                dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType] = {}
                            if medicalAidTypeName not in dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType].keys():
                                dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType][medicalAidTypeName] = [0]*2
                            dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType][medicalAidTypeName][0] += amount
                            dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType][medicalAidTypeName][1] += uet
                        else:
                            if actionTypeClass not in dataDict.keys():
                                dataDict[actionTypeClass] = {}
                            if (actionTypeGroupName, actionTypeGroupId) not in dataDict[actionTypeClass].keys():
                                dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)] = {}
                            if keyActionType not in dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)].keys():
                                dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType] = [0]*2
                            dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType][0] += amount
                            dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][keyActionType][1] += uet
                else: # not detailByActionTypeGroup
                    if detailByOrgStructures:
                        if detailByFinance and detailByMedicalAidType:
                            if orgStructureName not in dataDict.keys():
                                dataDict[orgStructureName] = {}
                            if actionTypeClass not in dataDict[orgStructureName].keys():
                                dataDict[orgStructureName][actionTypeClass] = {}
                            if keyActionType not in dataDict[orgStructureName][actionTypeClass].keys():
                                dataDict[orgStructureName][actionTypeClass][keyActionType] = {}
                            if financeName not in dataDict[orgStructureName][actionTypeClass][keyActionType].keys():
                                dataDict[orgStructureName][actionTypeClass][keyActionType][financeName] = {}
                            if medicalAidTypeName not in dataDict[orgStructureName][actionTypeClass][keyActionType][financeName].keys():
                                dataDict[orgStructureName][actionTypeClass][keyActionType][financeName][medicalAidTypeName] = [0]*2
                            dataDict[orgStructureName][actionTypeClass][keyActionType][financeName][medicalAidTypeName][0] += amount
                            dataDict[orgStructureName][actionTypeClass][keyActionType][financeName][medicalAidTypeName][1] += uet
                        elif detailByFinance:
                            if orgStructureName not in dataDict.keys():
                                dataDict[orgStructureName] = {}
                            if actionTypeClass not in dataDict[orgStructureName].keys():
                                dataDict[orgStructureName][actionTypeClass] = {}
                            if keyActionType not in dataDict[orgStructureName][actionTypeClass].keys():
                                dataDict[orgStructureName][actionTypeClass][keyActionType] = {}
                            if financeName not in dataDict[orgStructureName][actionTypeClass][keyActionType].keys():
                                dataDict[orgStructureName][actionTypeClass][keyActionType][financeName] = [0]*2
                            dataDict[orgStructureName][actionTypeClass][keyActionType][financeName][0] += amount
                            dataDict[orgStructureName][actionTypeClass][keyActionType][financeName][1] += uet
                        elif detailByMedicalAidType:
                            if orgStructureName not in dataDict.keys():
                                dataDict[orgStructureName] = {}
                            if actionTypeClass not in dataDict[orgStructureName].keys():
                                dataDict[orgStructureName][actionTypeClass] = {}
                            if keyActionType not in dataDict[orgStructureName][actionTypeClass].keys():
                                dataDict[orgStructureName][actionTypeClass][keyActionType] = {}
                            if medicalAidTypeName not in dataDict[orgStructureName][actionTypeClass][keyActionType].keys():
                                dataDict[orgStructureName][actionTypeClass][keyActionType][medicalAidTypeName] = [0]*2
                            dataDict[orgStructureName][actionTypeClass][keyActionType][medicalAidTypeName][0] += amount
                            dataDict[orgStructureName][actionTypeClass][keyActionType][medicalAidTypeName][1] += uet
                        else:
                            if orgStructureName not in dataDict.keys():
                                dataDict[orgStructureName] = {}
                            if actionTypeClass not in dataDict[orgStructureName].keys():
                                dataDict[orgStructureName][actionTypeClass] = {}
                            if keyActionType not in dataDict[orgStructureName][actionTypeClass].keys():
                                dataDict[orgStructureName][actionTypeClass][keyActionType] = [0]*2
                            dataDict[orgStructureName][actionTypeClass][keyActionType][0] += amount
                            dataDict[orgStructureName][actionTypeClass][keyActionType][1] += uet
                    else: # not detailByOrgStructures
                        if detailByFinance and detailByMedicalAidType:
                            if actionTypeClass not in dataDict.keys():
                                dataDict[actionTypeClass] = {}
                            if keyActionType not in dataDict[actionTypeClass].keys():
                                dataDict[actionTypeClass][keyActionType] = {}
                            if financeName not in dataDict[actionTypeClass][keyActionType].keys():
                                dataDict[actionTypeClass][keyActionType][financeName] = {}
                            if medicalAidTypeName not in dataDict[actionTypeClass][keyActionType][financeName].keys():
                                dataDict[actionTypeClass][keyActionType][financeName][medicalAidTypeName] = [0]*2
                            dataDict[actionTypeClass][keyActionType][financeName][medicalAidTypeName][0] += amount
                            dataDict[actionTypeClass][keyActionType][financeName][medicalAidTypeName][1] += uet
                        elif detailByFinance:
                            if actionTypeClass not in dataDict.keys():
                                dataDict[actionTypeClass] = {}
                            if keyActionType not in dataDict[actionTypeClass].keys():
                                dataDict[actionTypeClass][keyActionType] = {}
                            if financeName not in dataDict[actionTypeClass][keyActionType].keys():
                                dataDict[actionTypeClass][keyActionType][financeName] = [0]*2
                            dataDict[actionTypeClass][keyActionType][financeName][0] += amount
                            dataDict[actionTypeClass][keyActionType][financeName][1] += uet
                        elif detailByMedicalAidType:
                            if actionTypeClass not in dataDict.keys():
                                dataDict[actionTypeClass] = {}
                            if keyActionType not in dataDict[actionTypeClass].keys():
                                dataDict[actionTypeClass][keyActionType] = {}
                            if medicalAidTypeName not in dataDict[actionTypeClass][keyActionType].keys():
                                dataDict[actionTypeClass][keyActionType][medicalAidTypeName] = [0]*2
                            dataDict[actionTypeClass][keyActionType][medicalAidTypeName][0] += amount
                            dataDict[actionTypeClass][keyActionType][medicalAidTypeName][1] += uet
                        else:
                            if actionTypeClass not in dataDict.keys():
                                dataDict[actionTypeClass] = {}
                            if keyActionType not in dataDict[actionTypeClass].keys():
                                dataDict[actionTypeClass][keyActionType] = [0]*2
                            dataDict[actionTypeClass][keyActionType][0] += amount
                            dataDict[actionTypeClass][keyActionType][1] += uet
            else: # not detailByActionTypeClasses
                keyActionType = (actionTypeId, (actionTypeCode, actionTypeName))
                if detailByActionTypeGroup:
                    if detailByOrgStructures:
                        if detailByFinance and detailByMedicalAidType:
                            if orgStructureName not in dataDict.keys():
                                dataDict[orgStructureName] = {}
                            if (actionTypeGroupName, actionTypeGroupId) not in dataDict[orgStructureName].keys():
                                dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)] = {}
                            if keyActionType not in dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)].keys():
                                dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][keyActionType] = {}
                            if financeName not in dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][keyActionType].keys():
                                dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][keyActionType][financeName] = {}
                            if medicalAidTypeName not in dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][keyActionType][financeName].keys():
                                dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][keyActionType][financeName][medicalAidTypeName] = [0]*2
                            dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][keyActionType][financeName][medicalAidTypeName][0] += amount
                            dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][keyActionType][financeName][medicalAidTypeName][1] += uet
                        elif detailByFinance:
                            if orgStructureName not in dataDict.keys():
                                dataDict[orgStructureName] = {}
                            if (actionTypeGroupName, actionTypeGroupId) not in dataDict[orgStructureName].keys():
                                dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)] = {}
                            if keyActionType not in dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)].keys():
                                dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][keyActionType] = {}
                            if financeName not in dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][keyActionType].keys():
                                dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][keyActionType][financeName] = [0]*2
                            dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][keyActionType][financeName][0] += amount
                            dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][keyActionType][financeName][1] += uet
                        elif detailByMedicalAidType:
                            if orgStructureName not in dataDict.keys():
                                dataDict[orgStructureName] = {}
                            if (actionTypeGroupName, actionTypeGroupId) not in dataDict[orgStructureName].keys():
                                dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)] = {}
                            if keyActionType not in dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)].keys():
                                dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][keyActionType] = {}
                            if medicalAidTypeName not in dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][keyActionType].keys():
                                dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][keyActionType][medicalAidTypeName] = [0]*2
                            dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][keyActionType][medicalAidTypeName][0] += amount
                            dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][keyActionType][medicalAidTypeName][1] += uet
                        else:
                            if orgStructureName not in dataDict.keys():
                                dataDict[orgStructureName] = {}
                            if (actionTypeGroupName, actionTypeGroupId) not in dataDict[orgStructureName].keys():
                                dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)] = {}
                            if keyActionType not in dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)].keys():
                                dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][keyActionType] = [0]*2
                            dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][keyActionType][0] += amount
                            dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][keyActionType][1] += uet
                    else: # not detailByOrgStructures
                        if detailByFinance and detailByMedicalAidType:
                            if (actionTypeGroupName, actionTypeGroupId) not in dataDict.keys():
                                dataDict[(actionTypeGroupName, actionTypeGroupId)] = {}
                            if keyActionType not in dataDict[(actionTypeGroupName, actionTypeGroupId)].keys():
                                dataDict[(actionTypeGroupName, actionTypeGroupId)][keyActionType] = {}
                            if financeName not in dataDict[(actionTypeGroupName, actionTypeGroupId)][keyActionType].keys():
                                dataDict[(actionTypeGroupName, actionTypeGroupId)][keyActionType][financeName] = {}
                            if medicalAidTypeName not in dataDict[(actionTypeGroupName, actionTypeGroupId)][keyActionType][financeName].keys():
                                dataDict[(actionTypeGroupName, actionTypeGroupId)][keyActionType][financeName][medicalAidTypeName] = [0]*2
                            dataDict[(actionTypeGroupName, actionTypeGroupId)][keyActionType][financeName][medicalAidTypeName][0] += amount
                            dataDict[(actionTypeGroupName, actionTypeGroupId)][keyActionType][financeName][medicalAidTypeName][1] += uet
                        elif detailByFinance:
                            if (actionTypeGroupName, actionTypeGroupId) not in dataDict.keys():
                                dataDict[(actionTypeGroupName, actionTypeGroupId)] = {}
                            if keyActionType not in dataDict[(actionTypeGroupName, actionTypeGroupId)].keys():
                                dataDict[(actionTypeGroupName, actionTypeGroupId)][keyActionType] = {}
                            if financeName not in dataDict[(actionTypeGroupName, actionTypeGroupId)][keyActionType].keys():
                                dataDict[(actionTypeGroupName, actionTypeGroupId)][keyActionType][financeName] = [0]*2
                            dataDict[(actionTypeGroupName, actionTypeGroupId)][keyActionType][financeName][0] += amount
                            dataDict[(actionTypeGroupName, actionTypeGroupId)][keyActionType][financeName][1] += uet
                        elif detailByMedicalAidType:
                            if (actionTypeGroupName, actionTypeGroupId) not in dataDict.keys():
                                dataDict[(actionTypeGroupName, actionTypeGroupId)] = {}
                            if keyActionType not in dataDict[(actionTypeGroupName, actionTypeGroupId)].keys():
                                dataDict[(actionTypeGroupName, actionTypeGroupId)][keyActionType] = {}
                            if medicalAidTypeName not in dataDict[(actionTypeGroupName, actionTypeGroupId)][keyActionType].keys():
                                dataDict[(actionTypeGroupName, actionTypeGroupId)][keyActionType][medicalAidTypeName] = [0]*2
                            dataDict[(actionTypeGroupName, actionTypeGroupId)][keyActionType][medicalAidTypeName][0] += amount
                            dataDict[(actionTypeGroupName, actionTypeGroupId)][keyActionType][medicalAidTypeName][1] += uet
                        else:
                            if (actionTypeGroupName, actionTypeGroupId) not in dataDict.keys():
                                dataDict[(actionTypeGroupName, actionTypeGroupId)] = {}
                            if keyActionType not in dataDict[(actionTypeGroupName, actionTypeGroupId)].keys():
                                dataDict[(actionTypeGroupName, actionTypeGroupId)][keyActionType] = [0]*2
                            dataDict[(actionTypeGroupName, actionTypeGroupId)][keyActionType][0] += amount
                            dataDict[(actionTypeGroupName, actionTypeGroupId)][keyActionType][1] += uet
                else: # not detailByActionTypeGroup
                    if detailByOrgStructures:
                        if detailByFinance and detailByMedicalAidType:
                            if orgStructureName not in dataDict.keys():
                                dataDict[orgStructureName] = {}
                            if keyActionType not in dataDict[orgStructureName].keys():
                                dataDict[orgStructureName][keyActionType] = {}
                            if financeName not in dataDict[orgStructureName][keyActionType].keys():
                                dataDict[orgStructureName][keyActionType][financeName] = {}
                            if medicalAidTypeName not in dataDict[orgStructureName][keyActionType][financeName].keys():
                                dataDict[orgStructureName][keyActionType][financeName][medicalAidTypeName] = [0]*2
                            dataDict[orgStructureName][keyActionType][financeName][medicalAidTypeName][0] += amount
                            dataDict[orgStructureName][keyActionType][financeName][medicalAidTypeName][1] += uet
                        elif detailByFinance:
                            if orgStructureName not in dataDict.keys():
                                dataDict[orgStructureName] = {}
                            if keyActionType not in dataDict[orgStructureName].keys():
                                dataDict[orgStructureName][keyActionType] = {}
                            if financeName not in dataDict[orgStructureName][keyActionType].keys():
                                dataDict[orgStructureName][keyActionType][financeName] = [0]*2
                            dataDict[orgStructureName][keyActionType][financeName][0] += amount
                            dataDict[orgStructureName][keyActionType][financeName][1] += uet
                        elif detailByMedicalAidType:
                            if orgStructureName not in dataDict.keys():
                                dataDict[orgStructureName] = {}
                            if keyActionType not in dataDict[orgStructureName].keys():
                                dataDict[orgStructureName][keyActionType] = {}
                            if medicalAidTypeName not in dataDict[orgStructureName][keyActionType].keys():
                                dataDict[orgStructureName][keyActionType][medicalAidTypeName] = [0]*2
                            dataDict[orgStructureName][keyActionType][medicalAidTypeName][0] += amount
                            dataDict[orgStructureName][keyActionType][medicalAidTypeName][1] += uet
                        else:
                            if orgStructureName not in dataDict.keys():
                                dataDict[orgStructureName] = {}
                            if keyActionType not in dataDict[orgStructureName].keys():
                                dataDict[orgStructureName][keyActionType] = [0]*2
                            dataDict[orgStructureName][keyActionType][0] += amount
                            dataDict[orgStructureName][keyActionType][1] += uet
                    else:
                        if detailByFinance and detailByMedicalAidType:
                            if keyActionType not in dataDict.keys():
                                dataDict[keyActionType] = {}
                            if financeName not in dataDict[keyActionType].keys():
                                dataDict[keyActionType][financeName] = {}
                            if medicalAidTypeName not in dataDict[keyActionType][financeName].keys():
                                dataDict[keyActionType][financeName][medicalAidTypeName] = [0]*2
                            dataDict[keyActionType][financeName][medicalAidTypeName][0] += amount
                            dataDict[keyActionType][financeName][medicalAidTypeName][1] += uet
                        elif detailByFinance:
                            if keyActionType not in dataDict.keys():
                                dataDict[keyActionType] = {}
                            if financeName not in dataDict[keyActionType].keys():
                                dataDict[keyActionType][financeName] = [0]*2
                            dataDict[keyActionType][financeName][0] += amount
                            dataDict[keyActionType][financeName][1] += uet
                        elif detailByMedicalAidType:
                            if keyActionType not in dataDict.keys():
                                dataDict[keyActionType] = {}
                            if medicalAidTypeName not in dataDict[keyActionType].keys():
                                dataDict[keyActionType][medicalAidTypeName] = [0]*2
                            dataDict[keyActionType][medicalAidTypeName][0] += amount
                            dataDict[keyActionType][medicalAidTypeName][1] += uet
                        else:
                            if keyActionType not in dataDict.keys():
                                dataDict[keyActionType] = [0]*2
                            dataDict[keyActionType][0] += amount
                            dataDict[keyActionType][1] += uet

        medicalAidTypeList.sort()
        if detailByFinance and detailByMedicalAidType:
            self.tableColumnsLen = ((len(medicalAidTypeList)+1)*2)*(len(financeList)+1)
        elif detailByFinance:
            self.tableColumnsLen = len(financeList)*3
        elif detailByMedicalAidType:
            self.tableColumnsLen = len(medicalAidTypeList)*2
        else:
            self.tableColumnsLen = 2
        if detailByFinance or detailByMedicalAidType:
            detailedWidth = 70.0/(self.tableColumnsLen if self.tableColumnsLen > 0 else 1)
        else:
            detailedWidth = None

        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.setBlockFormat(CReportBase.AlignCenter)
        cursor.insertText(self.title())
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        tableColumns = [
                        ('5%' if detailedWidth else '15%', [u'Код исследования'],           CReportBase.AlignLeft),
                        ('15%' if detailedWidth else '65%', [u'Наименование исследования'], CReportBase.AlignLeft),
                        ]
        amountUETCols = [
                        ('10%', [u'иссл.'], CReportBase.AlignRight),
                        ('10%', [u'УЕТ'],   CReportBase.AlignRight),
                        ]
        if detailByFinance and detailByMedicalAidType:
            for i, financeName in enumerate(financeList):
                k = True
                for j, medicalAidTypeName in enumerate(medicalAidTypeList):
                    if k:
                        tableColumns.append(('%s'%detailedWidth+'%', [financeName, medicalAidTypeName, u'иссл'], CReportBase.AlignCenter))
                        k = False
                    else:
                        tableColumns.append(('%s'%detailedWidth+'%', [u'', medicalAidTypeName, u'иссл'], CReportBase.AlignCenter))
                    tableColumns.append(('%s'%detailedWidth+'%', [u'', u'', u'УЕТ'], CReportBase.AlignCenter))
                tableColumns.append(('%s'%detailedWidth+'%', [u'', u'Итого', u'иссл'], CReportBase.AlignCenter))
                tableColumns.append(('%s'%detailedWidth+'%', [u'', u'', u'УЕТ'], CReportBase.AlignCenter))
            k = True
            for j, medicalAidTypeName in enumerate(medicalAidTypeList):
                if k:
                    tableColumns.append(('%s'%detailedWidth+'%', [u'За счет всех источников', medicalAidTypeName, u'иссл'], CReportBase.AlignCenter))
                    k = False
                else:
                    tableColumns.append(('%s'%detailedWidth+'%', [u'', medicalAidTypeName, u'иссл'], CReportBase.AlignCenter))
                tableColumns.append(('%s'%detailedWidth+'%', [u'', u'', u'УЕТ'], CReportBase.AlignCenter))
            tableColumns.append(('%s'%detailedWidth+'%', [u'', u'Итого', u'иссл'], CReportBase.AlignCenter))
            tableColumns.append(('%s'%detailedWidth+'%', [u'', u'', u'УЕТ'], CReportBase.AlignCenter))
        elif detailByFinance:
            for i, financeName in enumerate(financeList):
                tableColumns.append(('%s'%detailedWidth+'%', [financeName, u'иссл'], CReportBase.AlignCenter))
                tableColumns.append(('%s'%detailedWidth+'%', [u'', u'УЕТ'], CReportBase.AlignCenter))
            tableColumns.append(('%s'%detailedWidth+'%', [u'За счет всех источников', u'иссл'], CReportBase.AlignCenter))
            tableColumns.append(('%s'%detailedWidth+'%', [u'', u'УЕТ'], CReportBase.AlignCenter))
        elif detailByMedicalAidType:
            for i, medicalAidTypeName in enumerate(medicalAidTypeList):
                tableColumns.append(('%s'%detailedWidth+'%', [medicalAidTypeName, u'иссл'], CReportBase.AlignCenter))
                tableColumns.append(('%s'%detailedWidth+'%', [u'', u'УЕТ'], CReportBase.AlignCenter))
        else:
            tableColumns.extend(amountUETCols)

        table = createTable(cursor, tableColumns)
        if detailByFinance and detailByMedicalAidType:
            table.mergeCells(0, 0, 3, 1)
            table.mergeCells(0, 1, 3, 1)
            for i in range(len(financeList)+1):
                lenMedicalCols = 2*len(medicalAidTypeList)+2
                table.mergeCells(0, 2+i*lenMedicalCols, 1, lenMedicalCols)
            for j in range((len(medicalAidTypeList))*len(financeList)*3):
                table.mergeCells(1, 2+2*j, 1, 2)
                table.mergeCells(1, 4+2*j, 1, 2)
        elif detailByFinance:
            table.mergeCells(0, 0, 2, 1)
            table.mergeCells(0, 1, 2, 1)
            for i in range(len(financeList)+2):
                table.mergeCells(0, 2+i*2, 1, 2)
        elif detailByMedicalAidType:
            table.mergeCells(0, 0, 2, 1)
            table.mergeCells(0, 1, 2, 1)
            for j in range(len(medicalAidTypeList)+1):
                table.mergeCells(0, 2+j*2, 1, 2)
                table.mergeCells(0, 4+j*2, 1, 2)
        self.groupingRange = table.table.columns()-2

        totalReport = [0]*len(tableColumns)
        dataActionClassName = [u'Статус', u'Диагностика', u'Лечение', u'Прочие мероприятия']
        if detailByActionTypeClasses:
            if detailByActionTypeGroup:
                if detailByFinance and detailByMedicalAidType:
                    if detailByOrgStructures:
                        totalByLPU = [0]*(self.tableColumnsLen+4)
                        for o, orgStructureName in enumerate(orgStructureList):
                            totalByOrgStructure = [0]*(self.tableColumnsLen+4)
                            f = table.addRow()
                            i = f
                            table.setText(f, 0, orgStructureName, CReportBase.TableTotal, blockFormat=CReportBase.AlignCenter)
                            table.mergeCells(f, 0,  1, self.tableColumnsLen+4)
                            dataActionClassDict = dataDict[orgStructureName]
                            dataActionClassKeys = dataActionClassDict.keys()
                            dataActionClassKeys.sort()
                            for actionTypeClass in dataActionClassKeys:
                                classI = table.addRow()
                                totalClass = [0]*(self.tableColumnsLen+4)
                                table.setText(classI, 0, dataActionClassName[actionTypeClass], CReportBase.TableTotal)
                                table.mergeCells(classI, 0,  1, 2)
                                dataActionGroupDict = dataDict[orgStructureName][actionTypeClass]
                                dataActionGroupKeys = dataActionGroupDict.keys()
                                dataActionGroupKeys.sort(key=lambda x: x[0])
                                for actionTypeGroup in dataActionGroupKeys:
                                    actionTypeGroupName, actionTypeGroupId = actionTypeGroup
                                    groupI = table.addRow()
                                    totalGroup = [0]*(self.tableColumnsLen+4)
                                    table.setText(groupI, 0, actionTypeGroup[0], CReportBase.TableTotal)
                                    table.mergeCells(groupI, 0,  1, 2)
                                    dataActionTypeDict = dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)]
                                    dataActionTypeKeys = dataActionTypeDict.keys()
                                    dataActionTypeKeys.sort(key=lambda x: x[1])
                                    for dataActionTypeKey in dataActionTypeKeys:
                                        actionTypeId, actionTypeInfo = dataActionTypeKey
                                        i = table.addRow()
                                        table.setText(i, 0, actionTypeInfo[0])
                                        table.setText(i, 1, actionTypeInfo[1])
                                        totalFinance = {}
                                        totallyTotalFinance = [0]*2
                                        for f, financeName in enumerate(financeList):
                                            total = [0]*2
                                            for j, medicalAidTypeName in enumerate(medicalAidTypeList):
                                                table.setText(i, 2+2*j+f*lenMedicalCols, dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0])
                                                totalByOrgStructure[2+2*j+f*lenMedicalCols] += dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0]
                                                table.setText(i, 3+2*j+f*lenMedicalCols, forceStringEx(dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                                totalByOrgStructure[3+2*j+f*lenMedicalCols] += dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]
                                                totalClass[2+2*j+f*lenMedicalCols] += dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0]
                                                totalClass[3+2*j+f*lenMedicalCols] += dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]
                                                totalGroup[2+2*j+f*lenMedicalCols] += dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0]
                                                totalGroup[3+2*j+f*lenMedicalCols] += dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]
                                                if medicalAidTypeName not in totalFinance.keys():
                                                    totalFinance[medicalAidTypeName] = [0]*2
                                                total[0] += dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0]
                                                total[1] += dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]
                                                totalFinance[medicalAidTypeName][0] += dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0]
                                                totalFinance[medicalAidTypeName][1] += dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]
                                            table.setText(i, 4+2*j+f*lenMedicalCols, total[0])
                                            totalByOrgStructure[4+2*j+f*lenMedicalCols] += total[0]
                                            table.setText(i, 5+2*j+f*lenMedicalCols, forceStringEx(total[1]).replace(QString('.'), QString(',')))
                                            totalByOrgStructure[5+2*j+f*lenMedicalCols] += total[1]
                                            totalClass[4+2*j+f*lenMedicalCols] += total[0]
                                            totalClass[5+2*j+f*lenMedicalCols] += total[1]
                                            totalGroup[4+2*j+f*lenMedicalCols] += total[0]
                                            totalGroup[5+2*j+f*lenMedicalCols] += total[1]
                                        for j, medicalAidTypeName in enumerate(medicalAidTypeList):
                                            table.setText(i, 2+2*j+(f+1)*lenMedicalCols, totalFinance.get(medicalAidTypeName, [0]*2)[0])
                                            totalByOrgStructure[2+2*j+(f+1)*lenMedicalCols] += totalFinance.get(medicalAidTypeName, [0]*2)[0]
                                            table.setText(i, 3+2*j+(f+1)*lenMedicalCols, forceStringEx(totalFinance.get(medicalAidTypeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                            totalByOrgStructure[3+2*j+(f+1)*lenMedicalCols] += totalFinance.get(medicalAidTypeName, [0]*2)[1]
                                            totalClass[2+2*j+(f+1)*lenMedicalCols] += totalFinance.get(medicalAidTypeName, [0]*2)[0]
                                            totalClass[3+2*j+(f+1)*lenMedicalCols] += totalFinance.get(medicalAidTypeName, [0]*2)[1]
                                            totalGroup[2+2*j+(f+1)*lenMedicalCols] += totalFinance.get(medicalAidTypeName, [0]*2)[0]
                                            totalGroup[3+2*j+(f+1)*lenMedicalCols] += totalFinance.get(medicalAidTypeName, [0]*2)[1]
                                            totallyTotalFinance[0] += totalFinance.get(medicalAidTypeName, [0]*2)[0]
                                            totallyTotalFinance[1] += totalFinance.get(medicalAidTypeName, [0]*2)[1]
                                        table.setText(i, 4+2*j+(f+1)*lenMedicalCols, totallyTotalFinance[0])
                                        totalByOrgStructure[4+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[0]
                                        table.setText(i, 5+2*j+(f+1)*lenMedicalCols, forceStringEx(totallyTotalFinance[1]).replace(QString('.'), QString(',')))
                                        totalByOrgStructure[5+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[1]
                                        totalClass[4+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[0]
                                        totalClass[5+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[1]
                                        totalGroup[4+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[0]
                                        totalGroup[5+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[1]
                                    for t in range(self.groupingRange):
                                        table.setText(groupI, t+2, forceStringEx(totalGroup[t+2]).replace(QString('.'), QString(',')), CReportBase.TableTotal)
                                for t in range(self.groupingRange):
                                    table.setText(classI, t+2, forceStringEx(totalClass[t+2]).replace(QString('.'), QString(',')), CReportBase.TableTotal)
                            i = table.addRow()
                            table.setText(i, 0, u'Итого по подразделению %s'%(orgStructureName), CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                            table.mergeCells(i, 0,  1, 2)
                            for t in range(self.groupingRange):
                                table.setText(i, t+2, forceStringEx(totalByOrgStructure[t+2]).replace(QString('.'), QString(',')))
                                totalByLPU[t] += totalByOrgStructure[t+2]
                        i = table.addRow()
                        table.setText(i, 0, u'ИТОГО', CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                        table.mergeCells(i, 0,  1, 2)
                        for t in range(self.groupingRange):
                            table.setText(i, t+2, forceStringEx(totalByLPU[t]).replace(QString('.'), QString(',')))
                    else:
                        dataActionClassDict = dataDict
                        dataActionClassKeys = dataActionClassDict.keys()
                        dataActionClassKeys.sort()
                        for actionTypeClass in dataActionClassKeys:
                            classI = table.addRow()
                            totalClass = [0]*(self.tableColumnsLen+4)
                            table.setText(classI, 0, dataActionClassName[actionTypeClass], CReportBase.TableTotal)
                            table.mergeCells(classI, 0,  1, 2)
                            dataActionGroupDict = dataDict[actionTypeClass]
                            dataActionGroupKeys = dataActionGroupDict.keys()
                            dataActionGroupKeys.sort(key=lambda x: x[0])
                            for actionTypeGroup in dataActionGroupKeys:
                                actionTypeGroupName, actionTypeGroupId = actionTypeGroup
                                groupI = table.addRow()
                                totalGroup = [0]*(self.tableColumnsLen+4)
                                table.setText(groupI, 0, actionTypeGroup[0], CReportBase.TableTotal)
                                table.mergeCells(groupI, 0,  1, 2)
                                dataActionTypeDict = dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)]
                                dataActionTypeKeys = dataActionTypeDict.keys()
                                dataActionTypeKeys.sort(key=lambda x: x[1])
                                for dataActionTypeKey in dataActionTypeKeys:
                                    actionTypeId, actionTypeInfo = dataActionTypeKey
                                    i = table.addRow()
                                    table.setText(i, 0, actionTypeInfo[0])
                                    table.setText(i, 1, forceStringEx(actionTypeInfo[1]).replace(QString('.'), QString(',')))
                                    totalFinance = {}
                                    totallyTotalFinance = [0]*2
                                    for f, financeName in enumerate(financeList):
                                        total = [0]*2
                                        for j, medicalAidTypeName in enumerate(medicalAidTypeList):
                                            table.setText(i, 2+2*j+f*lenMedicalCols, dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0])
                                            table.setText(i, 3+2*j+f*lenMedicalCols, forceStringEx(dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                            totalClass[2+2*j+f*lenMedicalCols] += dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0]
                                            totalClass[3+2*j+f*lenMedicalCols] += dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]
                                            totalGroup[2+2*j+f*lenMedicalCols] += dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0]
                                            totalGroup[3+2*j+f*lenMedicalCols] += dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]
                                            totalReport[2+2*j+f*lenMedicalCols] += dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0]
                                            totalReport[3+2*j+f*lenMedicalCols] += dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]
                                            if medicalAidTypeName not in totalFinance.keys():
                                                totalFinance[medicalAidTypeName] = [0]*2
                                            total[0] += dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0]
                                            total[1] += dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]
                                            totalFinance[medicalAidTypeName][0] += dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0]
                                            totalFinance[medicalAidTypeName][1] += dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]
                                        table.setText(i, 4+2*j+f*lenMedicalCols, total[0])
                                        table.setText(i, 5+2*j+f*lenMedicalCols, forceStringEx(total[1]).replace(QString('.'), QString(',')))
                                        totalClass[4+2*j+f*lenMedicalCols] += total[0]
                                        totalClass[5+2*j+f*lenMedicalCols] += total[1]
                                        totalGroup[4+2*j+f*lenMedicalCols] += total[0]
                                        totalGroup[5+2*j+f*lenMedicalCols] += total[1]
                                        totalReport[4+2*j+f*lenMedicalCols] += total[0]
                                        totalReport[5+2*j+f*lenMedicalCols] += total[1]
                                    for j, medicalAidTypeName in enumerate(medicalAidTypeList):
                                        table.setText(i, 2+2*j+(f+1)*lenMedicalCols, totalFinance.get(medicalAidTypeName, [0]*2)[0])
                                        table.setText(i, 3+2*j+(f+1)*lenMedicalCols, forceStringEx(totalFinance.get(medicalAidTypeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                        totallyTotalFinance[0] += totalFinance.get(medicalAidTypeName, [0]*2)[0]
                                        totallyTotalFinance[1] += totalFinance.get(medicalAidTypeName, [0]*2)[1]
                                        totalReport[2+2*j+(f+1)*lenMedicalCols] += totalFinance.get(medicalAidTypeName, [0]*2)[0]
                                        totalReport[3+2*j+(f+1)*lenMedicalCols] += totalFinance.get(medicalAidTypeName, [0]*2)[1]
                                    table.setText(i, 4+2*j+(f+1)*lenMedicalCols, totallyTotalFinance[0])
                                    table.setText(i, 5+2*j+(f+1)*lenMedicalCols, forceStringEx(totallyTotalFinance[1]).replace(QString('.'), QString(',')))
                                    totalClass[4+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[0]
                                    totalClass[5+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[1]
                                    totalGroup[4+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[0]
                                    totalGroup[5+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[1]
                                    totalReport[4+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[0]
                                    totalReport[5+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[1]
                                for t in range(self.groupingRange):
                                    table.setText(groupI, t+2, forceStringEx(totalGroup[t+2]).replace(QString('.'), QString(',')), CReportBase.TableTotal)
                            for t in range(self.groupingRange):
                                table.setText(classI, t+2, forceStringEx(totalClass[t+2]).replace(QString('.'), QString(',')), CReportBase.TableTotal)
                elif detailByFinance:
                    if detailByOrgStructures:
                        totalByLPU = [0]*(self.tableColumnsLen+4)
                        for o, orgStructureName in enumerate(orgStructureList):
                            totalByOrgStructure = [0]*(self.tableColumnsLen+4)
                            f = table.addRow()
                            i = f
                            table.setText(f, 0, orgStructureName, CReportBase.TableTotal, blockFormat=CReportBase.AlignCenter)
                            table.mergeCells(f, 0,  1, self.tableColumnsLen+4)
                            dataActionClassDict = dataDict[orgStructureName]
                            dataActionClassKeys = dataActionClassDict.keys()
                            dataActionClassKeys.sort()
                            for actionTypeClass in dataActionClassKeys:
                                classI = table.addRow()
                                totalClass = [0]*(self.tableColumnsLen+4)
                                table.setText(classI, 0, dataActionClassName[actionTypeClass], CReportBase.TableTotal)
                                table.mergeCells(classI, 0,  1, 2)
                                dataActionGroupDict = dataDict[orgStructureName][actionTypeClass]
                                dataActionGroupKeys = dataActionGroupDict.keys()
                                dataActionGroupKeys.sort(key=lambda x: x[0])
                                for actionTypeGroup in dataActionGroupKeys:
                                    actionTypeGroupName, actionTypeGroupId = actionTypeGroup
                                    groupI = table.addRow()
                                    totalGroup = [0]*(self.tableColumnsLen+4)
                                    table.setText(groupI, 0, actionTypeGroup[0], CReportBase.TableTotal)
                                    table.mergeCells(groupI, 0,  1, 2)
                                    dataActionTypeDict = dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)]
                                    dataActionTypeKeys = dataActionTypeDict.keys()
                                    dataActionTypeKeys.sort(key=lambda x: x[1])
                                    for dataActionTypeKey in dataActionTypeKeys:
                                        actionTypeId, actionTypeInfo = dataActionTypeKey
                                        i = table.addRow()
                                        total = [0]*2
                                        table.setText(i, 0, actionTypeInfo[0])
                                        table.setText(i, 1, forceStringEx(actionTypeInfo[1]).replace(QString('.'), QString(',')))
                                        for fi, financeName in enumerate(financeList):
                                            table.setText(i, 2+fi*2, dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, [0]*2)[0])
                                            totalByOrgStructure[2+fi*2] += dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, [0]*2)[0]
                                            table.setText(i, 3+fi*2, forceStringEx(dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                            totalByOrgStructure[3+fi*2] += dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, [0]*2)[1]
                                            total[0] += dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, [0]*2)[0]
                                            total[1] += dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, [0]*2)[1]
                                            totalClass[2+fi*2] += dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, [0]*2)[0]
                                            totalClass[3+fi*2] += dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, [0]*2)[1]
                                            totalGroup[2+fi*2] += dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, [0]*2)[0]
                                            totalGroup[3+fi*2] += dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, [0]*2)[1]
                                        fi += 1
                                        table.setText(i, 2+fi*2, total[0])
                                        totalByOrgStructure[2+fi*2] += total[0]
                                        table.setText(i, 3+fi*2, forceStringEx(total[1]).replace(QString('.'), QString(',')))
                                        totalByOrgStructure[3+fi*2] += total[1]
                                        totalClass[2+fi*2] += total[0]
                                        totalClass[3+fi*2] += total[1]
                                        totalGroup[2+fi*2] += total[0]
                                        totalGroup[3+fi*2] += total[1]
                                    for t in range(self.groupingRange):
                                        table.setText(groupI, t+2, forceStringEx(totalGroup[t+2]).replace(QString('.'), QString(',')), CReportBase.TableTotal)
                                for t in range(self.groupingRange):
                                    table.setText(classI, t+2, forceStringEx(totalClass[t+2]).replace(QString('.'), QString(',')), CReportBase.TableTotal)
                            i = table.addRow()
                            table.setText(i, 0, u'Итого по подразделению %s'%(orgStructureName), CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                            table.mergeCells(i, 0,  1, 2)
                            for t in range(self.groupingRange):
                                table.setText(i, t+2, forceStringEx(totalByOrgStructure[t+2]).replace(QString('.'), QString(',')))
                                totalByLPU[t] += totalByOrgStructure[t+2]
                        i = table.addRow()
                        table.setText(i, 0, u'ИТОГО', CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                        table.mergeCells(i, 0,  1, 2)
                        for t in range(self.groupingRange):
                            table.setText(i, t+2, forceStringEx(totalByLPU[t]).replace(QString('.'), QString(',')))
                    else:
                        dataActionClassDict = dataDict
                        dataActionClassKeys = dataActionClassDict.keys()
                        dataActionClassKeys.sort()
                        for actionTypeClass in dataActionClassKeys:
                            classI = table.addRow()
                            totalClass = [0]*(self.tableColumnsLen+4)
                            table.setText(classI, 0, dataActionClassName[actionTypeClass], CReportBase.TableTotal)
                            table.mergeCells(classI, 0,  1, 2)
                            dataActionGroupDict = dataDict[actionTypeClass]
                            dataActionGroupKeys = dataActionGroupDict.keys()
                            dataActionGroupKeys.sort(key=lambda x: x[0])
                            for actionTypeGroup in dataActionGroupKeys:
                                actionTypeGroupName, actionTypeGroupId = actionTypeGroup
                                groupI = table.addRow()
                                totalGroup = [0]*(self.tableColumnsLen+4)
                                table.setText(groupI, 0, actionTypeGroup[0], CReportBase.TableTotal)
                                table.mergeCells(groupI, 0,  1, 2)
                                dataActionTypeDict = dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)]
                                dataActionTypeKeys = dataActionTypeDict.keys()
                                dataActionTypeKeys.sort(key=lambda x: x[1])
                                for dataActionTypeKey in dataActionTypeKeys:
                                    actionTypeId, actionTypeInfo = dataActionTypeKey
                                    i = table.addRow()
                                    total = [0]*2
                                    table.setText(i, 0, actionTypeInfo[0])
                                    table.setText(i, 1, forceStringEx(actionTypeInfo[1]).replace(QString('.'), QString(',')))
                                    for f, financeName in enumerate(financeList):
                                        table.setText(i, 2+f*2, dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, [0]*2)[0])
                                        table.setText(i, 3+f*2, forceStringEx(dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                        total[0] += dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, [0]*2)[0]
                                        total[1] += dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, [0]*2)[1]
                                        totalClass[2+f*2] += dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, [0]*2)[0]
                                        totalClass[3+f*2] += dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, [0]*2)[1]
                                        totalGroup[2+f*2] += dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, [0]*2)[0]
                                        totalGroup[3+f*2] += dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, [0]*2)[1]
                                        totalReport[2+f*2] += dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, [0]*2)[0]
                                        totalReport[3+f*2] += dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, [0]*2)[1]
                                    table.setText(i, 4+f*2, total[0])
                                    table.setText(i, 5+f*2, forceStringEx(total[1]).replace(QString('.'), QString(',')))
                                    totalClass[4+f*2] += total[0]
                                    totalClass[5+f*2] += total[1]
                                    totalGroup[4+f*2] += total[0]
                                    totalGroup[5+f*2] += total[1]
                                    totalReport[4+f*2] += total[0]
                                    totalReport[5+f*2] += total[1]
                                for t in range(self.groupingRange):
                                    table.setText(groupI, t+2, forceStringEx(totalGroup[t+2]).replace(QString('.'), QString(',')), CReportBase.TableTotal)
                            for t in range(self.groupingRange):
                                table.setText(classI, t+2, forceStringEx(totalClass[t+2]).replace(QString('.'), QString(',')), CReportBase.TableTotal)
                elif detailByMedicalAidType:
                    if detailByOrgStructures:
                        totalByLPU = [0]*(self.tableColumnsLen+4)
                        for o, orgStructureName in enumerate(orgStructureList):
                            totalByOrgStructure = [0]*(self.tableColumnsLen+4)
                            f = table.addRow()
                            i = f
                            table.setText(f, 0, orgStructureName, CReportBase.TableTotal, blockFormat=CReportBase.AlignCenter)
                            table.mergeCells(f, 0,  1, self.tableColumnsLen+4)
                            dataActionClassDict = dataDict[orgStructureName]
                            dataActionClassKeys = dataActionClassDict.keys()
                            dataActionClassKeys.sort()
                            for actionTypeClass in dataActionClassKeys:
                                classI = table.addRow()
                                totalClass = [0]*(self.tableColumnsLen+4)
                                table.setText(classI, 0, dataActionClassName[actionTypeClass], CReportBase.TableTotal)
                                table.mergeCells(classI, 0,  1, 2)
                                dataActionGroupDict = dataDict[orgStructureName][actionTypeClass]
                                dataActionGroupKeys = dataActionGroupDict.keys()
                                dataActionGroupKeys.sort(key=lambda x: x[0])
                                for actionTypeGroup in dataActionGroupKeys:
                                    actionTypeGroupName, actionTypeGroupId = actionTypeGroup
                                    groupI = table.addRow()
                                    totalGroup = [0]*(self.tableColumnsLen+4)
                                    table.setText(groupI, 0, actionTypeGroup[0], CReportBase.TableTotal)
                                    table.mergeCells(groupI, 0,  1, 2)
                                    dataActionTypeDict = dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)]
                                    dataActionTypeKeys = dataActionTypeDict.keys()
                                    dataActionTypeKeys.sort(key=lambda x: x[1])
                                    for dataActionTypeKey in dataActionTypeKeys:
                                        actionTypeId, actionTypeInfo = dataActionTypeKey
                                        i = table.addRow()
                                        table.setText(i, 0, actionTypeInfo[0])
                                        table.setText(i, 1, forceStringEx(actionTypeInfo[1]).replace(QString('.'), QString(',')))
                                        for m, medicalAidTypeName in enumerate(medicalAidTypeList):
                                            table.setText(i, 2+m*2, dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[0])
                                            totalByOrgStructure[2+m*2] += dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[0]
                                            table.setText(i, 3+m*2, forceStringEx(dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                            totalByOrgStructure[3+m*2] += dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[1]
                                            totalClass[2+m*2] += dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[0]
                                            totalClass[3+m*2] += dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[1]
                                            totalGroup[2+m*2] += dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[0]
                                            totalGroup[3+m*2] += dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[1]
                                    for t in range(self.groupingRange):
                                        table.setText(groupI, t+2, forceStringEx(totalGroup[t+2]).replace(QString('.'), QString(',')), CReportBase.TableTotal)
                                for t in range(self.groupingRange):
                                    table.setText(classI, t+2, forceStringEx(totalClass[t+2]).replace(QString('.'), QString(',')), CReportBase.TableTotal)
                            i = table.addRow()
                            table.setText(i, 0, u'Итого по подразделению %s'%(orgStructureName), CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                            table.mergeCells(i, 0,  1, 2)
                            for t in range(self.groupingRange):
                                table.setText(i, t+2, forceStringEx(totalByOrgStructure[t+2]).replace(QString('.'), QString(',')))
                                totalByLPU[t] += totalByOrgStructure[t+2]
                        i = table.addRow()
                        table.setText(i, 0, u'ИТОГО', CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                        table.mergeCells(i, 0,  1, 2)
                        for t in range(self.groupingRange):
                            table.setText(i, t+2, forceStringEx(totalByLPU[t]).replace(QString('.'), QString(',')))
                    else:
                        dataActionClassDict = dataDict
                        dataActionClassKeys = dataActionClassDict.keys()
                        dataActionClassKeys.sort()
                        for actionTypeClass in dataActionClassKeys:
                            classI = table.addRow()
                            totalClass = [0]*(self.tableColumnsLen+4)
                            table.setText(classI, 0, dataActionClassName[actionTypeClass], CReportBase.TableTotal)
                            table.mergeCells(classI, 0,  1, 2)
                            dataActionGroupDict = dataDict[actionTypeClass]
                            dataActionGroupKeys = dataActionGroupDict.keys()
                            dataActionGroupKeys.sort(key=lambda x: x[0])
                            for actionTypeGroup in dataActionGroupKeys:
                                actionTypeGroupName, actionTypeGroupId = actionTypeGroup
                                groupI = table.addRow()
                                totalGroup = [0]*(self.tableColumnsLen+4)
                                table.setText(groupI, 0, actionTypeGroup[0], CReportBase.TableTotal)
                                table.mergeCells(groupI, 0,  1, 2)
                                dataActionTypeDict = dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)]
                                dataActionTypeKeys = dataActionTypeDict.keys()
                                dataActionTypeKeys.sort(key=lambda x: x[1])
                                for dataActionTypeKey in dataActionTypeKeys:
                                    actionTypeId, actionTypeInfo = dataActionTypeKey
                                    i = table.addRow()
                                    table.setText(i, 0, actionTypeInfo[0])
                                    table.setText(i, 1, forceStringEx(actionTypeInfo[1]).replace(QString('.'), QString(',')))
                                    for m, medicalAidTypeName in enumerate(medicalAidTypeList):
                                        table.setText(i, 2+m*2, dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[0])
                                        table.setText(i, 3+m*2, forceStringEx(dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                        totalClass[2+m*2] += dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[0]
                                        totalClass[3+m*2] += dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[1]
                                        totalGroup[2+m*2] += dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[0]
                                        totalGroup[3+m*2] += dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[1]
                                        totalReport[2+m*2] += dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[0]
                                        totalReport[3+m*2] += dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[1]
                                for t in range(self.groupingRange):
                                    table.setText(groupI, t+2, forceStringEx(totalGroup[t+2]).replace(QString('.'), QString(',')), CReportBase.TableTotal)
                            for t in range(self.groupingRange):
                                table.setText(classI, t+2, forceStringEx(totalClass[t+2]).replace(QString('.'), QString(',')), CReportBase.TableTotal)
                else:
                    if detailByOrgStructures:
                        totalByLPU = [0]*(self.tableColumnsLen+4)
                        for o, orgStructureName in enumerate(orgStructureList):
                            totalByOrgStructure = [0]*(self.tableColumnsLen+4)
                            f = table.addRow()
                            i = f
                            table.setText(f, 0, orgStructureName, CReportBase.TableTotal, blockFormat=CReportBase.AlignCenter)
                            table.mergeCells(f, 0,  1, self.tableColumnsLen+2)
                            dataActionClassDict = dataDict[orgStructureName]
                            dataActionClassKeys = dataActionClassDict.keys()
                            dataActionClassKeys.sort()
                            for actionTypeClass in dataActionClassKeys:
                                classI = table.addRow()
                                totalClass = [0]*(self.tableColumnsLen+4)
                                table.setText(classI, 0, dataActionClassName[actionTypeClass], CReportBase.TableTotal)
                                table.mergeCells(classI, 0,  1, 2)
                                dataActionGroupDict = dataDict[orgStructureName][actionTypeClass]
                                dataActionGroupKeys = dataActionGroupDict.keys()
                                dataActionGroupKeys.sort(key=lambda x: x[0])
                                for actionTypeGroup in dataActionGroupKeys:
                                    actionTypeGroupName, actionTypeGroupId = actionTypeGroup
                                    groupI = table.addRow()
                                    totalGroup = [0]*(self.tableColumnsLen+4)
                                    table.setText(groupI, 0, actionTypeGroup[0], CReportBase.TableTotal)
                                    table.mergeCells(groupI, 0,  1, 2)
                                    dataActionTypeDict = dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)]
                                    dataActionTypeKeys = dataActionTypeDict.keys()
                                    dataActionTypeKeys.sort(key=lambda x: x[1])
                                    for dataActionTypeKey in dataActionTypeKeys:
                                        actionTypeId, actionTypeInfo = dataActionTypeKey
                                        i = table.addRow()
                                        table.setText(i, 0, actionTypeInfo[0])
                                        table.setText(i, 1, actionTypeInfo[1])
                                        table.setText(i, 2, dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey][0])
                                        totalByOrgStructure[2] += dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey][0]
                                        table.setText(i, 3, forceStringEx(dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey][1]).replace(QString('.'), QString(',')))
                                        totalByOrgStructure[3] += dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey][1]
                                        totalClass[2] += dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey][0]
                                        totalClass[3] += dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey][1]
                                        totalGroup[2] += dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey][0]
                                        totalGroup[3] += dataDict[orgStructureName][actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey][1]
                                    i = table.addRow()
                                    table.setText(i, 0, u'Итого по подразделению %s'%(orgStructureName), CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                                    table.mergeCells(i, 0,  1, 2)
                                    for t in range(self.groupingRange):
                                        table.setText(i, t+2, forceStringEx(totalByOrgStructure[t+2]).replace(QString('.'), QString(',')))
                                        totalByLPU[t] += totalByOrgStructure[t+2]
                                    for t in range(self.groupingRange):
                                        table.setText(groupI, t+2, forceStringEx(totalGroup[t+2]).replace(QString('.'), QString(',')), CReportBase.TableTotal)
                                for t in range(self.groupingRange):
                                    table.setText(classI, t+2, forceStringEx(totalClass[t+2]).replace(QString('.'), QString(',')), CReportBase.TableTotal)
                        i = table.addRow()
                        table.setText(i, 0, u'ИТОГО', CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                        table.mergeCells(i, 0,  1, 2)
                        for t in range(self.groupingRange):
                            table.setText(i, t+2, forceStringEx(totalByLPU[t]).replace(QString('.'), QString(',')))
                    else:
                        dataActionClassDict = dataDict
                        dataActionClassKeys = dataActionClassDict.keys()
                        dataActionClassKeys.sort()
                        for actionTypeClass in dataActionClassKeys:
                            classI = table.addRow()
                            totalClass = [0]*(self.tableColumnsLen+4)
                            table.setText(classI, 0, dataActionClassName[actionTypeClass], CReportBase.TableTotal)
                            table.mergeCells(classI, 0,  1, 2)
                            dataActionGroupDict = dataDict[actionTypeClass]
                            dataActionGroupKeys = dataActionGroupDict.keys()
                            dataActionGroupKeys.sort(key=lambda x: x[0])
                            for actionTypeGroup in dataActionGroupKeys:
                                actionTypeGroupName, actionTypeGroupId = actionTypeGroup
                                groupI = table.addRow()
                                totalGroup = [0]*(self.tableColumnsLen+4)
                                table.setText(groupI, 0, actionTypeGroup[0], CReportBase.TableTotal)
                                table.mergeCells(groupI, 0,  1, 2)
                                dataActionTypeDict = dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)]
                                dataActionTypeKeys = dataActionTypeDict.keys()
                                dataActionTypeKeys.sort(key=lambda x: x[1])
                                for dataActionTypeKey in dataActionTypeKeys:
                                    actionTypeId, actionTypeInfo = dataActionTypeKey
                                    i = table.addRow()
                                    table.setText(i, 0, actionTypeInfo[0])
                                    table.setText(i, 1, actionTypeInfo[1])
                                    table.setText(i, 2, dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey][0])
                                    table.setText(i, 3, forceStringEx(dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey][1]).replace(QString('.'), QString(',')))
                                    totalClass[2] += dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey][0]
                                    totalClass[3] += dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey][1]
                                    totalGroup[2] += dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey][0]
                                    totalGroup[3] += dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey][1]
                                    totalReport[2] += dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey][0]
                                    totalReport[3] += dataDict[actionTypeClass][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey][1]
                                for t in range(self.groupingRange):
                                    table.setText(groupI, t+2, forceStringEx(totalGroup[t+2]).replace(QString('.'), QString(',')), CReportBase.TableTotal)
                            for t in range(self.groupingRange):
                                table.setText(classI, t+2, forceStringEx(totalClass[t+2]).replace(QString('.'), QString(',')), CReportBase.TableTotal)
            else: # not detailByActionTypeGroup
                if detailByFinance and detailByMedicalAidType:
                    if detailByOrgStructures:
                        totalByLPU = [0]*(self.tableColumnsLen+4)
                        for o, orgStructureName in enumerate(orgStructureList):
                            totalByOrgStructure = [0]*(self.tableColumnsLen+4)
                            f = table.addRow()
                            i = f
                            table.setText(f, 0, orgStructureName, CReportBase.TableTotal, blockFormat=CReportBase.AlignCenter)
                            table.mergeCells(f, 0,  1, self.tableColumnsLen+4)
                            dataActionClassDict = dataDict[orgStructureName]
                            dataActionClassKeys = dataActionClassDict.keys()
                            dataActionClassKeys.sort()
                            for actionTypeClass in dataActionClassKeys:
                                classI = table.addRow()
                                totalClass = [0]*(self.tableColumnsLen+4)
                                table.setText(classI, 0, dataActionClassName[actionTypeClass], CReportBase.TableTotal)
                                table.mergeCells(classI, 0,  1, 2)
                                dataActionTypeDict = dataDict[orgStructureName][actionTypeClass]
                                dataActionTypeKeys = dataActionTypeDict.keys()
                                dataActionTypeKeys.sort(key=lambda x: x[1])
                                for dataActionTypeKey in dataActionTypeKeys:
                                    actionTypeId, actionTypeInfo = dataActionTypeKey
                                    i = table.addRow()
                                    table.setText(i, 0, actionTypeInfo[0])
                                    table.setText(i, 1, actionTypeInfo[1])
                                    totalFinance = {}
                                    totallyTotalFinance = [0]*2
                                    for f, financeName in enumerate(financeList):
                                        total = [0]*2
                                        for j, medicalAidTypeName in enumerate(medicalAidTypeList):
                                            table.setText(i, 2+2*j+f*lenMedicalCols, dataDict[orgStructureName][actionTypeClass][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0])
                                            totalByOrgStructure[2+2*j+f*lenMedicalCols] += dataDict[orgStructureName][actionTypeClass][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0]
                                            table.setText(i, 3+2*j+f*lenMedicalCols, forceStringEx(dataDict[orgStructureName][actionTypeClass][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                            totalByOrgStructure[3+2*j+f*lenMedicalCols] += dataDict[orgStructureName][actionTypeClass][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]
                                            totalClass[2+2*j+f*lenMedicalCols] += dataDict[orgStructureName][actionTypeClass][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0]
                                            totalClass[3+2*j+f*lenMedicalCols] += dataDict[orgStructureName][actionTypeClass][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]
                                            if medicalAidTypeName not in totalFinance.keys():
                                                totalFinance[medicalAidTypeName] = [0]*2
                                            total[0] += dataDict[orgStructureName][actionTypeClass][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0]
                                            total[1] += dataDict[orgStructureName][actionTypeClass][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]
                                            totalFinance[medicalAidTypeName][0] += dataDict[orgStructureName][actionTypeClass][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0]
                                            totalFinance[medicalAidTypeName][1] += dataDict[orgStructureName][actionTypeClass][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]
                                        table.setText(i, 4+2*j+f*lenMedicalCols, total[0])
                                        totalByOrgStructure[4+2*j+f*lenMedicalCols] += total[0]
                                        table.setText(i, 5+2*j+f*lenMedicalCols, forceStringEx(total[1]).replace(QString('.'), QString(',')))
                                        totalByOrgStructure[5+2*j+f*lenMedicalCols] += total[1]
                                        totalClass[4+2*j+f*lenMedicalCols] += total[0]
                                        totalClass[5+2*j+f*lenMedicalCols] += total[1]
                                    for j, medicalAidTypeName in enumerate(medicalAidTypeList):
                                        table.setText(i, 2+2*j+(f+1)*lenMedicalCols, totalFinance.get(medicalAidTypeName, [0]*2)[0])
                                        totalByOrgStructure[2+2*j+(f+1)*lenMedicalCols] += totalFinance.get(medicalAidTypeName, [0]*2)[0]
                                        table.setText(i, 3+2*j+(f+1)*lenMedicalCols, forceStringEx(totalFinance.get(medicalAidTypeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                        totalByOrgStructure[3+2*j+(f+1)*lenMedicalCols] += totalFinance.get(medicalAidTypeName, [0]*2)[1]
                                        totalClass[2+2*j+(f+1)*lenMedicalCols] += totalFinance.get(medicalAidTypeName, [0]*2)[0]
                                        totalClass[3+2*j+(f+1)*lenMedicalCols] += totalFinance.get(medicalAidTypeName, [0]*2)[1]
                                        totallyTotalFinance[0] += totalFinance.get(medicalAidTypeName, [0]*2)[0]
                                        totallyTotalFinance[1] += totalFinance.get(medicalAidTypeName, [0]*2)[1]
                                    table.setText(i, 4+2*j+(f+1)*lenMedicalCols, totallyTotalFinance[0])
                                    totalByOrgStructure[4+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[0]
                                    table.setText(i, 5+2*j+(f+1)*lenMedicalCols, forceStringEx(totallyTotalFinance[1]).replace(QString('.'), QString(',')))
                                    totalByOrgStructure[5+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[1]
                                    totalClass[4+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[0]
                                    totalClass[5+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[1]
                                for t in range(self.groupingRange):
                                    table.setText(classI, t+2, forceStringEx(totalClass[t+2]).replace(QString('.'), QString(',')), CReportBase.TableTotal)
                            i = table.addRow()
                            table.setText(i, 0, u'Итого по подразделению %s'%(orgStructureName), CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                            table.mergeCells(i, 0,  1, 2)
                            for t in range(self.groupingRange):
                                table.setText(i, t+2, forceStringEx(totalByOrgStructure[t+2]).replace(QString('.'), QString(',')))
                                totalByLPU[t] += totalByOrgStructure[t+2]
                        i = table.addRow()
                        table.setText(i, 0, u'ИТОГО', CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                        table.mergeCells(i, 0,  1, 2)
                        for t in range(self.groupingRange):
                            table.setText(i, t+2, forceStringEx(totalByLPU[t]).replace(QString('.'), QString(',')))
                    else:
                        dataActionClassDict = dataDict
                        dataActionClassKeys = dataActionClassDict.keys()
                        dataActionClassKeys.sort()
                        for actionTypeClass in dataActionClassKeys:
                            classI = table.addRow()
                            totalClass = [0]*(self.tableColumnsLen+4)
                            table.setText(classI, 0, dataActionClassName[actionTypeClass], CReportBase.TableTotal)
                            table.mergeCells(classI, 0,  1, 2)
                            dataActionTypeDict = dataDict[actionTypeClass]
                            dataActionTypeKeys = dataActionTypeDict.keys()
                            dataActionTypeKeys.sort(key=lambda x: x[1])
                            for dataActionTypeKey in dataActionTypeKeys:
                                actionTypeId, actionTypeInfo = dataActionTypeKey
                                i = table.addRow()
                                table.setText(i, 0, actionTypeInfo[0])
                                table.setText(i, 1, forceStringEx(actionTypeInfo[1]).replace(QString('.'), QString(',')))
                                totalFinance = {}
                                totallyTotalFinance = [0]*2
                                for f, financeName in enumerate(financeList):
                                    total = [0]*2
                                    for j, medicalAidTypeName in enumerate(medicalAidTypeList):
                                        table.setText(i, 2+2*j+f*lenMedicalCols, dataDict[actionTypeClass][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0])
                                        table.setText(i, 3+2*j+f*lenMedicalCols, forceStringEx(dataDict[actionTypeClass][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                        totalClass[2+2*j+f*lenMedicalCols] += dataDict[actionTypeClass][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0]
                                        totalClass[3+2*j+f*lenMedicalCols] += dataDict[actionTypeClass][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]
                                        totalReport[2+2*j+f*lenMedicalCols] += dataDict[actionTypeClass][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0]
                                        totalReport[3+2*j+f*lenMedicalCols] += dataDict[actionTypeClass][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]
                                        if medicalAidTypeName not in totalFinance.keys():
                                            totalFinance[medicalAidTypeName] = [0]*2
                                        total[0] += dataDict[actionTypeClass][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0]
                                        total[1] += dataDict[actionTypeClass][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]
                                        totalFinance[medicalAidTypeName][0] += dataDict[actionTypeClass][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0]
                                        totalFinance[medicalAidTypeName][1] += dataDict[actionTypeClass][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]
                                    table.setText(i, 4+2*j+f*lenMedicalCols, total[0])
                                    table.setText(i, 5+2*j+f*lenMedicalCols, forceStringEx(total[1]).replace(QString('.'), QString(',')))
                                    totalClass[4+2*j+f*lenMedicalCols] += total[0]
                                    totalClass[5+2*j+f*lenMedicalCols] += total[1]
                                    totalReport[4+2*j+f*lenMedicalCols] += total[0]
                                    totalReport[5+2*j+f*lenMedicalCols] += total[1]
                                for j, medicalAidTypeName in enumerate(medicalAidTypeList):
                                    table.setText(i, 2+2*j+(f+1)*lenMedicalCols, totalFinance.get(medicalAidTypeName, [0]*2)[0])
                                    table.setText(i, 3+2*j+(f+1)*lenMedicalCols, forceStringEx(totalFinance.get(medicalAidTypeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                    totallyTotalFinance[0] += totalFinance.get(medicalAidTypeName, [0]*2)[0]
                                    totallyTotalFinance[1] += totalFinance.get(medicalAidTypeName, [0]*2)[1]
                                    totalReport[2+2*j+(f+1)*lenMedicalCols] += totalFinance.get(medicalAidTypeName, [0]*2)[0]
                                    totalReport[3+2*j+(f+1)*lenMedicalCols] += totalFinance.get(medicalAidTypeName, [0]*2)[1]
                                table.setText(i, 4+2*j+(f+1)*lenMedicalCols, totallyTotalFinance[0])
                                table.setText(i, 5+2*j+(f+1)*lenMedicalCols, forceStringEx(totallyTotalFinance[1]).replace(QString('.'), QString(',')))
                                totalClass[4+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[0]
                                totalClass[5+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[1]
                                totalReport[4+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[0]
                                totalReport[5+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[1]
                            for t in range(self.groupingRange):
                                    table.setText(classI, t+2, forceStringEx(totalClass[t+2]).replace(QString('.'), QString(',')), CReportBase.TableTotal)
                elif detailByFinance:
                    if detailByOrgStructures:
                        totalByLPU = [0]*(self.tableColumnsLen+4)
                        for o, orgStructureName in enumerate(orgStructureList):
                            totalByOrgStructure = [0]*(self.tableColumnsLen+4)
                            f = table.addRow()
                            i = f
                            table.setText(f, 0, orgStructureName, CReportBase.TableTotal, blockFormat=CReportBase.AlignCenter)
                            table.mergeCells(f, 0,  1, self.tableColumnsLen+4)
                            dataActionClassDict = dataDict[orgStructureName]
                            dataActionClassKeys = dataActionClassDict.keys()
                            dataActionClassKeys.sort()
                            for actionTypeClass in dataActionClassKeys:
                                classI = table.addRow()
                                totalClass = [0]*(self.tableColumnsLen+4)
                                table.setText(classI, 0, dataActionClassName[actionTypeClass], CReportBase.TableTotal)
                                table.mergeCells(classI, 0,  1, 2)
                                dataActionTypeDict = dataDict[orgStructureName][actionTypeClass]
                                dataActionTypeKeys = dataActionTypeDict.keys()
                                dataActionTypeKeys.sort(key=lambda x: x[1])
                                for dataActionTypeKey in dataActionTypeKeys:
                                    actionTypeId, actionTypeInfo = dataActionTypeKey
                                    i = table.addRow()
                                    total = [0]*2
                                    table.setText(i, 0, actionTypeInfo[0])
                                    table.setText(i, 1, forceStringEx(actionTypeInfo[1]).replace(QString('.'), QString(',')))
                                    for fi, financeName in enumerate(financeList):
                                        table.setText(i, 2+fi*2, dataDict[orgStructureName][actionTypeClass][dataActionTypeKey].get(financeName, [0]*2)[0])
                                        totalByOrgStructure[2+fi*2] += dataDict[orgStructureName][actionTypeClass][dataActionTypeKey].get(financeName, [0]*2)[0]
                                        table.setText(i, 3+fi*2, forceStringEx(dataDict[orgStructureName][actionTypeClass][dataActionTypeKey].get(financeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                        totalByOrgStructure[3+fi*2] += dataDict[orgStructureName][actionTypeClass][dataActionTypeKey].get(financeName, [0]*2)[1]
                                        total[0] += dataDict[orgStructureName][actionTypeClass][dataActionTypeKey].get(financeName, [0]*2)[0]
                                        total[1] += dataDict[orgStructureName][actionTypeClass][dataActionTypeKey].get(financeName, [0]*2)[1]
                                        totalClass[2+fi*2] += dataDict[orgStructureName][actionTypeClass][dataActionTypeKey].get(financeName, [0]*2)[0]
                                        totalClass[3+fi*2] += dataDict[orgStructureName][actionTypeClass][dataActionTypeKey].get(financeName, [0]*2)[1]
                                    fi += 1
                                    table.setText(i, 2+fi*2, total[0])
                                    totalByOrgStructure[2+fi*2] += total[0]
                                    table.setText(i, 3+fi*2, forceStringEx(total[1]).replace(QString('.'), QString(',')))
                                    totalByOrgStructure[3+fi*2] += total[1]
                                    totalClass[2+fi*2] += total[0]
                                    totalClass[3+fi*2] += total[1]
                                for t in range(self.groupingRange):
                                    table.setText(classI, t+2, forceStringEx(totalClass[t+2]).replace(QString('.'), QString(',')), CReportBase.TableTotal)
                            i = table.addRow()
                            table.setText(i, 0, u'Итого по подразделению %s'%(orgStructureName), CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                            table.mergeCells(i, 0,  1, 2)
                            for t in range(self.groupingRange):
                                table.setText(i, t+2, forceStringEx(totalByOrgStructure[t+2]).replace(QString('.'), QString(',')))
                                totalByLPU[t] += totalByOrgStructure[t+2]
                        i = table.addRow()
                        table.setText(i, 0, u'ИТОГО', CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                        table.mergeCells(i, 0,  1, 2)
                        for t in range(self.groupingRange):
                            table.setText(i, t+2, forceStringEx(totalByLPU[t]).replace(QString('.'), QString(',')))
                    else:
                        dataActionClassDict = dataDict
                        dataActionClassKeys = dataActionClassDict.keys()
                        dataActionClassKeys.sort()
                        for actionTypeClass in dataActionClassKeys:
                            classI = table.addRow()
                            totalClass = [0]*(self.tableColumnsLen+4)
                            table.setText(classI, 0, dataActionClassName[actionTypeClass], CReportBase.TableTotal)
                            table.mergeCells(classI, 0,  1, 2)
                            dataActionTypeDict = dataDict[actionTypeClass]
                            dataActionTypeKeys = dataActionTypeDict.keys()
                            dataActionTypeKeys.sort(key=lambda x: x[1])
                            for dataActionTypeKey in dataActionTypeKeys:
                                actionTypeId, actionTypeInfo = dataActionTypeKey
                                i = table.addRow()
                                total = [0]*2
                                table.setText(i, 0, actionTypeInfo[0])
                                table.setText(i, 1, forceStringEx(actionTypeInfo[1]).replace(QString('.'), QString(',')))
                                for f, financeName in enumerate(financeList):
                                    table.setText(i, 2+f*2, dataDict[actionTypeClass][dataActionTypeKey].get(financeName, [0]*2)[0])
                                    table.setText(i, 3+f*2, forceStringEx(dataDict[actionTypeClass][dataActionTypeKey].get(financeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                    total[0] += dataDict[actionTypeClass][dataActionTypeKey].get(financeName, [0]*2)[0]
                                    total[1] += dataDict[actionTypeClass][dataActionTypeKey].get(financeName, [0]*2)[1]
                                    totalClass[2+f*2] += dataDict[actionTypeClass][dataActionTypeKey].get(financeName, [0]*2)[0]
                                    totalClass[3+f*2] += dataDict[actionTypeClass][dataActionTypeKey].get(financeName, [0]*2)[1]
                                    totalReport[2+f*2] += dataDict[actionTypeClass][dataActionTypeKey].get(financeName, [0]*2)[0]
                                    totalReport[3+f*2] += dataDict[actionTypeClass][dataActionTypeKey].get(financeName, [0]*2)[1]
                                table.setText(i, 4+f*2, total[0])
                                table.setText(i, 5+f*2, forceStringEx(total[1]).replace(QString('.'), QString(',')))
                                totalClass[4+f*2] += total[0]
                                totalClass[5+f*2] += total[1]
                                totalReport[4+f*2] += total[0]
                                totalReport[5+f*2] += total[1]
                            for t in range(self.groupingRange):
                                table.setText(classI, t+2, forceStringEx(totalClass[t+2]).replace(QString('.'), QString(',')), CReportBase.TableTotal)
                elif detailByMedicalAidType:
                    if detailByOrgStructures:
                        totalByLPU = [0]*(self.tableColumnsLen+4)
                        for o, orgStructureName in enumerate(orgStructureList):
                            totalByOrgStructure = [0]*(self.tableColumnsLen+4)
                            f = table.addRow()
                            i = f
                            table.setText(f, 0, orgStructureName, CReportBase.TableTotal, blockFormat=CReportBase.AlignCenter)
                            table.mergeCells(f, 0,  1, self.tableColumnsLen+4)
                            dataActionClassDict = dataDict[orgStructureName]
                            dataActionClassKeys = dataActionClassDict.keys()
                            dataActionClassKeys.sort()
                            for actionTypeClass in dataActionClassKeys:
                                classI = table.addRow()
                                totalClass = [0]*(self.tableColumnsLen+4)
                                table.setText(classI, 0, dataActionClassName[actionTypeClass], CReportBase.TableTotal)
                                table.mergeCells(classI, 0,  1, 2)
                                dataActionTypeDict = dataDict[orgStructureName][actionTypeClass]
                                dataActionTypeKeys = dataActionTypeDict.keys()
                                dataActionTypeKeys.sort(key=lambda x: x[1])
                                for dataActionTypeKey in dataActionTypeKeys:
                                    actionTypeId, actionTypeInfo = dataActionTypeKey
                                    i = table.addRow()
                                    table.setText(i, 0, actionTypeInfo[0])
                                    table.setText(i, 1, forceStringEx(actionTypeInfo[1]).replace(QString('.'), QString(',')))
                                    for m, medicalAidTypeName in enumerate(medicalAidTypeList):
                                        table.setText(i, 2+m*2, dataDict[orgStructureName][actionTypeClass][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[0])
                                        totalByOrgStructure[2+m*2] += dataDict[orgStructureName][actionTypeClass][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[0]
                                        table.setText(i, 3+m*2, forceStringEx(dataDict[orgStructureName][actionTypeClass][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                        totalByOrgStructure[3+m*2] += dataDict[orgStructureName][actionTypeClass][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[1]
                                        totalClass[2+m*2] += dataDict[orgStructureName][actionTypeClass][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[0]
                                        totalClass[3+m*2] += dataDict[orgStructureName][actionTypeClass][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[1]
                                for t in range(self.groupingRange):
                                    table.setText(classI, t+2, forceStringEx(totalClass[t+2]).replace(QString('.'), QString(',')), CReportBase.TableTotal)
                            i = table.addRow()
                            table.setText(i, 0, u'Итого по подразделению %s'%(orgStructureName), CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                            table.mergeCells(i, 0,  1, 2)
                            for t in range(self.groupingRange):
                                table.setText(i, t+2, forceStringEx(totalByOrgStructure[t+2]).replace(QString('.'), QString(',')))
                                totalByLPU[t] += totalByOrgStructure[t+2]
                        i = table.addRow()
                        table.setText(i, 0, u'ИТОГО', CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                        table.mergeCells(i, 0,  1, 2)
                        for t in range(self.groupingRange):
                            table.setText(i, t+2, forceStringEx(totalByLPU[t]).replace(QString('.'), QString(',')))
                    else:
                        dataActionClassDict = dataDict
                        dataActionClassKeys = dataActionClassDict.keys()
                        dataActionClassKeys.sort()
                        for actionTypeClass in dataActionClassKeys:
                            classI = table.addRow()
                            totalClass = [0]*(self.tableColumnsLen+4)
                            table.setText(classI, 0, dataActionClassName[actionTypeClass], CReportBase.TableTotal)
                            table.mergeCells(classI, 0,  1, 2)
                            dataActionTypeDict = dataDict[actionTypeClass]
                            dataActionTypeKeys = dataActionTypeDict.keys()
                            dataActionTypeKeys.sort(key=lambda x: x[1])
                            for dataActionTypeKey in dataActionTypeKeys:
                                actionTypeId, actionTypeInfo = dataActionTypeKey
                                i = table.addRow()
                                table.setText(i, 0, actionTypeInfo[0])
                                table.setText(i, 1, forceStringEx(actionTypeInfo[1]).replace(QString('.'), QString(',')))
                                for m, medicalAidTypeName in enumerate(medicalAidTypeList):
                                    table.setText(i, 2+m*2, dataDict[actionTypeClass][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[0])
                                    table.setText(i, 3+m*2, forceStringEx(dataDict[actionTypeClass][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                    totalClass[2+m*2] += dataDict[actionTypeClass][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[0]
                                    totalClass[3+m*2] += dataDict[actionTypeClass][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[1]
                                    totalReport[2+m*2] += dataDict[actionTypeClass][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[0]
                                    totalReport[3+m*2] += dataDict[actionTypeClass][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[1]
                            for t in range(self.groupingRange):
                                table.setText(classI, t+2, forceStringEx(totalClass[t+2]).replace(QString('.'), QString(',')), CReportBase.TableTotal)
                else:
                    if detailByOrgStructures:
                        totalByLPU = [0]*(self.tableColumnsLen+4)
                        for o, orgStructureName in enumerate(orgStructureList):
                            totalByOrgStructure = [0]*(self.tableColumnsLen+4)
                            f = table.addRow()
                            i = f
                            table.setText(f, 0, orgStructureName, CReportBase.TableTotal, blockFormat=CReportBase.AlignCenter)
                            table.mergeCells(f, 0,  1, self.tableColumnsLen+2)
                            dataActionClassDict = dataDict[orgStructureName]
                            dataActionClassKeys = dataActionClassDict.keys()
                            dataActionClassKeys.sort()
                            for actionTypeClass in dataActionClassKeys:
                                classI = table.addRow()
                                totalClass = [0]*(self.tableColumnsLen+4)
                                table.setText(classI, 0, dataActionClassName[actionTypeClass], CReportBase.TableTotal)
                                table.mergeCells(classI, 0,  1, 2)
                                dataActionTypeDict = dataDict[orgStructureName][actionTypeClass]
                                dataActionTypeKeys = dataActionTypeDict.keys()
                                dataActionTypeKeys.sort(key=lambda x: x[1])
                                for dataActionTypeKey in dataActionTypeKeys:
                                    actionTypeId, actionTypeInfo = dataActionTypeKey
                                    i = table.addRow()
                                    table.setText(i, 0, actionTypeInfo[0])
                                    table.setText(i, 1, actionTypeInfo[1])
                                    table.setText(i, 2, dataDict[orgStructureName][actionTypeClass][dataActionTypeKey][0])
                                    totalByOrgStructure[2] += dataDict[orgStructureName][actionTypeClass][dataActionTypeKey][0]
                                    table.setText(i, 3, forceStringEx(dataDict[orgStructureName][actionTypeClass][dataActionTypeKey][1]).replace(QString('.'), QString(',')))
                                    totalByOrgStructure[3] += dataDict[orgStructureName][actionTypeClass][dataActionTypeKey][1]
                                    totalClass[2] += dataDict[orgStructureName][actionTypeClass][dataActionTypeKey][0]
                                    totalClass[3] += dataDict[orgStructureName][actionTypeClass][dataActionTypeKey][1]
                                i = table.addRow()
                                table.setText(i, 0, u'Итого по подразделению %s'%(orgStructureName), CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                                table.mergeCells(i, 0,  1, 2)
                                for t in range(self.groupingRange):
                                    table.setText(i, t+2, forceStringEx(totalByOrgStructure[t+2]).replace(QString('.'), QString(',')))
                                    totalByLPU[t] += totalByOrgStructure[t+2]
                            for t in range(self.groupingRange):
                                table.setText(classI, t+2, forceStringEx(totalClass[t+2]).replace(QString('.'), QString(',')), CReportBase.TableTotal)
                        i = table.addRow()
                        table.setText(i, 0, u'ИТОГО', CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                        table.mergeCells(i, 0,  1, 2)
                        for t in range(self.groupingRange):
                            table.setText(i, t+2, forceStringEx(totalByLPU[t]).replace(QString('.'), QString(',')))
                    else:
                        dataActionClassDict = dataDict
                        dataActionClassKeys = dataActionClassDict.keys()
                        dataActionClassKeys.sort()
                        for actionTypeClass in dataActionClassKeys:
                            classI = table.addRow()
                            totalClass = [0]*(self.tableColumnsLen+4)
                            table.setText(classI, 0, dataActionClassName[actionTypeClass], CReportBase.TableTotal)
                            table.mergeCells(classI, 0,  1, 2)
                            dataActionTypeDict = dataDict[actionTypeClass]
                            dataActionTypeKeys = dataActionTypeDict.keys()
                            dataActionTypeKeys.sort(key=lambda x: x[1])
                            for dataActionTypeKey in dataActionTypeKeys:
                                actionTypeId, actionTypeInfo = dataActionTypeKey
                                i = table.addRow()
                                table.setText(i, 0, actionTypeInfo[0])
                                table.setText(i, 1, actionTypeInfo[1])
                                table.setText(i, 2, dataDict[actionTypeClass][dataActionTypeKey][0])
                                table.setText(i, 3, forceStringEx(dataDict[actionTypeClass][dataActionTypeKey][1]).replace(QString('.'), QString(',')))
                                totalClass[2] += dataDict[actionTypeClass][dataActionTypeKey][0]
                                totalClass[3] += dataDict[actionTypeClass][dataActionTypeKey][1]
                                totalReport[2] += dataDict[actionTypeClass][dataActionTypeKey][0]
                                totalReport[3] += dataDict[actionTypeClass][dataActionTypeKey][1]
                            for t in range(self.groupingRange):
                                table.setText(classI, t+2, forceStringEx(totalClass[t+2]).replace(QString('.'), QString(',')), CReportBase.TableTotal)
        else: # not detailByActionTypeClasses
            if detailByActionTypeGroup:
                if detailByFinance and detailByMedicalAidType:
                    if detailByOrgStructures:
                        totalByLPU = [0]*(self.tableColumnsLen+4)
                        for o, orgStructureName in enumerate(orgStructureList):
                            totalByOrgStructure = [0]*(self.tableColumnsLen+4)
                            f = table.addRow()
                            i = f
                            table.setText(f, 0, orgStructureName, CReportBase.TableTotal, blockFormat=CReportBase.AlignCenter)
                            table.mergeCells(f, 0,  1, self.tableColumnsLen+4)
                            dataActionGroupDict = dataDict[orgStructureName]
                            dataActionGroupKeys = dataActionGroupDict.keys()
                            dataActionGroupKeys.sort(key=lambda x: x[0])
                            for actionTypeGroup in dataActionGroupKeys:
                                actionTypeGroupName, actionTypeGroupId = actionTypeGroup
                                groupI = table.addRow()
                                totalGroup = [0]*(self.tableColumnsLen+4)
                                table.setText(groupI, 0, actionTypeGroup[0], CReportBase.TableTotal)
                                table.mergeCells(groupI, 0,  1, 2)
                                dataActionTypeDict = dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)]
                                dataActionTypeKeys = dataActionTypeDict.keys()
                                dataActionTypeKeys.sort(key=lambda x: x[1])
                                for dataActionTypeKey in dataActionTypeKeys:
                                    actionTypeId, actionTypeInfo = dataActionTypeKey
                                    i = table.addRow()
                                    table.setText(i, 0, actionTypeInfo[0])
                                    table.setText(i, 1, actionTypeInfo[1])
                                    totalFinance = {}
                                    totallyTotalFinance = [0]*2
                                    for f, financeName in enumerate(financeList):
                                        total = [0]*2
                                        for j, medicalAidTypeName in enumerate(medicalAidTypeList):
                                            table.setText(i, 2+2*j+f*lenMedicalCols, dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0])
                                            totalByOrgStructure[2+2*j+f*lenMedicalCols] += dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0]
                                            table.setText(i, 3+2*j+f*lenMedicalCols, forceStringEx(dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                            totalByOrgStructure[3+2*j+f*lenMedicalCols] += dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]
                                            totalGroup[3+2*j+f*lenMedicalCols] += dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]
                                            totalGroup[2+2*j+f*lenMedicalCols] += dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0]
                                            if medicalAidTypeName not in totalFinance.keys():
                                                totalFinance[medicalAidTypeName] = [0]*2
                                            total[0] += dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0]
                                            total[1] += dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]
                                            totalFinance[medicalAidTypeName][0] += dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0]
                                            totalFinance[medicalAidTypeName][1] += dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]
                                        table.setText(i, 4+2*j+f*lenMedicalCols, total[0])
                                        totalByOrgStructure[4+2*j+f*lenMedicalCols] += total[0]
                                        table.setText(i, 5+2*j+f*lenMedicalCols, forceStringEx(total[1]).replace(QString('.'), QString(',')))
                                        totalByOrgStructure[5+2*j+f*lenMedicalCols] += total[1]
                                        totalGroup[4+2*j+f*lenMedicalCols] += total[0]
                                        totalGroup[5+2*j+f*lenMedicalCols] += total[1]
                                    for j, medicalAidTypeName in enumerate(medicalAidTypeList):
                                        table.setText(i, 2+2*j+(f+1)*lenMedicalCols, totalFinance.get(medicalAidTypeName, [0]*2)[0])
                                        totalByOrgStructure[2+2*j+(f+1)*lenMedicalCols] += totalFinance.get(medicalAidTypeName, [0]*2)[0]
                                        table.setText(i, 3+2*j+(f+1)*lenMedicalCols, forceStringEx(totalFinance.get(medicalAidTypeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                        totalByOrgStructure[3+2*j+(f+1)*lenMedicalCols] += totalFinance.get(medicalAidTypeName, [0]*2)[1]
                                        totalGroup[2+2*j+(f+1)*lenMedicalCols] += totalFinance.get(medicalAidTypeName, [0]*2)[0]
                                        totalGroup[3+2*j+(f+1)*lenMedicalCols] += totalFinance.get(medicalAidTypeName, [0]*2)[1]
                                        totallyTotalFinance[0] += totalFinance.get(medicalAidTypeName, [0]*2)[0]
                                        totallyTotalFinance[1] += totalFinance.get(medicalAidTypeName, [0]*2)[1]
                                    table.setText(i, 4+2*j+(f+1)*lenMedicalCols, totallyTotalFinance[0])
                                    totalByOrgStructure[4+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[0]
                                    table.setText(i, 5+2*j+(f+1)*lenMedicalCols, forceStringEx(totallyTotalFinance[1]).replace(QString('.'), QString(',')))
                                    totalByOrgStructure[5+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[1]
                                    totalGroup[4+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[0]
                                    totalGroup[5+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[1]
                                for t in range(self.groupingRange):
                                    table.setText(groupI, t+2, forceStringEx(totalGroup[t+2]).replace(QString('.'), QString(',')), CReportBase.TableTotal)
                            i = table.addRow()
                            table.setText(i, 0, u'Итого по подразделению %s'%(orgStructureName), CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                            table.mergeCells(i, 0,  1, 2)
                            for t in range(self.groupingRange):
                                table.setText(i, t+2, forceStringEx(totalByOrgStructure[t+2]).replace(QString('.'), QString(',')))
                                totalByLPU[t] += totalByOrgStructure[t+2]
                        i = table.addRow()
                        table.setText(i, 0, u'ИТОГО', CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                        table.mergeCells(i, 0,  1, 2)
                        for t in range(self.groupingRange):
                            table.setText(i, t+2, forceStringEx(totalByLPU[t]).replace(QString('.'), QString(',')))
                    else:
                        dataActionGroupDict = dataDict
                        dataActionGroupKeys = dataActionGroupDict.keys()
                        dataActionGroupKeys.sort(key=lambda x: x[0])
                        for actionTypeGroup in dataActionGroupKeys:
                            actionTypeGroupName, actionTypeGroupId = actionTypeGroup
                            groupI = table.addRow()
                            totalGroup = [0]*(self.tableColumnsLen+4)
                            table.setText(groupI, 0, actionTypeGroup[0], CReportBase.TableTotal)
                            table.mergeCells(groupI, 0,  1, 2)
                            dataActionTypeDict = dataDict[(actionTypeGroupName, actionTypeGroupId)]
                            dataActionTypeKeys = dataActionTypeDict.keys()
                            dataActionTypeKeys.sort(key=lambda x: x[1])
                            for dataActionTypeKey in dataActionTypeKeys:
                                actionTypeId, actionTypeInfo = dataActionTypeKey
                                i = table.addRow()
                                table.setText(i, 0, actionTypeInfo[0])
                                table.setText(i, 1, actionTypeInfo[1])
                                totalFinance = {}
                                totallyTotalFinance = [0]*2
                                for f, financeName in enumerate(financeList):
                                    total = [0]*2
                                    for j, medicalAidTypeName in enumerate(medicalAidTypeList):
                                        table.setText(i, 2+2*j+f*lenMedicalCols, dataDict[(actionTypeGroupName, actionTypeGroupId)] [dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0])
                                        table.setText(i, 3+2*j+f*lenMedicalCols, forceStringEx(dataDict[(actionTypeGroupName, actionTypeGroupId)] [dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                        totalReport[2+2*j+f*lenMedicalCols] += dataDict[(actionTypeGroupName, actionTypeGroupId)] [dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0]
                                        totalReport[3+2*j+f*lenMedicalCols] += dataDict[(actionTypeGroupName, actionTypeGroupId)] [dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]
                                        totalGroup[2+2*j+f*lenMedicalCols] += dataDict[(actionTypeGroupName, actionTypeGroupId)] [dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0]
                                        totalGroup[3+2*j+f*lenMedicalCols] += dataDict[(actionTypeGroupName, actionTypeGroupId)] [dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]
                                        if medicalAidTypeName not in totalFinance.keys():
                                            totalFinance[medicalAidTypeName] = [0]*2
                                        total[0] += dataDict[(actionTypeGroupName, actionTypeGroupId)] [dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0]
                                        total[1] += dataDict[(actionTypeGroupName, actionTypeGroupId)] [dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]
                                        totalFinance[medicalAidTypeName][0] += dataDict[(actionTypeGroupName, actionTypeGroupId)] [dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0]
                                        totalFinance[medicalAidTypeName][1] += dataDict[(actionTypeGroupName, actionTypeGroupId)] [dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]
                                    table.setText(i, 4+2*j+f*lenMedicalCols, total[0])
                                    table.setText(i, 5+2*j+f*lenMedicalCols, forceStringEx(total[1]).replace(QString('.'), QString(',')))
                                    totalReport[4+2*j+f*lenMedicalCols] += total[0]
                                    totalReport[5+2*j+f*lenMedicalCols] += total[1]
                                    totalGroup[4+2*j+f*lenMedicalCols] += total[0]
                                    totalGroup[5+2*j+f*lenMedicalCols] += total[1]
                                for j, medicalAidTypeName in enumerate(medicalAidTypeList):
                                    table.setText(i, 2+2*j+(f+1)*lenMedicalCols, totalFinance.get(medicalAidTypeName, [0]*2)[0])
                                    table.setText(i, 3+2*j+(f+1)*lenMedicalCols, forceStringEx(totalFinance.get(medicalAidTypeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                    totalReport[2+2*j+(f+1)*lenMedicalCols] += totalFinance.get(medicalAidTypeName, [0]*2)[0]
                                    totalReport[3+2*j+(f+1)*lenMedicalCols] += totalFinance.get(medicalAidTypeName, [0]*2)[1]
                                    totalGroup[2+2*j+(f+1)*lenMedicalCols] += totalFinance.get(medicalAidTypeName, [0]*2)[0]
                                    totalGroup[3+2*j+(f+1)*lenMedicalCols] += totalFinance.get(medicalAidTypeName, [0]*2)[1]
                                    totallyTotalFinance[0] += totalFinance.get(medicalAidTypeName, [0]*2)[0]
                                    totallyTotalFinance[1] += totalFinance.get(medicalAidTypeName, [0]*2)[1]
                                table.setText(i, 4+2*j+(f+1)*lenMedicalCols, totallyTotalFinance[0])
                                table.setText(i, 5+2*j+(f+1)*lenMedicalCols, forceStringEx(totallyTotalFinance[1]).replace(QString('.'), QString(',')))
                                totalReport[4+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[0]
                                totalReport[5+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[1]
                                totalGroup[4+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[0]
                                totalGroup[5+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[1]
                            for t in range(self.groupingRange):
                                table.setText(groupI, t+2, forceStringEx(totalGroup[t+2]).replace(QString('.'), QString(',')), CReportBase.TableTotal)
                elif detailByFinance:
                    if detailByOrgStructures:
                        totalByLPU = [0]*(self.tableColumnsLen+4)
                        for o, orgStructureName in enumerate(orgStructureList):
                            totalByOrgStructure = [0]*(self.tableColumnsLen+4)
                            f = table.addRow()
                            i = f
                            table.setText(f, 0, orgStructureName, CReportBase.TableTotal, blockFormat=CReportBase.AlignCenter)
                            table.mergeCells(f, 0,  1, self.tableColumnsLen+4)
                            dataActionGroupDict = dataDict[orgStructureName]
                            dataActionGroupKeys = dataActionGroupDict.keys()
                            dataActionGroupKeys.sort(key=lambda x: x[0])
                            for actionTypeGroup in dataActionGroupKeys:
                                actionTypeGroupName, actionTypeGroupId = actionTypeGroup
                                groupI = table.addRow()
                                totalGroup = [0]*(self.tableColumnsLen+4)
                                table.setText(groupI, 0, actionTypeGroup[0], CReportBase.TableTotal)
                                table.mergeCells(groupI, 0,  1, 2)
                                dataActionTypeDict = dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)]
                                dataActionTypeKeys = dataActionTypeDict.keys()
                                dataActionTypeKeys.sort(key=lambda x: x[1])
                                for dataActionTypeKey in dataActionTypeKeys:
                                    actionTypeId, actionTypeInfo = dataActionTypeKey
                                    i = table.addRow()
                                    total = [0]*2
                                    table.setText(i, 0, actionTypeInfo[0])
                                    table.setText(i, 1, actionTypeInfo[1])
                                    for fi, financeName in enumerate(financeList):
                                        table.setText(i, 2+fi*2, dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)] [dataActionTypeKey].get(financeName, [0]*2)[0])
                                        totalByOrgStructure[2+fi*2] += dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)] [dataActionTypeKey].get(financeName, [0]*2)[0]
                                        table.setText(i, 3+fi*2, forceStringEx(dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)] [dataActionTypeKey].get(financeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                        totalByOrgStructure[3+fi*2] += dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)] [dataActionTypeKey].get(financeName, [0]*2)[1]
                                        totalGroup[2+fi*2] += dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)] [dataActionTypeKey].get(financeName, [0]*2)[0]
                                        totalGroup[3+fi*2] += dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)] [dataActionTypeKey].get(financeName, [0]*2)[1]
                                        total[0] += dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)] [dataActionTypeKey].get(financeName, [0]*2)[0]
                                        total[1] += dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)] [dataActionTypeKey].get(financeName, [0]*2)[1]
                                    fi += 1
                                    table.setText(i, 2+fi*2, total[0])
                                    totalByOrgStructure[2+fi*2] += total[0]
                                    table.setText(i, 3+fi*2, forceStringEx(total[1]).replace(QString('.'), QString(',')))
                                    totalByOrgStructure[3+fi*2] += total[1]
                                    totalGroup[2+fi*2] += total[0]
                                    totalGroup[3+fi*2] += total[1]
                                for t in range(self.groupingRange):
                                    table.setText(groupI, t+2, forceStringEx(totalGroup[t+2]).replace(QString('.'), QString(',')), CReportBase.TableTotal)
                            i = table.addRow()
                            table.setText(i, 0, u'Итого по подразделению %s'%(orgStructureName), CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                            table.mergeCells(i, 0,  1, 2)
                            for t in range(self.groupingRange):
                                table.setText(i, t+2, forceStringEx(totalByOrgStructure[t+2]).replace(QString('.'), QString(',')))
                                totalByLPU[t] += totalByOrgStructure[t+2]
                        i = table.addRow()
                        table.setText(i, 0, u'ИТОГО', CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                        table.mergeCells(i, 0,  1, 2)
                        for t in range(self.groupingRange):
                            table.setText(i, t+2, forceStringEx(totalByLPU[t]).replace(QString('.'), QString(',')))
                    else:
                        dataActionGroupDict = dataDict
                        dataActionGroupKeys = dataActionGroupDict.keys()
                        dataActionGroupKeys.sort(key=lambda x: x[0])
                        for actionTypeGroup in dataActionGroupKeys:
                            actionTypeGroupName, actionTypeGroupId = actionTypeGroup
                            groupI = table.addRow()
                            totalGroup = [0]*(self.tableColumnsLen+4)
                            table.setText(groupI, 0, actionTypeGroup[0], CReportBase.TableTotal)
                            table.mergeCells(groupI, 0,  1, 2)
                            dataActionTypeDict = dataDict[(actionTypeGroupName, actionTypeGroupId)]
                            dataActionTypeKeys = dataActionTypeDict.keys()
                            dataActionTypeKeys.sort(key=lambda x: x[1])
                            for dataActionTypeKey in dataActionTypeKeys:
                                actionTypeId, actionTypeInfo = dataActionTypeKey
                                i = table.addRow()
                                total = [0]*2
                                table.setText(i, 0, actionTypeInfo[0])
                                table.setText(i, 1, actionTypeInfo[1])
                                for f, financeName in enumerate(financeList):
                                    table.setText(i, 2+f*2, dataDict[(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, [0]*2)[0])
                                    table.setText(i, 3+f*2, forceStringEx(dataDict[(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                    totalReport[2+f*2] += dataDict[(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, [0]*2)[0]
                                    totalReport[3+f*2] += dataDict[(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, [0]*2)[1]
                                    totalGroup[2+f*2] += dataDict[(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, [0]*2)[0]
                                    totalGroup[3+f*2] += dataDict[(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, [0]*2)[1]
                                    total[0] += dataDict[(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, [0]*2)[0]
                                    total[1] += dataDict[(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(financeName, [0]*2)[1]
                                table.setText(i, 4+f*2, total[0])
                                table.setText(i, 5+f*2, forceStringEx(total[1]).replace(QString('.'), QString(',')))
                                totalReport[4+f*2] += total[0]
                                totalReport[5+f*2] += total[1]
                                totalGroup[4+f*2] += total[0]
                                totalGroup[5+f*2] += total[1]
                            for t in range(self.groupingRange):
                                table.setText(groupI, t+2, forceStringEx(totalGroup[t+2]).replace(QString('.'), QString(',')), CReportBase.TableTotal)
                elif detailByMedicalAidType:
                    if detailByOrgStructures:
                        totalByLPU = [0]*(self.tableColumnsLen+4)
                        for o, orgStructureName in enumerate(orgStructureList):
                            totalByOrgStructure = [0]*(self.tableColumnsLen+4)
                            f = table.addRow()
                            i = f
                            table.setText(f, 0, orgStructureName, CReportBase.TableTotal, blockFormat=CReportBase.AlignCenter)
                            table.mergeCells(f, 0,  1, self.tableColumnsLen+4)
                            dataActionGroupDict = dataDict[orgStructureName]
                            dataActionGroupKeys = dataActionGroupDict.keys()
                            dataActionGroupKeys.sort(key=lambda x: x[0])
                            for actionTypeGroup in dataActionGroupKeys:
                                actionTypeGroupName, actionTypeGroupId = actionTypeGroup
                                groupI = table.addRow()
                                totalGroup = [0]*(self.tableColumnsLen+4)
                                table.setText(groupI, 0, actionTypeGroup[0], CReportBase.TableTotal)
                                table.mergeCells(groupI, 0,  1, 2)
                                dataActionTypeDict = dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)]
                                dataActionTypeKeys = dataActionTypeDict.keys()
                                dataActionTypeKeys.sort(key=lambda x: x[1])
                                for dataActionTypeKey in dataActionTypeKeys:
                                    actionTypeId, actionTypeInfo = dataActionTypeKey
                                    i = table.addRow()
                                    table.setText(i, 0, actionTypeInfo[0])
                                    table.setText(i, 1, actionTypeInfo[1])
                                    for m, medicalAidTypeName in enumerate(medicalAidTypeList):
                                        table.setText(i, 2+m*2, dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[0])
                                        totalByOrgStructure[2+m*2] += dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[0]
                                        table.setText(i, 3+m*2, forceStringEx(dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                        totalByOrgStructure[3+m*2] += dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[1]
                                        totalGroup[2+m*2] += dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[0]
                                        totalGroup[3+m*2] += dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[1]
                                for t in range(self.groupingRange):
                                    table.setText(groupI, t+2, forceStringEx(totalGroup[t+2]).replace(QString('.'), QString(',')), CReportBase.TableTotal)
                            i = table.addRow()
                            table.setText(i, 0, u'Итого по подразделению %s'%(orgStructureName), CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                            table.mergeCells(i, 0,  1, 2)
                            for t in range(self.groupingRange):
                                table.setText(i, t+2, forceStringEx(totalByOrgStructure[t+2]).replace(QString('.'), QString(',')))
                                totalByLPU[t] += totalByOrgStructure[t+2]
                        i = table.addRow()
                        table.setText(i, 0, u'ИТОГО', CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                        table.mergeCells(i, 0,  1, 2)
                        for t in range(self.groupingRange):
                            table.setText(i, t+2, forceStringEx(totalByLPU[t]).replace(QString('.'), QString(',')))
                    else:
                        dataActionGroupDict = dataDict
                        dataActionGroupKeys = dataActionGroupDict.keys()
                        dataActionGroupKeys.sort(key=lambda x: x[0])
                        for actionTypeGroup in dataActionGroupKeys:
                            actionTypeGroupName, actionTypeGroupId = actionTypeGroup
                            groupI = table.addRow()
                            totalGroup = [0]*(self.tableColumnsLen+4)
                            table.setText(groupI, 0, actionTypeGroup[0], CReportBase.TableTotal)
                            table.mergeCells(groupI, 0,  1, 2)
                            dataActionTypeDict = dataDict[(actionTypeGroupName, actionTypeGroupId)]
                            dataActionTypeKeys = dataActionTypeDict.keys()
                            dataActionTypeKeys.sort(key=lambda x: x[1])
                            for dataActionTypeKey in dataActionTypeKeys:
                                actionTypeId, actionTypeInfo = dataActionTypeKey
                                i = table.addRow()
                                table.setText(i, 0, actionTypeInfo[0])
                                table.setText(i, 1, actionTypeInfo[1])
                                for m, medicalAidTypeName in enumerate(medicalAidTypeList):
                                    table.setText(i, 2+m*2, dataDict[(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[0])
                                    table.setText(i, 3+m*2, forceStringEx(dataDict[(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                    totalReport[2+m*2] += dataDict[(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[0]
                                    totalReport[3+m*2] += dataDict[(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[1]
                                    totalGroup[2+m*2] += dataDict[(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[0]
                                    totalGroup[3+m*2] += dataDict[(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[1]
                        for t in range(self.groupingRange):
                            table.setText(groupI, t+2, forceStringEx(totalGroup[t+2]).replace(QString('.'), QString(',')), CReportBase.TableTotal)
                else:
                    if detailByOrgStructures:
                        totalByLPU = [0]*(self.tableColumnsLen+4)
                        for o, orgStructureName in enumerate(orgStructureList):
                            totalByOrgStructure = [0]*(self.tableColumnsLen+4)
                            f = table.addRow()
                            i = f
                            table.setText(f, 0, orgStructureName, CReportBase.TableTotal, blockFormat=CReportBase.AlignCenter)
                            table.mergeCells(f, 0,  1, self.tableColumnsLen+2)
                            dataActionGroupDict = dataDict[orgStructureName]
                            dataActionGroupKeys = dataActionGroupDict.keys()
                            dataActionGroupKeys.sort(key=lambda x: x[0])
                            for actionTypeGroup in dataActionGroupKeys:
                                actionTypeGroupName, actionTypeGroupId = actionTypeGroup
                                groupI = table.addRow()
                                totalGroup = [0]*(self.tableColumnsLen+4)
                                table.setText(groupI, 0, actionTypeGroup[0], CReportBase.TableTotal)
                                table.mergeCells(groupI, 0,  1, 2)
                                dataActionTypeDict = dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)]
                                dataActionTypeKeys = dataActionTypeDict.keys()
                                dataActionTypeKeys.sort(key=lambda x: x[1])
                                for dataActionTypeKey in dataActionTypeKeys:
                                    actionTypeId, actionTypeInfo = dataActionTypeKey
                                    i = table.addRow()
                                    table.setText(i, 0, actionTypeInfo[0])
                                    table.setText(i, 1, actionTypeInfo[1])
                                    table.setText(i, 2, dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey][0])
                                    totalByOrgStructure[2] += dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey][0]
                                    table.setText(i, 3, forceStringEx(dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey][1]).replace(QString('.'), QString(',')))
                                    totalByOrgStructure[3] += dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey][1]
                                    totalGroup[2] += dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey][0]
                                    totalGroup[3] += dataDict[orgStructureName][(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey][1]
                                for t in range(self.groupingRange):
                                    table.setText(groupI, t+2, forceStringEx(totalGroup[t+2]).replace(QString('.'), QString(',')), CReportBase.TableTotal)
                            i = table.addRow()
                            table.setText(i, 0, u'Итого по подразделению %s'%(orgStructureName), CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                            table.mergeCells(i, 0,  1, 2)
                            for t in range(self.groupingRange):
                                table.setText(i, t+2, forceStringEx(totalByOrgStructure[t+2]).replace(QString('.'), QString(',')))
                                totalByLPU[t] += totalByOrgStructure[t+2]
                        i = table.addRow()
                        table.setText(i, 0, u'ИТОГО', CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                        table.mergeCells(i, 0,  1, 2)
                        for t in range(self.groupingRange):
                            table.setText(i, t+2, forceStringEx(totalByLPU[t]).replace(QString('.'), QString(',')))
                    else:
                        dataActionGroupDict = dataDict
                        dataActionGroupKeys = dataActionGroupDict.keys()
                        dataActionGroupKeys.sort(key=lambda x: x[0])
                        for actionTypeGroup in dataActionGroupKeys:
                            actionTypeGroupName, actionTypeGroupId = actionTypeGroup
                            groupI = table.addRow()
                            totalGroup = [0]*(self.tableColumnsLen+4)
                            table.setText(groupI, 0, actionTypeGroup[0], CReportBase.TableTotal)
                            table.mergeCells(groupI, 0,  1, 2)
                            dataActionTypeDict = dataDict[(actionTypeGroupName, actionTypeGroupId)]
                            dataActionTypeKeys = dataActionTypeDict.keys()
                            dataActionTypeKeys.sort(key=lambda x: x[1])
                            for dataActionTypeKey in dataActionTypeKeys:
                                actionTypeId, actionTypeInfo = dataActionTypeKey
                                i = table.addRow()
                                table.setText(i, 0, actionTypeInfo[0])
                                table.setText(i, 1, actionTypeInfo[1])
                                table.setText(i, 2, dataDict[(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey][0])
                                table.setText(i, 3, forceStringEx(dataDict[(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey][1]).replace(QString('.'), QString(',')))
                                totalReport[2] += dataDict[(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey][0]
                                totalReport[3] += dataDict[(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey][1]
                                totalGroup[2] += dataDict[(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey][0]
                                totalGroup[3] += dataDict[(actionTypeGroupName, actionTypeGroupId)][dataActionTypeKey][1]
                            for t in range(self.groupingRange):
                                table.setText(groupI, t+2, forceStringEx(totalGroup[t+2]).replace(QString('.'), QString(',')), CReportBase.TableTotal)
            else: # not detailByActionTypeGroup
                if detailByFinance and detailByMedicalAidType:
                    if detailByOrgStructures:
                        totalByLPU = [0]*(self.tableColumnsLen+4)
                        for o, orgStructureName in enumerate(orgStructureList):
                            totalByOrgStructure = [0]*(self.tableColumnsLen+4)
                            f = table.addRow()
                            i = f
                            table.setText(f, 0, orgStructureName, CReportBase.TableTotal, blockFormat=CReportBase.AlignCenter)
                            table.mergeCells(f, 0,  1, self.tableColumnsLen+4)
                            dataActionTypeDict = dataDict[orgStructureName]
                            dataActionTypeKeys = dataActionTypeDict.keys()
                            dataActionTypeKeys.sort(key=lambda x: x[1])
                            for dataActionTypeKey in dataActionTypeKeys:
                                actionTypeId, actionTypeInfo = dataActionTypeKey
                                i = table.addRow()
                                table.setText(i, 0, actionTypeInfo[0])
                                table.setText(i, 1, actionTypeInfo[1])
                                totalFinance = {}
                                totallyTotalFinance = [0]*2
                                for f, financeName in enumerate(financeList):
                                    total = [0]*2
                                    for j, medicalAidTypeName in enumerate(medicalAidTypeList):
                                        table.setText(i, 2+2*j+f*lenMedicalCols, dataDict[orgStructureName][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0])
                                        totalByOrgStructure[2+2*j+f*lenMedicalCols] += dataDict[orgStructureName][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0]
                                        table.setText(i, 3+2*j+f*lenMedicalCols, forceStringEx(dataDict[orgStructureName][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                        totalByOrgStructure[3+2*j+f*lenMedicalCols] += dataDict[orgStructureName][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]
                                        if medicalAidTypeName not in totalFinance.keys():
                                            totalFinance[medicalAidTypeName] = [0]*2
                                        total[0] += dataDict[orgStructureName][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0]
                                        total[1] += dataDict[orgStructureName][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]
                                        totalFinance[medicalAidTypeName][0] += dataDict[orgStructureName][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0]
                                        totalFinance[medicalAidTypeName][1] += dataDict[orgStructureName][dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]
                                    table.setText(i, 4+2*j+f*lenMedicalCols, total[0])
                                    totalByOrgStructure[4+2*j+f*lenMedicalCols] += total[0]
                                    table.setText(i, 5+2*j+f*lenMedicalCols, forceStringEx(total[1]).replace(QString('.'), QString(',')))
                                    totalByOrgStructure[5+2*j+f*lenMedicalCols] += total[1]
                                for j, medicalAidTypeName in enumerate(medicalAidTypeList):
                                    table.setText(i, 2+2*j+(f+1)*lenMedicalCols, totalFinance.get(medicalAidTypeName, [0]*2)[0])
                                    totalByOrgStructure[2+2*j+(f+1)*lenMedicalCols] += totalFinance.get(medicalAidTypeName, [0]*2)[0]
                                    table.setText(i, 3+2*j+(f+1)*lenMedicalCols, forceStringEx(totalFinance.get(medicalAidTypeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                    totalByOrgStructure[3+2*j+(f+1)*lenMedicalCols] += totalFinance.get(medicalAidTypeName, [0]*2)[1]
                                    totallyTotalFinance[0] += totalFinance.get(medicalAidTypeName, [0]*2)[0]
                                    totallyTotalFinance[1] += totalFinance.get(medicalAidTypeName, [0]*2)[1]
                                table.setText(i, 4+2*j+(f+1)*lenMedicalCols, totallyTotalFinance[0])
                                totalByOrgStructure[4+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[0]
                                table.setText(i, 5+2*j+(f+1)*lenMedicalCols, forceStringEx(totallyTotalFinance[1]).replace(QString('.'), QString(',')))
                                totalByOrgStructure[5+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[1]
                            i = table.addRow()
                            table.setText(i, 0, u'Итого по подразделению %s'%(orgStructureName), CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                            table.mergeCells(i, 0,  1, 2)
                            for t in range(self.groupingRange):
                                table.setText(i, t+2, forceStringEx(totalByOrgStructure[t+2]).replace(QString('.'), QString(',')))
                                totalByLPU[t] += totalByOrgStructure[t+2]
                        i = table.addRow()
                        table.setText(i, 0, u'ИТОГО', CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                        table.mergeCells(i, 0,  1, 2)
                        for t in range(self.groupingRange):
                            table.setText(i, t+2, forceStringEx(totalByLPU[t]).replace(QString('.'), QString(',')))
                    else:
                        dataActionTypeDict = dataDict
                        dataActionTypeKeys = dataActionTypeDict.keys()
                        dataActionTypeKeys.sort(key=lambda x: x[1])
                        for dataActionTypeKey in dataActionTypeKeys:
                            actionTypeId, actionTypeInfo = dataActionTypeKey
                            i = table.addRow()
                            table.setText(i, 0, actionTypeInfo[0])
                            table.setText(i, 1, actionTypeInfo[1])
                            totalFinance = {}
                            totallyTotalFinance = [0]*2
                            for f, financeName in enumerate(financeList):
                                total = [0]*2
                                for j, medicalAidTypeName in enumerate(medicalAidTypeList):
                                    table.setText(i, 2+2*j+f*lenMedicalCols, dataDict[dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0])
                                    table.setText(i, 3+2*j+f*lenMedicalCols, forceStringEx(dataDict[dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                    totalReport[2+2*j+f*lenMedicalCols] += dataDict[dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0]
                                    totalReport[3+2*j+f*lenMedicalCols] += dataDict[dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]
                                    if medicalAidTypeName not in totalFinance.keys():
                                        totalFinance[medicalAidTypeName] = [0]*2
                                    total[0] += dataDict[dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0]
                                    total[1] += dataDict[dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]
                                    totalFinance[medicalAidTypeName][0] += dataDict[dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[0]
                                    totalFinance[medicalAidTypeName][1] += dataDict[dataActionTypeKey].get(financeName, {}).get(medicalAidTypeName, [0]*2)[1]
                                table.setText(i, 4+2*j+f*lenMedicalCols, total[0])
                                table.setText(i, 5+2*j+f*lenMedicalCols, forceStringEx(total[1]).replace(QString('.'), QString(',')))
                                totalReport[4+2*j+f*lenMedicalCols] += total[0]
                                totalReport[5+2*j+f*lenMedicalCols] += total[1]
                            for j, medicalAidTypeName in enumerate(medicalAidTypeList):
                                table.setText(i, 2+2*j+(f+1)*lenMedicalCols, totalFinance.get(medicalAidTypeName, [0]*2)[0])
                                table.setText(i, 3+2*j+(f+1)*lenMedicalCols, forceStringEx(totalFinance.get(medicalAidTypeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                totalReport[2+2*j+(f+1)*lenMedicalCols] += totalFinance.get(medicalAidTypeName, [0]*2)[0]
                                totalReport[3+2*j+(f+1)*lenMedicalCols] += totalFinance.get(medicalAidTypeName, [0]*2)[1]
                                totallyTotalFinance[0] += totalFinance.get(medicalAidTypeName, [0]*2)[0]
                                totallyTotalFinance[1] += totalFinance.get(medicalAidTypeName, [0]*2)[1]
                            table.setText(i, 4+2*j+(f+1)*lenMedicalCols, totallyTotalFinance[0])
                            table.setText(i, 5+2*j+(f+1)*lenMedicalCols, forceStringEx(totallyTotalFinance[1]).replace(QString('.'), QString(',')))
                            totalReport[4+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[0]
                            totalReport[5+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[1]
                elif detailByFinance:
                    if detailByOrgStructures:
                        totalByLPU = [0]*(self.tableColumnsLen+4)
                        for o, orgStructureName in enumerate(orgStructureList):
                            totalByOrgStructure = [0]*(self.tableColumnsLen+4)
                            f = table.addRow()
                            i = f
                            table.setText(f, 0, orgStructureName, CReportBase.TableTotal, blockFormat=CReportBase.AlignCenter)
                            table.mergeCells(f, 0,  1, self.tableColumnsLen+4)
                            dataActionTypeDict = dataDict[orgStructureName]
                            dataActionTypeKeys = dataActionTypeDict.keys()
                            dataActionTypeKeys.sort(key=lambda x: x[1])
                            for dataActionTypeKey in dataActionTypeKeys:
                                actionTypeId, actionTypeInfo = dataActionTypeKey
                                i = table.addRow()
                                total = [0]*2
                                table.setText(i, 0, actionTypeInfo[0])
                                table.setText(i, 1, actionTypeInfo[1])
                                for fi, financeName in enumerate(financeList):
                                    table.setText(i, 2+fi*2, dataDict[orgStructureName][dataActionTypeKey].get(financeName, [0]*2)[0])
                                    totalByOrgStructure[2+fi*2] += dataDict[orgStructureName][dataActionTypeKey].get(financeName, [0]*2)[0]
                                    table.setText(i, 3+fi*2, forceStringEx(dataDict[orgStructureName][dataActionTypeKey].get(financeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                    totalByOrgStructure[3+fi*2] += dataDict[orgStructureName][dataActionTypeKey].get(financeName, [0]*2)[1]
                                    total[0] += dataDict[orgStructureName][dataActionTypeKey].get(financeName, [0]*2)[0]
                                    total[1] += dataDict[orgStructureName][dataActionTypeKey].get(financeName, [0]*2)[1]
                                fi += 1
                                table.setText(i, 2+fi*2, total[0])
                                totalByOrgStructure[2+fi*2] += total[0]
                                table.setText(i, 3+fi*2, forceStringEx(total[1]).replace(QString('.'), QString(',')))
                                totalByOrgStructure[3+fi*2] += total[1]
                            i = table.addRow()
                            table.setText(i, 0, u'Итого по подразделению %s'%(orgStructureName), CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                            table.mergeCells(i, 0,  1, 2)
                            for t in range(self.groupingRange):
                                table.setText(i, t+2, forceStringEx(totalByOrgStructure[t+2]).replace(QString('.'), QString(',')))
                                totalByLPU[t] += totalByOrgStructure[t+2]
                        i = table.addRow()
                        table.setText(i, 0, u'ИТОГО', CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                        table.mergeCells(i, 0,  1, 2)
                        for t in range(self.groupingRange):
                            table.setText(i, t+2, forceStringEx(totalByLPU[t]).replace(QString('.'), QString(',')))
                    else:
                        dataActionTypeDict = dataDict
                        dataActionTypeKeys = dataActionTypeDict.keys()
                        dataActionTypeKeys.sort(key=lambda x: x[1])
                        for dataActionTypeKey in dataActionTypeKeys:
                            actionTypeId, actionTypeInfo = dataActionTypeKey
                            i = table.addRow()
                            total = [0]*2
                            table.setText(i, 0, actionTypeInfo[0])
                            table.setText(i, 1, actionTypeInfo[1])
                            for f, financeName in enumerate(financeList):
                                table.setText(i, 2+f*2, dataDict[dataActionTypeKey].get(financeName, [0]*2)[0])
                                table.setText(i, 3+f*2, forceStringEx(dataDict[dataActionTypeKey].get(financeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                totalReport[2+f*2] += dataDict[dataActionTypeKey].get(financeName, [0]*2)[0]
                                totalReport[3+f*2] += dataDict[dataActionTypeKey].get(financeName, [0]*2)[1]
                                total[0] += dataDict[dataActionTypeKey].get(financeName, [0]*2)[0]
                                total[1] += dataDict[dataActionTypeKey].get(financeName, [0]*2)[1]
                            table.setText(i, 4+f*2, total[0])
                            table.setText(i, 5+f*2, forceStringEx(total[1]).replace(QString('.'), QString(',')))
                            totalReport[4+f*2] += total[0]
                            totalReport[5+f*2] += total[1]
                elif detailByMedicalAidType:
                    if detailByOrgStructures:
                        totalByLPU = [0]*(self.tableColumnsLen+4)
                        for o, orgStructureName in enumerate(orgStructureList):
                            totalByOrgStructure = [0]*(self.tableColumnsLen+4)
                            f = table.addRow()
                            i = f
                            table.setText(f, 0, orgStructureName, CReportBase.TableTotal, blockFormat=CReportBase.AlignCenter)
                            table.mergeCells(f, 0,  1, self.tableColumnsLen+4)
                            dataActionTypeDict = dataDict[orgStructureName]
                            dataActionTypeKeys = dataActionTypeDict.keys()
                            dataActionTypeKeys.sort(key=lambda x: x[1])
                            for dataActionTypeKey in dataActionTypeKeys:
                                actionTypeId, actionTypeInfo = dataActionTypeKey
                                i = table.addRow()
                                table.setText(i, 0, actionTypeInfo[0])
                                table.setText(i, 1, actionTypeInfo[1])
                                for m, medicalAidTypeName in enumerate(medicalAidTypeList):
                                    table.setText(i, 2+m*2, dataDict[orgStructureName][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[0])
                                    totalByOrgStructure[2+m*2] += dataDict[orgStructureName][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[0]
                                    table.setText(i, 3+m*2, forceStringEx(dataDict[orgStructureName][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                    totalByOrgStructure[3+m*2] += dataDict[orgStructureName][dataActionTypeKey].get(medicalAidTypeName, [0]*2)[1]
                            i = table.addRow()
                            table.setText(i, 0, u'Итого по подразделению %s'%(orgStructureName), CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                            table.mergeCells(i, 0,  1, 2)
                            for t in range(self.groupingRange):
                                table.setText(i, t+2, forceStringEx(totalByOrgStructure[t+2]).replace(QString('.'), QString(',')))
                                totalByLPU[t] += totalByOrgStructure[t+2]
                        i = table.addRow()
                        table.setText(i, 0, u'ИТОГО', CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                        table.mergeCells(i, 0,  1, 2)
                        for t in range(self.groupingRange):
                            table.setText(i, t+2, forceStringEx(totalByLPU[t]).replace(QString('.'), QString(',')))
                    else:
                        dataActionTypeDict = dataDict
                        dataActionTypeKeys = dataActionTypeDict.keys()
                        dataActionTypeKeys.sort(key=lambda x: x[1])
                        for dataActionTypeKey in dataActionTypeKeys:
                            actionTypeId, actionTypeInfo = dataActionTypeKey
                            i = table.addRow()
                            table.setText(i, 0, actionTypeInfo[0])
                            table.setText(i, 1, actionTypeInfo[1])
                            for m, medicalAidTypeName in enumerate(medicalAidTypeList):
                                table.setText(i, 2+m*2, dataDict[dataActionTypeKey].get(medicalAidTypeName, [0]*2)[0])
                                table.setText(i, 3+m*2, forceStringEx(dataDict[dataActionTypeKey].get(medicalAidTypeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                totalReport[2+m*2] += dataDict[dataActionTypeKey].get(medicalAidTypeName, [0]*2)[0]
                                totalReport[3+m*2] += dataDict[dataActionTypeKey].get(medicalAidTypeName, [0]*2)[1]
                else:
                    if detailByOrgStructures:
                        totalByLPU = [0]*(self.tableColumnsLen+4)
                        for o, orgStructureName in enumerate(orgStructureList):
                            totalByOrgStructure = [0]*(self.tableColumnsLen+4)
                            f = table.addRow()
                            i = f
                            table.setText(f, 0, orgStructureName, CReportBase.TableTotal, blockFormat=CReportBase.AlignCenter)
                            table.mergeCells(f, 0,  1, self.tableColumnsLen+2)
                            dataActionTypeDict = dataDict[orgStructureName]
                            dataActionTypeKeys = dataActionTypeDict.keys()
                            dataActionTypeKeys.sort(key=lambda x: x[1])
                            for dataActionTypeKey in dataActionTypeKeys:
                                actionTypeId, actionTypeInfo = dataActionTypeKey
                                i = table.addRow()
                                table.setText(i, 0, actionTypeInfo[0])
                                table.setText(i, 1, actionTypeInfo[1])
                                table.setText(i, 2, dataDict[orgStructureName][dataActionTypeKey][0])
                                totalByOrgStructure[2] += dataDict[orgStructureName][dataActionTypeKey][0]
                                table.setText(i, 3, forceStringEx(dataDict[orgStructureName][dataActionTypeKey][1]).replace(QString('.'), QString(',')))
                                totalByOrgStructure[3] += dataDict[orgStructureName][dataActionTypeKey][1]
                            i = table.addRow()
                            table.setText(i, 0, u'Итого по подразделению %s'%(orgStructureName), CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                            table.mergeCells(i, 0,  1, 2)
                            for t in range(self.groupingRange):
                                table.setText(i, t+2, forceStringEx(totalByOrgStructure[t+2]).replace(QString('.'), QString(',')))
                                totalByLPU[t] += totalByOrgStructure[t+2]
                        i = table.addRow()
                        table.setText(i, 0, u'ИТОГО', CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                        table.mergeCells(i, 0,  1, 2)
                        for t in range(self.groupingRange):
                            table.setText(i, t+2, forceStringEx(totalByLPU[t]).replace(QString('.'), QString(',')))
                    else:
                        dataActionTypeDict = dataDict
                        dataActionTypeKeys = dataActionTypeDict.keys()
                        dataActionTypeKeys.sort(key=lambda x: x[1])
                        for dataActionTypeKey in dataActionTypeKeys:
                            actionTypeId, actionTypeInfo = dataActionTypeKey
                            i = table.addRow()
                            table.setText(i, 0, actionTypeInfo[0])
                            table.setText(i, 1, actionTypeInfo[1])
                            table.setText(i, 2, dataDict[dataActionTypeKey][0])
                            table.setText(i, 3, forceStringEx(dataDict[dataActionTypeKey][1]).replace(QString('.'), QString(',')))
                            totalReport[2] += dataDict[dataActionTypeKey][0]
                            totalReport[3] += dataDict[dataActionTypeKey][1]
        if totalReport and not detailByOrgStructures:
            i = table.addRow()
            table.setText(i, 0, u'ИТОГО', CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
            table.mergeCells(i, 0,  1, 2)
            for t, val in enumerate(totalReport):
                if t >= 2:
                    table.setText(i, t, forceStringEx(val).replace(QString('.'), QString(',')))
        return doc


class CReportUETActionByPersons(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Сводка УЕТ по исполнителям')
        self.orientation = CPageFormat.Landscape

    def getSetupDialog(self, parent):
        result = CReportUETActionsSetup(parent)
        result.setDetailByActionTypeClassesVisible(False)
        result.setDetailByActionTypeGroupVisible(False)
        result.setDetailByActionTypeVisible(True)
        result.setDetailByClientVisible(True)
        result.setTitle(self.title())
        return result


    def dumpParams(self, cursor, params):
        db = QtGui.qApp.db
        self.params = params
        nameList = []
        begDate          = params.get('begDate', QDate())
        endDate          = params.get('endDate', QDate())
        financeId        = params.get('financeId', None)
        medicalAidTypeId = params.get('medicalAidTypeId', None)
        orgStructureId   = params.get('orgStructureId', None)
        actionStatusList = params.get('actionStatusList', [])
        description = []
        if begDate and endDate:
            description.append(dateRangeAsStr(u'', begDate, endDate))
        if orgStructureId:
            orgStrName = getOrgStructureName(orgStructureId)
            description.append(u'Подразделение: %s'%orgStrName)
        if financeId:
            financeName = CFinanceType.getNameById(financeId)
            description.append(u'Тип финансирования: %s'%financeName)
        if medicalAidTypeId:
            medicalAidTypeName = getMedicalAidTypeName(medicalAidTypeId)
            description.append(u'Тип мед помощи: %s'%medicalAidTypeName)
        if actionStatusList:
            for i, name in enumerate(actionStatusList):
                    nameList.append(CActionStatus.names[name])
            description.append(u'Статус действия: ' + u','.join(name for name in nameList if name))
        chkActionTypeClass = params.get('chkActionTypeClass', False)
        actionTypeClass = params.get('actionTypeClass', None)
        actionTypeId = params.get('actionTypeId', None)
        if chkActionTypeClass:
            if actionTypeClass is not None:
                description.append(u'Класс действия: %s'%{0: u'Статус',
                                                   1: u'Диагностика',
                                                   2: u'Лечение',
                                                   3: u'Прочие мероприятия'}.get(actionTypeClass, u'Статус'))

            if actionTypeId:
                description.append(u'Тип действия: %s'%forceString(db.translate('ActionType', 'id', actionTypeId, 'CONCAT_WS(\' | \', code,name)')))
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertBlock(CReportBase.AlignCenter)
        cursor.movePosition(QtGui.QTextCursor.End)
        columns = [ ('100%', [], CReportBase.AlignLeft)]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)


    def build(self, params):
        detailByOrgStructures  = params.get('detailByOrgStructures', 0)
        detailByFinance        = params.get('detailByFinance', 0)
        detailByMedicalAidKind = params.get('detailByMedicalAidType', 0)
        detailByClient         = params.get('detailByClient', False)
        detailByActionTypeVisible = params.get('detailByActionTypeVisible', False)
        showAssistants         = params.get('showAssistants', 0)
        personParam            = params.get('personParam', 0)
        postParam              = params.get('postParam', 0)
        financeList = []
        medicalAidKindList = []
        orgStructureList = []
        personsList = []
        mapPersonToOrgStrAndSpeciality = {}
        dataDict = {}
        query = selectGroupingData(params, True)
        while query.next():
            record = query.record()
            financeName        = forceString(record.value('financeName'))
            medicalAidKindName = forceString(record.value('medicalAidKindName'))
            orgStructureName   = forceString(record.value('orgStructureName'))
            specialityName     = forceString(record.value('specialityName'))
            personId           = forceRef(record.value('personId'))
            personName         = forceString(record.value('personName'))
            if (personId, personName) not in mapPersonToOrgStrAndSpeciality.keys():
                mapPersonToOrgStrAndSpeciality[(personId, personName)] = [specialityName, orgStructureName]
            if showAssistants:
                assistantName = forceString(record.value('assistantName'))
                assistantId = forceRef(record.value('assistantId'))
            else:
                assistantName = None
                assistantId = None
            if financeName not in financeList:
                financeList.append(financeName)
            if medicalAidKindName not in medicalAidKindList:
                medicalAidKindList.append(medicalAidKindName)
            if ((personId, personName), (assistantId, assistantName)) not in personsList:
                if showAssistants:
                    personsList.append(((personId, personName), (assistantId, assistantName)))
                else:
                    personsList.append(((personId, personName), (None, None)))
            if orgStructureName not in orgStructureList:
                orgStructureList.append(orgStructureName)
        personsList.sort(key=lambda x: (x[0][1], x[1][1]))

        showCols = 0
        if showAssistants:
            showCols += 1
        if detailByClient:
            showCols += 1
        if detailByActionTypeVisible:
            showCols += 2
        medicalAidKindList.sort()
        if detailByFinance and detailByMedicalAidKind:
            self.tableColumnsLen = ((len(medicalAidKindList)+1)*2)*(len(financeList)+1) + showAssistants + (2 if detailByActionTypeVisible else 0)
            columnsLen = ((len(medicalAidKindList)+1)*2)*(len(financeList)+1) + showAssistants
        elif detailByFinance:
            self.tableColumnsLen = len(financeList)*3 + showAssistants + (2 if detailByActionTypeVisible else 0)
            columnsLen = len(financeList)*3 + showAssistants
        elif detailByMedicalAidKind:
            self.tableColumnsLen = len(medicalAidKindList)*2 + showAssistants + (2 if detailByActionTypeVisible else 0)
            columnsLen = len(medicalAidKindList)*2 + showAssistants
        else:
            self.tableColumnsLen = 3 + showAssistants + (2 if detailByActionTypeVisible else 0)
            columnsLen = 3 + showAssistants
        if detailByFinance or detailByMedicalAidKind or detailByClient or detailByActionTypeVisible:
            if detailByClient and detailByActionTypeVisible and (detailByFinance or detailByMedicalAidKind):
                detailedWidth = 70.0/(columnsLen if columnsLen > 0 else 1)
            elif detailByClient:
                detailedWidth = 60.0/(columnsLen if columnsLen > 0 else 1)
            elif detailByActionTypeVisible:
                detailedWidth = 75.0/(columnsLen+2)
            else:
                detailedWidth = 70.0/(columnsLen if columnsLen > 0 else 1)
        else:
            detailedWidth = None

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.setBlockFormat(CReportBase.AlignCenter)
        cursor.insertText(self.title())
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.setBlockFormat(CReportBase.AlignCenter)
        cursor.insertText(self.title())
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        colWidth = '5%' if ((detailByClient or detailByActionTypeVisible) and (detailByFinance or detailByMedicalAidKind)) else '10%'
        tableColumns = [
                        ('25%' if not detailedWidth else colWidth, [u'ФИО врача'],     CReportBase.AlignLeft),
                        ('20%' if not detailedWidth else colWidth, [u'Специальность'], CReportBase.AlignLeft),
                        ('35%' if not detailedWidth else colWidth, [u'Подразделение'], CReportBase.AlignLeft),
                        ]
        amountUETCols = [
                        ('15%' if detailedWidth else colWidth, [u'иссл.'], CReportBase.AlignRight),
                        ('15%' if detailedWidth else colWidth, [u'УЕТ'],   CReportBase.AlignRight),
                        ]
        assistantCols = [
                        (colWidth, [u'Ассистент'], CReportBase.AlignLeft),
                        ]
        if showAssistants:
            tableColumns.extend(assistantCols)
        if detailByClient:
            tableColumns.append(('25%' if not detailedWidth else colWidth, [u'ФИО пациента'], CReportBase.AlignLeft))
        if detailByActionTypeVisible:
            tableColumns.append((colWidth, [u'Код исследования'], CReportBase.AlignLeft))
            tableColumns.append((colWidth, [u'Наименование исследования'], CReportBase.AlignLeft))
        if detailByFinance and detailByMedicalAidKind:
            for i, financeName in enumerate(financeList):
                k = True
                for j, medicalAidKindName in enumerate(medicalAidKindList):
                    if k:
                        tableColumns.append(('%s'%detailedWidth+'%', [financeName, medicalAidKindName, u'иссл'], CReportBase.AlignCenter))
                        k = False
                    else:
                        tableColumns.append(('%s'%detailedWidth+'%', [u'', medicalAidKindName, u'иссл'], CReportBase.AlignCenter))
                    tableColumns.append(('%s'%detailedWidth+'%', [u'', u'', u'УЕТ'], CReportBase.AlignCenter))
                tableColumns.append(('%s'%detailedWidth+'%', [u'', u'Итого', u'иссл'], CReportBase.AlignCenter))
                tableColumns.append(('%s'%detailedWidth+'%', [u'', u'', u'УЕТ'], CReportBase.AlignCenter))
            k = True
            for j, medicalAidKindName in enumerate(medicalAidKindList):
                if k:
                    tableColumns.append(('%s'%detailedWidth+'%', [u'За счет всех источников', medicalAidKindName, u'иссл'], CReportBase.AlignCenter))
                    k = False
                else:
                    tableColumns.append(('%s'%detailedWidth+'%', [u'', medicalAidKindName, u'иссл'], CReportBase.AlignCenter))
                tableColumns.append(('%s'%detailedWidth+'%', [u'', u'', u'УЕТ'], CReportBase.AlignCenter))
            tableColumns.append(('%s'%detailedWidth+'%', [u'', u'Итого', u'иссл'], CReportBase.AlignCenter))
            tableColumns.append(('%s'%detailedWidth+'%', [u'', u'', u'УЕТ'], CReportBase.AlignCenter))
        elif detailByFinance:
            for i, financeName in enumerate(financeList):
                tableColumns.append(('%s'%detailedWidth+'%', [financeName, u'иссл'], CReportBase.AlignCenter))
                tableColumns.append(('%s'%detailedWidth+'%', [u'', u'УЕТ'], CReportBase.AlignCenter))
            tableColumns.append(('%s'%detailedWidth+'%', [u'За счет всех источников', u'иссл'], CReportBase.AlignCenter))
            tableColumns.append(('%s'%detailedWidth+'%', [u'', u'УЕТ'], CReportBase.AlignCenter))
        elif detailByMedicalAidKind:
            for i, medicalAidKindName in enumerate(medicalAidKindList):
                tableColumns.append(('%s'%detailedWidth+'%', [medicalAidKindName, u'иссл'], CReportBase.AlignCenter))
                tableColumns.append(('%s'%detailedWidth+'%', [u'', u'УЕТ'], CReportBase.AlignCenter))
        else:
            tableColumns.extend(amountUETCols)
        table = createTable(cursor, tableColumns)
        if detailByFinance and detailByMedicalAidKind:
            if detailByClient:
                table.mergeCells(0, 0, 3, 1)
                table.mergeCells(0, 1, 3, 1)
                table.mergeCells(0, 2, 3, 1)
                if showAssistants:
                    table.mergeCells(0, 3, 3, 1)
                table.mergeCells(0, 4 if showAssistants else 3, 3, 1)
                if detailByActionTypeVisible:
                    table.mergeCells(0, 5 if showAssistants else 4, 3, 1)
                    table.mergeCells(0, 6 if showAssistants else 5, 3, 1)
                for i in range(len(financeList)+1):
                    lenMedicalCols = 2*len(medicalAidKindList)+2
                    table.mergeCells(0, 3+showCols+i*lenMedicalCols, 1, lenMedicalCols)
                for j in range((len(medicalAidKindList))*len(financeList)*4):
                    table.mergeCells(1, 3+showCols+2*j, 1, 2)
                    table.mergeCells(1, 5+showCols+2*j, 1, 2)
            else:
                table.mergeCells(0, 0, 3, 1)
                table.mergeCells(0, 1, 3, 1)
                table.mergeCells(0, 2, 3, 1)
                if showAssistants:
                    table.mergeCells(0, 3, 3, 1)
                if detailByActionTypeVisible:
                    table.mergeCells(0, 4 if showAssistants else 3, 3, 1)
                    table.mergeCells(0, 5 if showAssistants else 4, 3, 1)
                for i in range(len(financeList)+1):
                    lenMedicalCols = 2*len(medicalAidKindList)+2
                    table.mergeCells(0, 3+showCols+i*lenMedicalCols, 1, lenMedicalCols)
                for j in range((len(medicalAidKindList))*len(financeList)*3):
                    table.mergeCells(1, 3+showCols+2*j, 1, 2)
                    table.mergeCells(1, 5+showCols+2*j, 1, 2)
        elif detailByFinance:
            if detailByClient:
                table.mergeCells(0, 0, 2, 1)
                table.mergeCells(0, 1, 2, 1)
                table.mergeCells(0, 2, 2, 1)
                if showAssistants:
                    table.mergeCells(0, 3, 2, 1)
                table.mergeCells(0, 4 if showAssistants else 3, 2, 1)
                if detailByActionTypeVisible:
                    table.mergeCells(0, 5 if showAssistants else 4, 3, 1)
                    table.mergeCells(0, 6 if showAssistants else 5, 3, 1)
                for i in range(len(financeList)+2):
                    table.mergeCells(0, 3+showCols+i*2, 1, 2)
            else:
                table.mergeCells(0, 0, 2, 1)
                table.mergeCells(0, 1, 2, 1)
                table.mergeCells(0, 2, 2, 1)
                if showAssistants:
                    table.mergeCells(0, 3, 2, 1)
                if detailByActionTypeVisible:
                    table.mergeCells(0, 4 if showAssistants else 3, 3, 1)
                    table.mergeCells(0, 5 if showAssistants else 4, 3, 1)
                for i in range(len(financeList)+2):
                    table.mergeCells(0, 3+showCols+i*2, 1, 2)
        elif detailByMedicalAidKind:
            if detailByClient:
                table.mergeCells(0, 0, 2, 1)
                table.mergeCells(0, 1, 2, 1)
                table.mergeCells(0, 2, 2, 1)
                if showAssistants:
                    table.mergeCells(0, 3, 2, 1)
                table.mergeCells(0, 4 if showAssistants else 3, 2, 1)
                if detailByActionTypeVisible:
                    table.mergeCells(0, 5 if showAssistants else 4, 3, 1)
                    table.mergeCells(0, 6 if showAssistants else 5, 3, 1)
                for j in range(len(medicalAidKindList)+1):
                    table.mergeCells(0, 3+showCols+j*2, 1, 2)
                    table.mergeCells(0, 5+showCols+j*2, 1, 2)
            else:
                table.mergeCells(0, 0, 2, 1)
                table.mergeCells(0, 1, 2, 1)
                table.mergeCells(0, 2, 2, 1)
                if showAssistants:
                    table.mergeCells(0, 3, 2, 1)
                if detailByActionTypeVisible:
                    table.mergeCells(0, 4 if showAssistants else 3, 3, 1)
                    table.mergeCells(0, 5 if showAssistants else 4, 3, 1)
                for j in range(len(medicalAidKindList)+1):
                    table.mergeCells(0, 3+showCols+j*2, 1, 2)
                    table.mergeCells(0, 5+showCols+j*2, 1, 2)
        elif detailByClient:
            table.mergeCells(0, 0, 2, 1)
            table.mergeCells(0, 1, 2, 1)
            table.mergeCells(0, 2, 2, 1)
            if showAssistants:
                table.mergeCells(0, 3, 2, 1)
            if detailByActionTypeVisible:
                table.mergeCells(0, 4 if showAssistants else 3, 3, 1)
                table.mergeCells(0, 5 if showAssistants else 4, 3, 1)
            table.mergeCells(0, 4 if showAssistants else 3, 2, 1)

        self.groupingRange = table.table.columns()-3-showAssistants-(1 if detailByClient else 0) - (2 if detailByActionTypeVisible else 0)
        query = selectData(params, True)
        if query is None:
            return doc
        while query.next():
            record = query.record()
            medicalAidKindName = forceString(record.value('medicalAidKindName'))
            orgStructureName   = forceString(record.value('orgStructureName'))
            financeName        = forceString(record.value('financeName'))
            personId           = forceRef(record.value('personId'))
            personName         = (personId, forceString(record.value('personName')))
            actionSpecification = forceRef(record.value('actionSpecification_id'))
            amount = forceInt(record.value('amount'))
            uetDoctor = forceDouble(record.value('uetDoctor'))
            uetAverageMedWorker = forceDouble(record.value('uetAverageMedWorker'))
            uetAssistantDoctor = forceDouble(record.value('uetAssistantDoctor'))
            uetAssistantAverageMedWorker = forceDouble(record.value('uetAssistantAverageMedWorker'))
            specificationUetDoctor = forceDouble(record.value('specificationUetDoctor'))
            specificationUetAverageMedWorker = forceDouble(record.value('specificationUetAverageMedWorker'))
            specificationUetAssistantDoctor = forceDouble(record.value('specificationUetAssistantDoctor'))
            specificationUetAssistantAverageMedWorker = forceDouble(record.value('specificationUetAssistantAverageMedWorker'))
            if detailByClient:
                clientId = forceRef(record.value('clientId'))
                lastName = forceStringEx(record.value('lastName'))
                firstName = forceStringEx(record.value('firstName'))
                patrName = forceStringEx(record.value('patrName'))
                clientName = formatNameInt(lastName, firstName, patrName)
            if showAssistants:
                assistantId = forceRef(record.value('assistantId'))
                assistantName = (assistantId, forceString(record.value('assistantName')))
            else:
                assistantId = None
                assistantName = (assistantId, None)
            if actionSpecification:
                if personParam:
                    if postParam: #ассистент+средний мед персонал
                        uet = specificationUetAssistantAverageMedWorker
                    else: #ассистент+врач
                        uet = specificationUetAssistantDoctor
                else:
                    if postParam: #исполнитель+средний мед персонал
                        uet = specificationUetAverageMedWorker
                    else: #исполнитель+врач
                        uet = specificationUetDoctor
            else:
                if personParam:
                    if postParam: #ассистент+средний мед персонал
                        uet = uetAssistantAverageMedWorker
                    else: #ассистент+врач
                        uet = uetAssistantDoctor
                else:
                    if postParam: #исполнитель+средний мед персонал
                        uet = uetAverageMedWorker
                    else: #исполнитель+врач
                        uet = uetDoctor
            if detailByActionTypeVisible:
                actionTypeId = forceRef(record.value('actionTypeId'))
                actionTypeCode = forceStringEx(record.value('actionTypeCode'))
                actionTypeName = forceStringEx(record.value('actionTypeName'))
                keyActionType = (actionTypeId, (actionTypeCode, actionTypeName))
                if detailByOrgStructures:
                    if detailByFinance and detailByMedicalAidKind:
                        if orgStructureName not in dataDict.keys():
                            dataDict[orgStructureName] = {}
                        if (personName, assistantName) not in dataDict[orgStructureName].keys():
                            dataDict[orgStructureName][(personName, assistantName)] = {}
                        if detailByClient:
                            if (clientId, clientName) not in dataDict[orgStructureName][(personName, assistantName)].keys():
                                dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)] = {}
                            if keyActionType not in dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)].keys():
                                dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)][keyActionType] = {}
                            if financeName not in dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)][keyActionType].keys():
                                dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)][keyActionType][financeName] = {}
                            if medicalAidKindName not in dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)][keyActionType][financeName].keys():
                                dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)][keyActionType][financeName][medicalAidKindName] = [0]*2
                            dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)][keyActionType][financeName][medicalAidKindName][0] += amount
                            dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)][keyActionType][financeName][medicalAidKindName][1] += uet
                        else:
                            if keyActionType not in dataDict[orgStructureName][(personName, assistantName)].keys():
                                dataDict[orgStructureName][(personName, assistantName)][keyActionType] = {}
                            if financeName not in dataDict[orgStructureName][(personName, assistantName)][keyActionType].keys():
                                dataDict[orgStructureName][(personName, assistantName)][keyActionType][financeName] = {}
                            if medicalAidKindName not in dataDict[orgStructureName][(personName, assistantName)][keyActionType][financeName].keys():
                                dataDict[orgStructureName][(personName, assistantName)][keyActionType][financeName][medicalAidKindName] = [0]*2
                            dataDict[orgStructureName][(personName, assistantName)][keyActionType][financeName][medicalAidKindName][0] += amount
                            dataDict[orgStructureName][(personName, assistantName)][keyActionType][financeName][medicalAidKindName][1] += uet
                    elif detailByFinance:
                        if orgStructureName not in dataDict.keys():
                            dataDict[orgStructureName] = {}
                        if (personName, assistantName) not in dataDict[orgStructureName].keys():
                            dataDict[orgStructureName][(personName, assistantName)] = {}
                        if detailByClient:
                            if (clientId, clientName) not in dataDict[orgStructureName][(personName, assistantName)].keys():
                                dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)] = {}
                            if keyActionType not in dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)].keys():
                                dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)][keyActionType] = {}
                            if financeName not in dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)][keyActionType].keys():
                                dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)][keyActionType][financeName] = [0]*2
                            dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)][keyActionType][financeName][0] += amount
                            dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)][keyActionType][financeName][1] += uet
                        else:
                            if keyActionType not in dataDict[orgStructureName][(personName, assistantName)].keys():
                                dataDict[orgStructureName][(personName, assistantName)][keyActionType] = {}
                            if financeName not in dataDict[orgStructureName][(personName, assistantName)][keyActionType].keys():
                                dataDict[orgStructureName][(personName, assistantName)][keyActionType][financeName] = [0]*2
                            dataDict[orgStructureName][(personName, assistantName)][keyActionType][financeName][0] += amount
                            dataDict[orgStructureName][(personName, assistantName)][keyActionType][financeName][1] += uet
                    elif detailByMedicalAidKind:
                        if orgStructureName not in dataDict.keys():
                            dataDict[orgStructureName] = {}
                        if (personName, assistantName) not in dataDict[orgStructureName].keys():
                            dataDict[orgStructureName][(personName, assistantName)] = {}
                        if detailByClient:
                            if (clientId, clientName) not in dataDict[orgStructureName][(personName, assistantName)].keys():
                                dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)] = {}
                            if keyActionType not in dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)].keys():
                                dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)][keyActionType] = {}
                            if medicalAidKindName not in dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)][keyActionType].keys():
                                dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)][keyActionType][medicalAidKindName] = [0]*2
                            dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)][keyActionType][medicalAidKindName][0] += amount
                            dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)][keyActionType][medicalAidKindName][1] += uet
                        else:
                            if keyActionType not in dataDict[orgStructureName][(personName, assistantName)].keys():
                                dataDict[orgStructureName][(personName, assistantName)][keyActionType] = {}
                            if medicalAidKindName not in dataDict[orgStructureName][(personName, assistantName)][keyActionType].keys():
                                dataDict[orgStructureName][(personName, assistantName)][keyActionType][medicalAidKindName] = [0]*2
                            dataDict[orgStructureName][(personName, assistantName)][keyActionType][medicalAidKindName][0] += amount
                            dataDict[orgStructureName][(personName, assistantName)][keyActionType][medicalAidKindName][1] += uet
                    else:
                        if orgStructureName not in dataDict.keys():
                            dataDict[orgStructureName] = {}
                        if detailByClient:
                            if (personName, assistantName) not in dataDict[orgStructureName].keys():
                                dataDict[orgStructureName][(personName, assistantName)] = {}
                            if (clientId, clientName) not in dataDict[orgStructureName][(personName, assistantName)].keys():
                                dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)] = {}
                            if keyActionType not in dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)].keys():
                                dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)][keyActionType] = [0]*2
                            dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)][keyActionType][0] += amount
                            dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)][keyActionType][1] += uet
                        else:
                            if (personName, assistantName) not in dataDict[orgStructureName].keys():
                                dataDict[orgStructureName][(personName, assistantName)] = {}
                            if keyActionType not in dataDict[orgStructureName][(personName, assistantName)].keys():
                                dataDict[orgStructureName][(personName, assistantName)][keyActionType] = [0]*2
                            dataDict[orgStructureName][(personName, assistantName)][keyActionType][0] += amount
                            dataDict[orgStructureName][(personName, assistantName)][keyActionType][1] += uet
                else:
                    if detailByFinance and detailByMedicalAidKind:
                        if (personName, assistantName) not in dataDict.keys():
                            dataDict[(personName, assistantName)] = {}
                        if detailByClient:
                            if (clientId, clientName) not in dataDict[(personName, assistantName)].keys():
                                dataDict[(personName, assistantName)][(clientId, clientName)] = {}
                            if keyActionType not in dataDict[(personName, assistantName)][(clientId, clientName)].keys():
                                dataDict[(personName, assistantName)][(clientId, clientName)][keyActionType] = {}
                            if financeName not in dataDict[(personName, assistantName)][(clientId, clientName)][keyActionType].keys():
                                dataDict[(personName, assistantName)][(clientId, clientName)][keyActionType][financeName] = {}
                            if medicalAidKindName not in dataDict[(personName, assistantName)][(clientId, clientName)][keyActionType][financeName].keys():
                                dataDict[(personName, assistantName)][(clientId, clientName)][keyActionType][financeName][medicalAidKindName] = [0]*2
                            dataDict[(personName, assistantName)][(clientId, clientName)][keyActionType][financeName][medicalAidKindName][0] += amount
                            dataDict[(personName, assistantName)][(clientId, clientName)][keyActionType][financeName][medicalAidKindName][1] += uet
                        else:
                            if keyActionType not in dataDict[(personName, assistantName)].keys():
                                dataDict[(personName, assistantName)][keyActionType] = {}
                            if financeName not in dataDict[(personName, assistantName)][keyActionType].keys():
                                dataDict[(personName, assistantName)][keyActionType][financeName] = {}
                            if medicalAidKindName not in dataDict[(personName, assistantName)][keyActionType][financeName].keys():
                                dataDict[(personName, assistantName)][keyActionType][financeName][medicalAidKindName] = [0]*2
                            dataDict[(personName, assistantName)][keyActionType][financeName][medicalAidKindName][0] += amount
                            dataDict[(personName, assistantName)][keyActionType][financeName][medicalAidKindName][1] += uet
                    elif detailByFinance:
                        if (personName, assistantName) not in dataDict.keys():
                            dataDict[(personName, assistantName)] = {}
                        if detailByClient:
                            if (clientId, clientName) not in dataDict[(personName, assistantName)].keys():
                                dataDict[(personName, assistantName)][(clientId, clientName)] = {}
                            if keyActionType not in dataDict[(personName, assistantName)][(clientId, clientName)].keys():
                                dataDict[(personName, assistantName)][(clientId, clientName)][keyActionType] = {}
                            if financeName not in dataDict[(personName, assistantName)][(clientId, clientName)][keyActionType].keys():
                                dataDict[(personName, assistantName)][(clientId, clientName)][keyActionType][financeName] = [0]*2
                            dataDict[(personName, assistantName)][(clientId, clientName)][keyActionType][financeName][0] += amount
                            dataDict[(personName, assistantName)][(clientId, clientName)][keyActionType][financeName][1] += uet
                        else:
                            if keyActionType not in dataDict[(personName, assistantName)].keys():
                                dataDict[(personName, assistantName)][keyActionType] = {}
                            if financeName not in dataDict[(personName, assistantName)][keyActionType].keys():
                                dataDict[(personName, assistantName)][keyActionType][financeName] = [0]*2
                            dataDict[(personName, assistantName)][keyActionType][financeName][0] += amount
                            dataDict[(personName, assistantName)][keyActionType][financeName][1] += uet
                    elif detailByMedicalAidKind:
                        if (personName, assistantName) not in dataDict.keys():
                            dataDict[(personName, assistantName)] = {}
                        if detailByClient:
                            if (clientId, clientName) not in dataDict[(personName, assistantName)].keys():
                                dataDict[(personName, assistantName)][(clientId, clientName)] = {}
                            if keyActionType not in dataDict[(personName, assistantName)][(clientId, clientName)].keys():
                                dataDict[(personName, assistantName)][(clientId, clientName)][keyActionType] = {}
                            if medicalAidKindName not in dataDict[(personName, assistantName)][(clientId, clientName)][keyActionType].keys():
                                dataDict[(personName, assistantName)][(clientId, clientName)][keyActionType][medicalAidKindName] = [0]*2
                            dataDict[(personName, assistantName)][(clientId, clientName)][keyActionType][medicalAidKindName][0] += amount
                            dataDict[(personName, assistantName)][(clientId, clientName)][keyActionType][medicalAidKindName][1] += uet
                        else:
                            if keyActionType not in dataDict[(personName, assistantName)].keys():
                                dataDict[(personName, assistantName)][keyActionType] = {}
                            if medicalAidKindName not in dataDict[(personName, assistantName)][keyActionType].keys():
                                dataDict[(personName, assistantName)][keyActionType][medicalAidKindName] = [0]*2
                            dataDict[(personName, assistantName)][keyActionType][medicalAidKindName][0] += amount
                            dataDict[(personName, assistantName)][keyActionType][medicalAidKindName][1] += uet
                    else:
                        if detailByClient:
                            if (personName, assistantName) not in dataDict.keys():
                                dataDict[(personName, assistantName)] = {}
                            if (clientId, clientName) not in dataDict[(personName, assistantName)].keys():
                                dataDict[(personName, assistantName)][(clientId, clientName)] = {}
                            if keyActionType not in dataDict[(personName, assistantName)][(clientId, clientName)].keys():
                                dataDict[(personName, assistantName)][(clientId, clientName)][keyActionType] = [0]*2
                            dataDict[(personName, assistantName)][(clientId, clientName)][keyActionType][0] += amount
                            dataDict[(personName, assistantName)][(clientId, clientName)][keyActionType][1] += uet
                        else:
                            if (personName, assistantName) not in dataDict.keys():
                                dataDict[(personName, assistantName)] = {}
                            if keyActionType not in dataDict[(personName, assistantName)].keys():
                                dataDict[(personName, assistantName)][keyActionType] = [0]*2
                            dataDict[(personName, assistantName)][keyActionType][0] += amount
                            dataDict[(personName, assistantName)][keyActionType][1] += uet
            else:
                if detailByOrgStructures:
                    if detailByFinance and detailByMedicalAidKind:
                        if orgStructureName not in dataDict.keys():
                            dataDict[orgStructureName] = {}
                        if (personName, assistantName) not in dataDict[orgStructureName].keys():
                            dataDict[orgStructureName][(personName, assistantName)] = {}
                        if detailByClient:
                            if (clientId, clientName) not in dataDict[orgStructureName][(personName, assistantName)].keys():
                                dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)] = {}
                            if financeName not in dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)].keys():
                                dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)][financeName] = {}
                            if medicalAidKindName not in dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)][financeName].keys():
                                dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)][financeName][medicalAidKindName] = [0]*2
                            dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)][financeName][medicalAidKindName][0] += amount
                            dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)][financeName][medicalAidKindName][1] += uet
                        else:
                            if financeName not in dataDict[orgStructureName][(personName, assistantName)].keys():
                                dataDict[orgStructureName][(personName, assistantName)][financeName] = {}
                            if medicalAidKindName not in dataDict[orgStructureName][(personName, assistantName)][financeName].keys():
                                dataDict[orgStructureName][(personName, assistantName)][financeName][medicalAidKindName] = [0]*2
                            dataDict[orgStructureName][(personName, assistantName)][financeName][medicalAidKindName][0] += amount
                            dataDict[orgStructureName][(personName, assistantName)][financeName][medicalAidKindName][1] += uet
                    elif detailByFinance:
                        if orgStructureName not in dataDict.keys():
                            dataDict[orgStructureName] = {}
                        if (personName, assistantName) not in dataDict[orgStructureName].keys():
                            dataDict[orgStructureName][(personName, assistantName)] = {}
                        if detailByClient:
                            if (clientId, clientName) not in dataDict[orgStructureName][(personName, assistantName)].keys():
                                dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)] = {}
                            if financeName not in dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)].keys():
                                dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)][financeName] = [0]*2
                            dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)][financeName][0] += amount
                            dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)][financeName][1] += uet
                        else:
                            if financeName not in dataDict[orgStructureName][(personName, assistantName)].keys():
                                dataDict[orgStructureName][(personName, assistantName)][financeName] = [0]*2
                            dataDict[orgStructureName][(personName, assistantName)][financeName][0] += amount
                            dataDict[orgStructureName][(personName, assistantName)][financeName][1] += uet
                    elif detailByMedicalAidKind:
                        if orgStructureName not in dataDict.keys():
                            dataDict[orgStructureName] = {}
                        if (personName, assistantName) not in dataDict[orgStructureName].keys():
                            dataDict[orgStructureName][(personName, assistantName)] = {}
                        if detailByClient:
                            if (clientId, clientName) not in dataDict[orgStructureName][(personName, assistantName)].keys():
                                dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)] = {}
                            if medicalAidKindName not in dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)].keys():
                                dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)][medicalAidKindName] = [0]*2
                            dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)][medicalAidKindName][0] += amount
                            dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)][medicalAidKindName][1] += uet
                        else:
                            if medicalAidKindName not in dataDict[orgStructureName][(personName, assistantName)].keys():
                                dataDict[orgStructureName][(personName, assistantName)][medicalAidKindName] = [0]*2
                            dataDict[orgStructureName][(personName, assistantName)][medicalAidKindName][0] += amount
                            dataDict[orgStructureName][(personName, assistantName)][medicalAidKindName][1] += uet
                    else:
                        if orgStructureName not in dataDict.keys():
                            dataDict[orgStructureName] = {}
                        if detailByClient:
                            if (personName, assistantName) not in dataDict[orgStructureName].keys():
                                dataDict[orgStructureName][(personName, assistantName)] = {}
                            if (clientId, clientName) not in dataDict[orgStructureName][(personName, assistantName)].keys():
                                dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)] = [0]*2
                            dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)][0] += amount
                            dataDict[orgStructureName][(personName, assistantName)][(clientId, clientName)][1] += uet
                        else:
                            if (personName, assistantName) not in dataDict[orgStructureName].keys():
                                dataDict[orgStructureName][(personName, assistantName)] = [0]*2
                            dataDict[orgStructureName][(personName, assistantName)][0] += amount
                            dataDict[orgStructureName][(personName, assistantName)][1] += uet
                else:
                    if detailByFinance and detailByMedicalAidKind:
                        if (personName, assistantName) not in dataDict.keys():
                            dataDict[(personName, assistantName)] = {}
                        if detailByClient:
                            if (clientId, clientName) not in dataDict[(personName, assistantName)].keys():
                                dataDict[(personName, assistantName)][(clientId, clientName)] = {}
                            if financeName not in dataDict[(personName, assistantName)][(clientId, clientName)].keys():
                                dataDict[(personName, assistantName)][(clientId, clientName)][financeName] = {}
                            if medicalAidKindName not in dataDict[(personName, assistantName)][(clientId, clientName)][financeName].keys():
                                dataDict[(personName, assistantName)][(clientId, clientName)][financeName][medicalAidKindName] = [0]*2
                            dataDict[(personName, assistantName)][(clientId, clientName)][financeName][medicalAidKindName][0] += amount
                            dataDict[(personName, assistantName)][(clientId, clientName)][financeName][medicalAidKindName][1] += uet
                        else:
                            if financeName not in dataDict[(personName, assistantName)].keys():
                                dataDict[(personName, assistantName)][financeName] = {}
                            if medicalAidKindName not in dataDict[(personName, assistantName)][financeName].keys():
                                dataDict[(personName, assistantName)][financeName][medicalAidKindName] = [0]*2
                            dataDict[(personName, assistantName)][financeName][medicalAidKindName][0] += amount
                            dataDict[(personName, assistantName)][financeName][medicalAidKindName][1] += uet
                    elif detailByFinance:
                        if (personName, assistantName) not in dataDict.keys():
                            dataDict[(personName, assistantName)] = {}
                        if detailByClient:
                            if (clientId, clientName) not in dataDict[(personName, assistantName)].keys():
                                dataDict[(personName, assistantName)][(clientId, clientName)] = {}
                            if financeName not in dataDict[(personName, assistantName)][(clientId, clientName)].keys():
                                dataDict[(personName, assistantName)][(clientId, clientName)][financeName] = [0]*2
                            dataDict[(personName, assistantName)][(clientId, clientName)][financeName][0] += amount
                            dataDict[(personName, assistantName)][(clientId, clientName)][financeName][1] += uet
                        else:
                            if financeName not in dataDict[(personName, assistantName)].keys():
                                dataDict[(personName, assistantName)][financeName] = [0]*2
                            dataDict[(personName, assistantName)][financeName][0] += amount
                            dataDict[(personName, assistantName)][financeName][1] += uet
                    elif detailByMedicalAidKind:
                        if (personName, assistantName) not in dataDict.keys():
                            dataDict[(personName, assistantName)] = {}
                        if detailByClient:
                            if (clientId, clientName) not in dataDict[(personName, assistantName)].keys():
                                dataDict[(personName, assistantName)][(clientId, clientName)] = {}
                            if medicalAidKindName not in dataDict[(personName, assistantName)][(clientId, clientName)].keys():
                                dataDict[(personName, assistantName)][(clientId, clientName)][medicalAidKindName] = [0]*2
                            dataDict[(personName, assistantName)][(clientId, clientName)][medicalAidKindName][0] += amount
                            dataDict[(personName, assistantName)][(clientId, clientName)][medicalAidKindName][1] += uet
                        else:
                            if medicalAidKindName not in dataDict[(personName, assistantName)].keys():
                                dataDict[(personName, assistantName)][medicalAidKindName] = [0]*2
                            dataDict[(personName, assistantName)][medicalAidKindName][0] += amount
                            dataDict[(personName, assistantName)][medicalAidKindName][1] += uet
                    else:
                        if detailByClient:
                            if (personName, assistantName) not in dataDict.keys():
                                dataDict[(personName, assistantName)] = {}
                            if (clientId, clientName) not in dataDict[(personName, assistantName)].keys():
                                dataDict[(personName, assistantName)][(clientId, clientName)] = {}
                                dataDict[(personName, assistantName)][(clientId, clientName)] = [0]*2
                            dataDict[(personName, assistantName)][(clientId, clientName)][0] += amount
                            dataDict[(personName, assistantName)][(clientId, clientName)][1] += uet
                        else:
                            if (personName, assistantName) not in dataDict.keys():
                                dataDict[(personName, assistantName)] = [0]*2
                            dataDict[(personName, assistantName)][0] += amount
                            dataDict[(personName, assistantName)][1] += uet

        clientCol = 4 if showAssistants else 3
        if detailByActionTypeVisible:
            if detailByFinance and detailByMedicalAidKind:
                if detailByOrgStructures:
                    totalByLPU = [0]*(self.tableColumnsLen+4)
                    for o, orgStructureName in enumerate(orgStructureList):
                        #totalByOrgStructure = [0]*(self.tableColumnsLen+4)
                        totalByOrgStructure = [0]*table.table.columns()
                        f = table.addRow()
                        i = f
                        table.setText(f, 0, orgStructureName, CReportBase.TableTotal, blockFormat=CReportBase.AlignCenter)
                        table.mergeCells(f, 0,  1, self.tableColumnsLen+4)
                        for a, (personName, assistantName) in enumerate(personsList):
                            if (personName, assistantName) in dataDict[orgStructureName].keys():
                                i = table.addRow()
                                table.setText(i, 0, personName[1])
                                table.setText(i, 1, mapPersonToOrgStrAndSpeciality[personName][0])
                                table.setText(i, 2, mapPersonToOrgStrAndSpeciality[personName][1])
                                if showAssistants:
                                    table.setText(i, 3, assistantName[1])
                                if detailByClient:
                                    dataClientDict = dataDict[orgStructureName][(personName, assistantName)]
                                    dataClientKeys = dataClientDict.keys()
                                    dataClientKeys.sort(key=lambda x: x[1])
                                    clientRow = 1
                                    mergeRow = 0
                                    begClientRow = i
                                    for dataClientKey in dataClientKeys:
                                        table.setText(i, clientCol, dataClientKey[1])
                                        dataActionTypeDict = dataDict[orgStructureName][(personName, assistantName)][dataClientKey]
                                        dataActionTypeKeys = dataActionTypeDict.keys()
                                        dataActionTypeKeys.sort(key=lambda x: x[1])
                                        actionTypeRow = 1
                                        begActionTypeRow = i
                                        for dataActionTypeKey in dataActionTypeKeys:
                                            actionTypeId, actionTypeInfo = dataActionTypeKey
                                            table.setText(i, clientCol+1, actionTypeInfo[0])
                                            table.setText(i, clientCol+2, actionTypeInfo[1])
                                            totalFinance = {}
                                            totallyTotalFinance = [0]*2
                                            for f, financeName in enumerate(financeList):
                                                total = [0]*2
                                                for j, medicalAidKindName in enumerate(medicalAidKindList):
                                                    table.setText(i, 3+showCols+2*j+f*lenMedicalCols, dataDict[orgStructureName][(personName, assistantName)][dataClientKey][dataActionTypeKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[0])
                                                    totalByOrgStructure[3+showCols+2*j+f*lenMedicalCols] += dataDict[orgStructureName][(personName, assistantName)][dataClientKey][dataActionTypeKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[0]
                                                    table.setText(i, 4+showCols+2*j+f*lenMedicalCols, forceStringEx(dataDict[orgStructureName][(personName, assistantName)][dataClientKey][dataActionTypeKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                                    totalByOrgStructure[4+showCols+2*j+f*lenMedicalCols] += dataDict[orgStructureName][(personName, assistantName)][dataClientKey][dataActionTypeKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[1]
                                                    if medicalAidKindName not in totalFinance.keys():
                                                        totalFinance[medicalAidKindName] = [0]*2
                                                    total[0] += dataDict[orgStructureName][(personName, assistantName)][dataClientKey][dataActionTypeKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[0]
                                                    total[1] += dataDict[orgStructureName][(personName, assistantName)][dataClientKey][dataActionTypeKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[1]
                                                    totalFinance[medicalAidKindName][0] += dataDict[orgStructureName][(personName, assistantName)][dataClientKey][dataActionTypeKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[0]
                                                    totalFinance[medicalAidKindName][1] += dataDict[orgStructureName][(personName, assistantName)][dataClientKey][dataActionTypeKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[1]
                                                table.setText(i, 5+showCols+2*j+f*lenMedicalCols, total[0])
                                                totalByOrgStructure[5+showCols+2*j+f*lenMedicalCols] += total[0]
                                                table.setText(i, 6+showCols+2*j+f*lenMedicalCols, forceStringEx(total[1]).replace(QString('.'), QString(',')))
                                                totalByOrgStructure[6+showCols+2*j+f*lenMedicalCols] += total[1]
                                            for j, medicalAidKindName in enumerate(medicalAidKindList):
                                                table.setText(i, 3+showCols+2*j+(f+1)*lenMedicalCols, totalFinance.get(medicalAidKindName, [0]*2)[0])
                                                totalByOrgStructure[3+showCols+2*j+(f+1)*lenMedicalCols] += totalFinance.get(medicalAidKindName, [0]*2)[0]
                                                table.setText(i, 4+showCols+2*j+(f+1)*lenMedicalCols, forceStringEx(totalFinance.get(medicalAidKindName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                                totalByOrgStructure[4+showCols+2*j+(f+1)*lenMedicalCols] += totalFinance.get(medicalAidKindName, [0]*2)[1]
                                                totallyTotalFinance[0] += totalFinance.get(medicalAidKindName, [0]*2)[0]
                                                totallyTotalFinance[1] += totalFinance.get(medicalAidKindName, [0]*2)[1]
                                            table.setText(i, 5+showCols+2*j+(f+1)*lenMedicalCols, totallyTotalFinance[0])
                                            totalByOrgStructure[5+showCols+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[0]
                                            table.setText(i, 6+showCols+2*j+(f+1)*lenMedicalCols, forceStringEx(totallyTotalFinance[1]).replace(QString('.'), QString(',')))
                                            totalByOrgStructure[6+showCols+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[1]
                                            if actionTypeRow < len(dataActionTypeKeys):
                                                actionTypeRow += 1
                                                mergeRow += 1
                                                i = table.addRow()
                                        table.mergeCells(begActionTypeRow, clientCol,  actionTypeRow, 1)
                                        if clientRow < len(dataClientKeys):
                                            clientRow += 1
                                            i = table.addRow()
                                    table.mergeCells(begClientRow, 0,  clientRow + ((mergeRow + 1) if mergeRow else 0), 1)
                                    table.mergeCells(begClientRow, 1,  clientRow + ((mergeRow + 1) if mergeRow else 0), 1)
                                    table.mergeCells(begClientRow, 2,  clientRow + ((mergeRow + 1) if mergeRow else 0), 1)
                                else:
                                    dataActionTypeDict = dataDict[orgStructureName][(personName, assistantName)]
                                    dataActionTypeKeys = dataActionTypeDict.keys()
                                    dataActionTypeKeys.sort(key=lambda x: x[1])
                                    actionTypeRow = 1
                                    begActionTypeRow = i
                                    for dataActionTypeKey in dataActionTypeKeys:
                                        actionTypeId, actionTypeInfo = dataActionTypeKey
                                        table.setText(i, clientCol, actionTypeInfo[0])
                                        table.setText(i, clientCol+1, actionTypeInfo[1])
                                        totalFinance = {}
                                        totallyTotalFinance = [0]*2
                                        for f, financeName in enumerate(financeList):
                                            total = [0]*2
                                            for j, medicalAidKindName in enumerate(medicalAidKindList):
                                                table.setText(i, 3+showCols+2*j+f*lenMedicalCols, dataDict[orgStructureName][(personName, assistantName)][dataActionTypeKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[0])
                                                totalByOrgStructure[3+showCols+2*j+f*lenMedicalCols] += dataDict[orgStructureName][(personName, assistantName)][dataActionTypeKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[0]
                                                table.setText(i, 4+showCols+2*j+f*lenMedicalCols, forceStringEx(dataDict[orgStructureName][(personName, assistantName)][dataActionTypeKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                                totalByOrgStructure[4+showCols+2*j+f*lenMedicalCols] += dataDict[orgStructureName][(personName, assistantName)][dataActionTypeKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[1]
                                                if medicalAidKindName not in totalFinance.keys():
                                                    totalFinance[medicalAidKindName] = [0]*2
                                                total[0] += dataDict[orgStructureName][(personName, assistantName)][dataActionTypeKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[0]
                                                total[1] += dataDict[orgStructureName][(personName, assistantName)][dataActionTypeKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[1]
                                                totalFinance[medicalAidKindName][0] += dataDict[orgStructureName][(personName, assistantName)][dataActionTypeKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[0]
                                                totalFinance[medicalAidKindName][1] += dataDict[orgStructureName][(personName, assistantName)][dataActionTypeKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[1]
                                            table.setText(i, 5+showCols+2*j+f*lenMedicalCols, total[0])
                                            totalByOrgStructure[5+showCols+2*j+f*lenMedicalCols] += total[0]
                                            table.setText(i, 6+showCols+2*j+f*lenMedicalCols, forceStringEx(total[1]).replace(QString('.'), QString(',')))
                                            totalByOrgStructure[6+showCols+2*j+f*lenMedicalCols] += total[1]
                                        for j, medicalAidKindName in enumerate(medicalAidKindList):
                                            table.setText(i, 3+showCols+2*j+(f+1)*lenMedicalCols, totalFinance.get(medicalAidKindName, [0]*2)[0])
                                            totalByOrgStructure[3+showCols+2*j+(f+1)*lenMedicalCols] += totalFinance.get(medicalAidKindName, [0]*2)[0]
                                            table.setText(i, 4+showCols+2*j+(f+1)*lenMedicalCols, forceStringEx(totalFinance.get(medicalAidKindName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                            totalByOrgStructure[4+showCols+2*j+(f+1)*lenMedicalCols] += totalFinance.get(medicalAidKindName, [0]*2)[1]
                                            totallyTotalFinance[0] += totalFinance.get(medicalAidKindName, [0]*2)[0]
                                            totallyTotalFinance[1] += totalFinance.get(medicalAidKindName, [0]*2)[1]
                                        table.setText(i, 5+showCols+2*j+(f+1)*lenMedicalCols, totallyTotalFinance[0])
                                        totalByOrgStructure[5+showCols+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[0]
                                        table.setText(i, 6+showCols+2*j+(f+1)*lenMedicalCols, forceStringEx(totallyTotalFinance[1]).replace(QString('.'), QString(',')))
                                        totalByOrgStructure[6+showCols+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[1]
                                        if actionTypeRow < len(dataActionTypeKeys):
                                            actionTypeRow += 1
                                            i = table.addRow()
                                    table.mergeCells(begActionTypeRow, 0,  actionTypeRow, 1)
                                    table.mergeCells(begActionTypeRow, 1,  actionTypeRow, 1)
                                    table.mergeCells(begActionTypeRow, clientCol-1,  actionTypeRow, 1)
                        i = table.addRow()
                        table.setText(i, 0, u'Итого по подразделению %s'%(orgStructureName), CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                        table.mergeCells(i, 0,  1, 3+showCols)
                        for t in range(self.groupingRange):
                            table.setText(i, t+3+showCols, forceStringEx(totalByOrgStructure[t+3+showCols]).replace(QString('.'), QString(',')))
                            totalByLPU[t] += totalByOrgStructure[t+3+showCols]
                    i = table.addRow()
                    table.setText(i, 0, u'ИТОГО', CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                    table.mergeCells(i, 0,  1, 3+showCols)
                    for t in range(self.groupingRange):
                        table.setText(i, t+3+showCols, forceStringEx(totalByLPU[t]).replace(QString('.'), QString(',')))
                else:
                    for a, (personName, assistantName) in enumerate(personsList):
                        i = table.addRow()
                        table.setText(i, 0, personName[1])
                        table.setText(i, 1, mapPersonToOrgStrAndSpeciality[personName][0])
                        table.setText(i, 2, mapPersonToOrgStrAndSpeciality[personName][1])
                        if showAssistants:
                            table.setText(i, 3, assistantName[1])
                        if detailByClient:
                            dataClientDict = dataDict[(personName, assistantName)]
                            dataClientKeys = dataClientDict.keys()
                            dataClientKeys.sort(key=lambda x: x[1])
                            clientRow = 1
                            mergeRow  = 0
                            begClientRow = i
                            for dataClientKey in dataClientKeys:
                                table.setText(i, clientCol, dataClientKey[1])
                                dataActionTypeDict = dataDict[(personName, assistantName)][dataClientKey]
                                dataActionTypeKeys = dataActionTypeDict.keys()
                                dataActionTypeKeys.sort(key=lambda x: x[1])
                                actionTypeRow = 1
                                begActionTypeRow = i
                                for dataActionTypeKey in dataActionTypeKeys:
                                    actionTypeId, actionTypeInfo = dataActionTypeKey
                                    table.setText(i, clientCol+1, actionTypeInfo[0])
                                    table.setText(i, clientCol+2, actionTypeInfo[1])
                                    totalFinance = {}
                                    totallyTotalFinance = [0]*2
                                    for f, financeName in enumerate(financeList):
                                        total = [0]*2
                                        for j, medicalAidKindName in enumerate(medicalAidKindList):
                                            table.setText(i, 3+showCols+2*j+f*lenMedicalCols, dataDict[(personName, assistantName)][dataClientKey][dataActionTypeKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[0])
                                            table.setText(i, 4+showCols+2*j+f*lenMedicalCols, forceStringEx(dataDict[(personName, assistantName)][dataClientKey][dataActionTypeKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                            if medicalAidKindName not in totalFinance.keys():
                                                totalFinance[medicalAidKindName] = [0]*2
                                            total[0] += dataDict[(personName, assistantName)][dataClientKey][dataActionTypeKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[0]
                                            total[1] += dataDict[(personName, assistantName)][dataClientKey][dataActionTypeKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[1]
                                            totalFinance[medicalAidKindName][0] += dataDict[(personName, assistantName)][dataClientKey][dataActionTypeKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[0]
                                            totalFinance[medicalAidKindName][1] += dataDict[(personName, assistantName)][dataClientKey][dataActionTypeKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[1]
                                        table.setText(i, 5+showCols+2*j+f*lenMedicalCols, total[0])
                                        table.setText(i, 6+showCols+2*j+f*lenMedicalCols, forceStringEx(total[1]).replace(QString('.'), QString(',')))
                                    for j, medicalAidKindName in enumerate(medicalAidKindList):
                                        table.setText(i, 3+showCols+2*j+(f+1)*lenMedicalCols, totalFinance.get(medicalAidKindName, [0]*2)[0])
                                        table.setText(i, 4+showCols+2*j+(f+1)*lenMedicalCols, forceStringEx(totalFinance.get(medicalAidKindName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                        totallyTotalFinance[0] += totalFinance.get(medicalAidKindName, [0]*2)[0]
                                        totallyTotalFinance[1] += totalFinance.get(medicalAidKindName, [0]*2)[1]
                                    table.setText(i, 5+showCols+2*j+(f+1)*lenMedicalCols, totallyTotalFinance[0])
                                    table.setText(i, 6+showCols+2*j+(f+1)*lenMedicalCols, forceStringEx(totallyTotalFinance[1]).replace(QString('.'), QString(',')))
                                    if actionTypeRow < len(dataActionTypeKeys):
                                        actionTypeRow += 1
                                        mergeRow += 1
                                        i = table.addRow()
                                table.mergeCells(begActionTypeRow, clientCol,  actionTypeRow, 1)
                                if clientRow < len(dataClientKeys):
                                    clientRow += 1
                                    i = table.addRow()
                            table.mergeCells(begClientRow, 0, clientRow + ((mergeRow + 1) if mergeRow else 0), 1)
                            table.mergeCells(begClientRow, 1, clientRow + ((mergeRow + 1) if mergeRow else 0), 1)
                            table.mergeCells(begClientRow, 2, clientRow + ((mergeRow + 1) if mergeRow else 0), 1)
                        else:
                            dataActionTypeDict = dataDict[(personName, assistantName)]
                            dataActionTypeKeys = dataActionTypeDict.keys()
                            dataActionTypeKeys.sort(key=lambda x: x[1])
                            actionTypeRow = 1
                            begActionTypeRow = i
                            for dataActionTypeKey in dataActionTypeKeys:
                                actionTypeId, actionTypeInfo = dataActionTypeKey
                                table.setText(i, clientCol, actionTypeInfo[0])
                                table.setText(i, clientCol+1, actionTypeInfo[1])
                                totalFinance = {}
                                totallyTotalFinance = [0]*2
                                for f, financeName in enumerate(financeList):
                                    total = [0]*2
                                    for j, medicalAidKindName in enumerate(medicalAidKindList):
                                        table.setText(i, 3+showCols+2*j+f*lenMedicalCols, dataDict[(personName, assistantName)][dataActionTypeKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[0])
                                        table.setText(i, 4+showCols+2*j+f*lenMedicalCols, forceStringEx(dataDict[(personName, assistantName)][dataActionTypeKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                        if medicalAidKindName not in totalFinance.keys():
                                            totalFinance[medicalAidKindName] = [0]*2
                                        total[0] += dataDict[(personName, assistantName)][dataActionTypeKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[0]
                                        total[1] += dataDict[(personName, assistantName)][dataActionTypeKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[1]
                                        totalFinance[medicalAidKindName][0] += dataDict[(personName, assistantName)][dataActionTypeKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[0]
                                        totalFinance[medicalAidKindName][1] += dataDict[(personName, assistantName)][dataActionTypeKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[1]
                                    table.setText(i, 5+showCols+2*j+f*lenMedicalCols, total[0])
                                    table.setText(i, 6+showCols+2*j+f*lenMedicalCols, forceStringEx(total[1]).replace(QString('.'), QString(',')))
                                for j, medicalAidKindName in enumerate(medicalAidKindList):
                                    table.setText(i, 3+showCols+2*j+(f+1)*lenMedicalCols, totalFinance.get(medicalAidKindName, [0]*2)[0])
                                    table.setText(i, 4+showCols+2*j+(f+1)*lenMedicalCols, forceStringEx(totalFinance.get(medicalAidKindName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                    totallyTotalFinance[0] += totalFinance.get(medicalAidKindName, [0]*2)[0]
                                    totallyTotalFinance[1] += totalFinance.get(medicalAidKindName, [0]*2)[1]
                                table.setText(i, 5+showCols+2*j+(f+1)*lenMedicalCols, totallyTotalFinance[0])
                                table.setText(i, 6+showCols+2*j+(f+1)*lenMedicalCols, forceStringEx(totallyTotalFinance[1]).replace(QString('.'), QString(',')))
                                if actionTypeRow < len(dataActionTypeKeys):
                                    actionTypeRow += 1
                                    i = table.addRow()
                            table.mergeCells(begActionTypeRow, 0,  actionTypeRow, 1)
                            table.mergeCells(begActionTypeRow, 1,  actionTypeRow, 1)
                            table.mergeCells(begActionTypeRow, clientCol-1,  actionTypeRow, 1)
            elif detailByFinance:
                if detailByOrgStructures:
                    totalByLPU = [0]*(self.tableColumnsLen+4)
                    for o, orgStructureName in enumerate(orgStructureList):
                        #totalByOrgStructure = [0]*(self.tableColumnsLen+4)
                        totalByOrgStructure = [0]*table.table.columns()
                        f = table.addRow()
                        i = f
                        table.setText(f, 0, orgStructureName, CReportBase.TableTotal, blockFormat=CReportBase.AlignCenter)
                        table.mergeCells(f, 0,  1, self.tableColumnsLen+4)
                        for a, (personName, assistantName) in enumerate(personsList):
                            if (personName, assistantName) in dataDict[orgStructureName].keys():
                                table.addRow()
                                i = i+1
                                table.setText(i, 0, personName[1])
                                table.setText(i, 1, mapPersonToOrgStrAndSpeciality[personName][0])
                                table.setText(i, 2, mapPersonToOrgStrAndSpeciality[personName][1])
                                if showAssistants:
                                    table.setText(i, 3, assistantName[1])
                                if detailByClient:
                                    dataClientDict = dataDict[orgStructureName][(personName, assistantName)]
                                    dataClientKeys = dataClientDict.keys()
                                    dataClientKeys.sort(key=lambda x: x[1])
                                    clientRow = 1
                                    mergeRow = 0
                                    begClientRow = i
                                    for dataClientKey in dataClientKeys:
                                        table.setText(i, clientCol, dataClientKey[1])
                                        dataActionTypeDict = dataDict[orgStructureName][(personName, assistantName)][dataClientKey]
                                        dataActionTypeKeys = dataActionTypeDict.keys()
                                        dataActionTypeKeys.sort(key=lambda x: x[1])
                                        actionTypeRow = 1
                                        begActionTypeRow = i
                                        for dataActionTypeKey in dataActionTypeKeys:
                                            actionTypeId, actionTypeInfo = dataActionTypeKey
                                            table.setText(i, clientCol+1, actionTypeInfo[0])
                                            table.setText(i, clientCol+2, actionTypeInfo[1])
                                            total = [0]*2
                                            for fi, financeName in enumerate(financeList):
                                                table.setText(i, 3+showCols+fi*2, dataDict[orgStructureName][(personName, assistantName)][dataClientKey][dataActionTypeKey].get(financeName, [0]*2)[0])
                                                totalByOrgStructure[3+showCols+fi*2] += dataDict[orgStructureName][(personName, assistantName)][dataClientKey][dataActionTypeKey].get(financeName, [0]*2)[0]
                                                table.setText(i, 4+showCols+fi*2, forceStringEx(dataDict[orgStructureName][(personName, assistantName)][dataClientKey][dataActionTypeKey].get(financeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                                totalByOrgStructure[4+showCols+fi*2] += dataDict[orgStructureName][(personName, assistantName)][dataClientKey][dataActionTypeKey].get(financeName, [0]*2)[1]
                                                total[0] += dataDict[orgStructureName][(personName, assistantName)][dataClientKey][dataActionTypeKey].get(financeName, [0]*2)[0]
                                                total[1] += dataDict[orgStructureName][(personName, assistantName)][dataClientKey][dataActionTypeKey].get(financeName, [0]*2)[1]
                                            fi += 1
                                            table.setText(i, 3+showCols+fi*2, total[0])
                                            totalByOrgStructure[3+showCols+fi*2] += total[0]
                                            table.setText(i, 4+showCols+fi*2, forceStringEx(total[1]).replace(QString('.'), QString(',')))
                                            totalByOrgStructure[4+showCols+fi*2] += total[1]
                                            if actionTypeRow < len(dataActionTypeKeys):
                                                actionTypeRow += 1
                                                mergeRow += 1
                                                i = table.addRow()
                                        table.mergeCells(begActionTypeRow, clientCol,  actionTypeRow, 1)
                                        if clientRow < len(dataClientKeys):
                                            clientRow += 1
                                            i = table.addRow()
                                    table.mergeCells(begClientRow, 0,  clientRow + ((mergeRow + 1) if mergeRow else 0), 1)
                                    table.mergeCells(begClientRow, 1,  clientRow + ((mergeRow + 1) if mergeRow else 0), 1)
                                    table.mergeCells(begClientRow, 2,  clientRow + ((mergeRow + 1) if mergeRow else 0), 1)
                                else:
                                    dataActionTypeDict = dataDict[orgStructureName][(personName, assistantName)]
                                    dataActionTypeKeys = dataActionTypeDict.keys()
                                    dataActionTypeKeys.sort(key=lambda x: x[1])
                                    actionTypeRow = 1
                                    begActionTypeRow = i
                                    for dataActionTypeKey in dataActionTypeKeys:
                                        actionTypeId, actionTypeInfo = dataActionTypeKey
                                        table.setText(i, clientCol, actionTypeInfo[0])
                                        table.setText(i, clientCol+1, actionTypeInfo[1])
                                        total = [0]*2
                                        for fi, financeName in enumerate(financeList):
                                            table.setText(i, 3+showCols+fi*2, dataDict[orgStructureName][(personName, assistantName)][dataActionTypeKey].get(financeName, [0]*2)[0])
                                            totalByOrgStructure[3+showCols+fi*2] += dataDict[orgStructureName][(personName, assistantName)][dataActionTypeKey].get(financeName, [0]*2)[0]
                                            table.setText(i, 4+showCols+fi*2, forceStringEx(dataDict[orgStructureName][(personName, assistantName)][dataActionTypeKey].get(financeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                            totalByOrgStructure[4+showCols+fi*2] += dataDict[orgStructureName][(personName, assistantName)][dataActionTypeKey].get(financeName, [0]*2)[1]
                                            total[0] += dataDict[orgStructureName][(personName, assistantName)][dataActionTypeKey].get(financeName, [0]*2)[0]
                                            total[1] += dataDict[orgStructureName][(personName, assistantName)][dataActionTypeKey].get(financeName, [0]*2)[1]
                                        fi += 1
                                        table.setText(i, 3+showCols+fi*2, total[0])
                                        totalByOrgStructure[3+showCols+fi*2] += total[0]
                                        table.setText(i, 4+showCols+fi*2, forceStringEx(total[1]).replace(QString('.'), QString(',')))
                                        totalByOrgStructure[4+showCols+fi*2] += total[1]
                                        if actionTypeRow < len(dataActionTypeKeys):
                                            actionTypeRow += 1
                                            i = table.addRow()
                                    table.mergeCells(begActionTypeRow, 0,  actionTypeRow, 1)
                                    table.mergeCells(begActionTypeRow, 1,  actionTypeRow, 1)
                                    table.mergeCells(begActionTypeRow, clientCol-1,  actionTypeRow, 1)
                        i = table.addRow()
                        table.setText(i, 0, u'Итого по подразделению %s'%(orgStructureName), CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                        table.mergeCells(i, 0,  1, 3+showCols)
                        for t in range(self.groupingRange):
                            table.setText(i, t+3+showCols, forceStringEx(totalByOrgStructure[t+3+showCols]).replace(QString('.'), QString(',')))
                            totalByLPU[t] += totalByOrgStructure[t+3+showCols]
                    i = table.addRow()
                    table.setText(i, 0, u'ИТОГО', CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                    table.mergeCells(i, 0,  1, 3+showCols)
                    for t in range(self.groupingRange):
                        table.setText(i, t+3+showCols, forceStringEx(totalByLPU[t]).replace(QString('.'), QString(',')))
                else:
                    for a, (personName, assistantName) in enumerate(personsList):
                        i = table.addRow()
                        table.setText(i, 0, personName[1])
                        table.setText(i, 1, mapPersonToOrgStrAndSpeciality[personName][0])
                        table.setText(i, 2, mapPersonToOrgStrAndSpeciality[personName][1])
                        if showAssistants:
                            table.setText(i, 3, assistantName[1])
                        if detailByClient:
                            dataClientDict = dataDict[(personName, assistantName)]
                            dataClientKeys = dataClientDict.keys()
                            dataClientKeys.sort(key=lambda x: x[1])
                            clientRow = 1
                            mergeRow = 0
                            begClientRow = i
                            for dataClientKey in dataClientKeys:
                                table.setText(i, clientCol, dataClientKey[1])
                                dataActionTypeDict = dataDict[(personName, assistantName)][dataClientKey]
                                dataActionTypeKeys = dataActionTypeDict.keys()
                                dataActionTypeKeys.sort(key=lambda x: x[1])
                                actionTypeRow = 1
                                begActionTypeRow = i
                                for dataActionTypeKey in dataActionTypeKeys:
                                    actionTypeId, actionTypeInfo = dataActionTypeKey
                                    table.setText(i, clientCol+1, actionTypeInfo[0])
                                    table.setText(i, clientCol+2, actionTypeInfo[1])
                                    total = [0]*2
                                    for f, financeName in enumerate(financeList):
                                        table.setText(i, 3+showCols+f*2, dataDict[(personName, assistantName)][dataClientKey][dataActionTypeKey].get(financeName, [0]*2)[0])
                                        table.setText(i, 4+showCols+f*2, forceStringEx(dataDict[(personName, assistantName)][dataClientKey][dataActionTypeKey].get(financeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                        total[0] += dataDict[(personName, assistantName)][dataClientKey][dataActionTypeKey].get(financeName, [0]*2)[0]
                                        total[1] += dataDict[(personName, assistantName)][dataClientKey][dataActionTypeKey].get(financeName, [0]*2)[1]
                                    table.setText(i, 5+showCols+f*2, total[0])
                                    table.setText(i, 6+showCols+f*2, forceStringEx(total[1]).replace(QString('.'), QString(',')))
                                    if actionTypeRow < len(dataActionTypeKeys):
                                        actionTypeRow += 1
                                        mergeRow += 1
                                        i = table.addRow()
                                table.mergeCells(begActionTypeRow, clientCol,  actionTypeRow, 1)
                                if clientRow < len(dataClientKeys):
                                    clientRow += 1
                                    i = table.addRow()
                            table.mergeCells(begClientRow, 0,  clientRow + ((mergeRow + 1) if mergeRow else 0), 1)
                            table.mergeCells(begClientRow, 1,  clientRow + ((mergeRow + 1) if mergeRow else 0), 1)
                            table.mergeCells(begClientRow, 2,  clientRow + ((mergeRow + 1) if mergeRow else 0), 1)
                        else:
                            dataActionTypeDict = dataDict[(personName, assistantName)]
                            dataActionTypeKeys = dataActionTypeDict.keys()
                            dataActionTypeKeys.sort(key=lambda x: x[1])
                            actionTypeRow = 1
                            begActionTypeRow = i
                            for dataActionTypeKey in dataActionTypeKeys:
                                actionTypeId, actionTypeInfo = dataActionTypeKey
                                table.setText(i, clientCol, actionTypeInfo[0])
                                table.setText(i, clientCol+1, actionTypeInfo[1])
                                total = [0]*2
                                for f, financeName in enumerate(financeList):
                                    table.setText(i, 3+showCols+f*2, dataDict[(personName, assistantName)][dataActionTypeKey].get(financeName, [0]*2)[0])
                                    table.setText(i, 4+showCols+f*2, forceStringEx(dataDict[(personName, assistantName)][dataActionTypeKey].get(financeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                    total[0] += dataDict[(personName, assistantName)][dataActionTypeKey].get(financeName, [0]*2)[0]
                                    total[1] += dataDict[(personName, assistantName)][dataActionTypeKey].get(financeName, [0]*2)[1]
                                table.setText(i, 5+showCols+f*2, total[0])
                                table.setText(i, 6+showCols+f*2, forceStringEx(total[1]).replace(QString('.'), QString(',')))
                                if actionTypeRow < len(dataActionTypeKeys):
                                    actionTypeRow += 1
                                    i = table.addRow()
                            table.mergeCells(begActionTypeRow, 0,  actionTypeRow, 1)
                            table.mergeCells(begActionTypeRow, 1,  actionTypeRow, 1)
                            table.mergeCells(begActionTypeRow, clientCol-1,  actionTypeRow, 1)
            elif detailByMedicalAidKind:
                if detailByOrgStructures:
                    totalByLPU = [0]*(self.tableColumnsLen+4)
                    for o, orgStructureName in enumerate(orgStructureList):
                        #totalByOrgStructure = [0]*(self.tableColumnsLen+4)
                        totalByOrgStructure = [0]*table.table.columns()
                        f = table.addRow()
                        i = f
                        table.setText(f, 0, orgStructureName, CReportBase.TableTotal, blockFormat=CReportBase.AlignCenter)
                        table.mergeCells(f, 0,  1, self.tableColumnsLen+4)
                        for a, (personName, assistantName) in enumerate(personsList):
                            if (personName, assistantName) in dataDict[orgStructureName].keys():
                                i = table.addRow()
                                table.setText(i, 0, personName[1])
                                table.setText(i, 1, mapPersonToOrgStrAndSpeciality[personName][0])
                                table.setText(i, 2, mapPersonToOrgStrAndSpeciality[personName][1])
                                if showAssistants:
                                    table.setText(i, 3, assistantName[1])
                                if detailByClient:
                                    dataClientDict = dataDict[orgStructureName][(personName, assistantName)]
                                    dataClientKeys = dataClientDict.keys()
                                    dataClientKeys.sort(key=lambda x: x[1])
                                    clientRow = 1
                                    mergeRow = 0
                                    begClientRow = i
                                    for dataClientKey in dataClientKeys:
                                        table.setText(i, clientCol, dataClientKey[1])
                                        dataActionTypeDict = dataDict[orgStructureName][(personName, assistantName)][dataClientKey]
                                        dataActionTypeKeys = dataActionTypeDict.keys()
                                        dataActionTypeKeys.sort(key=lambda x: x[1])
                                        actionTypeRow = 1
                                        begActionTypeRow = i
                                        for dataActionTypeKey in dataActionTypeKeys:
                                            actionTypeId, actionTypeInfo = dataActionTypeKey
                                            table.setText(i, clientCol+1, actionTypeInfo[0])
                                            table.setText(i, clientCol+2, actionTypeInfo[1])
                                            for m, medicalAidKindName in enumerate(medicalAidKindList):
                                                table.setText(i, 3+showCols+m*2, dataDict[orgStructureName][(personName, assistantName)][dataClientKey][dataActionTypeKey].get(medicalAidKindName, [0]*2)[0])
                                                totalByOrgStructure[3+showCols+m*2] += dataDict[orgStructureName][(personName, assistantName)][dataClientKey][dataActionTypeKey].get(medicalAidKindName, [0]*2)[0]
                                                table.setText(i, 4+showCols+m*2, forceStringEx(dataDict[orgStructureName][(personName, assistantName)][dataClientKey][dataActionTypeKey].get(medicalAidKindName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                                totalByOrgStructure[4+showCols+m*2] += dataDict[orgStructureName][(personName, assistantName)][dataClientKey][dataActionTypeKey].get(medicalAidKindName, [0]*2)[1]
                                            if actionTypeRow < len(dataActionTypeKeys):
                                                actionTypeRow += 1
                                                mergeRow += 1
                                                i = table.addRow()
                                        table.mergeCells(begActionTypeRow, clientCol,  actionTypeRow, 1)
                                        if clientRow < len(dataClientKeys):
                                            clientRow += 1
                                            i = table.addRow()
                                    table.mergeCells(begClientRow, 0,  clientRow + ((mergeRow + 1) if mergeRow else 0), 1)
                                    table.mergeCells(begClientRow, 1,  clientRow + ((mergeRow + 1) if mergeRow else 0), 1)
                                    table.mergeCells(begClientRow, 2,  clientRow + ((mergeRow + 1) if mergeRow else 0), 1)
                                else:
                                    dataActionTypeDict = dataDict[orgStructureName][(personName, assistantName)]
                                    dataActionTypeKeys = dataActionTypeDict.keys()
                                    dataActionTypeKeys.sort(key=lambda x: x[1])
                                    actionTypeRow = 1
                                    begActionTypeRow = i
                                    for dataActionTypeKey in dataActionTypeKeys:
                                        actionTypeId, actionTypeInfo = dataActionTypeKey
                                        table.setText(i, clientCol+1, actionTypeInfo[0])
                                        table.setText(i, clientCol+2, actionTypeInfo[1])
                                        for m, medicalAidKindName in enumerate(medicalAidKindList):
                                            table.setText(i, 3+showCols+m*2, dataDict[orgStructureName][(personName, assistantName)][dataActionTypeKey].get(medicalAidKindName, [0]*2)[0])
                                            totalByOrgStructure[3+showCols+m*2] += dataDict[orgStructureName][(personName, assistantName)][dataActionTypeKey].get(medicalAidKindName, [0]*2)[0]
                                            table.setText(i, 4+showCols+m*2, forceStringEx(dataDict[orgStructureName][(personName, assistantName)][dataActionTypeKey].get(medicalAidKindName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                            totalByOrgStructure[4+showCols+m*2] += dataDict[orgStructureName][(personName, assistantName)][dataActionTypeKey].get(medicalAidKindName, [0]*2)[1]
                                            if actionTypeRow < len(dataActionTypeKeys):
                                                actionTypeRow += 1
                                                i = table.addRow()
                                    table.mergeCells(begActionTypeRow, 0,  actionTypeRow, 1)
                                    table.mergeCells(begActionTypeRow, 1,  actionTypeRow, 1)
                                    table.mergeCells(begActionTypeRow, clientCol-1,  actionTypeRow, 1)
                        i = table.addRow()
                        table.setText(i, 0, u'Итого по подразделению %s'%(orgStructureName), CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                        table.mergeCells(i, 0,  1, 3+showCols)
                        for t in range(self.groupingRange):
                            table.setText(i, t+3+showCols, forceStringEx(totalByOrgStructure[t+3+showCols]).replace(QString('.'), QString(',')))
                            totalByLPU[t] += totalByOrgStructure[t+3+showCols]
                    i = table.addRow()
                    table.setText(i, 0, u'ИТОГО', CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                    table.mergeCells(i, 0,  1, 3+showCols)
                    for t in range(self.groupingRange):
                        table.setText(i, t+3+showCols, forceStringEx(totalByLPU[t]).replace(QString('.'), QString(',')))
                else:
                    for a, (personName, assistantName) in enumerate(personsList):
                        i = table.addRow()
                        table.setText(i, 0, personName[1])
                        table.setText(i, 1, mapPersonToOrgStrAndSpeciality[personName][0])
                        table.setText(i, 2, mapPersonToOrgStrAndSpeciality[personName][1])
                        if showAssistants:
                            table.setText(i, 3, assistantName[1])
                        if detailByClient:
                            dataClientDict = dataDict[(personName, assistantName)]
                            dataClientKeys = dataClientDict.keys()
                            dataClientKeys.sort(key=lambda x: x[1])
                            clientRow = 1
                            mergeRow = 0
                            begClientRow = i
                            for dataClientKey in dataClientKeys:
                                table.setText(i, clientCol, dataClientKey[1])
                                dataActionTypeDict = dataDict[(personName, assistantName)][dataClientKey]
                                dataActionTypeKeys = dataActionTypeDict.keys()
                                dataActionTypeKeys.sort(key=lambda x: x[1])
                                actionTypeRow = 1
                                begActionTypeRow = i
                                for dataActionTypeKey in dataActionTypeKeys:
                                    actionTypeId, actionTypeInfo = dataActionTypeKey
                                    table.setText(i, clientCol+1, actionTypeInfo[0])
                                    table.setText(i, clientCol+2, actionTypeInfo[1])
                                    for m, medicalAidKindName in enumerate(medicalAidKindList):
                                        table.setText(i, 3+showCols+m*2, dataDict[(personName, assistantName)][dataClientKey][dataActionTypeKey].get(medicalAidKindName, [0]*2)[0])
                                        table.setText(i, 4+showCols+m*2, forceStringEx(dataDict[(personName, assistantName)][dataClientKey][dataActionTypeKey].get(medicalAidKindName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                    if actionTypeRow < len(dataActionTypeKeys):
                                        actionTypeRow += 1
                                        mergeRow += 1
                                        i = table.addRow()
                                table.mergeCells(begActionTypeRow, clientCol,  actionTypeRow, 1)
                                if clientRow < len(dataClientKeys):
                                    clientRow += 1
                                    i = table.addRow()
                            table.mergeCells(begClientRow, 0,  clientRow + ((mergeRow + 1) if mergeRow else 0), 1)
                            table.mergeCells(begClientRow, 1,  clientRow + ((mergeRow + 1) if mergeRow else 0), 1)
                            table.mergeCells(begClientRow, 2,  clientRow + ((mergeRow + 1) if mergeRow else 0), 1)
                        else:
                            dataActionTypeDict = dataDict[(personName, assistantName)]
                            dataActionTypeKeys = dataActionTypeDict.keys()
                            dataActionTypeKeys.sort(key=lambda x: x[1])
                            actionTypeRow = 1
                            begActionTypeRow = i
                            for dataActionTypeKey in dataActionTypeKeys:
                                actionTypeId, actionTypeInfo = dataActionTypeKey
                                table.setText(i, clientCol, actionTypeInfo[0])
                                table.setText(i, clientCol+1, actionTypeInfo[1])
                                for m, medicalAidKindName in enumerate(medicalAidKindList):
                                    table.setText(i, 3+showCols+m*2, dataDict[(personName, assistantName)][dataActionTypeKey].get(medicalAidKindName, [0]*2)[0])
                                    table.setText(i, 4+showCols+m*2, forceStringEx(dataDict[(personName, assistantName)][dataActionTypeKey].get(medicalAidKindName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                    if actionTypeRow < len(dataActionTypeKeys):
                                        actionTypeRow += 1
                                        i = table.addRow()
                            table.mergeCells(begActionTypeRow, 0,  actionTypeRow, 1)
                            table.mergeCells(begActionTypeRow, 1,  actionTypeRow, 1)
                            table.mergeCells(begActionTypeRow, clientCol-1,  actionTypeRow, 1)
            else:
                if detailByOrgStructures:
                    totalByLPU = [0]*(self.tableColumnsLen+4)
                    for o, orgStructureName in enumerate(orgStructureList):
                        #totalByOrgStructure = [0]*(self.tableColumnsLen+4)
                        totalByOrgStructure = [0]*table.table.columns()
                        f = table.addRow()
                        i = f
                        table.setText(f, 0, orgStructureName, CReportBase.TableTotal, blockFormat=CReportBase.AlignCenter)
                        table.mergeCells(f, 0,  1, self.tableColumnsLen+2)
                        for a, (personName, assistantName) in enumerate(personsList):
                            if (personName, assistantName) in dataDict[orgStructureName].keys():
                                i = table.addRow()
                                table.setText(i, 0, personName[1])
                                table.setText(i, 1, mapPersonToOrgStrAndSpeciality[personName][0])
                                table.setText(i, 2, mapPersonToOrgStrAndSpeciality[personName][1])
                                if showAssistants:
                                    table.setText(i, 3, assistantName[1])
                                if detailByClient:
                                    dataClientDict = dataDict[orgStructureName][(personName, assistantName)]
                                    dataClientKeys = dataClientDict.keys()
                                    dataClientKeys.sort(key=lambda x: x[1])
                                    clientRow = 1
                                    mergeRow = 0
                                    begClientRow = i
                                    for dataClientKey in dataClientKeys:
                                        table.setText(i, clientCol, dataClientKey[1])
                                        dataActionTypeDict = dataDict[orgStructureName][(personName, assistantName)][dataClientKey]
                                        dataActionTypeKeys = dataActionTypeDict.keys()
                                        dataActionTypeKeys.sort(key=lambda x: x[1])
                                        actionTypeRow = 1
                                        begActionTypeRow = i
                                        for dataActionTypeKey in dataActionTypeKeys:
                                            actionTypeId, actionTypeInfo = dataActionTypeKey
                                            table.setText(i, clientCol+1, actionTypeInfo[0])
                                            table.setText(i, clientCol+2, actionTypeInfo[1])
                                            table.setText(i, 3+showCols, dataDict[orgStructureName][(personName, assistantName)][dataClientKey][dataActionTypeKey][0])
                                            totalByOrgStructure[3+showCols] += dataDict[orgStructureName][(personName, assistantName)][dataClientKey][dataActionTypeKey][0]
                                            table.setText(i, 4+showCols, forceStringEx(dataDict[orgStructureName][(personName, assistantName)][dataClientKey][dataActionTypeKey][1]).replace(QString('.'), QString(',')))
                                            totalByOrgStructure[4+showCols] += dataDict[orgStructureName][(personName, assistantName)][dataClientKey][dataActionTypeKey][1]
                                            if clientRow < len(dataClientKeys):
                                                mergeRow += 1
                                                i = table.addRow()
                                        table.mergeCells(begActionTypeRow, clientCol,  actionTypeRow, 1)
                                        if clientRow < len(dataClientKeys):
                                            clientRow += 1
                                            i = table.addRow()
                                    table.mergeCells(begClientRow, 0,  clientRow + ((mergeRow + 1) if mergeRow else 0), 1)
                                    table.mergeCells(begClientRow, 1,  clientRow + ((mergeRow + 1) if mergeRow else 0), 1)
                                    table.mergeCells(begClientRow, 2,  clientRow + ((mergeRow + 1) if mergeRow else 0), 1)
                                else:
                                    dataActionTypeDict = dataDict[orgStructureName][(personName, assistantName)]
                                    dataActionTypeKeys = dataActionTypeDict.keys()
                                    dataActionTypeKeys.sort(key=lambda x: x[1])
                                    actionTypeRow = 1
                                    begActionTypeRow = i
                                    for dataActionTypeKey in dataActionTypeKeys:
                                        actionTypeId, actionTypeInfo = dataActionTypeKey
                                        table.setText(i, clientCol, actionTypeInfo[0])
                                        table.setText(i, clientCol+1, actionTypeInfo[1])
                                        table.setText(i, 3+showCols, dataDict[orgStructureName][(personName, assistantName)][dataActionTypeKey][0])
                                        totalByOrgStructure[3+showCols] += dataDict[orgStructureName][(personName, assistantName)][dataActionTypeKey][0]
                                        table.setText(i, 4+showCols, forceStringEx(dataDict[orgStructureName][(personName, assistantName)][dataActionTypeKey][1]).replace(QString('.'), QString(',')))
                                        totalByOrgStructure[4+showCols] += dataDict[orgStructureName][(personName, assistantName)][dataActionTypeKey][1]
                                        if actionTypeRow < len(dataActionTypeKeys):
                                            actionTypeRow += 1
                                            i = table.addRow()
                                    table.mergeCells(begActionTypeRow, 0,  actionTypeRow, 1)
                                    table.mergeCells(begActionTypeRow, 1,  actionTypeRow, 1)
                                    table.mergeCells(begActionTypeRow, clientCol-1,  actionTypeRow, 1)
                        i = table.addRow()
                        table.setText(i, 0, u'Итого по подразделению %s'%(orgStructureName), CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                        table.mergeCells(i, 0,  1, 3+showCols)
                        for t in range(self.groupingRange):
                            table.setText(i, t+3+showCols, forceStringEx(totalByOrgStructure[t+3+showCols]).replace(QString('.'), QString(',')))
                            totalByLPU[t] += totalByOrgStructure[t+3+showCols]
                    i = table.addRow()
                    table.setText(i, 0, u'ИТОГО', CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                    table.mergeCells(i, 0,  1, 3+showCols)
                    for t in range(self.groupingRange):
                        table.setText(i, t+3+showCols, forceStringEx(totalByLPU[t]).replace(QString('.'), QString(',')))
                else:
                    for a, (personName, assistantName) in enumerate(personsList):
                        i = table.addRow()
                        table.setText(i, 0, personName[1])
                        table.setText(i, 1, mapPersonToOrgStrAndSpeciality[personName][0])
                        table.setText(i, 2, mapPersonToOrgStrAndSpeciality[personName][1])
                        if showAssistants:
                            table.setText(i, 3, assistantName[1])
                        if detailByClient:
                            dataClientDict = dataDict[(personName, assistantName)]
                            dataClientKeys = dataClientDict.keys()
                            dataClientKeys.sort(key=lambda x: x[1])
                            clientRow = 1
                            mergeRow = 0
                            begClientRow = i
                            for dataClientKey in dataClientKeys:
                                table.setText(i, clientCol, dataClientKey[1])
                                dataActionTypeDict = dataDict[(personName, assistantName)][dataClientKey]
                                dataActionTypeKeys = dataActionTypeDict.keys()
                                dataActionTypeKeys.sort(key=lambda x: x[1])
                                actionTypeRow = 1
                                begActionTypeRow = i
                                for dataActionTypeKey in dataActionTypeKeys:
                                    actionTypeId, actionTypeInfo = dataActionTypeKey
                                    table.setText(i, clientCol+1, actionTypeInfo[0])
                                    table.setText(i, clientCol+2, actionTypeInfo[1])
                                    table.setText(i, 3+showCols, dataDict[(personName, assistantName)][dataClientKey][dataActionTypeKey][0])
                                    table.setText(i, 4+showCols, forceStringEx(dataDict[(personName, assistantName)][dataClientKey][dataActionTypeKey][1]).replace(QString('.'), QString(',')))
                                    if actionTypeRow < len(dataActionTypeKeys):
                                        actionTypeRow += 1
                                        mergeRow += 1
                                        i = table.addRow()
                                table.mergeCells(begActionTypeRow, clientCol,  actionTypeRow, 1)
                                if clientRow < len(dataClientKeys):
                                    clientRow += 1
                                    i = table.addRow()
                            table.mergeCells(begClientRow, 0,  clientRow + ((mergeRow + 1) if mergeRow else 0), 1)
                            table.mergeCells(begClientRow, 1,  clientRow + ((mergeRow + 1) if mergeRow else 0), 1)
                            table.mergeCells(begClientRow, 2,  clientRow + ((mergeRow + 1) if mergeRow else 0), 1)
                        else:
                            dataActionTypeDict = dataDict[(personName, assistantName)]
                            dataActionTypeKeys = dataActionTypeDict.keys()
                            dataActionTypeKeys.sort(key=lambda x: x[1])
                            actionTypeRow = 1
                            begActionTypeRow = i
                            for dataActionTypeKey in dataActionTypeKeys:
                                actionTypeId, actionTypeInfo = dataActionTypeKey
                                table.setText(i, clientCol, actionTypeInfo[0])
                                table.setText(i, clientCol+1, actionTypeInfo[1])
                                table.setText(i, 3+showCols, dataDict[(personName, assistantName)][dataActionTypeKey][0])
                                table.setText(i, 4+showCols, forceStringEx(dataDict[(personName, assistantName)][dataActionTypeKey][1]).replace(QString('.'), QString(',')))
                                if actionTypeRow < len(dataActionTypeKeys):
                                    actionTypeRow += 1
                                    i = table.addRow()
                            table.mergeCells(begActionTypeRow, 0,  actionTypeRow, 1)
                            table.mergeCells(begActionTypeRow, 1,  actionTypeRow, 1)
                            table.mergeCells(begActionTypeRow, clientCol-1,  actionTypeRow, 1)
        else: # not detailByActionTypeVisible
            if detailByFinance and detailByMedicalAidKind:
                if detailByOrgStructures:
                    totalByLPU = [0]*(self.tableColumnsLen+4)
                    for o, orgStructureName in enumerate(orgStructureList):
                        #totalByOrgStructure = [0]*(self.tableColumnsLen+4)
                        totalByOrgStructure = [0]*table.table.columns()
                        f = table.addRow()
                        i = f
                        table.setText(f, 0, orgStructureName, CReportBase.TableTotal, blockFormat=CReportBase.AlignCenter)
                        table.mergeCells(f, 0,  1, self.tableColumnsLen+4)
                        for a, (personName, assistantName) in enumerate(personsList):
                            if (personName, assistantName) in dataDict[orgStructureName].keys():
                                i = table.addRow()
                                table.setText(i, 0, personName[1])
                                table.setText(i, 1, mapPersonToOrgStrAndSpeciality[personName][0])
                                table.setText(i, 2, mapPersonToOrgStrAndSpeciality[personName][1])
                                if showAssistants:
                                    table.setText(i, 3, assistantName[1])
                                if detailByClient:
                                    dataClientDict = dataDict[orgStructureName][(personName, assistantName)]
                                    dataClientKeys = dataClientDict.keys()
                                    dataClientKeys.sort(key=lambda x: x[1])
                                    clientRow = 1
                                    mergeRow = 0
                                    begClientRow = i
                                    for dataClientKey in dataClientKeys:
                                        table.setText(i, clientCol, dataClientKey[1])
                                        totalFinance = {}
                                        totallyTotalFinance = [0]*2
                                        for f, financeName in enumerate(financeList):
                                            total = [0]*2
                                            for j, medicalAidKindName in enumerate(medicalAidKindList):
                                                table.setText(i, 3+showCols+2*j+f*lenMedicalCols, dataDict[orgStructureName][(personName, assistantName)][dataClientKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[0])
                                                totalByOrgStructure[3+showCols+2*j+f*lenMedicalCols] += dataDict[orgStructureName][(personName, assistantName)][dataClientKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[0]
                                                table.setText(i, 4+showCols+2*j+f*lenMedicalCols, forceStringEx(dataDict[orgStructureName][(personName, assistantName)][dataClientKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                                totalByOrgStructure[4+showCols+2*j+f*lenMedicalCols] += dataDict[orgStructureName][(personName, assistantName)][dataClientKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[1]
                                                if medicalAidKindName not in totalFinance.keys():
                                                    totalFinance[medicalAidKindName] = [0]*2
                                                total[0] += dataDict[orgStructureName][(personName, assistantName)][dataClientKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[0]
                                                total[1] += dataDict[orgStructureName][(personName, assistantName)][dataClientKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[1]
                                                totalFinance[medicalAidKindName][0] += dataDict[orgStructureName][(personName, assistantName)][dataClientKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[0]
                                                totalFinance[medicalAidKindName][1] += dataDict[orgStructureName][(personName, assistantName)][dataClientKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[1]
                                            table.setText(i, 5+showCols+2*j+f*lenMedicalCols, total[0])
                                            totalByOrgStructure[5+showCols+2*j+f*lenMedicalCols] += total[0]
                                            table.setText(i, 6+showCols+2*j+f*lenMedicalCols, forceStringEx(total[1]).replace(QString('.'), QString(',')))
                                            totalByOrgStructure[6+showCols+2*j+f*lenMedicalCols] += total[1]
                                        for j, medicalAidKindName in enumerate(medicalAidKindList):
                                            table.setText(i, 3+showCols+2*j+(f+1)*lenMedicalCols, totalFinance.get(medicalAidKindName, [0]*2)[0])
                                            totalByOrgStructure[3+showCols+2*j+(f+1)*lenMedicalCols] += totalFinance.get(medicalAidKindName, [0]*2)[0]
                                            table.setText(i, 4+showCols+2*j+(f+1)*lenMedicalCols, forceStringEx(totalFinance.get(medicalAidKindName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                            totalByOrgStructure[4+showCols+2*j+(f+1)*lenMedicalCols] += totalFinance.get(medicalAidKindName, [0]*2)[1]
                                            totallyTotalFinance[0] += totalFinance.get(medicalAidKindName, [0]*2)[0]
                                            totallyTotalFinance[1] += totalFinance.get(medicalAidKindName, [0]*2)[1]
                                        table.setText(i, 5+showCols+2*j+(f+1)*lenMedicalCols, totallyTotalFinance[0])
                                        totalByOrgStructure[5+showCols+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[0]
                                        table.setText(i, 6+showCols+2*j+(f+1)*lenMedicalCols, forceStringEx(totallyTotalFinance[1]).replace(QString('.'), QString(',')))
                                        totalByOrgStructure[6+showCols+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[1]
                                        if clientRow < len(dataClientKeys):
                                            clientRow += 1
                                            i = table.addRow()
                                    table.mergeCells(begClientRow, 0,  clientRow, 1)
                                    table.mergeCells(begClientRow, 1,  clientRow, 1)
                                    table.mergeCells(begClientRow, 2,  clientRow, 1)
                                else:
                                    totalFinance = {}
                                    totallyTotalFinance = [0]*2
                                    for f, financeName in enumerate(financeList):
                                        total = [0]*2
                                        for j, medicalAidKindName in enumerate(medicalAidKindList):
                                            table.setText(i, 3+showAssistants+2*j+f*lenMedicalCols, dataDict[orgStructureName][(personName, assistantName)].get(financeName, {}).get(medicalAidKindName, [0]*2)[0])
                                            totalByOrgStructure[3+showAssistants+2*j+f*lenMedicalCols] += dataDict[orgStructureName][(personName, assistantName)].get(financeName, {}).get(medicalAidKindName, [0]*2)[0]
                                            table.setText(i, 4+showAssistants+2*j+f*lenMedicalCols, forceStringEx(dataDict[orgStructureName][(personName, assistantName)].get(financeName, {}).get(medicalAidKindName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                            totalByOrgStructure[4+showAssistants+2*j+f*lenMedicalCols] += dataDict[orgStructureName][(personName, assistantName)].get(financeName, {}).get(medicalAidKindName, [0]*2)[1]
                                            if medicalAidKindName not in totalFinance.keys():
                                                totalFinance[medicalAidKindName] = [0]*2
                                            total[0] += dataDict[orgStructureName][(personName, assistantName)].get(financeName, {}).get(medicalAidKindName, [0]*2)[0]
                                            total[1] += dataDict[orgStructureName][(personName, assistantName)].get(financeName, {}).get(medicalAidKindName, [0]*2)[1]
                                            totalFinance[medicalAidKindName][0] += dataDict[orgStructureName][(personName, assistantName)].get(financeName, {}).get(medicalAidKindName, [0]*2)[0]
                                            totalFinance[medicalAidKindName][1] += dataDict[orgStructureName][(personName, assistantName)].get(financeName, {}).get(medicalAidKindName, [0]*2)[1]
                                        table.setText(i, 5+showAssistants+2*j+f*lenMedicalCols, total[0])
                                        totalByOrgStructure[5+showAssistants+2*j+f*lenMedicalCols] += total[0]
                                        table.setText(i, 6+showAssistants+2*j+f*lenMedicalCols, forceStringEx(total[1]).replace(QString('.'), QString(',')))
                                        totalByOrgStructure[6+showAssistants+2*j+f*lenMedicalCols] += total[1]
                                    for j, medicalAidKindName in enumerate(medicalAidKindList):
                                        table.setText(i, 3+showAssistants+2*j+(f+1)*lenMedicalCols, totalFinance.get(medicalAidKindName, [0]*2)[0])
                                        totalByOrgStructure[3+showAssistants+2*j+(f+1)*lenMedicalCols] += totalFinance.get(medicalAidKindName, [0]*2)[0]
                                        table.setText(i, 4+showAssistants+2*j+(f+1)*lenMedicalCols, forceStringEx(totalFinance.get(medicalAidKindName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                        totalByOrgStructure[4+showAssistants+2*j+(f+1)*lenMedicalCols] += totalFinance.get(medicalAidKindName, [0]*2)[1]
                                        totallyTotalFinance[0] += totalFinance.get(medicalAidKindName, [0]*2)[0]
                                        totallyTotalFinance[1] += totalFinance.get(medicalAidKindName, [0]*2)[1]
                                    table.setText(i, 5+showAssistants+2*j+(f+1)*lenMedicalCols, totallyTotalFinance[0])
                                    totalByOrgStructure[5+showAssistants+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[0]
                                    table.setText(i, 6+showAssistants+2*j+(f+1)*lenMedicalCols, forceStringEx(totallyTotalFinance[1]).replace(QString('.'), QString(',')))
                                    totalByOrgStructure[6+showAssistants+2*j+(f+1)*lenMedicalCols] += totallyTotalFinance[1]
                        i = table.addRow()
                        table.setText(i, 0, u'Итого по подразделению %s'%(orgStructureName), CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                        table.mergeCells(i, 0,  1, 3+showCols)
                        for t in range(self.groupingRange):
                            table.setText(i, t+3+showCols, forceStringEx(totalByOrgStructure[t+3+showCols]).replace(QString('.'), QString(',')))
                            totalByLPU[t] += totalByOrgStructure[t+3+showCols]
                    i = table.addRow()
                    table.setText(i, 0, u'ИТОГО', CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                    table.mergeCells(i, 0,  1, 3+showCols)
                    for t in range(self.groupingRange):
                        table.setText(i, t+3+showCols, forceStringEx(totalByLPU[t]).replace(QString('.'), QString(',')))
                else:
                    for a, (personName, assistantName) in enumerate(personsList):
                        i = table.addRow()
                        table.setText(i, 0, personName[1])
                        table.setText(i, 1, mapPersonToOrgStrAndSpeciality[personName][0])
                        table.setText(i, 2, mapPersonToOrgStrAndSpeciality[personName][1])
                        if showAssistants:
                            table.setText(i, 3, assistantName[1])
                        if detailByClient:
                            dataClientDict = dataDict[(personName, assistantName)]
                            dataClientKeys = dataClientDict.keys()
                            dataClientKeys.sort(key=lambda x: x[1])
                            clientRow = 1
                            begClientRow = i
                            for dataClientKey in dataClientKeys:
                                table.setText(i, clientCol, dataClientKey[1])
                                totalFinance = {}
                                totallyTotalFinance = [0]*2
                                for f, financeName in enumerate(financeList):
                                    total = [0]*2
                                    for j, medicalAidKindName in enumerate(medicalAidKindList):
                                        table.setText(i, 3+showCols+2*j+f*lenMedicalCols, dataDict[(personName, assistantName)][dataClientKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[0])
                                        table.setText(i, 4+showCols+2*j+f*lenMedicalCols, forceStringEx(dataDict[(personName, assistantName)][dataClientKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                        if medicalAidKindName not in totalFinance.keys():
                                            totalFinance[medicalAidKindName] = [0]*2
                                        total[0] += dataDict[(personName, assistantName)][dataClientKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[0]
                                        total[1] += dataDict[(personName, assistantName)][dataClientKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[1]
                                        totalFinance[medicalAidKindName][0] += dataDict[(personName, assistantName)][dataClientKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[0]
                                        totalFinance[medicalAidKindName][1] += dataDict[(personName, assistantName)][dataClientKey].get(financeName, {}).get(medicalAidKindName, [0]*2)[1]
                                    table.setText(i, 5+showCols+2*j+f*lenMedicalCols, total[0])
                                    table.setText(i, 6+showCols+2*j+f*lenMedicalCols, forceStringEx(total[1]).replace(QString('.'), QString(',')))
                                for j, medicalAidKindName in enumerate(medicalAidKindList):
                                    table.setText(i, 3+showCols+2*j+(f+1)*lenMedicalCols, totalFinance.get(medicalAidKindName, [0]*2)[0])
                                    table.setText(i, 4+showCols+2*j+(f+1)*lenMedicalCols, forceStringEx(totalFinance.get(medicalAidKindName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                    totallyTotalFinance[0] += totalFinance.get(medicalAidKindName, [0]*2)[0]
                                    totallyTotalFinance[1] += totalFinance.get(medicalAidKindName, [0]*2)[1]
                                table.setText(i, 5+showCols+2*j+(f+1)*lenMedicalCols, totallyTotalFinance[0])
                                table.setText(i, 6+showCols+2*j+(f+1)*lenMedicalCols, forceStringEx(totallyTotalFinance[1]).replace(QString('.'), QString(',')))
                                if clientRow < len(dataClientKeys):
                                    clientRow += 1
                                    i = table.addRow()
                            table.mergeCells(begClientRow, 0,  clientRow, 1)
                            table.mergeCells(begClientRow, 1,  clientRow, 1)
                            table.mergeCells(begClientRow, 2,  clientRow, 1)
                        else:
                            totalFinance = {}
                            totallyTotalFinance = [0]*2
                            for f, financeName in enumerate(financeList):
                                total = [0]*2
                                for j, medicalAidKindName in enumerate(medicalAidKindList):
                                    table.setText(i, 3+showAssistants+2*j+f*lenMedicalCols, dataDict[(personName, assistantName)].get(financeName, {}).get(medicalAidKindName, [0]*2)[0])
                                    table.setText(i, 4+showAssistants+2*j+f*lenMedicalCols, forceStringEx(dataDict[(personName, assistantName)].get(financeName, {}).get(medicalAidKindName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                    if medicalAidKindName not in totalFinance.keys():
                                        totalFinance[medicalAidKindName] = [0]*2
                                    total[0] += dataDict[(personName, assistantName)].get(financeName, {}).get(medicalAidKindName, [0]*2)[0]
                                    total[1] += dataDict[(personName, assistantName)].get(financeName, {}).get(medicalAidKindName, [0]*2)[1]
                                    totalFinance[medicalAidKindName][0] += dataDict[(personName, assistantName)].get(financeName, {}).get(medicalAidKindName, [0]*2)[0]
                                    totalFinance[medicalAidKindName][1] += dataDict[(personName, assistantName)].get(financeName, {}).get(medicalAidKindName, [0]*2)[1]
                                table.setText(i, 5+showAssistants+2*j+f*lenMedicalCols, total[0])
                                table.setText(i, 6+showAssistants+2*j+f*lenMedicalCols, forceStringEx(total[1]).replace(QString('.'), QString(',')))
                            for j, medicalAidKindName in enumerate(medicalAidKindList):
                                table.setText(i, 3+showAssistants+2*j+(f+1)*lenMedicalCols, totalFinance.get(medicalAidKindName, [0]*2)[0])
                                table.setText(i, 4+showAssistants+2*j+(f+1)*lenMedicalCols, forceStringEx(totalFinance.get(medicalAidKindName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                totallyTotalFinance[0] += totalFinance.get(medicalAidKindName, [0]*2)[0]
                                totallyTotalFinance[1] += totalFinance.get(medicalAidKindName, [0]*2)[1]
                            table.setText(i, 5+showAssistants+2*j+(f+1)*lenMedicalCols, totallyTotalFinance[0])
                            table.setText(i, 6+showAssistants+2*j+(f+1)*lenMedicalCols, forceStringEx(totallyTotalFinance[1]).replace(QString('.'), QString(',')))
            elif detailByFinance:
                if detailByOrgStructures:
                    totalByLPU = [0]*(self.tableColumnsLen+4)
                    for o, orgStructureName in enumerate(orgStructureList):
                        #totalByOrgStructure = [0]*(self.tableColumnsLen+4)
                        totalByOrgStructure = [0]*table.table.columns()
                        f = table.addRow()
                        i = f
                        table.setText(f, 0, orgStructureName, CReportBase.TableTotal, blockFormat=CReportBase.AlignCenter)
                        table.mergeCells(f, 0,  1, self.tableColumnsLen+4)
                        for a, (personName, assistantName) in enumerate(personsList):
                            if (personName, assistantName) in dataDict[orgStructureName].keys():
                                table.addRow()
                                i = i+1
                                table.setText(i, 0, personName[1])
                                table.setText(i, 1, mapPersonToOrgStrAndSpeciality[personName][0])
                                table.setText(i, 2, mapPersonToOrgStrAndSpeciality[personName][1])
                                if showAssistants:
                                    table.setText(i, 3, assistantName[1])
                                if detailByClient:
                                    dataClientDict = dataDict[orgStructureName][(personName, assistantName)]
                                    dataClientKeys = dataClientDict.keys()
                                    dataClientKeys.sort(key=lambda x: x[1])
                                    clientRow = 1
                                    mergeRow = 0
                                    begClientRow = i
                                    for dataClientKey in dataClientKeys:
                                        table.setText(i, clientCol, dataClientKey[1])
                                        total = [0]*2
                                        for fi, financeName in enumerate(financeList):
                                            table.setText(i, 3+showCols+fi*2, dataDict[orgStructureName][(personName, assistantName)][dataClientKey].get(financeName, [0]*2)[0])
                                            totalByOrgStructure[3+showCols+fi*2] += dataDict[orgStructureName][(personName, assistantName)][dataClientKey].get(financeName, [0]*2)[0]
                                            table.setText(i, 4+showCols+fi*2, forceStringEx(dataDict[orgStructureName][(personName, assistantName)][dataClientKey].get(financeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                            totalByOrgStructure[4+showCols+fi*2] += dataDict[orgStructureName][(personName, assistantName)][dataClientKey].get(financeName, [0]*2)[1]
                                            total[0] += dataDict[orgStructureName][(personName, assistantName)][dataClientKey].get(financeName, [0]*2)[0]
                                            total[1] += dataDict[orgStructureName][(personName, assistantName)][dataClientKey].get(financeName, [0]*2)[1]
                                        fi += 1
                                        table.setText(i, 3+showCols+fi*2, total[0])
                                        totalByOrgStructure[3+showCols+fi*2] += total[0]
                                        table.setText(i, 4+showCols+fi*2, forceStringEx(total[1]).replace(QString('.'), QString(',')))
                                        totalByOrgStructure[4+showCols+fi*2] += total[1]
                                        if clientRow < len(dataClientKeys):
                                            clientRow += 1
                                            i = table.addRow()
                                    table.mergeCells(begClientRow, 0,  clientRow, 1)
                                    table.mergeCells(begClientRow, 1,  clientRow, 1)
                                    table.mergeCells(begClientRow, 2,  clientRow, 1)
                                else:
                                    total = [0]*2
                                    for fi, financeName in enumerate(financeList):
                                        table.setText(i, 3+showAssistants+fi*2, dataDict[orgStructureName][(personName, assistantName)].get(financeName, [0]*2)[0])
                                        totalByOrgStructure[3+showAssistants+fi*2] += dataDict[orgStructureName][(personName, assistantName)].get(financeName, [0]*2)[0]
                                        table.setText(i, 4+showAssistants+fi*2, forceStringEx(dataDict[orgStructureName][(personName, assistantName)].get(financeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                        totalByOrgStructure[4+showAssistants+fi*2] += dataDict[orgStructureName][(personName, assistantName)].get(financeName, [0]*2)[1]
                                        total[0] += dataDict[orgStructureName][(personName, assistantName)].get(financeName, [0]*2)[0]
                                        total[1] += dataDict[orgStructureName][(personName, assistantName)].get(financeName, [0]*2)[1]
                                    fi += 1
                                    table.setText(i, 3+showAssistants+fi*2, total[0])
                                    totalByOrgStructure[3+showAssistants+fi*2] += total[0]
                                    table.setText(i, 4+showAssistants+fi*2, forceStringEx(total[1]).replace(QString('.'), QString(',')))
                                    totalByOrgStructure[4+showAssistants+fi*2] += total[1]
                        i = table.addRow()
                        table.setText(i, 0, u'Итого по подразделению %s'%(orgStructureName), CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                        table.mergeCells(i, 0,  1, 3+showCols)
                        for t in range(self.groupingRange):
                            table.setText(i, t+3+showCols, forceStringEx(totalByOrgStructure[t+3+showCols]).replace(QString('.'), QString(',')))
                            totalByLPU[t] += totalByOrgStructure[t+3+showCols]
                    i = table.addRow()
                    table.setText(i, 0, u'ИТОГО', CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                    table.mergeCells(i, 0,  1, 3+showCols)
                    for t in range(self.groupingRange):
                        table.setText(i, t+3+showCols, forceStringEx(totalByLPU[t]).replace(QString('.'), QString(',')))
                else:
                    for a, (personName, assistantName) in enumerate(personsList):
                        i = table.addRow()
                        table.setText(i, 0, personName[1])
                        table.setText(i, 1, mapPersonToOrgStrAndSpeciality[personName][0])
                        table.setText(i, 2, mapPersonToOrgStrAndSpeciality[personName][1])
                        if showAssistants:
                            table.setText(i, 3, assistantName[1])
                        if detailByClient:
                            dataClientDict = dataDict[(personName, assistantName)]
                            dataClientKeys = dataClientDict.keys()
                            dataClientKeys.sort(key=lambda x: x[1])
                            clientRow = 1
                            begClientRow = i
                            for dataClientKey in dataClientKeys:
                                table.setText(i, clientCol, dataClientKey[1])
                                total = [0]*2
                                for f, financeName in enumerate(financeList):
                                    table.setText(i, 3+showCols+f*2, dataDict[(personName, assistantName)][dataClientKey].get(financeName, [0]*2)[0])
                                    table.setText(i, 4+showCols+f*2, forceStringEx(dataDict[(personName, assistantName)][dataClientKey].get(financeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                    total[0] += dataDict[(personName, assistantName)][dataClientKey].get(financeName, [0]*2)[0]
                                    total[1] += dataDict[(personName, assistantName)][dataClientKey].get(financeName, [0]*2)[1]
                                table.setText(i, 5+showCols+f*2, total[0])
                                table.setText(i, 6+showCols+f*2, forceStringEx(total[1]).replace(QString('.'), QString(',')))
                                if clientRow < len(dataClientKeys):
                                    clientRow += 1
                                    i = table.addRow()
                            table.mergeCells(begClientRow, 0,  clientRow, 1)
                            table.mergeCells(begClientRow, 1,  clientRow, 1)
                            table.mergeCells(begClientRow, 2,  clientRow, 1)
                        else:
                            total = [0]*2
                            for f, financeName in enumerate(financeList):
                                table.setText(i, 3+showAssistants+f*2, dataDict[(personName, assistantName)].get(financeName, [0]*2)[0])
                                table.setText(i, 4+showAssistants+f*2, forceStringEx(dataDict[(personName, assistantName)].get(financeName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                total[0] += dataDict[(personName, assistantName)].get(financeName, [0]*2)[0]
                                total[1] += dataDict[(personName, assistantName)].get(financeName, [0]*2)[1]
                            table.setText(i, 5+showAssistants+f*2, total[0])
                            table.setText(i, 6+showAssistants+f*2, forceStringEx(total[1]).replace(QString('.'), QString(',')))

            elif detailByMedicalAidKind:
                if detailByOrgStructures:
                    totalByLPU = [0]*(self.tableColumnsLen+4)
                    for o, orgStructureName in enumerate(orgStructureList):
                        #totalByOrgStructure = [0]*(self.tableColumnsLen+4)
                        totalByOrgStructure = [0]*table.table.columns()
                        f = table.addRow()
                        i = f
                        table.setText(f, 0, orgStructureName, CReportBase.TableTotal, blockFormat=CReportBase.AlignCenter)
                        table.mergeCells(f, 0,  1, self.tableColumnsLen+4)
                        for a, (personName, assistantName) in enumerate(personsList):
                            if (personName, assistantName) in dataDict[orgStructureName].keys():
                                i = table.addRow()
                                table.setText(i, 0, personName[1])
                                table.setText(i, 1, mapPersonToOrgStrAndSpeciality[personName][0])
                                table.setText(i, 2, mapPersonToOrgStrAndSpeciality[personName][1])
                                if showAssistants:
                                    table.setText(i, 3, assistantName[1])
                                if detailByClient:
                                    dataClientDict = dataDict[orgStructureName][(personName, assistantName)]
                                    dataClientKeys = dataClientDict.keys()
                                    dataClientKeys.sort(key=lambda x: x[1])
                                    clientRow = 1
                                    begClientRow = i
                                    for dataClientKey in dataClientKeys:
                                        table.setText(i, clientCol, dataClientKey[1])
                                        for m, medicalAidKindName in enumerate(medicalAidKindList):
                                            table.setText(i, 3+showCols+m*2, dataDict[orgStructureName][(personName, assistantName)][dataClientKey].get(medicalAidKindName, [0]*2)[0])
                                            totalByOrgStructure[3+showCols+m*2] += dataDict[orgStructureName][(personName, assistantName)][dataClientKey].get(medicalAidKindName, [0]*2)[0]
                                            table.setText(i, 4+showCols+m*2, forceStringEx(dataDict[orgStructureName][(personName, assistantName)][dataClientKey].get(medicalAidKindName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                            totalByOrgStructure[4+showCols+m*2] += dataDict[orgStructureName][(personName, assistantName)][dataClientKey].get(medicalAidKindName, [0]*2)[1]
                                        if clientRow < len(dataClientKeys):
                                            clientRow += 1
                                            i = table.addRow()
                                    table.mergeCells(begClientRow, 0,  clientRow, 1)
                                    table.mergeCells(begClientRow, 1,  clientRow, 1)
                                    table.mergeCells(begClientRow, 2,  clientRow, 1)
                                else:
                                    for m, medicalAidKindName in enumerate(medicalAidKindList):
                                        table.setText(i, 3+showAssistants+m*2, dataDict[orgStructureName][(personName, assistantName)].get(medicalAidKindName, [0]*2)[0])
                                        totalByOrgStructure[3+showAssistants+m*2] += dataDict[orgStructureName][(personName, assistantName)].get(medicalAidKindName, [0]*2)[0]
                                        table.setText(i, 4+showAssistants+m*2, forceStringEx(dataDict[orgStructureName][(personName, assistantName)].get(medicalAidKindName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                        totalByOrgStructure[4+showAssistants+m*2] += dataDict[orgStructureName][(personName, assistantName)].get(medicalAidKindName, [0]*2)[1]
                        i = table.addRow()
                        table.setText(i, 0, u'Итого по подразделению %s'%(orgStructureName), CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                        table.mergeCells(i, 0,  1, 3+showCols)
                        for t in range(self.groupingRange):
                            table.setText(i, t+3+showCols, forceStringEx(totalByOrgStructure[t+3+showCols]).replace(QString('.'), QString(',')))
                            totalByLPU[t] += totalByOrgStructure[t+3+showCols]
                    i = table.addRow()
                    table.setText(i, 0, u'ИТОГО', CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                    table.mergeCells(i, 0,  1, 3+showCols)
                    for t in range(self.groupingRange):
                        table.setText(i, t+3+showCols, forceStringEx(totalByLPU[t]).replace(QString('.'), QString(',')))
                else:
                    for a, (personName, assistantName) in enumerate(personsList):
                        i = table.addRow()
                        table.setText(i, 0, personName[1])
                        table.setText(i, 1, mapPersonToOrgStrAndSpeciality[personName][0])
                        table.setText(i, 2, mapPersonToOrgStrAndSpeciality[personName][1])
                        if showAssistants:
                            table.setText(i, 3, assistantName[1])
                        if detailByClient:
                            dataClientDict = dataDict[(personName, assistantName)]
                            dataClientKeys = dataClientDict.keys()
                            dataClientKeys.sort(key=lambda x: x[1])
                            clientRow = 1
                            begClientRow = i
                            for dataClientKey in dataClientKeys:
                                table.setText(i, clientCol, dataClientKey[1])
                                for m, medicalAidKindName in enumerate(medicalAidKindList):
                                    table.setText(i, 3+showCols+m*2, dataDict[(personName, assistantName)][dataClientKey].get(medicalAidKindName, [0]*2)[0])
                                    table.setText(i, 4+showCols+m*2, forceStringEx(dataDict[(personName, assistantName)][dataClientKey].get(medicalAidKindName, [0]*2)[1]).replace(QString('.'), QString(',')))
                                if clientRow < len(dataClientKeys):
                                    clientRow += 1
                                    i = table.addRow()
                            table.mergeCells(begClientRow, 0,  clientRow, 1)
                            table.mergeCells(begClientRow, 1,  clientRow, 1)
                            table.mergeCells(begClientRow, 2,  clientRow, 1)
                        else:
                            for m, medicalAidKindName in enumerate(medicalAidKindList):
                                table.setText(i, 3+showAssistants+m*2, dataDict[(personName, assistantName)].get(medicalAidKindName, [0]*2)[0])
                                table.setText(i, 4+showAssistants+m*2, forceStringEx(dataDict[(personName, assistantName)].get(medicalAidKindName, [0]*2)[1]).replace(QString('.'), QString(',')))
            else:
                if detailByOrgStructures:
                    totalByLPU = [0]*(self.tableColumnsLen+4)
                    for o, orgStructureName in enumerate(orgStructureList):
                        #totalByOrgStructure = [0]*(self.tableColumnsLen+4)
                        totalByOrgStructure = [0]*table.table.columns()
                        f = table.addRow()
                        i = f
                        table.setText(f, 0, orgStructureName, CReportBase.TableTotal, blockFormat=CReportBase.AlignCenter)
                        table.mergeCells(f, 0,  1, self.tableColumnsLen+2)
                        for a, (personName, assistantName) in enumerate(personsList):
                            if (personName, assistantName) in dataDict[orgStructureName].keys():
                                i = table.addRow()
                                table.setText(i, 0, personName[1])
                                table.setText(i, 1, mapPersonToOrgStrAndSpeciality[personName][0])
                                table.setText(i, 2, mapPersonToOrgStrAndSpeciality[personName][1])
                                if showAssistants:
                                    table.setText(i, 3, assistantName[1])
                                if detailByClient:
                                    dataClientDict = dataDict[orgStructureName][(personName, assistantName)]
                                    dataClientKeys = dataClientDict.keys()
                                    dataClientKeys.sort(key=lambda x: x[1])
                                    clientRow = 1
                                    begClientRow = i
                                    for dataClientKey in dataClientKeys:
                                        table.setText(i, clientCol, dataClientKey[1])
                                        table.setText(i, 3+showCols, dataDict[orgStructureName][(personName, assistantName)][dataClientKey][0])
                                        totalByOrgStructure[3+showCols] += dataDict[orgStructureName][(personName, assistantName)][dataClientKey][0]
                                        table.setText(i, 4+showCols, forceStringEx(dataDict[orgStructureName][(personName, assistantName)][dataClientKey][1]).replace(QString('.'), QString(',')))
                                        totalByOrgStructure[4+showCols] += dataDict[orgStructureName][(personName, assistantName)][dataClientKey][1]
                                        if clientRow < len(dataClientKeys):
                                            clientRow += 1
                                            i = table.addRow()
                                    table.mergeCells(begClientRow, 0,  clientRow, 1)
                                    table.mergeCells(begClientRow, 1,  clientRow, 1)
                                    table.mergeCells(begClientRow, 2,  clientRow, 1)
                                else:
                                    table.setText(i, 3+showAssistants, dataDict[orgStructureName][(personName, assistantName)][0])
                                    totalByOrgStructure[3+showAssistants] += dataDict[orgStructureName][(personName, assistantName)][0]
                                    table.setText(i, 4+showAssistants, forceStringEx(dataDict[orgStructureName][(personName, assistantName)][1]).replace(QString('.'), QString(',')))
                                    totalByOrgStructure[4+showAssistants] += dataDict[orgStructureName][(personName, assistantName)][1]
                        i = table.addRow()
                        table.setText(i, 0, u'Итого по подразделению %s'%(orgStructureName), CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                        table.mergeCells(i, 0,  1, 3+showCols)
                        for t in range(self.groupingRange):
                            table.setText(i, t+3+showCols, forceStringEx(totalByOrgStructure[t+3+showCols]).replace(QString('.'), QString(',')))
                            totalByLPU[t] += totalByOrgStructure[t+3+showCols]
                    i = table.addRow()
                    table.setText(i, 0, u'ИТОГО', CReportBase.TableTotal, blockFormat=CReportBase.AlignLeft)
                    table.mergeCells(i, 0,  1, 3+showCols)
                    for t in range(self.groupingRange):
                        table.setText(i, t+3+showCols, forceStringEx(totalByLPU[t]).replace(QString('.'), QString(',')))
                else:
                    for a, (personName, assistantName) in enumerate(personsList):
                        i = table.addRow()
                        table.setText(i, 0, personName[1])
                        table.setText(i, 1, mapPersonToOrgStrAndSpeciality[personName][0])
                        table.setText(i, 2, mapPersonToOrgStrAndSpeciality[personName][1])
                        if showAssistants:
                            table.setText(i, 3, assistantName[1])
                        if detailByClient:
                            dataClientDict = dataDict[(personName, assistantName)]
                            dataClientKeys = dataClientDict.keys()
                            dataClientKeys.sort(key=lambda x: x[1])
                            clientRow = 1
                            begClientRow = i
                            for dataClientKey in dataClientKeys:
                                table.setText(i, clientCol, dataClientKey[1])
                                table.setText(i, 3+showCols, dataDict[(personName, assistantName)][dataClientKey][0])
                                table.setText(i, 4+showCols, forceStringEx(dataDict[(personName, assistantName)][dataClientKey][1]).replace(QString('.'), QString(',')))
                                if clientRow < len(dataClientKeys):
                                    clientRow += 1
                                    i = table.addRow()
                            table.mergeCells(begClientRow, 0,  clientRow, 1)
                            table.mergeCells(begClientRow, 1,  clientRow, 1)
                            table.mergeCells(begClientRow, 2,  clientRow, 1)
                        else:
                            table.setText(i, 3+showAssistants, dataDict.get((personName, assistantName), [0]*2)[0])
                            table.setText(i, 4+showAssistants, forceStringEx(dataDict.get((personName, assistantName), [0]*2)[1]).replace(QString('.'), QString(',')))
        return doc


class CReportUETActionsSetup(QtGui.QDialog, Ui_ReportUETActions):
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbMedicalAidType.setTable('rbMedicalAidType', addNone=True)
        self.cmbFinance.setTable('rbFinance', addNone=True)
        self.setDetailByOrgStructuresVisible(True)
        self.setDetailByFinanceVisible(True)
        self.setDetailByMedicalAidTypeVisible(True)
        self.setDetailByActionTypeVisible(False)
        self.setDetailByActionTypeClassesVisible(False)
        self.setDetailByActionTypeGroupVisible(False)
        self.setDetailByClientVisible(False)
        self.actionStatusList = []


    def setDetailByClientVisible(self, value):
        self._detailByClientVisible = value
        self.chkDetailByClient.setVisible(value)


    def setDetailByOrgStructuresVisible(self, value):
        self._detailByOrgStructuresVisible = value
        self.chkDetailByOrgStructures.setVisible(value)


    def setDetailByFinanceVisible(self, value):
        self._detailByFinanceVisible = value
        self.chkDetailByFinance.setVisible(value)


    def setDetailByMedicalAidTypeVisible(self, value):
        self._detailByMedicalAidTypeVisible = value
        self.chkDetailByMedicalAidType.setVisible(value)


    def setDetailByActionTypeVisible(self, value):
        self._detailByActionTypeVisible = value
        self.chkDetailByActionType.setVisible(value)


    def setDetailByActionTypeClassesVisible(self, value):
        self._detailByActionTypeClassesVisible = value
        self.chkDetailByActionTypeClasses.setVisible(value)


    def setDetailByActionTypeGroupVisible(self, value):
        self._detailByActionTypeGroupVisible = value
        self.chkDetailByActionTypeGroup.setVisible(value)


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        self.cmbFinance.setValue(params.get('financeId', None))
        self.cmbMedicalAidType.setValue(params.get('medicalAidTypeId', None))
        self.chkDetailByOrgStructures.setChecked(params.get('detailByOrgStructures', False))
        self.chkDetailByFinance.setChecked(params.get('detailByFinance', False))
        self.chkDetailByMedicalAidType.setChecked(params.get('detailByMedicalAidType', False))
        self.chkDetailByActionType.setChecked(params.get('detailByActionTypeVisible', False))
        self.chkDetailByActionTypeClasses.setChecked(params.get('detailByActionTypeClasses', False))
        self.chkDetailByActionTypeGroup.setChecked(params.get('detailByActionTypeGroup', False))
        self.actionStatusList = params.get('actionStatusList', [])
        self.setLblActionStatusListText(self.actionStatusList)
        self.cmbPersonParam.setCurrentIndex(forceInt(params.get('personParam')))
        self.cmbPostParam.setCurrentIndex(forceInt(params.get('postParam')))
        self.chkDetailByClient.setChecked(params.get('detailByClient', False))
        chkActionTypeClass = params.get('chkActionTypeClass', False)
        self.chkActionClass.setChecked(chkActionTypeClass)
        classCode = params.get('actionTypeClass', 0)
        self.cmbActionTypeClass.setCurrentIndex(classCode)
        self.cmbActionType.setClassesPopup([classCode])
        self.cmbActionType.setClass(classCode)
        self.cmbActionType.setValue(params.get('actionTypeId', None))


    def params(self):
        params = {}
        params['begDate']     = self.edtBegDate.date()
        params['endDate']     = self.edtEndDate.date()
        params['financeId']   = self.cmbFinance.value()
        params['orgStructureId'] = self.cmbOrgStructure.value()
        params['medicalAidTypeId'] = self.cmbMedicalAidType.value()
        params['personParam']     = forceInt(self.cmbPersonParam.currentIndex())
        params['postParam']     = forceInt(self.cmbPostParam.currentIndex())
        if self._detailByOrgStructuresVisible:
            params['detailByOrgStructures'] = self.chkDetailByOrgStructures.isChecked()
        if self._detailByFinanceVisible:
            params['detailByFinance'] = self.chkDetailByFinance.isChecked()
        if self._detailByMedicalAidTypeVisible:
            params['detailByMedicalAidType'] = self.chkDetailByMedicalAidType.isChecked()
        if self._detailByActionTypeVisible:
            params['detailByActionTypeVisible'] = self.chkDetailByActionType.isChecked()
        if self._detailByActionTypeClassesVisible:
            params['detailByActionTypeClasses'] = self.chkDetailByActionTypeClasses.isChecked()
        if self._detailByActionTypeGroupVisible:
            params['detailByActionTypeGroup'] = self.chkDetailByActionTypeGroup.isChecked()
        if self.actionStatusList:
            params['actionStatusList'] = self.actionStatusList
        if self._detailByClientVisible:
            params['detailByClient'] = self.chkDetailByClient.isChecked()
        chkActionTypeClass = self.chkActionClass.isChecked()
        params['chkActionTypeClass'] = chkActionTypeClass
        if chkActionTypeClass:
            params['actionTypeClass'] = self.cmbActionTypeClass.currentIndex()
            params['actionTypeId'] = self.cmbActionType.value()
        else:
            params['actionTypeClass'] = 0
            params['actionTypeId'] = None
        return params


    @pyqtSignature('int')
    def on_cmbActionTypeClass_currentIndexChanged(self, classCode):
        self.cmbActionType.setClassesPopup([classCode])
        self.cmbActionType.setClass(classCode)


    @pyqtSignature('')
    def on_btnActionStatusList_clicked(self):
        self.actionStatusList = []
        self.lblActionStatusList.setText(u'не задано')
        dialog = CActionStatusListDialog(self)
        if dialog.exec_():
            actionStatusList = dialog.values()
            if actionStatusList:
                self.setLblActionStatusListText(actionStatusList)


    def setLblActionStatusListText(self, actionStatusList):
        nameList = []
        if actionStatusList:
            for i, name in enumerate(actionStatusList):
                name = name.row() if type(name) == QModelIndex else name
                if name not in nameList:
                    nameList.append(CActionStatus.names[name])
                if name not in self.actionStatusList:
                    self.actionStatusList.append(name.row() if type(name) == QModelIndex else name)
            self.lblActionStatusList.setText(u','.join(name for name in nameList if name))
        else:
            self.lblActionStatusList.setText(u'не задано')


def getMedicalAidTypeName(val):
    medicalAidTypeId = forceRef(val)
    medicalAidTypeRecord = QtGui.qApp.db.getRecord('rbMedicalAidType', 'name', medicalAidTypeId)
    if medicalAidTypeRecord:
        return forceString(medicalAidTypeRecord.value(0))
    else:
        return '{%s}' % medicalAidTypeId


def getOrgStructureName(val):
    orgStructureId = forceRef(val)
    orgStrRecord = QtGui.qApp.db.getRecord('OrgStructure', 'name', orgStructureId)
    if orgStrRecord:
        return forceString(orgStrRecord.value(0))
    else:
        return '{%s}' % orgStructureId

