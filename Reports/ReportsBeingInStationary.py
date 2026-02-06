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
from PyQt4.QtCore       import pyqtSignature, QDate, QDateTime

from library.Utils            import forceDate, forceInt, forceRef, forceString, formatName

from Events.ActionServiceType import CActionServiceType
from Orgs.Utils               import getOrgStructureFullName
from Reports.Report           import CReport, normalizeMKB
from Reports.ReportBase       import CReportBase, createTable
from Reports.ReportsActionTypeListDialog import CReportsActionTypeListDialog
from Reports.Utils            import dateRangeAsStr, getActionsToFlatCode

from Reports.Ui_ReportsBeingInStationary import Ui_ReportsBeingInStationaryDialog


class CReportsBeingInStationaryDialog(QtGui.QDialog, Ui_ReportsBeingInStationaryDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())
        self.edtLimitDays.setMaximum(1000)
        self.actionTypeList = []


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.edtLimitDays.setValue(params.get('limitDays', 0))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        self.cmbSelectType.setCurrentIndex(params.get('selectType', 0))
        self.cmbPerson.setValue(params.get('personId', None))
        self.actionTypeList =  params.get('actionTypeList', [])
        if self.actionTypeList:
            db = QtGui.qApp.db
            tableAT = db.table('ActionType')
            records = db.getRecordList(tableAT, [tableAT['code']], [tableAT['deleted'].eq(0), tableAT['id'].inlist(self.actionTypeList)])
            nameList = []
            nameCount = 0
            for record in records:
                nameF = forceString(record.value('code'))
                nameCount += 1
                if nameCount == 10:
                    nameF += u'\n'
                    nameCount = 0
                nameList.append(nameF)
            self.lblActionTypeList.setText(u','.join(name for name in nameList if name))
        else:
            self.lblActionTypeList.setText(u'не задано')
        MKBFilter = params.get('MKBFilter', 0)
        self.cmbMKBFilter.setCurrentIndex(MKBFilter if MKBFilter else 0)
        self.edtMKBFrom.setText(params.get('MKBFrom', 'A00'))
        self.edtMKBTo.setText(params.get('MKBTo',   'Z99.9'))


    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['limitDays'] = self.edtLimitDays.value()
        result['orgStructureId'] = self.cmbOrgStructure.value()
        result['actionTypeList'] = self.actionTypeList
        result['selectType']     = self.cmbSelectType.currentIndex()
        result['personId']  = self.cmbPerson.value()
        result['MKBFilter'] = forceInt(self.cmbMKBFilter.currentIndex())
        result['MKBFrom']   = unicode(self.edtMKBFrom.text())
        result['MKBTo']     = unicode(self.edtMKBTo.text())
        return result


    @pyqtSignature('int')
    def on_cmbMKBFilter_currentIndexChanged(self, index):
        mode = bool(index)
        for widget in (self.edtMKBFrom, self.edtMKBTo):
            widget.setEnabled(mode)


    @pyqtSignature('')
    def on_btnActionTypeList_clicked(self):
        self.actionTypeList = []
        self.lblActionTypeList.setText(u'не задано')
        dialog = CReportsActionTypeListDialog(self, filter=u'ActionType.serviceType = %d' % CActionServiceType.operation)
        if dialog.exec_():
            self.actionTypeList = dialog.values()
            if self.actionTypeList:
                db = QtGui.qApp.db
                table = db.table('ActionType')
                records = db.getRecordList(table, [table['code']], [table['deleted'].eq(0), table['id'].inlist(self.actionTypeList)])
                nameList = []
                nameCount = 0
                for record in records:
                    nameF = forceString(record.value('code'))
                    nameCount += 1
                    if nameCount == 10:
                        nameF += u'\n'
                        nameCount = 0
                    nameList.append(nameF)
                self.lblActionTypeList.setText(u','.join(name for name in nameList if name))


class CReportsBeingInStationary(CReport):
    def __init__(self, parent = None):
        CReport.__init__(self, parent)
        self.setTitle(u'Отчет по количеству дней проведенных в стационаре.')


    def getSetupDialog(self, parent):
        result = CReportsBeingInStationaryDialog(parent)
        return result


    def dumpParams(self, cursor, params):
        description = []
        limitDays = params.get('limitDays', 0)
        description.append(u'Находился менее %s суток'%(limitDays))
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        if begDate and endDate:
            description.append(dateRangeAsStr(u'за период', begDate, endDate))
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
        MKBFilter = params.get('MKBFilter', 0)
        if MKBFilter:
            MKBFrom = params.get('MKBFrom', 'A00')
            MKBTo = params.get('MKBTo',   'Z99.9')
            description.append(u'коды диагнозов по МКБ с %s по %s'%(forceString(MKBFrom), forceString(MKBTo)))
        actionTypeList = params.get('actionTypeList', None)
        if actionTypeList:
            db = QtGui.qApp.db
            tableAT = db.table('ActionType')
            records = db.getRecordList(tableAT, [tableAT['code']], [tableAT['deleted'].eq(0), tableAT['id'].inlist(actionTypeList)])
            nameList = []
            for record in records:
                nameList.append(forceString(record.value('code')))
            description.append(u'тип события:  %s'%(u','.join(name for name in nameList if name)))
        else:
            description.append(u'тип события:  не задано')
        description.append(u'отчёт составлен: '+forceString(QDateTime.currentDateTime()))
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()


    def build(self, params):
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        doc = QtGui.QTextDocument()
        if (not begDate) or (not endDate):
            currentDate = QDate.currentDate()
            begDate = QDate(currentDate.year(), 1, 1)
            endDate = currentDate
        if begDate and endDate:
            reportMainData = []
            doc = QtGui.QTextDocument()
            cursor = QtGui.QTextCursor(doc)
            cursor.setCharFormat(CReportBase.ReportTitle)
            cursor.insertText(u'Отчет по количеству дней проведенных в стационаре.')
            cursor.insertBlock()
            self.dumpParams(cursor, params)
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertBlock()
            cols = [('25%', [u'ФИО пациента',      u'2'], CReportBase.AlignLeft),
                    ('10%', [u'ДР пациента',       u'3'], CReportBase.AlignLeft),
                    ('10%', [u'Диагноз',           u'4'], CReportBase.AlignLeft),
                    ('20%', [u'Отделение',         u'5'], CReportBase.AlignLeft),
                    ('15%', [u'Код операции',      u'6'], CReportBase.AlignLeft),
                    ('20%', [u'Название операции', u'7'], CReportBase.AlignLeft)
                   ]
            table = createTable(cursor, cols)
            reportMainData = self.getSurgery(reportMainData, params)
            for reportLine in reportMainData:
                i = table.addRow()
                for col, item in enumerate(reportLine):
                    table.setText(i, col, forceString(item))
        return doc


    def getSurgery(self, mapCodeToRowIdx, params):
        db = QtGui.qApp.db
        orgStructureId = params.get('orgStructureId', None)
        orgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', orgStructureId) if orgStructureId else []
        begDate        = params.get('begDate', QDate())
        endDate        = params.get('endDate', QDate())
        actionTypeList = params.get('actionTypeList', None)
        selectType     = params.get('selectType', 0)
        personId       = params.get('personId', None)
        MKBFilter      = params.get('MKBFilter', 0)
        MKBFrom        = params.get('MKBFrom', 'A00')
        MKBTo          = params.get('MKBTo',   'Z99.9')
        limitDays      = params.get('limitDays', 0)
        tableEvent            = db.table('Event')
        tableAction           = db.table('Action')
        tableActionType       = db.table('ActionType')
        tableClient           = db.table('Client')
        tableEventType        = db.table('EventType')
        tableRBMedicalAidType = db.table('rbMedicalAidType')
        tablePerson           = db.table('Person')
        tableDiagnosis        = db.table('Diagnosis')
        tableDiagnostic       = db.table('Diagnostic')
        tableDiagnosisType    = db.table('rbDiagnosisType')
        tableOrgStructure     = db.table('OrgStructure')
        cond = [tableEvent['deleted'].eq(0),
                tableEventType['deleted'].eq(0),
                tableAction['deleted'].eq(0),
                tableActionType['deleted'].eq(0),
                tableClient['deleted'].eq(0),
                tableAction['endDate'].isNotNull(),
                tableActionType['serviceType'].eq(CActionServiceType.operation),
                tableEvent['execDate'].isNotNull(),
                getActionsToFlatCode(u'moving%')
                ]
        table = tableAction.innerJoin(tableActionType, tableAction['actionType_id'].eq(tableActionType['id']))
        table = table.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
        table = table.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
        table = table.innerJoin(tableRBMedicalAidType, tableEventType['medicalAidType_id'].eq(tableRBMedicalAidType['id']))
        table = table.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
        cond.append(tableRBMedicalAidType['code'].inlist([1, 2, 3, 7]))
        if actionTypeList:
            cond.append(tableActionType['id'].inlist(actionTypeList))
        if bool(begDate):
            cond.append(tableEvent['execDate'].ge(begDate))
        if bool(endDate):
            cond.append(tableEvent['execDate'].lt(endDate.addDays(1)))
        if selectType:
            table = table.innerJoin(tablePerson, tableEvent['execPerson_id'].eq(tablePerson['id']))
        else:
            table = table.innerJoin(tablePerson, tableAction['person_id'].eq(tablePerson['id']))
        table = table.innerJoin(tableOrgStructure, tablePerson['orgStructure_id'].eq(tableOrgStructure['id']))
        if personId:
            cond.append(tablePerson['deleted'].eq(0))
            cond.append(tablePerson['id'].eq(personId))
        if orgStructureIdList:
            cond.append(tablePerson['deleted'].eq(0))
            cond.append(tablePerson['orgStructure_id'].inlist(orgStructureIdList))
        cond.append('''(rbDiagnosisType.code = '1'
OR (rbDiagnosisType.code = '2' AND Diagnostic.person_id = Event.execPerson_id
AND (NOT EXISTS (SELECT DC.id FROM Diagnostic AS DC
INNER JOIN rbDiagnosisType AS DT ON DT.id = DC.diagnosisType_id WHERE DT.code = '1'
AND DC.event_id = Event.id))))''')
        if MKBFilter:
            table = table.innerJoin(tableDiagnostic, tableEvent['id'].eq(tableDiagnostic['event_id']))
            table = table.innerJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
            table = table.innerJoin(tableDiagnosisType, tableDiagnosisType['id'].eq(tableDiagnostic['diagnosisType_id']))
            cond.append(tableDiagnostic['deleted'].eq(0))
            cond.append(tableDiagnosis['deleted'].eq(0))
            cond.append('Diagnosis.MKB >= \'%s\' AND Diagnosis.MKB <= \'%s\''%(MKBFrom, MKBTo))
        else:
            table = table.leftJoin(tableDiagnostic, tableEvent['id'].eq(tableDiagnostic['event_id']))
            table = table.leftJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
            table = table.leftJoin(tableDiagnosisType, tableDiagnosisType['id'].eq(tableDiagnostic['diagnosisType_id']))
            cond.append(db.joinOr([tableDiagnostic['id'].isNull(), tableDiagnostic['deleted'].eq(0)]))
            cond.append(db.joinOr([tableDiagnosis['id'].isNull(), tableDiagnosis['deleted'].eq(0)]))
        cols = [tableClient['id'].alias('clientId'),
                tableClient['lastName'],
                tableClient['firstName'],
                tableClient['patrName'],
                tableClient['birthDate'],
                tableDiagnosis['MKB'],
                tableAction['id'].alias('actionId'),
                tableAction['MKB'],
                tableActionType['code'],
                tableActionType['name'],
                tableOrgStructure['name'].alias('orgStructureName'),
                tableEvent['setDate'],
                tableEvent['execDate']
                ]
        actionIdList = []
        records = db.getRecordList(table, cols, cond, u'ActionType.group_id, ActionType.code')
        for record in records:
            actionId  = forceRef(record.value('actionId'))
            if actionId not in  actionIdList:
                setDate = forceDate(record.value('setDate'))
                execDate = forceDate(record.value('execDate'))
                eventDays = setDate.daysTo(execDate)
                if limitDays == 0 or eventDays <= limitDays:
                    actionIdList.append(actionId)
                    reportLine = []
                    lastName  = forceString(record.value('lastName'))
                    firstName = forceString(record.value('firstName'))
                    patrName  = forceString(record.value('patrName'))
                    reportLine.append(formatName(lastName, firstName, patrName))
                    reportLine.append(forceDate(record.value('birthDate')))
                    reportLine.append(normalizeMKB(forceString(record.value('MKB'))))
                    reportLine.append(forceString(record.value('orgStructureName')))
                    reportLine.append(forceString(record.value('code')))
                    reportLine.append(forceString(record.value('name')))
                    mapCodeToRowIdx.append(reportLine)
        return mapCodeToRowIdx
