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
from PyQt4.QtCore import pyqtSignature, QDate, QDateTime

from library.Utils      import forceInt, forceRef, forceString

from Events.ActionServiceType import CActionServiceType
from Events.Utils       import getActionTypeIdListByFlatCode, getWorkEventTypeFilter
from Orgs.Utils         import getOrgStructureFullName
from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.Utils      import dateRangeAsStr, getDataOrgStructure, getStringProperty, getStringPropertyValue


from Ui_AnaliticReportsStationary import Ui_AnaliticReportsStationaryDialog

class CAnaliticReportsStationaryDialog(QtGui.QDialog, Ui_AnaliticReportsStationaryDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbEventType.setTable('EventType', True, filter=getWorkEventTypeFilter(isApplyActive=True))
        self.cmbSpeciality.setTable('rbSpeciality')
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())
        if QtGui.qApp.userSpecialityId:
            self.cmbPerson.setValue(QtGui.qApp.userId)
            self.cmbSpeciality.setValue(QtGui.qApp.userSpecialityId)


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        self.cmbPerson.setValue(params.get('personId', None))
        self.cmbEventType.setValue(params.get('eventTypeId', None))
        self.cmbSpeciality.setValue(params.get('specialityId', None))
        self.cmbTypeSurgery.setCurrentIndex(params.get('typeSurgery', 0))


    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['orgStructureId'] = self.cmbOrgStructure.value()
        result['eventTypeId'] = self.cmbEventType.value()
        result['personId'] = self.cmbPerson.value()
        result['specialityId'] = self.cmbSpeciality.value()
        result['typeSurgery'] = self.cmbTypeSurgery.currentIndex()
        return result


    @pyqtSignature('int')
    def on_cmbOrgStructure_currentIndexChanged(self, index):
        orgStructureId = self.cmbOrgStructure.value()
        self.cmbPerson.setOrgStructureId(orgStructureId)


    @pyqtSignature('int')
    def on_cmbSpeciality_currentIndexChanged(self, index):
        specialityId = self.cmbSpeciality.value()
        self.cmbPerson.setSpecialityId(specialityId)


class CAnaliticReportsStationary(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Анализ оперативной деятельности врача')
        self.analiticReportsStationaryDialog = None
        self.clientDeath = 8
        self.setOrientation(QtGui.QPrinter.Landscape)


    def getSetupDialog(self, parent):
        result = CAnaliticReportsStationaryDialog(parent)
        self.analiticReportsStationaryDialog = result
        return result


    def dumpParams(self, cursor, params):
        description = []
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        if begDate and endDate:
            description.append(dateRangeAsStr(u'за период', begDate, endDate))
        orgStructureId = params.get('orgStructureId', None)
        if orgStructureId:
            description.append(u'подразделение: ' + getOrgStructureFullName(orgStructureId))
        else:
            description.append(u'подразделение: ЛПУ')
        db = QtGui.qApp.db
        personId = params.get('personId', None)
        if personId:
            description.append(u'врач %s'%(forceString(db.translate('vrbPersonWithSpeciality', 'id', personId, 'name'))))
        eventTypeId = params.get('eventTypeId', None)
        if eventTypeId:
            description.append(u'тип события %s'%(forceString(db.translate('EventType', 'id', eventTypeId, 'name'))))
        specialityId = params.get('specialityId', None)
        if specialityId:
            description.append(u'специальность %s'%(forceString(db.translate('rbSpeciality', 'id', specialityId, 'name'))))
        description.append(u'учет операций: %s'%([u'номенклатурный', u'пользовательский'][params.get('typeSurgery', 0)]))
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
        db = QtGui.qApp.db
        orgStructureId = params.get('orgStructureId', None)
        orgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', orgStructureId) if orgStructureId else []
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        isNomeclature = params.get('typeSurgery', 0)
        personParamsId = params.get('personId', None)
        eventTypeId = params.get('eventTypeId', None)
        specialityId = params.get('specialityId', None)
        doc = QtGui.QTextDocument()
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
        self.analiticReportsStationaryDialog.edtBegDate.setDate(begDate)
        self.analiticReportsStationaryDialog.edtEndDate.setDate(endDate)
        if begDate and endDate:
            doc = QtGui.QTextDocument()
            cursor = QtGui.QTextCursor(doc)
            cursor.setCharFormat(CReportBase.ReportTitle)
            cursor.insertText(u'Анализ оперативной деятельности врача')
            cursor.insertBlock()
            self.dumpParams(cursor, params)
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertBlock()
            cols = [('5%',[u'№ п/п', u'', u'', u'1'], CReportBase.AlignLeft),
                    ('17%', [u'ФИО врача, специальность', u'', u'', u'2'], CReportBase.AlignLeft),
                    ('6%', [u'Выполнено операций', u'', u'', u'3'], CReportBase.AlignLeft),
                    ('6%', [u'Из них', u'Плановые', u'', u'4'], CReportBase.AlignLeft),
                    ('6%', [u'', u'Экстренные', u'', u'5'], CReportBase.AlignLeft),
                    ('6%', [u'Наличие послеоперационных осложнений', u'При плановых операциях', u'Всего', u'6'], CReportBase.AlignLeft),
                    ('6%', [u'',u'', u'%', u'7'], CReportBase.AlignLeft),
                    ('6%', [u'', u'При экстренных операциях', u'Всего', u'8'], CReportBase.AlignLeft),
                    ('6%', [u'', u'', u'%', u'9'], CReportBase.AlignLeft),
                    ('6%', [u'Умерло', u'При плановых операциях', u'Всего', u'10'], CReportBase.AlignLeft),
                    ('6%', [u'',u'', u'%', u'11'], CReportBase.AlignLeft),
                    ('6%', [u'', u'При экстренных операциях', u'Всего', u'12'], CReportBase.AlignLeft),
                    ('6%', [u'',u'', u'%', u'13'], CReportBase.AlignLeft),
                    ('6%', [u'Умерло всего', u'', u'', u'14'], CReportBase.AlignLeft),
                    ('6%', [u'Послеоперационная летальность %',u'всего', u'', u'15'], CReportBase.AlignLeft)
                   ]
            table = createTable(cursor, cols)
            table.mergeCells(0, 0, 3, 1)
            table.mergeCells(0, 1, 3, 1)
            table.mergeCells(0, 2, 3, 1)
            table.mergeCells(0, 3, 1, 2)
            table.mergeCells(1, 3, 2, 1)
            table.mergeCells(1, 4, 2, 1)
            table.mergeCells(0, 5, 1, 4)
            table.mergeCells(1, 5, 1, 2)
            table.mergeCells(1, 7, 1, 2)
            table.mergeCells(0, 9, 1, 4)
            table.mergeCells(1, 9, 1, 2)
            table.mergeCells(1, 11, 1, 2)
            table.mergeCells(0, 13, 3, 1)
            table.mergeCells(0, 14, 3, 1)
            cnt = 1
            mapCodesToRowIdx = self.getSurgery(orgStructureIdList, begDate, endDate, isNomeclature, personParamsId, eventTypeId, specialityId)
            for key, reportLine in mapCodesToRowIdx.items():
                i = table.addRow()
                for col, val in enumerate(reportLine):
                    if col+1 not in [6, 8, 10, 12, 14]:
                        table.setText(i, col+1, forceString(val))
                table.setText(i, 0, cnt)
                table.setText(i, 6, '%.2f'%(round((reportLine[4]/(reportLine[2]*1.0))*100, 2)) if reportLine[2] else 0.00)
                table.setText(i, 8, '%.2f'%(round((reportLine[6]/(reportLine[3]*1.0))*100, 2)) if reportLine[3] else 0.00)
                table.setText(i, 10,'%.2f'%(round((reportLine[8]/(reportLine[2]*1.0))*100, 2)) if reportLine[2] else 0.00)
                table.setText(i, 12,'%.2f'%(round((reportLine[10]/(reportLine[3]*1.0))*100,2)) if reportLine[3] else 0.00)
                table.setText(i, 14,'%.2f'%(round((reportLine[12]/(reportLine[1]*1.0))*100,2)) if reportLine[1] else 0.00)
                cnt += 1
        return doc


    def getSurgery(self, orgStructureIdList, begDateTime, endDateTime, isNomeclature, personParamsId, eventTypeId, specialityId):
        db = QtGui.qApp.db
        reportData = {}
        tableEvent = db.table('Event')
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        tableClient = db.table('Client')
        tableRBService = db.table('rbService')
        tableEventType = db.table('EventType')
        tableRBMedicalAidType = db.table('rbMedicalAidType')
        tablePersonWithSpeciality = db.table('vrbPersonWithSpeciality')
        table = tableActionType.innerJoin(tableAction, tableActionType['id'].eq(tableAction['actionType_id']))
        table = table.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
        table = table.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
        table = table.innerJoin(tableRBMedicalAidType, tableEventType['medicalAidType_id'].eq(tableRBMedicalAidType['id']))
        table = table.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
        cond = [tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode('received%')),
                tableEvent['deleted'].eq(0),
                tableAction['deleted'].eq(0),
                tableActionType['deleted'].eq(0),
                tableClient['deleted'].eq(0),
                tableEventType['deleted'].eq(0)
                ]
        cond.append(tableRBMedicalAidType['code'].inlist([1, 2, 3]))
        joinOr1 = db.joinAnd([tableAction['begDate'].isNull(), tableAction['endDate'].isNull()])
        joinOr2 = db.joinAnd([tableAction['begDate'].isNotNull(), tableAction['begDate'].ge(begDateTime), tableAction['begDate'].lt(endDateTime.addDays(1))])
        joinOr3 = db.joinAnd([tableAction['begDate'].isNull(), tableAction['endDate'].isNotNull(), tableAction['endDate'].ge(begDateTime)])
        joinOr4 = db.joinAnd([tableAction['begDate'].isNotNull(), tableAction['begDate'].lt(begDateTime.addDays(1)), db.joinOr([tableAction['endDate'].isNull(), tableAction['endDate'].ge(begDateTime)])])
        cond.append(db.joinOr([joinOr1, joinOr2, joinOr3, joinOr4]))
        if orgStructureIdList:
            cond.append(getDataOrgStructure(u'Направлен в отделение', orgStructureIdList))
        eventIdList = db.getDistinctIdList(table, 'Event.id', cond)
        if eventIdList:
            cols = [tableAction['id'].alias('actionId'),
                    tableAction['amount'].alias('countSurgery'),
                    tableEvent['order'],
                    tableAction['event_id'],
                    tableAction['person_id'],
                    tableAction['MKB'],
                    tablePersonWithSpeciality['name'].alias('personName'),
                    tableActionType['id'].alias('actionTypeId'),
                    tableActionType['group_id'].alias('groupId'),
                    tableRBService['code'] if not isNomeclature else tableActionType['flatCode'].alias('code'),
                    tableActionType['name']
                    ]
            cols.append(u'%s AS orderAction'%getStringPropertyValue(u'Порядок'))
            cols.append(u'%s AS countDeathSurgery'%(getStringProperty(u'Исход операции', u'(APS.value LIKE \'умер%\' OR APS.value LIKE \'смерть%\')')))
            cols.append(u'%s AS countDeathHospital'%(getStringProperty(u'Исход госпитализации', u'(APS.value LIKE \'умер%\' OR APS.value LIKE \'смерть%\')')))
            cols.append(u'%s AS countComplication'%(getStringProperty(u'Осложнени%', u'(APS.value != \'\' OR APS.value != \' \')')))
            table = tableAction.innerJoin(tableActionType, tableAction['actionType_id'].eq(tableActionType['id']))
            table = table.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
            table = table.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
            table = table.innerJoin(tablePersonWithSpeciality, tableAction['person_id'].eq(tablePersonWithSpeciality['id']))
            cond = [tableAction['event_id'].inlist(eventIdList),
                    tableEvent['deleted'].eq(0),
                    tableAction['deleted'].eq(0),
                    tableActionType['deleted'].eq(0),
                    tableClient['deleted'].eq(0),
                    #tableActionType['class'].eq(2),
                    tableAction['endDate'].isNotNull()
                    ]
            if eventTypeId:
                cond.append(tableEvent['eventType_id'].eq(eventTypeId))
            if personParamsId:
                cond.append(tableAction['person_id'].eq(personParamsId))
            if specialityId:
                cond.append(tablePersonWithSpeciality['speciality_id'].eq(specialityId))
            cond.append(tableActionType['serviceType'].eq(CActionServiceType.operation))
            if not isNomeclature:
                table = table.innerJoin(tableRBService, tableRBService['id'].eq(tableActionType['nomenclativeService_id']))
            records = db.getRecordList(table, cols, cond, u'vrbPersonWithSpeciality.name')
            for record in records:
                orderEvent = [u'', u'плановый', u'экстренный', u'самотёком', u'принудительный', u'внутренний перевод', u'неотложная'][forceInt(record.value('order'))]
                orderAction = forceString(record.value('orderAction'))
                personName = forceString(record.value('personName'))
                countDeathSurgery = forceInt(record.value('countDeathSurgery'))
                countDeathHospital = forceInt(record.value('countDeathHospital'))
                countComplication = forceInt(record.value('countComplication'))
                countSurgery = forceInt(record.value('countSurgery'))
                personId = forceRef(record.value('person_id'))
                reportLine = reportData.get(personId, [0]*14)
                reportLine[0] = personName
                reportLine[1] += countSurgery
                if orderAction:
                    if orderAction == u'плановый':
                        reportLine[2] += countSurgery
                        if countComplication:
                            reportLine[4] += 1
                        if countDeathSurgery or (not countDeathSurgery and countDeathHospital):
                            reportLine[8] += 1
                    elif orderAction == u'экстренный':
                        reportLine[3] += countSurgery
                        if countComplication:
                           reportLine[6] += 1
                        if countDeathSurgery or (not countDeathSurgery and countDeathHospital):
                            reportLine[10] += 1
                elif orderEvent:
                    if orderEvent == u'плановый':
                        reportLine[2] += countSurgery
                        if countComplication:
                            reportLine[4] += 1
                        if countDeathSurgery or (not countDeathSurgery and countDeathHospital):
                            reportLine[8] += 1
                    elif orderEvent == u'экстренный':
                        reportLine[3] += countSurgery
                        if countComplication:
                            reportLine[6] += 1
                        if countDeathSurgery or (not countDeathSurgery and countDeathHospital):
                            reportLine[10] += 1
                if countDeathSurgery or (not countDeathSurgery and countDeathHospital):
                    reportLine[12] += 1
                reportData[personId] = reportLine
        return reportData


