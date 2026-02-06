# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2021 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignature, QDate, Qt

from Reports.Ui_ReportPreventiveMinorsSetup import Ui_ReportPreventiveMinorsSetupDialog
from library.MapCode import createMapCodeToRowIdx
from library.database import addDateInRange
from library.Utils import forceInt, forceString

from Events.Utils import getWorkEventTypeFilter
from Events.EventTypeListEditorDialog import CEventTypeListEditorDialog
from Orgs.Utils import getOrgStructureDescendants
from Reports.Report import CReport, normalizeMKB
from Reports.ReportBase import CReportBase, createTable
from Reports.ReportView import CPageFormat

MKBRows = [
    (u'Некоторые инфекционные и паразитарные болезни, из них:', u'1', u'A00-B99'),
    (u'туберкулез', u'1.1', u'A15-A19'),
    (u'болезнь, вызванная вирусом иммунодефицита человека [ВИЧ]', u'1.2', u'B20-B24'),
    (u'Новообразования', u'2', u'C00-D48'),
    (u'Болезни крови и кроветворных органов и отдельные нарушения, вовлекающие иммунный механизм, из них:', u'3',
     u'D50-D89'),
    (u'Анемии, связанные с питанием', u'3.1', u'D50-D53'),
    (u'Болезни эндокринной системы, расстройства питания и нарушения обмена веществ, из них:', u'4', u'E00-E90'),
    (u'сахарный диабет', u'4.1', u'E10-E14'),
    (u'недостаточность питания', u'4.2', u'E40-E46'),
    (u'ожирение и другие виды избыточности питания', u'4.3', u'E65-E68'),
    (u'ожирение', u'4.3.1', u'E66'),
    (u'задержка полового развития', u'4.4', u'E30.0'),
    (u'преждевременное половое созревание', u'4.5', u'E30.1'),
    (u'Психические расстройства и расстройства поведения, из них:', u'5', u'F00-F99'),
    (u'умственная отсталость', u'5.1', u'F70-F79'),
    (u'Болезни нервной системы, из них:', u'6', u'G00-G98'),
    (u'церебральный паралич и другие паралитические синдромы', u'6.1', u'G80-G83'),
    (u'Болезни глаза и его придаточного аппарата', u'7', u'H00-H59'),
    (u'нарушение рефракции и аккомодации', u'7.1', u'H52'),
    (u'миопия', u'7.2', u'H52.1'),
    (u'Болезни уха и сосцевидного отростка', u'8', u'H60-H95'),
    (u'Болезни системы кровообращения', u'9', u'I00-I99'),
    (u'Болезни, характеризующиеся повышенным кровяным давлением', u'9.1', u'I10-I13'),
    (u'Болезни органов дыхания, из них:', u'10', u'J00-J99'),
    (u'астма, астматический статус', u'10.1', u'J45-J46'),
    (u'Болезни органов пищеварения', u'11', u'K00-K93'),
    (u'гастрит и дуоденит', u'11.1', u'K29'),
    (u'Болезни кожи и подкожной клетчатки', u'12', u'L00-L98'),
    (u'Болезни костно-мышечной системы и соединительной ткани, из них:', u'13', u'M00-M99'),
    (u'кифоз, лордоз', u'13.1', u'M40'),
    (u'сколиоз', u'13.2', u'M41'),
    (u'плоская стопа приобретенная', u'13.3', u'M21.4'),
    (u'Болезни мочеполовой системы, из них:', u'14', u'N00-N99'),
    (u'болезни мужских половых органов', u'14.1', u'N40-N51'),
    (u'отсутствие менструаций, скудные и редкие менструации; обильные, частые и нерегулярные менструации; другие аномальные кровотечения из матки и влагалища; болевые и другие состояния, связанные с женскими половыми органами и менструальным циклом', u'14.2',u'N91,N92,N93,N94'),
    (u'воспалительные болезни женских тазовых органов', u'14.3', u'N70-N77'),
    (u'невоспалительные болезни яичника, маточной трубы и широкой связки матки', u'14.4', u'N83'),
    (u'болезни молочной железы', u'14.5', u'N60-N64'),
    (u'Отдельные состояния, возникающие в перинатальном периоде', u'15', u'P05-P96'),
    (u'Врожденные аномалии (пороки развития), деформации и хромосомные нарушения, из них:', u'16', u'Q00-Q99'),
    (u'нервной системы', u'16.1', u'Q00-Q07'),
    (u'глаза, уха, лица и шеи', u'16.2', u'Q10-Q18'),
    (u'системы кровообращения', u'16.3', u'Q20-Q28'),
    (u'органов пищеварения', u'16.4', u'Q38-Q45'),
    (u'женских половых органов', u'16.5', u'Q52'),
    (u'мужских половых органов', u'16.6', u'Q55'),
    (u'мочевой системы', u'16.7', u'Q60-Q64'),
    (u'костно-мышечной системы', u'16.8', u'Q65-Q79'),
    (u'хромосомные аномалии, не классифицированные в других рубриках', u'16.9', u'Q90-Q99'),
    (u'Травмы, отравления и некоторые другие последствия воздействия внешних причин', u'17', u'S00-T98'),
    (u'ВСЕГО ЗАБОЛЕВАНИЙ', u'18', u'A00-T98'),
]


def selectDataMKB(params):
    stmt = u""" SELECT  
    c.sex,
	COUNT(distinct c.id) as countMKB,
	ds.MKB,
    ds.setDate BETWEEN Event.setDate AND Event.execDate AS firstInPeriod,
	d.code in ('2', '6') AS getObserved,
	(
	    (SELECT d.code 
	    FROM Diagnostic dc1 
	    INNER JOIN Event e1 on e1.id=dc1.event_id
		INNER JOIN Diagnosis  ds1 ON ds1.id=dc1.diagnosis_id
		INNER JOIN rbDispanser d ON d.id = dc1.dispanser_id 
		WHERE   dc1.deleted=0 and ds1.deleted=0 AND e1.deleted=0
		AND ds1.client_id=c.id
		AND ds1.MKB=ds.MKB AND e1.setDate < {endDate}
		ORDER BY e1.setDate desc
		LIMIT 1
	    ) IN ('1', '2', '6')
	)AS isObserved
    FROM
    Event
    INNER JOIN EventType  ON EventType.id=Event.eventType_id
    INNER JOIN rbMedicalAidType  ON rbMedicalAidType.id=EventType.medicalAidType_id
    LEFT JOIN Person on Person.id=Event.execPerson_id
    INNER JOIN Client c ON c.id=Event.client_id
    INNER JOIN Diagnostic dc ON   dc.event_id=Event.id
    INNER JOIN Diagnosis ds ON ds.id=dc.diagnosis_id
    INNER JOIN rbDiagnosisType ON rbDiagnosisType.id=dc.diagnosisType_id
    LEFT JOIN rbDispanser d ON d.id = dc.dispanser_id
    WHERE 
    {eventCond}
    AND
    {clientCond}
    AND rbDiagnosisType.code IN ('1', '2')
    AND dc.deleted=0 AND ds.deleted=0
    GROUP BY mkb, sex, isObserved, getObserved, firstInPeriod
    """
    begDate = params.get('begDate', QDate())
    endDate = params.get('endDate', QDate())

    return QtGui.qApp.db.query(
        stmt.format(
            eventCond=getCondForSelectDataEvent(params),
            clientCond=getCondForSelectDataClient(params, 'Event.execDate'),
            begDate=QtGui.qApp.db.formatDate(begDate),
            endDate=QtGui.qApp.db.formatDate(endDate.addDays(1)),
        ))


def selectDataAllChildren(params, previousPeriod=0):
    '''
        Если найден проф осмотр в периоде - возраст считается на дату осмотра
        Если не найден - на дату завершения периода
    '''
    stmt = u"""
    SELECT COUNT(c.id) AS clientCount,
    age(c.birthDate, IFNULL(e.execDate, {endDate})) AS clientAge,
    c.sex,
	COUNT(distinct (SELECT ClientSocStatus.client_id
	        FROM ClientSocStatus 
	        INNER JOIN rbSocStatusClass ON rbSocStatusClass.id=ClientSocStatus.socStatusClass_id 
	        left JOIN rbSocStatusClass rbSocStatusClassP ON rbSocStatusClassP.id = rbSocStatusClass.group_id
	        INNER JOIN rbSocStatusType ON rbSocStatusType.id=ClientSocStatus.socStatusType_id 
	        WHERE 
	        ClientSocStatus.deleted=0  AND ClientSocStatus.client_id=c.id 
	        AND rbSocStatusType.code IN ('084', '284', '081', '082', '083', '281', '282')
	        AND ((rbSocStatusClass.group_id IS NULL AND rbSocStatusClass.code='1') 
	            OR (rbSocStatusClassP.group_id IS NULL AND rbSocStatusClassP.code='1')) 
	        AND (ClientSocStatus.begDate IS NULL OR ClientSocStatus.begDate <= {endDate})
	        AND (ClientSocStatus.endDate IS NULL OR ClientSocStatus.endDate > {begDate})
	        LIMIT 1
		)) AS isDisabled,
		IF(e.execDate, 1, 0) AS hasProf,
	    ({attachCol}
	    ) AS isAttached,
        sum(rbResult.regionalCode = '332') AS h1group,
        sum(rbResult.regionalCode = '333') AS h2group,
        sum(rbResult.regionalCode = '334') AS h3group,
        sum(rbResult.regionalCode = '335') AS h4group,
        sum(rbResult.regionalCode = '336') AS h5group,
        SUM((SELECT 1
            FROM ActionProperty ap 
            INNER JOIN ActionPropertyType apt ON apt.id = ap.type_id  AND apt.shortname = '169mg'
            LEFT JOIN ActionProperty_Integer api  ON ap.id = api.id 
            LEFT JOIN `v1.2.643.5.1.13.13.99.2.526` vspr ON vspr.id=api.value
            LEFT JOIN ActionProperty_String aps  ON ap.id = aps.id 
            WHERE ap.action_id=a.id AND ap.deleted=0 and (vspr.code = '1' OR aps.value='I')
            LIMIT 1
        ))AS f1group,
        SUM((SELECT 1
            FROM ActionProperty ap 
            INNER JOIN ActionPropertyType apt ON apt.id = ap.type_id  AND apt.shortname = '169mg'
            LEFT JOIN ActionProperty_Integer api  ON ap.id = api.id 
            LEFT JOIN `v1.2.643.5.1.13.13.99.2.526` vspr ON vspr.id=api.value
            LEFT JOIN ActionProperty_String aps  ON ap.id = aps.id 
            WHERE ap.action_id=a.id AND  ap.deleted=0 and (vspr.code = '2' OR aps.value='II')
            LIMIT 1
        )) AS f2group,
        SUM((SELECT 1
            FROM ActionProperty ap 
            INNER JOIN ActionPropertyType apt ON apt.id = ap.type_id  AND apt.shortname = '169mg'
            LEFT JOIN ActionProperty_Integer api  ON ap.id = api.id 
            LEFT JOIN `v1.2.643.5.1.13.13.99.2.526` vspr ON vspr.id=api.value
            LEFT JOIN ActionProperty_String aps  ON ap.id = aps.id 
            WHERE ap.action_id=a.id AND ap.deleted=0 and (vspr.code = '3' OR aps.value='III')
            LIMIT 1
        )) AS f3group,
        SUM((SELECT 1
            FROM ActionProperty ap 
            INNER JOIN ActionPropertyType apt ON apt.id = ap.type_id  AND apt.shortname = '169mg'
            LEFT JOIN ActionProperty_Integer api  ON ap.id = api.id 
            LEFT JOIN `v1.2.643.5.1.13.13.99.2.526` vspr ON vspr.id=api.value
            LEFT JOIN ActionProperty_String aps  ON ap.id = aps.id 
            WHERE ap.action_id=a.id AND ap.deleted=0 and (vspr.code = '4' OR aps.value='IV')
            LIMIT 1
        )) AS f4group,
        SUM((SELECT 1
            FROM ActionProperty ap 
            INNER JOIN ActionPropertyType apt ON apt.id = ap.type_id  AND apt.shortname = '169mg'
            LEFT JOIN ActionProperty_Integer api  ON ap.id = api.id 
            LEFT JOIN `v1.2.643.5.1.13.13.99.2.526` vspr ON vspr.id=api.value
            LEFT JOIN ActionProperty_String aps  ON ap.id = aps.id 
            WHERE ap.action_id=a.id AND ap.deleted=0 and (vspr.code = '5' OR aps.value='не допущен')
            LIMIT 1
        )) AS f5group
        {addColsCurrentPeriod}  
        FROM Client c	
        -- обходим случаи нескольких профосмотров в указанном периоде, тк все данные (группы здоровья и тд) 
        -- берутся из последнего профосмотра (тз)
        LEFT JOIN Event e on e.id = (
            SELECT MAX(Event.id) FROM Event
            INNER JOIN EventType  ON EventType.id=Event.eventType_id
            INNER JOIN rbMedicalAidType  ON rbMedicalAidType.id=EventType.medicalAidType_id
            LEFT JOIN Person on Person.id=Event.execPerson_id
            WHERE Event.client_id=c.id AND {eventCond}
        )
        LEFT JOIN rbResult ON rbResult.id=e.result_id
        LEFT JOIN Action a ON a.id = (SELECT MAX(Action.id) FROM Action inner join ActionType on ActionType.id=Action.actionType_id WHERE Action.deleted=0 and Action.event_id=e.id and ActionType.flatCode LIKE "f030-po/y-17%")
        WHERE {clientCond}
        GROUP BY clientAge, c.sex, hasProf, isAttached;  
    """

    addColsCurrentPeriod = u''
    if not previousPeriod:
        addColsCurrentPeriod = u"""
        ,SUM((SELECT 1
            FROM ActionProperty ap 
            INNER JOIN ActionPropertyType apt ON apt.id = ap.type_id  AND apt.shortname IN ('1623dk', '1633dk', '1643dk', '1653dk', '1663dk', '1623di', '1633di', '1643di', '1653di', '1663di')
            INNER JOIN ActionProperty_String aps  ON ap.id = aps.id 
            WHERE ap.action_id=a.id AND ap.deleted=0 AND (aps.value LIKE '%амбулаторных%' OR aps.value LIKE '%дневного%')
            LIMIT 1
        )) AS tbl41col2,
        SUM((SELECT 1
            FROM ActionProperty ap 
            INNER JOIN ActionPropertyType apt ON apt.id = ap.type_id  AND apt.shortname IN ('1624dk', '1634dk', '1644dk', '1654dk', '1664dk', '1624di', '1634di', '1644di', '1654di', '1664di')
            INNER JOIN ActionProperty_String aps  ON ap.id = aps.id 
            WHERE ap.action_id=a.id AND ap.deleted=0 and (aps.value LIKE '%амбулаторных%' OR aps.value LIKE '%дневного%')
            LIMIT 1
        )) AS tbl41col3,
        SUM((SELECT 1
            FROM ActionProperty ap 
            INNER JOIN ActionPropertyType apt ON apt.id = ap.type_id  AND apt.shortname IN ('1623dk', '1633dk', '1643dk', '1653dk', '1663dk', '1623di', '1633di', '1643di', '1653di', '1663di')
            INNER JOIN ActionProperty_String aps  ON ap.id = aps.id 
            WHERE ap.action_id=a.id AND ap.deleted=0 AND aps.value LIKE '%стационарных%'
            LIMIT 1
        )) AS tbl41col4,
       SUM((SELECT 1
            FROM ActionProperty ap 
            INNER JOIN ActionPropertyType apt ON apt.id = ap.type_id  AND apt.shortname IN ('1624dk', '1634dk', '1644dk', '1654dk', '1664dk', '1624di', '1634di', '1644di', '1654di', '1664di')
            INNER JOIN ActionProperty_String aps  ON ap.id = aps.id 
            WHERE ap.action_id=a.id AND ap.deleted=0 and aps.value LIKE '%стационарных%'
            LIMIT 1
        )) AS tbl41col5,
       SUM((SELECT 1
            FROM ActionProperty ap 
            INNER JOIN ActionPropertyType apt ON apt.id = ap.type_id  AND apt.shortname IN ('1625lnaz', '1635lnaz', '1645lnaz', '1655lnaz', '1665lnaz')
            INNER JOIN ActionProperty_String aps  ON ap.id = aps.id 
            WHERE ap.action_id=a.id AND ap.deleted=0 and (aps.value LIKE '%амбулаторных%' OR aps.value LIKE '%дневного%')
            LIMIT 1
        )) AS tbl42col2,
       SUM((SELECT 1
            FROM ActionProperty ap 
            INNER JOIN ActionPropertyType apt ON apt.id = ap.type_id  AND apt.shortname IN ('1625lnaz', '1635lnaz', '1645lnaz', '1655lnaz', '1665lnaz')
            INNER JOIN ActionProperty_String aps  ON ap.id = aps.id 
            WHERE ap.action_id=a.id AND ap.deleted=0 and aps.value LIKE '%стационарных%'
            LIMIT 1
        )) AS tbl42col3,
       SUM((SELECT 1
            FROM ActionProperty ap 
            INNER JOIN ActionPropertyType apt ON apt.id = ap.type_id  AND apt.shortname IN ('1626mr', '1636mr', '1646mr', '1656mr', '1666mr')
            INNER JOIN ActionProperty_String aps  ON ap.id = aps.id 
            WHERE ap.action_id=a.id AND ap.deleted=0 and (aps.value LIKE '%амбулаторных%' OR aps.value LIKE '%дневного%')
            LIMIT 1
        )) AS tbl42col4,
       SUM((SELECT 1
            FROM ActionProperty ap 
            INNER JOIN ActionPropertyType apt ON apt.id = ap.type_id  AND apt.shortname IN ('1626mr', '1636mr', '1646mr', '1656mr', '1666mr')
            INNER JOIN ActionProperty_String aps  ON ap.id = aps.id 
            WHERE ap.action_id=a.id AND ap.deleted=0 and aps.value LIKE '%стационарных%'
            LIMIT 1
        )) AS tbl42col5,
        SUM((SELECT 1
            FROM ActionProperty ap 
            INNER JOIN ActionPropertyType apt ON apt.id = ap.type_id  AND apt.shortname IN ('1626sl', '1636sl', '1646sl', '1656sl', '1666sl')
            INNER JOIN ActionProperty_String aps  ON ap.id = aps.id 
            WHERE ap.action_id=a.id AND ap.deleted=0 and aps.value IS NOT null
            LIMIT 1
        )) AS tbl42col6,
        SUM((SELECT 1
            FROM ActionProperty ap 
            INNER JOIN ActionPropertyType apt ON apt.id = ap.type_id  AND apt.shortname IN ('04fiz', '517fiz')
            LEFT JOIN ActionProperty_String aps  ON ap.id = aps.id 
            LEFT JOIN ActionProperty_Integer api  ON ap.id = api.id 
            LEFT JOIN `v1.2.643.5.1.13.13.99.2.982` vspr ON vspr.id=api.value
            WHERE ap.action_id=a.id AND ap.deleted=0 AND (aps.value LIKE '%нормальное%' OR vspr.name LIKE '%нормальное%')
            LIMIT 1
        )) AS tbl5col3,
        SUM((SELECT 1
            FROM ActionProperty ap 
            INNER JOIN ActionPropertyType apt ON apt.id = ap.type_id  AND apt.shortname IN ('04fiz', '517fiz', '04fizm')
            LEFT JOIN ActionProperty_String aps  ON ap.id = aps.id 
            LEFT JOIN ActionProperty_Integer api  ON ap.id = api.id 
            LEFT JOIN `v1.2.643.5.1.13.13.99.2.982` vspr ON vspr.id=api.value
            WHERE ap.action_id=a.id AND ap.deleted=0 AND (aps.value LIKE '%дефицит массы тела%' OR vspr.name LIKE '%дефицит массы тела%')
            LIMIT 1
        )) AS tbl5col4,
        SUM((SELECT 1
            FROM ActionProperty ap 
            INNER JOIN ActionPropertyType apt ON apt.id = ap.type_id  AND apt.shortname IN ('04fiz', '517fiz', '04fizm')
            LEFT JOIN ActionProperty_String aps  ON ap.id = aps.id 
            LEFT JOIN ActionProperty_Integer api  ON ap.id = api.id 
            LEFT JOIN `v1.2.643.5.1.13.13.99.2.982` vspr ON vspr.id=api.value
            WHERE ap.action_id=a.id AND ap.deleted=0 AND (aps.value LIKE '%избыток массы тела%' OR vspr.name LIKE '%избыток массы тела%')
            LIMIT 1
        )) AS tbl5col5,
        SUM((SELECT 1
            FROM ActionProperty ap 
            INNER JOIN ActionPropertyType apt ON apt.id = ap.type_id  AND apt.shortname IN ('04fiz', '517fiz', '04fizr')
            LEFT JOIN ActionProperty_String aps  ON ap.id = aps.id 
            LEFT JOIN ActionProperty_Integer api  ON ap.id = api.id 
            LEFT JOIN `v1.2.643.5.1.13.13.99.2.982` vspr ON vspr.id=api.value
            WHERE ap.action_id=a.id AND ap.deleted=0 AND (aps.value LIKE '%низкий рост%' OR vspr.name LIKE '%низкий рост%')
            LIMIT 1
        )) AS tbl5col6,
        SUM((SELECT 1
            FROM ActionProperty ap 
            INNER JOIN ActionPropertyType apt ON apt.id = ap.type_id  AND apt.shortname IN ('04fiz', '517fiz', '04fizr')
            LEFT JOIN ActionProperty_String aps  ON ap.id = aps.id 
            LEFT JOIN ActionProperty_Integer api  ON ap.id = api.id 
            LEFT JOIN `v1.2.643.5.1.13.13.99.2.982` vspr ON vspr.id=api.value
            WHERE ap.action_id=a.id AND ap.deleted=0 AND (aps.value LIKE '%высокий рост%' OR vspr.name LIKE '%высокий рост%')
            LIMIT 1
    	 )) AS tbl5col7
            """

    begDate = QtGui.qApp.db.formatDate(params.get('begDateBeforeRecord' if previousPeriod else 'begDate', QDate()))
    endDate = QtGui.qApp.db.formatDate(params.get('endDateBeforeRecord' if previousPeriod else 'endDate', QDate()))

    return QtGui.qApp.db.query(
        stmt.format(
            eventCond=getCondForSelectDataEvent(params, previousPeriod),
            clientCond=getCondForSelectDataClient(params, 'IFNULL(e.execDate, %s)' % endDate),
            begDate=begDate,
            endDate=endDate,
            attachCol=getColForClientAttach(params).format(begDate=begDate, endDate=endDate),
            addColsCurrentPeriod=addColsCurrentPeriod,
        ))

def getColForClientAttach(params):
    cond = []
    tableClient = QtGui.qApp.db.table('Client').alias('c')

    outerCond = ['ClientAttach.client_id = c.id', '(ClientAttach.endDate > {begDate} or ClientAttach.endDate IS NULL )',
                 'ClientAttach.begDate IS NULL or ClientAttach.begDate <= {endDate}']
    innerCond = ['CA2.client_id = c.id', 'rbAttachType2.temporary=0']

    cond.append('''EXISTS (SELECT ClientAttach.id
               FROM ClientAttach
               LEFT JOIN rbAttachType ON rbAttachType.id = ClientAttach.attachType_id
               WHERE ClientAttach.deleted=0
               AND %s
               AND ClientAttach.id = (SELECT MAX(CA2.id)
                           FROM ClientAttach AS CA2
                           LEFT JOIN rbAttachType AS rbAttachType2 ON rbAttachType2.id = CA2.attachType_id
                           WHERE CA2.deleted=0 AND %s))''' % (
    QtGui.qApp.db.joinAnd(outerCond), QtGui.qApp.db.joinAnd(innerCond)))
    cond.append(tableClient['deathDate'].isNull())

    return QtGui.qApp.db.joinAnd(cond)

def getCondForSelectDataEvent(params, previousPeriod=0):
    begDate = params.get('begDateBeforeRecord', QDate()) if previousPeriod else params.get('begDate', QDate())
    endDate = params.get('endDateBeforeRecord', QDate()) if previousPeriod else params.get('endDate', QDate())
    eventPurposeId = params.get('eventPurposeId', None)
    eventTypeList = params.get('eventTypeList', [])
    orgStructureId = params.get('orgStructureId', None)
    personId = params.get('personId', None)

    db = QtGui.qApp.db
    tableEvent = db.table('Event')
    tableEventType = db.table('EventType')
    tablePerson = db.table('Person')
    tableRmt = db.table('rbMedicalAidType')

    cond = [
        tableRmt['regionalCode'].eq('262'),
        tableEvent['execDate'].isNotNull(),
        tableEvent['deleted'].eq(0),
    ]
    addDateInRange(cond, tableEvent['execDate'], begDate, endDate)
    if eventTypeList:
        cond.append(tableEvent['eventType_id'].inlist(eventTypeList))
    elif eventPurposeId:
        cond.append(tableEventType['purpose_id'].eq(eventPurposeId))
    if personId:
        cond.append(tableEvent['execPerson_id'].eq(personId))
    elif orgStructureId:
        cond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureDescendants(orgStructureId)))
    else:
        cond.append(tablePerson['org_id'].eq(QtGui.qApp.currentOrgId()))

    return QtGui.qApp.db.joinAnd(cond)


def getCondForSelectDataClient(params, dateString):
    sex = params.get('sex', 0)
    ageFrom = params.get('ageFrom', 0)
    ageTo = params.get('ageTo', 150)

    tableClient = QtGui.qApp.db.table('Client').alias('c')

    cond = [
        tableClient['deleted'].eq(0),
    ]
    if sex:
        cond.append(tableClient['sex'].eq(sex))
    cond.append('age(c.birthDate, %s) BETWEEN %d AND %d' % (dateString, ageFrom, ageTo))
    cond.append(tableClient['birthDate'].le(params.get('endDate', QDate())))

    return QtGui.qApp.db.joinAnd(cond)


class CReportPreventiveMinors(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Форма 030-ПО|о-17')
        self.pageFormat = CPageFormat(pageSize=CPageFormat.A4, orientation=CPageFormat.Landscape, leftMargin=5,
                                      topMargin=5, rightMargin=5, bottomMargin=5)

    def dumpParamsMultiSelect(self, cursor, params):
        description = []
        eventTypeList = params.get('eventTypeList', None)
        if eventTypeList:
            db = QtGui.qApp.db
            tableET = db.table('EventType')
            records = db.getRecordList(tableET, [tableET['name']],
                                       [tableET['deleted'].eq(0), tableET['id'].inlist(eventTypeList)])
            nameList = []
            for record in records:
                nameList.append(forceString(record.value('name')))
            description.append(u'тип события:  %s' % (u','.join(name for name in nameList if name)))
        else:
            description.append(u'тип события:  не задано')
        columns = [('100%', [], CReportBase.AlignLeft)]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)

    def getDescription(self, params):
        rows = CReport.getDescription(self, params)
        return rows

    def getSetupDialog(self, parent):
        result = CReportPreventiveMinorsSetupDialog(parent)
        result.setTitle(self.title())
        return result

    @staticmethod
    def calculateQueryMKB(query):
        rowMKBForCheck = MKBRows[-1]

        mapMKBForCheck = createMapCodeToRowIdx([rowMKBForCheck[2]])
        mapMKBRows = createMapCodeToRowIdx([row[2] for row in MKBRows])
        rowSize = 8
        reportData = [[0] * rowSize for _ in xrange(len(MKBRows))]

        while query.next():
            record = query.record()
            mkb = normalizeMKB(forceString(record.value('MKB')))
            # диагнозы, которые не требуется учитывать в данном разделе
            if not mapMKBForCheck.get(mkb, None):
                continue
            mkbCount = forceInt(record.value('countMKB'))
            sex = forceInt(record.value('sex'))
            firstInPeriod = forceInt(record.value('firstInPeriod'))
            getObserved = forceInt(record.value('getObserved'))
            isObserved = forceInt(record.value('isObserved'))

            for row in mapMKBRows.get(mkb, []):
                reportData[row][0] += mkbCount
                if firstInPeriod:
                    reportData[row][2] += mkbCount
                if isObserved:
                    reportData[row][4] += mkbCount
                if getObserved:
                    reportData[row][6] += mkbCount
                if sex == 1:
                    reportData[row][1] += mkbCount
                    if firstInPeriod:
                        reportData[row][3] += mkbCount
                    if isObserved:
                        reportData[row][5] += mkbCount
                    if getObserved:
                        reportData[row][7] += mkbCount

        return reportData

    @staticmethod
    def calculateQueryChildren(query, isPreviousPeriod = 0):
        # разделы 1, 2
        rows1_2 = [(u' всего в возрасте от 0 до 17 лет включительно: %d (человек), из них', u'1.1.', 0, 17, None),
                   (u' в возрасте от 0 до 4 лет включительно %d (человек)', u'1.1.1.', 0, 4, None),
                   (u' в возрасте от 0 до 14 лет включительно %d (человек),', u'1.1.2.', 0, 14, None),
                   (u' в возрасте от 5 до 9 лет включительно %d (человек),', u'1.1.3.', 5, 9, None),
                   (u' в возрасте от 10 до 14 лет включительно %d (человек),', u'1.1.4.', 10, 14, None),
                   (u' в возрасте от 15 до 17 лет включительно %d (человек),', u'1.1.5.', 15, 17, None),
                   (u' детей-инвалидов в возрасте от 0 до 17 лет включительно %d (человек).', u'1.1.6.', 0, 17, 1),
                   ]
        tableCount1_2 = 2
        reportData1_2 = [[row[1] + row[0] for row in rows1_2] for _ in xrange(tableCount1_2)]
        reportData1_2Section = [[0] * len(rows1_2) for _ in xrange(tableCount1_2)]

        # разделы с 4 до конца
        rows4etc = [(u'Всего детей в возрасте до 17 лет включительно, из них:', 0, 17, None),
                (u'от 0 до 4 лет включительно', 0, 4, None),
                (u'в том числе мальчиков', 0, 4, 1),
                (u'от 0 до 14 лет включительно', 0, 14, None),
                (u'в том числе мальчиков', 0, 14, 1),
                (u'от 5 до 9 лет включительно', 5, 9, None),
                (u'в том числе мальчиков', 5, 9, 1),
                (u'от 10 до 14 лет включительно', 10, 14, None),
                (u'в том числе мальчиков', 10, 14, 1),
                (u'от 15 до 17 лет включительно', 15, 17, None),
                (u'в том числе мальчиков', 15, 17, 1),
                ]
        mapToOriginRows4etc = {}
        tableCount4etc = 5
        maxColumnCount4etc = 6

        reportData4etc = [[] for _ in xrange(tableCount4etc)]
        for idxTable in range(0, tableCount4etc):
            for idxRow in xrange(len(rows4etc)):
                # для таблиц c индексом in (0, 1)
                # (дополнительные консультации и исследования
                # лечение, мед реабилитация, сан-кур)
                # не требуются строки по мальчикам
                if idxTable >= 2 or (idxTable < 2 and rows4etc[idxRow][3] is None):
                    tableDataRow = [0] * maxColumnCount4etc
                    tableDataRow.insert(0, rows4etc[idxRow][0])
                    reportData4etc[idxTable].append(tableDataRow)
                    mapToOriginRows4etc[(idxTable, len(reportData4etc[idxTable]) - 1)] = idxRow

        while query.next():
            record = query.record()
            clientCount = forceInt(record.value('clientCount'))
            clientSex = forceInt(record.value('sex'))
            clientAge = forceInt(record.value('clientAge'))
            isDisabled = forceInt(record.value('isDisabled'))
            hasProf = forceInt(record.value('hasProf'))
            isAttached = forceInt(record.value('isAttached'))

            # разделы 1, 2
            if not isPreviousPeriod:
                for idxTable in xrange(tableCount1_2):
                    # раздел2 - прошли проф мероприятия
                    if idxTable == 1 and not hasProf:
                        continue
                    # Раздел 1 Собирается только по прикрепленному населению
                    if idxTable == 0 and not isAttached:
                        continue
                    for idxRow in xrange(len(reportData1_2[idxTable])):
                        if rows1_2[idxRow][2] <= clientAge <= rows1_2[idxRow][3]:
                            if rows1_2[idxRow][4]:
                                reportData1_2Section[idxTable][idxRow] += isDisabled
                            else:
                                reportData1_2Section[idxTable][idxRow] += clientCount

            # разделы с 4 до конца
            if hasProf:
                for idxTable in xrange(tableCount4etc):
                    for idxRow in xrange(len(reportData4etc[idxTable])):
                        originRow = mapToOriginRows4etc.get((idxTable, idxRow), idxRow)
                        if clientAge > rows4etc[originRow][2] or clientAge < rows4etc[originRow][1]:
                            continue
                        # строки по мальчикам
                        if rows4etc[originRow][3] is not None and rows4etc[originRow][3] != clientSex:
                            continue
                        reportLine = reportData4etc[idxTable][idxRow]
                        if idxTable == 0:
                            # дополнительные консультации и исследования
                            reportLine[1] += forceInt(record.value('tbl41col2'))
                            reportLine[2] += forceInt(record.value('tbl41col3'))
                            reportLine[3] += forceInt(record.value('tbl41col4'))
                            reportLine[4] += forceInt(record.value('tbl41col5'))
                        elif idxTable == 1:
                            # лечение, мед реабилитация, сан-кур
                            reportLine[1] += forceInt(record.value('tbl42col2'))
                            reportLine[2] += forceInt(record.value('tbl42col3'))
                            reportLine[3] += forceInt(record.value('tbl42col4'))
                            reportLine[4] += forceInt(record.value('tbl42col5'))
                            reportLine[5] += forceInt(record.value('tbl42col6'))
                        elif idxTable == 2:
                            # физическое развитие
                            reportLine[1] += clientCount
                            reportLine[2] += forceInt(record.value('tbl5col3'))
                            reportLine[3] += forceInt(record.value('tbl5col4'))
                            reportLine[4] += forceInt(record.value('tbl5col5'))
                            reportLine[5] += forceInt(record.value('tbl5col6'))
                            reportLine[6] += forceInt(record.value('tbl5col7'))
                        elif idxTable == 3:
                            # группы для занятий физкультурой
                            reportLine[1] += clientCount
                            reportLine[2] += forceInt(record.value('f1group'))
                            reportLine[3] += forceInt(record.value('f2group'))
                            reportLine[4] += forceInt(record.value('f3group'))
                            reportLine[5] += forceInt(record.value('f4group'))
                            reportLine[6] += forceInt(record.value('f5group'))
                        elif idxTable == 4:
                            # группы здоровья
                            reportLine[1] += clientCount
                            reportLine[2] += forceInt(record.value('h1group'))
                            reportLine[3] += forceInt(record.value('h2group'))
                            reportLine[4] += forceInt(record.value('h3group'))
                            reportLine[5] += forceInt(record.value('h4group'))
                            reportLine[6] += forceInt(record.value('h5group'))

        # разделы 1, 2
        if not isPreviousPeriod:
            for idxTable in xrange(tableCount1_2):
                for idxRow in xrange(len(reportData1_2[idxTable])):
                    reportData1_2[idxTable][idxRow] = reportData1_2[idxTable][idxRow] % \
                                                      reportData1_2Section[idxTable][idxRow]
        return reportData1_2, reportData4etc

    def build(self, params):
        query = selectDataMKB(params)
        MKBData = CReportPreventiveMinors.calculateQueryMKB(query)

        query = selectDataAllChildren(params, 0)
        childrenSection1_2Data, childrenCurrentPeriodData = CReportPreventiveMinors.calculateQueryChildren(query, 0)

        query = selectDataAllChildren(params, 1)
        _, childrenPrevPeriodData = CReportPreventiveMinors.calculateQueryChildren(query, 1)

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        # self.dumpParamsMultiSelect(cursor, params)
        # self.dumpParams(cursor, params)
        # cursor.insertBlock()

        self.produceReportHeader(cursor, params)
        self.produceSection1(cursor, childrenSection1_2Data[0])
        self.produceSection2(cursor, childrenSection1_2Data[1])
        self.produceSection3(cursor, MKBData)
        self.produceSection4(cursor, childrenCurrentPeriodData[:2])
        self.produceSection5(cursor, childrenCurrentPeriodData[2])
        self.produceSection6(cursor, childrenCurrentPeriodData[3], childrenPrevPeriodData[3])
        self.produceSection7(cursor, childrenCurrentPeriodData[4], childrenPrevPeriodData[4])

        return doc

    def produceReportHeader(self, cursor, params):
        from Registry.Utils import formatAddress

        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertBlock(CReportBase.AlignCenter)
        cursor.insertText(u'Сведения о профилактических медицинских осмотрах несовершеннолетних\n '
                          u'за период %s-%s' % (params.get('begDate', QDate()).toString('dd.MM.yyyy'),
                                                params.get('endDate', QDate()).toString('dd.MM.yyyy')))
        cursor.insertBlock()
        cursor.insertBlock()

        bfAlignLeftTop = QtGui.QTextBlockFormat()
        bfAlignLeftTop.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        table = createTable(cursor, [('70%', [], CReportBase.AlignLeft), ('10%', [], CReportBase.AlignLeft),
                                     ('20%', [], CReportBase.AlignCenter)], headerRowCount=4, border=0, cellPadding=2,
                            cellSpacing=0)

        table.mergeCells(0, 0, 4, 1)
        cursorAt = table.cursorAt(0, 0)
        tmpTable = createTable(cursorAt, [('70%', [], CReportBase.AlignCenter), ('30%', [], CReportBase.AlignCenter)],
                               headerRowCount=2, border=1, cellPadding=2, cellSpacing=0)
        tmpTable.setText(0, 0, u'Представляют')
        tmpTable.setText(0, 1, u'Сроки представления')
        tmpTable.setText(1, 0,
                         u'\n\nМедицинские организации, проводившие профилактические медицинские осмотры несовершеннолетних:\n\n- в орган исполнительной власти субъекта Российской Федерации в сфере здравоохранения\n\n\n Орган исполнительной власти субъекта Российской Федерации в сфере здравоохранения:\n\n - в Минздрав России\n\n',
                         blockFormat=bfAlignLeftTop)
        tmpTable.setText(1, 1, u'\n\n\nЕжегодно\n\nдо 20 января\n\n\nЕжегодно\n\nдо 15 февраля\n')
        cursorAt.insertBlock()
        cursorAt = table.cursorAt(0, 2)
        tmpTable = createTable(cursorAt, [('100%', [], CReportBase.AlignCenter)],
                               headerRowCount=1, border=2, cellPadding=2, cellSpacing=0)
        tmpTable.setText(0, 0, u'\nОтчетная форма № 030-ПО/о-17\n', CReportBase.TableHeader)

        cursorAt = table.cursorAt(0, 2)
        tmpTable = createTable(cursorAt, [('100%', [], CReportBase.AlignCenter)],
                               headerRowCount=1, border=0, cellPadding=2, cellSpacing=0)
        tmpTable.setText(0, 0, u'\nУтверждена приказом\nМинздрава России\nот "14" апреля 2025 г. № 211н\n')

        cursorAt = table.cursorAt(0, 2)
        tmpTable = createTable(cursorAt, [('100%', [], CReportBase.AlignCenter)],
                               headerRowCount=1, border=2, cellPadding=2, cellSpacing=0)
        tmpTable.setText(0, 0, u'Ежегодная')

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()
        cursor.insertBlock()

        table = createTable(cursor, [('100%', [], CReportBase.AlignLeft)], headerRowCount=2, border=2, cellPadding=2,
                            cellSpacing=0)

        orgRec = QtGui.qApp.db.getRecordEx('Organisation', 'fullName, Address, address_id', 'id=%d' % QtGui.qApp.currentOrgId())
        if orgRec:
            table.setHtml(0, 0,
                          u'Наименование отчитывающейся организации <u><b>%s</b></u>' % forceString(orgRec.value('fullName')))
            address_id = forceInt(orgRec.value('address_id'))
            table.setHtml(1, 0,
                          u'Почтовый адрес <u><b>%s</b></u>' % formatAddress(address_id) if address_id else forceString(
                              orgRec.value('Address')))

        cursor.movePosition(QtGui.QTextCursor.End)

        pageBreakBlockFormat = QtGui.QTextBlockFormat()
        pageBreakBlockFormat.setPageBreakPolicy(QtGui.QTextFormat.PageBreak_AlwaysBefore)
        cursor.insertBlock(pageBreakBlockFormat)
        cursor.insertBlock(QtGui.QTextBlockFormat())

    def produceSection1(self, cursor, sectionData):
        cursor.setCharFormat(CReportBase.ReportSubTitle)
        cursor.insertText(
            u'1. Число несовершеннолетних (далее - дети), подлежащих профилактическим осмотрам в отчетном периоде:')
        cursor.insertBlock()

        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()
        self.produceSection1_2(cursor, sectionData)

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()

    def produceSection2(self, cursor, sectionData):
        cursor.setCharFormat(CReportBase.ReportSubTitle)
        cursor.insertText(
            u'2. Число детей прошедших профилактические осмотры в отчетном периоде (от п. 1.):')
        cursor.insertBlock()

        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()
        self.produceSection1_2(cursor, sectionData)

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()

    def produceSection1_2(self, cursor, sectionData):
        for idx in range(len(sectionData)):
            cursor.insertText(sectionData[idx])
            cursor.insertBlock()

    def produceSection3(self, cursor, sectionData):
        cursor.setCharFormat(CReportBase.ReportSubTitle)
        cursor.insertText(
            u'3. Структура выявленных заболеваний (состояний) у детей в возрасте от 0 до 17 лет включительно')
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertText(u'Таблица 1000')
        cursor.insertBlock()
        tableColumns = [
            ('5%', [u'N п/п', u'', u'1'], CReportBase.AlignLeft),
            (
            '32%', [u'Наименование заболеваний (по классам и отдельным нозологиям)', u'', u'2'], CReportBase.AlignLeft),
            ('7%', [u'Код по МКБ', u'', u'3'], CReportBase.AlignCenter),
            ('7%', [u'Всего зарегистрировано заболеваний', u'', u'4'], CReportBase.AlignCenter),
            ('7%', [u'из них у мальчиков (из графы 4)', u'', u'5'], CReportBase.AlignCenter),
            ('7%', [u'Выявлено впервые (из графы 4)', u'', u'6'], CReportBase.AlignCenter),
            ('7%', [u'из них у мальчиков (из графы 6)', u'', u'7'], CReportBase.AlignCenter),
            ('7%', [u'Проводится диспансерное наблюдение на конец отчетного периода', u'Всего', u'8'],
             CReportBase.AlignCenter),
            ('7%', [u'', u'из них мальчиков (из графы 8)', u'9'], CReportBase.AlignCenter),
            ('7%', [u'', u'Взято по результатам данного осмотра (из графы 8)', u'10'], CReportBase.AlignCenter),
            ('7%', [u'', u'из них мальчиков (из графы 10)', u'11'], CReportBase.AlignCenter),
        ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 7, 1, 4)
        for idx in range(7):
            table.mergeCells(0, idx, 2, 1)

        offset = 3
        for idxRow, row in enumerate(sectionData):
            i = table.addRow()
            table.setText(i, 0, MKBRows[idxRow][1])
            table.setText(i, 1, MKBRows[idxRow][0])
            table.setText(i, 2, MKBRows[idxRow][2])
            for idx in xrange(offset, len(tableColumns)):
                table.setText(i, idx, row[idx - offset])

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()

    def produceSection4(self, cursor, sectionData):
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportSubTitle)
        cursor.insertText(
            u'4. Результаты дополнительных консультаций, исследований, лечения, медицинской реабилитации детей по результатам проведения профилактических осмотров:')
        cursor.insertBlock()
        cursor.insertBlock()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertText(u'4.1. Дополнительные консультации и (или) исследования')
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertText(u'Таблица 2000')
        cursor.insertBlock()
        tableColumns = [
            ('20%', [u'Возраст детей', u'1'], CReportBase.AlignLeft),
            ('20%', [
                u'Нуждались в дополнительных консультациях и (или) исследованиях в амбулаторных условиях и в условиях дневного стационара (человек)',
                u'2'], CReportBase.AlignCenter),
            ('20%', [
                u'Прошли дополнительные консультации и (или) исследования в амбулаторных условиях и в условиях дневного стационара (человек) (из графы 2)',
                u'3'], CReportBase.AlignCenter),
            ('20%',
             [u'Нуждались в дополнительных консультациях и (или) исследованиях в стационарных условиях (человек)',
              u'4'], CReportBase.AlignCenter),
            ('20%',
             [u'Прошли дополнительные консультации и (или) исследования в стационарных условиях (человек) (из графы 4)',
              u'5'], CReportBase.AlignCenter),
        ]
        table = createTable(cursor, tableColumns)
        for item in sectionData[0]:
            i = table.addRow()
            for idx in xrange(len(tableColumns)):
                table.setText(i, idx, item[idx])

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()

        cursor.setCharFormat(CReportBase.ReportSubTitle)
        cursor.insertText(u'4.2. Лечение, медицинская реабилитация и санаторно-курортное лечение')
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()
        cursor.insertText(u'Таблица 3000')
        cursor.insertBlock()
        tableColumns = [
            ('20%', [u'Возраст детей', u'1'], CReportBase.AlignLeft),
            ('16%', [u'Рекомендовано лечение в амбулаторных условиях и в условиях дневного стационара(человек)', u'2'],
             CReportBase.AlignCenter),
            ('16%', [u'Рекомендовано лечение в стационарных условиях (человек)', u'3'], CReportBase.AlignCenter),
            ('16%', [
                u'Рекомендована медицинская реабилитация в амбулаторных условиях и в условиях дневного стационара (человек)',
                u'4'], CReportBase.AlignCenter),
            ('16%', [u'Рекомендована медицинская реабилитация в стационарных условиях (человек)', u'5'],
             CReportBase.AlignCenter),
            ('16%', [u'Рекомендовано санаторно-курортное лечение (человек)', u'6'], CReportBase.AlignCenter),
        ]
        table = createTable(cursor, tableColumns)
        for item in sectionData[1]:
            i = table.addRow()
            for idx in xrange(len(tableColumns)):
                table.setText(i, idx, item[idx])

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()

    def produceSection5(self, cursor, sectionData):
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportSubTitle)
        cursor.insertText(u'5. Число детей по уровню физического развития')
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertText(u'Таблица 4000')
        cursor.insertBlock()
        tableColumns = [
            ('20%', [u'Возраст', u'', u'1'], CReportBase.AlignLeft),
            ('10%', [u'Число прошедших профилактические осмотры в отчетном периоде (человек)', u'', u'2'],
             CReportBase.AlignCenter),
            ('14%', [u'Нормальное физическое развитие (человек) (из графы 2)', u'', u'3'], CReportBase.AlignCenter),
            ('14%', [u'Нарушения физического развития (человек) (из графы 2)', u'дефицит массы тела', u'4'],
             CReportBase.AlignCenter),
            ('14%', [u'', u'избыток массы тела', u'5'], CReportBase.AlignCenter),
            ('14%', [u'', u'низкий рост', u'6'], CReportBase.AlignCenter),
            ('14%', [u'', u'высокий рост', u'7'], CReportBase.AlignCenter),
        ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 2, 1)
        table.mergeCells(0, 3, 1, 4)

        for item in sectionData:
            i = table.addRow()
            for idx in xrange(len(tableColumns)):
                table.setText(i, idx, item[idx])

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()

    def produceSection6(self, cursor, sectionData, sectionPrevData):
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportSubTitle)
        cursor.insertText(u'6. Распределение количества детей по отношению к медицинским группам для занятий физической культурой')
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertText(u'Таблица 5000')
        cursor.insertBlock()
        tableColumns = [
            ('20%', [u'Наименование показателя', u'', u'', u'1'], CReportBase.AlignLeft),
            ('10%', [u'Число прошедших профилактические осмотры в отчетном периоде (человек)', u'', u'', u'2'],
             CReportBase.AlignCenter),
            ('7%', [u'Медицинская группа для занятий физической культурой',
                    u'По результатам ранее проведенных медицинских осмотров (человек)', u'I', u'3'],
             CReportBase.AlignCenter),
            ('7%', [u'', u'', u'II', u'4'], CReportBase.AlignCenter),
            ('7%', [u'', u'', u'III', u'5'], CReportBase.AlignCenter),
            ('7%', [u'', u'', u'IV', u'6'], CReportBase.AlignCenter),
            ('7%', [u'', u'', u'не допущен', u'7'], CReportBase.AlignCenter),
            ('7%', [u'', u'По результатам профилактических осмотров в данном отчетном периоде (человек)', u'I', u'8'],
             CReportBase.AlignCenter),
            ('7%', [u'', u'', u'II', u'9'], CReportBase.AlignCenter),
            ('7%', [u'', u'', u'III', u'10'], CReportBase.AlignCenter),
            ('7%', [u'', u'', u'IV', u'11'], CReportBase.AlignCenter),
            ('7%', [u'', u'', u'не допущен', u'12'], CReportBase.AlignCenter),
        ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 3, 1)
        table.mergeCells(0, 1, 3, 1)
        table.mergeCells(0, 2, 1, 10)
        table.mergeCells(1, 2, 1, 5)
        table.mergeCells(1, 7, 1, 5)

        for idxItem, item in enumerate(sectionData):
            i = table.addRow()
            table.setText(i, 0, item[0])
            table.setText(i, 1, item[1])
            for idx in xrange(2, len(item)):
                table.setText(i, idx + 5, item[idx])
                if sectionPrevData:
                    table.setText(i, idx, sectionPrevData[idxItem][idx])

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()

    def produceSection7(self, cursor, sectionData, sectionPrevData):
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportSubTitle)
        cursor.insertText(u'7. Число детей по группам здоровья')
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertText(u'Таблица 6000')
        cursor.insertBlock()
        tableColumns = [
            ('20%', [u'Наименование показателя', u'', u'', u'1'], CReportBase.AlignLeft),
            ('10%', [u'Число прошедших профилактические осмотры в отчетном периоде (человек)', u'', u'', u'2'],
             CReportBase.AlignCenter),
            ('7%', [u'Группы здоровья', u'По результатам ранее проведенных медицинских осмотров (человек)', u'I', u'3'],
             CReportBase.AlignCenter),
            ('7%', [u'', u'', u'II', u'4'], CReportBase.AlignCenter),
            ('7%', [u'', u'', u'III', u'5'], CReportBase.AlignCenter),
            ('7%', [u'', u'', u'IV', u'6'], CReportBase.AlignCenter),
            ('7%', [u'', u'', u'V', u'7'], CReportBase.AlignCenter),
            ('7%', [u'', u'По результатам профилактических осмотров в данном отчетном периоде (человек)', u'I', u'8'],
             CReportBase.AlignCenter),
            ('7%', [u'', u'', u'II', u'9'], CReportBase.AlignCenter),
            ('7%', [u'', u'', u'III', u'10'], CReportBase.AlignCenter),
            ('7%', [u'', u'', u'IV', u'11'], CReportBase.AlignCenter),
            ('7%', [u'', u'', u'V', u'12'], CReportBase.AlignCenter),
        ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 3, 1)
        table.mergeCells(0, 1, 3, 1)
        table.mergeCells(0, 2, 1, 10)
        table.mergeCells(1, 2, 1, 5)
        table.mergeCells(1, 7, 1, 5)

        for idxItem, item in enumerate(sectionData):
            i = table.addRow()
            table.setText(i, 0, item[0])
            table.setText(i, 1, item[1])
            for idx in xrange(2, len(item)):
                table.setText(i, idx + 5, item[idx])
                if sectionPrevData:
                    table.setText(i, idx, sectionPrevData[idxItem][idx])

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()


class CReportPreventiveMinorsSetupDialog(QtGui.QDialog, Ui_ReportPreventiveMinorsSetupDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbEventPurpose.setTable('rbEventTypePurpose', True, filter='code != \'0\'')
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())
        self.eventTypeList = []

    def setTitle(self, title):
        self.setWindowTitle(title)

    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.edtPrevBegDate.setDate(params.get('begDateBeforeRecord', QDate.currentDate()))
        self.edtPrevEndDate.setDate(params.get('endDateBeforeRecord', QDate.currentDate()))
        self.cmbEventPurpose.setValue(params.get('eventPurposeId', None))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        self.cmbPerson.setValue(params.get('personId', None))
        self.cmbSex.setCurrentIndex(params.get('sex', 0))
        self.edtAgeFrom.setValue(params.get('ageFrom', 0))
        self.edtAgeTo.setValue(params.get('ageTo', 150))
        self.eventTypeList = params.get('eventTypeList', [])
        if self.eventTypeList:
            db = QtGui.qApp.db
            tableET = db.table('EventType')
            records = db.getRecordList(tableET, [tableET['name']],
                                       [tableET['deleted'].eq(0), tableET['id'].inlist(self.eventTypeList)])
            nameList = []
            for record in records:
                nameList.append(forceString(record.value('name')))
            self.lblEventTypeList.setText(u','.join(name for name in nameList if name))
        else:
            self.lblEventTypeList.setText(u'не задано')

    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['begDateBeforeRecord'] = self.edtPrevBegDate.date()
        result['endDateBeforeRecord'] = self.edtPrevEndDate.date()
        result['eventPurposeId'] = self.cmbEventPurpose.value()
        result['orgStructureId'] = self.cmbOrgStructure.value()
        result['personId'] = self.cmbPerson.value()
        result['sex'] = self.cmbSex.currentIndex()
        result['ageFrom'] = self.edtAgeFrom.value()
        result['ageTo'] = self.edtAgeTo.value()
        result['eventTypeList'] = self.eventTypeList
        return result

    @pyqtSignature('QDate')
    def on_edtBegDate_dateChanged(self, date):
        self.cmbPerson.setBegDate(date)

    @pyqtSignature('QDate')
    def on_edtEndDate_dateChanged(self, date):
        self.cmbPerson.setEndDate(date)

    @pyqtSignature('int')
    def on_cmbEventPurpose_currentIndexChanged(self, index):
        self.eventTypeList = []
        self.lblEventTypeList.setText(u'не задано')

    @pyqtSignature('int')
    def on_cmbOrgStructure_currentIndexChanged(self, index):
        orgStructureId = self.cmbOrgStructure.value()
        self.cmbPerson.setOrgStructureId(orgStructureId)

    @pyqtSignature('')
    def on_btnEventTypeList_clicked(self):
        self.eventTypeList = []
        self.lblEventTypeList.setText(u'не задано')
        eventPurposeId = self.cmbEventPurpose.value()
        if eventPurposeId:
            filter = u'EventType.purpose_id =%d' % eventPurposeId
        else:
            filter = getWorkEventTypeFilter(isApplyActive=True)
        dialog = CEventTypeListEditorDialog(self, filter)
        if dialog.exec_():
            self.eventTypeList = dialog.values()
            if self.eventTypeList:
                db = QtGui.qApp.db
                tableET = db.table('EventType')
                records = db.getRecordList(tableET, [tableET['name']],
                                           [tableET['deleted'].eq(0), tableET['id'].inlist(self.eventTypeList)])
                nameList = []
                for record in records:
                    nameList.append(forceString(record.value('name')))
                self.lblEventTypeList.setText(u','.join(name for name in nameList if name))
