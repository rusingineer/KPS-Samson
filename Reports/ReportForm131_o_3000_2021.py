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

from library.Utils             import forceDate, forceInt, forceRef, forceString

from Events.ActionStatus       import CActionStatus
from Reports.Report            import CReport
from Reports.ReportBase        import CReportBase, createTable
from Reports.ReportSetupDialog import CReportSetupDialog
from Orgs.Utils                import getOrgStructurePersonIdList


def selectData(params):
    begDate = params.get('begDate', QDate())
    endDate = params.get('endDate', QDate())
    orgStructureId = params.get('orgStructureId', None)
    if not endDate:
        return None
    db = QtGui.qApp.db
    # record = db.getRecordEx('rbAccountingSystem', 'id', "urn = 'urn:oid:131o'")
    # if not record:
    #     return None
    # systemId = forceInt(record.value('id'))
    orgStructure = u''
    if orgStructureId:
        personIdList = getOrgStructurePersonIdList(orgStructureId)
        if personIdList:
            orgStructure = u''' AND Event.execPerson_id IN (%s)'''%(u','.join(str(personId) for personId in personIdList if personId))
    mesDispansIdList = params.get('mesDispansIdList', [])
    if mesDispansIdList:
        mesDispans = u''' AND Event.MES_id IN (%s)'''%(u','.join(forceString(mesId) for mesId in mesDispansIdList if mesId))
    else:
        mesDispans = u''

    stmt = u'''
SELECT
    Client.id AS clientId,
    Event.id AS eventId,
    Action.MKB AS actionMkb,
    Action.status,
    Action.endDate,
    Event.execDate,
    
    DATE(Action.endDate) < DATE(Event.setDate) AS isActionExecPrev,
    
    DATE(Action.endDate) BETWEEN DATE(%(begDate)s) AND DATE(%(endDate)s) AS isActionExecNow,
    rbService.code AS serviceCode,
    rbResult.name AS resultName,
    ActionType.flatCode,
    (Event.prevEvent_id IS NOT NULL) AS hasPrevEvent,
    rbMesSpecification.regionalCode AS mesLevel,
    IF(rbEventProfile.code IN ('8009', '8015'), 1, 0) as isDisp2,
    
    EXISTS(SELECT EC.id FROM Client CC 
    LEFT JOIN Event EC ON EC.client_id = CC.id
    LEFT JOIN EventType ETC ON EC.eventType_id = ETC.id
    LEFT JOIN rbEventProfile EPC ON EPC.id = ETC.eventProfile_id AND EPC.code IN ('8009', '8015')
    LEFT JOIN rbResult RC ON EC.result_id = RC.id
    WHERE CC.id = Client.id AND EC.id != Event.id AND rbEventProfile.code IN ('8008', '8014') AND rbResult.regionalCode IN ('353', '357', '358')
    AND (EC.execDate >= %(begDate)s AND EC.execDate < %(endDate)s AND EPC.code NOT IN ('8009', '8015') OR EPC.code IN ('8009', '8015') AND EC.execDate IS NULL)
    ) AS isCancelDisp,
    IF(rbResult.regionalCode IN ('353', '357', '358'),1,0) AS isRegCode,

    EXISTS(SELECT EC2.id FROM Client CC2 
    LEFT JOIN Event EC2 ON EC2.client_id = CC2.id
    LEFT JOIN EventType ETC2 ON EC2.eventType_id = ETC2.id
    LEFT JOIN rbEventProfile EPC2 ON EPC2.id = ETC2.eventProfile_id
    WHERE EPC2.code IN ('8009', '8015') AND CC2.id = Client.id) AS hasDisp2,

    EXISTS(SELECT 1
      FROM Event E
      JOIN Visit ON Visit.event_id = E.id
      JOIN rbService_Identification AS rbSI ON Visit.service_id = rbSI.master_id
      JOIN rbAccountingSystem AS rbAS ON rbAS.id = rbSI.system_id
      JOIN EventType as ET ON ET.id = E.eventType_id
      JOIN rbEventProfile as rbEP ON rbEP.id = ET.eventProfile_id
      WHERE E.id = Event.id AND rbAS.code = '131o'
        AND rbEP.code IN ('8009', '8015')
        AND Visit.deleted = 0 AND rbSI.deleted = 0
        AND (rbSI.value = 'B01.047.01' OR rbSI.value = 'B01.026.01')
    ) AS isPropertyServiceCode,

    (SELECT rbSI2.value
     FROM rbService_Identification AS rbSI2
     WHERE rbSI2.master_id = ActionType.nomenclativeService_id
      AND rbSI2.system_id = rbAccountingSystem.id AND rbSI2.deleted = 0
      LIMIT 1
    ) AS serviceCode2,

    EXISTS(SELECT 1
           FROM ActionProperty
           WHERE ActionProperty.action_id = Action.id
             AND ActionProperty.deleted = 0
             AND ActionProperty.evaluation IS NOT NULL
             AND ActionProperty.evaluation != 0
          ) AS propertyEvaluation,

    EXISTS(SELECT AP.id
     FROM Action A
     LEFT JOIN ActionType AType ON A.actionType_id = AType.id
     LEFT JOIN ActionProperty AP ON AP.action_id = A.id
     LEFT JOIN ActionProperty AP2 ON AP2.action_id = A.id
     LEFT JOIN ActionProperty_String APS ON AP.id = APS.id
     LEFT JOIN ActionPropertyType APType ON APType.id = AP.type_id
      LEFT JOIN ActionPropertyType APType2 ON APType2.id = AP2.type_id    
     LEFT JOIN ActionProperty_rbSpeciality APSpec ON AP2.id = APSpec.id
     LEFT JOIN rbSpeciality ON APSpec.value = rbSpeciality.id
     WHERE AP.deleted = 0 AND AType.deleted = 0
        AND A.event_id = Event.id 
        AND AType.flatCode = 'appointments'
        AND APType.name = 'Назначения: направлен на'
        AND APType2.name = 'Специальность'
        AND APS.value LIKE '%%консультацию%%'
        AND rbSpeciality.name LIKE '%%онколог%%'
     LIMIT 1
    ) AS personSpeciality,

    (SELECT Diagnosis.MKB
    FROM Diagnosis INNER JOIN Diagnostic ON Diagnostic.diagnosis_id=Diagnosis.id
    INNER JOIN rbDiagnosisType ON Diagnostic.diagnosisType_id=rbDiagnosisType.id
    INNER JOIN rbDiseaseCharacter ON Diagnostic.character_id=rbDiseaseCharacter.id
    INNER JOIN rbDiseasePhases ON Diagnostic.phase_id=rbDiseasePhases.id
    WHERE Diagnostic.event_id = Event.id AND Diagnosis.deleted = 0 AND Diagnostic.deleted = 0
    AND rbDiseasePhases.code = '10' AND rbDiseaseCharacter.code = 2
    AND (rbDiagnosisType.code = '1'
    OR (rbDiagnosisType.code = '2' AND Diagnostic.person_id = Event.execPerson_id
    AND (NOT EXISTS (SELECT DC.id FROM Diagnostic AS DC
    INNER JOIN rbDiagnosisType AS DT ON DT.id = DC.diagnosisType_id WHERE DT.code = '1'
    AND DC.event_id = Event.id AND DC.deleted = 0
    LIMIT 1)))) LIMIT 1) AS MKB,

    (SELECT Diagnostic.setDate
    FROM Diagnosis INNER JOIN Diagnostic ON Diagnostic.diagnosis_id=Diagnosis.id
    INNER JOIN rbDiagnosisType ON Diagnostic.diagnosisType_id=rbDiagnosisType.id
    INNER JOIN rbDiseaseCharacter ON Diagnostic.character_id=rbDiseaseCharacter.id
    INNER JOIN rbDiseasePhases ON Diagnostic.phase_id=rbDiseasePhases.id
    WHERE Diagnostic.event_id = Event.id AND Diagnosis.deleted = 0 AND Diagnostic.deleted = 0
    AND rbDiseasePhases.code = '10' AND rbDiseaseCharacter.code = 2
    AND (rbDiagnosisType.code = '1'
    OR (rbDiagnosisType.code = '2' AND Diagnostic.person_id = Event.execPerson_id
    AND (NOT EXISTS (SELECT DC.id FROM Diagnostic AS DC
    INNER JOIN rbDiagnosisType AS DT ON DT.id = DC.diagnosisType_id WHERE DT.code = '1'
    AND DC.event_id = Event.id AND DC.deleted = 0
    LIMIT 1)))) LIMIT 1) AS MKBDate,
    
    EXISTS(SELECT apb.value 
        FROM ActionType atp 
        left JOIN Action a1et ON a1et.actionType_id = atp.id
        LEFT JOIN ActionPropertyType apt1et ON atp.id = apt1et.actionType_id  AND apt1et.deleted = 0
        LEFT JOIN ActionProperty ap1et on ap1et.action_id = a1et.id AND ap1et.type_id = apt1et.id AND ap1et.deleted = 0
        left JOIN ActionProperty_Boolean apb ON ap1et.id = apb.id
      WHERE atp.flatCode = 'disp_2et_act' AND a1et.deleted = 0 AND a1et.event_id = Event.id AND (apt1et.shortName = rbService_Identification.value or apt1et.shortName = rbService.code)
      AND apb.value = 1 LIMIT 1) AS pat

FROM Event
JOIN EventType ON Event.eventType_id = EventType.id
LEFT JOIN Action ON Action.event_id = Event.id
JOIN ActionType ON Action.actionType_id = ActionType.id
JOIN Client ON Client.id = Event.client_id
LEFT JOIN rbEventProfile ON rbEventProfile.id = EventType.eventProfile_id
LEFT JOIN rbResult ON Event.result_id = rbResult.id
LEFT JOIN rbService ON rbService.id = ActionType.nomenclativeService_id
LEFT JOIN rbService_Identification ON rbService_Identification.master_id = rbService.id
LEFT JOIN rbAccountingSystem ON rbAccountingSystem.id=rbService_Identification.system_id   
LEFT JOIN rbMesSpecification ON Event.mesSpecification_id = rbMesSpecification.id
WHERE Event.deleted = 0
  AND (Event.execDate >= %(begDate)s AND Event.execDate < %(endDate)s)
    %(orgStructure)s
    %(mesDispans)s
    AND Action.deleted = 0
  AND Client.deleted = 0
  AND ActionType.deleted = 0
  AND EventType.deleted = 0
  AND rbEventProfile.code IN ('8008', '8009', '8014', '8015')
    AND rbAccountingSystem.code = '131o' AND rbService_Identification.deleted = 0
    GROUP BY Action.id
''' % { 'orgStructure':orgStructure,
        'begDate': db.formatDate(begDate),
        'endDate': db.formatDate(endDate.addDays(1)),
        'mesDispans' : mesDispans,
      }
    return db.query(stmt)




class CReportForm131_o_3000_2021(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Сведения о приемах (осмотрах), медицинских исследованиях и иных медицинских вмешательствах второго этапа диспансеризации')
        self.mapCodeToRow = {
            'B01.023.01': 0,
            'A04.12.005': 1,
            'B01.057.01': 2,
            'B01.053.01': 2,
            'B01.057.04': 3,
            'B01.018.01': 3,
            'A03.18.001': 4,
            'A03.16.001': 5,
            'A06.09.001.07': 6,
            'A06.09.008.001.08': 7,
            'A12.09.002.003': 8,
            'A12.09.001': 8,
            'B01.001.01': 9,
            'B01.028.01': 10,
            'B01.029.01': 11,
            'B04.070.003': 12,
            'B04.070.004.01': 13,
            'B04.070.004.02': 14,
            'B04.070.004.03': 15,
            'B04.070.004.04': 16,
            'B01.026.01': 17,
            'B01.047.01': 17,
        }
        self.rowDescr = [
            (u'Осмотр (консультация) врачом-неврологом', u'1'),
            (u'Дуплексное сканирование брахиоцефальных артерий', u'2'),
            (u'Осмотр (консультация) врачом-хирургом или врачом-урологом', u'3'),
            (u'Осмотр (консультация) врачом-хирургом или врачом-колопроктологом, включая проведение ректороманоскопии', u'4'),
            (u'Колоноскопия', u'5'),
            (u'Эзофагогастродуоденоскопия', u'6'),
            (u'Рентгенография легких', u'7'),
            (u'Компьютерная томография легких', u'8'),
            (u'Спирометрия', u'9'),
            (u'Осмотр (консультация) врачом акушером-гинекологом', u'10'),
            (u'Осмотр (консультация) врачом-оториноларингологом', u'11'),
            (u'Осмотр (консультация) врачом-офтальмологом', u'12'),
            (u'Индивидуальное или групповое (школа для пациентов) углубленное профилактическое консультирование для граждан:', u'13'),
            (u'с выявленными ишемической болезнью сердца, цереброваскулярными заболеваниями, хронической ишемией нижних конечностей атеросклеротического генеза или болезнями, характеризующимися повышенным кровяным давлением', u'13.1'),
            (u'с выявленным по результатам анкетирования риском пагубного потребления алкоголя и (или) потребления наркотических средств и психотропных веществ без назначения врача', u'13.2'),
            (u'в возрасте 65 лет и старше в целях коррекции выявленных факторов риска и (или) профилактики старческой астении', u'13.3'),
            (u'при выявлении высокого относительного, высокого и очень высокого абсолютного сердечно-сосудистого риска, и (или) ожирения и (или) гиперхолестеринемии с уровнем общего холестерина 8 ммоль/л и более, а также установленном по результатам анкетирования курении более 20 сигарет в день, риске пагубного потребления алкоголя и (или) риске немедицинского потребления наркотических средств и психотропных веществ', u'13.4'),
            (u'Прием (осмотр) врачом-терапевтом по результатам второго этапа диспансеризации', u'14'),
            (u'Направление на осмотр (консультацию) врачом-онкологом при подозрении на онкологические заболевания', u'15'),
        ]


    def getSetupDialog(self, parent):
        result = CReportSetupDialog(parent)
        result.setEventTypeVisible(False)
        # result.setMesDispansListVisible(True)
        result.setOnlyPermanentAttachVisible(False)
        result.setOrgStructureVisible(True)
        result.setTitle(self.title())
        result.resize(0,0)
        return result


    def _getDefault(self):
        result = [ [0, 0, 0, 0, 0]
                   for row in self.rowDescr
                 ]
        return result


    def getReportData(self, query, params):
        endDate = params.get('endDate', QDate())
        reportData = self._getDefault()
        reportLine14 = [set() for i in xrange(len(reportData[0]))]
        events = set()
        clients3001 = set()
        clients3002 = set()
        clients3003 = set()
        while query.next():
            record = query.record()
            clientId = forceRef(record.value('clientId'))
            eventId = forceRef(record.value('eventId'))
            actionMKB = forceString(record.value('actionMKB'))
            MKB = forceString(record.value('MKB'))
            MKBDate = forceDate(record.value('MKBDate'))
            serviceCode1 = forceString(record.value('serviceCode'))
            serviceCode2 = forceString(record.value('serviceCode2'))
            isPropertyServiceCode = forceInt(record.value('isPropertyServiceCode'))
            resultName = forceString(record.value('resultName')).lower()
            actionExecNow = forceInt(record.value('isActionExecNow'))
            actionExecPrev = forceInt(record.value('isActionExecPrev'))
            propertyEvaluation = forceInt(record.value('propertyEvaluation'))
            endDate = forceDate(record.value('endDate'))
            execDate = forceDate(record.value('execDate'))
            status = forceInt(record.value('status'))
            flatCode = forceString(record.value('flatCode'))
            hasPrevEvent = forceInt(record.value('hasPrevEvent'))
            personSpeciality = forceInt(record.value('personSpeciality'))
            mesLevel = forceInt(record.value('mesLevel'))
            patology = forceInt(record.value('pat'))
            isCancelDisp = forceInt(record.value('isCancelDisp'))
            isRegCode = forceInt(record.value('isRegCode'))
            hasDisp2 = forceInt(record.value('hasDisp2'))
            isDisp2 = forceInt(record.value('isDisp2'))


            # if hasPrevEvent:
            if isDisp2:
                if mesLevel == 1:
                    clients3001.add(clientId)
                if mesLevel == 2:
                    clients3002.add(clientId)
            else:
                if isCancelDisp or (not hasDisp2 and isRegCode):
                    clients3003.add(clientId)

            if isDisp2:

                actionExecRefusal  = (not endDate) and (status == CActionStatus.refused)
                if serviceCode2.startswith('B04.070.004.0'):
                    items = (serviceCode2, ) if serviceCode1 == serviceCode2 else (serviceCode1, serviceCode2)
                else:
                    items = (serviceCode2, ) if serviceCode1 == serviceCode2 else (serviceCode1, serviceCode2)

                for serviceCode in items:
                    targetRow = self.mapCodeToRow.get(serviceCode)
                    if targetRow is None:
                        if personSpeciality:
                            if eventId in events:
                                continue
                            events.add(eventId)
                            targetRow = 18
                        elif isPropertyServiceCode:
                            targetRow = 17
                        else:
                            continue
                    reportLine = reportData[targetRow]

                    # if hasPrevEvent:
                    if status != CActionStatus.canceled:
                        # reportLine14[0].add(eventId)
                        reportLine[0] += 1
                        if targetRow == 18 and MKBDate <= endDate:
                            reportLine[1] += 1
                    if execDate and endDate and status == CActionStatus.finished:
                        if targetRow != 18:
                            if actionExecNow:
                                # reportLine14[1].add(eventId)
                                reportLine[1] += 1
                            elif actionExecPrev:
                                # reportLine14[2].add(eventId)
                                reportLine[2] += 1
                    if actionExecRefusal:
                        # reportLine14[3].add(eventId)
                        reportLine[3] += 1
                    if (actionMKB and 'A00' <= actionMKB[:3] <= 'T98') or patology:
                        # reportLine14[4].add(eventId)
                        reportLine[4] += 1

        # reportLine = reportData[17]
        # for col in xrange(len(reportLine14)):
        #     reportLine[col] = len(reportLine14[col])

        # reportLine = reportData[12]  # строка 13 = сумма 13.1 + 13.4
        # for col in xrange(len(reportLine)):
        #     reportLine[col] += sum(reportData[row][col] for row in xrange(13,17))
        return reportData, len(clients3001), len(clients3002), len(clients3003)


    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        cursor.insertText(u'(3000)')
        cursor.insertBlock()
        tableColumns = [
            ('45%', [u'Медицинское вмешательство, входящее в объем второго этапа диспансеризации ', u'', u'1'], CReportBase.AlignLeft),
            ('3%',  [u'№ строки', u'', u'2'], CReportBase.AlignRight),
            ('10%', [u'Число лиц с выявленными медицинскими показаниями в рамках первого этапа диспансеризации ', u'', u'3'], CReportBase.AlignRight),
            ('10%', [u'Число выполненных медицинских мероприятий', u'в рамках диспансеризации', u'4'], CReportBase.AlignRight),
            ('10%', [u'', u'проведено ранее (в предшествующие 12 мес.)', u'5'], CReportBase.AlignRight),
            ('10%', [u'Число отказов', u'', u'6'], CReportBase.AlignRight),
            ('10%', [u'Впервые выявлено заболевание или патологическое состояние', u'', u'7'], CReportBase.AlignRight)
        ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 2, 1)
        table.mergeCells(0, 3, 1, 2)
        table.mergeCells(0, 5, 2, 1)
        table.mergeCells(0, 6, 2, 1)
        query = selectData(params)
        if query is None:
            return doc
        reportData, clients3001, clients3002, clients3003 = self.getReportData(query, params)
        for row, descr in enumerate(self.rowDescr):
            reportLine = reportData[row]
            i = table.addRow()
            table.setText(i, 0, descr[0])
            table.setText(i, 1, descr[1])
            table.setText(i, 2, reportLine[0])
            table.setText(i, 3, reportLine[1])
            table.setText(i, 4, reportLine[2])
            table.setText(i, 5, reportLine[3])
            table.setText(i, 6, 'X' if 12 <= row <= 16 else reportLine[4])
        table.setText(21, 4, 'X')
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()

        def writeInfoCode(code):
            table = createTable(cursor, [('50%', [''], CReportBase.AlignLeft), ('50%', [''], CReportBase.AlignLeft)])
            fmt = table.table.format()
            fmt.setBorder(0)
            table.table.setFormat(fmt)
            table.setText(0, 0, code)
            table.setText(0, 1, u'Код по ОКЕИ: человек - 792')
            cursor.movePosition(QtGui.QTextCursor.End)

        writeInfoCode(u'(3001)')
        cursor.insertBlock()
        cursor.insertText(u'Число лиц, прошедших полностью все мероприятия второго этапа диспансеризации, на которые они были направлены по результатам первого этапа ')
        cursor.insertText(str(clients3001))

        writeInfoCode(u'(3002)')
        cursor.insertBlock()
        cursor.insertText(u'Число лиц, прошедших частично (не все рекомендованные) мероприятия второго этапа диспансеризации, на которые они были направлены по результатам первого этапа ')
        cursor.insertText(str(clients3002))

        writeInfoCode(u'(3003)')
        cursor.insertBlock()
        cursor.insertText(u'Число лиц, не прошедших ни одного мероприятия второго этапа диспансеризации, на которые они были направлены по результатам первого этапа ')
        cursor.insertText(str(clients3003))
        return doc
