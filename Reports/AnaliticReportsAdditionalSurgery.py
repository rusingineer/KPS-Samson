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
from PyQt4.QtCore import pyqtSignature, QDate, QDateTime, QString

from library.Utils      import forceDate, forceInt, forceString

from Events.ActionServiceType import CActionServiceType
from Events.Utils       import getActionTypeIdListByFlatCode, getWorkEventTypeFilter
from Orgs.Utils         import getOrgStructureFullName
from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.Utils      import dateRangeAsStr, getDataOrgStructure

from Ui_AnaliticReportsAdditionalSurgery import Ui_AnaliticReportsAdditionalSurgeryDialog


class CAnaliticReportsAdditionalSurgeryDialog(QtGui.QDialog, Ui_AnaliticReportsAdditionalSurgeryDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbEventType.setTable('EventType', True, filter=getWorkEventTypeFilter(isApplyActive=True))
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        self.cmbEventType.setValue(params.get('eventTypeId', None))
        MKBFilter = params.get('MKBFilter', 0)
        self.cmbMKBFilter.setCurrentIndex(MKBFilter if MKBFilter else 0)
        self.edtMKBFrom.setText(params.get('MKBFrom', 'A00'))
        self.edtMKBTo.setText(params.get('MKBTo',   'Z99.9'))
        self.cmbOrder.setCurrentIndex(params.get('order', 0))


    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['orgStructureId'] = self.cmbOrgStructure.value()
        result['eventTypeId'] = self.cmbEventType.value()
        result['MKBFilter'] = self.cmbMKBFilter.currentIndex()
        result['MKBFrom']   = unicode(self.edtMKBFrom.text())
        result['MKBTo']     = unicode(self.edtMKBTo.text())
        result['order']     = forceInt(self.cmbOrder.currentIndex())
        return result


    @pyqtSignature('int')
    def on_cmbMKBFilter_currentIndexChanged(self, index):
        mode = bool(index)
        for widget in (self.edtMKBFrom, self.edtMKBTo):
            widget.setEnabled(mode)


class CAnaliticReportsAdditionalSurgery(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Дополнительные сведения по хирургической помощи по нозологическим формам')
        self.analiticReportsAdditionalSurgeryDialog = None
        self.setOrientation(QtGui.QPrinter.Landscape)
        self.clientDeath = 8


    def getSetupDialog(self, parent):
        result = CAnaliticReportsAdditionalSurgeryDialog(parent)
        self.analiticReportsAdditionalSurgeryDialog = result
        return result


    def dumpParams(self, cursor, params):
        description = []
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        if begDate and endDate:
            description.append(dateRangeAsStr(u'за период', begDate, endDate))
        db = QtGui.qApp.db
        eventTypeId = params.get('eventTypeId', None)
        if eventTypeId:
            description.append(u'тип события %s'%(forceString(db.translate('EventType', 'id', eventTypeId, 'name'))))
        orgStructureId = params.get('orgStructureId', None)
        if orgStructureId:
            description.append(u'подразделение: ' + getOrgStructureFullName(orgStructureId))
        else:
            description.append(u'подразделение: ЛПУ')
        MKBFilter = params.get('MKBFilter', 0)
        if MKBFilter:
            MKBFrom = params.get('MKBFrom', 'A00')
            MKBTo = params.get('MKBTo',   'Z99.9')
            description.append(u'коды диагнозов по МКБ с %s по %s'%(forceString(MKBFrom), forceString(MKBTo)))
        order = params.get('order', 0)
        if order:
            description.append(u'порядок поступления %s'%([u'не задано', u'плановый', u'экстренный', u'самотёком', u'принудительный', u'внутренний перевод', u'неотложная'][order]))
        description.append(u'отчёт составлен: '+forceString(QDateTime.currentDateTime()))
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()


    def getOrgStructureIdList(self, treeIndex):
        treeItem = treeIndex.internalPointer() if treeIndex.isValid() else None
        return treeItem.getItemIdList() if treeItem else []


    def getOrgStructureId(self, treeIndex):
        treeItem = treeIndex.internalPointer() if treeIndex.isValid() else None
        return treeItem._id if treeItem else None


    def getOrgStructureName(self, treeIndex):
        treeItem = treeIndex.internalPointer() if treeIndex.isValid() else None
        return treeItem._name if treeItem else None


    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Дополнительные сведения по хирургической помощи по нозологическим формам')
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()
        cols = [('20%', [u'Степень тяжести заболевания', u'', u'', u'1'], CReportBase.AlignLeft),
                ('8%', [u'Выбыло человек', u'Всего', u'', u'2'], CReportBase.AlignLeft),
                ('8%', [u'', u'Умерло', u'', u'3'], CReportBase.AlignLeft),
                ('8%', [u'Не оперировано человек', u'Всего', u'', u'4'], CReportBase.AlignLeft),
                ('8%', [u'', u'Умерло', u'', u'5'], CReportBase.AlignLeft),
                ('8%', [u'Оперировано человек', u'Всего', u'', u'6'], CReportBase.AlignLeft),
                ('8%', [u'', u'Умерло', u'', u'7'], CReportBase.AlignLeft),
                ('8%', [u'', u'В срок до 7 суток', u'Всего', u'8'], CReportBase.AlignLeft),
                ('8%', [u'', u'', u'Умерло', u'9'], CReportBase.AlignLeft),
                ('8%', [u'', u'В срок позднее 7 суток', u'Всего', u'10'], CReportBase.AlignLeft),
                ('8%', [u'', u'', u'Умерло', u'11'], CReportBase.AlignLeft)
               ]
        table = createTable(cursor, cols)
        table.mergeCells(0, 0, 3, 1)
        table.mergeCells(0, 1, 1, 2)
        table.mergeCells(1, 1, 2, 1)
        table.mergeCells(1, 2, 2, 1)
        table.mergeCells(0, 3, 1, 2)
        table.mergeCells(1, 3, 2, 1)
        table.mergeCells(1, 4, 2, 1)
        table.mergeCells(0, 5, 1, 6)
        table.mergeCells(1, 5, 2, 1)
        table.mergeCells(1, 6, 2, 1)
        table.mergeCells(1, 7, 1, 2)
        table.mergeCells(1, 9, 1, 2)

        mapCodesToRowIdx, reportDataTotal = self.getDeathInfo(params)
        keysList = mapCodesToRowIdx.keys()
        keysList.sort()
        for key in keysList:
            reportDataLine = mapCodesToRowIdx.get(key, [0]*11)
            i = table.addRow()
            table.setText(i, 0, key)
            for col, val in enumerate(reportDataLine):
                table.setText(i, col+1, forceString(val))
        i = table.addRow()
        for col, val in enumerate(reportDataTotal):
            table.setText(i, col, forceString(val))
        return doc


    def getDeathInfo(self, params):
        orgStructureIndex = self.analiticReportsAdditionalSurgeryDialog.cmbOrgStructure._model.index(self.analiticReportsAdditionalSurgeryDialog.cmbOrgStructure.currentIndex(), 0, self.analiticReportsAdditionalSurgeryDialog.cmbOrgStructure.rootModelIndex())
        orgStructureIdList = self.getOrgStructureIdList(orgStructureIndex) if orgStructureIndex.row() else []
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        eventTypeId = params.get('eventTypeId', None)
        MKBFilter = params.get('MKBFilter', 0)
        MKBFrom = params.get('MKBFrom', 'A00')
        MKBTo = params.get('MKBTo',   'Z99.9')
        order = params.get('order',   0)
        if (not begDate) and (not endDate):
            currentDate = QDate.currentDate()
            begDate = QDate(currentDate.year(), 1, 1)
            endDate = currentDate
        elif not begDate:
            currentDate = QDate.currentDate()
            if currentDate > endDate:
                begDate = QDate(endDate.year(), 1, 1)
            else:
                begDate = currentDate
        elif not endDate:
            currentDate = QDate.currentDate()
            if currentDate > begDate:
                endDate = QDate(begDate.year(), 1, 1)
            else:
                endDate = currentDate
        self.analiticReportsAdditionalSurgeryDialog.edtBegDate.setDate(begDate)
        self.analiticReportsAdditionalSurgeryDialog.edtEndDate.setDate(endDate)
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        tableClient = db.table('Client')
        tableEventType = db.table('EventType')
        tableRBMedicalAidType = db.table('rbMedicalAidType')
        tableDiagnosis = db.table('Diagnosis')
        tableDiagnostic = db.table('Diagnostic')
        table = tableEvent.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
        table = table.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        table = table.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
        table = table.innerJoin(tableRBMedicalAidType, tableEventType['medicalAidType_id'].eq(tableRBMedicalAidType['id']))
        table = table.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
        leavedIdList = getActionTypeIdListByFlatCode('leaved%')
        cols = [tableAction['event_id'],
                tableAction['person_id'],
                tableEvent['order'],
                tableEvent['setDate']
                ]
        cols.append(u'''(SELECT APS.value
                    FROM ActionPropertyType AS APT
                    INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id
                    INNER JOIN ActionProperty_String AS APS ON APS.id=AP.id
                    WHERE  Action.id IS NOT NULL AND APT.actionType_id=Action.actionType_id AND AP.action_id=Action.id
                    AND APT.deleted=0 AND APT.name = '%s'
                    LIMIT 1) AS conditionClient'''%(u'Состояние'))
        cols.append('''EXISTS(SELECT APS.id
                    FROM Action AS A
                    INNER JOIN ActionType AS AT ON A.`actionType_id`= AT.`id`
                    INNER JOIN ActionPropertyType AS APT ON APT.actionType_id=A.actionType_id
                    INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id
                    INNER JOIN ActionProperty_String AS APS ON APS.id=AP.id
                    WHERE A.`event_id` = Event.id AND A.`deleted`=0 AND A.actionType_id IN (%s) AND AT.`deleted`=0
                    AND A.begDate IS NOT NULL AND AP.deleted = 0
                    AND AP.action_id=A.id
                    AND APT.deleted=0 AND APT.name = '%s'
                    AND (APS.value LIKE '%s' OR APS.value LIKE '%s')) AS resultHospital
                    '''%(','.join(str(leavedId) for leavedId in leavedIdList), u'Исход госпитализации', u'умер%', u'смерть%'))
        cols.append('''(EXISTS(SELECT Action.id
                        FROM Action
                        INNER JOIN ActionType ON Action.`actionType_id`=ActionType.`id`
                        WHERE Action.`event_id` = Event.id AND (Action.`deleted`=0) AND (ActionType.`deleted`=0)
                        AND (Client.`deleted`=0) AND (Action.`endDate` IS NOT NULL)
                        AND ActionType.serviceType = %d)) AS countSurgery'''%(CActionServiceType.operation))
        cols.append('''(SELECT A.begDate
                        FROM Action AS A
                        INNER JOIN ActionType AS AT ON A.`actionType_id`=AT.`id`
                        WHERE A.`event_id` = Event.id AND (A.`deleted`=0) AND (AT.`deleted`=0)
                        AND (Client.`deleted`=0) AND (A.`endDate` IS NOT NULL)
                        AND AT.serviceType = %d
                        LIMIT 1) AS begDateSurgery'''%(CActionServiceType.operation))
        cond = [tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode('received%')),
                tableEvent['deleted'].eq(0),
                tableAction['begDate'].isNotNull(),
                tableAction['deleted'].eq(0),
                tableActionType['deleted'].eq(0),
                tableClient['deleted'].eq(0),
                tableEventType['deleted'].eq(0)
                ]
        if eventTypeId:
            cond.append(tableEventType['id'].eq(eventTypeId))
        cond.append(tableRBMedicalAidType['code'].inlist([1, 2, 3]))
        joinOr1 = db.joinAnd([tableAction['begDate'].isNull(), tableAction['endDate'].isNull()])
        joinOr2 = db.joinAnd([tableAction['begDate'].isNotNull(), tableAction['begDate'].ge(begDate), tableAction['begDate'].lt(endDate.addDays(1))])
        joinOr3 = db.joinAnd([tableAction['begDate'].isNull(), tableAction['endDate'].isNotNull(), tableAction['endDate'].ge(begDate)])
        joinOr4 = db.joinAnd([tableAction['begDate'].isNotNull(), tableAction['begDate'].lt(begDate.addDays(1)), db.joinOr([tableAction['endDate'].isNull(), tableAction['endDate'].ge(begDate)])])
        cond.append(db.joinOr([joinOr1, joinOr2, joinOr3, joinOr4]))
        if orgStructureIdList:
            cond.append(getDataOrgStructure(u'Направлен в отделение', orgStructureIdList))
        if order:
            cond.append(tableEvent['order'].eq(order))
        if MKBFilter:
            table = table.innerJoin(tableDiagnostic, tableEvent['id'].eq(tableDiagnostic['event_id']))
            table = table.innerJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
            cond.append(tableDiagnostic['deleted'].eq(0))
            cond.append(tableDiagnosis['deleted'].eq(0))
            cond.append('Diagnosis.MKB >= \'%s\' AND Diagnosis.MKB <= \'%s\''%(MKBFrom, MKBTo))
        else:
            table = table.leftJoin(tableDiagnostic, tableEvent['id'].eq(tableDiagnostic['event_id']))
            table = table.leftJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
            cond.append(db.joinOr([tableDiagnostic['id'].isNull(), tableDiagnostic['deleted'].eq(0)]))
            cond.append(db.joinOr([tableDiagnosis['id'].isNull(), tableDiagnosis['deleted'].eq(0)]))
        cols.append(tableDiagnosis['MKB'])
        cond.append('''EXISTS(SELECT A.id
            FROM Action AS A
            INNER JOIN ActionType AS AT ON A.`actionType_id`= AT.`id`
            WHERE A.`event_id` = Event.id AND A.`deleted`=0 AND A.actionType_id IN (%s) AND AT.`deleted`=0
            AND A.begDate IS NOT NULL)'''%(','.join(str(leavedId) for leavedId in leavedIdList)))
        records = db.getRecordListGroupBy(table, cols, cond, u'Event.id', 'conditionClient')
        reportData = {}
        reportDataTotal = [0]*11
        reportDataTotal[0] = u'Итого'
        for record in records:
            countSurgery = forceInt(record.value('countSurgery'))
            conditionClient = QString(forceString(record.value('conditionClient')))
            if not conditionClient:
                conditionClient = u'без уточнения'
            resultHospital =  forceInt(record.value('resultHospital'))
            begDateSurgery = forceDate(record.value('begDateSurgery'))
            setDate = forceDate(record.value('setDate'))
            daysSurgery = 0
            if setDate and begDateSurgery:
                daysSurgery = setDate.daysTo(begDateSurgery) if begDateSurgery != setDate else 1
            reportLine = reportData.get(conditionClient, [0]*10)
            reportLine[0] += 1
            reportLine[1] += resultHospital
            reportDataTotal[1] += 1
            reportDataTotal[2] += resultHospital
            if countSurgery:
                reportLine[4] += countSurgery
                reportLine[5] += resultHospital
                reportDataTotal[5] += countSurgery
                reportDataTotal[6] += resultHospital
                if daysSurgery <= 7:
                    reportLine[6] += countSurgery
                    reportLine[7] += resultHospital
                    reportDataTotal[7] += countSurgery
                    reportDataTotal[8] += resultHospital
                elif daysSurgery > 7:
                    reportLine[8] += countSurgery
                    reportLine[9] += resultHospital
                    reportDataTotal[9] += countSurgery
                    reportDataTotal[10] += resultHospital
            else:
                reportLine[2] += 1
                reportLine[3] += resultHospital
                reportDataTotal[3] += 1
                reportDataTotal[4] += resultHospital
            reportData[conditionClient] = reportLine
        return reportData, reportDataTotal


