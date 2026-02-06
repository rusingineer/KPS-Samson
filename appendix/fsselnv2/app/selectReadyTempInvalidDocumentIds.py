# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2018-2025 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

# Определение готовности ЛН к передаче:
# fssStatus = ''   (не передавалось)
# - есть подпись D0 и (не требуется подпись пред.вк или есть подпись C0)
# - есть направление на МСЭ
#
# fssStatus = 'P0' (передан один период)
# - есть подпись D1 и (не требуется подпись пред.вк или есть подпись C1)
# - есть направление на МСЭ
# - есть подпись R
#
# fssStatus = 'P1' (передано два периода)
# - есть подпись D2 и (не требуется подпись пред.вк или есть подпись C2)
# - есть направление на МСЭ
# - есть подпись R
#
# fssStatus = 'P2' (передано три периода)
# - есть направление на МСЭ
# - есть подпись R
#
# fssStatus = 'M'  (передано направление на МСЭ)
# - есть подпись R
#
# требуется подпись председателя ВК для подписи Dx:
#
#    EXISTS(SELECT NULL
#           FROM TempInvalidDocument_Signature,
#           INNER JOIN Event      ON Event.tempInvalid_id = TempInvalidDocument.master_id
#           INNER JOIN Action     ON Action.event_id = Event.id
#           INNER JOIN ActionType ON ActionType.id = Action.actionType_id
#           INNER JOIN ActionPropertyType   ON ActionPropertyType.actionType_id = Action.actionType_id
#           INNER JOIN ActionProperty       ON ActionProperty.action_id=Action.id AND ActionProperty.type_id = ActionPropertyType.id AND ActionProperty.deleted=0
#           INNER JOIN ActionPropertyString ON ActionPropertyString.id = ActionProperty.id
#           WHERE TempInvalidDocument_Signature.master_id = TempInvalidDocument.id
#             AND TempInvalidDocument_Signature.subject = 'Dx'
#             AND Event.deleted = 0
#             AND Action.deleted = 0
#             AND DATE(Action.directionDate) = DATE(TempInvalidDocument_Signature.signDatetime)
#             AND ActionType.flatCode like 'inspection%'
#             AND ActionPropertyType.deleted = 0
#             AND ActionPropertyType.name = 'номер ЛН'
#             AND ActionPropertyString.value = TempInvalidDocument.number
#          )
#
# есть подпись председателя ВК для подписи Dx:
#
#    EXISTS(SELECT NULL
#           FROM TempInvalidDocument_Signature
#           WHERE TempInvalidDocument_Signature.master_id = TempInvalidDocument.id
#             AND TempInvalidDocument_Signature.subject = 'Сx'
#          )
#
#  есть направление на МСЭ
#    EXISTS(SELECT NULL
#           FROM TempInvalidDocument_Signature,
#           INNER JOIN Event      ON Event.tempInvalid_id = TempInvalidDocument.master_id
#           INNER JOIN Action     ON Action.event_id = Event.id
#           INNER JOIN ActionType ON ActionType.id = Action.actionType_id
#           INNER JOIN ActionPropertyType   ON ActionPropertyType.actionType_id = Action.actionType_id
#           INNER JOIN ActionProperty       ON ActionProperty.action_id=Action.id AND ActionProperty.type_id = ActionPropertyType.id AND ActionProperty.deleted=0
#           INNER JOIN ActionPropertyString ON ActionPropertyString.id = ActionProperty.id
#           WHERE TempInvalidDocument_Signature.master_id = TempInvalidDocument.id
#             AND TempInvalidDocument_Signature.subject = 'Dx'
#             AND Event.deleted = 0
#             AND Action.deleted = 0
#             AND DATE(Action.directionDate) = DATE(TempInvalidDocument_Signature.signDatetime)
#             AND ActionType.flatCode = 'inspection_mse'
#             AND ActionPropertyType.deleted = 0
#             AND ActionPropertyType.name = 'номер ЛН'
#             AND ActionPropertyString.value = TempInvalidDocument.number
#          )
#


from PyQt4               import QtGui
from Events.ActionStatus import CActionStatus
from library.Utils import forceDate


#from library.database         import CTableRecordCache

def formConditionForPeriod(tableTempInvalidDocument, fssStatus, doctorSubject, chairmanSubject):
    db = QtGui.qApp.db

    tableTempInvalidDocumentAlias     = tableTempInvalidDocument.alias('TID')
    tableTempInvalidDocumentSignature = db.table('TempInvalidDocument_Signature')
    tableEvent                = db.table('Event')
    tableAction               = db.table('Action')
    tableActionType           = db.table('ActionType')
    tableActionPropertyType   = db.table('ActionPropertyType')
    tableActionProperty       = db.table('ActionProperty')
    tableActionPropertyString = db.table('ActionProperty_String')
    table = tableTempInvalidDocumentAlias
    table = table.innerJoin(tableTempInvalidDocumentSignature, [ tableTempInvalidDocumentSignature['master_id'].eq(tableTempInvalidDocumentAlias['id']),
                                                                 tableTempInvalidDocumentSignature['subject'].eq(doctorSubject),
                                                           ]
                           )
    table = table.innerJoin(tableEvent, tableEvent['tempInvalid_id'].eq(tableTempInvalidDocumentAlias['master_id']))
    table = table.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
    table = table.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
    table = table.innerJoin(tableActionPropertyType, tableActionPropertyType['actionType_id'].eq(tableAction['actionType_id']))
    table = table.innerJoin(tableActionProperty, [ tableActionProperty['action_id'].eq(tableAction['id']),
                                                   tableActionProperty['type_id'].eq(tableActionPropertyType['id']),
                                                   tableActionProperty['deleted'].eq(0)
                                                 ]
                           )
    table = table.innerJoin(tableActionPropertyString, tableActionPropertyString['id'].eq(tableActionProperty['id']))
    # это условие "существует направление на ВК"
    cond = [ tableTempInvalidDocumentAlias['id'].eq(tableTempInvalidDocument['id']),
             tableEvent['deleted'].eq(0),
             tableAction['deleted'].eq(0),
             tableAction['directionDate'].dateEq(tableTempInvalidDocumentSignature['signDatetime']),
             tableActionType['flatCode'].like('inspection%'),
             tableActionPropertyType['deleted'].eq(0),
             tableActionPropertyType['name'].eq(u'номер ЛН'),
             tableActionPropertyString['value'].eq(tableTempInvalidDocument['number'])
           ]
    result = db.joinAnd([ tableTempInvalidDocument['fssStatus'].eq(fssStatus),
                          db.existsStmt(tableTempInvalidDocumentSignature,
                                        [ tableTempInvalidDocumentSignature['master_id'].eq(tableTempInvalidDocument['id']),
                                          tableTempInvalidDocumentSignature['subject'].eq(doctorSubject)
                                        ]
                                       ),
                          db.joinOr([
                                      db.existsStmt(tableTempInvalidDocumentSignature,
                                                    [ tableTempInvalidDocumentSignature['master_id'].eq(tableTempInvalidDocument['id']),
                                                      tableTempInvalidDocumentSignature['subject'].eq(chairmanSubject)
                                                    ]
                                                   ),
                                      db.notExistsStmt(table, cond)
                                    ]
                                   )
                        ]
                       )
    return result


def formTableAndCondtionForMse(tableTempInvalidDocumentId):
    db = QtGui.qApp.db

    tableTempInvalidDocumentAlias = db.table('TempInvalidDocument').alias('TID')
    tableTempInvalid          = db.table('TempInvalid')
    # tableEvent                = db.table('Event')
    # tableAction               = db.table('Action')
    # tableActionType           = db.table('ActionType')
    # tableActionPropertyType   = db.table('ActionPropertyType')
    # tableActionProperty       = db.table('ActionProperty')
    # tableActionPropertyString = db.table('ActionProperty_String')
    table = tableTempInvalidDocumentAlias
    table = table.innerJoin(tableTempInvalid, tableTempInvalid['id'].eq(tableTempInvalidDocumentAlias['master_id']))
    # table = table.innerJoin(tableEvent, tableEvent['id'].eq(tableTempInvalid['event_id']))
    # table = table.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
    # table = table.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
    # table = table.innerJoin(tableActionPropertyType, tableActionPropertyType['actionType_id'].eq(tableAction['actionType_id']))
    # table = table.innerJoin(tableActionProperty, [ tableActionProperty['action_id'].eq(tableAction['id']),
    #                                                tableActionProperty['type_id'].eq(tableActionPropertyType['id']),
    #                                                tableActionProperty['deleted'].eq(0)
    #                                              ]
    #                        )
    # table = table.innerJoin(tableActionPropertyString, tableActionPropertyString['id'].eq(tableActionProperty['id']))
    # это условие "существует направление на МСЭ"
    cond = [ tableTempInvalidDocumentAlias['id'].eq(tableTempInvalidDocumentId),
             tableTempInvalid['mseDate'].isNotNull()
             # tableEvent['deleted'].eq(0),
             # tableAction['deleted'].eq(0),
             # # tableAction['status'].eq(CActionStatus.withoutResult),
             # tableAction['endDate'].isNotNull(),
             # tableActionType['flatCode'].eq('inspection_mse'),
             # tableActionPropertyType['deleted'].eq(0),
             # tableActionPropertyType['name'].eq(u'номер ЛН'),
             # tableActionPropertyString['value'].eq(tableTempInvalidDocumentAlias['number'])
           ]
    return table, cond


def getDateOfDirectionToMse(tempInvalidDocumentId):
    db = QtGui.qApp.db
    tableTempInvalidDocument = db.table('TempInvalidDocument')
    tableTempInvalid = db.table('TempInvalid')
    table = tableTempInvalid.leftJoin(tableTempInvalidDocument,
                                      tableTempInvalid['id'].eq(tableTempInvalidDocument['master_id']))
    record = db.getRecordEx(table,
                            tableTempInvalid['mseDate'],
                            tableTempInvalidDocument['id'].eq(tempInvalidDocumentId)
                            )
    if record:
        return forceDate(record.value('mseDate'))
    else:
        return None

def formConditionForDirectionToMse(tableTempInvalidDocument):
    db = QtGui.qApp.db

    fssStatusList = ['', 'P0', 'P1', 'P2', 'P3']
    table, cond = formTableAndCondtionForMse(tableTempInvalidDocument['id'])
    result = db.joinAnd([ tableTempInvalidDocument['fssStatus'].inlist(fssStatusList),
                          db.existsStmt(table, cond)
                        ]
                       )
    return result


def formConditionForResult(tableTempInvalidDocument):
    db = QtGui.qApp.db

    fssStatusList = ['', 'P0', 'P1', 'P2', 'P3', 'M']
    resultSubject = 'R'

    tableTempInvalidDocumentSignature = db.table('TempInvalidDocument_Signature')

    result = db.joinAnd([ tableTempInvalidDocument['fssStatus'].inlist(fssStatusList),
                          db.existsStmt(tableTempInvalidDocumentSignature,
                                        [ tableTempInvalidDocumentSignature['master_id'].eq(tableTempInvalidDocument['id']),
                                          tableTempInvalidDocumentSignature['subject'].eq(resultSubject)
                                        ]
                                       ),
                        ]
                       )
    return result


def selectReadyTempInvalidDocumentIds(filter):
    db = QtGui.qApp.db
    fssSystemId    = QtGui.qApp.getFssSystemId()
    orgId          = QtGui.qApp.getCurrentOrgId()
    orgStructureId = filter.get('orgStructureId', None)
    personId       = filter.get('personId', None)
    number         = filter.get('number', None)
    begDate        = filter.get('begDate', None)
    endDate        = filter.get('endDate', None)
    tempInvalidDocTypeId = QtGui.qApp.getTempInvalidDocTypeId()

    tableTempInvalidDocument          = db.table('TempInvalidDocument')
    tableTempInvalid                  = db.table('TempInvalid')
    tablePerson                       = db.table('Person')
    tableTempInvalidDocumentSignature = db.table('TempInvalidDocument_Signature')
    tableTempInvalidDocumentExport    = db.table('TempInvalidDocument_Export')

    table = tableTempInvalidDocument
    table = table.innerJoin( tableTempInvalid,
                             tableTempInvalid['id'].eq(tableTempInvalidDocument['master_id'])
                           )
    table = table.leftJoin ( tableTempInvalidDocumentSignature,
                             tableTempInvalidDocumentSignature['master_id'].eq(tableTempInvalidDocument['id'])
                           )
    table = table.innerJoin(tablePerson,
                            db.joinOr([ tablePerson['id'].eq(tableTempInvalid['person_id']),
                                        tablePerson['id'].eq(tableTempInvalidDocumentSignature['signPerson_id'])
                                      ]
                                     )
                           )
    table = table.leftJoin (tableTempInvalidDocumentExport,
                            [ tableTempInvalidDocumentExport['master_id'].eq(tableTempInvalidDocument['id']),
                              tableTempInvalidDocumentExport['masterDatetime'].eq(tableTempInvalidDocument['modifyDatetime']),
                              tableTempInvalidDocumentExport['system_id'].eq(fssSystemId)
                            ]
                           )
    cond = [ tableTempInvalidDocument['deleted'].eq(0),
             tableTempInvalidDocument['electronic'].eq(1),
             tableTempInvalidDocument['annulmentReason_id'].isNull(),
             tableTempInvalid['deleted'].eq(0),
             tableTempInvalid['doctype_id'].eq(tempInvalidDocTypeId),
             tableTempInvalidDocumentExport['id'].isNull()
           ]
    if personId:
        cond.append(tablePerson['id'].eq(personId))
    elif orgStructureId:
        orgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', orgStructureId)
        cond.append(tablePerson['orgStructure_id'].inlist(orgStructureIdList))
    else:
        cond.append(tablePerson['org_id'].eq(orgId))

    if number:
        cond.append(tableTempInvalidDocument['number'].eq(number))
    if begDate:
        cond.append(tableTempInvalidDocument['modifyDatetime'].ge(begDate))
    if endDate:
        cond.append(tableTempInvalidDocument['modifyDatetime'].lt(endDate.addDays(1)))

    condByStatuses = [ formConditionForPeriod(tableTempInvalidDocument, '',   'D0', 'C0'),
                       formConditionForPeriod(tableTempInvalidDocument, 'P0', 'D1', 'C1'),
                       formConditionForPeriod(tableTempInvalidDocument, 'P1', 'D2', 'C2'),
                       formConditionForDirectionToMse(tableTempInvalidDocument),
                       formConditionForResult(tableTempInvalidDocument),
                     ]
    cond.append( db.joinOr(condByStatuses) )
    idList = db.getDistinctIdList(table,
                                  idCol=tableTempInvalidDocument['id'].name(),
                                  where=cond,
                                  order='TempInvalidDocument.id'
                                 )
    return idList


def selectReadyTempInvalidDocumentById(tempId, fssSystemId):
    db = QtGui.qApp.db

    tableTempInvalidDocument = db.table('TempInvalidDocument')
    tableTempInvalid         = db.table('TempInvalid')
    tableTempInvalidReason   = db.table('rbTempInvalidReason')
    tablePerson              = db.table('Person')
#    for subject in ('D0', 'C0', 'D1', 'C1', 'D2', 'C2', 'B', 'R'):
#        tableSignatures[subject] = db.table('TempInvalidDocument_Signature').alias('tableTIDS' + subject)

    tableTempInvalidDocumentExport    = db.table('TempInvalidDocument_Export')

    table = tableTempInvalidDocument
    table = table.innerJoin( tableTempInvalid,
                             tableTempInvalid['id'].eq(tableTempInvalidDocument['master_id'])
                           )
    table = table.leftJoin( tableTempInvalidReason,
                            tableTempInvalidReason['id'].eq(tableTempInvalid['tempInvalidReason_id'])
                          )

    tableSignatures = {}
    for subject in ('D0', 'C0', 'D1', 'C1', 'D2', 'C2', 'B', 'R'):
        tableSignature = tableSignatures[subject] = db.table('TempInvalidDocument_Signature').alias('SignatureFor' + subject)
        table = table.leftJoin( tableSignature,
                                db.joinAnd([ tableSignature['master_id'].eq(tableTempInvalidDocument['id']),
                                             tableSignature['subject'].eq(subject)
                                           ]
                                          )
                              )
    table = table.innerJoin(tablePerson,
                            db.joinOr([ tablePerson['id'].eq(tableTempInvalid['person_id']),
                                        tablePerson['id'].eq(tableSignatures['C0']['signPerson_id']),
                                        tablePerson['id'].eq(tableSignatures['D0']['signPerson_id']),
                                        tablePerson['id'].eq(tableSignatures['C1']['signPerson_id']),
                                        tablePerson['id'].eq(tableSignatures['D1']['signPerson_id']),
                                        tablePerson['id'].eq(tableSignatures['C2']['signPerson_id']),
                                        tablePerson['id'].eq(tableSignatures['D2']['signPerson_id']),
                                        tablePerson['id'].eq(tableSignatures['B']['signPerson_id']),
                                        tablePerson['id'].eq(tableSignatures['R']['signPerson_id']),
                                      ]
                                     )
                           )
    table = table.leftJoin (tableTempInvalidDocumentExport,
                            [ tableTempInvalidDocumentExport['master_id'].eq(tableTempInvalidDocument['id']),
                              tableTempInvalidDocumentExport['masterDatetime'].eq(tableTempInvalidDocument['modifyDatetime']),
                              tableTempInvalidDocumentExport['system_id'].eq(fssSystemId)
                            ]
                           )
    cond = [ tableTempInvalidDocument['deleted'].eq(0),
             tableTempInvalidDocument['electronic'].eq(1),
             tableTempInvalidDocument['annulmentReason_id'].isNull(),
             tableTempInvalid['deleted'].eq(0),
             tableTempInvalid['id'].eq(tempId),
             tableTempInvalidDocumentExport['id'].isNull()
           ]


    condByStatuses = [ formConditionForPeriod(tableTempInvalidDocument, '', 'D0', 'C0'),
                       formConditionForPeriod(tableTempInvalidDocument, 'P0', 'D1', 'C1'),
                       formConditionForPeriod(tableTempInvalidDocument, 'P1', 'D2', 'C2'),
                       formConditionForDirectionToMse(tableTempInvalidDocument),
                       formConditionForResult(tableTempInvalidDocument),
                     ]
    cond.append( db.joinOr(condByStatuses) )
    idList = db.getDistinctIdList(table,
                                  idCol=tableTempInvalidDocument['id'].name(),
                                  where=cond,
                                  order='TempInvalidDocument.id'
                                 )
    return idList
