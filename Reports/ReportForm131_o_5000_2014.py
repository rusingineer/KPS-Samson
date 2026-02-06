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

from library.Utils             import forceInt, forceRef, forceStringEx, trim
from Reports.Report            import CReport
from Reports.ReportBase        import CReportBase, createTable
from Reports.ReportSetupDialog import CReportSetupDialog
from Orgs.Utils                import getOrgStructurePersonIdList


def selectData(params, is5000=True):
    begDate = params.get('begDate', QDate())
    endDate = params.get('endDate', QDate())
    orgStructureId = params.get('orgStructureId', None)
    db = QtGui.qApp.db

    tableEvent = db.table('Event')
    tableMES = db.table('mes.MES')
    tableMESGroup = db.table('mes.mrbMESGroup')
    tableClient = db.table('Client')
    tableDiagnostic = db.table('Diagnostic')
    tableDiagnosis = db.table('Diagnosis')

    queryTable = tableEvent

    queryTable = queryTable.leftJoin(tableMES, tableMES['id'].eq(tableEvent['MES_id']))
    queryTable = queryTable.leftJoin(tableMESGroup, tableMESGroup['id'].eq(tableMES['group_id']))
    queryTable = queryTable.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
    queryTable = queryTable.leftJoin(tableDiagnostic, tableDiagnostic['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.leftJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))

    cond = [tableEvent['deleted'].eq(0),
            tableEvent['execDate'].ge(begDate),
            tableEvent['execDate'].lt(endDate.addDays(1)),
            tableMESGroup['code'].eq(u'ДиспанС'),
            ]
    if orgStructureId:
        cond.append(tableEvent['execPerson_id'].inlist(getOrgStructurePersonIdList(orgStructureId)))
    if is5000:
        diseasePhaseId_suspicion = forceRef(db.translate('rbDiseasePhases', 'code', '10', 'id'))
        if diseasePhaseId_suspicion:
            cond.append(db.joinOr([tableDiagnostic['phase_id'].ne(diseasePhaseId_suspicion), tableDiagnostic['phase_id'].isNull()]))
    else:
        diseasePhaseId_suspicion = forceInt(db.translate('rbDiseasePhases', 'code', '10', 'id'))
        cond.append(tableDiagnostic['phase_id'].eq(diseasePhaseId_suspicion))

    fields = [tableEvent['id'].alias('eventId'),
              'age(Client.`birthDate`, \'%s\') AS clientAge' % unicode(QDate(endDate.year(), 12, 31).toString('yyyy-MM-dd')),
              tableDiagnosis['MKB'].name(),
              tableClient['sex'].alias('clientSex'),
              tableClient['id'].alias('clientId')
              ]


    stmt = db.selectStmt(queryTable, fields, cond, tableEvent['id'].name())

#    print stmt

    return db.query(stmt)

class CReportForm131_o_5000_2014(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Сведения о выявленных заболеваниях (случаев)')

        rus = u'АВСКТЕНХРОМ'
        eng = u'ABCKTEHXPOM'
        self.r2e = {}
        for i in range(len(rus)):
            self.r2e[ rus[i] ] = eng[i]


    def getSetupDialog(self, parent):
        result = CReportSetupDialog(parent)
        result.setEventTypeVisible(False)
        result.setOnlyPermanentAttachVisible(False)
        result.setOrgStructureVisible(True)
        result.setTitle(self.title())
        return result


    def _getMkb2Rows(self, rows):
        result = {}

        from string import ascii_uppercase

        for row, values in rows.items():
            mkbValue = values[1]

            if not mkbValue:
                continue

            if '-' in mkbValue:
                bValue, eValue = mkbValue.split('-')
                bChar, eChar = bValue[0], eValue[0]
                bInt, eInt = int(bValue[1:3]), int(eValue[1:3])
                bI, eI = (bInt, eInt) if bChar == eChar else (bInt, 99)

                if self.r2e.has_key(bChar):
                    bChar = self.r2e[bChar]
                if self.r2e.has_key(eChar):
                    eChar = self.r2e[eChar]

                bCharIndex = ascii_uppercase.index(bChar)
                currentChar = bChar
                currentCharIndex = bCharIndex
                i = bI
                while i <= eI:
                    mkb = currentChar+str(i)
                    mkbNum = str(i) if len(str(i)) == 2 else '0'+str(i)
                    mkb = currentChar+mkbNum
                    rowList = result.setdefault(mkb, [])
                    rowList.append(row)
                    if i == eI:
                        if currentChar == eChar:
                            break
                        else:
                            currentCharIndex += 1
                            currentChar = ascii_uppercase[currentCharIndex]
                            i = 0
                            if currentChar == eChar:
                                eI = eInt
                    i += 1

            elif ',' in mkbValue:
                mkbValueList = mkbValue.split(',')
                for mkb in mkbValueList:
                    mkb = trim(mkb)
                    rowList = result.setdefault(mkb, [])
                    rowList.append(row)

            else:
                rowList = result.setdefault(mkbValue, [])
                rowList.append(row)

        result[u'I120.0'] = [32]

        return result

    def _getRowsDefaults(self):
        rows  = { 1: [u'Некоторые инфекционные и паразитарные болезни', u'А00-В99'],
                  2: [u'    в том числе:\n        туберкулез', u'А15-А19'],
                  3: [u'Новообразования', u'С00-D48'],
                  4: [u'    в том числе:\n        злокачественные новообразования', u'С00-D48'],
                  5: [u'            в том числе:\n                пищевода', u'C15'],
                  6: [u'                желудка', u'С16'],
                  7: [u'                ободочной кишки', u'C18'],
                  8: [u'                прямой кишки, ректосигмоидного соединения, заднего прохода (ануса) и анального канала', u'С19-С21'],
                  9: [u'                поджелудочной железы', u'С25'],
                 10: [u'                трахеи, бронхов и легкого', u'С33, С34'],
                 11: [u'                молочной железы', u'C50'],
                 12: [u'                шейки матки', u'C53'],
                 13: [u'                тела матки', u'C54'],
                 14: [u'                яичника', u'C56'],
                 15: [u'                предстательной железы', u'C61'],
                 16: [u'                почки (кроме почечной лоханки)', u'С64'],
                 17: [u'Болезни крови, кроветворных органов и отдельные нарушения, вовлекающие иммунный механизм', u'D50-D89'],
                 18: [u'    в том числе:\n        анемии', u'D50-D64'],
                 19: [u'Болезни эндокринной системы, расстройства питания и нарушения обмена веществ', u'Е00-Е89'],
                 20: [u'    в том числе:\n        сахарный диабет', u'Е10-Е14'],
                 21: [u'        ожирение', u'E66'],
                 22: [u'Болезни нервной системы', u'G00-G98'],
                 23: [u'    в том числе:\n        преходящие транзиторные церебральные ишемические приступы [атаки] и родственные синдромы', u'G45'],
                 24: [u'Болезни глаза и его придаточного аппарата', u'H00-H59'],
                 25: [u'    в том числе:\n        катаракта', u'H25, H26'],
                 26: [u'        глаукома', u'Н40'],
                 27: [u'        слепота и пониженное зрение', u'Н54'],
                 28: [u'Болезни системы кровообращения', u'I00-I99'],
                 29: [u'    в том числе:\n        болезни, характеризующиеся повышенным кровяным давлением', u'I10-I13'],
                 30: [u'        ишемическая болезнь сердца', u'I20-I25'],
                 31: [u'            в том числе:\n                стенокардия (грудная жаба)', u'I20'],
                 32: [u'                    в том числе:\n                        нестабильная стенокардия', u'I20.0'],
                 33: [u'                хроническая ишемическая болезнь сердца', u'I25'],
                 34: [u'        другие болезни сердца', u'I30-I52'],
                 35: [u'        цереброваскулярные болезни', u'I60-I69'],
                 36: [u'            в том числе:\n                закупорка и стеноз прецеребральных, церебральных артерий, не приводящие к инфаркту мозга ', u'I65, I66'],
                 37: [u'                другие цереброваскулярные болезни', u'I67'],
                 38: [u'Болезни органов дыхания', u'J00-J98'],
                 39: [u'    в том числе:\n        пневмония', u'J12-J18'],
                 40: [u'        бронхит хронический и неуточненный, эмфизема ', u'J40-J43'],
                 41: [u'        другая хроническая обструктивная легочная болезнь, бронхоэктатическая болезнь', u'J44-J47'],
                 42: [u'Болезни органов пищеварения', u'K00-K92'],
                 43: [u'    в том числе:\n        язва желудка, двенадцатиперстной кишки', u'K25, K26'],
                 44: [u'        гастрит и дуоденит', u'K29'],
                 45: [u'        неинфекционный энтерит и колит', u'K50-K52'],
                 46: [u'        другие болезни кишечника', u'К55-К63'],
                 47: [u'Болезни мочеполовой системы', u'N00-N99'],
                 48: [u'    в том числе:\n        болезни предстательной железы', u'N40-N42'],
                 49: [u'        доброкачественная дисплазия молочной железы', u'N60'],
                 50: [u'        воспалительные болезни женских тазовых органов', u'N70-N77'],
                 51: [u'Прочие заболевания', u''],
                 52: [u'Итого', u'']}

        mkb2Rows = self._getMkb2Rows(rows)

        for rowValueList in rows.values():
            for i in range(9):
                rowValueList.append(0)

        return rows, mkb2Rows

    def getReportData(self, query):
        reportData, mkb2Rows = self._getRowsDefaults()

        previous = None

        commonColumn = 8

        while query.next():

            record = query.record()

            eventId = forceRef(record.value('eventId'))
            clientAge = forceInt(record.value('clientAge'))
            clientSex = forceInt(record.value('clientSex'))
            mkb = forceStringEx(record.value('MKB'))
            clientId = forceRef(record.value('clientId'))

#            print clientId

            if clientId == 651960:
                pass

            if (eventId, mkb) == previous:
                continue

            previous = (eventId, mkb)

            rows = mkb2Rows.get(mkb[0:3], [51])

            if mkb == 'I20.0':
                rows.append(32)

            for row in rows:

                data = reportData.get(row, None)
                if data and clientSex:

                    column = 2 if clientSex == 1 else 5

                    if 18 <= clientAge <= 36:
                        data[column] += 1
                        data[commonColumn] += 1
                        reportData[52][column] += 1
                        reportData[52][commonColumn] += 1

                    elif 39 <= clientAge <= 60:
                        data[column+1] += 1
                        data[commonColumn+1] += 1
                        reportData[52][column+1] += 1
                        reportData[52][commonColumn+1] += 1

                    elif 60 < clientAge:
                        data[column+2] += 1
                        data[commonColumn+2] += 1
                        reportData[52][column+2] += 1
                        reportData[52][commonColumn+2] += 1

        return reportData


    def _selectData(self, params):
        return selectData(params, is5000=True)


    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        tableColumns = [
            ( '47%', [u'Заболевание/подозрение на заболевание', u''], CReportBase.AlignLeft),
            ( '3%',  [u'№', u''], CReportBase.AlignRight),
            ( '5%',  [u'Код по МКБ-10', u''], CReportBase.AlignRight),
            ( '5%',  [u'Мужчины', u'18 – 36 лет'], CReportBase.AlignRight),
            ( '5%',  [u'', u'39 – 60 лет'], CReportBase.AlignRight),
            ( '5%',  [u'', u'Старше 60 лет'], CReportBase.AlignRight),
            ( '5%',  [u'Женщины', u'18 – 36 лет'], CReportBase.AlignRight),
            ( '5%',  [u'', u'39 – 60 лет'], CReportBase.AlignRight),
            ( '5%',  [u'', u'Старше 60 лет'], CReportBase.AlignRight),
            ( '5%',  [u'Всего', u'18 – 36 лет'], CReportBase.AlignRight),
            ( '5%',  [u'', u'39 – 60 лет'], CReportBase.AlignRight),
            ( '5%',  [u'', u'Старше 60 лет'], CReportBase.AlignRight)
                      ]

        table = createTable(cursor, tableColumns)

        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 2, 1)
        table.mergeCells(0, 3, 1, 3)
        table.mergeCells(0, 6, 1, 3)
        table.mergeCells(0, 9, 1, 3)


        query = self._selectData(params)

        reportData = self.getReportData(query)

        reportDataKeyList = reportData.keys()
        reportDataKeyList.sort()
        for dataKey in reportDataKeyList:
            data = reportData[dataKey]

            i = table.addRow()
            table.setText(i, 0, data[0])
            table.setText(i, 1, dataKey)
            table.setText(i, 2, data[1])

            for idx, value in enumerate(data[2:]):
                table.setText(i, idx+3, value)

        return doc

class CReportForm131_o_6000_2014(CReportForm131_o_5000_2014):
    def __init__(self, parent):
        CReportForm131_o_5000_2014.__init__(self, parent)
        self.setTitle(u'Сведения о выявленных подозрениях на наличие заболеваний (случаев)')

    def _selectData(self, params):
        return selectData(params, is5000=False)

