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

from RefBooks.Equipment.Protocol import CEquipmentProtocol
from Reports.Report import CReport
from Reports.ReportBase import CReportBase, createTable
from library.Utils               import forceRef, forceString, formatNameByRecord, forceInt, forceDouble


PROPS_LIMIT = 25

AVAILABLE_EQUIPMENT_PROTOCOLS = (
#    0,  #  HL2,5
    CEquipmentProtocol.astm,     #  ASTM
    CEquipmentProtocol.fhir102,  #  FHIR
)


class CActionPropertiesTestsReport(CReport):
    def __init__(self, parent = None):
        CReport.__init__(self, parent)
        self.setTitle(u'Отчет по лабораторным исследованиям')
        self._mapTestId2Column = {}
        self._mapOrgstructureClientTests = {}
        self._mapTestId2Name = {}
        self._mapOrgStructureId2Name = {}
        self._mergeCellsDataList = []
        self._idsSet = set()

        self._data = []

    def getSetupDialog(self, parent):
        dialog = CReport.getSetupDialog(self, parent)
        dialog.setEventTypeVisible(False)
        dialog.setOnlyPermanentAttachVisible(False)
        dialog.setActionTypeVisible(True)
        dialog.setEquipmentVisible(True)
        dialog.cmbEquipment.setFilter('protocol IN {0}'.format(AVAILABLE_EQUIPMENT_PROTOCOLS))
        dialog.chkActionClass.setVisible(False)
        layout = dialog.layout()
        if layout:
            minimumSize = layout.minimumSize()
            dialog.resize(dialog.size().width(), minimumSize.height())

        return dialog

    def preCheckData(self, parent, params):
        self._mapTestId2Column = {}
        self._mapOrgstructureClientTests = {}
        self._mapTestId2Name = {}
        self._mapOrgStructureId2Name = {}
        self._mergeCellsDataList = []
        self._idsSet = set()

        self._data = []

        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        actionTypeClass = params.get('actionTypeClass', None)
        actionTypeId = params.get('actionTypeId', None)
        equipmentId = params.get('equipmentId', None)

        db = QtGui.qApp.db

        tableEvent = db.table('Event')
        tableClient = db.table('Client')
        tableAction = db.table('Action')
        tableActionProperty = db.table('ActionProperty')
        tableActionType = db.table('ActionType')
        tableActionPropertyType = db.table('ActionPropertyType')
        tableTest = db.table('rbTest')
        tableEquipmentTest = db.table('rbEquipment_Test')
        tableIntValue = db.table('ActionProperty_Integer')
        tableStringValue = db.table('ActionProperty_String')
        tableDoubleValue = db.table('ActionProperty_Double')
        tablePerson = db.table('vrbPerson')
        tableOrgStructure = db.table('OrgStructure')
        tableTakenTissueJournal = db.table('TakenTissueJournal')
        tableCourseTTJ = db.table('TakenTissueJournal').alias('CourseTTS')
        tableProbe = db.table('Probe')

        queryTable = tableAction.leftJoin(tableActionProperty,
                                          tableActionProperty['action_id'].eq(tableAction['id']))
        queryTable = queryTable.leftJoin(tableActionType,
                                         tableActionType['id'].eq(tableAction['actionType_id']))
        queryTable = queryTable.leftJoin(tableActionPropertyType,
                                         [tableActionPropertyType['id'].eq(tableActionProperty['type_id']),
                                          tableActionPropertyType['actionType_id'].eq(tableActionType['id'])])
        queryTable = queryTable.leftJoin(tableTest, tableTest['id'].eq(tableActionPropertyType['test_id']))
        queryTable = queryTable.leftJoin(tableEquipmentTest,
                                         tableEquipmentTest['test_id'].eq(tableTest['id']))
        queryTable = queryTable.leftJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
        queryTable = queryTable.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))

        queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(tableAction['setPerson_id']))
        queryTable = queryTable.leftJoin(tableOrgStructure, tableOrgStructure['id'].eq(tablePerson['orgStructure_id']))

        queryTable = queryTable.leftJoin(tableIntValue,
                                         tableIntValue['id'].eq(tableActionProperty['id']))
        queryTable = queryTable.leftJoin(tableStringValue,
                                         tableStringValue['id'].eq(tableActionProperty['id']))
        queryTable = queryTable.leftJoin(tableDoubleValue,
                                         tableDoubleValue['id'].eq(tableActionProperty['id']))

        queryTable = queryTable.leftJoin(tableTakenTissueJournal, tableTakenTissueJournal['id'].eq(tableAction['takenTissueJournal_id']))
        queryTable = queryTable.leftJoin(tableCourseTTJ, tableCourseTTJ['parent_id'].eq(tableTakenTissueJournal['id']))
        queryTable = queryTable.leftJoin(tableProbe, db.joinAnd([
            tableProbe['takenTissueJournal_id'].eq(tableCourseTTJ['id']),
            tableProbe['test_id'].eq(tableActionPropertyType['test_id'])
        ]))


        cond = [tableAction['endDate'].ge(begDate),
                tableAction['endDate'].lt(endDate.addDays(1)),
                tableEquipmentTest['equipment_id'].eq(equipmentId),
                tableTest['id'].isNotNull(),
                tableAction['deleted'].eq(0),
                tableEvent['deleted'].eq(0),
                tableClient['id'].isNotNull()]

        if actionTypeClass is not None:
            cond.append(tableActionType['class'].eq(actionTypeClass))
        if actionTypeId is not None:
            actionTypeIdList = db.getDescendants(tableActionType, 'group_id', actionTypeId)
            cond.append(tableActionType['id'].inlist(actionTypeIdList))

        fields = [tableClient['id'].alias('clientId'),
                  tableClient['firstName'],
                  tableClient['lastName'],
                  tableClient['patrName'],
                  tableActionType['id'].alias('actionTypeId'),
                  tableActionType['name'].alias('actionTypeName'),
                  tableAction['begDate'].alias('actionBegDate'),
                  tableAction['id'].alias('actionId'),
                  tableOrgStructure['id'].alias('setOrgStructureId'),
                  tableOrgStructure['name'].alias('setOrgStructureName'),
                  tableTest['id'].alias('testId'),
                  tableTest['name'].alias('testName'),
                  tableActionProperty['id'].alias('propertyId'),
                  tableActionPropertyType['id'].alias('propertyTypeId'),
                  tableActionPropertyType['name'].alias('propertyTypeName'),
                  tableIntValue['value'].alias('intValue'),
                  tableStringValue['value'].alias('stringValue'),
                  tableDoubleValue['value'].alias('doubleValue'),
                  tableCourseTTJ['externalId'].alias('ttjIBM'),
                  tableProbe['externalId'].alias('probeIBM')]

        order = [tableOrgStructure['id'].name(),
                 tableClient['lastName'].name(),
                 tableClient['firstName'].name(),
                 tableClient['patrName'].name(),
                 tableClient['id'].name(),
                 tableActionType['id'].name(),
                 tableAction['id'].name(),
                 tableTest['id'].name()]

        stmt = db.selectStmt(queryTable, fields, cond, order)

        query = db.query(stmt)

        needAsk = True
        while query.next():
            if needAsk and len(self._idsSet) > PROPS_LIMIT:
                if QtGui.QMessageBox.question(
                        parent, u'Внимание!',
                        u'В отчете будет указано очень много исследований, отображение данных может быть не удобным.'
                        u'\nПродолжить?',
                        QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel) != QtGui.QMessageBox.Ok:
                    return False
                needAsk = False
            record = query.record()
            clientId = forceRef(record.value('clientId'))
            setOrgStructureId = forceRef(record.value('setOrgStructureId'))
            setOrgStructureName = forceString(record.value('setOrgStructureName'))
            testId = forceRef(record.value('testId'))
            qIntValue = record.value('intValue')
            qStringValue = record.value('stringValue')
            qDoubleValue = record.value('doubleValue')
            testName = forceString(record.value('testName'))
            ttjIBM = forceString(record.value('ttjIBM'))
            probeIBM = forceString(record.value('probeIBM'))

            passRow =  qStringValue.isNull() and qIntValue.isNull() and qDoubleValue.isNull()

            if not qStringValue.isNull():
                value = forceString(qStringValue)
            elif not qIntValue.isNull():
                value = forceInt(qIntValue)
            elif not qDoubleValue.isNull():
                value = forceDouble(qDoubleValue)
            else:
                value = ''

            if passRow:
                continue

            if testId not in self._mapTestId2Name:
                self._mapTestId2Name[testId] = testName
            if setOrgStructureId not in self._mapOrgStructureId2Name:
                self._mapOrgStructureId2Name[setOrgStructureId] = setOrgStructureName
            ibm = probeIBM if probeIBM else ttjIBM
            row = (testId, clientId, formatNameByRecord(record), value, setOrgStructureId, ibm)
            self._data.append(row)
            self._idsSet.add(testId)

        return True

    def build(self, params):

        tableColumns = self.__getTableColumns()

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        table = createTable(cursor, tableColumns)
        for mergeCellsData in self._mergeCellsDataList:
            table.mergeCells(*mergeCellsData)

        orgStructureClientTestRow = {}

        existsDataKeys = set()

        defaultRow = None
        i = 0
        prevClientId = prevSetOrgStructureId = None
        for (testId, clientId, clientName, value, setOrgStructureId, ibm) in self._data:
            rowKey = (setOrgStructureId, clientId, testId)
            existsDataKey = rowKey + (value,)

            if existsDataKey in existsDataKeys:
                continue
            existsDataKeys.add(existsDataKey)

            newRow = clientId != prevClientId or setOrgStructureId != prevSetOrgStructureId
            sameRow = rowKey in orgStructureClientTestRow

            if newRow or (sameRow and orgStructureClientTestRow[rowKey] > i):
                i = table.addRow()
                table.setText(i, 0, i)
                table.setText(i, 1, clientName)
                table.setText(i, 2, self._mapOrgStructureId2Name[setOrgStructureId])
                if newRow:
                    defaultRow = i

            prevClientId = clientId
            prevSetOrgStructureId = setOrgStructureId
            columnIndex = self._mapTestId2Column[testId]

            row = orgStructureClientTestRow.setdefault(rowKey, defaultRow)
            orgStructureClientTestRow[rowKey] += 1

            table.setText(row, columnIndex+3, value)

        return doc

    def __getTableColumns(self):
        nWidth = 2
        clientWidth = 7
        orgstructureWidth = 7
        condWidth = 100 - clientWidth - orgstructureWidth - nWidth
        tableColumns = [
            ('{0}%'.format(nWidth), [u'№'], CReportBase.AlignRight),
            ('{0}%'.format(clientWidth), [u'Пациент'], CReportBase.AlignLeft),
            ('{0}%'.format(orgstructureWidth), [u'Подразделение'], CReportBase.AlignLeft),
        ]
        self._mergeCellsDataList.extend([(0, 0, 2, 1)])

        keysLen = len(self._idsSet)
        if not keysLen:
            return tableColumns

        width = condWidth / keysLen
        residue = condWidth % keysLen
        residueCount = 0

        for columnIndex, testId in enumerate(self._idsSet):
            self._mapTestId2Column[testId] = columnIndex
            if residueCount < residue:
                columnWidth = width+1
                residueCount += 1
            else:
                columnWidth = width


            tableColumns.append(('{0}%'.format(min(columnWidth, 15)),
                                 [self._mapTestId2Name[testId]],
                                 CReportBase.AlignRight))
        return tableColumns
