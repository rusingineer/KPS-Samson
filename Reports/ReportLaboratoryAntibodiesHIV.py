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

from PyQt4              import QtGui
from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.ReportView import CPageFormat
from library.Utils      import forceInt, forceString
from copy               import deepcopy
from Reports.Utils      import dateRangeAsStr

from Reports.ReportHealthResortAnalysisUsePlacesRegions import CReportHealthResortSetupDialog


baseDict = {'ageFrom0To14':  {'pos': 0, 'neg': 0},
            'ageFrom15To17': {'pos': 0, 'neg': 0},
            'otherAge':      {'pos': 0, 'neg': 0}
           }


def selectData(params):
    russianCitizens = dict() # {socCode: baseDict}
    foreignCitizens = deepcopy(baseDict)

    db = QtGui.qApp.db
    tableEvent            = db.table('Event')
    tableAction           = db.table('Action')
    tableActionType       = db.table('ActionType')
    tableActionProperty   = db.table('ActionProperty')
    tablePropertyType     = db.table('ActionPropertyType')
    tablePropertyString   = db.table('ActionProperty_String')
    tableClient           = db.table('Client')
    tableClientSocStatus  = db.table('ClientSocStatus')
    tableRbSocStatusType  = db.table('rbSocStatusType')
    tableRbSocStatusClass = db.table('rbSocStatusClass')

    queryTable = tableEvent
    queryTable = queryTable.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
    queryTable = queryTable.innerJoin(tableActionType, tableAction['actionType_id'].eq(tableActionType['id']))
    queryTable = queryTable.innerJoin(tableActionProperty, tableActionProperty['action_id'].eq(tableAction['id']))
    queryTable = queryTable.innerJoin(tablePropertyType, tableActionProperty['type_id'].eq(tablePropertyType['id']))
    queryTable = queryTable.innerJoin(tablePropertyString, tableActionProperty['id'].eq(tablePropertyString['id']))
    queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
    queryTable = queryTable.innerJoin(tableClientSocStatus, tableClientSocStatus['client_id'].eq(tableClient['id']))
    queryTable = queryTable.innerJoin(tableRbSocStatusType, tableClientSocStatus['socStatusType_id'].eq(tableRbSocStatusType['id']))
    queryTable = queryTable.innerJoin(tableRbSocStatusClass, tableClientSocStatus['socStatusClass_id'].eq(tableRbSocStatusClass['id']))

    cond = [ tableAction['deleted'].eq(0),
             tableEvent['deleted'].eq(0),
             tableActionProperty['deleted'].eq(0),
             tableClientSocStatus['deleted'].eq(0),
             tableActionType['name'].eq(u'Исследование образцов крови в ИФА на СПИД'),
             tablePropertyType['name'].eq(u'Результат'),
             tableEvent['setDate'].ge(params['begDate']),
             tableEvent['setDate'].lt(params['endDate'].addDays(1))
           ]
    cols = [ tableRbSocStatusType['socCode'],
             tablePropertyString['value'],
             'age(Client.birthDate, Event.setDate) as `clientAge`',
             tableRbSocStatusClass['name'].alias('statusClassName'),
             tableRbSocStatusType['name'].alias('statusTypeName')
           ]

    stmt = db.selectStmt(queryTable, cols, cond)
    query = db.query(stmt)
    while query.next():
        record = query.record()
        socCode = forceInt(record.value('socCode'))
        clientAge = forceInt(record.value('clientAge'))
        isNegative = (forceString(record.value('value')).lower() == u'отрицательно')
        statusClassName = forceString(record.value('statusClassName'))
        statusTypeName = forceString(record.value('statusTypeName'))

        if statusClassName ==  u'Гражданство' and statusTypeName != u'Россия':
            data = foreignCitizens
        else:
            if not russianCitizens.has_key(socCode):
                russianCitizens[socCode] = deepcopy(baseDict)
            data = russianCitizens[socCode]

        if 0 <= clientAge <= 14:
            ageKey = 'ageFrom0To14'
        elif 15 <= clientAge <= 17:
            ageKey = 'ageFrom15To17'
        else:
            ageKey = 'otherAge'

        resultKey = 'neg' if isNegative else 'pos'
        data[ageKey][resultKey] += 1

    return russianCitizens, foreignCitizens



class CReportLaboratoryAntibodiesHIV(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Результаты исследования крови на антитела ВИЧ')

    def getSetupDialog(self, parent):
        result = CReportHealthResortSetupDialog(parent)
        result.setTitle(self.title())
        return result

    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.setBlockFormat(CReportBase.AlignCenter)

        cursor.insertText(u'Сведения о результатах исследования крови на антитела ВИЧ')
        cursor.insertBlock()
        alignRight, alignCenter, alignLeft = CReportBase.AlignRight, CReportBase.AlignCenter, CReportBase.AlignLeft

        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.setBlockFormat(alignLeft)
        cursor.insertBlock()
        cursor.insertText(dateRangeAsStr(u'За период', params['begDate'], params['endDate']))

        cols = [('40%', [u'Контингент обследованных', '', '1'], alignLeft),
                ('10%', [u'№ строки', '', '2'], alignLeft),
                ('10%', [u'Код контингентов обследованных', '', '3'], alignLeft),
                ('10%', [u'Всего обследовано', '', '4'], alignLeft),
                ('10%', [u'В том числе', u'Дети (0-14)', '5.1'], alignLeft),
                ('10%', ['', u'Подростки (15-17)', '5.2'], alignLeft),
                ('10%', [u'Выявлено положительных результатов у обследованных', u'В ИФА', '6'], alignLeft)
               ]
        table = createTable(cursor, cols)

        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 2, 1)
        table.mergeCells(0, 3, 2, 1)
        table.mergeCells(0, 4, 1, 2)

        russianCitizens, foreignCitizens = selectData(params)
        totalForAll = deepcopy(baseDict)
        indent = "    "  # 4 пробела для отступа


        # Сумма всех значений из словаря по выбранным ключам
        def sumResults(data, ageKeyList=['ageFrom0To14', 'ageFrom15To17', 'otherAge'], resultKeyList=['pos', 'neg']):
            total = 0
            for ageKey in ageKeyList:
                for resultKey in resultKeyList:
                    total += data[ageKey][resultKey]
            return total

        # Сложение двух словарей
        def sumDictValues(toDict, fromDict):
            for ageKey in ('ageFrom0To14', 'ageFrom15To17', 'otherAge'):
                for resultKey in ('pos', 'neg'):
                    toDict[ageKey][resultKey] += fromDict[ageKey][resultKey]


        # Группа "Граждане Российской Федерации, в том числе"
        row = table.addRow()
        table.setText(row, 0, u'Граждане Российской Федерации, в том числе:')
        table.setText(row, 1, str(row - 2), blockFormat=alignCenter)
        table.setText(row, 2, '100', blockFormat=alignCenter)
        russianCitizensRowIndex = row

        row = table.addRow()
        table.setText(row, 0, indent + u'Обследованные в плановом порядке:')
        table.setText(row, 1, str(row - 2), blockFormat=alignCenter)
        table.setText(row, 2, '119', blockFormat=alignCenter)

        # Группа "Обследованные в плановом порядке"
        groupTotal, groupRowIndex = deepcopy(baseDict), row
        for socCode, rowTitle in [ (108, indent * 2 + u'Доноры (крови, биологических жидкостей органов и тканей)'),
                                   (115, indent * 2 + u'Медицинский персонал, работающий с больными ВИЧ-инфекцией или инфицированным материалом'),
                                 ]:
            data = baseDict if not russianCitizens.has_key(socCode) else russianCitizens[socCode]
            row = table.addRow()
            table.setText(row, 0, rowTitle)
            table.setText(row, 1, str(row - 2), blockFormat=alignCenter)
            table.setText(row, 2, str(socCode), blockFormat=alignCenter)
            table.setText(row, 3, sumResults(data), blockFormat=alignRight)
            table.setText(row, 4, sumResults(data, ['ageFrom0To14']), blockFormat=alignRight)
            table.setText(row, 5, sumResults(data, ['ageFrom15To17']), blockFormat=alignRight)
            table.setText(row, 6, sumResults(data, resultKeyList=['pos']), blockFormat=alignRight)
            sumDictValues(groupTotal, data)

        table.setText(groupRowIndex, 3, sumResults(groupTotal), blockFormat=alignRight)
        table.setText(groupRowIndex, 4, sumResults(groupTotal, ['ageFrom0To14']), blockFormat=alignRight)
        table.setText(groupRowIndex, 5, sumResults(groupTotal, ['ageFrom15To17']), blockFormat=alignRight)
        table.setText(groupRowIndex, 6, sumResults(groupTotal, resultKeyList=['pos']), blockFormat=alignRight)
        ### ### ###

        sumDictValues(totalForAll, groupTotal)

        row = table.addRow()
        table.setText(row, 0, indent + u'Обследованные добровольно:')
        table.setText(row, 1, str(row - 2), blockFormat=alignCenter)
        table.setText(row, 2, '126', blockFormat=alignCenter)

        # Группа "Обследованные добровольно"
        groupTotal, groupRowIndex = deepcopy(baseDict), row
        for socCode, rowTitle in [ (102, indent * 2 + u'Больные наркоманией'),
                                   (103, indent * 2 + u'гомо-и бисексуалисты'),
                                   (104, indent * 2 + u'больные заболеваниями, передающимися половым путем'),
                                   (112, indent * 2 + u'лица, находящиеся в местах лишения свободы'),
                                   (113, indent * 2 + u'обследованные по клиническим показаниям'),
                                   (109, indent * 2 + u'беременные (доноры плацентарной и абортной крови)'),
                                   (118, indent * 2 + u'прочие'),
                                 ]:
            data = baseDict if not russianCitizens.has_key(socCode) else russianCitizens[socCode]
            row = table.addRow()
            table.setText(row, 0, rowTitle)
            table.setText(row, 1, str(row - 2), blockFormat=alignCenter)
            table.setText(row, 2, str(socCode), blockFormat=alignCenter)
            table.setText(row, 3, sumResults(data), blockFormat=alignRight)
            table.setText(row, 4, sumResults(data, ['ageFrom0To14']), blockFormat=alignRight)
            table.setText(row, 5, sumResults(data, ['ageFrom15To17']), blockFormat=alignRight)
            table.setText(row, 6, sumResults(data, resultKeyList=['pos']), blockFormat=alignRight)
            sumDictValues(groupTotal, data)

        table.setText(groupRowIndex, 3, sumResults(groupTotal), blockFormat=alignRight)
        table.setText(groupRowIndex, 4, sumResults(groupTotal, ['ageFrom0To14']), blockFormat=alignRight)
        table.setText(groupRowIndex, 5, sumResults(groupTotal, ['ageFrom15To17']), blockFormat=alignRight)
        table.setText(groupRowIndex, 6, sumResults(groupTotal, resultKeyList=['pos']), blockFormat=alignRight)
        ### ### ###

        sumDictValues(totalForAll, groupTotal)

        data = baseDict if not russianCitizens.has_key(120) else russianCitizens[120]
        row = table.addRow()
        table.setText(row, 0, indent + u'Обследованные при эпидемиологическом расследовании')
        table.setText(row, 1, str(row - 2), blockFormat=alignCenter)
        table.setText(row, 2, '120', blockFormat=alignCenter)
        table.setText(row, 3, sumResults(data), blockFormat=alignRight)
        table.setText(row, 4, sumResults(data, ['ageFrom0To14']), blockFormat=alignRight)
        table.setText(row, 5, sumResults(data, ['ageFrom15To17']), blockFormat=alignRight)
        table.setText(row, 6, sumResults(data, resultKeyList=['pos']), blockFormat=alignRight)
        sumDictValues(totalForAll, data)


        # Закрытие группы "Граждане Российской Федерации, в том числе"
        table.setText(russianCitizensRowIndex, 3, sumResults(totalForAll), blockFormat=alignRight)
        table.setText(russianCitizensRowIndex, 4, sumResults(totalForAll, ['ageFrom0To14']), blockFormat=alignRight)
        table.setText(russianCitizensRowIndex, 5, sumResults(totalForAll, ['ageFrom15To17']), blockFormat=alignRight)
        table.setText(russianCitizensRowIndex, 6, sumResults(totalForAll, resultKeyList=['pos']), blockFormat=alignRight)


        row = table.addRow()
        table.setText(row, 0, u'Иностранные граждане')
        table.setText(row, 1, str(row - 2), blockFormat=alignCenter)
        table.setText(row, 2, '200', blockFormat=alignCenter)
        table.setText(row, 3, sumResults(foreignCitizens), blockFormat=alignRight)
        table.setText(row, 4, sumResults(foreignCitizens, ['ageFrom0To14']), blockFormat=alignRight)
        table.setText(row, 5, sumResults(foreignCitizens, ['ageFrom15To17']), blockFormat=alignRight)
        table.setText(row, 6, sumResults(foreignCitizens, resultKeyList=['pos']), blockFormat=alignRight)
        sumDictValues(totalForAll, foreignCitizens)


        row = table.addRow()
        table.setText(row, 0, u'ИТОГО:')
        table.setText(row, 1, str(row - 2), blockFormat=alignCenter)
        # table.setText(row, 2, '')
        table.setText(row, 3, sumResults(totalForAll), blockFormat=alignRight)
        table.setText(row, 4, sumResults(totalForAll, ['ageFrom0To14']), blockFormat=alignRight)
        table.setText(row, 5, sumResults(totalForAll, ['ageFrom15To17']), blockFormat=alignRight)
        table.setText(row, 6, sumResults(totalForAll, resultKeyList=['pos']), blockFormat=alignRight)

        return doc
