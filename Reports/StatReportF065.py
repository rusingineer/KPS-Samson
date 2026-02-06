# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2023 SAMSON Group. All rights reserved.
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

from library.Utils      import forceBool, forceInt, forceString, forceDate
from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable
from Orgs.Utils         import getOrgStructureDescendants


def selectData(params):
    begDate = params.get('begDate', QDate())
    endDate = params.get('endDate', QDate.currentDate())
    eventTypeId = params.get('eventTypeId')
    orgStructureId = params.get('orgStructureId')

    db = QtGui.qApp.db
    tableDiagnosis = db.table('Diagnosis')
    tablePerson = db.table('Person')
    tableEvent = db.table('Event')

    cond = [
        tableDiagnosis['setDate'].ge(begDate),
        tableDiagnosis['setDate'].lt(endDate.addDays(1)),
    ]
    if eventTypeId:
        cond.append(tableEvent['eventType_id'].eq(eventTypeId))
    if orgStructureId:
        cond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureDescendants(orgStructureId)))

    stmt = '''
    SELECT
        Client.id AS clientId,
        Diagnosis.MKB,
        Diagnostic.endDate,
        ({firstInPeriod}) AS firstInPeriod,
        rbDiseaseCharacter.code AS diseaseCharacterCode,
        rbDiagnosisType.code AS diagnosisTypeCode,
        age(Client.birthDate, Diagnosis.setDate) AS clientAge,
        Client.sex AS clientSex,
        rbDispanser.code AS dispanserCode
    FROM
        Event
        JOIN Diagnostic ON Diagnostic.event_id = Event.id
        JOIN Diagnosis ON Diagnostic.diagnosis_id = Diagnosis.id
        JOIN Client ON Diagnosis.client_id = Client.id
        JOIN Person ON Diagnostic.person_id = Person.id
        LEFT JOIN rbDiagnosisType ON rbDiagnosisType.id = Diagnosis.diagnosisType_id
        LEFT JOIN rbDiseaseCharacter ON rbDiseaseCharacter.id = Diagnosis.character_id
        LEFT JOIN rbDispanser ON Diagnostic.dispanser_id = rbDispanser.id
    WHERE
        Diagnosis.deleted = 0
        AND Diagnostic.deleted = 0
        AND Client.deleted = 0
        AND Event.deleted = 0
        AND Person.deleted = 0
        AND Event.client_id = Diagnosis.client_id
        AND Client.sex > 0
        AND LEFT(Diagnosis.MKB, 3) = 'B18'
        AND {cond}
    '''.format(
        firstInPeriod=db.joinAnd([
            tableDiagnosis['setDate'].le(endDate),
            tableDiagnosis['setDate'].ge(begDate),
        ]),
        cond=db.joinAnd(cond),
    )
    query = db.query(stmt)
    return query


class CStatReportF065_1000(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Форма 065 (1000)')


    def getSetupDialog(self, parent):
        dialog = CReport.getSetupDialog(self, parent)
        dialog.setWindowTitle(self.title())
        dialog.setOnlyPermanentAttachVisible(False)
        dialog.setOrgStructureVisible(True)
        dialog.adjustSize()
        return dialog


    def build(self, params):
        begDate = params.get('begDate', QDate())
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportSubTitle)
        cursor.insertText(u'Число заболеваний с впервые в жизни установленным диагнозом хронического вирусного гепатита')
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        cursor.insertText(u'(1000)')
        cursor.insertBlock()

        tableColumns = [
            ('', [u'Заболевания и пациенты', u'', u'', u'1'], CReportBase.AlignLeft),
            ('', [u'Пол', u'', u'', u'2'], CReportBase.AlignLeft),
            ('', [u'№ строки', u'', u'', u'3'], CReportBase.AlignLeft),
            ('', [u'Код по МКБ-10', u'', u'', u'4'], CReportBase.AlignLeft),
            ('', [u'Число заболеваний с впервые в жизни установленным диагнозом', u'Всего', u'', u'5'], CReportBase.AlignRight),
            ('', [u'', u'в том числе в возрасте', u'до 1 года', u'6'], CReportBase.AlignRight),
            ('', [u'', u'', u'1-2 года', u'7'], CReportBase.AlignRight),
            ('', [u'', u'', u'3-4 года', u'8'], CReportBase.AlignRight),
            ('', [u'', u'', u'5-9 лет', u'9'], CReportBase.AlignRight),
            ('', [u'', u'', u'10-14 лет', u'10'], CReportBase.AlignRight),
            ('', [u'', u'', u'15-17 лет', u'11'], CReportBase.AlignRight),
            ('', [u'', u'', u'18-24 года', u'12'], CReportBase.AlignRight),
            ('', [u'', u'', u'25-34 года', u'13'], CReportBase.AlignRight),
            ('', [u'', u'', u'35-44 года', u'14'], CReportBase.AlignRight),
            ('', [u'', u'', u'45-49 лет', u'15'], CReportBase.AlignRight),
            ('', [u'', u'', u'ж:50-55, м:50-60', u'16'], CReportBase.AlignRight),
            ('', [u'', u'', u'старше трудосп. возр.', u'17'], CReportBase.AlignRight),
        ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 3, 1)
        table.mergeCells(0, 1, 3, 1)
        table.mergeCells(0, 2, 3, 1)
        table.mergeCells(0, 3, 3, 1)
        table.mergeCells(0, 4, 1, 13)
        table.mergeCells(1, 4, 2, 1)
        table.mergeCells(1, 5, 1, 12)

        reportData = {}  # {MKB: [reportLineMale, reportLineFemale]}
        uniqueClients = [[set() for i in range(13)], [set() for i in range(13)]]  # [male, female]
        severalDiseasesUniqueClients = [[set() for i in range(13)], [set() for i in range(13)]]  # [male, female]

        def updateClientSets(column, clientSex, clientId):
            if clientId in uniqueClients[clientSex-1][column]:
                severalDiseasesUniqueClients[clientSex-1][column].add(clientId)
            uniqueClients[clientSex-1][column].add(clientId)

        query = selectData(params)
        while query.next():
            record = query.record()
            if forceBool(record.value('firstInPeriod')):
                MKB = forceString(record.value('MKB'))
                clientAge = forceInt(record.value('clientAge'))
                clientSex = forceInt(record.value('clientSex'))
                clientId = forceInt(record.value('clientId'))

                reportLine = reportData.setdefault(MKB, [[0]*13, [0]*13])[clientSex-1]
                reportLine[0] += 1
                if clientAge < 1:
                    reportLine[1] += 1
                    updateClientSets(1, clientSex, clientId)
                elif 1 <= clientAge <= 2:
                    reportLine[2] += 1
                    updateClientSets(2, clientSex, clientId)
                elif 3 <= clientAge <= 4:
                    reportLine[3] += 1
                    updateClientSets(3, clientSex, clientId)
                elif 5 <= clientAge <= 9:
                    reportLine[4] += 1
                    updateClientSets(4, clientSex, clientId)
                elif 10 <= clientAge <= 14:
                    reportLine[5] += 1
                    updateClientSets(5, clientSex, clientId)
                elif 15 <= clientAge <= 17:
                    reportLine[6] += 1
                    updateClientSets(6, clientSex, clientId)
                elif 18 <= clientAge <= 24:
                    reportLine[7] += 1
                    updateClientSets(7, clientSex, clientId)
                elif 25 <= clientAge <= 34:
                    reportLine[8] += 1
                    updateClientSets(8, clientSex, clientId)
                elif 35 <= clientAge <= 44:
                    reportLine[9] += 1
                    updateClientSets(9, clientSex, clientId)
                elif 45 <= clientAge <= 349:
                    reportLine[10] += 1
                    updateClientSets(10, clientSex, clientId)
                elif (clientSex == 1 and 50 <= clientAge <= 60) \
                        or (clientSex == 2 and 50 <= clientAge <= 55):
                    reportLine[11] += 1
                    updateClientSets(11, clientSex, clientId)
                else:
                    if begDate.year() < 2022:
                        if (clientSex == 1 and clientAge >= 61) or (clientSex == 2 and clientAge >= 56):
                            reportLine[12] += 1
                            updateClientSets(12, clientSex, clientId)
                    elif 2022 <= begDate.year() <= 2023:
                        if (clientSex == 1 and clientAge >= 62) or (clientSex == 2 and clientAge >= 57):
                            reportLine[12] += 1
                            updateClientSets(12, clientSex, clientId)
                    elif begDate.year() >= 2024:
                        if (clientSex == 1 and clientAge >= 63) or (clientSex == 2 and clientAge >= 58):
                            reportLine[12] += 1
                            updateClientSets(12, clientSex, clientId)

        self.writeRow(table, (1,2), 'B18', reportData, u'Зарегистрировано заболеваний хроническими вирусными гепатитами, всего (ед)')
        self.writeRow(table, (3,4), 'B18.0', reportData, u'в том числе:\nхронический вирусный гепатит В с дельта-агентом')
        self.writeRow(table, (5,6), 'B18.1', reportData, u'хронический вирусный гепатит В без дельта-агента')
        self.writeRow(table, (7,8), 'B18.2', reportData, u'хронический вирусный гепатит С')
        self.writeRow(table, (9,10), 'B18.8', reportData, u'хронический вирусный гепатит E')
        self.writeRow(table, (11,12), 'B18.9', reportData, u'хронический вирусный гепатит неуточненный')

        data = {
            '-': [
                [len(uniqueClients[0][i]) for i in range(13)],
                [len(uniqueClients[1][i]) for i in range(13)],
            ],
        }
        self.writeRow(table, (13,14), '-', data, u'из стр. 1 и 2: пациентов всего (чел)')

        data = {
            '-': [
                [len(severalDiseasesUniqueClients[0][i]) for i in range(13)],
                [len(severalDiseasesUniqueClients[1][i]) for i in range(13)],
            ],
        }
        self.writeRow(table, (15,16), '-', data, u'из них (из стр. 13 и 14): число пациентов с двумя и более заболеваниями')

        return doc


    def writeRow(self, table, rowNumbers, MKB, reportData, text):
        rowMale = table.addRow()
        rowFemale = table.addRow()
        table.mergeCells(rowMale, 0, 2, 1)
        table.mergeCells(rowMale, 3, 2, 1)

        rowNumberMale, rowNumberFemale = rowNumbers
        table.setText(rowMale, 0, text)
        table.setText(rowMale, 1, u'М')
        table.setText(rowFemale, 1, u'Ж')
        table.setText(rowMale, 2, str(rowNumberMale))
        table.setText(rowFemale, 2, str(rowNumberFemale))
        table.setText(rowMale, 3, MKB)

        reportLine = reportData.get(MKB, [[0]*13, [0]*13])
        for i in range(13):
            table.setText(rowMale, 4+i, str(reportLine[0][i]))
        for i in range(13):
            table.setText(rowFemale, 4+i, str(reportLine[1][i]))



class CStatReportF065_2000(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Форма 065 (2000)')


    def getSetupDialog(self, parent):
        dialog = CReport.getSetupDialog(self, parent)
        dialog.setWindowTitle(self.title())
        dialog.setOnlyPermanentAttachVisible(False)
        dialog.setOrgStructureVisible(True)
        dialog.adjustSize()
        return dialog


    def build(self, params):
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate.currentDate())
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportSubTitle)
        cursor.insertText(u'Заболеваемость хроническими вирусными гепатитами и диспансерное наблюдение')
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        cursor.insertText(u'(2000)')
        cursor.insertBlock()

        tableColumns = [
            ('', [u'Заболевания и пациенты', u'', u'', u'', u'1'], CReportBase.AlignLeft),
            ('', [u'№ строки', u'', u'', u'', u'2'], CReportBase.AlignLeft),
            ('', [u'Код по МКБ-10', u'', u'', u'', u'3'], CReportBase.AlignLeft),
            ('', [u'Зарегистрировано и взято под диспансерное наблюдение в отчетном году', u'Всего', u'', u'', u'4'], CReportBase.AlignRight),
            ('', [u'', u'из них (гр. 4):', u'состояло и взято под дисп. наблюдение', u'', u'5'], CReportBase.AlignRight),
            ('', [u'', u'', u'с впервые в жизни установленным диагнозом', u'', u'6'], CReportBase.AlignRight),
            ('', [u'', u'', u'переведено из других организаций', u'', u'7'], CReportBase.AlignRight),
            ('', [u'', u'', u'прибыло из других субъектов России', u'', u'8'], CReportBase.AlignRight),
            ('', [u'из заболеваний с впервые в жизни установлен-ным диагнозом (гр. 6)', u'взято под диспансерное наблюдение', u'', u'всего', u'9'], CReportBase.AlignRight),
            ('', [u'', u'', u'', u'детей в возрасте 0-17 лет', u'10'], CReportBase.AlignRight),
            ('', [u'Снято с диспансерного наблюдения в отчетном году', u'всего', u'', u'', u'11'], CReportBase.AlignRight),
            ('', [u'', u'из них:', u'детей в возрасте 0-17 лет', u'', u'12'], CReportBase.AlignRight),
            ('', [u'', u'', u'переведено в другие организации', u'', u'13'], CReportBase.AlignRight),
            ('', [u'', u'', u'выбыло в другие субъекты России', u'', u'14'], CReportBase.AlignRight),
            ('', [u'', u'', u'умерло', u'', u'15'], CReportBase.AlignRight),
            ('', [u'Состоит под диспансерным наблюдением на конец отчетного года', u'всего', u'', u'', u'16'], CReportBase.AlignRight),
            ('', [u'', u'детей в возрасте 0-17 лет', u'', u'', u'17'], CReportBase.AlignRight),
        ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 4, 1)
        table.mergeCells(0, 1, 4, 1)
        table.mergeCells(0, 2, 4, 1)
        table.mergeCells(0, 3, 1, 5)
        table.mergeCells(0, 8, 1, 2)
        table.mergeCells(0, 10, 1, 5)
        table.mergeCells(0, 15, 1, 2)

        table.mergeCells(1, 3, 3, 1)
        table.mergeCells(1, 4, 1, 4)
        table.mergeCells(1, 8, 2, 2)
        table.mergeCells(1, 10, 3, 1)
        table.mergeCells(1, 11, 1, 4)
        table.mergeCells(1, 15, 3, 1)
        table.mergeCells(1, 16, 3, 1)

        table.mergeCells(2, 4, 2, 1)
        table.mergeCells(2, 5, 2, 1)
        table.mergeCells(2, 6, 2, 1)
        table.mergeCells(2, 7, 2, 1)
        table.mergeCells(2, 11, 2, 1)
        table.mergeCells(2, 12, 2, 1)
        table.mergeCells(2, 13, 2, 1)
        table.mergeCells(2, 14, 2, 1)

        reportData = {}  # {MKB: reportLine}
        dispObvervedChilds = 0
        uniqueClients = [set() for i in range(14)]
        uniqueClientsObservedChilds = set()
        severalDiseasesUniqueClients = [set() for i in range(14)]
        severalDiseasesUniqueClientsObservedChilds = set()

        def updateClientSets(column, clientId):
            if clientId in uniqueClients[column]:
                severalDiseasesUniqueClients[column].add(clientId)
            uniqueClients[column].add(clientId)

        query = selectData(params)
        while query.next():
            record = query.record()
            diagnosisTypeCode = forceString(record.value('diagnosisTypeCode'))
            dispanserCode = forceString(record.value('dispanserCode'))
            diseaseCharacterCode = forceString(record.value('diseaseCharacterCode'))
            date = forceDate(record.value('endDate'))
            MKB = forceString(record.value('MKB'))
            clientAge = forceInt(record.value('clientAge'))
            clientId = forceInt(record.value('clientId'))

            if begDate <= date <= endDate and diagnosisTypeCode not in ('7', '8', '10', '11', '12'):
                reportLine = reportData.setdefault(MKB, [0]*14)
                reportLine[0] += 1
                updateClientSets(0, clientId)

                if dispanserCode in ('1', '2', '6'):
                    reportLine[1] += 1
                    updateClientSets(1, clientId)
                    if clientAge <= 17:
                        dispObvervedChilds += 1
                        if clientId in uniqueClientsObservedChilds:
                            severalDiseasesUniqueClientsObservedChilds.add(clientId)
                        uniqueClientsObservedChilds.add(clientId)

                if diseaseCharacterCode == '2':
                    reportLine[2] += 1
                    updateClientSets(2, clientId)
                    if dispanserCode in ('2', '6'):
                        reportLine[5] += 1
                        updateClientSets(5, clientId)
                        if clientAge <= 17:
                            reportLine[6] += 1
                            updateClientSets(6, clientId)

                if dispanserCode in ('3', '4', '6'):
                    reportLine[7] += 1
                    updateClientSets(7, clientId)
                    if clientAge <= 17:
                        reportLine[8] += 1
                        updateClientSets(8, clientId)

                if dispanserCode == '5':
                    reportLine[11] += 1
                    updateClientSets(11, clientId)

        for reportLine in reportData.itervalues():
            reportLine[12] = reportLine[1] - reportLine[7]
            reportLine[13] = dispObvervedChilds - reportLine[8]

        self.writeRow(table, reportData, 1, 'B18', u'Зарегистрировано заболеваний хроническими вирусными гепатитами, всего (ед)')
        self.writeRow(table, reportData, 2, 'B18.0', u'в том числе:\nхронический вирусный гепатит В с дельта-агентом')
        self.writeRow(table, reportData, 3, 'B18.1', u'хронический вирусный гепатит В без дельта-агента')
        self.writeRow(table, reportData, 4, 'B18.2', u'хронический вирусный гепатит С')
        self.writeRow(table, reportData, 5, 'B18.8', u'хронический вирусный гепатит Е')
        self.writeRow(table, reportData, 6, 'B18.9', u'хронический вирусный гепатит неуточненный')

        reportLine = [len(i) for i in uniqueClients]
        reportLine[12] = reportLine[1] - reportLine[7]
        reportLine[13] = len(uniqueClientsObservedChilds) - reportLine[8]
        row = table.addRow()
        table.setText(row, 0, u'из стр. 1:\nчисло пациентов всего (чел)')
        table.setText(row, 1, '7')
        table.setText(row, 2, '-')
        for col, value in enumerate(reportLine):
            table.setText(row, 3+col, str(value))

        reportLine = [len(i) for i in severalDiseasesUniqueClients]
        reportLine[12] = reportLine[1] - reportLine[7]
        reportLine[13] = len(severalDiseasesUniqueClientsObservedChilds) - reportLine[8]
        row = table.addRow()
        table.setText(row, 0, u'из них (из стр. 7):\nчисло пациентов с двумя и более заболеваниями')
        table.setText(row, 1, '8')
        table.setText(row, 2, '-')
        for col, value in enumerate(reportLine):
            table.setText(row, 3+col, str(value))

        return doc


    def writeRow(self, table, reportData, number, MKB, title):
        row = table.addRow()
        table.setText(row, 0, title)
        table.setText(row, 1, str(number))
        table.setText(row, 2, MKB)
        for col, value in enumerate(reportData.get(MKB, [0]*14)):
            table.setText(row, 3+col, str(value))
