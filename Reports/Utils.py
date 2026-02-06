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

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QString, QTime

from library.Utils import forceDateTime, forceInt, forceRef, forceString, formatShortName
from Events.Utils              import getActionTypeIdListByFlatCode
from RefBooks.ContingentType.List import CContingentTypeTranslator


def getAgeClass(clientAge):
    if 18 <= clientAge <= 36:
        return 0
    if 39 <= clientAge <= 60:
        return 1
    if clientAge>60:
        return 2
    return None


def updateLIKE(val):
    if val.endswith('...') or val.endswith('%') or val.endswith('%%') or val.startswith('...') or val.startswith('%') or val.startswith('%%'):
        return u'''LIKE '%s' '''%(val)
    else:
        return u'''= '%s' '''%(val)


def existsPropertyValue(tableName, propertyName, value):
    return u'''EXISTS(SELECT APV.id
        FROM ActionProperty AS AP
        INNER JOIN ActionPropertyType AS APT ON AP.type_id = APT.id
        INNER JOIN %s AS APV ON APV.id = AP.id
        WHERE AP.action_id = Action.id AND APT.actionType_id = Action.actionType_id
        AND  Action.id IS NOT NULL
        AND APT.deleted = 0 AND AP.deleted = 0 AND APT.name %s AND APV.value %s)'''%(tableName, updateLIKE(propertyName), updateLIKE(value))


def getAdultCount(femaleAge=55, maleAge=60):
    return u'''EXISTS(SELECT A.id
    FROM Action AS A
    INNER JOIN ActionType AS AT ON AT.id=A.actionType_id
    INNER JOIN Event AS E ON A.event_id=E.id
    INNER JOIN Client AS C ON E.client_id=C.id
    WHERE A.deleted = 0 AND Action.id IS NOT NULL AND A.id = Action.id
    AND (age(C.birthDate, A.begDate)) >= IF(Client.sex = 2, %d, IF(Client.sex = 1, %d, %d)))'''%(femaleAge, maleAge, femaleAge)


def getAdultCountNewAges():
    return u'''EXISTS(SELECT A.id
    FROM Action AS A
    INNER JOIN ActionType AS AT ON AT.id=A.actionType_id
    INNER JOIN Event AS E ON A.event_id=E.id
    INNER JOIN Client AS C ON E.client_id=C.id
    WHERE A.deleted = 0 AND Action.id IS NOT NULL AND A.id = Action.id
    AND ((A.begDate<'2022-01-01T00:00:00' AND (age(C.birthDate, A.begDate)) >= IF(Client.sex = 2, 56, IF(Client.sex = 1, 61, 56)))
	OR ((A.begDate between '2022-01-01T00:00:00' AND '2023-12-31T23:59:59') AND (age(C.birthDate, A.begDate)) >= IF(Client.sex = 2, 57, IF(Client.sex = 1, 62, 57)))
	OR (A.begDate >='2024-01-01T00:00:00' AND (age(C.birthDate, A.begDate)) >= IF(Client.sex = 2, 58, IF(Client.sex = 1, 63, 58)))))'''


def getAgeCount(age=60):
    return u'''EXISTS(SELECT A.id
    FROM Action AS A
    INNER JOIN ActionType AS AT ON AT.id=A.actionType_id
    INNER JOIN Event AS E ON A.event_id=E.id
    INNER JOIN Client AS C ON E.client_id=C.id
    WHERE A.deleted = 0 AND Action.id IS NOT NULL AND A.id = Action.id
    AND (age(C.birthDate, A.begDate)) >= %s)'''%age


def getOtkaz():
    return u'''EXISTS(SELECT APS.value
                        FROM Action AS A
                        INNER JOIN ActionType AS AT ON AT.id = A.actionType_id
                        INNER JOIN ActionPropertyType AS APT ON APT.actionType_id = AT.id
                        INNER JOIN ActionProperty AS AP ON AP.type_id = APT.id
                        INNER JOIN ActionProperty_String AS APS ON APS.id = AP.id
                        WHERE A.actionType_id IN (131) AND  A.event_id = Event.id AND A.deleted=0
                        AND AP.deleted=0
                        AND APT.deleted=0
                        AND AP.action_id = A.id
                        AND APT.name LIKE 'Причина отказа от госпитализации')'''

def getChildrenCount():
    return'''EXISTS(SELECT A.id
    FROM Action AS A
    INNER JOIN ActionType AS AT ON AT.id=A.actionType_id
    INNER JOIN Event AS E ON A.event_id=E.id
    INNER JOIN Client AS C ON E.client_id=C.id
    WHERE A.deleted = 0 AND Action.id IS NOT NULL AND A.id = Action.id
    AND (age(C.birthDate, A.begDate)) <= 17)'''


def getNoDeathAdultCount(femaleAge=55, maleAge=60):
    return u'''EXISTS(SELECT A.id
    FROM Action AS A
    INNER JOIN ActionType AS AT ON AT.id=A.actionType_id
    INNER JOIN Event AS E ON A.event_id=E.id
    INNER JOIN Client AS C ON E.client_id=C.id
    WHERE A.deleted = 0 AND Action.id IS NOT NULL AND A.id = Action.id
    AND NOT EXISTS(SELECT APS.id
    FROM ActionProperty AS AP
    INNER JOIN ActionPropertyType AS APT ON AP.type_id=APT.id
    INNER JOIN ActionProperty_String AS APS ON APS.id=AP.id
    WHERE AP.action_id=Action.id AND APT.actionType_id=Action.actionType_id
    AND  Action.id IS NOT NULL
    AND APT.deleted=0 AND AP.deleted=0 AND APT.name = '%s' AND (APS.value %s OR APS.value %s)
    )
    AND (age(C.birthDate, A.begDate)) >= IF(Client.sex = 2, %d, IF(Client.sex = 1, %d, %d)))'''%\
    (u'Исход госпитализации', updateLIKE(u'умер%%'), updateLIKE(u'смерть%%'), femaleAge, maleAge, femaleAge)


def getNoDeathAdultCountNewAges():
    return u'''EXISTS(SELECT A.id
    FROM Action AS A
    INNER JOIN ActionType AS AT ON AT.id=A.actionType_id
    INNER JOIN Event AS E ON A.event_id=E.id
    INNER JOIN Client AS C ON E.client_id=C.id
    WHERE A.deleted = 0 AND Action.id IS NOT NULL AND A.id = Action.id
    AND NOT EXISTS(SELECT APS.id
    FROM ActionProperty AS AP
    INNER JOIN ActionPropertyType AS APT ON AP.type_id=APT.id
    INNER JOIN ActionProperty_String AS APS ON APS.id=AP.id
    WHERE AP.action_id=Action.id AND APT.actionType_id=Action.actionType_id
    AND  Action.id IS NOT NULL
    AND APT.deleted=0 AND AP.deleted=0 AND APT.name = '%s' AND (APS.value %s OR APS.value %s))
    AND ((A.begDate<'2022-01-01T00:00:00' AND (age(C.birthDate, A.begDate)) >= IF(Client.sex = 2, 56, IF(Client.sex = 1, 61, 56)))
	OR ((A.begDate between '2022-01-01T00:00:00' AND '2023-12-31T23:59:59') AND (age(C.birthDate, A.begDate)) >= IF(Client.sex = 2, 57, IF(Client.sex = 1, 62, 57)))
	OR (A.begDate >='2024-01-01T00:00:00' AND (age(C.birthDate, A.begDate)) >= IF(Client.sex = 2, 58, IF(Client.sex = 1, 63, 58)))))'''%\
    (u'Исход госпитализации', updateLIKE(u'умер%%'), updateLIKE(u'смерть%%'))


def getNoDeathChildrenCount():
    return'''EXISTS(SELECT A.id
    FROM Action AS A
    INNER JOIN ActionType AS AT ON AT.id=A.actionType_id
    INNER JOIN Event AS E ON A.event_id=E.id
    INNER JOIN Client AS C ON E.client_id=C.id
    WHERE A.deleted = 0 AND Action.id IS NOT NULL AND A.id = Action.id
    AND NOT EXISTS(SELECT APS.id
    FROM ActionProperty AS AP
    INNER JOIN ActionPropertyType AS APT ON AP.type_id=APT.id
    INNER JOIN ActionProperty_String AS APS ON APS.id=AP.id
    WHERE AP.action_id=Action.id AND APT.actionType_id=Action.actionType_id
    AND  Action.id IS NOT NULL
    AND APT.deleted=0 AND AP.deleted=0 AND APT.name = '%s' AND (APS.value %s OR APS.value %s)
    )
    AND (age(C.birthDate, A.begDate)) <= 17)'''%(u'Исход госпитализации', updateLIKE(u'умер%%'), updateLIKE(u'смерть%%'))


def dateRangeAsStr(title, begDate, endDate):
    result = ''
    if begDate:
        result += u' с '+forceString(begDate)
    if endDate:
        result += u' по '+forceString(endDate)
    if result:
        result = title + result
    return result


def getOrstructureHasHospitalBeds(idlist = []):
    db = QtGui.qApp.db
    table = db.table('OrgStructure')
    cond = [table['deleted'].eq(0),
            table['hasHospitalBeds'].ne(0)
            ]
    if idlist:
        cond.append(table['id'].inlist(idlist))
    return db.getIdList(table, 'id', cond)


def getTheseAndChildrens(idlist):
    db = QtGui.qApp.db
    table = db.table('OrgStructure')
    result = []
    childrenIdList = db.getIdList(table, 'id', [table['parent_id'].inlist(idlist), table['deleted'].eq(0), table['hasHospitalBeds'].ne(0)])
    if childrenIdList:
        result = getTheseAndChildrens(childrenIdList)
    result += idlist
    return result


def isActionToServiceTypeForEvent(serviceType):
    return u'''EXISTS(SELECT A.id
                      FROM Action AS A
                      INNER JOIN ActionType AS AT ON AT.id = A.actionType_id
                      WHERE A.event_id = Event.id AND A.deleted = 0
                      AND AT.serviceType = %d AND AT.deleted = 0
                      AND A.endDate IS NULL) AS isActionToServiceType'''%(serviceType)


def getDataOrgStructureNameMoving(nameProperty, actionDate, clientId, flatCode, alias = 'nameOrgStructure'):
    actionTypeIdList = getActionTypeIdListByFlatCode(flatCode)
    if actionTypeIdList and actionDate and clientId:
        db = QtGui.qApp.db
        return '''SELECT OS.name  AS %s
        FROM Action
        INNER JOIN Event ON (Event.id = Action.event_id AND Event.client_id = %s)
        INNER JOIN ActionPropertyType AS APT ON APT.actionType_id=Action.actionType_id
        INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id
        INNER JOIN ActionProperty_OrgStructure AS APOS ON APOS.id=AP.id
        INNER JOIN OrgStructure AS OS ON OS.id=APOS.value
        WHERE Action.actionType_id IN (%s)
        AND DATE(Action.begDate) <= DATE(%s) AND (DATE(Action.endDate) IS NULL OR DATE(Action.endDate) >= DATE(%s))
        AND AP.action_id=Action.id AND Action.deleted = 0 AND Event.deleted = 0
        AND APT.deleted=0 AND APT.name %s
        AND OS.deleted=0
        ORDER BY Action.begDate DESC
        LIMIT 1'''%(alias, clientId, ','.join(forceString(actionTypeId) for actionTypeId in actionTypeIdList if actionTypeId), db.formatDate(actionDate), db.formatDate(actionDate), updateLIKE(nameProperty))
    return u'NOT EXISTS(1)'


def getJobTicketPropertyAction():
    return '''(SELECT APJT.value
    FROM ActionPropertyType AS APT
    INNER JOIN ActionProperty AS AP ON AP.type_id = APT.id
    INNER JOIN ActionProperty_Job_Ticket AS APJT ON APJT.id = AP.id
    WHERE APT.actionType_id = Action.actionType_id
    AND APT.deleted=0 AND APT.typeName = 'JobTicket'
    AND AP.action_id = Action.id AND AP.deleted = 0)'''


def getActionQueueClientPolicyForDate():
    return u'''(IF(
(SELECT IF(rbFinance.code = 2, 1, IF(rbFinance.code = 3, 0, NULL))
    FROM  ActionType AS AT
        INNER JOIN Action AS A ON AT.id=A.actionType_id
        INNER JOIN ActionPropertyType AS APT ON APT.actionType_id=AT.id
        LEFT JOIN ActionProperty AS AP ON AP.type_id=APT.id AND AP.action_id = A.id
        LEFT JOIN ActionProperty_rbFinance ON ActionProperty_rbFinance.id=AP.id
        LEFT JOIN rbFinance ON rbFinance.id=ActionProperty_rbFinance.value
    WHERE  A.deleted=0 AND AT.deleted=0 AND APT.deleted=0 AND A.id = Action.id
    AND APT.name = 'источник финансирования') IS NOT NULL,
getClientPolicyEndDateForDate(Client.id,
(SELECT IF(rbFinance.code = 2, 1, IF(rbFinance.code = 3, 0, NULL))
    FROM  ActionType AS AT
        INNER JOIN Action AS A ON AT.id=A.actionType_id
        INNER JOIN ActionPropertyType AS APT ON APT.actionType_id=AT.id
        LEFT JOIN ActionProperty AS AP ON AP.type_id=APT.id AND AP.action_id = A.id
        LEFT JOIN ActionProperty_rbFinance ON ActionProperty_rbFinance.id=AP.id
        LEFT JOIN rbFinance ON rbFinance.id=ActionProperty_rbFinance.value
    WHERE  A.deleted=0 AND AT.deleted=0 AND APT.deleted=0 AND A.id = Action.id
    AND APT.name = 'источник финансирования'),
CURDATE()),
NULL)) AS policyEndDate'''


def getClientPolicyForDate():
    return u'''(IF(IF(Action.finance_id IS NOT NULL AND Action.deleted=0,
(IF(rbFinance.code = 2, 1, IF(rbFinance.code = 3, 0, NULL))),
IF(Contract.id IS NOT NULL AND Contract.deleted=0,
(IF(rbFinanceByContract.code = 2, 1, IF(rbFinanceByContract.code = 3, 0, NULL))), NULL)) IS NOT NULL,
getClientPolicyEndDateForDate(Client.id, IF(Action.finance_id IS NOT NULL AND Action.deleted=0,
(IF(rbFinance.code = 2, 1, IF(rbFinance.code = 3, 0, NULL))),
IF(Contract.id IS NOT NULL AND Contract.deleted=0,
(IF(rbFinanceByContract.code = 2, 1, IF(rbFinanceByContract.code = 3, 0, NULL))), NULL)),
IF(Action.endDate IS NOT NULL, DATE(Action.endDate), CURDATE())),
NULL
)) AS policyEndDate'''


def getActionClientPolicyForDate():
    return u'''(IF(IF(Action.id IS NOT NULL AND Action.deleted=0,
IF(rbFinance.code = 2, 1, IF(rbFinance.code = 3, 0, NULL)), NULL) IS NOT NULL,
getClientPolicyEndDateForDate(Client.id,
IF(Action.id IS NOT NULL AND Action.deleted=0,
IF(rbFinance.code = 2, 1, IF(rbFinance.code = 3, 0, NULL)), NULL),
IF(Action.endDate IS NOT NULL, DATE(Action.endDate), CURDATE())),
NULL)) AS policyEndDate'''


def getContractClientPolicyForDate():
    return u'''(IF(
IF(Contract.id IS NOT NULL AND Contract.deleted=0,
IF(rbFinance.code = 2, 1, IF(rbFinance.code = 3, 0, NULL)), NULL) IS NOT NULL,
getClientPolicyEndDateForDate(Client.id,
IF(Contract.id IS NOT NULL AND Contract.deleted=0,
IF(rbFinance.code = 2, 1, IF(rbFinance.code = 3, 0, NULL)), NULL),
IF(Action.endDate IS NOT NULL, DATE(Action.endDate), CURDATE())),
NULL)) AS policyEndDate'''


def getTransferProperty(nameProperty, dayStat=False):
    return u'''EXISTS(SELECT APOS2.value
    FROM ActionPropertyType AS APT2
    INNER JOIN ActionProperty AS AP2 ON AP2.type_id=APT2.id
    INNER JOIN ActionProperty_OrgStructure AS APOS2 ON APOS2.id=AP2.id
    INNER JOIN OrgStructure AS OS2 ON OS2.id=APOS2.value
    WHERE APT2.actionType_id=A.actionType_id AND AP2.action_id=A.id AND APT2.deleted=0
    AND APT2.name %s %s AND OS2.deleted=0)'''%(updateLIKE(nameProperty),
    u'AND OS2.type = 0' if dayStat else u'AND OS2.type != 0')


def getTransferPropertyIn(nameProperty):
    return u'''EXISTS(SELECT APOS.value
    FROM ActionPropertyType AS APT
    INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id
    INNER JOIN ActionProperty_OrgStructure AS APOS ON APOS.id=AP.id
    INNER JOIN OrgStructure AS OS ON OS.id=APOS.value
    WHERE APT.actionType_id=Action.actionType_id AND AP.action_id=Action.id
    AND APT.deleted=0 AND APT.name %(nameProperty)s
    AND OS.deleted=0)'''% dict(nameProperty = updateLIKE(nameProperty))


#nameProperty = u'Отделение пребывания'
# в другие отделения: inMovingTransfer u'Переведен в отделение' transferType=0
# из других отделений: fromMovingTransfer u'Переведен из отделения' transferType=1
def getValuePropertyAPOS(nameProperty):
    return u'''(SELECT APOS23.value
    FROM ActionPropertyType AS APT23
    INNER JOIN ActionProperty AS AP23 ON AP23.type_id=APT23.id
    INNER JOIN ActionProperty_OrgStructure AS APOS23 ON APOS23.id=AP23.id
    INNER JOIN OrgStructure AS OS23 ON OS23.id=APOS23.value
    WHERE APT23.actionType_id=Action.actionType_id AND AP23.action_id=Action.id
    AND APT23.deleted=0 AND APT23.name %(nameProperty)s
    AND OS23.deleted=0)'''%(dict(nameProperty = updateLIKE(nameProperty)))


def isEXISTSTransfer(namePropertyT, namePropertyP=u'Отделение пребывания', transferType=0):
    return u'''EXISTS(SELECT APOS2.value
    FROM ActionPropertyType AS APT2
    INNER JOIN ActionProperty AS AP2 ON AP2.type_id=APT2.id
    INNER JOIN ActionProperty_OrgStructure AS APOS2 ON APOS2.id=AP2.id
    INNER JOIN OrgStructure AS OS2 ON OS2.id=APOS2.value
    WHERE APT2.actionType_id=Action.actionType_id
    AND AP2.action_id=Action.id AND APT2.deleted=0 AND AP2.deleted=0
    AND APT2.name %(namePropertyT)s AND OS2.deleted=0
    AND (APOS2.value != (SELECT APOS3.value
    FROM ActionPropertyType AS APT3
    INNER JOIN ActionProperty AS AP3 ON AP3.type_id=APT3.id
    INNER JOIN ActionProperty_OrgStructure AS APOS3 ON APOS3.id=AP3.id
    INNER JOIN OrgStructure AS OS3 ON OS3.id=APOS3.value
    WHERE APT3.actionType_id=Action.actionType_id
    AND AP3.action_id=Action.id AND APT3.deleted=0 AND AP3.deleted=0
    AND APT3.name %(namePropertyP)s AND OS3.deleted=0)
    OR (SELECT OSHB22.profile_id
    FROM ActionType AS AT22
    INNER JOIN Action AS A22 ON AT22.id=A22.actionType_id
    INNER JOIN ActionPropertyType AS APT22 ON APT22.actionType_id=AT22.id
    INNER JOIN ActionProperty AS AP22 ON AP22.type_id=APT22.id
    INNER JOIN ActionProperty_HospitalBed AS APHB22 ON APHB22.id=AP22.id
    INNER JOIN OrgStructure_HospitalBed AS OSHB22 ON OSHB22.id=APHB22.value
    WHERE A22.id=Action.id
    AND A22.deleted=0
    AND APT22.actionType_id=A22.actionType_id
    AND AP22.action_id=A22.id
    AND AP22.deleted=0
    AND APT22.deleted=0
    AND APT22.typeName = 'HospitalBed'
    ) != ((SELECT OSHB3.master_id
FROM ActionType AS AT3
INNER JOIN Action AS A3 ON AT3.id=A3.actionType_id
INNER JOIN ActionPropertyType AS APT3 ON APT3.actionType_id=AT3.id
INNER JOIN ActionProperty AS AP3 ON AP3.type_id=APT3.id
INNER JOIN ActionProperty_HospitalBed AS APHB3 ON APHB3.id=AP3.id
INNER JOIN OrgStructure_HospitalBed AS OSHB3 ON OSHB3.id=APHB3.value
WHERE A3.id = %(actionDateBack)s
AND A3.deleted=0
AND APT3.actionType_id=A3.actionType_id
AND AP3.action_id=A3.id
AND AP3.deleted=0
AND APT3.deleted=0
AND APT3.typeName = 'HospitalBed'
AND EXISTS(SELECT APOS.value
FROM ActionPropertyType AS APT
INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id
INNER JOIN ActionProperty_OrgStructure AS APOS ON APOS.id=AP.id
INNER JOIN OrgStructure AS OS ON OS.id=APOS.value
WHERE APT.actionType_id=Action.actionType_id
AND AP.action_id=A3.id AND APT.deleted=0
AND APT.name %(transferProperty)s
AND OS.deleted=0)
GROUP BY A3.event_id
ORDER BY %(orderT)s DESC
)))
    )'''%(dict(namePropertyT      = updateLIKE(namePropertyT),
               namePropertyP      = updateLIKE(namePropertyP),
               actionDateBack     = u'getPrevActionId(Action.event_id, Action.id, Action.actionType_id, Action.begDate)' if transferType else u'getNextActionId(Action.event_id, Action.id, Action.actionType_id, Action.endDate)',
               transferProperty   = updateLIKE(u'Переведен в отделение' if transferType else u'Переведен из отделения'),
               orderT             = u'A3.endDate' if transferType else u'A3.begDate',
               )
         )


def getTransferPropertyInPeriod(nameProperty, begDateTime, endDateTime):
    return u'''EXISTS(SELECT APOS.value
    FROM ActionPropertyType AS APT
    INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id
    INNER JOIN ActionProperty_OrgStructure AS APOS ON APOS.id=AP.id
    INNER JOIN OrgStructure AS OS ON OS.id=APOS.value
    WHERE APT.actionType_id=Action.actionType_id AND AP.action_id=Action.id
    AND APT.deleted=0 AND APT.name %s AND OS.type != 0 AND OS.deleted=0
    AND (Action.begDate IS NULL OR (Action.begDate >= '%s'
    AND Action.begDate < '%s')))'''%(updateLIKE(nameProperty), begDateTime.toString(Qt.ISODate),
    endDateTime.toString(Qt.ISODate))


def getPropertyAPHBPNoProfile(joinType=u'INNER', nameProperty=None):
    return '''SELECT APHBP.value
FROM ActionPropertyType AS APT_Profile
%(joinType)s JOIN ActionProperty AS AP_Profile ON AP_Profile.type_id=APT_Profile.id
%(joinType)s JOIN ActionProperty_rbHospitalBedProfile AS APHBP ON APHBP.id=AP_Profile.id
%(joinType)s JOIN rbHospitalBedProfile AS RBHBP ON RBHBP.id=APHBP.value
WHERE APT_Profile.actionType_id = Action.actionType_id
AND AP_Profile.action_id = Action.id
AND AP_Profile.deleted = 0
AND APT_Profile.deleted = 0
AND APT_Profile.typeName = 'rbHospitalBedProfile'
%(propName)s
AND APHBP.value IS NULL'''%(dict(joinType = joinType, propName = (' AND APT_Profile.name %s'%(updateLIKE(nameProperty))) if nameProperty else u''))


def getDataOrgStructureStay(nameProperty, orgStructureIdList, dayStat=None):
    orgStructureList = [u'NULL']
    for orgStructureId in orgStructureIdList:
        orgStructureList.append(forceString(orgStructureId))
    return '''EXISTS(SELECT APOS2.value
    FROM ActionPropertyType AS APT2
    INNER JOIN ActionProperty AS AP2 ON AP2.type_id=APT2.id
    INNER JOIN ActionProperty_OrgStructure AS APOS2 ON APOS2.id=AP2.id
    INNER JOIN OrgStructure AS OS2 ON OS2.id=APOS2.value
    WHERE APT2.actionType_id=A.actionType_id AND AP2.action_id=A.id
    AND APT2.deleted=0 AND APT2.name %s AND OS2.deleted=0
    AND APOS2.value %s %s)'''%(updateLIKE(nameProperty),
    u' IN ('+(','.join(orgStructureList))+')',
    u'' if dayStat is None else(u' AND OS2.type = 0' if dayStat else u' AND OS2.type != 0')
    )


def getPropertyAPHBPName(profileList, noProfileBed, col='name', fieldName ='profileName'):
    return '''(SELECT RBHBP.%s
FROM ActionPropertyType AS APT_Profile
INNER JOIN ActionProperty AS AP_Profile ON AP_Profile.type_id=APT_Profile.id
INNER JOIN ActionProperty_rbHospitalBedProfile AS APHBP ON APHBP.id=AP_Profile.id
INNER JOIN rbHospitalBedProfile AS RBHBP ON RBHBP.id=APHBP.value
WHERE APT_Profile.actionType_id = Action.actionType_id
AND AP_Profile.action_id = Action.id
AND AP_Profile.deleted = 0
AND APT_Profile.deleted = 0
AND APT_Profile.typeName = 'rbHospitalBedProfile'
%s) AS %s'''%(col, (u'AND (APHBP.value IN (%s)%s)'%((','.join(forceString(profile)
                                           for profile in profileList if profile)), u' OR APHBP.value IS NULL'
                                           if noProfileBed and len(profileList) > 1 else u'')
                                           if profileList else (u'AND APHBP.value IS NOT NULL')), fieldName)


def getDataAPHBnoProperty(isPermanentBed, nameProperty, noProfileBed, profileList=[], endDate=u'', namePropertyStay=u'Отделение пребывания', orgStructureIdList=[], isMedical = None, bedsSchedule = None):
    strIsMedical = u''''''
    strIsMedicalJoin = u''''''
    strIsScheduleJoin = u''''''
    if isMedical is not None:
        strIsMedicalJoin += u''' INNER JOIN OrgStructure AS OS ON OSHB.master_id = OS.id INNER JOIN Organisation AS ORG ON OS.organisation_id = ORG.id'''
        strIsMedical += u''' AND OS.type != 0 AND ORG.isMedical = %d'''%(isMedical)
    strFilter = u''''''
    if profileList:
        if QtGui.qApp.defaultHospitalBedProfileByMoving():
            strFilter += u''' AND (''' + getPropertyAPHBP(profileList, noProfileBed) + u''')'''
        else:
            strFilter += u''' AND (OSHB.profile_id IN (%s)%s)'''%((','.join(forceString(profile) for profile in profileList if profile)), u' OR OSHB.profile_id IS NULL' if noProfileBed and len(profileList) > 1 else u'')
    elif noProfileBed:
        if QtGui.qApp.defaultHospitalBedProfileByMoving():
            strFilter += u''' AND EXISTS(''' + getPropertyAPHBPNoProfile() + u''')'''
        else:
            strFilter += u''' AND OSHB.profile_id IS NULL'''
    if bedsSchedule:
        strIsScheduleJoin += u''' INNER JOIN rbHospitalBedShedule AS HBS ON OSHB.schedule_id = HBS.id'''
    if bedsSchedule == 1:
        strFilter += u''' AND HBS.code = 1'''
    elif bedsSchedule == 2:
        strFilter += u''' AND HBS.code != 1'''
    return '''EXISTS(SELECT APHB.value
FROM ActionType AS AT
INNER JOIN Action AS A ON AT.id=A.actionType_id
INNER JOIN ActionPropertyType AS APT ON APT.actionType_id=AT.id
INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id
INNER JOIN ActionProperty_HospitalBed AS APHB ON APHB.id=AP.id
INNER JOIN OrgStructure_HospitalBed AS OSHB ON OSHB.id=APHB.value%s%s
WHERE A.event_id=Event.id%s%s AND A.deleted=0 AND APT.actionType_id=A.actionType_id
AND AP.action_id=A.id AND AP.deleted=0 AND APT.deleted=0 AND APT.typeName = 'HospitalBed'%s
AND (NOT %s)%s)'''%(strIsMedicalJoin, strIsScheduleJoin, strIsMedical, endDate, strFilter,
getTransferProperty(nameProperty),
u' AND %s'%(getDataOrgStructureStay(namePropertyStay, orgStructureIdList, dayStat=0) if orgStructureIdList else u''))


def getActionsToFlatCode(flatCode):
    actionTypeIdList = getActionTypeIdListByFlatCode(flatCode)
    if actionTypeIdList:
        return u'''EXISTS(SELECT A.id
        FROM Action AS A
        WHERE A.event_id = Event.id AND A.deleted = 0
        AND A.actionType_id IN (%s))'''%(','.join(forceString(actionTypeId) for actionTypeId in actionTypeIdList if actionTypeId))
    return u'NOT EXISTS(1)'


def getOrgStructureProperty(nameProperty, orgStructureIdList, type=u' != 0'):
    orgStructureList = [u'NULL']
    for orgStructureId in orgStructureIdList:
        orgStructureList.append(forceString(orgStructureId))
    return u'''EXISTS(SELECT APOS2.value
    FROM ActionPropertyType AS APT2
    INNER JOIN ActionProperty AS AP2 ON AP2.type_id=APT2.id
    INNER JOIN ActionProperty_OrgStructure AS APOS2 ON APOS2.id=AP2.id
    INNER JOIN OrgStructure AS OS2 ON OS2.id=APOS2.value
    WHERE APT2.actionType_id=Action.actionType_id AND AP2.action_id=Action.id
    AND APT2.name %s AND APOS2.value %s AND APT2.deleted=0
    AND OS2.type%s AND OS2.deleted=0)'''%(updateLIKE(nameProperty), u' IN ('+(','.join(orgStructureList))+')', type)

def getOrgStructurePropertyF30(nameProperty, orgStructureIdList, type=u' != 0'):
    orgStructureList = [u'NULL']
    for orgStructureId in orgStructureIdList:
        orgStructureList.append(forceString(orgStructureId))
    return u'''OrgStructure.id %s  AND OrgStructure.type%s '''%(u' IN ('+(','.join(orgStructureList))+')', type)


def getPropertyAPHBP(profileList, noProfileBed):
    return '''EXISTS(SELECT APHBP.id
FROM ActionPropertyType AS APT_Profile
INNER JOIN ActionProperty AS AP_Profile ON AP_Profile.type_id=APT_Profile.id
INNER JOIN ActionProperty_rbHospitalBedProfile AS APHBP ON APHBP.id=AP_Profile.id
INNER JOIN rbHospitalBedProfile AS RBHBP ON RBHBP.id=APHBP.value
WHERE APT_Profile.actionType_id = Action.actionType_id
AND AP_Profile.action_id = Action.id
AND AP_Profile.deleted = 0
AND APT_Profile.deleted = 0
AND APT_Profile.typeName = 'rbHospitalBedProfile'
%s)'''%((u'AND (APHBP.value IN (%s)%s)'%((','.join(forceString(profile)
                                           for profile in profileList if profile)), u' OR APHBP.value IS NULL'
                                           if noProfileBed and len(profileList) > 1 else u'')
                                           if profileList else (u'AND APHBP.value IS NULL')))


def getPropertyHospitalBedProfile(nameProperty, profile):
    return '''EXISTS(SELECT APHBP.value
FROM ActionPropertyType AS APT_Profile
INNER JOIN ActionProperty AS AP_Profile ON AP_Profile.type_id=APT_Profile.id
INNER JOIN ActionProperty_rbHospitalBedProfile AS APHBP ON APHBP.id=AP_Profile.id
INNER JOIN rbHospitalBedProfile AS RBHBP ON RBHBP.id=APHBP.value
WHERE APT_Profile.actionType_id = Action.actionType_id
AND AP_Profile.action_id = Action.id
AND AP_Profile.deleted = 0
AND APT_Profile.deleted = 0
AND APT_Profile.name %s
AND APT_Profile.typeName = 'rbHospitalBedProfile'
AND APHBP.value = %s)'''%(updateLIKE(nameProperty), str(profile))


def getStringProperty(nameProperty, value):
    return u'''EXISTS(SELECT APS.id
    FROM ActionProperty AS AP
    INNER JOIN ActionPropertyType AS APT ON AP.type_id=APT.id
    INNER JOIN ActionProperty_String AS APS ON APS.id=AP.id
    WHERE AP.action_id=Action.id AND APT.actionType_id=Action.actionType_id
    AND  Action.id IS NOT NULL
    AND APT.deleted=0 AND AP.deleted=0 AND APT.name %s AND %s
    )'''%(updateLIKE(nameProperty), value)


def getStringPropertyForTableName(tableName, nameProperty, value):
    return u'''EXISTS(SELECT APS.id
    FROM ActionProperty AS AP
    INNER JOIN ActionPropertyType AS APT ON AP.type_id=APT.id
    INNER JOIN ActionProperty_String AS APS ON APS.id=AP.id
    WHERE AP.action_id=%s.id AND APT.actionType_id=%s.actionType_id
    AND  %s.id IS NOT NULL
    AND APT.deleted=0 AND AP.deleted=0 AND APT.name %s AND %s
    )'''%(tableName, tableName, tableName, updateLIKE(nameProperty), value)


def getStringPropertyActionType(nameProperty, actionTypeIdList, value):
    return u'''EXISTS(SELECT APS.id
    FROM ActionPropertyType AS APT
    INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id
    INNER JOIN ActionProperty_String AS APS ON APS.id=AP.id
    WHERE Action.actionType_id IN (%s) AND Action.id IS NOT NULL
    AND APT.actionType_id=Action.actionType_id AND AP.action_id=Action.id
    AND APT.deleted=0 AND APT.name %s AND %s)'''%(','.join(str(actionTypeId) for actionTypeId in actionTypeIdList),
    updateLIKE(nameProperty), value)


def getStringPropertyEvent(actionTypeIdList, nameProperty):
    return '''(SELECT APS.value
    FROM Action AS A
    INNER JOIN ActionPropertyType AS APT ON APT.actionType_id=A.actionType_id
    INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id
    INNER JOIN ActionProperty_String AS APS ON APS.id=AP.id
    WHERE A.`event_id` = getFirstEventId(Event.id) AND A.`deleted`=0  AND AP.deleted=0
    AND A.actionType_id IN (%s) AND A.begDate IS NOT NULL AND AP.action_id=A.id
    AND APT.deleted=0 AND APT.name %s)'''%(','.join(str(actionTypeId) for actionTypeId in actionTypeIdList), updateLIKE(nameProperty))


def getStringPropertyLastEvent(actionTypeIdList, nameProperty):
    return '''(SELECT APS.value
    FROM Action AS A
    INNER JOIN ActionPropertyType AS APT ON APT.actionType_id=A.actionType_id
    INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id
    INNER JOIN ActionProperty_String AS APS ON APS.id=AP.id
    WHERE A.`event_id` = getLastEventId(Event.id) AND A.`deleted`=0  AND AP.deleted=0
    AND A.actionType_id IN (%s) AND A.begDate IS NOT NULL AND AP.action_id=A.id
    AND APT.deleted=0 AND APT.name %s)'''%(','.join(str(actionTypeId) for actionTypeId in actionTypeIdList), updateLIKE(nameProperty))


def getStringPropertyEventYes(actionTypeIdList, nameProperty):
    return '''EXISTS(SELECT APS.id
    FROM Action AS A
    INNER JOIN ActionPropertyType AS APT ON APT.actionType_id=A.actionType_id
    INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id
    INNER JOIN ActionProperty_String AS APS ON APS.id=AP.id
    WHERE A.`event_id` = getFirstEventId(Event.id) AND A.`deleted`=0  AND AP.deleted=0
    AND A.actionType_id IN (%s) AND A.begDate IS NOT NULL AND AP.action_id=A.id
    AND APT.deleted=0 AND APT.name %s AND APS.value = '%s')'''%(','.join(str(actionTypeId) for actionTypeId in actionTypeIdList), updateLIKE(nameProperty), u'да')


def getPropertyAPHBPForActionType(actionTypeIdList, profileList, noProfileBed):
    return '''EXISTS(SELECT APHBP.id
FROM Action AS A_Profile
INNER JOIN ActionPropertyType AS APT_Profile ON APT_Profile.actionType_id=A_Profile.actionType_id
INNER JOIN ActionProperty AS AP_Profile ON AP_Profile.type_id=APT_Profile.id
INNER JOIN ActionProperty_rbHospitalBedProfile AS APHBP ON APHBP.id=AP_Profile.id
INNER JOIN rbHospitalBedProfile AS RBHBP ON RBHBP.id=APHBP.value
WHERE A_Profile.event_id = getLastEventId(Event.id)
AND A_Profile.actionType_id IN (%s)
AND A_Profile.deleted=0
AND AP_Profile.action_id = A_Profile.id
AND AP_Profile.deleted = 0
AND APT_Profile.deleted = 0
AND APT_Profile.typeName = 'rbHospitalBedProfile'
%s)'''%(','.join(str(actionTypeId) for actionTypeId in actionTypeIdList),
        (u'AND (APHBP.value IN (%s)%s)'%((','.join(forceString(profile) for profile in profileList if profile)),
                                         u' OR APHBP.value IS NULL' if noProfileBed and len(profileList) > 1 else u'')
                                         if profileList else (u'AND APHBP.value IS NULL')))


def getStringPropertyCurrEvent(actionTypeIdList, nameProperty):
    return '''(SELECT GROUP_CONCAT(DISTINCT(TRIM(APS.value)))
    FROM Action AS A
    INNER JOIN ActionPropertyType AS APT ON APT.actionType_id=A.actionType_id
    INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id
    INNER JOIN ActionProperty_String AS APS ON APS.id=AP.id
    WHERE A.event_id = Event.id AND A.`deleted`=0  AND AP.deleted=0
    AND A.actionType_id IN (%s) AND A.begDate IS NOT NULL AND AP.action_id=A.id
    AND APT.deleted=0 AND APT.name %s)'''%(','.join(str(actionTypeId) for actionTypeId in actionTypeIdList), updateLIKE(nameProperty))


def getExistsStringPropertyCurrEvent(actionTypeIdList, nameProperty, value):
    return '''EXISTS(SELECT APS.id
    FROM Action AS A
    INNER JOIN ActionPropertyType AS APT ON APT.actionType_id=A.actionType_id
    INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id
    INNER JOIN ActionProperty_String AS APS ON APS.id=AP.id
    WHERE A.event_id = Event.id AND A.deleted=0  AND AP.deleted=0
    AND A.actionType_id IN (%s) AND A.begDate IS NOT NULL AND AP.action_id=A.id
    AND APT.deleted=0 AND APT.name %s AND APS.value %s)'''%(','.join(str(actionTypeId) for actionTypeId in actionTypeIdList), updateLIKE(nameProperty), updateLIKE(value))


def getStringPropertyValue(nameProperty):
    return u'''(SELECT APS.value
    FROM ActionPropertyType AS APT
    INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id
    INNER JOIN ActionProperty_String AS APS ON APS.id=AP.id
    WHERE  Action.id IS NOT NULL AND APT.actionType_id=Action.actionType_id
    AND AP.action_id=Action.id AND AP.deleted=0
    AND APT.deleted=0 AND APT.name %s LIMIT 1)'''%(updateLIKE(nameProperty))


def getStringPropertyPrevEvent(actionTypeIdList, nameProperty, value):
    return '''EXISTS(SELECT APS.id
    FROM Action AS A
    INNER JOIN ActionPropertyType AS APT ON APT.actionType_id=A.actionType_id
    INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id
    INNER JOIN ActionProperty_String AS APS ON APS.id=AP.id
    WHERE A.`event_id` = getFirstEventId(Event.id) AND A.`deleted`=0  AND AP.deleted=0
    AND A.actionType_id IN (%s) AND A.begDate IS NOT NULL AND AP.action_id=A.id
    AND APT.deleted=0 AND APT.name %s
    AND APS.value %s)'''%(','.join(str(actionTypeId) for actionTypeId in actionTypeIdList),
    updateLIKE(nameProperty), updateLIKE(value))


def getStringPropertyLastEventValue(actionTypeIdList, nameProperty, value):
    return '''EXISTS(SELECT APS.id
    FROM Action AS A
    INNER JOIN ActionPropertyType AS APT ON APT.actionType_id=A.actionType_id
    INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id
    INNER JOIN ActionProperty_String AS APS ON APS.id=AP.id
    WHERE A.event_id = getLastEventId(Event.id) AND A.deleted=0  AND AP.deleted=0
    AND A.actionType_id IN (%s) AND A.begDate IS NOT NULL AND AP.action_id=A.id
    AND APT.deleted=0 AND APT.name %s
    AND %s)'''%(','.join(str(actionTypeId) for actionTypeId in actionTypeIdList),
    updateLIKE(nameProperty), value)


def getActionTypeStringPropertyValue(nameProperty, flatCode, value):
    actionTypeIdList = getActionTypeIdListByFlatCode(flatCode)
    if actionTypeIdList:
        return u'''EXISTS(SELECT APS.id
        FROM Action AS A
        INNER JOIN ActionProperty AS AP ON AP.action_id=A.id
        INNER JOIN ActionPropertyType AS APT ON AP.type_id=APT.id
        INNER JOIN ActionProperty_String AS APS ON APS.id=AP.id
        WHERE A.event_id = Event.id AND A.deleted = 0 AND APT.actionType_id IN (%s)
        AND APT.actionType_id = A.actionType_id
        AND APT.deleted=0 AND APT.name %s
        AND APS.value %s)'''%((','.join(forceString(actionTypeId) for actionTypeId in actionTypeIdList if actionTypeId)),
        updateLIKE(nameProperty), updateLIKE(value))
    return u'NOT EXISTS(1)'


def getNoPropertyAPHBP():
    return '''NOT EXISTS(SELECT APHBP.id
FROM ActionPropertyType AS APT_Profile
INNER JOIN ActionProperty AS AP_Profile ON AP_Profile.type_id=APT_Profile.id
INNER JOIN ActionProperty_rbHospitalBedProfile AS APHBP ON APHBP.id=AP_Profile.id
INNER JOIN rbHospitalBedProfile AS RBHBP ON RBHBP.id=APHBP.value
WHERE APT_Profile.actionType_id = Action.actionType_id
AND AP_Profile.action_id = Action.id
AND AP_Profile.deleted = 0
AND APT_Profile.deleted = 0
AND APT_Profile.typeName = 'rbHospitalBedProfile')'''


def getKladrClientRural():
    return u'''EXISTS(SELECT kladr.KLADR.OCATD
    FROM ClientAddress
    INNER JOIN Address ON ClientAddress.address_id = Address.id
    INNER JOIN AddressHouse ON Address.house_id = AddressHouse.id
    INNER JOIN kladr.KLADR ON kladr.KLADR.CODE = AddressHouse.KLADRCode
    WHERE Client.id IS NOT NULL AND ClientAddress.client_id = Client.id
    AND (((SUBSTRING(kladr.KLADR.OCATD,3,1) IN (1, 2, 4))
    AND SUBSTRING(kladr.KLADR.OCATD,6,1) = 8) OR ((SUBSTRING(kladr.KLADR.OCATD,3,1) NOT IN (1, 2, 4))
    AND SUBSTRING(kladr.KLADR.OCATD,6,1) = 9)))'''


def getKladrClientDefaultCity(defaultKLADRCode):
    return u'''EXISTS(SELECT ClientAddress.id
    FROM ClientAddress
    INNER JOIN Address ON ClientAddress.address_id = Address.id
    INNER JOIN AddressHouse ON Address.house_id = AddressHouse.id
    INNER JOIN kladr.KLADR ON kladr.KLADR.CODE = AddressHouse.KLADRCode
    WHERE Client.id IS NOT NULL AND ClientAddress.client_id = Client.id AND ClientAddress.type=0
    AND ClientAddress.deleted = 0  AND ClientAddress.id IS NOT NULL
    AND ClientAddress.id = (SELECT MAX(CA.id) FROM ClientAddress AS CA WHERE CA.deleted = 0
    AND CA.client_id = Client.id AND CA.type=0 LIMIT 1)
    AND AddressHouse.KLADRCode %s
    AND NOT (((SUBSTRING(kladr.KLADR.OCATD,3,1) IN (1, 2, 4))
    AND SUBSTRING(kladr.KLADR.OCATD,6,1) = 8) OR ((SUBSTRING(kladr.KLADR.OCATD,3,1) NOT IN (1, 2, 4))
    AND SUBSTRING(kladr.KLADR.OCATD,6,1) = 9))) '''''%(updateLIKE(defaultKLADRCode))


def getKladrClientAddressRural():
    return u'''EXISTS(SELECT ClientAddress.id
    FROM ClientAddress
    INNER JOIN Address ON ClientAddress.address_id = Address.id
    INNER JOIN AddressHouse ON Address.house_id = AddressHouse.id
    INNER JOIN kladr.KLADR ON kladr.KLADR.CODE = AddressHouse.KLADRCode
    WHERE Client.id IS NOT NULL AND ClientAddress.client_id = Client.id AND ClientAddress.type=0
    AND ClientAddress.deleted = 0  AND ClientAddress.id IS NOT NULL
    AND ClientAddress.id = (SELECT MAX(CA.id) FROM ClientAddress AS CA WHERE CA.deleted = 0
    AND CA.client_id = Client.id AND CA.type=0 LIMIT 1)
    AND (((SUBSTRING(kladr.KLADR.OCATD,3,1) IN (1, 2, 4))
    AND SUBSTRING(kladr.KLADR.OCATD,6,1) = 8) OR ((SUBSTRING(kladr.KLADR.OCATD,3,1) NOT IN (1, 2, 4))
    AND SUBSTRING(kladr.KLADR.OCATD,6,1) = 9))) '''''


def getDataOrgStructureName(nameProperty, alias = 'nameOrgStructure'):
    return '''(SELECT OS.name
    FROM ActionPropertyType AS APT
    INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id
    INNER JOIN ActionProperty_OrgStructure AS APOS ON APOS.id=AP.id
    INNER JOIN OrgStructure AS OS ON OS.id=APOS.value
    WHERE APT.actionType_id=Action.actionType_id AND AP.action_id=Action.id
    AND APT.deleted=0 AND AP.deleted = 0 AND APT.name %s
    AND OS.deleted=0 LIMIT 1) AS %s'''%(updateLIKE(nameProperty), alias)


def getDataOrgStructureCode(nameProperty, alias = 'nameOrgStructure'):
    return '''(SELECT OS.code
    FROM ActionPropertyType AS APT
    INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id
    INNER JOIN ActionProperty_OrgStructure AS APOS ON APOS.id=AP.id
    INNER JOIN OrgStructure AS OS ON OS.id=APOS.value
    WHERE APT.actionType_id=Action.actionType_id AND AP.action_id=Action.id
    AND APT.deleted=0 AND AP.deleted = 0 AND APT.name %s
    AND OS.deleted=0) AS %s'''%(updateLIKE(nameProperty), alias)


def getTransferOrganisaionName(nameProperty, alias = 'nameOrganisaion'):
    return '''(SELECT APS_Organisation.value
    FROM ActionPropertyType AS APT_Organisation
    INNER JOIN ActionProperty AS AP_Organisation ON AP_Organisation.type_id = APT_Organisation.id
    INNER JOIN ActionProperty_String AS APS_Organisation ON APS_Organisation.id = AP_Organisation.id
    WHERE APT_Organisation.actionType_id = Action.actionType_id
    AND AP_Organisation.action_id = Action.id
    AND AP_Organisation.deleted = 0
    AND APT_Organisation.name %s
    AND APT_Organisation.deleted = 0) AS %s'''%(updateLIKE(nameProperty), alias)


def getDataOrgStructure(nameProperty, orgStructureIdList, stationaryOnly = True):
    orgStructureList = [u'NULL']
    for orgStructureId in orgStructureIdList:
        orgStructureList.append(forceString(orgStructureId))
    return '''EXISTS(SELECT APOS2.value
    FROM ActionPropertyType AS APT2
    INNER JOIN ActionProperty AS AP2 ON AP2.type_id=APT2.id
    INNER JOIN ActionProperty_OrgStructure AS APOS2 ON APOS2.id=AP2.id
    INNER JOIN OrgStructure AS OS2 ON OS2.id=APOS2.value
    WHERE APT2.actionType_id=Action.actionType_id AND AP2.action_id=Action.id
    AND APT2.deleted=0 AND APT2.name %s %s AND OS2.deleted=0 AND AP2.deleted = 0
    AND APOS2.value %s)'''%(updateLIKE(nameProperty), u'AND OS2.type != 0' if stationaryOnly else u'',u' IN ('+(','.join(orgStructureList))+')')


def getOrgStructureProperty_HBDS(nameProperty, orgStructureIdList, type = 0):
    orgStructureList = [u'NULL']
    if type == 1:
        isType = u' AND OS2.type != 0'
    elif type == 2:
        isType = u' AND (OS2.type = 0 AND (SELECT getOrgStructureIsType(OS2.id)) = 1)'
    else:
        isType = u' AND (OS2.type != 0 OR (OS2.type = 0 AND (SELECT getOrgStructureIsType(OS2.id)) = 1))'
    for orgStructureId in orgStructureIdList:
        orgStructureList.append(forceString(orgStructureId))
    return u'''EXISTS(SELECT APOS2.value
    FROM ActionPropertyType AS APT2
    INNER JOIN ActionProperty AS AP2 ON AP2.type_id=APT2.id
    INNER JOIN ActionProperty_OrgStructure AS APOS2 ON APOS2.id=AP2.id
    INNER JOIN OrgStructure AS OS2 ON OS2.id=APOS2.value
    WHERE APT2.actionType_id=Action.actionType_id AND AP2.action_id=Action.id
    AND APT2.name %s AND APOS2.value %s AND APT2.deleted=0
    %s AND OS2.deleted=0)'''%(updateLIKE(nameProperty),
                              u' IN ('+(','.join(orgStructureList))+')',
                              isType)


def getDataOrgStructure_HBDS(nameProperty, orgStructureIdList, type = 0):
    orgStructureList = [u'NULL']
    if type == 1:
        isType = u' AND OS2.type != 0'
    elif type == 2:
        isType = u' AND (OS2.type = 0 AND (SELECT getOrgStructureIsType(OS2.id)) = 1)'
    else:
        isType = u' AND (OS2.type != 0 OR (OS2.type = 0 AND (SELECT getOrgStructureIsType(OS2.id)) = 1))'
    for orgStructureId in orgStructureIdList:
        orgStructureList.append(forceString(orgStructureId))
    return '''EXISTS(SELECT APOS2.value
    FROM ActionPropertyType AS APT2
    INNER JOIN ActionProperty AS AP2 ON AP2.type_id=APT2.id
    INNER JOIN ActionProperty_OrgStructure AS APOS2 ON APOS2.id=AP2.id
    INNER JOIN OrgStructure AS OS2 ON OS2.id=APOS2.value
    WHERE APT2.actionType_id=Action.actionType_id AND AP2.action_id=Action.id
    AND APT2.deleted=0 AND APT2.name %s %s AND OS2.deleted=0
    AND APOS2.value %s)'''%(updateLIKE(nameProperty),
                            isType,
                            u' IN ('+(','.join(orgStructureList))+')')


def getDataOrgStructureAT(flatCode, nameProperty, orgStructureIdList):
    actionTypeList = getActionTypeIdListByFlatCode(flatCode)
    actionTypeIdList = (','.join(str(actionTypeId) for actionTypeId in actionTypeList if actionTypeId))
    if actionTypeIdList:
        orgStructureList = [u'NULL']
        for orgStructureId in orgStructureIdList:
            orgStructureList.append(forceString(orgStructureId))
        return '''EXISTS(SELECT APOS2.value
        FROM Action AS A2
        INNER JOIN ActionPropertyType AS APT2 ON APT2.actionType_id=A2.actionType_id
        INNER JOIN ActionProperty AS AP2 ON AP2.type_id=APT2.id
        INNER JOIN ActionProperty_OrgStructure AS APOS2 ON APOS2.id=AP2.id
        INNER JOIN OrgStructure AS OS2 ON OS2.id=APOS2.value
        WHERE APT2.actionType_id IN (%s) AND A2.event_id = Event.id AND A2.deleted = 0
        AND AP2.action_id=A2.id AND APT2.deleted=0 AND APT2.name %s
        AND OS2.type != 0 AND OS2.deleted=0 AND APOS2.value %s)'''%(actionTypeIdList, updateLIKE(nameProperty), u' IN ('+(','.join(orgStructureList))+')')
    else:
        return u''


def getPlacement(flatCode, eventId):
    actionTypeList = getActionTypeIdListByFlatCode(flatCode)
    actionTypeIdList = (','.join(str(actionTypeId) for actionTypeId in actionTypeList if actionTypeId))
    if actionTypeIdList:
        return u'''SELECT OSP.name AS placement
            FROM Action AS A
            INNER JOIN ActionPropertyType AS APT ON APT.actionType_id = A.actionType_id
            INNER JOIN ActionProperty AS AP ON AP.type_id = APT.id
            INNER JOIN ActionProperty_OrgStructure_Placement AS APOS ON APOS.id = AP.id
            INNER JOIN OrgStructure_Placement as OSP on OSP.id = APOS.value
            WHERE A.event_id = %s
            AND A.deleted = 0
            AND A.endDate IS NULL
            AND A.actionType_id IN (%s)
            AND AP.action_id = A.id
            AND AP.deleted = 0
            AND APT.actionType_id = A.actionType_id
            AND APT.deleted = 0
            AND APT.name = 'Помещение'
            ORDER BY A.begDate DESC
            LIMIT 1'''%(eventId, actionTypeIdList)
    else:
        return u''


def getMovingDays(orgStructureIdList, begDatePeriod, endDatePeriod, profile = None, isHospital = None, rural = None, additionalCond = None, bedsSchedule = None, typeOS = None, financeTypeId = None, financeEventId = None):
    days = 0
    db = QtGui.qApp.db
    tableAPT = db.table('ActionPropertyType')
    tableAP = db.table('ActionProperty')
    tableActionType = db.table('ActionType')
    tableAction = db.table('Action')
    tableEvent = db.table('Event')
    tableClient = db.table('Client')
    tableOrg = db.table('Organisation')
    tableOS = db.table('OrgStructure')
    tableOSHB = db.table('OrgStructure_HospitalBed')
    tableHPS = db.table('rbHospitalBedShedule')
    queryTable = (u''' ActionType 
  INNER JOIN Action ON ActionType.`id`=Action.`actionType_id`  
  INNER JOIN Event ON Action.`event_id`=Event.`id`  
  LEFT JOIN EventType ON EventType.id = Event.eventType_id
  LEFT JOIN mes.MES on MES.id = Event.MES_id
  LEFT JOIN rbService ON rbService.infis = MES.code
  LEFT JOIN rbMedicalAidType ON EventType.medicalAidType_id = rbMedicalAidType.id

  LEFT JOIN Client ON Event.`client_id`=Client.`id`  
  LEFT JOIN Contract ON Contract.id = Event.contract_id
LEFT JOIN rbFinance on rbFinance.id = Contract.finance_id
LEFT JOIN Contract_Tariff ct ON ct.master_id = Contract.id
    and ct.service_id = rbService.id and ct.deleted = 0
    and (ct.endDate is not null and DATE(Event.execDate) between ct.begDate and ct.endDate
    or DATE(Event.execDate) >= ct.begDate and ct.endDate is null) and ct.tariffType = 13
  LEFT JOIN ClientPolicy on ClientPolicy.id = COALESCE((SELECT MAX(cp2.id) 
                                                      FROM ClientPolicy cp2
                                                      WHERE cp2.client_id = Client.id AND cp2.deleted = 0 AND cp2.begDate =
    (select MAX(cp.begDate) from ClientPolicy cp
            WHERE cp.client_id = Client.id
              AND cp.policyType_id IN (1,2)
              AND cp.deleted = 0
              AND cp.begDate <= Event.setDate AND (cp.endDate is NULL OR cp.endDate >= Event.setDate))),
   (SELECT MAX(cp2.id)
            FROM ClientPolicy cp2
            WHERE cp2.client_id = Client.id AND cp2.deleted = 0 AND cp2.begDate =
            (select MAX(cp.begDate)
              from ClientPolicy cp
              WHERE cp.client_id = Client.id
              AND cp.policyType_id IN (1,2)
              AND cp.deleted = 0
              AND cp.begDate BETWEEN Event.setDate AND ADDDATE(DATE(Event.execDate), 30)
              )),
  (SELECT MAX(cp2.id)
          FROM ClientPolicy cp2
          WHERE cp2.client_id = Event.relative_id AND cp2.deleted = 0 AND cp2.begDate =
          (select MAX(cp.begDate)
          from ClientPolicy cp
          WHERE cp.client_id = Event.relative_id
              AND cp.policyType_id IN (1,2)
              AND cp.deleted = 0
              AND cp.begDate <= Event.setDate AND (cp.endDate is NULL OR cp.endDate >= Event.setDate)
             )))
  LEFT JOIN Organisation AS Insurer ON Insurer.id = ClientPolicy.insurer_id
LEFT JOIN rbMedicalAidType mt ON mt.id = case when rbMedicalAidType.regionalCode in ('271', '272') and Event.execDate >= '2020-05-01' then (select mat.id from rbMedicalAidType mat where mat.regionalCode = IF(rbMedicalAidType.regionalCode = '271', '21', '22') limit 1) else rbMedicalAidType.id end

  INNER JOIN ActionPropertyType ON ActionPropertyType.`actionType_id`=ActionType.`id`  
  INNER JOIN ActionProperty ON ActionProperty.`type_id`=ActionPropertyType.`id`  
  INNER JOIN ActionProperty_HospitalBed ON ActionProperty_HospitalBed.`id`=ActionProperty.`id`  
  INNER JOIN OrgStructure_HospitalBed ON OrgStructure_HospitalBed.`id`=ActionProperty_HospitalBed.`value`  
  INNER JOIN OrgStructure ON OrgStructure.`id`=OrgStructure_HospitalBed.`master_id`  
  INNER JOIN Organisation ON Organisation.`id`=OrgStructure.`organisation_id`  
  INNER JOIN rbHospitalBedShedule ON rbHospitalBedShedule.`id`=OrgStructure_HospitalBed.`schedule_id`  
''')
    cond = [tableActionType['flatCode'].like('moving%'),
            tableAction['deleted'].eq(0),
            tableEvent['deleted'].eq(0),
            tableAP['deleted'].eq(0),
            tableActionType['deleted'].eq(0),
            tableAPT['deleted'].eq(0),
            tableOS['deleted'].eq(0),
            #tableOS['type'].ne(0),
            tableClient['deleted'].eq(0),
            tableOrg['deleted'].eq(0),
            tableAPT['typeName'].like('HospitalBed'),
            tableAP['action_id'].eq(tableAction['id']), 
            tableEvent['execDate'].ge(begDatePeriod), 
            tableEvent['execDate'].le(endDatePeriod)
           ]
    if financeTypeId:
        cond.append(tableOSHB['finance_id'].eq(financeTypeId))
    if financeEventId:
        cond.append('''rbFinance.id = %s'''%(financeEventId))
    if typeOS == 0:
        cond.append(tableOS['type'].eq(0))
    elif typeOS > 0:
        cond.append(tableOS['type'].ne(0))
    if isHospital is not None:
       cond.append(tableOrg['isHospital'].eq(isHospital))
    if rural:
        cond.append(getKladrClientRural())
    if bedsSchedule:
        if bedsSchedule == 1:
            cond.append(tableHPS['code'].eq(1))
        elif bedsSchedule == 2:
            cond.append(tableHPS['code'].ne(1))
    if additionalCond:
        cond.append(additionalCond)
    if profile:
        cond.append(tableOSHB['profile_id'].inlist(profile))
    else:
        cond.append(tableOSHB['profile_id'].isNull())
    cond.append(tableOSHB['master_id'].inlist(orgStructureIdList))
    cond.append('''ct.id is not null''')
    stmt = db.selectStmt(queryTable, [tableEvent['id'].alias('eventId'), tableAction['id'].alias('actionId'), tableAction['begDate'], tableAction['endDate'], tableHPS['code'].alias('schedule_code'), u"""if(mt.regionalCode in ('11', '12', '301', '302', '401', '402','41', '42', '43', '51', '52', '71', '72', '90', '411', '422', '511', '522'),
    WorkDays(Event.setDate, Event.execDate, EventType.weekProfileCode, mt.regionalCode), 0) as colPD"""],  cond)
    query = db.query(stmt)
    actionIdList = []
    while query.next():
        record = query.record()
        actionId = forceRef(record.value('actionId'))
        if actionId not in actionIdList:
            actionIdList.append(actionId)
            days += forceInt(record.value('colPD'))
    return days


def getSeniorsMovingDays(orgStructureIdList, begDatePeriod, endDatePeriod, profile = None, isHospital = None, rural = None, additionalCond = None, bedsSchedule = None, typeOS = None, financeTypeId = None, financeTypeIdList=[]):
    days = 0
    db = QtGui.qApp.db
    tableAPT = db.table('ActionPropertyType')
    tableAP = db.table('ActionProperty')
    tableActionType = db.table('ActionType')
    tableAction = db.table('Action')
    tableEvent = db.table('Event')
    tableClient = db.table('Client')
    tableOrg = db.table('Organisation')
    tableOS = db.table('OrgStructure')
    tableAPHB = db.table('ActionProperty_HospitalBed')
    tableOSHB = db.table('OrgStructure_HospitalBed')
    tableHPS = db.table('rbHospitalBedShedule')
    queryTable = tableActionType.innerJoin(tableAction, tableActionType['id'].eq(tableAction['actionType_id']))
    queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.leftJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
    queryTable = queryTable.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
    queryTable = queryTable.innerJoin(tableAP, tableAP['type_id'].eq(tableAPT['id']))
    queryTable = queryTable.innerJoin(tableAPHB, tableAPHB['id'].eq(tableAP['id']))
    queryTable = queryTable.innerJoin(tableOSHB, tableOSHB['id'].eq(tableAPHB['value']))
    queryTable = queryTable.innerJoin(tableOS, tableOS['id'].eq(tableOSHB['master_id']))
    queryTable = queryTable.innerJoin(tableOrg, tableOrg['id'].eq(tableOS['organisation_id']))
    queryTable = queryTable.innerJoin(tableHPS, tableHPS['id'].eq(tableOSHB['schedule_id']))
    cond = [tableActionType['flatCode'].like('moving%'),
            tableAction['deleted'].eq(0),
            tableEvent['deleted'].eq(0),
            tableAP['deleted'].eq(0),
            tableActionType['deleted'].eq(0),
            tableAPT['deleted'].eq(0),
            tableOS['deleted'].eq(0),
            #tableOS['type'].ne(0),
            tableClient['deleted'].eq(0),
            tableOrg['deleted'].eq(0),
            tableAPT['typeName'].like('HospitalBed'),
            tableAP['action_id'].eq(tableAction['id'])
           ]
    if financeTypeIdList:
        cond.append(tableOSHB['finance_id'].inlist(financeTypeIdList))
    if financeTypeId:
        cond.append(tableOSHB['finance_id'].eq(financeTypeId))
    cond.append(u'(age(Client.birthDate, Action.begDate)) >= IF(Client.sex = 2, 55, IF(Client.sex = 1, 60, 55))')
    if typeOS == 0:
        cond.append(tableOS['type'].eq(0))
    elif typeOS > 0:
        cond.append(tableOS['type'].ne(0))
    if isHospital is not None:
       cond.append(tableOrg['isHospital'].eq(isHospital))
    if rural:
        cond.append(getKladrClientRural())
    if bedsSchedule:
        if bedsSchedule == 1:
            cond.append(tableHPS['code'].eq(1))
        elif bedsSchedule == 2:
            cond.append(tableHPS['code'].ne(1))
    if additionalCond:
        cond.append(additionalCond)
#    if profile:
    cond.append(tableOSHB['profile_id'].inlist(profile))
    cond.append(tableOSHB['master_id'].inlist(orgStructureIdList))
    cond.append(tableAction['endDate'].ge(begDatePeriod),tableAction['begDate'].le(endDatePeriod))
    stmt = db.selectStmt(queryTable, [tableEvent['id'].alias('eventId'), tableAction['id'].alias('actionId'), tableAction['begDate'], tableAction['endDate'], tableHPS['code'].alias('schedule_code')], cond)
    query = db.query(stmt)
    actionIdList = []
    while query.next():
        record = query.record()
        actionId = forceRef(record.value('actionId'))
        if actionId not in actionIdList:
            actionIdList.append(actionId)
            begDate = forceDateTime(record.value('begDate'))
            endDate = forceDateTime(record.value('endDate'))
            schedule = forceInt(record.value('schedule_code'))
            days += countMovingDays(begDate, endDate, begDatePeriod, endDatePeriod, schedule)
    return days


def countMovingDays(begDate, endDate, begDatePeriod, endDatePeriod, schedule):
    days = 0
    if begDate < begDatePeriod:
        begDate = begDatePeriod #.addDays(-1)
    if not endDate or endDate > endDatePeriod:
        endDate = endDatePeriod
        if schedule != 1:
            days -= 1
        if endDate.date().dayOfYear() == endDate.date().daysInYear() or endDate.date().dayOfYear() == 1:
            days += 1
    if begDate and endDate:
        daysTo = begDate.daysTo(endDate)
        days += daysTo
        begTime = begDate.time()
        endTime = endDate.time()
        if schedule != 1:
            days += 1
        else:
            dayOfYear = begDate.date().dayOfYear()
            if daysTo:
                if begTime < QTime(9, 0) and dayOfYear != 1:
                    days += 1
                if endTime < QTime(9, 0):
                    days -= 1
            else:
                if begTime < QTime(9, 0) and dayOfYear != 1 and endTime >= QTime(9, 0):
                    days += 1
    return days


def appendContingentTypeCond(contingentTypeId):
    db = QtGui.qApp.db
    tableClient = db.table('Client')
    table = tableClient
    if not contingentTypeId:
        return table
    contingentOperation = forceInt(db.translate(CContingentTypeTranslator.CTTName, 'id',
                                                contingentTypeId, 'contingentOperation'))
    contingentTypeCond = []
    if CContingentTypeTranslator.isSexAgeSocStatusEnabled(contingentOperation):
        tmp = []
        contingentTypeCond.append('clientCT.id = Client.id AND Client.deleted = 0')
        tableClientSocStatus = db.table('ClientSocStatus')
        table = table.leftJoin(tableClientSocStatus, tableClient['id'].eq(tableClientSocStatus['client_id']))
        sexAgeCond    = CContingentTypeTranslator.getSexAgeCond(contingentTypeId)
        socStatusCond = CContingentTypeTranslator.getSocStatusCond(contingentTypeId)
        if CContingentTypeTranslator.isSexAgeSocStatusOperationType_OR(contingentOperation):
            if sexAgeCond is not None:
                tmp.extend(sexAgeCond)
            if socStatusCond is not None:
                tmp.extend(socStatusCond)
            contingentTypeCond.append(db.joinOr(tmp))
        else:
            if sexAgeCond is not None:
                tmp.append(db.joinOr(sexAgeCond))
            if socStatusCond is not None:
                tmp.append(db.joinOr(socStatusCond))
            contingentTypeCond.append(db.joinAnd(tmp))
    return db.selectStmt(table, 'DISTINCT Client.id', contingentTypeCond, order='', limit=1)

class CCheckableComboBox(QtGui.QComboBox):
    def __init__(self, parent = None):
        super(CCheckableComboBox, self).__init__(parent)
        self.view().pressed.connect(self.handleItemPressed)
        self.setModel(QtGui.QStandardItemModel(self))
        db = QtGui.qApp.db
        table = 'rbFinance'
        cols = ['id', 'code','name']
        recordList = db.getRecordList(table, cols, [], 'code')
        for record in recordList:
            name = forceString(record.value('name'))
            item = QtGui.QStandardItem(QString('%s'%(name)))
            item.setCheckState(Qt.Unchecked)
            item.financeId = forceRef(record.value('id'))
            self.model().appendRow(item)

    def handleItemPressed(self, index):
        item = self.model().itemFromIndex(index)
        if item.checkState() == Qt.Checked:
            item.setCheckState(Qt.Unchecked)
        else:
            item.setCheckState(Qt.Checked)


def splitTitle(cursor, t1, t2, width=u'100%'):
    cursor.movePosition(QtGui.QTextCursor.End)
    cursor.insertBlock()
    html = u'''
<table width="{0}">
<tr>
    <td align="left"><h5>{1}</h5></td>
    <td align="right"><h5>{2}</h5></td>
</tr>
</table>
    '''.format(width, t1, t2)
    cursor.insertHtml(html)
    cursor.insertBlock()


def _getChiefName(orgId):
    u"""Возвращает Ф.И.О руководителя организации"""
    db = QtGui.qApp.db
    result = None
    personId = forceRef(db.translate('Organisation', 'id', orgId, 'chief_id'))
    if personId:
        record = db.getRecord('Person', 'firstName,patrName,lastName', personId)
        if record:
            result = formatShortName(record.value('lastName'),
                                     record.value('firstName'),
                                     record.value('patrName'))
    if not result:
        result = forceString(db.translate('Organisation', 'id', orgId, 'chiefFreeInput'))
    return result

def getRetireeAges(begDate):
    '''
        Возвращает возраст нетрудоспособности на заданную дату
    '''

    if begDate:
        if begDate.year() == 2021:
            return 61, 56
        elif begDate.year() in (2022, 2023):
            return 62, 57
        elif begDate.year() in (2024, 2025):
            return 63, 58
        elif begDate.year() in (2026, 2027):
            return 64, 59
        elif begDate.year() >= 2028:
            return 65, 60
    return 60, 55
