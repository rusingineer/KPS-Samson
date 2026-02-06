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

from PyQt4        import QtGui
from PyQt4.QtCore import QDate


from Reports.Report      import CReport
from Reports.ReportBase  import CReportBase, createTable
from Reports.ReportView  import CPageFormat
from Reports.Utils       import dateRangeAsStr
from library.Utils       import forceString, forceInt

from Reports.Ui_ReportLaboratoryActionsByMedicalTypeSetupDialog import Ui_ReportLaboratoryActionsByMedicalTypeSetupDialog
from library.DialogBase import CDialogBase


actionsGroups = { u'clinical':    u'Клиника',
                  u'bioch':       u'Биохимия',
                  u'hormon':      u'Гормоны',
                  u'marker':      u'Маркеры',
                  u'immunology':  u'Иммунология',
                  u'coagulology': u'Коагулология',
                  u'cytology':    u'Цитология ',
                  u'bacteriology':u'Бактериология ',
                  u'PCR':         u'ПЦР ',
                  u'allergology': u'Аллергология '
                }


AID_TYPE_NOT_SET = 0
AID_TYPE_STATIONARY = 1
AID_TYPE_AMBULATORY = 2
AID_TYPE_DAILY_STAT = 3


def getAidTypeName(aidType):
    return {
        'stat': u'Стационарная помощь',
        'amb': u'Амбулаторная помощь',
        'dailyStat': u'Дневной стационар',
    }[aidType]


def getMonthName(month):
    return [
        u'Январь', u'Февраль', u'Март',
        u'Апрель', u'Май', u'Июнь',
        u'Июль', u'Август', u'Сентябрь',
        u'Октябрь', u'Ноябрь', u'Декабрь',
    ][month-1]


def getQuarterMonths(quarter):
    return {
        1: [1,2,3],
        2: [4,5,6],
        3: [7,8,9],
        4: [10,11,12],
    }[quarter]



def selectData(params):
    begDate = params.get('begDate', QDate())
    endDate = params.get('endDate', QDate())
    db = QtGui.qApp.db
    tableAction        = db.table('Action')
    tableActionType    = db.table('ActionType')
    tableEvent         = db.table('Event')
    tableEventType     = db.table('EventType')
    tableClient        = db.table('Client')
    tableClientWork    = db.table('ClientWork')
    tablePerson        = db.table('Person')
    tableOrgStructure  = db.table('OrgStructure')
    tableRbTissueType  = db.table('rbTissueType')
    tableActionTypeTissueType = db.table('ActionType_TissueType')

    cond = [ tableAction['deleted'].eq(0),
             tableActionType['deleted'].eq(0),
             tableEvent['deleted'].eq(0),
             tableEventType['deleted'].eq(0),
             tableClient['deleted'].eq(0),
             tablePerson['deleted'].eq(0),
             tableClientWork['deleted'].eq(0),
             tableOrgStructure['deleted'].eq(0),
             tableActionType['flatCode'].inlist(actionsGroups.keys()),
             tableAction['finance_id'].inlist([1, 2, 4]),
             tableAction['endDate'].ge(begDate),
             tableAction['endDate'].lt(endDate.addDays(1)),
           ]

    cols = [ tableAction['finance_id'].alias('financeId'),
             'COUNT(DISTINCT Action.id) AS `amount`',
             tableActionType['name'].alias('actionTypeName'),
             tableActionType['flatCode'],
             tableRbTissueType['name'].alias('tissueTypeName'),
             tableEventType['medicalAidType_id'].alias('medicalAidTypeId'),
             tableClientWork['org_id'].alias('orgId'),
             'GROUP_CONCAT(DISTINCT Client.id) as `clientsIdList`',
             'MONTH(Action.endDate) AS `month`',
             'QUARTER(Action.endDate) AS `quarter`',
             tableOrgStructure['name'].alias('orgStructureName'),
           ]

    groupBy = [ tableAction['finance_id'].name(),
                tableClientWork['org_id'].name(),
                'QUARTER(Action.endDate)',
                'MONTH(Action.endDate)',
                tableOrgStructure['id'].name(),
                tableActionType['flatCode'].name(),
                tableActionType['id'].name(),
                tableRbTissueType['id'].name(),
              ]

    if params['medicalAidType'] == AID_TYPE_STATIONARY:
        cond.append(tableEventType['medicalAidType_id'].inlist([1, 2, 3]))

    elif params['medicalAidType'] == AID_TYPE_AMBULATORY:
        cond.append(tableEventType['medicalAidType_id'].eq(6))

    elif params['medicalAidType'] == AID_TYPE_DAILY_STAT:
        cond.append(tableEventType['medicalAidType_id'].eq(7))

    elif params['medicalAidType'] == AID_TYPE_NOT_SET:
        cond.append(tableEventType['medicalAidType_id'].inlist([1, 2, 3, 6, 7]))
        groupBy.append(tableEventType['medicalAidType_id'].name())

    queryTable = tableAction
    queryTable = queryTable.leftJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
    queryTable = queryTable.leftJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
    queryTable = queryTable.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
    queryTable = queryTable.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
    queryTable = queryTable.leftJoin(tableClientWork, tableClientWork['client_id'].eq(tableClient['id']))
    queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(tableAction['setPerson_id']))
    queryTable = queryTable.leftJoin(tableOrgStructure, tableOrgStructure['id'].eq(tablePerson['orgStructure_id']))
    queryTable = queryTable.leftJoin(tableActionTypeTissueType, tableActionTypeTissueType['master_id'].eq(tableActionType['id']))
    queryTable = queryTable.leftJoin(tableRbTissueType, tableRbTissueType['id'].eq(tableActionTypeTissueType['tissueType_id']))

    stmt = db.selectStmtGroupBy(queryTable, cols, cond, groupBy)
    query = db.query(stmt)
    while query.next():
        record = query.record()
        reportData = {}
        reportData['financeId'] = forceInt(record.value('financeId'))
        reportData['amount'] = forceInt(record.value('amount'))
        reportData['actionTypeName'] = forceString(record.value('actionTypeName'))
        reportData['flatCode'] = forceString(record.value('flatCode'))
        reportData['tissueTypeName'] = forceString(record.value('tissueTypeName'))
        reportData['orgId'] = forceInt(record.value('orgId'))
        reportData['clientsIdList'] = forceString(record.value('clientsIdList')).split(',')
        reportData['medicalAidTypeId'] = forceInt(record.value('medicalAidTypeId'))

        if params['detailByMonths']:
            reportData['month'] = forceInt(record.value('month'))

        if params['detailByQuarters']:
            reportData['quarter'] = forceInt(record.value('quarter'))

        if params['detailByOrgStructures']:
            reportData['orgStructureName'] = forceString(record.value('orgStructureName'))

        yield reportData


class CReportLaboratoryActionsByMedicalType(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Проведенные исследования в разрезе методик и типов медицинской помощи')
        self.orientation = CPageFormat.Landscape


    def getSetupDialog(self, parent):
        result = CReportLaboratoryActionsByMedicalTypeSetupDialog(parent)
        result.setTitle(self.title())
        return result


    def constructData(self, params):
        tableData = {}
        availableAidTypes = set()
        availableOrgStructures = set()
        availableMonths = set()
        availableQuarters = set()

        for row in selectData(params):
            if row['medicalAidTypeId'] in (1,2,3): row['medicalAidTypeId'] = 'stat'
            elif row['medicalAidTypeId'] == 6: row['medicalAidTypeId'] = 'amb'
            elif row['medicalAidTypeId'] == 7: row['medicalAidTypeId'] = 'dailyStat'
            availableAidTypes.add(row['medicalAidTypeId'])

            if params['detailByQuarters']:
                availableQuarters.add(row['quarter'])
            else:
                row['quarter'] = None

            if params['detailByMonths']:
                availableMonths.add(row['month'])
            else:
                row['month'] = None

            if params['detailByOrgStructures']:
                availableOrgStructures.add(row['orgStructureName'])
            else:
                row['orgStructureName'] = None

            data = tableData
            if not data.has_key(row['flatCode']):
                data[row['flatCode']] = {}
            data = data[row['flatCode']]

            if not data.has_key(row['tissueTypeName']):
                data[row['tissueTypeName']] = {}
            data = data[row['tissueTypeName']]

            if not data.has_key(row['actionTypeName']):
                data[row['actionTypeName']] = {}
            data = data[row['actionTypeName']]

            if not data.has_key(row['medicalAidTypeId']):
                data[row['medicalAidTypeId']] = {}
            data = data[row['medicalAidTypeId']]

            if not data.has_key(row['quarter']):
                data[row['quarter']] = {}
            data = data[row['quarter']]

            if not data.has_key(row['month']):
                data[row['month']] = {}
            data = data[row['month']]

            if not data.has_key(row['orgStructureName']):
                data[row['orgStructureName']] = {'pays': 0, 'free': 0, 'clientPays': set(), 'clientFree': set()}
            data = data[row['orgStructureName']]

            if row['financeId'] == 4:
                data['pays'] += row['amount']
                data['clientPays'].update(row['clientsIdList'])
            else:
                data['free'] += row['amount']
                data['clientFree'].update(row['clientsIdList'])

        return (tableData, sorted(availableAidTypes), sorted(availableQuarters),
                sorted(availableMonths), sorted(availableOrgStructures))


    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertBlock(CReportBase.AlignCenter)
        cursor.insertText(self.title())
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock(CReportBase.AlignLeft)

        description = [dateRangeAsStr(u'За период', params['begDate'], params['endDate'])]
        if params['detailByQuarters']:
            description.append(u'Детализировать по кварталам')
        if params['detailByMonths']:
            description.append(u'Детализировать по месяцам')
        if params['detailByOrgStructures']:
            description.append(u'Детализировать по подразделениям')
        for line in description:
            cursor.insertText(line)
            cursor.insertBlock()

        tableData, availableAidTypes, availableQuarters, availableMonths, availableOrgStructures = self.constructData(params)

        if len(availableQuarters) == 0:
            availableQuarters.insert(0, None)
        if len(availableMonths) == 0:
            availableMonths.insert(0, None)
        if len(availableOrgStructures) == 0:
            availableOrgStructures.insert(0, None)

        monthsCount = len(availableMonths)
        quartersCount = len(availableQuarters)
        orgStructsCount = len(availableOrgStructures)
        aidTypes = max(1, len(availableAidTypes))

        columnsCountForAidType = max(monthsCount, quartersCount) * orgStructsCount
        columnsCountTotal = columnsCountForAidType * aidTypes
        columnWidth = int(round(55.0 / columnsCountTotal))  # 55%

        cols = [ ('15%', [u'Методика'], CReportBase.AlignLeft),
                 ('15%', [u'Оплата'], CReportBase.AlignLeft),
               ]
        for i in xrange(columnsCountTotal):
            cols.append(('%d%%' % columnWidth, [''], CReportBase.AlignLeft))
        cols.append(('15%', [u'ИТОГО'], CReportBase.AlignLeft))
        finalColumnIndex = 2 + (orgStructsCount * monthsCount)  # Столбец "ИТОГО"

        table = createTable(cursor, cols)
        table.mergeCells(0,2+columnsCountTotal, 2,1)

        bold = CReportBase.ReportBody
        bold.setFontWeight(QtGui.QFont.Bold)
        center = CReportBase.AlignCenter
        right = CReportBase.AlignRight

        if params['detailByQuarters']:
            quarterRow = table.addRow()
        if params['detailByMonths']:
            monthRow = table.addRow()
        if params['detailByOrgStructures']:
            orgStructRow = table.addRow()

        for n,aidType in enumerate(availableAidTypes):
            baseIndex = 2 + n * columnsCountForAidType
            table.setText(0, baseIndex, getAidTypeName(aidType), blockFormat=center, charFormat=bold)
            table.mergeCells(0,baseIndex, 1,columnsCountForAidType)

            if params['detailByQuarters'] and bool(availableQuarters):
                if params['detailByMonths'] and bool(availableMonths):
                    for quarter in availableQuarters:
                        columnsToMerge = 0
                        month = getQuarterMonths(quarter)
                        if month[0] in availableMonths:
                            col = baseIndex + availableMonths.index(month[0]) * orgStructsCount
                            table.setText(quarterRow, col, u'%d-й квартал' % quarter, charFormat=bold, blockFormat=center)
                            columnsToMerge += 1
                        if month[1] in availableMonths:
                            if columnsToMerge <= 0:  # Если № квартала еще не написан
                                col = baseIndex + availableMonths.index(month[1]) * orgStructsCount
                                table.setText(quarterRow, col, u'%d-й квартал' % quarter, charFormat=bold, blockFormat=center)
                            columnsToMerge += 1
                        if month[2] in availableMonths:
                            if columnsToMerge <= 0:  # Если № квартала еще не написан
                                col = baseIndex + availableMonths.index(month[2]) * orgStructsCount
                                table.setText(quarterRow, col, u'%d-й квартал' % quarter, charFormat=bold, blockFormat=center)
                            columnsToMerge += 1

                        table.mergeCells(quarterRow, col, 1,columnsToMerge*orgStructsCount)
                else:
                    for i,quarter in enumerate(availableQuarters):
                        table.setText(quarterRow, baseIndex+i*orgStructsCount, u'%d-й квартал' % quarter, charFormat=bold, blockFormat=center)
                        table.mergeCells(quarterRow, baseIndex+i*orgStructsCount, 1,orgStructsCount)


            if params['detailByMonths'] and bool(availableMonths):
                for i, month in enumerate(availableMonths):
                    table.setText(monthRow, baseIndex+i*orgStructsCount, getMonthName(month), blockFormat=center, charFormat=bold)
                    table.mergeCells(monthRow, baseIndex+i*orgStructsCount, 1,orgStructsCount)
                table.mergeCells(monthRow,baseIndex, 1,orgStructsCount)
                table.mergeCells(monthRow,0, 1,2)


            if params['detailByOrgStructures'] and bool(availableOrgStructures):
                for i in xrange(columnsCountForAidType):
                    table.setText(orgStructRow, baseIndex+i, availableOrgStructures[i % orgStructsCount], blockFormat=center, charFormat=bold)
                table.mergeCells(orgStructRow,0, 1,2)


        def getRowData(data, valueKey, forClients=False):
            if forClients == False:
                row = [0] * (columnsCountTotal + 1)
            else:
                row = [set() for _ in xrange(columnsCountTotal + 1)]

            for aidType in sorted(data.keys()):
                for quarter in sorted(data[aidType].keys()):
                    for month in sorted(data[aidType][quarter].keys()):
                        for orgName in sorted(data[aidType][quarter][month].keys()):
                            index = availableAidTypes.index(aidType) * columnsCountForAidType + \
                                max(availableQuarters.index(quarter), availableMonths.index(month)) * orgStructsCount + \
                                availableOrgStructures.index(orgName)
                            row[index] = data[aidType][quarter][month][orgName][valueKey]

            if forClients == False:
                row[-1] = sum(row[:-1])
            else:
                row[-1] = set.union(*row[:-1])
            return row


        analysisTotal = [{'pays':0, 'free':0} for _ in xrange(columnsCountTotal+1)]
        clientsTotal = [{'pays':set(), 'free':set()} for _ in xrange(columnsCountTotal+1)]
        for flatCode in sorted(tableData.keys()):
            flatCodeTotal = [{'pays':0, 'free':0} for _ in xrange(columnsCountTotal+1)]
            row = table.addRow()
            table.mergeCells(row,0, 1,2)
            table.setText(row, 0, actionsGroups[flatCode], charFormat=bold, blockFormat=center)

            for tissueTypeName in sorted(tableData[flatCode].keys()):
                tissueTypeTotal = [{'pays':0, 'free':0} for i in xrange(columnsCountTotal+1)]
                row = table.addRow()
                table.setText(row, 0, tissueTypeName, charFormat=bold)
                table.mergeCells(row,0, 1,2)

                for actionTypeName, data in sorted(tableData[flatCode][tissueTypeName].items()):
                    freeRowIndex = table.addRow()
                    freeRowData = getRowData(data, 'free')
                    freeClientData = getRowData(data, 'clientFree', forClients=True)
                    table.setText(freeRowIndex, 0, actionTypeName)
                    table.setText(freeRowIndex, 1, u'бесп.')

                    paysRowIndex = table.addRow()
                    paysRowData = getRowData(data, 'pays')
                    paysClientData = getRowData(data, 'clientPays', forClients=True)
                    table.setText(paysRowIndex, 1, u'хозрасч.')

                    totalRowIndex = table.addRow()
                    table.setText(totalRowIndex, 1, u'всего')

                    for i in xrange(columnsCountTotal + 1):
                        total = freeRowData[i] + paysRowData[i]
                        table.setText(freeRowIndex, 2+i, freeRowData[i] if freeRowData[i] else '', blockFormat=right)
                        table.setText(paysRowIndex, 2+i, paysRowData[i] if paysRowData[i] else '', blockFormat=right)
                        table.setText(totalRowIndex, 2+i, total if total else '', blockFormat=right)
                        tissueTypeTotal[i]['free'] += freeRowData[i]
                        tissueTypeTotal[i]['pays'] += paysRowData[i]
                        clientsTotal[i]['free'].update(freeClientData[i])
                        clientsTotal[i]['pays'].update(paysClientData[i])

                    table.mergeCells(freeRowIndex,0, 3,1)
                ### end for actionTypeName


                freeRowIndex = table.addRow()
                table.setText(freeRowIndex, 0, tissueTypeName + u' - итого', charFormat=bold)
                table.setText(freeRowIndex, 1, u'бесп.')

                paysRowIndex = table.addRow()
                table.setText(paysRowIndex, 1, u'хозрасч.')

                totalRowIndex = table.addRow()
                table.setText(totalRowIndex, 1, u'всего')

                for i,data in enumerate(tissueTypeTotal):
                    total = data['free'] + data['pays']
                    table.setText(freeRowIndex, 2+i, data['free'] if data['free'] else '', blockFormat=right)
                    table.setText(paysRowIndex, 2+i, data['pays'] if data['pays'] else '', blockFormat=right)
                    table.setText(totalRowIndex, 2+i, total if total else '', blockFormat=right)
                    flatCodeTotal[i]['free'] += data['free']
                    flatCodeTotal[i]['pays'] += data['pays']

                table.mergeCells(freeRowIndex,0, 3,1)
            ### end for tissueTypeName

            freeRowIndex = table.addRow()
            table.setText(freeRowIndex, 0, actionsGroups[flatCode] + u' - итого', charFormat=bold, blockFormat=center)
            table.setText(freeRowIndex, 1, u'бесп.', charFormat=bold)

            paysRowIndex = table.addRow()
            table.setText(paysRowIndex, 1, u'хозрасч.', charFormat=bold)

            totalRowIndex = table.addRow()
            table.setText(totalRowIndex, 1, u'всего', charFormat=bold)

            for i,data in enumerate(flatCodeTotal):
                total = data['free'] + data['pays']
                table.setText(freeRowIndex, 2+i, data['free'] if data['free'] else '', charFormat=bold, blockFormat=right)
                table.setText(paysRowIndex, 2+i, data['pays'] if data['pays'] else '', charFormat=bold, blockFormat=right)
                table.setText(totalRowIndex, 2+i, total if total else '', charFormat=bold, blockFormat=right)
                analysisTotal[i]['free'] += data['free']
                analysisTotal[i]['pays'] += data['pays']

            table.mergeCells(freeRowIndex,0, 3,1)
        ### end for flatCode

        freeRowIndex = table.addRow()
        table.setText(freeRowIndex, 0, u'Анализов итого', charFormat=bold, blockFormat=center)
        table.setText(freeRowIndex, 1, u'бесп.', charFormat=bold)

        paysRowIndex = table.addRow()
        table.setText(paysRowIndex, 1, u'хозрасч.', charFormat=bold)

        totalRowIndex = table.addRow()
        table.setText(totalRowIndex, 1, u'всего', charFormat=bold)

        for i,data in enumerate(analysisTotal):
            total = data['free'] + data['pays']
            table.setText(freeRowIndex, 2+i, data['free'], charFormat=bold, blockFormat=right)
            table.setText(paysRowIndex, 2+i, data['pays'], charFormat=bold, blockFormat=right)
            table.setText(totalRowIndex, 2+i, total, charFormat=bold, blockFormat=right)

        table.mergeCells(freeRowIndex,0, 3,1)


        freeRowIndex = table.addRow()
        table.setText(freeRowIndex, 0, u'Всего больных обследовано', charFormat=bold, blockFormat=center)
        table.setText(freeRowIndex, 1, u'бесп.', charFormat=bold)

        paysRowIndex = table.addRow()
        table.setText(paysRowIndex, 1, u'хозрасч.', charFormat=bold)

        totalRowIndex = table.addRow()
        table.setText(totalRowIndex, 1, u'всего', charFormat=bold)

        columnIndexesWithoutData = []
        for i,data in enumerate(clientsTotal):
            table.setText(freeRowIndex, 2+i, len(data['free']), charFormat=bold, blockFormat=right)
            table.setText(paysRowIndex, 2+i, len(data['pays']), charFormat=bold, blockFormat=right)
            table.setText(totalRowIndex, 2+i, len(data['free']) + len(data['pays']), charFormat=bold, blockFormat=right)

            if params['detailByOrgStructures'] and len(data['free']) + len(data['pays']) == 0:
                columnIndexesWithoutData.append(2+i)

        table.mergeCells(freeRowIndex,0, 3,1)

        # Удалить столбцы без данных, если детализируем по подразделениям
        if params['detailByOrgStructures']:
            qtexttable = table.table
            for columnIndex in sorted(columnIndexesWithoutData, reverse=True):
                qtexttable.removeColumns(columnIndex, 1)

            # Обновить ширину столбцов
            columnsCountTotal -= len(columnIndexesWithoutData)
            columnWidth = int(round(55.0 / columnsCountTotal))
            lengths = [QtGui.QTextLength(QtGui.QTextLength.PercentageLength, 15)] * 2
            lengths.extend([QtGui.QTextLength(QtGui.QTextLength.PercentageLength, max(1, columnWidth))] * columnsCountTotal)
            lengths.append(QtGui.QTextLength(QtGui.QTextLength.PercentageLength, 15))

            fmt = qtexttable.format()
            fmt.setColumnWidthConstraints(lengths)
            qtexttable.setFormat(fmt)

        return doc



class CReportLaboratoryActionsByMedicalTypeSetupDialog(Ui_ReportLaboratoryActionsByMedicalTypeSetupDialog, CDialogBase):
    def __init__(self, parent=None):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)

    def setTitle(self, title):
        self.setWindowTitle(title)
        self.setObjectName(title)

    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.cmbMedicalAidType.setCurrentIndex(params.get('medicalAidType', AID_TYPE_NOT_SET))
        self.chkDetailByQuarters.setChecked(params.get('detailByQuarters', False))
        self.chkDetailByMonths.setChecked(params.get('detailByMonths', False))
        self.chkDetailByOrgStructures.setChecked(params.get('detailByOrgStructures', False))

    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['medicalAidType'] = self.cmbMedicalAidType.currentIndex()
        result['detailByQuarters'] = self.chkDetailByQuarters.isChecked()
        result['detailByMonths'] = self.chkDetailByMonths.isChecked()
        result['detailByOrgStructures'] = self.chkDetailByOrgStructures.isChecked()
        return result

