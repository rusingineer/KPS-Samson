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

from library.Utils       import forceDate, forceString, getMKBInfo, isMKB

from Orgs.Utils          import getOrgStructureFullName
from Reports.Report      import CReport
from Reports.ReportBase  import CReportBase, createTable

from Reports.Ui_ReportLengthOfStayInHospital import Ui_ReportLengthOfStayInHospitalDialog


class CReportLengthOfStayInHospitalDialog(QtGui.QDialog, Ui_ReportLengthOfStayInHospitalDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbEventType.setTable('EventType', addNone=True)
        #self.cmbEventType.setTable('EventType', True, filter=getWorkEventTypeFilter(isApplyActive=True))
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        self.edtBegSetDate.setDate(         params.get('begSetDate',     QDate.currentDate()))
        self.edtEndSetDate.setDate(         params.get('endSetDate',     QDate.currentDate()))
        self.edtBegExecDate.setDate(        params.get('begExecDate',    QDate.currentDate()))
        self.edtEndExecDate.setDate(        params.get('endExecDate',    QDate.currentDate()))
        self.cmbOrgStructure.setValue(      params.get('orgStructureId', None))
        self.cmbPerson.setValue(            params.get('personId',       None))
        self.cmbEventStatus.setCurrentIndex(params.get('eventStatus',    0))
        self.cmbEventType.setValue(         params.get('eventTypeId',    None))
        self.cmbMKBFilter.setCurrentIndex(  params.get('MKBFilter',      0))
        self.edtMKBFrom.setText(            params.get('MKBFrom',        u'A00'))
        self.edtMKBTo.setText(              params.get('MKBTo',          u'Z99.9'))


    def params(self):
        params = {}
        params['begSetDate']         = self.edtBegSetDate.date()
        params['endSetDate']         = self.edtEndSetDate.date()
        params['begExecDate']        = self.edtBegExecDate.date()
        params['endExecDate']        = self.edtEndExecDate.date()
        params['orgStructureId']     = self.cmbOrgStructure.value()
        params['orgStructureIdList'] = self.getOrgStructureIdList()
        params['personId']           = self.cmbPerson.value()
        params['eventStatus']        = self.cmbEventStatus.currentIndex()
        params['eventTypeId']        = self.cmbEventType.value()
        params['MKBFilter']          = self.cmbMKBFilter.currentIndex()
        params['MKBFrom']            = unicode(self.edtMKBFrom.text())
        params['MKBTo']              = unicode(self.edtMKBTo.text())
        return params


    def getOrgStructureModel(self):
        return self.cmbOrgStructure.model()


    def getOrgStructureIdList(self):
        treeIndex = self.cmbOrgStructure._model.index(self.cmbOrgStructure.currentIndex(), 0, self.cmbOrgStructure.rootModelIndex())
        treeItem = treeIndex.internalPointer() if treeIndex.isValid() else None
        return treeItem.getItemIdList() if treeItem else []


    @pyqtSignature('int')
    def on_cmbEventStatus_currentIndexChanged(self, index):
        mode = bool(index!=2)
        for widget in (self.edtBegExecDate, self.edtEndExecDate):
            widget.setEnabled(mode)


    @pyqtSignature('int')
    def on_cmbMKBFilter_currentIndexChanged(self, index):
        mode = bool(index)
        for widget in (self.edtMKBFrom, self.edtMKBTo):
            widget.setEnabled(mode)


def selectData(params):
    begSetDate         = params.get('begSetDate', None)
    endSetDate         = params.get('endSetDate', None)
    begExecDate        = params.get('begExecDate', None)
    endExecDate        = params.get('endExecDate', None)
    orgStructureIdList = params.get('orgStructureIdList', None)
    personId           = params.get('personId', None)
    eventStatus        = params.get('eventStatus',  0)
    eventTypeId        = params.get('eventTypeId', None)
    MKBFilter          = params.get('MKBFilter', 0)
    MKBFrom            = params.get('MKBFrom', u'A00')
    MKBTo              = params.get('MKBTo',   u'Z99.9')

    db = QtGui.qApp.db
#    tableAction            = db.table('Action')
#    tableActionType        = db.table('ActionType')
    tableEvent             = db.table('Event')
    tableEventType         = db.table('EventType')
    tablePerson            = db.table('vrbPersonWithSpeciality')

#    queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
#    queryTable = queryTable.innerJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
#    queryTable = queryTable.innerJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
#    queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(tableAction['person_id']))

    queryTable = tableEvent.innerJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
    queryTable = queryTable.leftJoin(tablePerson, tablePerson['id'].eq(tableEvent['execPerson_id']))

    cond = [#tableAction['deleted'].eq(0),
            #tableActionType['deleted'].eq(0),
            tableEvent['deleted'].eq(0)
            ]
    if eventTypeId:
        cond.append(tableEventType['id'].eq(eventTypeId))
    if eventStatus == 1:
        cond.append(tableEvent['execDate'].isNotNull())
    if eventStatus == 2:
        cond.append(tableEvent['execDate'].isNull())
    else:
        if eventStatus == 1:
            cond.append(tableEvent['execDate'].isNotNull())
            if begExecDate:
                cond.append(tableEvent['execDate'].ge(begExecDate))
            if endExecDate:
                cond.append(tableEvent['execDate'].lt(endExecDate.addDays(1)))
        else:
            joinAnd1 = [tableEvent['execDate'].isNull()]
            joinAnd2 = [tableEvent['execDate'].isNotNull()]
            if endExecDate:
                joinAnd1.append(tableEvent['setDate'].lt(endExecDate.addDays(1)))
                joinAnd2.append(tableEvent['execDate'].lt(endExecDate.addDays(1)))
            if begExecDate:
                joinAnd2.append(tableEvent['execDate'].ge(begExecDate))
            cond.append(db.joinOr([db.joinAnd(joinAnd1),
                                   db.joinAnd(joinAnd2)]))
    if begSetDate:
        cond.append(tableEvent['setDate'].ge(begSetDate))
    if endSetDate:
        cond.append(tableEvent['setDate'].lt(endSetDate.addDays(1)))
    if orgStructureIdList:
        cond.append(tablePerson['orgStructure_id'].inlist(orgStructureIdList))
    if personId:
        cond.append(tablePerson['id'].eq(personId))
    if MKBFilter:
        cond.append(isMKB(MKBFrom, MKBTo))
    cols = [tableEvent['setDate'],
            tableEvent['execDate'],
            tableEvent['client_id'],
            getMKBInfo()
           ]
    cond.append(tableEventType['deleted'].eq(0))
    stmt = db.selectDistinctStmt(queryTable, cols, cond)
    query = db.query(stmt)
    return query


class CReportLengthOfStayInHospital(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Отчет по заболеванию и срокам пребывания в Стационаре')


    def getSetupDialog(self, parent):
        result = CReportLengthOfStayInHospitalDialog(parent)
        result.setTitle(self.title())
        return result


    def build(self, params):
        query = selectData(params)
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        tableColumns = [
                        ('8%',  [u'Код Диагноза'         ], CReportBase.AlignLeft),
                        ('10%', [u'Наименование диагноза'], CReportBase.AlignLeft),
                        ('10%', [u'Описание диагноза'    ], CReportBase.AlignLeft),
                        ('8%',  [u'Всего'                ], CReportBase.AlignRight),
                        ('8%',  [u'< 2 суток'            ], CReportBase.AlignRight),
                        ('8%',  [u'2-3 сутки'            ], CReportBase.AlignRight),
                        ('8%',  [u'4-5 сутки'            ], CReportBase.AlignRight),
                        ('8%',  [u'6-10 сутки'           ], CReportBase.AlignRight),
                        ('8%',  [u'11-20 сутки'          ], CReportBase.AlignRight),
                        ('8%',  [u'21-30 сутки'          ], CReportBase.AlignRight),
                        ('8%',  [u'31-40 сутки'          ], CReportBase.AlignRight),
                        ('8%',  [u'> 40 суток'           ], CReportBase.AlignRight)
                        ]
        table = createTable(cursor, tableColumns)
        reportData = {}
        reportSize = 12
        while query.next():
            record = query.record()
            MKBInfo  = forceString(record.value('MKBInfo'))
            setDate  = forceDate(record.value('setDate'))
            execDate = forceDate(record.value('execDate'))
            MKBInfoList = MKBInfo.split('  ')
            len_MKBInfoList = len(MKBInfoList)
            DiagID = u''
            DiagName = u''
            freeInput = u''
            if len_MKBInfoList >= 1:
                DiagID = MKBInfoList[0]
            if len_MKBInfoList >= 2:
                DiagName = MKBInfoList[1]
            if len_MKBInfoList >= 3:
                freeInput = MKBInfoList[2]
            reportLine = reportData.setdefault(DiagID, [0]*(reportSize-1))
            reportLine[0] = DiagName
            reportLine[1] = freeInput
            reportLine[2] += 1
            if setDate == execDate:
                days = 1
            else:
                days = execDate.daysTo(setDate)
            if days < 2:
                reportLine[3] += 1
            elif days >= 2 and days <= 3:
                reportLine[4] += 1
            elif days >= 4 and days <= 5:
                reportLine[5] += 1
            elif days >= 6 and days <= 10:
                reportLine[6] += 1
            elif days >= 11 and days <= 20:
                reportLine[7] += 1
            elif days >= 21 and days <= 30:
                reportLine[8] += 1
            elif days >= 31 and days <= 40:
                reportLine[9] += 1
            elif days > 40:
                reportLine[10] += 1
        mkbKeys = reportData.keys()
        mkbKeys.sort()
        for mkb in mkbKeys:
            reportLine = reportData.get(mkb, [0]*(reportSize-1))
            i = table.addRow()
            table.setText(i, 0, mkb)
            for col, val in enumerate(reportLine):
                table.setText(i, col+1, val)
        return doc


    def getDescription(self, params):
        db = QtGui.qApp.db
        begSetDate     = params.get('begSetDate', None)
        endSetDate     = params.get('endSetDate', None)
        begExecDate    = params.get('begExecDate', None)
        endExecDate    = params.get('endExecDate', None)
        orgStructureId = params.get('orgStructureId', None)
        personId       = params.get('personId', None)
        eventStatus    = params.get('eventStatus',  0)
        eventTypeId    = params.get('eventTypeId', None)
        MKBFilter      = params.get('MKBFilter', 0)
        rows = []
        rows.append(u'По дате начала события')
        if begSetDate:
            rows.append(u'Начальная дата периода: %s'%forceString(begSetDate))
        if endSetDate:
            rows.append(u'Конечная дата периода: %s'%forceString(endSetDate))
        rows.append(u'По дате окончания события')
        if begExecDate:
            rows.append(u'Начальная дата периода: %s'%forceString(begExecDate))
        if endExecDate:
            rows.append(u'Конечная дата периода: %s'%forceString(endExecDate))
        if eventStatus:
            rows.append(u'Статус события: %s'%[u'Закрытые', u'Открытые'][eventStatus-1])
        if eventTypeId:
            rows.append(u'Тип события %s'%(forceString(db.translate('EventType', 'id', eventTypeId, 'name'))))
        if orgStructureId:
            rows.append(u'Подразделение: ' + getOrgStructureFullName(orgStructureId))
        else:
            rows.append(u'Подразделение: ЛПУ')
        if personId:
            rows.append(u'Врач: ' + forceString(db.translate('vrbPersonWithSpeciality', 'id', personId, 'name')))
        if MKBFilter:
            MKBFrom = params.get('MKBFrom', 'A00')
            MKBTo = params.get('MKBTo',   'Z99.9')
            rows.append(u'Коды диагнозов по МКБ с %s по %s'%(forceString(MKBFrom), forceString(MKBTo)))
        rows.append(u'отчёт составлен: '+forceString(QDateTime.currentDateTime()))
        return rows

