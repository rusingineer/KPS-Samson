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

from library.Utils             import forceInt, forceString, forceBool
from Reports.Report            import CReport
from Reports.ReportBase        import CReportBase, createTable
from Orgs.Utils                import getOrgStructurePersonIdList

from Reports.ReportForm131_o_2000_2021 import CReportForm131SetupDialog2021



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
    orgStructure = u''
    if orgStructureId:
        personIdList = getOrgStructurePersonIdList(orgStructureId)
        if personIdList:
            orgStructure = u' AND Event.setPerson_id IN (%s)'%(u','.join(str(personId) for personId in personIdList if personId))

    mesDispansIdList = params.get('mesDispansIdList', [])
    if mesDispansIdList:
        mesDispans = u' AND Event.MES_id IN (%s)'%(u','.join(forceString(mesId) for mesId in mesDispansIdList if mesId))
    else:
        mesDispans = u''

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

  EXISTS(SELECT API.id
    FROM Action AS A
    JOIN ActionPropertyType AS APT ON APT.actionType_id = A.actionType_id
    JOIN ActionProperty AS AP  ON (APT.id = AP.type_id AND AP.action_id = A.id)
    JOIN ActionType AS AT      ON AT.id = A.actionType_id
    JOIN ActionProperty_Integer AS API ON API.id = AP.id
    
    WHERE APT.deleted = 0 AND A.event_id = Event.id AND A.deleted = 0
    AND AP.deleted = 0
    AND AT.name LIKE '%%Прохождение 1 этапа ДОГВН или ПМО%%'
    AND APT.name LIKE '%%относительный сердечно-сосудистый риск%%'
    AND API.value > 1
  ) AS hasRelativeRisk,

  EXISTS(SELECT API.id
    FROM Action AS A
    JOIN ActionPropertyType AS APT ON APT.actionType_id = A.actionType_id
    JOIN ActionProperty AS AP  ON (APT.id = AP.type_id AND AP.action_id = A.id)
    JOIN ActionType AS AT      ON AT.id = A.actionType_id
    JOIN ActionProperty_Integer AS API ON API.id = AP.id
    
    WHERE APT.deleted = 0 AND A.event_id = Event.id AND A.deleted = 0
    AND AP.deleted = 0
    AND AT.name LIKE '%%Прохождение 1 этапа ДОГВН или ПМО%%'
    AND APT.name LIKE '%%абсолютный сердечно-сосудистый риск%%'
    AND API.value > 5
  ) AS hasAbsoluteRisk
    
FROM Event
JOIN Client ON Client.id = Event.client_id
JOIN Diagnostic ON Diagnostic.event_id = Event.id
JOIN Diagnosis ON Diagnostic.diagnosis_id = Diagnosis.id
JOIN rbDiagnosisType ON Diagnosis.diagnosisType_id = rbDiagnosisType.id
LEFT JOIN Action ON Action.event_id = Event.id
LEFT JOIN ActionType ON Action.actionType_id = ActionType.id
LEFT JOIN rbService ON rbService.id = ActionType.nomenclativeService_id
LEFT JOIN rbService_Identification ON rbService_Identification.master_id = rbService.id
LEFT JOIN rbAccountingSystem ON rbAccountingSystem.id = rbService_Identification.system_id
LEFT JOIN EventType ON Event.eventType_id = EventType.id
LEFT JOIN rbEventProfile ON rbEventProfile.id = EventType.eventProfile_id
WHERE Event.deleted = 0
  AND (Event.execDate >= %(begDate)s AND Event.execDate < %(endDate)s)
  AND Client.deleted = 0
  AND Diagnostic.deleted = 0
  AND Diagnosis.deleted = 0
  AND Event.prevEvent_id IS NULL
  %(orgStructure)s
  %(mesDispans)s
  AND Diagnostic.setDate < %(endDate)s
  AND (Diagnostic.endDate >= %(begDate)s OR Diagnostic.endDate IS NULL)
  
  AND rbDiagnosisType.code IN ('1','2','4','3','98','9','10','11')
  AND Diagnosis.mod_id IS NULL
  AND rbAccountingSystem.code = '131o'
    AND rbEventProfile.code IN (%(dispType)s)
    GROUP BY Diagnostic.id
    ''' % {
        'begDate': db.formatDate(begDate),
        'endDate': db.formatDate(endDate.addDays(1)),
        'orgStructure': orgStructure,
        'mesDispans': mesDispans,
        'dispType': dispTypeStr,
        'systemId': systemId,
    }

    return db.query(stmt)



class CReportForm131_o_4000_2021(CReport):

    rows = (
        (u'', u'Гиперхолестеринемия', 'E78'),
        (u'', u'Гипергликемия', 'R73.9'),
        (u'', u'Курение табака', 'Z72.0'),
        (u'', u'Нерациональное питание', 'Z72.4'),
        (u'', u'Избыточная масса тела', 'R63.5'),
        (u'', u'Ожирение', 'E66'),
        (u'', u'Низкая физическая активность', 'Z72.3'),
        (u'', u'Риск пагубного потребления алкоголя', 'Z72.1'),
        (u'', u'Риск потребления наркотических средств и психотропных веществ без назначения врача', 'Z72.2'),
        (u'Отягощенная наследственность по сердечно-сосудистым заболеваниям', u'инфаркт миокарда', 'Z82.4'),
        (u'', u'мозговой инсульт', 'Z82.3'),
        (u'Отягощенная наследственность по злокачественным новообразованиям', u'колоректальной области', 'Z80.0'),
        (u'', u'других локализаций', 'Z80.9'),
        (u'', u'Отягощенная наследственность по хроническим болезням нижних дыхательных путей', 'Z82.5'),
        (u'', u'Отягощенная наследственность по сахарному диабету', 'Z83.3'),
        (u'', u'Высокий (5% и более) или очень высокий (10% и более) абсолютный сердечно-сосудистый риск', '-'),
        (u'', u'Высокий (более 1 ед.) относительный сердечно-сосудистый риск', '-'),
        (u'', u'Старческая астения', 'R54'),
    )

    mapMKBToRows = {
        'E78'   : 0,
        'R73.9' : 1,
        'Z72.0' : 2,
        'Z72.4' : 3,
        'R63.5' : 4,
        'E66'   : 5,
        'Z72.3' : 6,
        'Z72.1' : 7,
        'Z72.2' : 8,
        'Z82.4' : 9,
        'Z82.3' : 10,
        'Z80.0' : 11,
        'Z80.9' : 12,
        'Z82.5' : 13,
        'Z83.3' : 14,
        'R54'   : 17,
    }

    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Сведения о выявленных при проведении профилактического медицинского осмотра (диспансеризации) факторах риска и других патологических состояниях и заболеваниях, повышающих вероятность развития хронических неинфекционных заболеваний (далее - факторы риска)')


    def getSetupDialog(self, parent):
        result = CReportForm131SetupDialog2021(parent)
        result.setTitle(self.title())
        return result


    def getReportData(self, query):
        reportData = [ [0]*9 for row in xrange(len(self.rows)) ]
        reportData4001 = set()
        hasRiskFactorSet = set()
        clientUniqueSet = set()
        if not query:
            return reportData, 0
        while query.next():
            record = query.record()
            MKB = forceString(record.value('MKB'))
            clientAge = forceInt(record.value('clientAge'))
            clientSex = forceInt(record.value('clientSex'))
            clientId = forceInt(record.value('clientId'))
            hasAbsoluteRisk = forceBool(record.value('hasAbsoluteRisk'))
            hasRelativeRisk = forceBool(record.value('hasRelativeRisk'))
            # hasRiscFactor = MKB in ('Z72.0', 'Z72.4', 'Z72.3', 'Z72.1', 'Z72.2')
            clientUniqueSet.add(clientId)
            if MKB in ('Z72.0', 'Z72.4', 'Z72.3', 'Z72.1', 'Z72.2'):
                hasRiskFactorSet.add(clientId)

            targetRow = self.mapMKBToRows.get(MKB)
            if targetRow is None:
                targetRow = self.mapMKBToRows.get(MKB.split('.')[0])

            if targetRow is None:
                if hasAbsoluteRisk and 40 <= clientAge <= 65:
                    targetRow = 15
                elif hasRelativeRisk and 18 <= clientAge <= 39:
                    targetRow = 16
                else:
                    continue
            reportLine = reportData[targetRow]

            # if not hasRiscFactor:
            #     reportData4001.add(clientId)

            if clientSex == 1:
                if 16 <= clientAge <= 60:
                    reportLine[4] += 1
                elif clientAge >= 61:
                    reportLine[5] += 1
            elif clientSex == 2:
                if 16 <= clientAge <= 55:
                    reportLine[7] += 1
                elif clientAge >= 56:
                    reportLine[8] += 1

        for client in clientUniqueSet:
            if client not in hasRiskFactorSet:
                reportData4001.add(client)
        for line in reportData:
            line[6] = line[7] + line[8]
            line[3] = line[4] + line[5]
            line[1] = line[4] + line[7]
            line[2] = line[5] + line[8]
            line[0] = line[1] + line[2]

        return reportData, len(reportData4001)


    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        cursor.insertText(u'(4000)')
        cursor.insertBlock()
        tableColumns = [
            ('12.5%',[u'Наименование факторов риска и других патологических состояний и заболеваний', u'', u'', u'', u'1'], CReportBase.AlignLeft),
            ('12.5%',[u'', u'', u'', u'', u''], CReportBase.AlignLeft),
            ('6%',   [u'Код МКБ-10', u'', u'', u'', u'2'], CReportBase.AlignLeft),
            ('4%',   [u'№ строки', u'', u'', u'', u'3'], CReportBase.AlignRight),
            ('7.2%', [u'Все взрослое население', u'Всего', u'', u'', u'4'], CReportBase.AlignRight),
            ('7.2%', [u'', u'в том числе:', u'в трудоспособном возрасте', u'', u'5'], CReportBase.AlignRight),
            ('7.2%', [u'', u'', u'в возрасте старше трудоспособного', u'', u'6'], CReportBase.AlignRight),
            ('7.2%', [u'в том числе:', u'Мужчины', u'Всего', u'', u'7'], CReportBase.AlignRight),
            ('7.2%', [u'', u'', u'в том числе:', u'в трудоспособном возрасте', u'8'], CReportBase.AlignRight),
            ('7.3%', [u'', u'', u'', u'в возрасте старше трудоспособного', u'9'], CReportBase.AlignRight),
            ('7.2%', [u'', u'Женщины', u'Всего', u'', u'10'], CReportBase.AlignRight),
            ('7.2%', [u'', u'', u'в том числе:', u'в трудоспособном возрасте', u'11'], CReportBase.AlignRight),
            ('7.3%', [u'', u'', u'', u'в возрасте старше трудоспособного', u'12'], CReportBase.AlignRight),
        ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0,  4, 2)
        table.mergeCells(0, 2,  4, 1)
        table.mergeCells(0, 3,  4, 1)
        table.mergeCells(0, 4,  1, 3)
        table.mergeCells(0, 7,  1, 6)
        table.mergeCells(1, 4,  3, 1)
        table.mergeCells(1, 5,  1, 2)
        table.mergeCells(1, 7,  1, 3)
        table.mergeCells(1, 10, 1, 3)
        table.mergeCells(2, 5,  2, 1)
        table.mergeCells(2, 6,  2, 1)
        table.mergeCells(2, 7,  2, 1)
        table.mergeCells(2, 8,  1, 2)
        table.mergeCells(2, 10, 2, 1)
        table.mergeCells(2, 11, 1, 2)
        table.mergeCells(4, 0,  1, 2)

        query = selectData(params)
        reportData, reportData4001 = self.getReportData(query)
        for row, reportLine in enumerate(reportData):
            i = table.addRow()
            table.setText(i, 0, self.rows[row][0])
            table.setText(i, 1, self.rows[row][1])
            table.setText(i, 2, self.rows[row][2])
            table.setText(i, 3, row+1)
            for idx, value in enumerate(reportLine):
                table.setText(i, idx+4, value)

        for i in xrange(9):
            table.mergeCells(5+i, 0, 1, 2)
        table.mergeCells(14, 0, 2, 1)
        table.mergeCells(16, 0, 2, 1)
        for i in xrange(5):
            table.mergeCells(18+i, 0, 1, 2)

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        table = createTable(cursor, [('50%', [''], CReportBase.AlignLeft), ('50%', [''], CReportBase.AlignLeft)])
        fmt = table.table.format()
        fmt.setBorder(0)
        table.table.setFormat(fmt)
        table.setText(0, 0, u'(4001)')
        table.setText(0, 1, u'Код по ОКЕИ: человек - 792')
        cursor.movePosition(QtGui.QTextCursor.End)

        cursor.insertBlock()
        cursor.insertText(u'Число лиц, у которых по строкам 3, 4, 7, 8, 9 отсутствуют факторы риска ')
        cursor.insertText(str(reportData4001))

        return doc

