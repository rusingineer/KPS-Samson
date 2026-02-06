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

from library.Utils             import forceInt, forceString, getRetirementAge
from library.MapCode           import createMapCodeToRowIdx
from Reports.Report            import CReport, normalizeMKB
from Reports.ReportBase        import CReportBase, createTable
from Orgs.Utils                import getOrgStructurePersonIdList

from Reports.ReportForm131_o_2000_2021 import CReportForm131SetupDialog2021



MainRows = [
    (u'Туберкулез органов дыхания',                                                                                                                 u'1',    u'A15-A16'),
    (u'Злокачественные новообразования',                                                                                                            u'2',    u'C00-C97'),
    (u'Из них губы, полости рта и глотки',                                                                                                          u'2.1',  u'C00-C14'),
    (u'из них в 1-2 стадии',                                                                                                                        u'2.2',  u''),
    (u'пищевода',                                                                                                                                   u'2.3',  u'C15'),
    (u'из них в 1-2 стадии',                                                                                                                        u'2.4',  u''),
    (u'желудка',                                                                                                                                    u'2.5',  u'C16'),
    (u'из них в 1-2 стадии',                                                                                                                        u'2.6',  u''),
    (u'тонкого кишечника',                                                                                                                          u'2.7',  u'C17'),
    (u'из них в 1-2 стадии',                                                                                                                        u'2.8',  u''),
    (u'ободочной кишки',                                                                                                                            u'2.9',  u'C18'),
    (u'из них в 1-2 стадии',                                                                                                                        u'2.10', u''),
    (u'ректосигмоидного соединения, прямой кишки, заднего прохода (ануса) и анального канала',                                                      u'2.11', u'C19-C21'),
    (u'из них в 1-2 стадии',                                                                                                                        u'2.12', u''),
    (u'трахеи, бронхов, легкого',                                                                                                                   u'2.13', u'C33,C34'),
    (u'из них в 1-2 стадии',                                                                                                                        u'2.14', u''),
    (u'кожи',                                                                                                                                       u'2.15', u'C43-C44'),
    (u'из них в 0-1 стадии',                                                                                                                        u'2.16', u''),
    (u'молочной железы',                                                                                                                            u'2.17', u'C50'),
    (u'из них в 0-1 стадии',                                                                                                                        u'2.18', u''),
    (u'2 стадии',                                                                                                                                   u'2.19', u''),
    (u'шейки матки',                                                                                                                                u'2.20', u'C53'),
    (u'из них в 0-1 стадии',                                                                                                                        u'2.21', u''),
    (u'2 стадии',                                                                                                                                   u'2.22', u''),
    (u'предстательной железы',                                                                                                                      u'2.23', u'C61'),
    (u'из них в 1-2 стадии',                                                                                                                        u'2.24', u''),
    (u'Сахарный диабет',                                                                                                                            u'3',    u'E10-E14'),
    (u'из него: инсулиннезависимый сахарный диабет',                                                                                                u'3.1',  u'E11'),
    (u'Преходящие церебральные ишемические приступы (атаки) и родственные синдромы',                                                                u'4',    u'G45'),
    (u'Старческая катаракта и другие катаракты',                                                                                                    u'5',    u'H25,H26'),
    (u'Глаукома',                                                                                                                                   u'6',    u'H40'),
    (u'Слепота и пониженное зрение',                                                                                                                u'7',    u'H54'),
    (u'Кондуктивная и нейросенсорная потеря слуха',                                                                                                 u'8',    u'H90'),
    (u'Болезни системы кровообращения',                                                                                                             u'9',    u'I00-I99'),
    (u'из них болезни, характеризующиеся повышенным кровяным давлением',                                                                            u'9.1',  u'I10-I13'),
    (u'ишемические болезни сердца',                                                                                                                 u'9.2',  u'I20-I25'),
    (u'цереброваскулярные болезни',                                                                                                                 u'9.3',  u'I60-I69'),
    (u'из них: закупорка и стеноз прецеребральных и (или) церебральных артерий, не приводящие к инфаркту мозга',                                    u'9.4',  u'I65,I66'),
    (u'Болезни органов дыхания',                                                                                                                    u'10',   u'J00-J99'),
    (u'Бронхит, не уточненный как острый и хронический, простой и слизистогнойный хронический бронхит, хронический бронхит неуточненный, эмфизема', u'10.1', u'J40-J43'),
    (u'Другая хроническая обструктивная легочная болезнь, астма, астматический статус, бронхоэктатическая болезнь',                                 u'10.2', u'J44-J47'),
    (u'Болезни органов пищеварения',                                                                                                                u'11',   u'K00-K93'),
    (u'язва желудка, язва двенадцатиперстной кишки',                                                                                                u'11.1', u'K25,K26'),
    (u'Гастрит и дуоденит',                                                                                                                         u'12',   u'K29'),
    (u'Прочие',                                                                                                                                     u'13',   u''),
]


def selectData(params):
    begDate = params.get('begDate', QDate())
    endDate = params.get('endDate', QDate())
    orgStructureId = params.get('orgStructureId', None)
    dispType = params.get('dispType', 0)
    db = QtGui.qApp.db

    record = db.getRecordEx('rbAccountingSystem', 'id', "urn = 'urn:oid:131o'")
    if not record:
        return None
    systemId = forceInt(record.value('id'))

    mesDispansIdList = params.get('mesDispansIdList', [])
    if mesDispansIdList:
        mesDispans = u''' AND Event.MES_id IN (%s)'''%(u','.join(forceString(mesId) for mesId in mesDispansIdList if mesId))
    else:
        mesDispans = u''

    orgStructure = u''
    if orgStructureId:
        personIdList = getOrgStructurePersonIdList(orgStructureId)
        if personIdList:
            orgStructure = u''' AND Event.execPerson_id IN (%s)'''%(u','.join(str(personId) for personId in personIdList if personId))

    if dispType == 0:
        dispTypeStr = u"'8011', '8008', '8009','8014','8015'"
    elif dispType == 1:
        dispTypeStr = u"'8008', '8009','8014','8015'"
    else:
        dispTypeStr = u"'8011'"

    stmt = u'''
SELECT
    Client.id AS clientId,
    age(Client.birthDate, Event.execDate) AS clientAge,
    Client.sex AS clientSex,
    Diagnosis.MKB,
    rbDiseaseStage.code AS `stage`,
    rbDiseaseCharacter.code AS `character`,
    
    EXISTS(SELECT Event.id FROM Client c 
      LEFT JOIN Event e ON e.client_id = c.id 
      LEFT JOIN EventType et ON et.id = e.eventType_id
      LEFT JOIN rbEventProfile rbep ON rbep.id = et.eventProfile_id
      LEFT JOIN Diagnostic dc ON dc.event_id = e.id
      LEFT JOIN Diagnosis ds ON ds.id = dc.diagnosis_id
      WHERE c.id = Client.id AND rbep.code IN ('8008', '8014') AND e.id != Event.id AND Diagnosis.MKB = ds.MKB
      AND (e.execDate >= %(begDate)s AND e.execDate < %(endDate)s) AND dc.deleted = 0
  ) AS hasInFirst,

    EXISTS(SELECT 1
           FROM Diagnostic AS D
           LEFT JOIN rbDispanser ON rbDispanser.id = D.dispanser_id
           WHERE D.diagnosis_id = Diagnosis.id AND D.deleted = 0
              AND rbDispanser.code IN ('1', '2', '6')
          ) AS isObserved,

    EXISTS(SELECT 1
           FROM Action
           JOIN ActionType ON Action.actionType_id = ActionType.id
           JOIN ActionProperty AP ON AP.action_id = Action.id
           JOIN ActionPropertyType APT ON AP.type_id = APT.id
           JOIN ActionProperty_String APS ON AP.id = APS.id
           WHERE Action.deleted = 0 AND AP.deleted = 0 AND APT.deleted = 0
              AND ActionType.deleted = 0 AND APT.descr = '5001'
              AND ActionType.serviceType IN (1,2) AND APS.value = '<140/90'
              AND Action.event_id = Event.id
          ) AS hasPropPressure

FROM Client
LEFT JOIN Event ON Client.id = Event.client_id
LEFT JOIN Diagnostic ON Diagnostic.event_id = Event.id
LEFT JOIN Diagnosis ON Diagnosis.id = Diagnostic.diagnosis_id
LEFT JOIN rbDiseaseCharacter ON rbDiseaseCharacter.id = Diagnostic.character_id
LEFT JOIN EventType ON EventType.id = Event.eventType_id
LEFT  JOIN rbDiseasePhases ON rbDiseasePhases.id = Diagnostic.phase_id
LEFT  JOIN rbDiseaseStage ON rbDiseaseStage.id = Diagnostic.stage_id

LEFT JOIN Action ON Action.event_id = Event.id
LEFT JOIN ActionType ON Action.actionType_id = ActionType.id
LEFT JOIN rbService ON rbService.id = ActionType.nomenclativeService_id
LEFT JOIN rbService_Identification ON rbService_Identification.master_id = rbService.id
LEFT JOIN rbAccountingSystem ON rbAccountingSystem.id = rbService_Identification.system_id
LEFT JOIN rbEventProfile ON rbEventProfile.id = EventType.eventProfile_id
WHERE Event.deleted = 0
  AND (Event.execDate >= %(begDate)s AND Event.execDate < %(endDate)s)
  %(orgStructure)s
  AND Diagnostic.deleted = 0
  AND Diagnosis.deleted = 0
  AND (Diagnosis.MKB BETWEEN 'A00' and 'T98.99')
  AND Client.deleted = 0
  AND EventType.deleted = 0
  AND rbService_Identification.deleted = 0
  AND rbAccountingSystem.code = '131o'
  AND rbEventProfile.code IN (%(dispType)s)
  AND (rbDiseasePhases.code != '10' OR rbDiseasePhases.id IS NULL)
  AND (rbDiseaseCharacter.code IN ('1', '2', '3') OR rbDiseaseCharacter.code IS NULL)
  AND EventType.context != 'flag'
  AND EventType.code != 'flag' 
  GROUP BY Diagnostic.id
  ''' % {
        'begDate':      db.formatDate(begDate),
        'endDate':      db.formatDate(endDate.addDays(1)),
        'orgStructure': orgStructure,
        'systemId':     systemId,
        'dispType':     dispTypeStr,
    }
    return db.query(stmt)


class CReportForm131_o_5000_2021(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Сведения о выявленных заболеваниях (случаев) (2021)')


    def getSetupDialog(self, parent):
        result = CReportForm131SetupDialog2021(parent)
        result.setTitle(self.title())
        return result


    def getReportData(self, params, query):
        begDate = params.get('begDate', QDate())
        retirementAgeM, retirementAgeF = getRetirementAge(begDate)
        clients5001 = set()
        mapRows = createMapCodeToRowIdx( [row[2] for row in MainRows] )
        reportData = [ [0]*10 for row in MainRows ]
        notClasifiedRow = len(MainRows)-1
        if not query:
            return reportData, 0

        def isInWorkingAge(clientAge, clientSex):
            if clientSex == 1: # М
                return 16 <= clientAge < retirementAgeM
            if clientSex == 2: # Ж
                return 16 <= clientAge < retirementAgeF
            return False

        def isOlderWorkingAge(clientAge, clientSex):
            if clientSex == 1: # М
                return clientAge >= retirementAgeM
            if clientSex == 2: # Ж
                return clientAge >= retirementAgeF
            return False

        while query.next():
            record = query.record()
            clientId = forceInt(record.value('clientId'))
            clientAge = forceInt(record.value('clientAge'))
            clientSex = forceInt(record.value('clientSex'))
            stage = forceInt(record.value('stage'))
            character = forceString(record.value('character'))
            MKB = normalizeMKB(forceString(record.value('MKB')))
            isObserved = forceInt(record.value('isObserved'))
            hasPropPressure = forceInt(record.value('hasPropPressure'))
            hasInFirst = forceInt(record.value('hasInFirst'))
            if hasPropPressure:
                clients5001.add(clientId)

            rows = mapRows.get(MKB, [])
            destRows = rows[:]
            for row in rows:
                if MainRows[row][1] in ('2.1', '2.3', '2.5', '2.7', '2.9', '2.11', '2.13', '2.15', '2.23') and stage in (1, 2):
                    destRows.append(row + 1)
                elif MainRows[row][1] in ('2.17', '2.20'):
                    if stage in (0, 1):
                        destRows.append(row + 1)
                    elif stage == 2:
                        destRows.append(row + 2)
            if len(destRows) == 0:
                destRows = [ notClasifiedRow ]

            for row in destRows:
                if not hasInFirst:
                    reportLine = reportData[row]
                    reportLine[0] += 1
                    reportLine[1] += isObserved
                    reportLine[2] += isInWorkingAge(clientAge, clientSex)
                    reportLine[3] += isOlderWorkingAge(clientAge, clientSex)
                    if character in ('1', '2'):
                        reportLine[4] += 1
                        reportLine[5] += isObserved
                        if isInWorkingAge(clientAge, clientSex):
                            reportLine[6] += 1
                            reportLine[7] += isObserved
                        if isOlderWorkingAge(clientAge, clientSex):
                            reportLine[8] += 1
                            reportLine[9] += isObserved

        return reportData, len(clients5001)



    def build(self, params):
        query = selectData(params)
        reportData, clients5001 = self.getReportData(params, query)

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        cursor.insertText('(5000)')
        cursor.insertBlock()
        tableColumns = [
            ('20%',  [u'Наименование классов и отдельных заболеваний', u'', u'', u'1'], CReportBase.AlignLeft),
            ('3%',   [u'№ строки', u'', u'', u'2'], CReportBase.AlignLeft),
            ('5%',   [u'Код МКБ-10', u'', u'', u'3'], CReportBase.AlignLeft),
            ('7.2%', [u'Выявлено заболеваний', u'всего', u'всего', u'4'], CReportBase.AlignRight),
            ('7.2%', [u'', u'', u'из них: установлено диспансерное наблюдение', u'5'], CReportBase.AlignRight),
            ('7.2%', [u'', u'в том числе:', u'В трудоспособном возрасте', u'6'], CReportBase.AlignRight),
            ('7.2%', [u'', u'', u'В возрасте старше трудоспособного', u'7'], CReportBase.AlignRight),
            ('7.2%', [u'из них: с впервые в жизни установленным диагнозом', u'всего', u'всего', u'8'], CReportBase.AlignRight),
            ('7.2%', [u'', u'', u'из них: установлено диспансерное наблюдение', u'9'], CReportBase.AlignRight),
            ('7.2%', [u'', u'в трудоспособном возрасте', u'всего', u'10'], CReportBase.AlignRight),
            ('7.2%', [u'', u'', u'из них: установлено диспансерное наблюдение', u'11'], CReportBase.AlignRight),
            ('7.2%', [u'', u'в возрасте старше трудоспособного', u'всего', u'12'], CReportBase.AlignRight),
            ('7.2%', [u'', u'', u'из них: установлено диспансерное наблюдение', u'13'], CReportBase.AlignRight),
        ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0,0, 3,1)
        table.mergeCells(0,1, 3,1)
        table.mergeCells(0,2, 3,1)
        table.mergeCells(0,3, 1,4)
        table.mergeCells(0,7, 1,6)

        table.mergeCells(1,3,  1,2)
        table.mergeCells(1,5,  1,2)
        table.mergeCells(1,7,  1,2)
        table.mergeCells(1,9,  1,2)
        table.mergeCells(1,11, 1,2)

        for row, rowDescr in enumerate(MainRows):
            reportLine = reportData[row]
            i = table.addRow()
            table.setText(i, 0, rowDescr[0])
            table.setText(i, 1, rowDescr[1])
            table.setText(i, 2, rowDescr[2])
            for col, value in enumerate(reportLine):
                table.setText(i, 3+col, value)

        table.mergeCells(6,2,  2,1)
        table.mergeCells(8,2,  2,1)
        table.mergeCells(10,2, 2,1)
        table.mergeCells(12,2, 2,1)
        table.mergeCells(14,2, 2,1)
        table.mergeCells(16,2, 2,1)
        table.mergeCells(18,2, 2,1)
        table.mergeCells(20,2, 2,1)
        table.mergeCells(22,2, 3,1)
        table.mergeCells(25,2, 3,1)
        table.mergeCells(28,2, 2,1)

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        table = createTable(cursor, [('50%', [''], CReportBase.AlignLeft), ('50%', [''], CReportBase.AlignLeft)])
        fmt = table.table.format()
        fmt.setBorder(0)
        table.table.setFormat(fmt)
        table.setText(0, 0, u'(5001)')
        table.setText(0, 1, u'Код по ОКЕИ: человек - 792')
        cursor.movePosition(QtGui.QTextCursor.End)

        cursor.insertBlock()
        cursor.insertText(u'Число лиц с артериальным давлением ниже 140/90 мм рт. ст. на фоне приема гипотензивных лекарственных препаратов, при наличии болезней, характеризующихся повышенным кровяным давлением (I10 - I15 по МКБ-10) ')
        cursor.insertText(str(clients5001))
        return doc

