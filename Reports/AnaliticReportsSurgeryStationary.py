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

from library.Utils            import forceBool, forceDate, forceInt, forceRef, forceString

from Orgs.Utils               import getOrgStructureFullName
from Events.ActionServiceType import CActionServiceType
from Events.Utils             import getActionTypeIdListByFlatCode, getWorkEventTypeFilter
from Reports.HospitalBedProfileListDialog import CHospitalBedProfileListDialog
from Reports.ReportView       import CPageFormat
from Reports.Report           import CReport
from Reports.ReportBase       import CReportBase, createTable
from Reports.Utils            import dateRangeAsStr, getDataOrgStructure, getPropertyAPHBP, getStringProperty, getStringPropertyForTableName

from Ui_AnaliticReportsSurgeryStationary import Ui_AnaliticReportsSurgeryStationaryDialog


class CAnaliticReportsSurgeryStationaryDialog(QtGui.QDialog, Ui_AnaliticReportsSurgeryStationaryDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbEventType.setTable('EventType', True, filter=getWorkEventTypeFilter(isApplyActive=True))
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())
        self.cmbFinance.setTable('rbFinance', addNone=True)
        self.profileList = []


    def setProfileListEnabled(self, value):
        self.btnProfileList.setEnabled(value)
        self.lblProfileList.setEnabled(value)


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        self.cmbEventType.setValue(params.get('eventTypeId', None))
        self.chkIsGroupingOS.setChecked(params.get('isGroupingOS', False))
        self.chkIsGroupingParentOS.setChecked(params.get('isGroupingParentOS', False))
        self.chkShowFlatCode.setChecked(params.get('showFlatCode', False))
        self.chkExistFlatCode.setChecked(params.get('existFlatCode', False))
        self.cmbTypeSurgery.setCurrentIndex(params.get('typeSurgery', 0))
        self.cmbSelectActionType.setCurrentIndex(params.get('selectActionType', 0))
        self.cmbSelectType.setCurrentIndex(params.get('selectType', 0))
        self.cmbPerson.setValue(params.get('personId', None))
        self.cmbFinance.setValue(params.get('financeId', None))
        self.profileList = params.get('profileList', [])
        if self.profileList:
            db = QtGui.qApp.db
            table = db.table('rbHospitalBedProfile')
            records = db.getRecordList(table, [table['name']], [table['id'].inlist(self.profileList)])
            self.lblProfileList.setText(u', '.join(forceString(record.value('name')) for record in records if forceString(record.value('name'))))
        else:
            self.lblProfileList.setText(u'не задано')
        self.setProfileListEnabled(bool(self.cmbSelectActionType.currentIndex() in [3, 4]))


    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['orgStructureId'] = self.cmbOrgStructure.value()
        result['eventTypeId'] = self.cmbEventType.value()
        result['typeSurgery'] = self.cmbTypeSurgery.currentIndex()
        result['isGroupingOS'] = self.chkIsGroupingOS.isChecked()
        result['isGroupingParentOS'] = self.chkIsGroupingParentOS.isChecked()
        result['showFlatCode'] = self.chkShowFlatCode.isChecked()
        result['existFlatCode'] = self.chkExistFlatCode.isChecked()
        result['selectActionType'] = self.cmbSelectActionType.currentIndex()
        result['selectType'] = self.cmbSelectType.currentIndex()
        result['personId'] = self.cmbPerson.value()
        result['financeId'] = self.cmbFinance.value()
        result['profileList'] = self.profileList
        return result


    @pyqtSignature('')
    def on_btnProfileList_clicked(self):
        self.profileList = []
        self.lblProfileList.setText(u'не задано')
        dialog = CHospitalBedProfileListDialog(self)
        if dialog.exec_():
            self.profileList = dialog.values()
            if self.profileList:
                db = QtGui.qApp.db
                table = db.table('rbHospitalBedProfile')
                records = db.getRecordList(table, [table['name']], [table['id'].inlist(self.profileList)])
                nameList = []
                for record in records:
                    nameList.append(forceString(record.value('name')))
                self.lblProfileList.setText(u', '.join(name for name in nameList if name))


    @pyqtSignature('int')
    def on_cmbSelectActionType_currentIndexChanged(self, index):
        self.setProfileListEnabled(bool(index in [3, 4]))


class CAnaliticReportsSurgeryStationary(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Общие показатели хирургической деятельности')
        self.analiticReportsSurgeryStationaryDialog = None
        self.orientation = CPageFormat.Landscape
        self.clientDeath = 8


    def getSetupDialog(self, parent):
        result = CAnaliticReportsSurgeryStationaryDialog(parent)
        self.analiticReportsSurgeryStationaryDialog = result
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
        selectType = params.get('selectType', 0)
        description.append(u'выбор: %s'%{0: u'по врачу ответственному за действие',
                                         1: u'по врачу ответственному за событие'}.get(selectType, u'по врачу ответственному за действие'))
        personId = params.get('personId', None)
        if personId:
            description.append(u'врач: %s'%(forceString(QtGui.qApp.db.translate('vrbPersonWithSpeciality', 'id', personId, 'name'))))
        orgStructureId = params.get('orgStructureId', None)
        if orgStructureId:
            description.append(u'подразделение: ' + getOrgStructureFullName(orgStructureId))
        else:
            description.append(u'подразделение: ЛПУ')
        selectActionType = params.get('selectActionType', 0)
        if selectActionType in [3, 4]:
            profileList = params.get('profileList', None)
            if profileList:
                db = QtGui.qApp.db
                table = db.table('rbHospitalBedProfile')
                records = db.getRecordList(table, [table['name']], [table['id'].inlist(profileList)])
                nameList = []
                for record in records:
                    nameList.append(forceString(record.value('name')))
                description.append(u'Профиль выбытия:  %s'%(u','.join(name for name in nameList if name)))
            else:
                description.append(u'Профиль выбытия:  не задано')
        financeId = params.get('financeId', None)
        description.append(u'тип финансирования: %s'%(forceString(QtGui.qApp.db.translate('rbFinance', 'id', financeId, 'name')) if financeId else u'не задано'))
        isGroupingOS = params.get('isGroupingOS', False)
        if isGroupingOS:
            description.append(u'с детализацией по операциям')
        showFlatCode = params.get('showFlatCode', False)
        if showFlatCode:
            description.append(u'отображать "код для отчетов"')
        existFlatCode = params.get('existFlatCode', False)
        if existFlatCode:
            description.append(u'учитывать только заполненный "код для отчетов"')
        description.append(u'отбор по %s'%([u'операциям', u'поступлению', u'движению', u'выписке', u'выписке+внешним Событиям'][selectActionType]))
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
        orgStructureId     = params.get('orgStructureId', None)
        orgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', orgStructureId) if orgStructureId else []
        begDate            = params.get('begDate', QDate())
        endDate            = params.get('endDate', QDate())
        eventTypeId        = params.get('eventTypeId', None)
        isGroupingOS       = params.get('isGroupingOS', False)
        isGroupingParentOS = params.get('isGroupingParentOS', False)
        showFlatCode       = params.get('showFlatCode', False)
        existFlatCode       = params.get('existFlatCode', False)
        isNomeclature      = params.get('typeSurgery', 0)
        selectActionType   = params.get('selectActionType', 0)
        selectType         = params.get('selectType', 0)
        personId           = params.get('personId', None)
        financeId          = params.get('financeId', None)
        profileList        = params.get('profileList', None)

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
        self.analiticReportsSurgeryStationaryDialog.edtBegDate.setDate(begDate)
        self.analiticReportsSurgeryStationaryDialog.edtEndDate.setDate(endDate)
        if begDate and endDate:
            doc = QtGui.QTextDocument()
            cursor = QtGui.QTextCursor(doc)
            cursor.setCharFormat(CReportBase.ReportTitle)
            cursor.insertText(u'Общие показатели хирургической деятельности')
            cursor.insertBlock()
            self.dumpParams(cursor, params)
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertBlock()

            cols = [('10%',[u'Подразделение', u'', u''], CReportBase.AlignLeft),
                    ('18%', [u'Название операции', u'', u''], CReportBase.AlignLeft),
                    ('5%', [u'Оперировано больных', u'Всего',  u''], CReportBase.AlignLeft),
                    ('5%', [u'', u'С план. опер.',  u''], CReportBase.AlignLeft),
                    ('5%', [u'Операций', u'Всего',  u''], CReportBase.AlignLeft),
                    ('5%', [u'', u'Плановых',  u''], CReportBase.AlignLeft),
                    ('5%', [u'Послеоперационные осложнения', u'Всего',  u''], CReportBase.AlignLeft),
                    ('5%', [u'', u'Плановых',  u''], CReportBase.AlignLeft),
                    ('5%', [u'Умерло оперированных',u'Всего',  u''], CReportBase.AlignLeft),
                    ('5%', [u'', u'С план. опер.',  u''], CReportBase.AlignLeft),
                    ('5%', [u'Дооперационные койко-дни', u'Всего',  u''], CReportBase.AlignLeft),
                    ('5%', [u'', u'С план. опер.',  u''], CReportBase.AlignLeft),
                    ('5%', [u'Послеоперационные койко-дни',u'Всего',  u''], CReportBase.AlignLeft),
                    ('5%', [u'', u'С план. опер.',  u''], CReportBase.AlignLeft),
                    ('5%', [u'Общий койко-день',u'Всего',  u''], CReportBase.AlignLeft),
                    ('5%', [u'', u'С план. опер.',  u''], CReportBase.AlignLeft)
                   ]
            if isGroupingParentOS:
                cols.insert(0, ('10%', [u'', u'', u''], CReportBase.AlignLeft))
            showFlatCode = int(showFlatCode)
            if showFlatCode:
                cols.insert(2 if isGroupingParentOS else 1, ('5%', [u'Код операции / Код для отчетов', u'', u''], CReportBase.AlignLeft))
            else:
                if isNomeclature:
                    cols.insert(1, ('5%', [u'Код операции', u'', u''], CReportBase.AlignLeft))
            for row, col in enumerate(cols):
                cols[row][1][2] = forceString(row+1)
            table = createTable(cursor, cols)
            if isGroupingParentOS:
                table.mergeCells(0, 0, 2, 1)
                table.mergeCells(0, 1, 2, 1)
                if isNomeclature:
                    table.mergeCells(0, 2, 2, 1)
                    table.mergeCells(0, 3, 2, 1)
                    table.mergeCells(0, 4, 1, 2)
                    table.mergeCells(0, 6, 1, 2)
                    table.mergeCells(0, 8, 1, 2)
                    table.mergeCells(0, 10, 1, 2)
                    table.mergeCells(0, 12, 1, 2)
                    table.mergeCells(0, 14, 1, 2)
                    table.mergeCells(0, 16, 1, 2)
                elif showFlatCode:
                    table.mergeCells(0, 2, 2, 1)
                    table.mergeCells(0, 3, 2, 1)
                    table.mergeCells(0, 4, 1, 2)
                    table.mergeCells(0, 6, 1, 2)
                    table.mergeCells(0, 8, 1, 2)
                    table.mergeCells(0, 10, 1, 2)
                    table.mergeCells(0, 12, 1, 2)
                    table.mergeCells(0, 14, 1, 2)
                    table.mergeCells(0, 16, 1, 2)
                else:
                    table.mergeCells(0, 2, 2, 1)
                    table.mergeCells(0, 3, 1, 2)
                    table.mergeCells(0, 5, 1, 2)
                    table.mergeCells(0, 7, 1, 2)
                    table.mergeCells(0, 9, 1, 2)
                    table.mergeCells(0, 11, 1, 2)
                    table.mergeCells(0, 13, 1, 2)
                    table.mergeCells(0, 15, 1, 2)
            else:
                table.mergeCells(0, 0, 2, 1)
                if isNomeclature:
                    table.mergeCells(0, 1, 2, 1)
                    table.mergeCells(0, 2, 2, 1)
                    table.mergeCells(0, 3, 1, 2)
                    table.mergeCells(0, 5, 1, 2)
                    table.mergeCells(0, 7, 1, 2)
                    table.mergeCells(0, 9, 1, 2)
                    table.mergeCells(0, 11, 1, 2)
                    table.mergeCells(0, 13, 1, 2)
                    table.mergeCells(0, 15, 1, 2)
                elif showFlatCode:
                    table.mergeCells(0, 1, 2, 1)
                    table.mergeCells(0, 2, 2, 1)
                    table.mergeCells(0, 3, 1, 2)
                    table.mergeCells(0, 5, 1, 2)
                    table.mergeCells(0, 7, 1, 2)
                    table.mergeCells(0, 9, 1, 2)
                    table.mergeCells(0, 11, 1, 2)
                    table.mergeCells(0, 13, 1, 2)
                    table.mergeCells(0, 15, 1, 2)
                else:
                    table.mergeCells(0, 1, 2, 1)
                    table.mergeCells(0, 2, 1, 2)
                    table.mergeCells(0, 4, 1, 2)
                    table.mergeCells(0, 6, 1, 2)
                    table.mergeCells(0, 8, 1, 2)
                    table.mergeCells(0, 10, 1, 2)
                    table.mergeCells(0, 12, 1, 2)
                    table.mergeCells(0, 14, 1, 2)
            recordsOS = db.getRecordList('OrgStructure', 'id, name, parent_id', '', 'name')
            orgStructureNameList = {}
            for recordOS in recordsOS:
                osId = forceRef(recordOS.value('id'))
                parentId = forceRef(recordOS.value('parent_id'))
                osName = forceString(recordOS.value('name'))
                orgStructureNameList[osId] = (parentId, osName)
            mapCodesToRowIdx, reportDataTotalAll = self.getSurgery(orgStructureIdList, begDate, endDate, isNomeclature, eventTypeId, selectActionType, selectType, personId, financeId, profileList, showFlatCode, existFlatCode, isGroupingParentOS, orgStructureNameList)
            keysList = mapCodesToRowIdx.keys()
            keysList.sort()
            if isGroupingParentOS:
                parentI = 0
                for personParentOSId in keysList:
                    reportDataParent = mapCodesToRowIdx.get(personParentOSId, {})
                    osKeysList = reportDataParent.keys()
                    osKeysList.sort()
                    reportDataParentTotal = [0]*(16+(isNomeclature or showFlatCode))
                    reportDataParentTotal[0] = u''
                    if isNomeclature or showFlatCode:
                        reportDataParentTotal[1] = u''
                    reportDataParentTotal[1+(isNomeclature or showFlatCode)] = u'Итого'
                    captionParent = True
                    parentCnt = 0 #2 if isGroupingOS else 11
                    parentName = orgStructureNameList.get(personParentOSId, (None, u'не задано'))[1]
                    for personOSId in osKeysList:
                        reportDataLine = reportDataParent.get(personOSId, {})
                        mkbKeys = reportDataLine.keys()
                        mkbKeys.sort()
                        reportDataTotal = [0]*(16+(isNomeclature or showFlatCode))
                        reportDataTotal[0] = u''
                        if isNomeclature or showFlatCode:
                            reportDataTotal[1] = u''
                        reportDataTotal[1+(isNomeclature or showFlatCode)] = u'Итого'
                        caption = True
                        for mkbKey in mkbKeys:
                            reportLine = reportDataLine.get(mkbKey, [])
                            if reportLine:
                                i = table.addRow()
                                parentCnt += 1
                                if captionParent:
                                    table.setText(i, 0, parentName)
                                    captionParent = False
                                    parentI = i
                                if caption:
                                    table.setText(i, 1, forceString(reportLine[0]))
                                    caption = False
                                    oldI = i
                                for col, val in enumerate(reportLine):
                                    if col != 0:
                                        table.setText(i, col+1, forceString(val))
                                    if col > 1+(isNomeclature or showFlatCode):
                                        reportDataTotal[col] += val
                                        reportDataParentTotal[col] += val
                        if isGroupingOS:
                            i = table.addRow()
                            for col, val in enumerate(reportDataTotal):
                                table.setText(i, col+1, forceString(val))
                            table.mergeCells(oldI, 1, len(mkbKeys)+1, 1)
                            parentCnt += 1
                        else:
                            table.mergeCells(oldI, 1, len(mkbKeys), 1)
                    if parentI:
                        i = table.addRow()
                        for col, val in enumerate(reportDataParentTotal):
                            if col == (2 if isNomeclature or showFlatCode else 1):
                                table.setText(i, 1, forceString(val) + u' ' + parentName)
                            else:
                                table.setText(i, col+1, forceString(val))
                        table.mergeCells(parentI, 0, parentCnt, 1)
                i = table.addRow()
                for col, val in enumerate(reportDataTotalAll):
                    if col == 0:
                        table.setText(i, col, forceString(val))
                    else:
                        table.setText(i, col+1, forceString(val))
            else:
                for key in keysList:
                    reportDataLine = mapCodesToRowIdx.get(key, {})
                    mkbKeys = reportDataLine.keys()
                    mkbKeys.sort()
                    reportDataTotal = [0]*(16+(isNomeclature or showFlatCode))
                    reportDataTotal[0] = u''
                    if isNomeclature or showFlatCode:
                        reportDataTotal[1] = u''
                    reportDataTotal[1+(isNomeclature or showFlatCode)] = u'Итого'
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
                                if col > 1+(isNomeclature or showFlatCode):
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


    def getSurgery(self, orgStructureIdList, begDate, endDate, isNomeclature, eventTypeId, selectActionType, selectType, personId, financeId, profileList, showFlatCode, existFlatCode, isGroupingParentOS, orgStructureNameList):
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        tableClient = db.table('Client')
        tableRBService = db.table('rbService')
        tableEventType = db.table('EventType')
        tableContract = db.table('Contract')
        tablePerson = db.table('Person')
        tableOrgStructure = db.table('OrgStructure')
        table = tableActionType.innerJoin(tableAction, tableActionType['id'].eq(tableAction['actionType_id']))
        table = table.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
        table = table.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
        table = table.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
        eventIdDataList = {}
        records = []
        if selectActionType > 0:
            flatCode = ['received%', 'moving%', 'leaved%', 'leaved%'][selectActionType-1]
            nameProperty = [u'Направлен в отделение', u'Отделение пребывания', u'Отделение', u'Отделение'][selectActionType-1]
            cond = [tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode(flatCode)),
                          tableEvent['deleted'].eq(0),
                          tableAction['deleted'].eq(0),
                          tableActionType['deleted'].eq(0),
                          tableClient['deleted'].eq(0),
                          tableEventType['deleted'].eq(0),
                          tableAction['endDate'].isNotNull()
                        ]
            if existFlatCode:
                cond.append(tableActionType['flatCode'].ne(u''))
            if bool(begDate):
                cond.append(tableAction['endDate'].ge(begDate))
            if bool(endDate):
                cond.append(tableAction['endDate'].lt(endDate.addDays(1)))
            if orgStructureIdList:
                cond.append(getDataOrgStructure(nameProperty, orgStructureIdList, stationaryOnly = False))
            if selectActionType in [3, 4] and profileList:
                cond.append(getPropertyAPHBP(profileList, False))
#            if profileList:
#                if selectActionType == 3:
#                    cond.append(getPropertyAPHBP(profileList, False))
#                else:
#                    cond.append(getPropertyAPHBPForActionType(getActionTypeIdListByFlatCode('leaved%'), profileList, False))
            if selectActionType == 2:
                eventRecords = db.getRecordList(table, 'Event.id AS eventId, Action.begDate, Action.endDate', cond)
                for eventRecord in eventRecords:
                    eventId = forceRef(eventRecord.value('eventId'))
                    dateList = eventIdDataList.get(eventId, [])
                    begDateA = forceDate(eventRecord.value('begDate'))
                    endDateA = forceDate(eventRecord.value('endDate'))
                    if (begDateA, endDateA) not in dateList:
                        dateList.append((begDateA, endDateA))
                    eventIdDataList[eventId] = dateList
                eventIdList = eventIdDataList.keys()
            else:
                eventIdList = db.getDistinctIdList(table, 'Event.id', cond)
                idList = set([])
                if selectActionType == 1:
                    for eventId in eventIdList:
                        idListDescendant = set(db.getDescendants(tableEvent, 'prevEvent_id', eventId))
                        idList |= idListDescendant
                elif selectActionType == 3:
                    idListParents = set(db.getTheseAndParents(tableEvent, 'prevEvent_id', eventIdList))
                    idList |= idListParents
                setEventIdList = set(eventIdList)
                setEventIdList |= idList
                eventIdList = list(setEventIdList)
            if eventIdList:
                order = u'ActionType.group_id, %s'%(u'ActionType.code' if not isNomeclature else u'ActionType.flatCode')
                cols = [tableAction['id'].alias('actionId'),
                        tableAction['amount'].alias('countSurgery'),
                        tableEvent['order'],
                        tableEvent['setDate'],
                        tableEvent['execDate'],
                        tableAction['event_id'],
                        tableAction['person_id'],
                        tableAction['begDate'],
                        tableAction['endDate'],
                        tableAction['MKB'],
                        tableActionType['id'].alias('actionTypeId'),
                        tableActionType['group_id'].alias('groupId'),
                        tablePerson['id'].alias('personId'),
                        tablePerson['orgStructure_id'].alias('personOSId'),
                        tableActionType['code'] if not isNomeclature else tableActionType['flatCode'].alias('code'),
                        tableActionType['name'],
                        tableClient['id'].alias('clientId'),
                        tableActionType['code'].alias('actionTypeCode'),
                        tableActionType['flatCode'].alias('actionTypeFlatCode'),
                        tableActionType['serviceType']
                        ]
                if isGroupingParentOS:
                    cols.append(tableOrgStructure['parent_id'].alias('personParentOSId'))
                cols.append(u'%s AS countDeathHospital'%(getStringProperty(u'Исход операции', u'(APS.value LIKE \'умер%\' OR APS.value LIKE \'смерть%\')')))
                cols.append(u'%s AS countComplication'%(getStringProperty(u'Осложнени%', u'(APS.value != \'\' OR APS.value != \' \')')))
                cols.append(u'%s AS orderSurgery'%(getStringProperty(u'Порядок', u'''(APS.value LIKE '%s')'''%(u'%%плановый%%'))))
                table = tableAction.innerJoin(tableActionType, tableAction['actionType_id'].eq(tableActionType['id']))
                table = table.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
                table = table.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
                cond = [tableAction['event_id'].inlist(eventIdList),
                        tableEvent['deleted'].eq(0),
                        tableAction['deleted'].eq(0),
                        tableActionType['deleted'].eq(0),
                        tableClient['deleted'].eq(0),
                        tableAction['endDate'].isNotNull()
                        ]
                if existFlatCode:
                    cond.append(tableActionType['flatCode'].ne(u''))
                if selectActionType == 4:
                    tableEvent_P = db.table('Event').alias('Event_P')
                    tableAction_P = db.table('Action').alias('Action_P')
                    tableActionType_P = db.table('ActionType').alias('ActionType_P')
                    tableRBService_P = db.table('rbService').alias('rbService_P')
                    tableContract_P = db.table('Contract').alias('Contract_P')
                    tablePerson_P = db.table('Person').alias('Person_P')
                    cols_P = [  tableAction_P['id'].alias('actionId_P'),
                                tableAction_P['amount'].alias('countSurgery_P'),
                                tableEvent_P['order'].alias('order_P'),
                                tableEvent_P['setDate'].alias('setDate_P'),
                                tableEvent_P['execDate'].alias('execDate_P'),
                                tableAction_P['event_id'].alias('event_id_P'),
                                tableAction_P['person_id'].alias('person_id_P'),
                                tableAction_P['begDate'].alias('begDate_P'),
                                tableAction_P['endDate'].alias('endDate_P'),
                                tableAction_P['MKB'].alias('MKB_P'),
                                tableActionType_P['id'].alias('actionTypeId_P'),
                                tableActionType_P['group_id'].alias('groupId_P'),
                                tablePerson_P['id'].alias('personId_P'),
                                tablePerson['orgStructure_id'].alias('personOSId_P') if selectType else tablePerson_P['orgStructure_id'].alias('personOSId_P'),
                                tableActionType_P['code'].alias('code_P') if not isNomeclature else tableActionType_P['flatCode'].alias('code_P'),
                                tableActionType_P['name'].alias('name_P'),
                                tableEvent_P['client_id'].alias('clientId_P'),
                                tableActionType_P['code'].alias('actionTypeCode_P'),
                                tableActionType_P['serviceType'].alias('serviceType_P')
                            ]
                    if isGroupingParentOS:
                        cols.append(tableOrgStructure['parent_id'].alias('personParentOSId_P'))
                    cols_P.append(u'%s AS countDeathHospital_P'%(getStringPropertyForTableName(u'Action_P', u'Исход операции', u'(APS.value LIKE \'умер%\' OR APS.value LIKE \'смерть%\')')))
                    cols_P.append(u'%s AS countComplication_P'%(getStringPropertyForTableName(u'Action_P', u'Осложнени%', u'(APS.value != \'\' OR APS.value != \' \')')))
                    cols_P.append(u'%s AS orderSurgery_P'%(getStringPropertyForTableName(u'Action_P', u'Порядок', u'''(APS.value LIKE '%s')'''%(u'%%плановый%%'))))
                    tableA_F = db.table('Action').alias('A_F')
                    tableE_F = db.table('Event').alias('E_F')
                    condA_F = [u'E_F.id = getFirstEventId(Event.id)',
                               tableA_F['deleted'].eq(0),
                               tableE_F['deleted'].eq(0),
                               tableA_F['actionType_id'].inlist(getActionTypeIdListByFlatCode('received%'))
                               ]
                    stmtJOINA = db.selectStmt(u'''Event AS E_F INNER JOIN Action AS A_F ON A_F.event_id = E_F.id''', u'A_F.begDate', condA_F)
                    tableA_E = db.table('Action').alias('A_E')
                    tableAT_E = db.table('ActionType').alias('AT_E')
                    condA_E = [tableA_E['deleted'].eq(0),
                               tableA_E['event_id'].eq(tableEvent_P['id']),
                               tableA_E['endDate'].isNotNull(),
                               tableAT_E['deleted'].eq(0),
                               tableA_E['endDate'].lt(tableAction['endDate'].addDays(1)),
                               u'DATE(A_E.begDate) >= DATE(('+unicode(stmtJOINA)+u'))'
                               ]
                    tableAE = tableA_E.innerJoin(tableAT_E, tableAT_E['id'].eq(tableA_E['actionType_id']))
                    condA_E.append(tableAT_E['serviceType'].eq(CActionServiceType.operation))
                    if personId:
                        condA_E.append(tableA_E['person_id'].eq(personId))
                    if not isNomeclature:
                        tableRB_A = db.table('rbService').alias('RB_A')
                        condRBSA = [tableRB_A['id'].eq(tableAT_E['nomenclativeService_id'])]
                        tableAE = tableAE.innerJoin(tableRB_A, db.joinAnd(condRBSA))
                    table = table.leftJoin(tableEvent_P, db.joinAnd([tableEvent_P['id'].notInlist(eventIdList),
                                                                     tableEvent_P['client_id'].eq(tableClient['id']),
                                                                     tableEvent_P['deleted'].eq(0),
                                                                     tableEvent_P['id'].ne(tableEvent['id']),
                                                                     db.existsStmt(tableAE, condA_E)
                                                                     ]))
                    condJOINAction = [tableAction_P['event_id'].notInlist(eventIdList),
                                      tableAction_P['event_id'].eq(tableEvent_P['id']),
                                      tableAction_P['event_id'].ne(tableEvent['id']),
                                      tableAction_P['endDate'].isNotNull(),
                                      tableAction_P['deleted'].eq(0),
                                      tableEvent_P['deleted'].eq(0),
                                      tableAction_P['endDate'].lt(tableAction['endDate'].addDays(1)),
                                      u'DATE(Action_P.begDate) >= DATE(('+unicode(stmtJOINA)+u'))'
                                      ]
                    if personId:
                        condJOINAction.append(tableAction_P['person_id'].eq(personId))
                    table = table.leftJoin(tableAction_P, db.joinAnd(condJOINAction))
                    condJOINAT = [tableAction_P['actionType_id'].eq(tableActionType_P['id']),
                                  tableActionType_P['deleted'].eq(0)
                                  ]
                    condJOINAT.append(tableActionType_P['serviceType'].eq(CActionServiceType.operation))
                    table = table.leftJoin(tableActionType_P, db.joinAnd(condJOINAT))
                    cond.append(tableActionType_P['serviceType'].eq(CActionServiceType.operation))
                    if not isNomeclature:
                        condRBS = [tableRBService_P['id'].eq(tableActionType_P['nomenclativeService_id'])]
                        table = table.leftJoin(tableRBService_P, db.joinAnd(condRBS))
                    condJOINP = [tablePerson_P['deleted'].eq(0)]
                    if orgStructureIdList:
                        if selectType:
                            cond.append(db.joinOr([db.joinAnd([tablePerson['deleted'].eq(0), tablePerson['orgStructure_id'].inlist(orgStructureIdList)]), tablePerson_P['deleted'].eq(0)]))
                        else:
                            condJOINP.append(tablePerson_P['orgStructure_id'].inlist(orgStructureIdList))
                            cond.append(db.joinOr([db.joinAnd([tablePerson['deleted'].eq(0), tablePerson['orgStructure_id'].inlist(orgStructureIdList)]), db.joinAnd([tablePerson_P['deleted'].eq(0), tablePerson_P['orgStructure_id'].inlist(orgStructureIdList)])]))
                    if personId:
                        condJOINP.append(tablePerson_P['id'].eq(personId))
                        cond.append(db.joinOr([db.joinAnd([tablePerson['deleted'].eq(0), tablePerson['id'].eq(personId)]), db.joinAnd([tablePerson_P['deleted'].eq(0), tablePerson_P['id'].eq(personId)])]))
                    if selectType:
                        condJOINP.append(tableEvent_P['execPerson_id'].eq(tablePerson_P['id']))
                    else:
                        condJOINP.append(tableAction_P['person_id'].eq(tablePerson_P['id']))
                    table = table.leftJoin(tablePerson_P, db.joinAnd(condJOINP))
                    if financeId:
                        condJOINC = [tableContract_P['id'].eq(tableEvent_P['contract_id']),
                                     u'''((Action_P.finance_id IS NOT NULL AND Action_P.deleted=0 AND Action_P.finance_id = %s)
                                          OR (Contract_P.id IS NOT NULL AND Contract_P.deleted=0 AND Contract_P.finance_id = %s))'''%(str(financeId), str(financeId))
                                    ]
                        table = table.leftJoin(tableContract_P, db.joinAnd(condJOINC))
                    cols.extend(cols_P)
                    order += u', ActionType_P.group_id, %s'%(u'ActionType_P.code' if not isNomeclature else u'ActionType_P.flatCode')
                if eventTypeId:
                    cond.append(tableEvent['eventType_id'].eq(eventTypeId))
                if selectType:
                    table = table.innerJoin(tablePerson, tableEvent['execPerson_id'].eq(tablePerson['id']))
                    if personId:
                        cond.append(tablePerson['deleted'].eq(0))
                        cond.append(tablePerson['id'].eq(personId))
                    if isGroupingParentOS:
                        table = table.leftJoin(tableOrgStructure, db.joinAnd([tableOrgStructure['id'].eq(tablePerson['orgStructure_id']), tableOrgStructure['deleted'].eq(0)]))
                else:
                    condJIONPST = [tableAction['person_id'].eq(tablePerson['id'])]
                    if selectActionType == 4:
                        if personId:
                            condJIONPST.append(tablePerson['deleted'].eq(0))
                            condJIONPST.append(tablePerson['id'].eq(personId))
                        if isGroupingParentOS:
                            table = table.leftJoin(tableOrgStructure, db.joinAnd([tableOrgStructure['id'].eq(tablePerson_P['orgStructure_id']), tableOrgStructure['deleted'].eq(0)]))
                    else:
                        if personId:
                            cond.append(tablePerson['deleted'].eq(0))
                            cond.append(tablePerson['id'].eq(personId))
                        if isGroupingParentOS:
                            table = table.leftJoin(tableOrgStructure, db.joinAnd([tableOrgStructure['id'].eq(tablePerson['orgStructure_id']), tableOrgStructure['deleted'].eq(0)]))
                    table = table.leftJoin(tablePerson, db.joinAnd(condJIONPST))
                if financeId:
                    if selectActionType == 4:
                        condJIONFInance = ['''((Action.finance_id IS NOT NULL AND Action.deleted=0 AND Action.finance_id = %s) OR (Contract.id IS NOT NULL AND Contract.deleted=0 AND Contract.finance_id = %s))'''%(str(financeId), str(financeId))]
                        table = table.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                        cond.append(db.joinOr([db.joinAnd(condJIONFInance), db.joinAnd(condJOINC)]))
                    else:
                        cond.append('''((Action.finance_id IS NOT NULL AND Action.deleted=0 AND Action.finance_id = %s) OR (Contract.id IS NOT NULL AND Contract.deleted=0 AND Contract.finance_id = %s))'''%(str(financeId), str(financeId)))
                        table = table.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                if orgStructureIdList and selectActionType != 4:
                    cond.append(tablePerson['deleted'].eq(0))
                    cond.append(tablePerson['orgStructure_id'].inlist(orgStructureIdList))
                if not isNomeclature:
                    table = table.innerJoin(tableRBService, tableRBService['id'].eq(tableActionType['nomenclativeService_id']))
                if existFlatCode:
                    cond.append(tableActionType['flatCode'].ne(u''))
                if selectActionType == 4:
                    cond.append(db.joinOr([tableActionType['serviceType'].eq(CActionServiceType.operation), tableActionType['id'].inlist(getActionTypeIdListByFlatCode('leaved%'))]))
                else:
                    cond.append(tableActionType['serviceType'].eq(CActionServiceType.operation))
                records = db.getRecordList(table, cols, cond, order)
        else:
            cond = [tableEvent['deleted'].eq(0),
                    tableEventType['deleted'].eq(0),
                    tableAction['deleted'].eq(0),
                    tableActionType['deleted'].eq(0),
                    tableClient['deleted'].eq(0),
                    tableAction['endDate'].isNotNull()
                    ]
            if existFlatCode:
                cond.append(tableActionType['flatCode'].ne(u''))
            if bool(begDate):
                cond.append(tableAction['endDate'].ge(begDate))
            if bool(endDate):
                cond.append(tableAction['endDate'].lt(endDate.addDays(1)))
            cols = [tableAction['id'].alias('actionId'),
                    tableAction['amount'].alias('countSurgery'),
                    tableEvent['order'],
                    tableEvent['setDate'],
                    tableEvent['execDate'],
                    tableAction['event_id'],
                    tableAction['person_id'],
                    tableAction['begDate'],
                    tableAction['endDate'],
                    tableAction['MKB'],
                    tableActionType['id'].alias('actionTypeId'),
                    tableActionType['group_id'].alias('groupId'),
                    tablePerson['id'].alias('personId'),
                    tablePerson['orgStructure_id'].alias('personOSId'),
                    tableActionType['code'] if not isNomeclature else tableActionType['flatCode'].alias('code'),
                    tableActionType['name'],
                    tableClient['id'].alias('clientId'),
                    tableActionType['code'].alias('actionTypeCode'),
                    tableActionType['flatCode'].alias('actionTypeFlatCode'),
                    tableActionType['serviceType']
                    ]
            if isGroupingParentOS:
                cols.append(tableOrgStructure['parent_id'].alias('personParentOSId'))
#            if profileList:
#                cond.append(getPropertyAPHBPForActionType(getActionTypeIdListByFlatCode('leaved%'), profileList, False))
            cols.append(u'%s AS countDeathHospital'%(getStringProperty(u'Исход операции', u'(APS.value LIKE \'умер%\' OR APS.value LIKE \'смерть%\')')))
            cols.append(u'%s AS countComplication'%(getStringProperty(u'Осложнени%', u'(APS.value != \'\' OR APS.value != \' \')')))
            cols.append(u'%s AS orderSurgery'%(getStringProperty(u'Порядок', u'''(APS.value LIKE '%s')'''%(u'%%плановый%%'))))
            table = tableAction.innerJoin(tableActionType, tableAction['actionType_id'].eq(tableActionType['id']))
            table = table.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
            table = table.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
            table = table.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
            if eventTypeId:
                cond.append(tableEvent['eventType_id'].eq(eventTypeId))
            cond.append(tableActionType['serviceType'].eq(CActionServiceType.operation))
            if not isNomeclature:
                table = table.innerJoin(tableRBService, tableRBService['id'].eq(tableActionType['nomenclativeService_id']))
            if existFlatCode:
                    cond.append(tableActionType['flatCode'].ne(u''))
            if selectType:
                table = table.innerJoin(tablePerson, tableEvent['execPerson_id'].eq(tablePerson['id']))
            else:
                table = table.leftJoin(tablePerson, tableAction['person_id'].eq(tablePerson['id']))
            if personId:
                cond.append(tablePerson['deleted'].eq(0))
                cond.append(tablePerson['id'].eq(personId))
            if financeId:
                cond.append('''((Action.finance_id IS NOT NULL AND Action.deleted=0 AND Action.finance_id = %s) OR (Contract.id IS NOT NULL AND Contract.deleted=0 AND Contract.finance_id = %s))'''%(str(financeId), str(financeId)))
                table = table.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
            if orgStructureIdList:
                cond.append(tablePerson['deleted'].eq(0))
                cond.append(tablePerson['orgStructure_id'].inlist(orgStructureIdList))
            if isGroupingParentOS:
                table = table.leftJoin(tableOrgStructure, db.joinAnd([tableOrgStructure['id'].eq(tablePerson['orgStructure_id']), tableOrgStructure['deleted'].eq(0)]))
            records = db.getRecordList(table, cols, cond, u'ActionType.group_id, %s'%(u'ActionType.code' if not isNomeclature else u'ActionType.flatCode'))
        reportDataParentTotal = {}
        reportDataTotal = {}
        reportDataTotalAll = [0]*(16+(isNomeclature or showFlatCode))
        reportDataTotalAll[0] = u'Итого'
        if isNomeclature or showFlatCode:
            reportDataTotalAll[1] = u''
        reportDataTotalAll[1+(isNomeclature or showFlatCode)] = u''
        clientIdList = []
        actionIdList = []
        for record in records:
            begDate = forceDate(record.value('begDate'))
            endDate = forceDate(record.value('endDate'))
            eventId = forceRef(record.value('event_id'))
            actionId = forceRef(record.value('actionId'))
            serviceType = forceInt(record.value('serviceType'))
            if actionId and actionId not in actionIdList and serviceType == CActionServiceType.operation:
                actionIdList.append(actionId)
                iterationNext = True
                if selectActionType == 2:
                    actionDateList = eventIdDataList.get(eventId, [])
                    for actionDate in actionDateList:
                        actionBegDate = actionDate[0]
                        actionEndDate = actionDate[1]
                        if endDate > actionBegDate and begDate < actionEndDate:
                            iterationNext = True
                        elif endDate == begDate and (endDate >= actionBegDate and begDate <= actionEndDate):
                            iterationNext = True
                        else:
                            iterationNext = False
                if iterationNext:
                    countSurgery = forceInt(record.value('countSurgery'))
                    orderSurgery = forceBool(record.value('orderSurgery'))
                    personId = forceInt(record.value('personId'))
                    personOSId = forceRef(record.value('personOSId'))
                    personParentOSId = forceRef(record.value('personParentOSId'))
                    countDeathHospital = forceInt(record.value('countDeathHospital'))
                    countComplication = forceInt(record.value('countComplication'))
                    clientId = forceRef(record.value('clientId'))
                    actionTypeId = forceRef(record.value('actionTypeId'))
                    name = forceString(record.value('name'))
                    endDateEvent = forceDate(record.value('execDate'))
                    begDateEvent = forceDate(record.value('setDate'))
                    bedDaysAll = 0
                    if begDateEvent and endDateEvent:
                        bedDaysAll = begDateEvent.daysTo(endDateEvent) if begDateEvent != endDateEvent else 1
                    bedDaysFrom = 0
                    if begDateEvent and begDate:
                        bedDaysFrom = begDateEvent.daysTo(begDate)# if begDateEvent != begDate else 1
                    bedDaysTo = 0
                    if endDate and endDateEvent:
                        bedDaysTo = endDate.daysTo(endDateEvent)# if endDate != endDateEvent else 1
                    if isGroupingParentOS:
                        reportDataTotal = reportDataParentTotal.get(personParentOSId, {})
                    reportData = reportDataTotal.get(personOSId, {})
                    reportLine = reportData.get(actionTypeId, [0]*(16+(isNomeclature or showFlatCode)))
                    reportLine[0] = orgStructureNameList.get(personOSId, (None, u'не определено'))[1]
                    if showFlatCode:
                        reportLine[1] = QString(forceString(record.value('actionTypeCode')) + u"/" + forceString(record.value('actionTypeFlatCode')))
                    else:
                        if isNomeclature:
                            reportLine[1] = QString(forceString(record.value('actionTypeCode')))
                    reportLine[1+(isNomeclature or showFlatCode)] = name
                    if clientId and eventId and (clientId, eventId) not in clientIdList:
                        reportLine[2+(isNomeclature or showFlatCode)] += 1
                        reportDataTotalAll[2+(isNomeclature or showFlatCode)] += 1
                        if orderSurgery:
                            reportLine[3+(isNomeclature or showFlatCode)] += 1
                            reportDataTotalAll[3+(isNomeclature or showFlatCode)] += 1
                        clientIdList.append((clientId, eventId))
                    reportLine[4+(isNomeclature or showFlatCode)] += countSurgery
                    reportDataTotalAll[4+(isNomeclature or showFlatCode)] += countSurgery
                    if orderSurgery:
                        reportLine[5+(isNomeclature or showFlatCode)] += countSurgery
                        reportDataTotalAll[5+(isNomeclature or showFlatCode)] += countSurgery
                        if countComplication:
                            reportLine[7+(isNomeclature or showFlatCode)] += countSurgery
                            reportDataTotalAll[7+(isNomeclature or showFlatCode)] += countSurgery
                        if countDeathHospital:
                            reportLine[9+(isNomeclature or showFlatCode)] += 1
                            reportDataTotalAll[9+(isNomeclature or showFlatCode)] += 1
                        reportLine[11+(isNomeclature or showFlatCode)] += bedDaysFrom
                        reportDataTotalAll[11+(isNomeclature or showFlatCode)] += bedDaysFrom
                        reportLine[13+(isNomeclature or showFlatCode)] += bedDaysTo
                        reportDataTotalAll[13+(isNomeclature or showFlatCode)] += bedDaysTo
                        reportLine[15+(isNomeclature or showFlatCode)] += bedDaysAll
                        reportDataTotalAll[15+(isNomeclature or showFlatCode)] += bedDaysAll
                    if countComplication:
                        reportLine[6+(isNomeclature or showFlatCode)] += countSurgery
                        reportDataTotalAll[6+(isNomeclature or showFlatCode)] += countSurgery
                    if countDeathHospital:
                        reportLine[8+(isNomeclature or showFlatCode)] += 1
                        reportDataTotalAll[8+(isNomeclature or showFlatCode)] += 1
                    reportLine[10+(isNomeclature or showFlatCode)] += bedDaysFrom
                    reportDataTotalAll[10+(isNomeclature or showFlatCode)] += bedDaysFrom
                    reportLine[12+(isNomeclature or showFlatCode)] += bedDaysTo
                    reportDataTotalAll[12+(isNomeclature or showFlatCode)] += bedDaysTo
                    reportLine[14+(isNomeclature or showFlatCode)] += bedDaysAll
                    reportDataTotalAll[14+(isNomeclature or showFlatCode)] += bedDaysAll
                    reportData[actionTypeId] = reportLine
                    reportDataTotal[personOSId] = reportData
                    if isGroupingParentOS:
                        reportDataParentTotal[personParentOSId] = reportDataTotal
            if selectActionType == 4:
                begDate = forceDate(record.value('begDate_P'))
                endDate = forceDate(record.value('endDate_P'))
                eventId = forceRef(record.value('event_id_P'))
                actionId = forceRef(record.value('actionId_P'))
                serviceType = forceInt(record.value('serviceType_P'))
                if actionId and actionId not in actionIdList and serviceType == CActionServiceType.operation:
                    actionIdList.append(actionId)
                    iterationNext = True
                    if selectActionType == 2:
                        actionDateList = eventIdDataList.get(eventId, [])
                        for actionDate in actionDateList:
                            actionBegDate = actionDate[0]
                            actionEndDate = actionDate[1]
                            if endDate > actionBegDate and begDate < actionEndDate:
                                iterationNext = True
                            elif endDate == begDate and (endDate >= actionBegDate and begDate <= actionEndDate):
                                iterationNext = True
                            else:
                                iterationNext = False
                    if iterationNext:
                        countSurgery = forceInt(record.value('countSurgery_P'))
                        orderSurgery = forceBool(record.value('orderSurgery_P'))
                        personId = forceInt(record.value('personId_P'))
                        personOSId = forceRef(record.value('personOSId_P'))
                        personParentOSId = forceRef(record.value('personParentOSId_P'))
                        countDeathHospital = forceInt(record.value('countDeathHospital_P'))
                        countComplication = forceInt(record.value('countComplication_P'))
                        clientId = forceRef(record.value('clientId_P'))
                        actionTypeId = forceRef(record.value('actionTypeId_P'))
                        name = forceString(record.value('name_P'))
                        endDateEvent = forceDate(record.value('execDate_P'))
                        begDateEvent = forceDate(record.value('setDate_P'))
                        bedDaysAll = 0
                        if begDateEvent and endDateEvent:
                            bedDaysAll = begDateEvent.daysTo(endDateEvent) if begDateEvent != endDateEvent else 1
                        bedDaysFrom = 0
                        if begDateEvent and begDate:
                            bedDaysFrom = begDateEvent.daysTo(begDate)# if begDateEvent != begDate else 1
                        bedDaysTo = 0
                        if endDate and endDateEvent:
                            bedDaysTo = endDate.daysTo(endDateEvent)# if endDate != endDateEvent else 1
                        if isGroupingParentOS:
                            reportDataTotal = reportDataParentTotal.get(personParentOSId, {})
                        reportData = reportDataTotal.get(personOSId, {})
                        reportLine = reportData.get(actionTypeId, [0]*(16+(isNomeclature or showFlatCode)))
                        reportLine[0] = orgStructureNameList.get(personOSId, (None, u'не определено'))[1]
                        if showFlatCode:
                            reportLine[1] = QString(forceString(record.value('actionTypeCode_P')) + u"/" + forceString(record.value('code_P')))
                        else:
                            if isNomeclature:
                                reportLine[1] = QString(forceString(record.value('actionTypeCode_P')))
                        reportLine[1+(isNomeclature or showFlatCode)] = name
                        if clientId and eventId and (clientId, eventId) not in clientIdList:
                            reportLine[2+(isNomeclature or showFlatCode)] += 1
                            reportDataTotalAll[2+(isNomeclature or showFlatCode)] += 1
                            if orderSurgery:
                                reportLine[3+(isNomeclature or showFlatCode)] += 1
                                reportDataTotalAll[3+(isNomeclature or showFlatCode)] += 1
                            clientIdList.append((clientId, eventId))
                        reportLine[4+(isNomeclature or showFlatCode)] += countSurgery
                        reportDataTotalAll[4+(isNomeclature or showFlatCode)] += countSurgery
                        if orderSurgery:
                            reportLine[5+(isNomeclature or showFlatCode)] += countSurgery
                            reportDataTotalAll[5+(isNomeclature or showFlatCode)] += countSurgery
                            if countComplication:
                                reportLine[7+(isNomeclature or showFlatCode)] += countSurgery
                                reportDataTotalAll[7+(isNomeclature or showFlatCode)] += countSurgery
                            if countDeathHospital:
                                reportLine[9+(isNomeclature or showFlatCode)] += 1
                                reportDataTotalAll[9+(isNomeclature or showFlatCode)] += 1
                            reportLine[11+(isNomeclature or showFlatCode)] += bedDaysFrom
                            reportDataTotalAll[11+(isNomeclature or showFlatCode)] += bedDaysFrom
                            reportLine[13+(isNomeclature or showFlatCode)] += bedDaysTo
                            reportDataTotalAll[13+(isNomeclature or showFlatCode)] += bedDaysTo
                            reportLine[15+(isNomeclature or showFlatCode)] += bedDaysAll
                            reportDataTotalAll[15+(isNomeclature or showFlatCode)] += bedDaysAll
                        if countComplication:
                            reportLine[6+(isNomeclature or showFlatCode)] += countSurgery
                            reportDataTotalAll[6+(isNomeclature or showFlatCode)] += countSurgery
                        if countDeathHospital:
                            reportLine[8+(isNomeclature or showFlatCode)] += 1
                            reportDataTotalAll[8+(isNomeclature or showFlatCode)] += 1
                        reportLine[10+(isNomeclature or showFlatCode)] += bedDaysFrom
                        reportDataTotalAll[10+(isNomeclature or showFlatCode)] += bedDaysFrom
                        reportLine[12+(isNomeclature or showFlatCode)] += bedDaysTo
                        reportDataTotalAll[12+(isNomeclature or showFlatCode)] += bedDaysTo
                        reportLine[14+(isNomeclature or showFlatCode)] += bedDaysAll
                        reportDataTotalAll[14+(isNomeclature or showFlatCode)] += bedDaysAll
                        reportData[actionTypeId] = reportLine
                        reportDataTotal[personOSId] = reportData
                        if isGroupingParentOS:
                            reportDataParentTotal[personParentOSId] = reportDataTotal
        return reportDataParentTotal if isGroupingParentOS else reportDataTotal, reportDataTotalAll

