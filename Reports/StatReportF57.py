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
from PyQt4.QtCore import QDate

from library.database   import addDateInRange
from library.MapCode    import createMapCodeToRowIdx, threeChar
from library.Utils      import forceBool, forceInt, forceString


from Reports.Report     import CReport, normalizeMKB
from Reports.ReportBase import CReportBase, createTable
from Reports.ReportAcuteInfections import CReportAcuteInfectionsSetupDialog
from Orgs.Utils         import getOrgStructureDescendants
from Reports.ReportView import CPageFormat
from Reports.ReportView import CPageFormat


MainRows = [
  (u'Всего,\nв том числе:', u'S00 - T98'),
  (u'поверхностные травмы', u'S00, S10, S20, S30, S40, S50, S60, S70, S80, S90, T00, T09.0, T11.0, T13.0, T14.0'),
  (u'открытые  раны, травмы кровеносных сосудов', u'S01, S09.0, S11, S15, S21, S25, S31, S35, S41, S45, S51, S55, S61, S65, S71, S75, S81, S85, S91, S95, T01, T06.3, T09.1, T11.1, T11.4, T13.1, T13.4, T14.1, T14.5'),
  (u'переломы черепа и лицевых костей', u'S02'),
  (u'травмы глаза  и глазницы', u'S05'),
  (u'внутричерепные травмы', u'S06'),
  (u'переломы костей верхней конечности', u'S42, S52, S62, T02.2, T02.4, T10'),
  (u'в том числе перелом нижнего конца лучевой кости, сочетанный перелом нижних концов локтевой и лучевой кости', u'S52.5, 6'),
  (u'переломы костей нижней конечности', u'S72, S82, S92, T02.3, T02.5, T12'),
  (u'в том числе перелом нижнего конца бедренной кости', u'S72.4'),
  (u'переломы позвоночника, костей туловища, других и неуточненных областей тела', u'S12, S22, S32, T02.0, T02.1, T02.7-9, T08, T14.2'),
  (u'вывихи, растяжения и перенапряжения капсульно-связочного аппарата суставов, травмы мышц и сухожилий', u'S03, S09.1, S13, S16, S23, S29.0, S33, S39.0, S43, S46, S53, S56, S63, S66, S73, S76, S83, S86, S93, S96, T03, T06.4, T09.2, T09.5, T11.2, T11.5, T13.2, T13.5, T14.3, T14.6'),
  (u'травмы нервов и спинного мозга', u'S04, S14, S24, S34, S44, S54, S64, S74, S84, S94, T06.0-T06.2, T09.3, T09.4, T11.3, T13.3, T14.4'),
  (u'размозжения (раздавливание), травматические ампутации', u'S07, S08, S17, S18, S28, S38, S47, S48, S57, S58, S67, S68, S77, S78, S87, S88, S97, S98, T04, T05, T09.6, T11.6, T13.6, T14.7'),
  (u'травмы внутренних органов грудной и брюшной областей, таза', u'S26, S27, S36, S37, S39.6-9, T06.5'),
  (u'термические и химические ожоги', u'T20 - T32'),
  (u'отравления лекарственными средствами, медикаментами и биологическими веществами, токсическое действие веществ, преимущественно немедицинского назначения', u'T36 - T65'),
  (u'осложнения хирургических и терапевтических вмешательств, не классифицированные в других рубриках', u'T80 - T88'),
  (u'последствия травм, отравлений, других воздействий внешних причин', u'T90 - T98'),
  (u'прочие', u'S09.2, 7-9, S19, S29.7 - 9, S49, S59, S69, S79, S89, S99, T02.6, T06.8, T07, T09.8 - 9, T11.8 - 9, T13.8 - 9, T14.8 - 9, T15 - T19, T33 - T35, T66 - T79'),
    ]


MainRowsNew = [
  (u'Всего, из них:', u'1',u'S00 - T98'),
  (u'трaвмы головы, всего', u'2', u'S00-S09'),
  (u'из них: перелом черепа и лицевых костей', u'3', u'S02'),
  (u'травма глаза и глазницы', u'4', u'S05'),
  (u'внутричерепная травма', u'5', u'S06'),
  (u'трaвмы шеи, всего', u'6', u'S10-S19'),
  (u'из них: перелом шейного отдела позвоночника', u'7', u'S12'),
  (u'травма нервов и спинного мозга на уровне шеи', u'8', u'S14'),
  (u'трaвмы грудной клетки, всего', u'9',  u'S20-S29'),
  (u'из них: перелом ребра (ребер), грудины и грудного отдела позвоночника ', u'10', u'S22'),
  (u'травма сердца', u'11', u'S26'),
  (u'травма других и неуточненных органов грудной полости', u'12', u'S27'),
  (u'трaвмы живота, нижней части спины, поясничного отдела позвоночника и таза, всего', u'13', u'S30-S39'),
  (u'из них: перелом пояснично-крестцового отдела позвоночника и костей таза', u'14', u'S32'),
  (u'травма органов брюшной полости', u'15', u'S36'),
  (u'травма тазовых органов', u'16', u'S37'),
  (u'трaвмы плечевого пояса и плеча, всего', u'17', u'S40-S49'),
  (u'из них: перелом на уровне плечевого пояса и плеча', u'18', u'S42'),
  (u'трaвмы локтя и предплечья, всего', u'19', u'S50-S59'),
  (u'из них: перелом костей предплечья', u'20', u'S52'),
  (u'трaвмы запястья и кисти, всего', u'21', u'S60-S69'),
  (u'из них: перелом на уровне запястья и кисти', u'22', u'S62'),
  (u'трaвмы области тазобедренного сустава и бедра, всего', u'23', u'S70-S79'),
  (u'из них: перелом бедренной кости', u'24', u'S72'),
  (u'трaвмы колена и голени, всего', u'25', u'S80-S89'),
  (u'из них: перелом костей голени, включая голеностопный сустав', u'26', u'S82'),
  (u'трaвмы области голеностопного сустава и стопы, всего', u'27', u'S90-S99'),
  (u'из них: перелом стопы, исключая перелом голеностопного сустава', u'28', u'S92'),
  (u'трaвмы, захватывающие несколько областей тела, всего', u'29', u'T00-T07'),
  (u'из них: переломы, захватывающие несколько областей тела', u'30', u'T02'),
  (u'трaвмы неуточненной части туловища, конечности или области тела', u'31', u'T08-T14'),
  (u'последствия проникновения инородного тела через естественные отверстия', u'32', u'T15-T19'),
  (u'термические и химические ожоги', u'33', u'T20-T32'),
  (u'отморожение', u'34', u'T33-T35 '),
  (u'отравление лекарственными средствами, медикаментами и биологическими веществами, всего', u'35', u'T36-T50'),
  (u'из них: отравление наркотиками', u'36', u'T40.0-6'),
  (u'отравление психотропными средствами', u'37', u'T43'),
  (u'токсическое действие веществ, преимущественно немедицинского назначения всего', u'38', u'T51-T65'),
  (u'из них: токсическое действие алкоголя', u'39', u'T51'),
  (u'другие и неуточненные эффекты воздействия внешних причин', u'40', u'T66-T78'),
  (u'осложнения хирургических и терaпевтических вмешaтельств', u'41', u'T80-T88'),
  (u'последствия трaвм, отрaвлений и других последствий внешних причин', u'42', u'T90-T98'),
    ]


def convCode(diagRange, posfix, diagList = []):
    diagLimits = diagRange.split('-')
    nDiagRange = len(diagLimits)
    posfixLimits = posfix.split('-')
    nPosfix = len(posfixLimits)

    if nDiagRange == 1 and diagLimits[0]:
        code = diagLimits[0]
        code = code.strip().upper()
        if threeChar.match(code):
            if nPosfix == 1:
                diagList.append(code + '.%s'%(posfixLimits[0]))
            elif nPosfix == 2:
                lowPosfix = int(posfixLimits[0])
                highPosfix = int(posfixLimits[1])
                for p in xrange(lowPosfix, highPosfix+1):
                    diagList.append(code + '.%s'%(str(p)))
    elif nDiagRange == 2:
        lowCode = diagLimits[0]
        highCode = diagLimits[1]
        lowCode = lowCode.strip().upper()
        highCode = highCode.strip().upper()
        assert  lowCode <= highCode
        if nPosfix == 1:
            if not threeChar.match(lowCode):
                lowCode = lowCode.split('.')[0]
            if not threeChar.match(highCode):
                highCode = highCode.split('.')[0]
            low  = int(lowCode[1:len(lowCode):1])
            high  = int(highCode[1:len(highCode):1])
            lowFirst = ord(lowCode[0])
            highFirst = ord(highCode[0])
            for d in xrange(lowFirst, highFirst+1):
                for i in xrange(low, high+1):
                    part1 = str(i)
                    diagList.append(chr(d) + ((u'0' + part1) if len(part1) == 1 else part1) + '.%s'%(posfixLimits[0]))
        elif nPosfix == 2:
            lowPosfix = int(posfixLimits[0])
            highPosfix = int(posfixLimits[1])
            if not threeChar.match(lowCode):
                lowCode = lowCode.split('.')[0]
            if not threeChar.match(highCode):
                highCode = highCode.split('.')[0]
            low  = int(lowCode[1:len(lowCode):1])
            high  = int(highCode[1:len(highCode):1])
            lowFirst = ord(lowCode[0])
            highFirst = ord(highCode[0])
            for d in xrange(lowFirst, highFirst+1):
                for i in xrange(low, high+1):
                    for p in xrange(lowPosfix, highPosfix+1):
                        part1 = str(i)
                        diagList.append(chr(d) + ((u'0' + part1) if len(part1) == 1 else part1) + '.%s'%str(p))
    else:
        assert False, 'Wrong codes range "'+diagRange+'"';
    return diagList


def convCodeList():
    diagRangeList = [(u'V01-V04', u'1'),
                     (u'V09',     u'2-3'),
                     (u'V10-V29', u'4-9'),
                     (u'V30-V38', u'5-9'),
                     (u'V39',     u'4-9'),
                     (u'V40-V48', u'5-9'),
                     (u'V49',     u'4-9'),
                     (u'V50-V58', u'5-9'),
                     (u'V59',     u'4-9'),
                     (u'V60-V68', u'5-9'),
                     (u'V69',     u'4-9'),
                     (u'V70-V78', u'5-9'),
                     (u'V79',     u'4-9'),
                     (u'V83-V86', u'0-3'),
                     (u'V87',     u'0-9'),
                     (u'V89',     u'2-3')
                     ]
    diagList = []
    for diagRange, posfix in diagRangeList:
        diagList = convCode(diagRange, posfix, diagList)
    diagList.extend([u'V06.1', u'V82.1', u'V82.9'])
    return u','.join(diag for diag in diagList)


MainRows_3500 = [
    (u'Случаи смерти от всех внешних причин', u'1', u'V01-Y98'),
    (u'из них: Несчастные случаи всего, из них:', u'2', u'V01-X59'),
    (u'транспортные', u'2.1 ', u'V01-V99'),
    (u'из них: дорожно-транспортные ', u'2.1.1', convCodeList()),
    (u'падения', u'2.2', u'W00-W19'),
    (u'утопление', u'2.3', u'W65-W74'),
    (u'с угрозой дыханию ', u'2.4', u'W75-W84'),
    (u'воздействие дыма, огня, пламени ', u'2.5', u'X00-X09'),
    (u'Самоубийства', u'3', u'X60-X84'),
    (u'Убийства', u'4', u'X85-Y09'),
    (u'Повреждения с неопределенными намерениями', u'5', u'Y10-Y34'),
    ]


HeaderCols = [
            ( u'Внешние причины заболеваемости и смертности, всего',                u'4',  u'V01-Y98'),
            (u'Транспортные несчастные случаи (V01-V99)',                           u'5',  u'V01-V99'),
            (u'из них: дорожно-транспортные несчастные случаи',                     u'6',  convCodeList()),
            (u'Другие внешние причины (W00 - X59)',                                 u'7',  u'W00-X59'),
            (u'из них: W00 - W19',                                                  u'8',  u'W00-W19'),
            (u'случайное утопление',                                                u'9',  u'W65-W74'),
            (u'воздействие дыма, огня и пламени',                                   u'10',  u'X00-X09'),
            (u'случайное отравление',                                               u'11', u'X40-X49'),
            (u'из гр.10: наркотиками',                                              u'12', u'X42'),
            (u'алкоголем',                                                          u'13', u'X45'),
            (u'Преднамеренное самоповреждение(X60-X84)',                            u'14', u'X60-X84'),
            (u'из них: наркотиками',                                                u'15', u'X62'),
            (u'алкоголем',                                                          u'16', u'X65'),
            (u'Нападение',                                                          u'17', u'X85-Y09'),
            (u'Повреждение с неопределенными намерениями',                          u'18', u'Y10-Y34'),
            (u'Действия, предусмотренные законом, военные операции и терроризм',    u'19', u'Y35-Y38'),
            (u'Осложнения терапевтических и хирургических вмешательств',            u'20', u'Y40-Y84'),
            (u'Последствия воздействия внешних причин заболеваемости и смертности', u'21', u'Y85-Y89'),
           ]


def selectData(params, isSeniors = False):
    stmt="""
SELECT
   COUNT(*) AS sickCount,
   Diagnosis.MKB AS MKB,
   Client.sex AS sex,
   rbTraumaType.code AS traumaType,
   (ADDDATE(Client.birthDate, INTERVAL 18 YEAR) <= Diagnosis.endDate) AS adult
FROM Diagnosis
LEFT JOIN Client ON Client.id = Diagnosis.client_id
LEFT JOIN rbDiagnosisType    ON rbDiagnosisType.id = Diagnosis.diagnosisType_id
LEFT JOIN rbDiseaseCharacter ON rbDiseaseCharacter.id = Diagnosis.character_id
LEFT JOIN rbTraumaType       ON rbTraumaType.id = Diagnosis.traumaType_id
WHERE
%s
GROUP BY MKB, sex, traumaType, adult
    """

    registeredInPeriod = params.get('registeredInPeriod', False)
    begDate            = params.get('begDate', QDate())
    endDate            = params.get('endDate', QDate())
    eventPurposeId     = params.get('eventPurposeId', None)
    eventTypeId        = params.get('eventTypeId', None)
    orgStructureId     = params.get('orgStructureId', None)
    personId           = params.get('personId', None)
    ageFrom            = params.get('ageFrom', 0)
    ageTo              = params.get('ageTo', 150)
    socStatusClassId   = params.get('socStatusClassId', None)
    socStatusTypeId    = params.get('socStatusTypeId', None)
    onlyFirstTime      = params.get('onlyFirstTime', False)
    notNullTraumaType  = params.get('notNullTraumaType', False)
    accountAccomp      = params.get('accountAccomp', False)
    locality           = params.get('locality', 0)
    isPersonPost       = params.get('isPersonPost', 0)

    db = QtGui.qApp.db
    tableDiagnosis  = db.table('Diagnosis')
    tableDiseaseCharacter = db.table('rbDiseaseCharacter')
    tableClient = db.table('Client')
    tableDiagnostic = db.table('Diagnostic')
    tablePerson = db.table('Person')
    tableDiagnosisType = db.table('rbDiagnosisType')

    cond = []
    cond.append(tableDiagnosis['deleted'].eq(0))
    cond.append(tableDiagnosis['mod_id'].isNull())

#    cond.append(tableDiagnosis['traumaType_id'].isNotNull())
    cond.append(tableDiagnosis['MKB'].gt('S'))
    cond.append(tableDiagnosis['MKB'].lt('U'))

#    cond.append(db.joinOr([tableDiagnosis['setDate'].isNull(), tableDiagnosis['setDate'].le(endDate)]))
#    cond.append(db.joinOr([tableDiagnosis['endDate'].ge(begDate), tableDiseaseCharacter['code'].eq('3')]))

    if onlyFirstTime:
        cond.append(tableDiagnosis['setDate'].le(endDate))
        cond.append(tableDiagnosis['setDate'].ge(begDate))
    else:
        cond.append(db.joinOr([tableDiagnosis['setDate'].isNull(), tableDiagnosis['setDate'].lt(endDate.addDays(1))]))
        cond.append(db.joinOr([tableDiagnosis['endDate'].ge(begDate), tableDiseaseCharacter['code'].eq('3')]))

    if notNullTraumaType:
        cond.append(tableDiagnosis['traumaType_id'].isNotNull())

    diagnosticQuery = tableDiagnostic
    diagnosticCond = [ tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']),
                       tableDiagnostic['deleted'].eq(0)
                     ]
    if registeredInPeriod:
        addDateInRange(diagnosticCond, tableDiagnostic['setDate'], begDate, endDate)
    if isPersonPost:
        tableRBPost = db.table('rbPost')
        diagnosticQuery = diagnosticQuery.innerJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
        diagnosticQuery = diagnosticQuery.innerJoin(tableRBPost, tableRBPost['id'].eq(tablePerson['post_id']))
        diagnosticCond.append(tablePerson['deleted'].eq(0))
        if isPersonPost == 1:
            diagnosticCond.append('''LEFT(rbPost.code, 1) IN ('1','2','3') ''')
        elif isPersonPost == 2:
            diagnosticCond.append('''LEFT(rbPost.code, 1) IN ('4','5','6','7','8','9')''')
    if personId:
        diagnosticCond.append(tableDiagnostic['person_id'].eq(personId))
    elif orgStructureId:
        if not isPersonPost:
            diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
            diagnosticCond.append(tablePerson['deleted'].eq(0))
        diagnosticCond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureDescendants(orgStructureId)))
    else:
        if not isPersonPost:
            diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
            diagnosticCond.append(tablePerson['deleted'].eq(0))
        diagnosticCond.append(tablePerson['org_id'].eq(QtGui.qApp.currentOrgId()))
    if eventTypeId:
        tableEvent = db.table('Event')
        diagnosticQuery = diagnosticQuery.leftJoin(tableEvent, tableEvent['id'].eq(tableDiagnostic['event_id']))
        diagnosticCond.append(tableEvent['eventType_id'].eq(eventTypeId))
    elif eventPurposeId:
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        diagnosticQuery = diagnosticQuery.leftJoin(tableEvent, tableEvent['id'].eq(tableDiagnostic['event_id']))
        diagnosticQuery = diagnosticQuery.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
        diagnosticCond.append(tableEventType['purpose_id'].eq(eventPurposeId))
    cond.append(db.existsStmt(diagnosticQuery, diagnosticCond))

#    if sex:
#        cond.append(tableClient['sex'].eq(sex))
    if ageFrom <= ageTo:
        if isSeniors:
            cond.append('Diagnosis.endDate >= ADDDATE(Client.birthDate, INTERVAL IF(Client.sex = 2 AND %d < 55, 55, IF(Client.sex = 1 AND %d < 60, 60, %d)) YEAR)'%(ageFrom, ageFrom, ageFrom))
            cond.append(tableClient['sex'].ne(0))
            cond.append('Diagnosis.endDate < SUBDATE(ADDDATE(Client.birthDate, INTERVAL %d YEAR),1)'%(ageTo+1))
        else:
            cond.append('Diagnosis.endDate >= ADDDATE(Client.birthDate, INTERVAL %d YEAR)'%ageFrom)
            cond.append('Diagnosis.endDate < SUBDATE(ADDDATE(Client.birthDate, INTERVAL %d YEAR),1)'%(ageTo+1))
    if socStatusTypeId:
        subStmt = ('SELECT ClientSocStatus.id FROM ClientSocStatus WHERE '
                  +'ClientSocStatus.deleted=0 AND ClientSocStatus.client_id=Client.id AND '
                  +'ClientSocStatus.socStatusType_id=%d' % socStatusTypeId)
        cond.append('EXISTS('+subStmt+')')
    elif socStatusClassId:
        subStmt = ('SELECT ClientSocStatus.id FROM ClientSocStatus WHERE '
                  +'ClientSocStatus.deleted=0 AND ClientSocStatus.client_id=Client.id AND '
                  +'ClientSocStatus.socStatusClass_id=%d' % socStatusClassId)
        cond.append('EXISTS('+subStmt+')')
    if not accountAccomp:
        cond.append(tableDiagnosisType['code'].inlist(['1', '2', '4']))
    if locality:
        # 1: горожане, isClientVillager == 0 или NULL
        # 2: сельские жители, isClientVillager == 1
        cond.append('IFNULL(isClientVillager(Client.id), 0) = %d' % (locality-1))
    return db.query(stmt % db.joinAnd(cond))


def selectDataNew(params, isSeniors = False):
    stmt="""
SELECT
   COUNT(*) AS sickCount,
   Diagnosis.MKB AS MKB,
   Diagnosis.MKBEx AS MKBEx,
   rbTraumaType.code AS traumaType
FROM Diagnosis
LEFT JOIN Client ON Client.id = Diagnosis.client_id
LEFT JOIN rbDiagnosisType    ON rbDiagnosisType.id = Diagnosis.diagnosisType_id
LEFT JOIN rbDiseaseCharacter ON rbDiseaseCharacter.id = Diagnosis.character_id
LEFT JOIN rbTraumaType       ON rbTraumaType.id = Diagnosis.traumaType_id
WHERE
%s
GROUP BY MKB, MKBEx, traumaType
    """

    registeredInPeriod = params.get('registeredInPeriod', False)
    begDate            = params.get('begDate', QDate())
    endDate            = params.get('endDate', QDate())
    eventPurposeId     = params.get('eventPurposeId', None)
    eventTypeId        = params.get('eventTypeId', None)
    orgStructureId     = params.get('orgStructureId', None)
    personId           = params.get('personId', None)
    sex                = params.get('sex', 0)
    ageFrom            = params.get('ageFrom', 0)
    ageTo              = params.get('ageTo', 150)
    socStatusClassId   = params.get('socStatusClassId', None)
    socStatusTypeId    = params.get('socStatusTypeId', None)
    onlyFirstTime      = params.get('onlyFirstTime', False)
    notNullTraumaType  = params.get('notNullTraumaType', False)
    accountAccomp      = params.get('accountAccomp', False)
    locality           = params.get('locality', 0)
    isPersonPost       = params.get('isPersonPost', 0)

    db = QtGui.qApp.db
    tableDiagnosis  = db.table('Diagnosis')
    tableDiseaseCharacter = db.table('rbDiseaseCharacter')
    tableClient = db.table('Client')
    tableDiagnostic = db.table('Diagnostic')
    tablePerson = db.table('Person')
    tableDiagnosisType = db.table('rbDiagnosisType')

    cond = []
    cond.append(tableDiagnosis['deleted'].eq(0))
    cond.append(tableDiagnosis['mod_id'].isNull())

#    cond.append(tableDiagnosis['traumaType_id'].isNotNull())
    cond.append(tableDiagnosis['MKB'].gt('S'))
    cond.append(tableDiagnosis['MKB'].lt('U'))

#    cond.append(db.joinOr([tableDiagnosis['setDate'].isNull(), tableDiagnosis['setDate'].le(endDate)]))
#    cond.append(db.joinOr([tableDiagnosis['endDate'].ge(begDate), tableDiseaseCharacter['code'].eq('3')]))

    if onlyFirstTime:
        cond.append(tableDiagnosis['setDate'].le(endDate))
        cond.append(tableDiagnosis['setDate'].ge(begDate))
    else:
        cond.append(db.joinOr([tableDiagnosis['setDate'].isNull(), tableDiagnosis['setDate'].lt(endDate.addDays(1))]))
        cond.append(db.joinOr([tableDiagnosis['endDate'].ge(begDate), tableDiseaseCharacter['code'].eq('3')]))

    if notNullTraumaType:
        cond.append(tableDiagnosis['traumaType_id'].isNotNull())

    diagnosticQuery = tableDiagnostic
    diagnosticCond = [ tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']),
                       tableDiagnostic['deleted'].eq(0)
                     ]
    if registeredInPeriod:
        addDateInRange(diagnosticCond, tableDiagnostic['setDate'], begDate, endDate)
    if isPersonPost:
        tableRBPost = db.table('rbPost')
        diagnosticQuery = diagnosticQuery.innerJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
        diagnosticQuery = diagnosticQuery.innerJoin(tableRBPost, tableRBPost['id'].eq(tablePerson['post_id']))
        diagnosticCond.append(tablePerson['deleted'].eq(0))
        if isPersonPost == 1:
            diagnosticCond.append('''LEFT(rbPost.code, 1) IN ('1','2','3') ''')
        elif isPersonPost == 2:
            diagnosticCond.append('''LEFT(rbPost.code, 1) IN ('4','5','6','7','8','9')''')
    if personId:
        diagnosticCond.append(tableDiagnostic['person_id'].eq(personId))
    elif orgStructureId:
        if not isPersonPost:
            diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
            diagnosticCond.append(tablePerson['deleted'].eq(0))
        diagnosticCond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureDescendants(orgStructureId)))
    else:
        if not isPersonPost:
            diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
            diagnosticCond.append(tablePerson['deleted'].eq(0))
        diagnosticCond.append(tablePerson['org_id'].eq(QtGui.qApp.currentOrgId()))
    if eventTypeId:
        tableEvent = db.table('Event')
        diagnosticQuery = diagnosticQuery.leftJoin(tableEvent, tableEvent['id'].eq(tableDiagnostic['event_id']))
        diagnosticCond.append(tableEvent['eventType_id'].eq(eventTypeId))
    elif eventPurposeId:
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        diagnosticQuery = diagnosticQuery.leftJoin(tableEvent, tableEvent['id'].eq(tableDiagnostic['event_id']))
        diagnosticQuery = diagnosticQuery.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
        diagnosticCond.append(tableEventType['purpose_id'].eq(eventPurposeId))
    cond.append(db.existsStmt(diagnosticQuery, diagnosticCond))
    if sex:
        cond.append(tableClient['sex'].eq(sex))
    if ageFrom <= ageTo:
        if isSeniors:
            cond.append('Diagnosis.endDate >= ADDDATE(Client.birthDate, INTERVAL IF(Client.sex = 2 AND %d < 55, 55, IF(Client.sex = 1 AND %d < 60, 60, %d)) YEAR)'%(ageFrom, ageFrom, ageFrom))
            cond.append(tableClient['sex'].ne(0))
            cond.append('Diagnosis.endDate < SUBDATE(ADDDATE(Client.birthDate, INTERVAL %d YEAR),1)'%(ageTo+1))
        else:
            cond.append('Diagnosis.endDate >= ADDDATE(Client.birthDate, INTERVAL %d YEAR)'%ageFrom)
            cond.append('Diagnosis.endDate < SUBDATE(ADDDATE(Client.birthDate, INTERVAL %d YEAR),1)'%(ageTo+1))
    if socStatusTypeId:
        subStmt = ('SELECT ClientSocStatus.id FROM ClientSocStatus WHERE '
                  +'ClientSocStatus.deleted=0 AND ClientSocStatus.client_id=Client.id AND '
                  +'ClientSocStatus.socStatusType_id=%d' % socStatusTypeId)
        cond.append('EXISTS('+subStmt+')')
    elif socStatusClassId:
        subStmt = ('SELECT ClientSocStatus.id FROM ClientSocStatus WHERE '
                  +'ClientSocStatus.deleted=0 AND ClientSocStatus.client_id=Client.id AND '
                  +'ClientSocStatus.socStatusClass_id=%d' % socStatusClassId)
        cond.append('EXISTS('+subStmt+')')
    if not accountAccomp:
        cond.append(tableDiagnosisType['code'].inlist(['1', '2', '4']))
    if locality:
        # 1: горожане, isClientVillager == 0 или NULL
        # 2: сельские жители, isClientVillager == 1
        cond.append('IFNULL(isClientVillager(Client.id), 0) = %d' % (locality-1))
    return db.query(stmt % db.joinAnd(cond))


def selectData3500(params):
    stmt="""
SELECT
   COUNT(*) AS sickCount,
   Diagnosis.MKB AS MKB,
   Diagnosis.MKBEx AS MKBEx,
   rbTraumaType.code AS traumaType,
   Client.sex,
   age(Client.birthDate, Diagnosis.endDate) AS clientAge
FROM Diagnosis
LEFT JOIN Client ON Client.id = Diagnosis.client_id
LEFT JOIN rbDiagnosisType    ON rbDiagnosisType.id = Diagnosis.diagnosisType_id
LEFT JOIN rbDiseaseCharacter ON rbDiseaseCharacter.id = Diagnosis.character_id
LEFT JOIN rbTraumaType       ON rbTraumaType.id = Diagnosis.traumaType_id
WHERE
%s
GROUP BY MKB, MKBEx, traumaType, sex, clientAge
    """
    registeredInPeriod = params.get('registeredInPeriod', False)
    begDate            = params.get('begDate', QDate())
    endDate            = params.get('endDate', QDate())
    eventPurposeId     = params.get('eventPurposeId', None)
    eventTypeId        = params.get('eventTypeId', None)
    orgStructureId     = params.get('orgStructureId', None)
    personId           = params.get('personId', None)
    sex                = params.get('sex', 0)
    ageFrom            = params.get('ageFrom', 0)
    ageTo              = params.get('ageTo', 150)
    socStatusClassId   = params.get('socStatusClassId', None)
    socStatusTypeId    = params.get('socStatusTypeId', None)
    onlyFirstTime      = params.get('onlyFirstTime', False)
    notNullTraumaType  = params.get('notNullTraumaType', False)
    accountAccomp      = params.get('accountAccomp', False)
    locality           = params.get('locality', 0)
    isPersonPost       = params.get('isPersonPost', 0)

    db = QtGui.qApp.db
    tableDiagnosis  = db.table('Diagnosis')
    tableDiseaseCharacter = db.table('rbDiseaseCharacter')
    tableClient = db.table('Client')
    tableDiagnostic = db.table('Diagnostic')
    tablePerson = db.table('Person')
    tableDiagnosisType = db.table('rbDiagnosisType')

    cond = [tableClient['deleted'].eq(0),
            u'''EXISTS(SELECT Event.id
                FROM Event
                INNER JOIN Diagnostic ON Diagnostic.event_id = Event.id
                INNER JOIN EventType ON EventType.id = Event.eventType_id
                INNER JOIN rbEventTypePurpose ON rbEventTypePurpose.id = EventType.purpose_id
                WHERE
                Event.client_id = Diagnosis.client_id AND Diagnostic.diagnosis_id = Diagnosis.id
                AND Event.deleted = 0 AND EventType.deleted = 0 AND Diagnostic.deleted = 0
                AND rbEventTypePurpose.code = 5 AND (EventType.code = 15 OR EventType.code = 23)
                )'''
            ]
    cond.append(tableDiagnosis['deleted'].eq(0))
    cond.append(tableDiagnosis['mod_id'].isNull())

    cond.append(tableDiagnosis['MKB'].gt('S'))
    cond.append(tableDiagnosis['MKB'].lt('U'))

    if onlyFirstTime:
        cond.append(tableDiagnosis['setDate'].le(endDate))
        cond.append(tableDiagnosis['setDate'].ge(begDate))
    else:
        cond.append(db.joinOr([tableDiagnosis['setDate'].isNull(), tableDiagnosis['setDate'].lt(endDate.addDays(1))]))
        cond.append(db.joinOr([tableDiagnosis['endDate'].ge(begDate), tableDiseaseCharacter['code'].eq('3')]))

    if notNullTraumaType:
        cond.append(tableDiagnosis['traumaType_id'].isNotNull())

    diagnosticQuery = tableDiagnostic
    diagnosticCond = [ tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']),
                       tableDiagnostic['deleted'].eq(0)
                     ]
    if registeredInPeriod:
        addDateInRange(diagnosticCond, tableDiagnostic['setDate'], begDate, endDate)
    if isPersonPost:
        tableRBPost = db.table('rbPost')
        diagnosticQuery = diagnosticQuery.innerJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
        diagnosticQuery = diagnosticQuery.innerJoin(tableRBPost, tableRBPost['id'].eq(tablePerson['post_id']))
        diagnosticCond.append(tablePerson['deleted'].eq(0))
        if isPersonPost == 1:
            diagnosticCond.append('''LEFT(rbPost.code, 1) IN ('1','2','3') ''')
        elif isPersonPost == 2:
            diagnosticCond.append('''LEFT(rbPost.code, 1) IN ('4','5','6','7','8','9')''')
    if personId:
        diagnosticCond.append(tableDiagnostic['person_id'].eq(personId))
    elif orgStructureId:
        if not isPersonPost:
            diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
            diagnosticCond.append(tablePerson['deleted'].eq(0))
        diagnosticCond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureDescendants(orgStructureId)))
    else:
        if not isPersonPost:
            diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
            diagnosticCond.append(tablePerson['deleted'].eq(0))
        diagnosticCond.append(tablePerson['org_id'].eq(QtGui.qApp.currentOrgId()))
    if eventTypeId:
        tableEvent = db.table('Event')
        diagnosticQuery = diagnosticQuery.leftJoin(tableEvent, tableEvent['id'].eq(tableDiagnostic['event_id']))
        diagnosticCond.append(tableEvent['eventType_id'].eq(eventTypeId))
    elif eventPurposeId:
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        diagnosticQuery = diagnosticQuery.leftJoin(tableEvent, tableEvent['id'].eq(tableDiagnostic['event_id']))
        diagnosticQuery = diagnosticQuery.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
        diagnosticCond.append(tableEventType['purpose_id'].eq(eventPurposeId))
    cond.append(db.existsStmt(diagnosticQuery, diagnosticCond))
    if sex:
        cond.append(tableClient['sex'].eq(sex))
    if ageFrom <= ageTo:
        cond.append('Diagnosis.endDate >= ADDDATE(Client.birthDate, INTERVAL %d YEAR)'%ageFrom)
        cond.append('Diagnosis.endDate < SUBDATE(ADDDATE(Client.birthDate, INTERVAL %d YEAR),1)'%(ageTo+1))
    if socStatusTypeId:
        subStmt = ('SELECT ClientSocStatus.id FROM ClientSocStatus WHERE '
                  +'ClientSocStatus.deleted=0 AND ClientSocStatus.client_id=Client.id AND '
                  +'ClientSocStatus.socStatusType_id=%d' % socStatusTypeId)
        cond.append('EXISTS('+subStmt+')')
    elif socStatusClassId:
        subStmt = ('SELECT ClientSocStatus.id FROM ClientSocStatus WHERE '
                  +'ClientSocStatus.deleted=0 AND ClientSocStatus.client_id=Client.id AND '
                  +'ClientSocStatus.socStatusClass_id=%d' % socStatusClassId)
        cond.append('EXISTS('+subStmt+')')
    if not accountAccomp:
        cond.append(tableDiagnosisType['code'].inlist(['1', '2', '4']))
    if locality:
        # 1: горожане, isClientVillager == 0 или NULL
        # 2: сельские жители, isClientVillager == 1
        cond.append('IFNULL(isClientVillager(Client.id), 0) = %d' % (locality-1))
    return db.query(stmt % db.joinAnd(cond))


mapAdultTraumaTypeToColumns = {
'01' : [0, 11, 20],    # Промышленная
'04' : [1, 11, 20],    # Сельскохозяйственная
'02' : [4, 11, 20],    # Строительная
'03' : [2, 3, 11, 20], # Дорожно-транспортная
'05' : [4, 11, 20],    # Прочая
'06' : [5, 11, 20],    # Бытовая
'07' : [6, 11, 20],    # Уличная
'08' : [7, 8, 11, 20], # Дорожно-транспортная
#9 Школьная
'10' : [9, 11, 20],     # Спортивная
'12' : [11, 20, 21, 22],# Т.а.
'11' : [10, 11, 20],    # Прочая не Пр.
''   : [11, 20]         # Всего + Прочая ост.
}

mapChildTraumaTypeToColumns = {
'06' : [12, 19, 20],    # Бытовая
'07' : [13, 19, 20],    # Уличная
'03' : [14, 15, 19, 20],# Дорожно-транспортная
'08' : [14, 15, 19, 20],# Дорожно-транспортная
'09' : [16, 19, 20],    # Школьная
'10' : [17, 19, 20],     # Спортивная
'12' : [19, 20, 21, 23], # Т.а.
''   : [18, 19, 20]     # Прочая
}

# столбики -
# взрослые
# 0 в промышленности
# 1 в с/х
# 2 транспортные - всего
# 3 транспортные - в т.ч. а/дор
# 4 прочие
# 5 бытовые
# 6 уличные
# 7 транспортные - всего
# 8 транспортные - в т.ч. а/дор
# 9 спортивные
#10  прочие
#11  итого
# дети и подростки
#12 бытовые
#13 уличные
#14 транспортные - всего
#15 транспортные - в т.ч. а/дор
#16 школьные
#17 спортивные
#18 прочие
#19 итого
#20 всего
#21 т.а.
#22 т.а. - взрослые
#23 т.а. - дети


class CStatReportF57(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Сведения о травмах, отравлениях и др. (Ф57)')


    def getDefaultParams(self):
        result = CReport.getDefaultParams(self)
        result['onlyFirstTime'] = True
        result['notNullTraumaType'] = False
        return result


    def getSetupDialog(self, parent):
        result = CReportAcuteInfectionsSetupDialog(parent)
        result.setMKBFilterEnabled(False)
        result.setAccountAccompEnabled(True)
        result.setOnlyFirstTimeEnabled(True)
        result.setNotNullTraumaTypeEnabled(True)
        result.setTitle(self.title())
        return result


    def build(self, params):
        mapMainRows = createMapCodeToRowIdx( [row[1] for row in MainRows if row[1]] )
        rowSize = 24
        reportMainData = [ [0]*rowSize for row in xrange(len(MainRows)*2) ]
        query = selectData(params)
        while query.next():
            record   = query.record()
            sickCount = forceInt(record.value('sickCount'))
            MKB   = normalizeMKB(forceString(record.value('MKB')))
            sex   = forceInt(record.value('sex'))
            adult = forceBool(record.value('adult'))
            traumaType  = forceString(record.value('traumaType'))
            mapTraumaTypeToColumns = mapAdultTraumaTypeToColumns if adult else mapChildTraumaTypeToColumns
            columns = mapTraumaTypeToColumns.get(traumaType, None)
            if not columns:
                columns = mapTraumaTypeToColumns['']
                mapTraumaTypeToColumns[traumaType] = columns
            baseIndex = (0 if sex == 1 else 1)
            rows = mapMainRows.get(MKB, [])
            for row in rows:
                reportLine = reportMainData[baseIndex+row*2]
                for column in columns:
                    reportLine[column] += sickCount
        # now text
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
#        cursor.setCharFormat(CReportBase.ReportTitle)
#        cursor.insertText(u'Сведения о травмах, отравлениях и некоторых других последствиях воздействия внешних причин (Ф57)')
#        cursor.insertBlock()
#        cursor.setCharFormat(CReportBase.ReportBody)
#        cursor.insertText(u'за период с %s по %s' % (forceString(begDate), forceString(endDate)))
#        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        tableColumns = [
            ('15%', [u'Травмы, отравления и некоторые другие последствия воздействия внешних причин',            u'', u'', u'',       u'1' ], CReportBase.AlignLeft),
            ('15%', [u'Код по МКБ X',                               u'',                             u'',                  u'',       u'2' ], CReportBase.AlignLeft),
            ( '3%', [u'Пол',                                        u'',                             u'',                  u'',       u'3' ], CReportBase.AlignCenter),
            ( '3%', [u'№ стр.',                                     u'',                             u'',                  u'',       u'4' ], CReportBase.AlignRight),
            ( '3%', [u'У взрослых (18 лет и старше)',               u'связанные с производством',    u'пром',              u'',       u'5' ], CReportBase.AlignRight),
            ( '3%', [u'',                                           u'',                             u'с/х',               u'',       u'6' ], CReportBase.AlignRight),
            ( '3%', [u'',                                           u'',                             u'трансп.',           u'вс',     u'7' ], CReportBase.AlignRight),
            ( '3%', [u'',                                           u'',                             u'',                  u'авт',    u'8' ], CReportBase.AlignRight),
            ( '3%', [u'',                                           u'',                             u'пр',                u'',       u'9' ], CReportBase.AlignRight),
            ( '3%', [u'',                                           u'быт',                          u'',                  u'',       u'10'], CReportBase.AlignRight),
            ( '3%', [u'',                                           u'не связанные с производством', u'ул',                u'',       u'11'], CReportBase.AlignRight),
            ( '3%', [u'',                                           u'',                             u'трансп.',           u'вс',     u'12'], CReportBase.AlignRight),
            ( '3%', [u'',                                           u'',                             u'',                  u'авт',    u'13'], CReportBase.AlignRight),
            ( '3%', [u'',                                           u'',                             u'спорт',             u'',       u'14'], CReportBase.AlignRight),
            ( '3%', [u'',                                           u'',                             u'пр',                u'',       u'15'], CReportBase.AlignRight),
            ( '3%', [u'',                                           u'ИТОГО',                        u'',                  u'',       u'16'], CReportBase.AlignRight),
            ( '3%', [u'У детей (0 - 17 лет включительно)',          u'быт',                          u'',                  u'',       u'17'], CReportBase.AlignRight),
            ( '3%', [u'',                                           u'ул',                           u'',                  u'',       u'18'], CReportBase.AlignRight),
            ( '3%', [u'',                                           u'трансп.',                      u'вс',                u'',       u'19'], CReportBase.AlignRight),
            ( '3%', [u'',                                           u'',                             u'авт',               u'',       u'20'], CReportBase.AlignRight),
            ( '3%', [u'',                                           u'шк',                           u'',                  u'',       u'21'], CReportBase.AlignRight),
            ( '3%', [u'',                                           u'спорт',                        u'',                  u'',       u'22'], CReportBase.AlignRight),
            ( '3%', [u'',                                           u'пр',                           u'',                  u'',       u'23'], CReportBase.AlignRight),
            ( '3%', [u'',                                           u'ИТОГО',                        u'',                  u'',       u'24'], CReportBase.AlignRight),
            ( '3%', [u'ВСЕГО',                                      u'',                             u'',                  u'',       u'25'], CReportBase.AlignRight),
            ( '3%', [u'Из гр.25',                                   u'в рез. терр. дей-\nствий',     u'',                  u'',       u'26'], CReportBase.AlignRight),
            ( '3%', [u'Из гр.26',                                   u'у взро-\nслых',                u'',                  u'',       u'27'], CReportBase.AlignRight),
            ( '3%', [u'',                                           u'у детей',                      u'',                  u'',       u'28'], CReportBase.AlignRight),
            ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 4, 1) # п.н.
        table.mergeCells(0, 1, 4, 1) # мкб
        table.mergeCells(0, 2, 4, 1) # пол
        table.mergeCells(0, 3, 4, 1) # N
        table.mergeCells(0, 4, 1,12) # взрослые
        table.mergeCells(1, 4, 1, 5) # произв.
        table.mergeCells(2, 4, 2, 1) # пром
        table.mergeCells(2, 5, 2, 1) # сх
        table.mergeCells(2, 6, 1, 2) # тр
        table.mergeCells(2, 8, 2, 1) # проч
        table.mergeCells(1, 9, 3, 1) # быт
        table.mergeCells(1,10, 1, 5) # непроизв.
        table.mergeCells(2,10, 2, 1) # ул
        table.mergeCells(2,11, 1, 2) # тр
        table.mergeCells(2,13, 2, 1) # сп
        table.mergeCells(2,14, 2, 1) # пр
        table.mergeCells(1,15, 3, 1) # итого
        table.mergeCells(0,16, 1, 8) # дети
        table.mergeCells(1,16, 3, 1) # быт
        table.mergeCells(1,17, 3, 1) # ул
        table.mergeCells(1,18, 1, 2) # трансп
        table.mergeCells(2,18, 2, 1) # всего
        table.mergeCells(2,19, 2, 1) # авт
        table.mergeCells(1,20, 3, 1) # шк
        table.mergeCells(1,21, 3, 1) # сп
        table.mergeCells(1,22, 3, 1) # пр
        table.mergeCells(1,23, 3, 1) # итого
        table.mergeCells(0,24, 4, 1) # ВСЕГО
        table.mergeCells(1,25, 3, 1) # т.а.
        table.mergeCells(0,26, 1, 2) # т.а. - по возр.
        table.mergeCells(1,26, 3, 1) # т.а. - взрослые
        table.mergeCells(1,27, 3, 1) # т.а. - дети
        for row, rowDescr in enumerate(MainRows):
            man   = table.addRow()
            woman = table.addRow()
            table.setText(man, 0, rowDescr[0])
            table.setText(man, 1, rowDescr[1])
            table.mergeCells(man, 0, 2, 1) # п.н.
            table.mergeCells(man, 1, 2, 1) # мкб
            table.setText(man,   2, u'М')
            table.setText(man,   3, row*2+1)
            reportLine = reportMainData[row*2]
            for column in xrange(rowSize):
                table.setText(man, 4+column, reportLine[column])
            table.setText(woman,   2, u'Ж')
            table.setText(woman,   3, row*2+2)
            reportLine = reportMainData[row*2+1]
            for column in xrange(rowSize):
                table.setText(woman, 4+column, reportLine[column])
        return doc


class CStatReportF57_1000(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'1000. Травмы по характеру и соответствующие им внешние причины у детей (0 - 17 лет включительно). (Ф57)')
        self.pageFormat = CPageFormat(pageSize=CPageFormat.A4, orientation=CPageFormat.Landscape)


    def getDefaultParams(self):
        result = CReport.getDefaultParams(self)
        result['onlyFirstTime'] = True
        result['notNullTraumaType'] = False
        result['ageFrom'] = 0
        result['ageTo'] = 17
        return result


    def getSetupDialog(self, parent):
        result = CReportAcuteInfectionsSetupDialog(parent)
        result.setAGE(0, 17)
        result.setMKBFilterEnabled(False)
        result.setAccountAccompEnabled(True)
        result.setOnlyFirstTimeEnabled(True)
        result.setNotNullTraumaTypeEnabled(True)
        result.setTitle(self.title())
        return result


    def build(self, params):
        mapMainRows = createMapCodeToRowIdx( [row[2] for row in MainRowsNew] )
        rowSize = 18
        reportMainData = [ [0]*rowSize for row in xrange(len(MainRowsNew)) ]
        mapHeaderCols = createMapCodeToRowIdx( [row[2] for row in HeaderCols] )
#        reportHeaderData = [ 0 for row in xrange(len(HeaderCols)) ]

        query = selectDataNew(params)
        while query.next():
            record   = query.record()
            sickCount = forceInt(record.value('sickCount'))
            MKB   = normalizeMKB(forceString(record.value('MKB')))
            MKBEx = normalizeMKB(forceString(record.value('MKBEx')))
            columns = mapHeaderCols.get(MKBEx, [])
            rows = mapMainRows.get(MKB, [])
            for row in rows:
                reportLine = reportMainData[row]
                for column in columns:
                    reportLine[column] += sickCount

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertText('(1000)')
        tableColumns = [
            ('12.5%', [u'Травмы, отрав-\nления и некоторые другие\n последствия воздействия\n внешних причин\n(Класс XIX МКБ-10)',u'',                                                                u'',                                               u'',                                 u'',        u'1' ], CReportBase.AlignLeft),
            ('7.5%',  [u'Код по МКБ-10',                                                                                  u'',                                                                        u'',                                               u'',                                 u'',        u'2' ], CReportBase.AlignLeft),
            ( '4.5%', [u'N строки',                                                                                       u'',                                                                        u'',                                               u'',                                 u'',        u'3' ], CReportBase.AlignRight),
            ( '4.5%', [u'Внешние причины-\n заболеваемости и смертности\n(Класс XX МКБ-10)',                              u'Внешние причины за-\nболеваемости и смерт-\nности, всего',                u'',                                               u'',                                 u'V01-Y98', u'4'], CReportBase.AlignRight),
            ( '4.5%', [u'',                                                                                               u'Транспортные несча-\nстные случаи (V01-V99)',                             u'Всего',                                          u'',                                 u'V01-V99', u'5'], CReportBase.AlignRight),
            ( '4.5%', [u'',                                                                                               u'',                                                                        u'из них: дорожно-\nтранспортные несчастные случаи', u'',                               u'*',       u'6'], CReportBase.AlignRight),
            ( '4.5%', [u'',                                                                                               u'Другие внешние при-\nчины (W00 - X59)',                                   u'Всего',                                          u'',                                 u'W00-X59', u'7'], CReportBase.AlignRight),
            ( '4%',   [u'',                                                                                               u'',                                                                        u'из них: ',                                       u'падения',                          u'W00-W19', u'8'], CReportBase.AlignRight),
            ( '4%',   [u'',                                                                                               u'',                                                                        u'',                                               u'случайное утопление',              u'W65-W74', u'9'], CReportBase.AlignRight),
            ( '4%',   [u'',                                                                                               u'',                                                                        u'',                                               u'воздействие дыма,\n огня и пламени',u'X00-X09', u'10'], CReportBase.AlignRight),
            ( '4%',   [u'',                                                                                               u'',                                                                        u'',                                               u'случайное отравление',             u'X40-X49', u'11'],CReportBase.AlignRight),
            ( '4%',   [u'',                                                                                               u'',                                                                        u'из гр.10:',                                      u'наркотиками ',                     u'X42',     u'12'], CReportBase.AlignRight),
            ( '4%',   [u'',                                                                                               u'',                                                                        u'',                                               u'алкоголем ',                       u'X45',     u'13'], CReportBase.AlignRight),
            ( '4.5%', [u'',                                                                                               u'Преднамеренное самоп-\nовреждение(X60-X84)',                              u'Всего',                                          u'',                                 u'X60-X84', u'14'], CReportBase.AlignRight),
            ( '4%',   [u'',                                                                                               u'',                                                                        u'из них:',                                        u'наркотиками ',                     u'X62',     u'15'], CReportBase.AlignRight),
            ( '4%',   [u'',                                                                                               u'',                                                                        u'',                                               u'алкоголем ',                       u'X65',     u'16'], CReportBase.AlignRight),
            ( '4.5%', [u'',                                                                                               u'Нападение',                                                               u'',                                               u'',                                 u'X85-Y09', u'17'], CReportBase.AlignRight),
            ( '4.5%', [u'',                                                                                               u'Повреждение с неопре-\nделенными намерениями',                            u'',                                               u' ',                                u'Y10-Y34 ',u'18'], CReportBase.AlignRight),
            ( '4.5%', [u'',                                                                                               u'Действия, предусмотре-\nнные законом, воен-\nные операции и терроризм',   u'',                                               u'',                                 u'Y35-Y38', u'19'], CReportBase.AlignRight),
            ( '4.5%', [u'',                                                                                               u'Осложнения терапевти-\nческих и хирургичес-\nких вмешательств',           u'',                                               u'',                                 u'Y40-Y84', u'20'], CReportBase.AlignRight),
            ( '4.5%', [u'',                                                                                               u'Последствия воздейст-\nвия внешних причин за-\nболеваемости и смертности',u'',                                               u'',                                 u'Y85-Y89', u'21'], CReportBase.AlignRight),
            ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 5, 1)
        table.mergeCells(0, 1, 5, 1)
        table.mergeCells(0, 2, 5, 1)
        table.mergeCells(0, 3, 1, 18)
        table.mergeCells(1, 3, 3, 1)
        table.mergeCells(1, 4, 1, 2)
        table.mergeCells(2, 4, 2, 1)
        table.mergeCells(2, 5, 2, 1)
        table.mergeCells(1, 6, 1, 7)
        table.mergeCells(2, 6, 2, 1)
        table.mergeCells(2, 7, 1, 4)
        table.mergeCells(2, 11, 1, 2)
        table.mergeCells(1, 13, 1, 3)
        table.mergeCells(2, 13, 2, 1)
        table.mergeCells(2, 14, 1, 2)
        table.mergeCells(1, 16, 3, 1)
        table.mergeCells(1, 17, 3, 1)
        table.mergeCells(1, 18, 3, 1)
        table.mergeCells(1, 19, 3, 1)
        table.mergeCells(1, 20, 3, 1)

        for row, rowDescr in enumerate(MainRowsNew):
            i   = table.addRow()
            table.setText(i, 0, rowDescr[0])
            table.setText(i, 1, rowDescr[2])
            table.mergeCells(i, 0, 2, 1) # п.н.
            table.mergeCells(i, 1, 2, 1) # мкб
            table.setText(i, 2, rowDescr[1])
            reportLine = reportMainData[row]
            for column in xrange(rowSize):
                table.setText(i, 3+column, reportLine[column])
        return doc


class CStatReportF57_2000(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'2000. Травмы по характеру и соответствующие им внешние причины у взрослых (18 лет и более). (Ф57)')
        self.pageFormat = CPageFormat(pageSize=CPageFormat.A4, orientation=CPageFormat.Landscape)


    def getDefaultParams(self):
        result = CReport.getDefaultParams(self)
        result['onlyFirstTime'] = True
        result['notNullTraumaType'] = False
        result['ageFrom'] = 18
        result['ageTo'] = 150
        return result


    def getSetupDialog(self, parent):
        result = CReportAcuteInfectionsSetupDialog(parent)
        result.setAGE(18, 150)
        result.setMKBFilterEnabled(False)
        result.setAccountAccompEnabled(True)
        result.setOnlyFirstTimeEnabled(True)
        result.setNotNullTraumaTypeEnabled(True)
        result.setTitle(self.title())
        return result


    def build(self, params):
        mapMainRows = createMapCodeToRowIdx( [row[2] for row in MainRowsNew] )
        rowSize = 18
        reportMainData = [ [0]*rowSize for row in xrange(len(MainRowsNew)) ]
        mapHeaderCols = createMapCodeToRowIdx( [row[2] for row in HeaderCols] )
#        reportHeaderData = [ 0 for row in xrange(len(HeaderCols)) ]

        query = selectDataNew(params)
        while query.next():
            record   = query.record()
            sickCount = forceInt(record.value('sickCount'))
            MKB   = normalizeMKB(forceString(record.value('MKB')))
            MKBEx = normalizeMKB(forceString(record.value('MKBEx')))
            columns = mapHeaderCols.get(MKBEx, [])
            rows = mapMainRows.get(MKB, [])
            for row in rows:
                reportLine = reportMainData[row]
                for column in columns:
                    reportLine[column] += sickCount

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertText('(2000)')
        tableColumns = [
            ( '12.5%', [u'Травмы, отрав-\nления и некоторые другие\n последствия воздействия\n внешних причин\n(Класс XIX МКБ-10)',u'',                                                               u'',                                               u'',                                 u'',        u'1' ], CReportBase.AlignLeft),
            ( '7.5%', [u'Код по МКБ-10',                                                                                  u'',                                                                        u'',                                               u'',                                 u'',        u'2' ], CReportBase.AlignLeft),
            ( '3.5%', [u'N строки',                                                                                       u'',                                                                        u'',                                               u'',                                 u'',        u'3' ], CReportBase.AlignRight),
            ( '4.5%', [u'Внешние причины-\n заболеваемости и смертности\n(Класс XX МКБ-10)',                              u'Внешние причины за-\nболеваемости и смерт-\nности, всего',                u'',                                               u'',                                 u'V01-Y98', u'4'], CReportBase.AlignRight),
            ( '4.5%', [u'',                                                                                               u'Транспортные несча-\nстные случаи (V01-V99)',                             u'Всего',                                          u'',                                 u'V01-V99', u'5'], CReportBase.AlignRight),
            ( '4.5%', [u'',                                                                                               u'',                                                                        u'из них: дорожно-\nтранспортные несчастные случаи',u'',                                 u'*',       u'6'], CReportBase.AlignRight),
            ( '4.5%', [u'',                                                                                               u'Другие внешние при-\nчины (W00 - X59)',                                   u'Всего',                                          u'',                                 u'W00-X59', u'7'], CReportBase.AlignRight),
            ( '4%',   [u'',                                                                                               u'',                                                                        u'из них: ',                                       u'падения',                          u'W00-W19', u'8'], CReportBase.AlignRight),
            ( '4%',   [u'',                                                                                               u'',                                                                        u'',                                               u'случайное утопление',              u'W65-W74', u'9'], CReportBase.AlignRight),
            ( '4%',   [u'',                                                                                               u'',                                                                        u'',                                               u'воздействие дыма,\n огня и пламени', u'X00-X09', u'10'], CReportBase.AlignRight),
            ( '4%',   [u'',                                                                                               u'',                                                                        u'',                                               u'случайное отравление',             u'X40-X49', u'11'],CReportBase.AlignRight),
            ( '4%',   [u'',                                                                                               u'',                                                                        u'из гр.10:',                                      u'наркотиками ',                     u'X42',     u'12'], CReportBase.AlignRight),
            ( '4%',   [u'',                                                                                               u'',                                                                        u'',                                               u'алкоголем ',                       u'X45',     u'13'], CReportBase.AlignRight),
            ( '4.5%', [u'',                                                                                               u'Преднамеренное самоп-\nовреждение(X60-X84)',                              u'Всего',                                          u'',                                 u'X60-X84', u'14'], CReportBase.AlignRight),
            ( '4%',   [u'',                                                                                               u'',                                                                        u'из них:',                                        u'наркотиками ',                     u'X62',     u'15'], CReportBase.AlignRight),
            ( '4%',   [u'',                                                                                               u'',                                                                        u'',                                               u'алкоголем ',                       u'X65',     u'16'], CReportBase.AlignRight),
            ( '4.5%', [u'',                                                                                               u'Нападение',                                                               u'',                                               u'',                                 u'X85-Y09', u'17'], CReportBase.AlignRight),
            ( '4.5%', [u'',                                                                                               u'Повреждение с неопре-\nделенными намерениями',                            u'',                                               u' ',                                u'Y10-Y34 ',u'18'], CReportBase.AlignRight),
            ( '4.5%', [u'',                                                                                               u'Действия, предусмотре-\nнные законом, воен-\nные операции и терроризм',   u'',                                               u'',                                 u'Y35-Y38', u'19'], CReportBase.AlignRight),
            ( '4.5%', [u'',                                                                                               u'Осложнения терапевти-\nческих и хирургичес-\nких вмешательств',           u'',                                               u'',                                 u'Y40-Y84', u'20'], CReportBase.AlignRight),
            ( '4.5%', [u'',                                                                                               u'Последствия воздейст-\nвия внешних причин за-\nболеваемости и смертности',u'',                                               u'',                                 u'Y85-Y89', u'21'], CReportBase.AlignRight),
            ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 5, 1)
        table.mergeCells(0, 1, 5, 1)
        table.mergeCells(0, 2, 5, 1)
        table.mergeCells(0, 3, 1, 18)
        table.mergeCells(1, 3, 3, 1)
        table.mergeCells(1, 4, 1, 2)
        table.mergeCells(2, 4, 2, 1)
        table.mergeCells(2, 5, 2, 1)
        table.mergeCells(1, 6, 1, 7)
        table.mergeCells(2, 6, 2, 1)
        table.mergeCells(2, 7, 1, 4)
        table.mergeCells(2, 11, 1, 2)
        table.mergeCells(1, 13, 1, 3)
        table.mergeCells(2, 13, 2, 1)
        table.mergeCells(2, 14, 1, 2)
        table.mergeCells(1, 16, 3, 1)
        table.mergeCells(1, 17, 3, 1)
        table.mergeCells(1, 18, 3, 1)
        table.mergeCells(1, 19, 3, 1)
        table.mergeCells(1, 20, 3, 1)

        for row, rowDescr in enumerate(MainRowsNew):
            i   = table.addRow()
            table.setText(i, 0, rowDescr[0])
            table.setText(i, 1, rowDescr[2])
            table.mergeCells(i, 0, 2, 1) # п.н.
            table.mergeCells(i, 1, 2, 1) # мкб
            table.setText(i, 2, rowDescr[1])
            reportLine = reportMainData[row]
            for column in xrange(rowSize):
                table.setText(i, 3+column, reportLine[column])
        return doc


class CStatReportF57_3000(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'3000. Травмы по характеру и соответствующие им внешние причины у взрослых старше трудоспособного возраста. (Ф57)')
        self.pageFormat = CPageFormat(pageSize=CPageFormat.A4, orientation=CPageFormat.Landscape)


    def getDefaultParams(self):
        result = CReport.getDefaultParams(self)
        result['onlyFirstTime'] = True
        result['notNullTraumaType'] = False
        result['ageFrom'] = 55
        result['ageTo'] = 150
        return result


    def getSetupDialog(self, parent):
        result = CReportAcuteInfectionsSetupDialog(parent)
        result.setAGE(55, 150)
        result.setMKBFilterEnabled(False)
        result.setAccountAccompEnabled(True)
        result.setOnlyFirstTimeEnabled(True)
        result.setNotNullTraumaTypeEnabled(True)
        result.setTitle(self.title())
        return result


    def build(self, params):
        mapMainRows = createMapCodeToRowIdx( [row[2] for row in MainRowsNew] )
        rowSize = 18
        reportMainData = [ [0]*rowSize for row in xrange(len(MainRowsNew)) ]
        mapHeaderCols = createMapCodeToRowIdx( [row[2] for row in HeaderCols] )
#        reportHeaderData = [ 0 for row in xrange(len(HeaderCols)) ]

        query = selectDataNew(params)
        while query.next():
            record   = query.record()
            sickCount = forceInt(record.value('sickCount'))
            MKB   = normalizeMKB(forceString(record.value('MKB')))
            MKBEx = normalizeMKB(forceString(record.value('MKBEx')))
            columns = mapHeaderCols.get(MKBEx, [])
            rows = mapMainRows.get(MKB, [])
            for row in rows:
                reportLine = reportMainData[row]
                for column in columns:
                    reportLine[column] += sickCount

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertText('(3000)')
        tableColumns = [
            ('12.5%', [u'Травмы, отрав-\nления и некоторые другие\n последствия воздействия\n внешних причин\n(Класс XIX МКБ-10)',u'',                                                                 u'',                                               u'',                                 u'',        u'1' ], CReportBase.AlignLeft),
            ('7.5%',  [u'Код по МКБ-10',                                                                                  u'',                                                                         u'',                                               u'',                                 u'',        u'2' ], CReportBase.AlignLeft),
            ( '4.5%', [u'N строки',                                                                                       u'',                                                                         u'',                                               u'',                                 u'',        u'3' ], CReportBase.AlignRight),
            ( '4.5%', [u'Внешние при-\nчины заболеваемости и смертности\n(Класс XX МКБ-10)',                              u'Внешние причины за-\nболеваемости и смерт-\nности, всего',                 u'',                                               u'',                                 u'V01-Y98', u'4'], CReportBase.AlignRight),
            ( '4.5%', [u'',                                                                                               u'Транспортные несча-\nстные случаи (V01-V99)',                              u'Всего',                                          u'',                                 u'V01-V99', u'5'], CReportBase.AlignRight),
            ( '4.5%', [u'',                                                                                               u'',                                                                         u'из них: дорожно-\nтранспортные несчастные случаи', u'',                                 u'*',       u'6'], CReportBase.AlignRight),
            ( '4.5%', [u'',                                                                                               u'Другие внешние при-\nчины (W00 - X59)',                                    u'Всего',                                          u'',                                 u'W00-X59', u'7'], CReportBase.AlignRight),
            ( '4%', [u'',                                                                                               u'',                                                                         u'из них: ',                                       u'падения',                          u'W00-W19', u'8'], CReportBase.AlignRight),
            ( '4%', [u'',                                                                                               u'',                                                                         u'',                                               u'случайное утопление',              u'W65-W74', u'9'], CReportBase.AlignRight),
            ( '4%', [u'',                                                                                               u'',                                                                         u'',                                               u'воздействие дыма,\n огня и пламени', u'X00-X09', u'10'], CReportBase.AlignRight),
            ( '4%', [u'',                                                                                               u'',                                                                         u'',                                               u'случайное отравление',             u'X40-X49', u'11'],CReportBase.AlignRight),
            ( '4%', [u'',                                                                                               u'',                                                                         u'из гр.10:',                                      u'наркотиками ',                     u'X42',     u'12'], CReportBase.AlignRight),
            ( '4%', [u'',                                                                                               u'',                                                                         u'',                                               u'алкоголем ',                       u'X45',     u'13'], CReportBase.AlignRight),
            ( '4.5%', [u'',                                                                                               u'Преднамеренное самоп-\nовреждение(X60-X84)',                               u'Всего',                                          u'',                                 u'X60-X84', u'14'], CReportBase.AlignRight),
            ( '4.5%', [u'',                                                                                               u'',                                                                         u'из них:',                                        u'наркотиками ',                     u'X62',     u'15'], CReportBase.AlignRight),
            ( '4%', [u'',                                                                                               u'',                                                                         u'',                                               u'алкоголем ',                       u'X65',     u'16'], CReportBase.AlignRight),
            ( '4%', [u'',                                                                                               u'Нападение',                                                                u'',                                               u'',                                 u'X85-Y09', u'17'], CReportBase.AlignRight),
            ( '4.5%', [u'',                                                                                               u'Повреждение с неопре-\nделенными намерениями',                             u'',                                               u' ',                                u'Y10-Y34 ',u'18'], CReportBase.AlignRight),
            ( '4.5%', [u'',                                                                                               u'Действия, предусмотре-\nнные законом, воен-\nные операции и терроризм',    u'',                                               u'',                                 u'Y35-Y38', u'19'], CReportBase.AlignRight),
            ( '4.5%', [u'',                                                                                               u'Осложнения терапевти-\nческих и хирургичес-\nких вмешательств',            u'',                                               u'',                                 u'Y40-Y84', u'20'], CReportBase.AlignRight),
            ( '4.5%', [u'',                                                                                               u'Последствия воздейст-\nвия внешних причин за-\nболеваемости и смертности', u'',                                               u'',                                 u'Y85-Y89', u'21'], CReportBase.AlignRight),
            ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 5, 1)
        table.mergeCells(0, 1, 5, 1)
        table.mergeCells(0, 2, 5, 1)
        table.mergeCells(0, 3, 1, 18)
        table.mergeCells(1, 3, 3, 1)
        table.mergeCells(1, 4, 1, 2)
        table.mergeCells(2, 4, 2, 1)
        table.mergeCells(2, 5, 2, 1)
        table.mergeCells(1, 6, 1, 7)
        table.mergeCells(2, 6, 2, 1)
        table.mergeCells(2, 7, 1, 4)
        table.mergeCells(2, 11, 1, 2)
        table.mergeCells(1, 13, 1, 3)
        table.mergeCells(2, 13, 2, 1)
        table.mergeCells(2, 14, 1, 2)
        table.mergeCells(1, 16, 3, 1)
        table.mergeCells(1, 17, 3, 1)
        table.mergeCells(1, 18, 3, 1)
        table.mergeCells(1, 19, 3, 1)
        table.mergeCells(1, 20, 3, 1)

        for row, rowDescr in enumerate(MainRowsNew):
            i   = table.addRow()
            table.setText(i, 0, rowDescr[0])
            table.setText(i, 1, rowDescr[2])
            table.mergeCells(i, 0, 2, 1) # п.н.
            table.mergeCells(i, 1, 2, 1) # мкб
            table.setText(i,   2, rowDescr[1])
            reportLine = reportMainData[row]
            for column in xrange(rowSize):
                table.setText(i, 3+column, reportLine[column])
        return doc


class CStatReportF57_3500(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'3500. Случаи смерти от внешних причин. (Ф57)')
        self.pageFormat = CPageFormat(pageSize=CPageFormat.A4, orientation=CPageFormat.Landscape)


    def getDefaultParams(self):
        result = CReport.getDefaultParams(self)
        result['onlyFirstTime'] = True
        result['notNullTraumaType'] = False
        return result


    def getSetupDialog(self, parent):
        result = CReportAcuteInfectionsSetupDialog(parent)
        result.setMKBFilterEnabled(False)
        result.setAccountAccompEnabled(True)
        result.setOnlyFirstTimeEnabled(True)
        result.setNotNullTraumaTypeEnabled(True)
        result.setTitle(self.title())
        return result


    def build(self, params):
        mapHeaderCols = createMapCodeToRowIdx( [row[2] for row in MainRowsNew] )
        mapMainRows = createMapCodeToRowIdx( [row[2] for row in MainRows_3500] )
        rowSize = 3
        reportMainData = [ [0]*rowSize for row in xrange(len(MainRows_3500)) ]

        query = selectData3500(params)
        while query.next():
            record   = query.record()
            sickCount = forceInt(record.value('sickCount'))
            MKB       = normalizeMKB(forceString(record.value('MKB')))
            MKBEx     = normalizeMKB(forceString(record.value('MKBEx')))
            sex       = forceInt(record.value('sex'))
            clientAge = forceInt(record.value('clientAge'))
            cols = mapHeaderCols.get(MKB, [])
            if cols:
                rows = mapMainRows.get(MKBEx, [])
                for row in rows:
                    reportLine = reportMainData[row]
                    if clientAge < 18:
                        reportLine[0] += sickCount
                    else:
                        reportLine[1] += sickCount
                    if (sex == 1 and  clientAge >= 60) or (sex == 2 and  clientAge >= 55):
                        reportLine[2] += sickCount

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertText('(3500)')
        tableColumns = [
            ('25%', [u'Виды травм по внешней причине',                                   u'',                                                                     u'1' ], CReportBase.AlignLeft),
            ('25%', [u'Коды по МКБ-10',                                                  u'',                                                                     u'2' ], CReportBase.AlignLeft),
            ( '5%', [u'N строки',                                                        u'',                                                                     u'3' ], CReportBase.AlignCenter),
            ( '15%',[u'Случаи смерти детей (0 - 17 лет включительно) (из таблицы 1000)', u'',                                                                     u'4' ], CReportBase.AlignRight),
            ( '15%',[u'Случаи смерти взрослых (18 лет и более) (из таблицы 2000)',       u'',                                                                     u'5' ], CReportBase.AlignRight),
            ( '15%',[u'из гр. 5:',                                                       u'случаи смерти лиц старше трудоспособного возраста (из таблицы 3000)',  u'6' ], CReportBase.AlignRight),
            ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 2, 1)
        table.mergeCells(0, 3, 2, 1)
        table.mergeCells(0, 4, 2, 1)
        for row, rowDescr in enumerate(MainRows_3500):
            i = table.addRow()
            table.setText(i, 0, rowDescr[0])
            table.setText(i, 1, rowDescr[2] if rowDescr[1] != u'2.1.1' else u'*')
            table.setText(i, 2, rowDescr[1])
            reportLine = reportMainData[row]
            for column in xrange(rowSize):
                table.setText(i, 3+column, reportLine[column])
        return doc

