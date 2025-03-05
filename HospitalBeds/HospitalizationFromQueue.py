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

from library.DialogBase         import CDialogBase
from library.Utils              import forceDate, forceInt, forceRef, forceString, forceDateTime

from Events.CreateEvent         import requestNewEvent
from Events.Utils               import getActionTypeIdListByFlatCode
from Registry.Utils             import CCheckNetMixin


class CHospitalizationFromQueue(CDialogBase, CCheckNetMixin):
    def __init__(self, parent, clientId = None, eventId = None, directionInfo = [], isHealthResort = False):
        CDialogBase.__init__(self, parent)
        CCheckNetMixin.__init__(self)
        self.clientId = clientId
        self.eventId = eventId
        self.directionInfo = directionInfo
        self.isHealthResort = isHealthResort
        self.newEventId = None


    def requestNewEvent(self):
        self.newEventId = None
        if self.eventId and self.clientId:
            params = {}
            actionId, orgStructureId, bedId, begDate, endDate, execDate, plannedEndDate, personId, _, form, relegateOrgId, docNum, srcDate = self.getDataQueueEvent(self.eventId)
            params['widget'] = self
            params['clientId'] = self.clientId
            params['flagHospitalization'] = True
            params['valueProperties'] = [orgStructureId, bedId]
            params['dateTime'] = None
            params['personId'] = None
            params['planningEventId'] = self.eventId
            params['planningActionId'] = actionId
            params['prevEventId'] = self.eventId
            params['financeId'] = self.getPlanningFinanceId(self.eventId)
            params['protocolQuoteId'] = self.getProtocolQuote(self.eventId) if form == '027' else None
            params['eventTypeFilterHospitalization'] = 2 if not self.isHealthResort else 5
            params['diagnos'] = self.getDiagnosString(self.eventId)
            params['relegateOrgId'] = relegateOrgId
            params['docNum'] = docNum
            params['srcOrgId'] = relegateOrgId if relegateOrgId else self.directionInfo[1]
            relegatePersonId = personId #self.directionInfo[6] if self.directionInfo[6] else self.directionInfo[2]
            if QtGui.qApp.currentOrgId() == relegateOrgId:
                params['relegatePersonId'] = relegatePersonId
                params['srcPerson'] = None
            else:
                params['relegatePersonId'] = None
                params['srcPerson'] = forceString(QtGui.qApp.db.translate('vrbPersonWithSpeciality', 'id', relegatePersonId, 'name')) if relegatePersonId else ''
            params['srcNumber'] = docNum if docNum else (self.directionInfo[4] if self.directionInfo[4] else self.directionInfo[0])
            params['srcDate'] = self.directionInfo[5] if self.directionInfo[5] else self.directionInfo[3]
            params['plannedEndDate'] = plannedEndDate
            params['planningActionId'] = actionId
            params['srcMKB'] = self.directionInfo[7] if self.directionInfo[7] else ''
            self.newEventId = requestNewEvent(params)
            # if self.newEventId:
            #     if actionId:
            #         self.editReceivedQueueEvent(actionId, begDate, endDate, execDate, plannedEndDate, self.newEventId)
            return self.newEventId
        return None


    def getPlanningFinanceId(self, eventId):
        if eventId:
            db = QtGui.qApp.db
            tableEvent = db.table('Event')
            tableAction = db.table('Action')
            tableActionType = db.table('ActionType')
            tableActionPRBF = db.table('ActionProperty_rbFinance')
            tableActionProperty = db.table('ActionProperty')
            tableAPT = db.table('ActionPropertyType')
            table = tableEvent.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
            table = table.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
            table = table.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
            table = table.innerJoin(tableActionProperty, tableActionProperty['type_id'].eq(tableAPT['id']))
            table = table.innerJoin(tableActionPRBF, tableActionPRBF['id'].eq(tableActionProperty['id']))
            cols = [tableActionPRBF['value']]
            cond = [tableEvent['id'].eq(eventId),
                    tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode(u'planning%')),
                    tableEvent['deleted'].eq(0),
                    tableAction['deleted'].eq(0),
                    tableAction['id'].isNotNull(),
                    tableActionType['deleted'].eq(0),
                    tableAPT['deleted'].eq(0),
                    tableAPT['name'].like(u'источник финансирования'),
                    tableActionProperty['deleted'].eq(0),
                    tableActionProperty['action_id'].eq(tableAction['id'])
                    ]
            record = db.getRecordEx(table, cols, cond, 'Action.id DESC')
            return forceRef(record.value('value')) if record else None
        return None


    def getProtocolQuote(self, eventId):
        if eventId:
            db = QtGui.qApp.db
            tableEvent = db.table('Event')
            tableAction = db.table('Action')
            tableActionType = db.table('ActionType')
            tableActionCQ = db.table('ActionProperty_Client_Quoting')
            tableActionProperty = db.table('ActionProperty')
            tableAPT = db.table('ActionPropertyType')
            table = tableEvent.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
            table = table.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
            table = table.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
            table = table.innerJoin(tableActionProperty, tableActionProperty['type_id'].eq(tableAPT['id']))
            table = table.innerJoin(tableActionCQ, tableActionCQ['id'].eq(tableActionProperty['id']))
            cols = [tableActionCQ['value']]
            cond = [tableEvent['id'].eq(eventId),
                    tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode(u'protocol%')),
                    tableEvent['deleted'].eq(0),
                    tableAction['deleted'].eq(0),
                    tableAction['id'].isNotNull(),
                    tableActionType['deleted'].eq(0),
                    tableAPT['deleted'].eq(0),
                    tableAPT['name'].like(u'Квота'),
                    tableActionProperty['deleted'].eq(0),
                    tableActionProperty['action_id'].eq(tableAction['id'])
                    ]
            record = db.getRecordEx(table, cols, cond, 'Action.id DESC')
            return forceRef(record.value('value')) if record else None
        return None


    def getDiagnosString(self, eventId):
        if eventId:
            db = QtGui.qApp.db
            tableEvent = db.table('Event')
            tableAction = db.table('Action')
            tableActionType = db.table('ActionType')
            table = tableEvent.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
            table = table.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
            cols = [tableActionType['flatCode']]
            cols.append('''(SELECT APS.value
                            FROM ActionPropertyType AS APT
                            INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id
                            INNER JOIN ActionProperty_String AS APS ON APS.id=AP.id
                            WHERE  Action.id IS NOT NULL AND APT.actionType_id=Action.actionType_id AND AP.action_id=Action.id AND APT.deleted=0 AND APT.name = '%s' limit 1) AS diagnos'''%(u'Диагноз'))
            cond = [tableEvent['id'].eq(eventId),
                    tableEvent['deleted'].eq(0),
                    tableAction['deleted'].eq(0),
                    tableActionType['deleted'].eq(0)
                    ]
            records = db.getRecordList(table, cols, cond, 'Action.endDate DESC')
            for record in records:
                diagnos = forceString(record.value('diagnos'))
                flatCode = forceString(record.value('flatCode'))
                if u'protocol' in flatCode.lower():
                    return diagnos
            for record in records:
                diagnos = forceString(record.value('diagnos'))
                if diagnos:
                    return diagnos
        return None


    def getDataQueueEvent(self, eventId = None):
        orgStructureId = None
        begDate = None
        endDate = None
        plannedEndDate = None
        actionId = None
        bedId = None
        execDate = None
        personId = None
        setPersonId = None
        relegateOrgId = None
        outRelegateOrgId = None
        docNum = ''
        form = ''
        srcDate = None
        if eventId:
            db = QtGui.qApp.db
            tableAPHB = db.table('ActionProperty_HospitalBed')
            tableAPT = db.table('ActionPropertyType')
            
            tableAP = db.table('ActionProperty')
            tableActionType = db.table('ActionType')
            tableAction = db.table('Action')
            tableEvent = db.table('Event')
            tableEventType = db.table('EventType')
            tableAPOS = db.table('ActionProperty_OrgStructure')
            tableAPTnum = db.table('ActionPropertyType').alias('apt_number')
            tableAPnum = db.table('ActionProperty').alias('ap_number')
            tableAPSnum = db.table('ActionProperty_String').alias('apv_number')
            cols = [tableAction['id'],
                    tableAction['begDate'],
                    tableAction['endDate'],
                    tableAction['plannedEndDate'],
                    tableAction['setPerson_id'],
                    tableAction['person_id'],
                    tableAction['directionDate'],
                    tableEvent['execDate'],
                    tableEventType['form'],
                    tableEvent['srcDate'],
                    tableAPHB['value'].alias('bedId'),
                    tableAPSnum['value'].alias('docNum')
                    ]
            cols.append(u'''(SELECT APS.`value`
                             FROM ActionProperty_String AS APS
                             LEFT JOIN ActionProperty AS AP ON APS.`id` = AP.`id`
                             LEFT JOIN Action AS ACT ON AP.`action_id` = ACT.`id`
                             LEFT JOIN ActionPropertyType AS APT ON APT.`actionType_id` = ACT.`actionType_id`
                             WHERE APT.`name` = 'Номер документа' AND ACT.`id` = Action.`id` AND AP.`type_id` = APT.`id`
                             AND ACT.`deleted` = 0 AND AP.`deleted` = 0 AND APT.`deleted` = 0) AS docNum''')
            if QtGui.qApp.defaultKLADR().startswith('01'):
                cols.append(u"""(SELECT Organisation.id 
                    FROM Person  
                    left join OrgStructure as PersonOrgStructure on PersonOrgStructure.id = Person.orgStructure_id
                    left join OrgStructure as Parent1 on Parent1.id = PersonOrgStructure.parent_id
                    left join OrgStructure as Parent2 on Parent2.id = Parent1.parent_id
                    left join OrgStructure as Parent3 on Parent3.id = Parent2.parent_id
                    left join OrgStructure as Parent4 on Parent4.id = Parent3.parent_id
                    left join OrgStructure as Parent5 on Parent5.id = Parent4.parent_id
                    LEFT JOIN Organisation ON Organisation.infisCode = IF(length(trim(PersonOrgStructure.bookkeeperCode))>=5, PersonOrgStructure.bookkeeperCode,
                                    IF(length(trim(Parent1.bookkeeperCode))>=5, Parent1.bookkeeperCode,
                                      IF(length(trim(Parent2.bookkeeperCode))>=5, Parent2.bookkeeperCode,
                                        IF(length(trim(Parent3.bookkeeperCode))>=5, Parent3.bookkeeperCode,
                                          IF(length(trim(Parent4.bookkeeperCode))>=5, Parent4.bookkeeperCode, Parent5.bookkeeperCode))))) AND Organisation.deleted = 0
                    WHERE Person.id = Action.person_id
                    LIMIT 1) AS relegateOrg_id""")
            else:
                cols.append(u"""(SELECT Organisation.id 
    FROM Person  
    left join OrgStructure as PersonOrgStructure on PersonOrgStructure.id = Person.orgStructure_id
    left join OrgStructure as Parent1 on Parent1.id = PersonOrgStructure.parent_id
    left join OrgStructure as Parent2 on Parent2.id = Parent1.parent_id
    left join OrgStructure as Parent3 on Parent3.id = Parent2.parent_id
    left join OrgStructure as Parent4 on Parent4.id = Parent3.parent_id
    left join OrgStructure as Parent5 on Parent5.id = Parent4.parent_id
    LEFT JOIN Organisation ON Organisation.infisCode = IF(length(trim(PersonOrgStructure.bookkeeperCode))=5, PersonOrgStructure.bookkeeperCode,
                    IF(length(trim(Parent1.bookkeeperCode))=5, Parent1.bookkeeperCode,
                      IF(length(trim(Parent2.bookkeeperCode))=5, Parent2.bookkeeperCode,
                        IF(length(trim(Parent3.bookkeeperCode))=5, Parent3.bookkeeperCode,
                          IF(length(trim(Parent4.bookkeeperCode))=5, Parent4.bookkeeperCode, Parent5.bookkeeperCode))))) AND Organisation.deleted = 0
    WHERE Person.id = Action.person_id
    LIMIT 1) AS relegateOrg_id""")
            cols.append(u"Action.org_id AS outRelegateOrg_id")
                
            queryTable = tableActionType.innerJoin(tableAction, tableActionType['id'].eq(tableAction['actionType_id']))
            queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.innerJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
            queryTable = queryTable.leftJoin(tableAP, db.joinAnd([tableAP['action_id'].eq(tableAction['id']),
                                                                   tableAP['deleted'].eq(0)]))
            queryTable = queryTable.leftJoin(tableAPT, db.joinAnd([tableAPT['actionType_id'].eq(tableAction['actionType_id']),
                                                                    tableAP['type_id'].eq(tableAPT['id']),
                                                                    tableAPT['deleted'].eq(0),
                                                                    tableAP['deleted'].eq(0),
                                                                    tableAPT['typeName'].like('HospitalBed')
                                                                    ]))
            queryTable = queryTable.leftJoin(tableAPTnum, db.joinAnd([tableAPTnum['actionType_id'].eq(tableAction['actionType_id']),
                                                                    tableAPTnum['deleted'].eq(0),
                                                                    tableAPTnum['name'].like(u'Номер направления')
                                                                    ]))
            queryTable = queryTable.leftJoin(tableAPnum, db.joinAnd([tableAPnum['type_id'].eq(tableAPTnum['id']),
                                                                    tableAPnum['action_id'].eq(tableAction['id']),
                                                                    tableAPnum['deleted'].eq('0')
                                                                    ]))
            queryTable = queryTable.leftJoin(tableAPSnum, tableAPSnum['id'].eq(tableAPnum['id']))                                                                      
            queryTable = queryTable.leftJoin(tableAPHB, db.joinAnd([tableAPHB['id'].eq(tableAP['id']),
                                                                     tableAP['deleted'].eq(0)]))
            cond = [tableActionType['flatCode'].like('planning'),
                    tableAction['deleted'].eq(0),
                    tableActionType['deleted'].eq(0),
                    tableEvent['deleted'].eq(0),
                    tableEventType['deleted'].eq(0),
                    tableAction['event_id'].eq(eventId)
                    ]
            record = db.getRecordEx(queryTable, cols, cond, 'bedId, Action.plannedEndDate')
            if record:
                actionId = forceRef(record.value('id'))
                bedId = forceRef(record.value('bedId'))
                begDate = forceDate(record.value('begDate'))
                endDate = forceDate(record.value('endDate'))
                plannedEndDate = forceDate(record.value('plannedEndDate'))
                execDate = forceDate(record.value('execDate'))
                personId = forceRef(record.value('person_id'))
                form     = forceString(record.value('form'))
                relegateOrgId = forceInt(record.value('relegateOrg_id'))
                outRelegateOrgId = forceRef(record.value('outRelegateOrg_id'))
                docNum = forceString(record.value('docNum'))
                srcDate = forceDate(record.value('directionDate')) or forceDate(record.value('srcDate'))

            cols = [tableAction['id'],
                    tableAction['begDate'],
                    tableAction['endDate'],
                    tableAction['plannedEndDate'],
                    tableAction['person_id'],
                    tableEvent['execDate'],
                    tableEventType['form'],
                    tableAPOS['value'].alias('orgStructureId'),
                    tableAPSnum['value'].alias('docNum')
                    ]
            cols.append(u"""(SELECT Organisation.id 
FROM Person  
left join OrgStructure as PersonOrgStructure on PersonOrgStructure.id = Person.orgStructure_id
left join OrgStructure as Parent1 on Parent1.id = PersonOrgStructure.parent_id
left join OrgStructure as Parent2 on Parent2.id = Parent1.parent_id
left join OrgStructure as Parent3 on Parent3.id = Parent2.parent_id
left join OrgStructure as Parent4 on Parent4.id = Parent3.parent_id
left join OrgStructure as Parent5 on Parent5.id = Parent4.parent_id
LEFT JOIN Organisation ON Organisation.infisCode = IF(length(trim(PersonOrgStructure.bookkeeperCode))=5, PersonOrgStructure.bookkeeperCode,
                IF(length(trim(Parent1.bookkeeperCode))=5, Parent1.bookkeeperCode,
                  IF(length(trim(Parent2.bookkeeperCode))=5, Parent2.bookkeeperCode,
                    IF(length(trim(Parent3.bookkeeperCode))=5, Parent3.bookkeeperCode,
                      IF(length(trim(Parent4.bookkeeperCode))=5, Parent4.bookkeeperCode, Parent5.bookkeeperCode))))) AND Organisation.deleted = 0
WHERE Person.id = Action.person_id
LIMIT 1) AS relegateOrg_id""")
            cols.append(u"Action.org_id AS outRelegateOrg_id")

            cols.append(u'''(SELECT ActionProperty_String.`value` FROM ActionProperty_String
                LEFT JOIN ActionProperty ON (ActionProperty_String.`id` = ActionProperty.`id`)
                LEFT JOIN Action as ACT ON (ActionProperty.`action_id` = ACT.`id`)
                LEFT JOIN ActionPropertyType ON (ActionPropertyType.`actionType_id` = ACT.`actionType_id`)
                WHERE ActionPropertyType.`name` = 'Номер документа' AND (ACT.`id` = Action.`id`) AND (ActionProperty_String.`value` IS NOT NULL
                AND ActionProperty_String.`value` != '') ORDER BY ActionProperty_String.id DESC LIMIT 1) AS docNum''')

            cond = [tableActionType['flatCode'].like(u'planning%'),
                    tableAction['deleted'].eq(0),
                    tableEvent['deleted'].eq(0),
                    tableAction['event_id'].eq(eventId),
                    tableActionType['deleted'].eq(0),
                    tableEventType['deleted'].eq(0),
                    tableAPT['deleted'].eq(0)
                    ]
            queryNoBed = tableActionType.innerJoin(tableAction, tableActionType['id'].eq(tableAction['actionType_id']))
            queryNoBed = queryNoBed.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
            queryNoBed = queryNoBed.innerJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
            queryNoBed = queryNoBed.leftJoin(tableAP, db.joinAnd([tableAP['action_id'].eq(tableAction['id']),
                                                                   tableAP['deleted'].eq(0)]))
            queryNoBed = queryNoBed.leftJoin(tableAPT, db.joinAnd([tableAPT['actionType_id'].eq(tableAction['actionType_id']),
                                                                    tableAP['type_id'].eq(tableAPT['id']),
                                                                    tableAPT['deleted'].eq(0),
                                                                    tableAP['deleted'].eq(0),
                                                                    tableAPT['typeName'].like('OrgStructure')
                                                                    ]))
            queryNoBed = queryNoBed.leftJoin(tableAPTnum, db.joinAnd([tableAPTnum['actionType_id'].eq(tableAction['actionType_id']),
                                                                    tableAPTnum['deleted'].eq(0),
                                                                    tableAPTnum['name'].like(u'Номер направления')
                                                                    ]))
            queryNoBed = queryNoBed.leftJoin(tableAPnum, db.joinAnd([tableAPnum['type_id'].eq(tableAPTnum['id']),
                                                                    tableAPnum['action_id'].eq(tableAction['id']),
                                                                    tableAPnum['deleted'].eq('0')
                                                                    ]))
            queryNoBed = queryNoBed.leftJoin(tableAPSnum, tableAPSnum['id'].eq(tableAPnum['id']))  
            queryNoBed = queryNoBed.leftJoin(tableAPOS, db.joinAnd([tableAPOS['id'].eq(tableAP['id']),
                                                                     tableAP['deleted'].eq(0)]))
            recordNoBed = db.getRecordEx(queryNoBed, cols, cond, 'orgStructureId, Action.plannedEndDate')
            if recordNoBed:
                actionId = forceRef(recordNoBed.value('id'))
                orgStructureId = forceRef(recordNoBed.value('orgStructureId'))
                begDate = forceDate(recordNoBed.value('begDate'))
                endDate = forceDate(recordNoBed.value('endDate'))
                execDate = forceDate(recordNoBed.value('execDate'))
                plannedEndDate = forceDate(recordNoBed.value('plannedEndDate'))
                personId = forceRef(recordNoBed.value('person_id'))
                setPersonId = forceRef(record.value('setPerson_id'))
                form     = forceString(recordNoBed.value('form'))
                relegateOrgId = forceInt(record.value('relegateOrg_id'))
                outRelegateOrgId = forceRef(record.value('outRelegateOrg_id'))
                docNum = forceString(record.value('docNum'))
        return actionId, orgStructureId, bedId, begDate, endDate, execDate, plannedEndDate, personId if not outRelegateOrgId else None, setPersonId,  form, outRelegateOrgId if outRelegateOrgId else relegateOrgId, docNum, srcDate


    def editReceivedQueueEvent(self, actionId, begDate, endDate, execDate, plannedEndDate, newEventId):
        if actionId:
            db = QtGui.qApp.db
            tableAction = db.table('Action')
            tableEvent = db.table('Event')
            record = db.getRecordEx(tableEvent, [tableEvent['setDate']], [tableEvent['id'].eq(newEventId), tableEvent['deleted'].eq(0)])
            setDate = forceDateTime(record.value('setDate')) if record else None
            if not endDate:
                tableEvent = db.table('Event')
                record = db.getRecordEx(tableEvent, [tableEvent['setDate']], [tableEvent['id'].eq(newEventId), tableEvent['deleted'].eq(0)])
                setDate = forceDateTime(record.value('setDate')) if record else None
                db.updateRecords(tableAction, tableAction['endDate'].eq(setDate), [tableAction['id'].eq(actionId), tableAction['deleted'].eq(0)])
                db.updateRecords(tableAction, tableAction['status'].eq(2), [tableAction['id'].eq(actionId), tableAction['deleted'].eq(0)])
                if not begDate:
                    db.updateRecords(tableAction, tableAction['begDate'].eq(setDate), [tableAction['id'].eq(actionId), tableAction['deleted'].eq(0)])
#            if not plannedEndDate:
#                db.updateRecords(tableAction, tableAction['plannedEndDate'].eq(setDate), [tableAction['id'].eq(actionId), tableAction['deleted'].eq(0)])
