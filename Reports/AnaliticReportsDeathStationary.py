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

from library.Utils      import forceInt, forceRef, forceString

from Events.Utils       import getActionTypeIdListByFlatCode, getWorkEventTypeFilter

from Orgs.Utils         import getOrgStructureFullName
from Reports.Report     import CReport, normalizeMKB
from Reports.ReportBase import CReportBase, createTable
from Reports.Utils      import dateRangeAsStr, getDataOrgStructure, getStringPropertyValue


from Ui_AnaliticReportsDeathStationary import Ui_AnaliticReportsDeathStationaryDialog

class CAnaliticReportsDeathStationaryDialog(QtGui.QDialog, Ui_AnaliticReportsDeathStationaryDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbEventType.setTable('EventType', True, filter=getWorkEventTypeFilter())
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        self.cmbEventType.setValue(params.get('eventTypeId', None))
        self.chkIsGroupingOS.setChecked(params.get('isGroupingOS', False))
        MKBFilter = params.get('MKBFilter', 0)
        self.cmbMKBFilter.setCurrentIndex(MKBFilter if MKBFilter else 0)
        self.edtMKBFrom.setText(params.get('MKBFrom', 'A00'))
        self.edtMKBTo.setText(params.get('MKBTo',   'Z99.9'))


    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['orgStructureId'] = self.cmbOrgStructure.value()
        result['eventTypeId'] = self.cmbEventType.value()
        result['isGroupingOS'] = self.chkIsGroupingOS.isChecked()
        result['MKBFilter'] = self.cmbMKBFilter.currentIndex()
        result['MKBFrom']   = unicode(self.edtMKBFrom.text())
        result['MKBTo']     = unicode(self.edtMKBTo.text())
        return result


    @pyqtSignature('int')
    def on_cmbMKBFilter_currentIndexChanged(self, index):
        mode = bool(index)
        for widget in (self.edtMKBFrom, self.edtMKBTo):
            widget.setEnabled(mode)


class CAnaliticReportsDeathStationary(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Анализ умерших больных в стационаре по возрастным группам')
        self.analiticReportsDeathStationaryDialog = None
        self.clientDeath = 8
        self.setOrientation(QtGui.QPrinter.Landscape)


    def getSetupDialog(self, parent):
        result = CAnaliticReportsDeathStationaryDialog(parent)
        self.analiticReportsDeathStationaryDialog = result
        return result


    def dumpParams(self, cursor, params):
        description = []
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        #eventOrder = params.get('eventOrder', 0)
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
        isGroupingOS = params.get('isGroupingOS', False)
        if isGroupingOS:
            description.append(u'группировка по подразделениям')
        MKBFilter = params.get('MKBFilter', 0)
        if MKBFilter:
            MKBFrom = params.get('MKBFrom', 'A00')
            MKBTo = params.get('MKBTo',   'Z99.9')
            description.append(u'коды диагнозов по МКБ с %s по %s'%(forceString(MKBFrom), forceString(MKBTo)))
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
        cursor.insertText(u'Анализ умерших больных в стационаре по возрастным группам')
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()
        cols = [('17%', [u'Подразделение', u'', u'1'], CReportBase.AlignLeft),
                ('7%', [u'Диагноз', u'', u'2'], CReportBase.AlignLeft),
                ('4%', [u'Умерло', u'', u'3'], CReportBase.AlignLeft),
                ('4%', [u'Пол', u'М', u'4'], CReportBase.AlignLeft),
                ('4%', [u'', u'Ж', u'5'], CReportBase.AlignLeft),
                ('4%', [u'Подростки', u'15-17', u'6'], CReportBase.AlignLeft),
                ('4%', [u'Взрослые',u'18-19', u'7'], CReportBase.AlignLeft),
                ('4%', [u'', u'20-29', u'8'], CReportBase.AlignLeft),
                ('4%', [u'', u'30-39', u'9'], CReportBase.AlignLeft),
                ('4%', [u'', u'40-49', u'10'], CReportBase.AlignLeft),
                ('4%', [u'',u'50-59', u'11'], CReportBase.AlignLeft),
                ('4%', [u'', u'60-69', u'12'], CReportBase.AlignLeft),
                ('4%', [u'',u'>70', u'13'], CReportBase.AlignLeft),
                ('4%', [u'Госп. план.', u'', u'14'], CReportBase.AlignLeft),
                ('4%', [u'Госп. экстр.',u'', u'15'], CReportBase.AlignLeft),
                ('4%', [u'Сроки госпитализации от начала заболевания.',u'0-6ч', u'16'], CReportBase.AlignLeft),
                ('4%', [u'',u'7-24ч', u'17'], CReportBase.AlignLeft),
                ('4%', [u'',u'> 24ч', u'18'], CReportBase.AlignLeft),
                ('4%', [u'',u'Без уточн.', u'19'], CReportBase.AlignLeft),
                ('4%', [u'Оперировано',u'Всего', u'20'], CReportBase.AlignLeft),
                ('4%', [u'',u'Осл.', u'21'], CReportBase.AlignLeft)
               ]
        table = createTable(cursor, cols)
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 2, 1)
        table.mergeCells(0, 3, 1, 2)
        table.mergeCells(0, 6, 1, 7)
        table.mergeCells(0, 13, 2, 1)
        table.mergeCells(0, 14, 2, 1)
        table.mergeCells(0, 15, 1, 4)
        table.mergeCells(0, 19, 1, 2)
        table.mergeCells(0, 20, 2, 1)
        mapCodesToRowIdx, reportDataTotalAll = self.getDeathInfo(params)
        keysList = mapCodesToRowIdx.keys()
        keysList.sort()
        isGroupingOS = params.get('isGroupingOS', False)
        for key in keysList:
            reportDataLine = mapCodesToRowIdx.get(key, {})
            mkbKeys = reportDataLine.keys()
            mkbKeys.sort()
            reportDataTotal = [0]*21
            reportDataTotal[0] = u''
            reportDataTotal[1] = u'Итого'
            caption = True
            for mkbKey in mkbKeys:
                reportLine = reportDataLine.get(mkbKey, [])
                if reportLine:
                    i = table.addRow()
                    if caption:
                        table.setText(i, 0, forceString(reportLine[0]))
                        caption = False
                        oldI = i
                    for col, val in enumerate(reportLine):
                        if col != 0:
                            table.setText(i, col, forceString(val))
                        if col != 0 and col != 1:
                            reportDataTotal[col] += val
            if isGroupingOS:
                i = table.addRow()
                for col, val in enumerate(reportDataTotal):
                    table.setText(i, col, forceString(val))
                table.mergeCells(oldI, 0, len(mkbKeys)+1, 1)
            else:
                table.mergeCells(oldI, 0, len(mkbKeys), 1)
        i = table.addRow()
        for col, val in enumerate(reportDataTotalAll):
            table.setText(i, col, forceString(val))
        return doc


    def getDeathInfo(self, params):
        orgStructureId = params.get('orgStructureId', None)
        orgStructureIndex = self.analiticReportsDeathStationaryDialog.cmbOrgStructure._model.index(self.analiticReportsDeathStationaryDialog.cmbOrgStructure.currentIndex(), 0, self.analiticReportsDeathStationaryDialog.cmbOrgStructure.rootModelIndex())
        orgStructureIdList = self.getOrgStructureIdList(orgStructureIndex) if orgStructureIndex.row() else []
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        eventTypeId = params.get('eventTypeId', None)
        MKBFilter = params.get('MKBFilter', 0)
        MKBFrom = params.get('MKBFrom', 'A00')
        MKBTo = params.get('MKBTo',   'Z99.9')
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
        self.analiticReportsDeathStationaryDialog.edtBegDate.setDate(begDate)
        self.analiticReportsDeathStationaryDialog.edtEndDate.setDate(endDate)
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
                tableClient['sex'],
                tableEvent['order']
                ]
        cols.append('age(Client.birthDate, Event.setDate) AS ageClient')
        cols.append(u'%s AS deliver'%getStringPropertyValue(u'Доставлен'))
        cols.append('''(SELECT OS.id
                        FROM ActionPropertyType AS APT
                        INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id
                        INNER JOIN ActionProperty_OrgStructure AS APOS ON APOS.id=AP.id
                        INNER JOIN OrgStructure AS OS ON OS.id=APOS.value
                        WHERE APT.actionType_id=Action.actionType_id AND AP.action_id=Action.id
                        AND APT.deleted=0 AND APT.name = '%s'
                        AND OS.deleted=0) AS nameOrgStructure'''%(u'Отделение'))
        cols.append('''(SELECT EXISTS(SELECT APS.id
                        FROM ActionPropertyType AS APT
                        INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id
                        INNER JOIN ActionProperty_String AS APS ON APS.id=AP.id
                        WHERE  Action.id IS NOT NULL AND APT.actionType_id=Action.actionType_id
                        AND AP.action_id=Action.id
                        AND APT.deleted=0 AND APT.name LIKE '%s' AND (APS.value != '%s'
                        OR APS.value != '%s'))
                        FROM Action
                        INNER JOIN ActionType ON Action.`actionType_id`=ActionType.`id`
                        left join rbService on rbService.id = ActionType.nomenclativeService_id
                        WHERE Action.`event_id` = Event.id AND (Action.`deleted`=0) AND (ActionType.`deleted`=0)
                        AND (Client.`deleted`=0) AND (Action.`endDate` IS NOT NULL)
                        AND ((ActionType.`code` LIKE '%s') OR (rbService.`infis` LIKE '%s')
                        OR (ActionType.serviceType = 4)) LIMIT 1) AS countComplication '''%(u'Осложнени%', u'', u' ', u'1-2', u'A16%'))
        cols.append('''(EXISTS(SELECT Action.id
                        FROM Action
                        INNER JOIN ActionType ON Action.`actionType_id`=ActionType.`id`
                        left join rbService on rbService.id = ActionType.nomenclativeService_id
                        WHERE Action.`event_id` = Event.id AND (Action.`deleted`=0) AND (ActionType.`deleted`=0)
                        AND (Client.`deleted`=0) AND (Action.`endDate` IS NOT NULL)
                        AND ((ActionType.`code` LIKE '%s') OR (rbService.`infis` LIKE '%s')
                        OR (ActionType.serviceType = 4)) LIMIT 1)) AS countSurgery'''%(u'1-2', u'A16%'))
        cond = [tableAction['actionType_id'].inlist(leavedIdList),
                tableEvent['deleted'].eq(0),
                tableAction['begDate'].isNotNull(),
                tableAction['deleted'].eq(0),
                tableActionType['deleted'].eq(0),
                tableClient['deleted'].eq(0),
                tableDiagnostic['diagnosisType_id'].eq(1),
                tableEventType['deleted'].eq(0)
                ]
        cond.append('''EXISTS(SELECT APS.id
                    FROM Action AS A
                    INNER JOIN ActionType AS AT ON A.`actionType_id`= AT.`id`
                    INNER JOIN ActionPropertyType AS APT ON APT.actionType_id=A.actionType_id
                    INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id
                    INNER JOIN ActionProperty_String AS APS ON APS.id=AP.id
                    WHERE A.`event_id` = Event.id AND A.`deleted`=0 AND A.actionType_id = Action.actionType_id AND AT.`deleted`=0
                    AND A.begDate IS NOT NULL AND AP.deleted = 0
                    AND AP.action_id=A.id
                    AND APT.deleted=0 AND APT.name = '%s'
                    AND (APS.value LIKE '%s' OR APS.value LIKE '%s'))
                    '''%( u'Исход госпитализации', u'умер%', u'смерть%'))
        if eventTypeId:
            cond.append(tableEventType['id'].eq(eventTypeId))
        cond.append(tableRBMedicalAidType['code'].inlist([1, 2, 3]))
        joinOr1 = db.joinAnd([tableAction['begDate'].isNull(), tableAction['endDate'].isNull()])
        joinOr2 = db.joinAnd([tableAction['begDate'].isNotNull(), tableAction['begDate'].ge(begDate), tableAction['begDate'].lt(endDate.addDays(1))])
        joinOr3 = db.joinAnd([tableAction['begDate'].isNull(), tableAction['endDate'].isNotNull(), tableAction['endDate'].ge(begDate)])
        joinOr4 = db.joinAnd([tableAction['begDate'].isNotNull(), tableAction['begDate'].lt(begDate.addDays(1)), db.joinOr([tableAction['endDate'].isNull(), tableAction['endDate'].ge(begDate)])])
        cond.append(db.joinOr([joinOr1, joinOr2, joinOr3, joinOr4]))
        if orgStructureId:
            cond.append(getDataOrgStructure(u'Отделение',orgStructureIdList if orgStructureIdList else [orgStructureId]))
        recordsOS = db.getRecordList('OrgStructure', 'id, name', '', 'name')
        orgStructureNameList = {}
        for recordOS in recordsOS:
            osId = forceRef(recordOS.value('id'))
            osName = forceString(recordOS.value('name'))
            orgStructureNameList[osId] = osName
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
        records = db.getRecordListGroupBy(table, cols, cond, 'Event.id')
        reportDataTotal = {}
        reportDataTotalAll = [0]*21
        reportDataTotalAll[0] = u'Итого'
        reportDataTotalAll[1] = u''
        for record in records:
            orderEvent = forceInt(record.value('order'))
            ageClient = forceInt(record.value('ageClient'))
            countComplication = forceInt(record.value('countComplication'))
            countSurgery = forceInt(record.value('countSurgery'))
            deliver = QString(forceString(record.value('deliver')))
            MKBRec = normalizeMKB(forceString(record.value('MKB')))
            sex = forceInt(record.value('sex'))
            nameOSId = forceRef(record.value('nameOrgStructure'))
            reportData = reportDataTotal.get(nameOSId, {})
            reportLine = reportData.get(MKBRec, [0]*21)
            reportLine[0] = orgStructureNameList.get(nameOSId, u'не определено')
            reportLine[1] = MKBRec
            reportLine[2] += 1
            reportDataTotalAll[2] += 1
            if sex == 1:
                reportLine[3] += 1
                reportDataTotalAll[3] += 1
            elif sex == 2:
                reportLine[4] += 1
                reportDataTotalAll[4] += 1
            if ageClient >= 15 and ageClient <= 17:
                reportLine[5] += 1
                reportDataTotalAll[5] += 1
            elif ageClient >= 18 and ageClient <= 19:
                reportLine[6] += 1
                reportDataTotalAll[6] += 1
            elif ageClient >= 20 and ageClient <= 29:
                reportLine[7] += 1
                reportDataTotalAll[7] += 1
            elif ageClient >= 30 and ageClient <= 39:
                reportLine[8] += 1
                reportDataTotalAll[8] += 1
            elif ageClient >= 40 and ageClient <= 49:
                reportLine[9] += 1
                reportDataTotalAll[9] += 1
            elif ageClient >= 50 and ageClient <= 59:
                reportLine[10] += 1
                reportDataTotalAll[10] += 1
            elif ageClient >= 60 and ageClient <= 69:
                reportLine[11] += 1
                reportDataTotalAll[11] += 1
            elif ageClient >= 70:
                reportLine[12] += 1
                reportDataTotalAll[12] += 1
            if orderEvent == 1:
                reportLine[13] += 1
                reportDataTotalAll[13] += 1
            elif orderEvent == 2:
                reportLine[14] += 1
                reportDataTotalAll[14] += 1
            if deliver.endsWith(u'в первые 6 часов'):
                reportLine[15] += 1
                reportDataTotalAll[15] += 1
            if deliver.endsWith(u'в течении 7-24 часов'):
                reportLine[16] += 1
                reportDataTotalAll[16] += 1
            if deliver.endsWith(u'позднее 24-х часов'):
                reportLine[17] += 1
                reportDataTotalAll[17] += 1
            else:
                reportLine[18] += 1
                reportDataTotalAll[18] += 1
            reportLine[19] += countSurgery
            reportDataTotalAll[19] += countSurgery
            reportLine[20] += countComplication
            reportDataTotalAll[20] += countComplication
            reportData[MKBRec] = reportLine
            reportDataTotal[nameOSId] = reportData
        return reportDataTotal, reportDataTotalAll


