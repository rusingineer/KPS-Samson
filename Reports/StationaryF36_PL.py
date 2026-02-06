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

from library.Utils             import forceInt, forceDate, forceString, forceBool, calcAgeInYears
from Reports.Report            import CReport
from Reports.ReportBase        import CReportBase, createTable
from Reports.ReportView        import CPageFormat

from Reports.StationaryF036_2300 import CStationaryF036_2300_SetupDialog


def mapClientsData(query):
    clientsData = {}
    while (query.next()):
        rec = query.record()
        clientId = forceInt(rec.value('clientId'))
        data = {}
        data['begDate'] = forceDate(rec.value('begDate'))
        data['endDate'] = forceDate(rec.value('endDate'))
        data['flatCode'] = forceString(rec.value('flatCode'))
        data['birthDate'] = forceDate(rec.value('birthDate'))
        data['MKB'] = forceString(rec.value('MKB'))
        data['propBegDate'] = forceDate(rec.value('propBegDate'))
        data['propEndDate'] = forceDate(rec.value('propEndDate'))
        data['isFirstInLife'] = forceBool(rec.value('isFirstInLife'))
        data['isFirstInCriminalCase'] = forceBool(rec.value('isFirstInCriminalCase'))
        data['isReceivedAfterAmb'] = forceBool(rec.value('isReceivedAfterAmb'))
        data['isCureTypeChanged'] = forceBool(rec.value('isCureTypeChanged'))
        data['isCureTypeChangedCriminalCase'] = forceBool(rec.value('isCureTypeChangedCriminalCase'))
        data['statType'] = forceString(rec.value('statType'))
        data['isMovingToAmb'] = forceBool(rec.value('isMovingToAmb'))
        data['is97Case'] = forceBool(rec.value('is97Case'))

        if not clientsData.has_key(clientId):
            clientsData[clientId] = []
        clientsData[clientId].append(data)

    return clientsData


def getActionPropertyValue(propTable, column, typeName, alias):
    return u'''(SELECT APTable.%s
    FROM %s APTable
        JOIN ActionProperty AP ON AP.id = APTable.id
        JOIN ActionPropertyType APT ON AP.type_id = APT.id
    WHERE AP.action_id = Action.id
        AND AP.deleted = 0
        AND APT.deleted = 0
        AND APT.name = '%s'
    ) AS `%s`''' % (column, propTable, typeName, alias)


def selectData(params):
    db = QtGui.qApp.db
    tableEvent = db.table('Event')
    tableAction = db.table('Action')
    tableAT = db.table('ActionType')
    tableClient = db.table('Client')
    tableDiagnostic = db.table('Diagnostic')
    tableDiagnosis = db.table('Diagnosis')

    begDate = params.get('begDate')
    endDate = params.get('endDate')

    queryTable = tableEvent
    queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
    queryTable = queryTable.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.innerJoin(tableAT, tableAction['actionType_id'].eq(tableAT['id']))
    queryTable = queryTable.innerJoin(tableDiagnostic, tableDiagnostic['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.innerJoin(tableDiagnosis, tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']))

    cols = [ tableClient['birthDate'],
             tableAT['flatCode'],
             tableAction['begDate'],
             tableAction['endDate'],
             tableDiagnosis['MKB'],
             tableClient['id'].alias('clientId'),

             getActionPropertyValue('ActionProperty_Date', 'value',
                u'Дата решения суда о применении принудительных мер медицинского характера', 'propBegDate'),

             getActionPropertyValue('ActionProperty_Date', 'value',
                u'Дата решения суда о прекращении принудительных мер медицинского характера', 'propEndDate'),

             getActionPropertyValue('ActionProperty_String', u"value = 'Да'",
                u'Поступает впервые в жизни', 'isFirstInLife'),

             getActionPropertyValue('ActionProperty_String', u"value = 'Да'",
                u'По данному уголовному делу впервые', 'isFirstInCriminalCase'),

             getActionPropertyValue('ActionProperty_String', u"value = 'Да'",
                u'Поступает после амбулаторного принудительного наблюдения и лечения', 'isReceivedAfterAmb'),

             getActionPropertyValue('ActionProperty_String', u"value = 'Да'",
                u'В связи с изменением вида принудительного лечения', 'isCureTypeChanged'),

             getActionPropertyValue('ActionProperty_String', u"value = 'Да'",
                u'В связи с изменением вида принудительного лечения по данному уголовному делу',
                'isCureTypeChangedCriminalCase'),

             getActionPropertyValue('ActionProperty_String', "value",
                u'Тип психиатрического стационара', 'statType'),

             getActionPropertyValue('ActionProperty_String', u"value = 'Да'",
                u'Перевод на амбулаторное принудительное наблюдение и лечение', 'isMovingToAmb'),

             getActionPropertyValue('ActionProperty_String', u"value = 'Да'", u'По ст.97', 'is97Case'),
           ]

    cond = [ tableEvent['deleted'].eq(0),
             tableAction['deleted'].eq(0),
             tableAT['deleted'].eq(0),
             tableClient['deleted'].eq(0),
             tableDiagnosis['deleted'].eq(0),
             tableDiagnostic['deleted'].eq(0),
             tableAT['flatCode'].inlist(['leaved', 'received', 'moving']),
           ]
    if begDate:
        cond.append(tableAction['begDate'].ge(begDate))
    if endDate:
        cond.append(tableAction['begDate'].lt(endDate.addDays(1)))

    stmt = db.selectDistinctStmt(queryTable, cols, cond)
    query = db.query(stmt)
    return mapClientsData(query)



class CStationaryF36_PL(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Состав больных, находящихся на принудительном лечении (ПЛ) в психиатрических стационарах (2200)')
        self.orientation = CPageFormat.Landscape


    def getSetupDialog(self, parent):
        result = CStationaryF036_2300_SetupDialog(parent)
        result.setWindowTitle(self.title())
        return result


    def getRowData(self, rowMKBFilter, extraCond=None):
        received = 0
        receivedAgeBefore17 = 0
        receivedFirstInCriminalCase = 0
        receivedFirstInLife = 0
        receivedBecauseStatTypeChanged = 0
        receivedAfterAmb = 0
        leaved = 0
        bedDays = 0
        leavedBecauseStatTypeChanged = 0
        leavedByMovingToAmb = 0
        inStat = 0
        inStatAgeBefore17 = 0

        begDate = self.params.get('begDate')
        endDate = self.params.get('endDate')

        clientsData = self.clientsData
        if extraCond:
            # clientsData = {k:v for (k,v) in clientsData.items() if extraCond(v)}
            clientsDataExtra = {}
            for k,v in clientsData.items():
                if extraCond(v):
                    clientsDataExtra[k] = v
            clientsData = clientsDataExtra

        for (clientId, dataList) in clientsData.items():
            dataList = filter(lambda i: rowMKBFilter(i['MKB']), dataList)
            for data in dataList:
                maxBegDate = max((data['begDate'], data['propBegDate']))
                minEndDate = min((data['endDate'], data['propEndDate']))
                clientAge = calcAgeInYears(data['birthDate'], maxBegDate)

                if data['flatCode'] == 'received':
                    if not (data['propBegDate'].isValid() and maxBegDate >= begDate and maxBegDate <= endDate):
                        continue
                    received += 1
                    inStat += 1
                    if clientAge <= 17:
                        receivedAgeBefore17 += 1
                        inStatAgeBefore17 += 1
                    if data['isFirstInLife']:
                        receivedFirstInLife += 1
                    if data['isFirstInCriminalCase']:
                        receivedFirstInCriminalCase += 1
                    if data['isCureTypeChangedCriminalCase']:
                        receivedBecauseStatTypeChanged += 1
                    if data['isReceivedAfterAmb']:
                        receivedAfterAmb += 1

                elif data['flatCode'] == 'leaved':
                    if not data['propEndDate']:
                        bedDays += data['endDate'].toJulianDay() - maxBegDate.toJulianDay()
                    else:
                        leaved += 1
                        inStat -= 1
                        if clientAge <= 17:
                            inStatAgeBefore17 -= 1
                        if data['isCureTypeChanged']:
                            leavedBecauseStatTypeChanged += 1
                        if data['isMovingToAmb']:
                            leavedByMovingToAmb += 1
                        bedDays += minEndDate.toJulianDay() - maxBegDate.toJulianDay()

        return [received, receivedAgeBefore17, receivedFirstInCriminalCase, receivedFirstInLife,
                receivedBecauseStatTypeChanged, receivedAfterAmb, leaved, bedDays,
                leavedBecauseStatTypeChanged, leavedByMovingToAmb, inStat, inStatAgeBefore17,
               ]


    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        tableColumns = [
            ('10%',[u'Наименование болезней', '',], CReportBase.AlignLeft),
            ('10%',[u'Код по МКБ-10', ''], CReportBase.AlignLeft),
            ('6%', [u'№ строки', ''], CReportBase.AlignCenter),
            ('6%', [u'Поступило больных в отчетном периоде на ПЛ', u'всего'], CReportBase.AlignRight),
            ('6%', ['', u'из них детей до 17 лет включительно'], CReportBase.AlignRight),
            ('6%', ['', u'впервые в жизни в ПБ (из гр.4)'], CReportBase.AlignRight),
            ('6%', ['', u'впервые по данному УД'], CReportBase.AlignRight),
            ('6%', ['', u'в связи с изменением вида ПЛ по данному УД'], CReportBase.AlignRight),
            ('6%', ['', u'из них после АПНЛ'], CReportBase.AlignRight),
            ('6%', [u'Выбыло больных', ''], CReportBase.AlignRight),
            ('6%', [u'Ими проведено койко-дней в данном стационаре', ''], CReportBase.AlignRight),
            ('8%', [u'Из числа выбывших (гр.10) выбыло', u'в связи с изменением вида ПЛ'], CReportBase.AlignRight),
            ('6%', ['', u'в том числе переводом на АПНЛ'], CReportBase.AlignRight),
            ('6%', [u'Состоит на конец периода', u'Всего'], CReportBase.AlignRight),
            ('6%', ['', u'из них детей до 17 лет включительно'], CReportBase.AlignRight),
        ]

        table = createTable(cursor, tableColumns)
        row = table.addRow()
        for i in xrange(len(tableColumns)):
            table.setText(row, i, str(i+1), blockFormat=CReportBase.AlignCenter)

        table.mergeCells(0,0, 2,1)
        table.mergeCells(0,1, 2,1)
        table.mergeCells(0,2, 2,1)
        table.mergeCells(0,3, 1,6)
        table.mergeCells(0,9, 2,1)
        table.mergeCells(0,10, 2,1)
        table.mergeCells(0,11, 1,2)
        table.mergeCells(0,13, 1,2)

        self.clientsData = selectData(params)
        self.params = params

        def insertRowTitle(row, rowName, rowMKB):
            table.setText(row, 0, rowName)
            table.setText(row, 1, rowMKB)
            table.setText(row, 2, row-2)

        def insertRowData(row, rowMKBFilter, extraCond=None):
            for (i,data) in enumerate(self.getRowData(rowMKBFilter, extraCond)):
                table.setText(row, 3+i, data)

        row = table.addRow()
        insertRowTitle(row, u'Психозы и (или) состояния слабоумия', u'F00-F05, F06 (часть), F09, F20-F25, F28, F29, F84.0-4, F30-F39 (часть)')
        insertRowData(row, lambda d: ('F00'<=d<='F05') or ('F20'<=d<='F25') or ('F06.0'<=d<='F06.2') or ('F84.0'<=d<='F84.4') \
            or d in ('F06','F06.81','F06.91','F09','F28','F29','F30','F31','F32','F33','F39','F80','F81.31','F99.1'))

        row = table.addRow()
        insertRowTitle(row, u'из них: шизофрения, шизоаффективные психозы, шизотипическое расстройство, аффективные психозы с неконгруентным аффекту бредом', 'F20, F21, F25, F3x..x4')
        insertRowData(row, lambda d: d in ('F20','F21','F25','F30.24','F31.24','F31.54','F32.34','F33.34'))

        row = table.addRow()
        insertRowTitle(row, u'Психические расстройства непсихотического характера', u'F06 (часть), F07, F30-F39 (часть), F40-F69, F80-F83, F84.5, F90-F98')
        insertRowData(row, lambda d: ('F33.4'<=d<='F38.8') or ('F40'<=d<='F69') or ('F80'<=d<='F83') or ('F90'<=d<='F98') \
            or d in ('F06','F06.4','F06.5','F06.6','F06.7','F06.82','F06.92','F7','F30','F31','F32','F33','F07','F84.5'))

        row = table.addRow()
        insertRowTitle(row, u'Умственная отсталость', 'F70-F79')
        insertRowData(row, lambda d: 'F70' <= d <= 'F79')

        row = table.addRow()
        insertRowTitle(row, u'Психические расстройства - всего', 'F00-F09, F20-F99')
        insertRowData(row, lambda d: ('F00' <= d <= 'F09') or ('F20' <= d <= 'F99'))

        row = table.addRow()
        insertRowTitle(row, u'Кроме того: больные с заболеваниями, связанными с употреблением психоактивных веществ', 'F10-F19')
        insertRowData(row, lambda d: 'F10' <= d <= 'F19')

        row = table.addRow()
        insertRowTitle(row, u'из них: больные алкогольными психозами и слабоумием', 'F10.4-F10.7')
        insertRowData(row, lambda d: 'F10.4' <= d <= 'F10.7')

        row = table.addRow()
        insertRowTitle(row, u'Из строк 5 и 6: число больных, заболевших психическими расстройствами после совершения преступления (пункт «б» части 1 статьи 97 УК РФ)', 'F00-F99')
        insertRowData(row, lambda d: 'F00' <= d <= 'F99')

        def hasPropCase97(dataList):
            for i in dataList:
                if i['flatCode'] == 'received' and i['is97Case']:
                    return True
            return False

        def hasPropStatType(dataList, statType):
            for i in dataList:
                if i['flatCode'] == 'moving' and i['statType'].lower() == statType:
                    return True
            return False

        row = table.addRow()
        insertRowTitle(row, u'Больные (из стр.5 и 6), находящиеся на ПЛ в течение отчетного года в психиатрическом стационаре общего типа', '')
        insertRowData(row, lambda d: 'F00' <= d <= 'F99', lambda dataList: hasPropStatType(dataList, u'общий'))

        row = table.addRow()
        insertRowTitle(row, u'из них число больных, заболевших психическими расстройствами после совершения преступления (пункт «б» части 1 статьи 97 УК РФ)', '')
        insertRowData(row, lambda d: 'F00' <= d <= 'F99', lambda dataList: hasPropStatType(dataList, u'общий') and hasPropCase97(dataList))

        row = table.addRow()
        insertRowTitle(row, u'Больные (из строк 5 и 6), находящиеся на ПЛ в течение отчетного года в психиатрическом стационаре специализированного типа', '')
        insertRowData(row, lambda d: 'F00' <= d <= 'F99', lambda dataList: hasPropStatType(dataList, u'специализированный'))

        row = table.addRow()
        insertRowTitle(row, u'из них число больных, заболевших психическими расстройствами после совершения преступления (пункт «б» части 1 статьи 97 УК РФ)', '')
        insertRowData(row, lambda d: 'F00' <= d <= 'F99', lambda dataList: hasPropStatType(dataList, u'специализированный') and hasPropCase97(dataList))

        return doc
