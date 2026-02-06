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
from PyQt4.QtCore import QDate

from library.database   import addDateInRange
from library.MapCode    import createMapCodeToRowIdx
from library.Utils      import forceInt, forceString
from Reports.Report     import CReport, normalizeMKB
from Reports.ReportBase import CReportBase, createTable
from Reports.ReportPersonSickList import addAddressCond, addAttachCond
from Reports.ReportAcuteInfections import getFilterAddress, CReportAcuteInfectionsSetupDialog
from Orgs.Utils         import getOrgStructureListDescendants, getOrgStructureAddressIdList


MainRows = [
    ( u'Зарегистрировано заболеваний – всего', u'1.0', u'A00-T98'),
    ( u'в том числе: некоторые инфекционные и паразитарные болезни', u'2.0', u'A00-B99'),
    ( u'из них: кишечные инфекции', u'2.1', u'A00-A09'),
    ( u'новообразования', u'3.0', u'C00-D48'),
    ( u'болезни крови, кроветворных органов и отдельные нарушения, вовлекающие иммунный механизм', u'4.0', u'D50-D89'),
    ( u'из них: анемии', u'4.1', u'D50-D64'),
    ( u'болезни эндокринной системы, расстройства питания и нарушения обмена веществ', u'5.0', u'E00-E89'),
    ( u'из них: болезни щитовидной железы', u'5.1', u'E00-E07'),
    ( u'из них: эндемический зоб, связанный с йодной недостаточностью', u'5.1.1', u'E01.0-2'),
    ( u'сахарный диабет', u'5.2', u'E10-E14'),
    ( u'из него: сахарный диабет I типа', u'5.2.1', u'E10'),
    ( u'дисфункция яичников', u'5.3', u'E28'),
    ( u'дисфункция яичек', u'5.4', u'E29'),
    ( u'недостаточность питания', u'5.5', u'E40-E46'),
    ( u'ожирение', u'5.6', u'E66'),
    ( u'из них, крайняя степень ожирения', u'5.6.1', u'E66.2'),
    ( u'психические расстройства и расстройства поведения', u'6.0', u'F01, F03-F99'),
    ( u'из них: психические расстройства и расстройства поведения, связанные с употреблением психоактивных веществ', u'6.1', u'F10-F19'),
    ( u'невротические, связанные со стрессом и соматоформные расстройства', u'6.2', u'F40-F48'),
    ( u'расстройства психологического развития', u'6.3', u'F80-F89'),
    ( u'болезни нервной системы', u'7.0', u'G00-G98'),
    ( u'болезни глаза и его придаточного аппарата', u'8.0', u'H00-H59'),
    ( u'из них: болезни мышц глаза, нарушения содружественного движения глаз, аккомодации и рефракции', u'8.11', u'H49-H52'),
    ( u'из них:  миопия', u'8.11.1', u'H52.1'),
    ( u'болезни уха и сосцевидного отростка', u'9.0', u'H60-H95'),
    ( u'болезни системы кровообращения', u'10.0', u'I00-I99'),
    ( u'из них: болезни, характеризующиеся повышенным кровяным давлением', u'10.3', u'I10-I13'),
    ( u'болезни органов дыхания', u'11.0', u'J00-J98'),
    ( u'из них: острые респираторные инфекции верхних дыхательных путей', u'11.1', u'J00-J06'),
    ( u'грипп', u'11.2', u'J09-J11'),
    ( u'пневмонии', u'11.3', u'J12-J16, J18'),
    ( u'острые респираторные инфекции нижних дыхательных путей', u'11.4', u'J20-J22'),
    ( u'бронхит хронический и неуточненный, эмфизема', u'11.5', u'J40-J43'),
    ( u'астма; астматический статус', u'11.6', u'J45, J46'),
    ( u'болезни органов пищеварения', u'12.0', u'K00-K92'),
    ( u'из них: гастрит и дуоденит', u'12.1', u'K29'),
    ( u'болезни печени', u'12.2', u'K70-K76'),
    ( u'болезни желчного пузыря, желчевыводящих путей', u'12.3', u'K80-K83'),
    ( u'болезни поджелудочной железы', u'12.4', u'K85-K86'),
    ( u'болезни кожи и подкожной клетчатки', u'13.0', u'L00-L98'),
    ( u'из них: атопический дерматит', u'13.1', u'L20'),
    ( u'контактный дерматит', u'13.2', u'L23-L25'),
    ( u'другие дерматиты (экзема)', u'13.3', u'L30'),
    ( u'болезни костно-мышечной системы и соединительной ткани', u'14.0', u'M00-M99'),
    ( u'из них: артропатии', u'14.1', u'M00-M25'),
    ( u'деформирующие дорсопатии', u'14.3', u'M40-M43'),
    ( u'из них: кифоз, лордоз, сколиоз', u'14.3.1', u'M40-M41'),
    ( u'болезни мочеполовой системы', u'15.0', u'N00-N99'),
    ( u'из них: гломерулярные,  тубулоинтерстициальные болезни почек, другие болезни почки и мочеточника', u'15.1', u'N00-N07, N09-N15, N25-N28'),
    ( u'воспалительные болезни женских тазовых органов', u'15.2', u'N70-N73, N75-N76'),
    ( u'из них сальпингит и оофорит', u'15.2.1', u'N70'),
    ( u'расстройства менструаций', u'15.3', u'N91-N94'),
    ( u'травмы, отравления и некоторые другие последствия воздействия внешних причин', u'20.0', u'S00-T98'),
    ( u'COVID-19', u'21.0', u'U07.1, U07.2'),
]


def selectData(begDate, endDate, eventPurposeId, eventTypeIdList, orgStructureIdList, personId, sex, ageFrom, ageTo, socStatusClassId, socStatusTypeId, isFilterAddressOrgStructure, addrType, addressOrgStructureId, locality, params):
    stmt = u"""
SELECT
    Diagnosis.MKB AS MKB,
    age(Client.birthDate, %(ageDate)s) AS age,
    COUNT(*) AS sickCount
FROM Diagnosis
LEFT JOIN Client ON Client.id = Diagnosis.client_id
%(stmtAddress)s
WHERE Diagnosis.diagnosisType_id NOT IN (SELECT RBDT.id FROM rbDiagnosisType AS RBDT WHERE RBDT.code = '7' OR RBDT.code = '11')
    AND EXISTS (
        SELECT CSS.id
        FROM ClientSocStatus as CSS
            INNER JOIN rbSocStatusClass as SSC on SSC.id = CSS.socStatusClass_id
            INNER JOIN rbSocStatusType as SST on SST.id = CSS.socStatusType_id
        WHERE CSS.client_id = Client.id
            AND CSS.deleted = 0
            AND (CSS.begDate IS NULL OR CSS.begDate <= %(ageDate)s)
            AND (CSS.endDate IS NULL OR CSS.endDate >= %(ageDate)s)
            AND SSC.code = '9'
            AND SST.regionalCode = (CASE WHEN age(Client.birthDate, %(ageDate)s) < 7 THEN 'с02' ELSE 'с25' END)
    )
AND %(cond)s
GROUP BY MKB, age
    """
    db = QtGui.qApp.db
    tableDiagnosis  = db.table('Diagnosis')
    tableClient = db.table('Client')
    tableDiagnostic = db.table('Diagnostic')
    tablePerson = db.table('Person')
    specialityId = params.get('specialityId', None)

    cond = []
    cond.append(tableDiagnosis['deleted'].eq(0))
    cond.append(tableDiagnosis['mod_id'].isNull())
    cond.append(tableClient['deleted'].eq(0))
    diagnosticQuery = tableDiagnostic
    diagnosticCond = [ tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']),
                       tableDiagnostic['deleted'].eq(0)
                     ]
    addDateInRange(diagnosticCond, tableDiagnostic['setDate'], begDate, endDate)
    tableEvent = db.table('Event')
    tableEventType = db.table('EventType')
    diagnosticQuery = diagnosticQuery.leftJoin(tableEvent, tableEvent['id'].eq(tableDiagnostic['event_id']))
    diagnosticQuery = diagnosticQuery.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
    diagnosticCond.append(tableEventType['code'].notInlist(['rmDisp', 'MSE']))
    if specialityId:
        diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
        diagnosticCond.append(tablePerson['speciality_id'].eq(specialityId))
        diagnosticCond.append(tablePerson['deleted'].eq(0))
    isPersonPost = params.get('isPersonPost', 0)
    if isPersonPost:
        tableRBPost = db.table('rbPost')
        if not specialityId:
            diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
            diagnosticCond.append(tablePerson['deleted'].eq(0))
        diagnosticQuery = diagnosticQuery.leftJoin(tableRBPost, tableRBPost['id'].eq(tablePerson['post_id']))
        if isPersonPost == 1:
            diagnosticCond.append('''LEFT(rbPost.code, 1) IN ('1','2','3') ''')
        elif isPersonPost == 2:
            diagnosticCond.append('''LEFT(rbPost.code, 1) IN ('4','5','6','7','8','9')''')
    if personId:
        diagnosticCond.append(tableDiagnostic['person_id'].eq(personId))
    elif orgStructureIdList:
        if not isPersonPost and not specialityId:
            diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
            diagnosticCond.append(tablePerson['deleted'].eq(0))
        diagnosticCond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureListDescendants(orgStructureIdList)))
    else:
        if not isPersonPost and not specialityId:
            diagnosticQuery = diagnosticQuery.leftJoin(tablePerson, tablePerson['id'].eq(tableDiagnostic['person_id']))
            diagnosticCond.append(tablePerson['deleted'].eq(0))
        diagnosticCond.append(tablePerson['org_id'].eq(QtGui.qApp.currentOrgId()))
    if eventTypeIdList:
        diagnosticCond.append(tableEvent['eventType_id'].inlist(eventTypeIdList))
    elif eventPurposeId:
        diagnosticCond.append(tableEventType['purpose_id'].eq(eventPurposeId))

    cond.append(db.existsStmt(diagnosticQuery, diagnosticCond))

    if sex:
        cond.append(tableClient['sex'].eq(sex))
    ageDate = tableDiagnosis['setDate'].formatValue(QDate(endDate.year(), 12, 31))
    if ageFrom <= ageTo:
        cond.append('Client.birthDate <= ADDDATE(%s, INTERVAL -%d YEAR)' % (ageDate, ageFrom))
        cond.append('Client.birthDate >= ADDDATE(ADDDATE(%s, INTERVAL -%d YEAR),1)' % (ageDate, ageTo+1))
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
    stmtAddress = ''
    if isFilterAddressOrgStructure:
        addrIdList = None
        cond2 = []
        if (addrType+1) & 1:
            addrIdList = getOrgStructureAddressIdList(addressOrgStructureId)
            cond2 = addAddressCond(db, cond2, 0, addrIdList)
        if (addrType+1) & 2:
            if addrIdList is None:
                addrIdList = getOrgStructureAddressIdList(addressOrgStructureId)
            cond2 = addAddressCond(db, cond2, 1, addrIdList)
        if ((addrType+1) & 4):
            if addressOrgStructureId:
                cond2 = addAttachCond(db, cond2, 'orgStructure_id = %d'%addressOrgStructureId, 1, None)
            else:
                cond2 = addAttachCond(db, cond2, 'LPU_id=%d'%QtGui.qApp.currentOrgId(), 1, None)
        if cond2:
            cond.append(db.joinOr(cond2))
    if locality:
        # 1: горожане, isClientVillager == 0 или NULL
        # 2: сельские жители, isClientVillager == 1
        cond.append('IFNULL(isClientVillager(Client.id), 0) = %d' % (locality-1))
    filterAddress = params.get('isFilterAddress', False)
    if filterAddress:
        stmtAddress += u'''INNER JOIN ClientAddress ON ClientAddress.client_id = Client.id
                              INNER JOIN Address ON Address.id = ClientAddress.address_id
                              INNER JOIN AddressHouse ON AddressHouse.id = Address.house_id'''
        cond.append('ClientAddress.id IN (%s)'%(getFilterAddress(params)))
    if 'attachTo' in params:
        attachOrgId = params['attachTo']
        if attachOrgId:
            cond = addAttachCond(db, cond, 'LPU_id=%d'%attachOrgId, *params.get('attachType', (0, None, QDate(), QDate())))
    elif 'attachToNonBase' in params:
        cond = addAttachCond(db, cond, 'LPU_id!=%d'%QtGui.qApp.currentOrgId(), *params.get('attachType', (0, None, QDate(), QDate())))
    elif 'attachType' in params:
        cond = addAttachCond(db, cond, '', *params['attachType'])
    excludeLeaved = params.get('excludeLeaved', False)
    if excludeLeaved:
        outerCond = ['ClientAttach.client_id = Client.id']
        innerCond = ['CA2.client_id = Client.id']
        cond.append('''EXISTS (SELECT ClientAttach.id
           FROM ClientAttach
           LEFT JOIN rbAttachType ON rbAttachType.id = ClientAttach.attachType_id
           WHERE ClientAttach.deleted=0
           AND %s
           AND ClientAttach.id = (SELECT MAX(CA2.id)
                       FROM ClientAttach AS CA2
                       LEFT JOIN rbAttachType AS rbAttachType2 ON rbAttachType2.id = CA2.attachType_id
                       WHERE CA2.deleted=0 AND %s))'''% (QtGui.qApp.db.joinAnd(outerCond), QtGui.qApp.db.joinAnd(innerCond)))
        cond.append(tableClient['deathDate'].isNull())
    if 'dead' in params:
        cond.append(tableClient['deathDate'].isNotNull())
        if 'begDeathDate' in params:
            begDeathDate = params['begDeathDate']
            if begDeathDate:
                cond.append(tableClient['deathDate'].ge(begDeathDate))
        if 'endDeathDate' in params:
            endDeathDate = params['endDeathDate']
            if endDeathDate:
                cond.append(tableClient['deathDate'].lt(endDeathDate.addDays(1)))
    isDispanser = params.get('isDispanser', False)
    if params.get('MKBFrom'):
        cond.append(tableDiagnosis['MKB'].ge(params.get('MKBFrom')))
    if params.get('MKBTo'):
        cond.append(tableDiagnosis['MKB'].le(params.get('MKBTo')))
    if isDispanser:
        cond.append(u'''IF((SELECT MAX(rbDispanser.observed)
        FROM
        Diagnostic AS D1
        LEFT JOIN rbDispanser ON rbDispanser.id = D1.dispanser_id
        WHERE
          D1.diagnosis_id = Diagnosis.id
          AND rbDispanser.observed = 1
          AND D1.endDate = (
            SELECT MAX(D2.endDate)
            FROM Diagnostic AS D2
            WHERE D2.diagnosis_id = Diagnosis.id
              AND D2.dispanser_id IS NOT NULL
              AND D2.endDate < %s)) = 1, 1, 0)''' % (tableDiagnosis['setDate'].formatValue(endDate.addDays(1))))
    return db.query(stmt % {
        'ageDate': ageDate,
        'stmtAddress': stmtAddress,
        'cond': db.joinAnd(cond)
        })


class CStatReportF12Students_2025(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Обучающиеся в образовательных организациях (3 года - 17 лет включительно): дошкольники и школьники')


    def getDefaultParams(self):
        result = CReport.getDefaultParams(self)
        result['ageFrom'] = 3
        result['ageTo']   = 17
        return result
    
    
    def dumpParamsMultiSelect(self, cursor, params):
        description = []
        eventTypeList = params.get('eventTypeList', None)
        if eventTypeList:
            db = QtGui.qApp.db
            tableET = db.table('EventType')
            records = db.getRecordList(tableET, [tableET['name']], [tableET['deleted'].eq(0), tableET['id'].inlist(eventTypeList)])
            nameList = []
            for record in records:
                nameList.append(forceString(record.value('name')))
            description.append(u'тип события:  %s'%(u','.join(name for name in nameList if name)))
        else:
            description.append(u'тип события:  не задано')
        orgStructureList = params.get('orgStructureList', None)
        if orgStructureList:
            if len(orgStructureList) == 1 and not orgStructureList[0]:
                description.append(u'подразделение: ЛПУ')
            else:
                db = QtGui.qApp.db
                table = db.table('OrgStructure')
                records = db.getRecordList(table, [table['name']], [table['id'].inlist(orgStructureList)])
                nameList = []
                for record in records:
                    nameList.append(forceString(record.value('name')))
                description.append(u'подразделение:  %s'%(u','.join(name for name in nameList if name)))
        else:
            description.append(u'подразделение: ЛПУ')
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
    

    def dumpParamsIsDispanser(self, cursor, params):
        description = []
        isDispanser = params.get('isDispanser', False)
        if isDispanser:
            description.append(u'Учитывать только состоящих на диспансерном наблюдении')
            columns = [ ('100%', [], CReportBase.AlignLeft) ]
            table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
            for i, row in enumerate(description):
                table.setText(i, 0, row)
            cursor.movePosition(QtGui.QTextCursor.End)


    def getSetupDialog(self, parent):
        result = CReportAcuteInfectionsSetupDialog(parent)
        result.setAreaEnabled(False)
        result.setFilterAddressOrgStructureVisible(True)
        result.setAllAddressSelectable(True)
        result.setAllAttachSelectable(True)
        result.setEventTypeListListVisible(True)
        result.setOrgStructureListVisible(True)
        result.setSpecialityVisible(True)
        result.setCMBEventTypeVisible(False)
        result.setCMBOrgStructureVisible(False)
        result.setChkFilterDispanser(True)
        result.setTitle(self.title())
        result.chkDetailMKB.setVisible(True)
        result.chkFilterExcludeLeaved.setVisible(False)
        result.chkFilterExcludeLeaved.setChecked(False)
        result.chkRegisteredInPeriod.setChecked(True)
        result.chkRegisteredInPeriod.setVisible(False)
        result.setUseInputDate(False)
        return result
    
    
    def build(self, params):
        mapMainRows = createMapCodeToRowIdx( [row[2] for row in MainRows] )
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        eventPurposeId = params.get('eventPurposeId', None)
        eventTypeList = params.get('eventTypeList', None)
        orgStructureList = params.get('orgStructureList', None)
        personId = params.get('personId', None)
        sex = params.get('sex', 0)
        ageFrom = params.get('ageFrom', 3)
        ageTo = params.get('ageTo', 17)
        socStatusClassId = params.get('socStatusClassId', None)
        socStatusTypeId = params.get('socStatusTypeId', None)
        isFilterAddressOrgStructure = params.get('isFilterAddressOrgStructure', False)
        addrType = params.get('addressOrgStructureType', 0)
        addressOrgStructureId = params.get('addressOrgStructure', None)
        locality = params.get('locality', 0)
        detailMKB = params.get('detailMKB', False)
        reportLine = None

        rowSize = 4
        if detailMKB:
            reportMainData = {}  # { MKB: [reportLine] }
        else:
            reportMainData = [ [0]*rowSize for row in xrange(len(MainRows)) ]
        
        query = selectData(begDate, endDate, eventPurposeId, eventTypeList, orgStructureList, personId, sex, ageFrom, ageTo, socStatusClassId, socStatusTypeId, isFilterAddressOrgStructure, addrType, addressOrgStructureId, locality, params)
        while query.next():
            record = query.record()
            MKB = normalizeMKB(forceString(record.value('MKB')))
            age = forceInt(record.value('age'))
            sickCount = forceInt(record.value('sickCount'))
            cols = []
            if 3 <= age <= 6:
                cols.append(0)
            elif 7 <= age <= 10:
                cols.append(1)
            elif 11 <= age <= 14:
                cols.append(2)
            elif 15 <= age <= 17:
                cols.append(3)
            if detailMKB:
                reportLine = reportMainData.setdefault(MKB, [0]*rowSize)
                for col in cols:
                    reportLine[col] += sickCount
            else:
                for row in mapMainRows.get(MKB, []):
                    reportLine = reportMainData[row]
                    for col in cols:
                        reportLine[col] += sickCount
        
        # now text
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        chkFilterAttachType = params.get('chkFilterAttachType', False)
        dead = params.get('dead', False)
        chkFilterAttach = params.get('chkFilterAttach', False)
        attachToNonBase = params.get('attachToNonBase', False)
        excludeLeaved = params.get('excludeLeaved', False)
        if chkFilterAttachType or dead or chkFilterAttach or attachToNonBase or excludeLeaved:
           self.dumpParamsAttach(cursor, params)
        if params.get('isFilterAddress', False):
            self.dumpParamsAdress(cursor, params)
        self.dumpParamsMultiSelect(cursor, params)
        self.dumpParamsIsDispanser(cursor, params)
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        cursor.insertText(u'(2200)')
        cursor.insertBlock()

        tableColumns = [
            ('40%', [u'Наименование классов и отдельных болезней', u'', u'1'], CReportBase.AlignLeft),
            ('6%', [u'№ строк', u'', u'2'], CReportBase.AlignLeft),
            ('10%', [u'Код по МКБ-10', u'', u'3'], CReportBase.AlignLeft),
            ('11%', [u'Зарегистрировано заболеваний у дошкольников всего, ед', u'', u'4'], CReportBase.AlignRight),
            ('11%', [u'Зарегистрировано заболеваний у школьников, ед', u'7-10 лет включительно', u'5'], CReportBase.AlignRight),
            ('11%', [u'', u'11-14 лет включительно', u'6'], CReportBase.AlignRight),
            ('11%', [u'', u'15-17 лет включительно', u'7'], CReportBase.AlignRight)
            ]

        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 2, 1) # Наименование
        table.mergeCells(0, 1, 2, 1) # № стр.
        table.mergeCells(0, 2, 2, 1) # Код МКБ
        table.mergeCells(0, 3, 2, 1) # Дошкольники
        table.mergeCells(0, 4, 1, 3) # Школьники

        if detailMKB:
            for row, MKB in enumerate(sorted(reportMainData.keys())):
                reportLine = reportMainData[MKB]
                if not MKB:
                    MKBDescr, MKB = u'', u'Не указано'
                else:
                    MKBDescr = forceString(QtGui.qApp.db.translate('MKB', 'DiagID', MKB, 'DiagName'))
                if MKB.endswith('.0') and not MKBDescr:
                    MKBDescr = forceString(QtGui.qApp.db.translate('MKB', 'DiagID', MKB[:-2], 'DiagName'))
                i = table.addRow()
                table.setText(i, 0, MKBDescr)
                table.setText(i, 1, row+1)
                table.setText(i, 2, MKB)
                for col in xrange(rowSize):
                    table.setText(i, 3+col, reportLine[col])
        else:
            for row, rowDescr in enumerate(MainRows):
                reportLine = reportMainData[row]
                i = table.addRow()
                table.setText(i, 0, rowDescr[0])
                table.setText(i, 1, rowDescr[1])
                table.setText(i, 2, rowDescr[2])
                for col in xrange(rowSize):
                    table.setText(i, 3+col, reportLine[col])
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        return doc

