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
from PyQt4.QtCore import Qt, pyqtSignature, QChar, QDate, QDateTime, QString

from library.Utils      import forceBool, forceDate, forceDateTime, forceInt, forceRef, forceString

from Events.Utils       import getActionTypeIdListByFlatCode, getWorkEventTypeFilter
from Events.ActionServiceType import CActionServiceType
from Orgs.Utils         import getOrgStructureFullName

from Reports.Report     import CReport, normalizeMKB
from Reports.ReportBase import CReportBase, createTable
from Reports.ReportView import CPageFormat
from Reports.Utils      import dateRangeAsStr, getDataOrgStructure, getStringPropertyPrevEvent


from Ui_AnaliticReportsGeneralInfoSurgery import Ui_AnaliticReportsGeneralInfoSurgeryDialog

class CAnaliticReportsGeneralInfoSurgeryDialog(QtGui.QDialog, Ui_AnaliticReportsGeneralInfoSurgeryDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbEventType.setTable('EventType', True, filter=getWorkEventTypeFilter(isApplyActive=True))
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())
        self.cmbDiseaseCharacter.setTable('rbDiseaseCharacter', True)
        self.timeDeliverReceived()


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
        self.cmbOrder.setCurrentIndex(params.get('order', 0))
        self.cmbDiseaseCharacter.setValue(params.get('diseaseCharacterId', None))
        self.chkAdditionalMKB.setChecked(params.get('isAdditionalMKB', False))
        self.cmbTimeDeliver.setValue(params.get('timeDeliver', u'не определено'))


    def params(self):
        result = {}
        result['begDate'] = forceDate(self.edtBegDate.date())
        result['endDate'] = forceDate(self.edtEndDate.date())
        result['orgStructureId'] = forceRef(self.cmbOrgStructure.value())
        result['eventTypeId'] = forceRef(self.cmbEventType.value())
        result['isGroupingOS'] = forceBool(self.chkIsGroupingOS.isChecked())
        result['MKBFilter'] = forceInt(self.cmbMKBFilter.currentIndex())
        result['MKBFrom']   = unicode(self.edtMKBFrom.text())
        result['MKBTo']     = unicode(self.edtMKBTo.text())
        result['order']     = forceInt(self.cmbOrder.currentIndex())
        result['diseaseCharacterId'] = forceInt(self.cmbDiseaseCharacter.value())
        result['isAdditionalMKB'] = forceBool(self.chkAdditionalMKB.isChecked())
        result['timeDeliver'] = forceString(self.cmbTimeDeliver.text())
        return result


    @pyqtSignature('int')
    def on_cmbMKBFilter_currentIndexChanged(self, index):
        mode = bool(index)
        for widget in (self.edtMKBFrom, self.edtMKBTo):
            widget.setEnabled(mode)
        self.chkAdditionalMKB.setEnabled(not mode)


    @pyqtSignature('bool')
    def on_chkAdditionalMKB_toggled(self, index):
        if self.cmbMKBFilter.currentIndex() > 0:
            mode = bool(index)
            for widget in (self.edtMKBFrom, self.edtMKBTo):
                widget.setEnabled(not mode)


    def timeDeliverReceived(self):
        self.cmbTimeDeliver._model.clear()
        domain = u''
        record = self.timeDeliverReceivedDomain(u'received%')
        if record:
            domainR = QString(forceString(record))
            if u'*' in domainR:
                index = domainR.indexOf(u'*', 0, Qt.CaseInsensitive)
                if domainR[index - 1] != u',':
                    domainR.replace(QString('*'), QString(','))
                else:
                    domainR.remove(QChar('*'), Qt.CaseInsensitive)
            if domainR.indexOf(QString('\'\'')) == -1:
               domain = u'\'не определено\','
            domain += domainR
        self.cmbTimeDeliver.setDomain(domain)


    def timeDeliverReceivedDomain(self, flatCode = u'received%'):
        db = QtGui.qApp.db
        tableAPT = db.table('ActionPropertyType')
        tableActionType = db.table('ActionType')
        tableAction = db.table('Action')
        cond =[tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode(flatCode)),
               tableAPT['name'].like(u'Доставлен'),
               tableAPT['typeName'].like(u'String')
               ]
        queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        queryTable = queryTable.innerJoin(tableAPT, tableActionType['id'].eq(tableAPT['actionType_id']))
        record = db.getRecordEx(queryTable, [tableAPT['valueDomain']], cond)
        if record:
            return record.value(0)
        return None


class CAnaliticReportsGeneralInfoSurgery(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Общие сведения по хирургической помощи по нозологическим формам')
        self.analiticReportsGeneralInfoSurgeryDialog = None
        self.orientation = CPageFormat.Landscape
        self.clientDeath = 8


    def getSetupDialog(self, parent):
        result = CAnaliticReportsGeneralInfoSurgeryDialog(parent)
        self.analiticReportsGeneralInfoSurgeryDialog = result
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
        isGroupingOS = params.get('isGroupingOS', False)
        if isGroupingOS:
            description.append(u'группировка по подразделениям')
        MKBFilter = params.get('MKBFilter', 0)
        if MKBFilter:
            MKBFrom = params.get('MKBFrom', 'A00')
            MKBTo = params.get('MKBTo',   'Z99.9')
            description.append(u'коды диагнозов по МКБ с %s по %s'%(forceString(MKBFrom), forceString(MKBTo)))
        isAdditionalMKB = params.get('isAdditionalMKB', False)
        if isAdditionalMKB:
            description.append(u'фильтр: острые заболевания ЖКТ')
        diseaseCharacterId = params.get('diseaseCharacterId', None)
        if diseaseCharacterId:
            description.append(u'характер заболевания %s'%(forceString(db.translate('rbDiseaseCharacter', 'id', diseaseCharacterId, 'name'))))
        order = params.get('order', 0)
        if order:
            description.append(u'порядок поступления %s'%([u'не задано', u'плановый', u'экстренный', u'самотёком', u'принудительный', u'внутренний перевод', u'неотложная'][order]))
        timeDeliver = params.get('timeDeliver', u'не определено')
        if timeDeliver:
            description.append(u'срок доставки %s' % timeDeliver)
        description.append(u'отчёт составлен: '+forceString(QDateTime.currentDateTime()))
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()


    def getCaptionReport(self, cursor):
        cols = [('10%', [u'Нозологические формы', u'Код МКБ', u'', u'1'], CReportBase.AlignLeft),
                ('18%', [u'', u'Наименование', u'', u'2'], CReportBase.AlignLeft),
                ('9%', [u'Срок доставки', u'', u'', u'3'], CReportBase.AlignLeft),
                ('6%', [u'Выбыло', u'Всего', u'', u'4'], CReportBase.AlignLeft),
                ('6%', [u'', u'Не оперировано', u'Всего', u'5'], CReportBase.AlignLeft),
                ('6%', [u'',u'', u'Умерло', u'6'], CReportBase.AlignLeft),
                ('6%', [u'', u'Оперировано', u'Всего', u'7'], CReportBase.AlignLeft),
                ('6%', [u'', u'', u'Умерло', u'8'], CReportBase.AlignLeft),
                ('9%', [u'Срок операций',u'', u'', u'9'], CReportBase.AlignLeft),
                ('6%', [u'Всего операций', u'', u'', u'10'], CReportBase.AlignLeft),
                ('6%', [u'Из них умерло',u'', u'', u'11'], CReportBase.AlignLeft),
                ('6%', [u'Летальность', u'Общая %', u'', u'12'], CReportBase.AlignLeft),
                ('6%', [u'',u'Послеоперационная %', u'', u'13'], CReportBase.AlignLeft)
               ]
        table = createTable(cursor, cols)
        table.mergeCells(0, 0, 1, 2)
        table.mergeCells(0, 2, 3, 1)
        table.mergeCells(1, 0, 2, 1)
        table.mergeCells(1, 1, 2, 1)
        table.mergeCells(0, 3, 1, 5)
        table.mergeCells(1, 3, 2, 1)
        table.mergeCells(1, 4, 1, 2)
        table.mergeCells(1, 6, 1, 2)
        table.mergeCells(0, 8, 3, 1)
        table.mergeCells(0, 9, 3, 1)
        table.mergeCells(0, 10, 3, 1)
        table.mergeCells(0, 11, 1, 2)
        table.mergeCells(1, 11, 2, 1)
        table.mergeCells(1, 12, 2, 1)
        return table


    def getCaptionReportOrgStructure(self, cursor):
        cols = [('13%', [u'Подразделение', u'', u'', u'1'], CReportBase.AlignLeft),
                ('10%', [u'Нозологические формы', u'Код МКБ', u'', u'2'], CReportBase.AlignLeft),
                ('16%', [u'', u'Наименование', u'', u'3'], CReportBase.AlignLeft),
                ('8%', [u'Срок доставки', u'', u'', u'4'], CReportBase.AlignLeft),
                ('5%', [u'Выбыло', u'Всего', u'', u'5'], CReportBase.AlignLeft),
                ('5%', [u'', u'Не оперировано', u'Всего', u'6'], CReportBase.AlignLeft),
                ('5%', [u'',u'', u'Умерло', u'7'], CReportBase.AlignLeft),
                ('5%', [u'', u'Оперировано', u'Всего', u'8'], CReportBase.AlignLeft),
                ('5%', [u'', u'', u'Умерло', u'9'], CReportBase.AlignLeft),
                ('8%', [u'Срок операций',u'', u'', u'10'], CReportBase.AlignLeft),
                ('5%', [u'Всего операций', u'', u'', u'11'], CReportBase.AlignLeft),
                ('5%', [u'Из них умерло',u'', u'', u'12'], CReportBase.AlignLeft),
                ('5%', [u'Летальность', u'Общая %', u'', u'13'], CReportBase.AlignLeft),
                ('5%', [u'',u'Послеоперационная %', u'', u'14'], CReportBase.AlignLeft)
               ]
        table = createTable(cursor, cols)
        table.mergeCells(0, 0, 3, 1)
        table.mergeCells(0, 1, 1, 2)
        table.mergeCells(0, 3, 3, 1)
        table.mergeCells(1, 1, 2, 1)
        table.mergeCells(1, 2, 2, 1)
        table.mergeCells(0, 4, 1, 5)
        table.mergeCells(1, 4, 2, 1)
        table.mergeCells(1, 5, 1, 2)
        table.mergeCells(1, 7, 1, 2)
        table.mergeCells(0, 9, 3, 1)
        table.mergeCells(0, 10, 3, 1)
        table.mergeCells(0, 11, 3, 1)
        table.mergeCells(0, 12, 1, 2)
        table.mergeCells(1, 12, 2, 1)
        table.mergeCells(1, 13, 2, 1)
        return table


    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Общие сведения по хирургической помощи по нозологическим формам')
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()
        isGroupingOS = params.get('isGroupingOS', False)
        if isGroupingOS:
            table = self.getCaptionReportOrgStructure(cursor)
        else:
            table = self.getCaptionReport(cursor)
        if isGroupingOS:
            mapCodesToRowIdx, reportDataTotalAll = self.getLeavedInfoGroupingOS(params)
            keysList = mapCodesToRowIdx.keys()
            keysList.sort()
            for key in keysList:
                reportDataLine = mapCodesToRowIdx.get(key, {})
                mkbKeys = reportDataLine.keys()
                mkbKeys.sort()
                reportDataTotal = [0]*14
                reportDataTotal[0] = u''
                reportDataTotal[1] = u'Итого'
                reportDataTotal[2] = u''
                reportDataTotal[3] = u''
                reportDataTotal[9] = u'Итого'
                caption = True
                for mkbKey in mkbKeys:
                    reportLineData = reportDataLine.get(mkbKey, {})
                    mergeDeliverKeys = reportLineData.keys()
                    captionMKB = True
                    for deliver, reportLine in reportLineData.items():
                        captionDeliver = True
                        i = table.addRow()
                        for col, val in enumerate(reportLine):
                            if col >= 9:
                                countKeys = len(val.keys())-1
                                mergeTimeKeys = val.keys()
                                for reportLineTime in val.values():
                                    for colTime, valTime in enumerate(reportLineTime):
                                        table.setText(i, colTime+9, forceString(valTime))
                                        if colTime > 0:
                                            reportDataTotal[colTime+9] += valTime
                                    table.setText(i, 12, '%.2f'%(round(reportLineTime[2]*100.0/reportLine[4], 2)) if reportLine[4] else 0.00)
                                    table.setText(i, 13, '%.2f'%(round(reportLineTime[2]*100.0/reportLineTime[1], 2)) if reportLineTime[1] else 0.00)
                                    countKeys -= 1
                                    if countKeys >= 0:
                                        i = table.addRow()
                            else:
                                if caption:
                                    oldI = i
                                    caption = False
                                    table.setText(i, 0, forceString(val))
                                else:
                                    if col > 0 and col != 9:
                                        if forceString(val) == mkbKey[0] and captionMKB:
                                            mkbI = i
                                            deliverI = i
                                            captionMKB = False
                                            table.setText(i, 1, forceString(val))
                                            table.setText(i, 2, forceString(reportLine[2]))
                                        if col == 3 and forceString(val) == deliver and captionDeliver:
                                            deliverI = i
                                            captionDeliver = False
                                            table.setText(i, 3, forceString(val))
                                    if col > 3 and col != 9:
                                        table.setText(i, col, forceString(val))
                            if col > 3 and col < 9:
                                reportDataTotal[col] += val
                        table.mergeCells(deliverI, 3, len(mergeDeliverKeys) * len(mergeTimeKeys), 1)
                        table.mergeCells(deliverI, 4, len(mergeDeliverKeys) * len(mergeTimeKeys), 1)
                        table.mergeCells(deliverI, 5, len(mergeDeliverKeys) * len(mergeTimeKeys), 1)
                        table.mergeCells(deliverI, 6, len(mergeDeliverKeys) * len(mergeTimeKeys), 1)
                        table.mergeCells(deliverI, 7, len(mergeDeliverKeys) * len(mergeTimeKeys), 1)
                        table.mergeCells(deliverI, 8, len(mergeDeliverKeys) * len(mergeTimeKeys), 1)
                    table.mergeCells(mkbI, 1, len(mergeDeliverKeys) * len(mergeTimeKeys), 1)
                    table.mergeCells(mkbI, 2, len(mergeDeliverKeys) * len(mergeTimeKeys), 1)
                if isGroupingOS:
                    i = table.addRow()
                    reportDataTotal[12] = round(reportDataTotal[11]*100.0/reportDataTotal[4], 2) if reportDataTotal[4] else 0.00
                    reportDataTotal[13] = round(reportDataTotal[11]*100.0/reportDataTotal[10], 2) if reportDataTotal[10] else 0.00
                    for col, val in enumerate(reportDataTotal):
                        table.setText(i, col, forceString(val))
                    table.mergeCells(oldI, 0, len(mkbKeys) * len(mergeDeliverKeys) + (len(mkbKeys) * len(mergeDeliverKeys) * len(mergeTimeKeys))+1, 1)
                else:
                    table.mergeCells(oldI, 0, len(mkbKeys) * len(mergeDeliverKeys) + (len(mkbKeys) * len(mergeDeliverKeys) * len(mergeTimeKeys)), 1)
            i = table.addRow()
            reportDataTotalAll[12] = round(reportDataTotalAll[11]*100.0/reportDataTotalAll[4], 2) if reportDataTotalAll[4] else 0.00
            reportDataTotalAll[13] = round(reportDataTotalAll[11]*100.0/reportDataTotalAll[10], 2) if reportDataTotalAll[10] else 0.00
            for col, val in enumerate(reportDataTotalAll):
                table.setText(i, col, forceString(val))
        else:
            mapCodesToRowIdx, reportDataTotalAll = self.getLeavedInfoNoGroupingOS(params)
            mkbKeys = mapCodesToRowIdx.keys()
            mkbKeys.sort()
            for mkbKey in mkbKeys:
                reportDataLine = mapCodesToRowIdx.get(mkbKey, {})
                mergeDeliverKeys = reportDataLine.keys()
                mergeDeliverKeys.sort()
                captionMKB = True
                for deliver, reportLine in reportDataLine.items():
                    captionDeliver = True
                    i = table.addRow()
                    for col, val in enumerate(reportLine):
                        if col == 8:
                            countKeys = len(val.keys())-1
                            mergeTimeKeys = val.keys()
                            for reportLineTime in val.values():
                                for colTime, valTime in enumerate(reportLineTime):
                                    table.setText(i, colTime+8, forceString(valTime))
                                table.setText(i, 11, '%.2f'%(round(reportLineTime[2]*100.0/reportLine[3], 2)) if reportLine[3] else 0.00)
                                table.setText(i, 12, '%.2f'%(round(reportLineTime[2]*100.0/reportLineTime[1], 2)) if reportLineTime[1] else 0.00)
                                countKeys -= 1
                                if countKeys >= 0:
                                    i = table.addRow()
                        else:
                            if col < 8:
                                if forceString(val) == mkbKey[0] and captionMKB:
                                    mkbI = i
                                    #deliverI = i
                                    captionMKB = False
                                    table.setText(i, 0, forceString(val))
                                    table.setText(i, 1, forceString(reportLine[1]))
                                if col == 2 and forceString(val) == deliver and captionDeliver:
                                    deliverI = i
                                    captionDeliver = False
                                    table.setText(i, 2, forceString(val))
                            if col > 2 and col < 8:
                                table.setText(i, col, forceString(val))
                    table.mergeCells(deliverI, 2, len(mergeDeliverKeys) * len(mergeTimeKeys), 1)
                    table.mergeCells(deliverI, 3, len(mergeDeliverKeys) * len(mergeTimeKeys), 1)
                    table.mergeCells(deliverI, 4, len(mergeDeliverKeys) * len(mergeTimeKeys), 1)
                    table.mergeCells(deliverI, 5, len(mergeDeliverKeys) * len(mergeTimeKeys), 1)
                    table.mergeCells(deliverI, 6, len(mergeDeliverKeys) * len(mergeTimeKeys), 1)
                    table.mergeCells(deliverI, 7, len(mergeDeliverKeys) * len(mergeTimeKeys), 1)
                table.mergeCells(mkbI, 0, len(mergeDeliverKeys) * len(mergeTimeKeys), 1)
                table.mergeCells(mkbI, 1, len(mergeDeliverKeys) * len(mergeTimeKeys), 1)
            i = table.addRow()
            reportDataTotalAll[11] = round(reportDataTotalAll[10]*100.0/reportDataTotalAll[3], 2) if reportDataTotalAll[3] else 0.00
            reportDataTotalAll[12] = round(reportDataTotalAll[10]*100.0/reportDataTotalAll[9], 2) if reportDataTotalAll[9] else 0.00
            for col, val in enumerate(reportDataTotalAll):
                table.setText(i, col, forceString(val))
        return doc


    def getLeavedInfoNoGroupingOS(self, params):
        db = QtGui.qApp.db
        orgStructureId = params.get('orgStructureId', None)
        orgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', orgStructureId) if orgStructureId else []
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        order = params.get('order', 0)
        eventTypeId = params.get('eventTypeId', None)
        diseaseCharacterId = params.get('diseaseCharacterId', None)
        MKBFilter = params.get('MKBFilter', 0)
        MKBFrom = params.get('MKBFrom', 'A00')
        MKBTo = params.get('MKBTo',   'Z99.9')
        isAdditionalMKB = params.get('isAdditionalMKB', False)
        timeDeliver = params.get('timeDeliver', u'не определено')
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
        self.analiticReportsGeneralInfoSurgeryDialog.edtBegDate.setDate(begDate)
        self.analiticReportsGeneralInfoSurgeryDialog.edtEndDate.setDate(endDate)
        tableEvent = db.table('Event')
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        tableClient = db.table('Client')
        tableEventType = db.table('EventType')
        tableRBMedicalAidType = db.table('rbMedicalAidType')
        tableDiagnosis = db.table('Diagnosis')
        tableDiagnostic = db.table('Diagnostic')
        tableDiagnosisType = db.table('rbDiagnosisType')
        tableMKB = db.table('MKB')
        table = tableEvent.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
        table = table.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        table = table.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
        table = table.innerJoin(tableRBMedicalAidType, tableEventType['medicalAidType_id'].eq(tableRBMedicalAidType['id']))
        table = table.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
        leavedIdList = getActionTypeIdListByFlatCode('leaved%')
        movingIdList = getActionTypeIdListByFlatCode('moving%')
        receivedIdList = getActionTypeIdListByFlatCode('received%')
        cols = [tableAction['event_id'],
                tableAction['person_id'],
                tableEvent['setDate'],
                tableEvent['execDate'],
                tableAction['begDate'],
                tableAction['endDate'],
                tableEvent['order'],
                tableEvent['client_id'],
                tableDiagnosis['MKB'],
                tableMKB['DiagName'],
                tableEventType['name']
                ]
        cols.append(u'''(SELECT APS.value
                    FROM Action AS A
                    INNER JOIN ActionPropertyType AS APT ON APT.actionType_id=A.actionType_id
                    INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id
                    INNER JOIN ActionProperty_String AS APS ON APS.id=AP.id
                    WHERE A.`event_id` = getFirstEventId(Event.id) AND A.`deleted`=0
                    AND A.actionType_id IN (%s) AND AP.deleted=0
                    AND A.begDate IS NOT NULL AND AP.action_id=A.id
                    AND APT.deleted=0 AND APT.name = '%s' AND APS.value != ''
                    LIMIT 1) AS deliver'''%(','.join(str(receivedId) for receivedId in receivedIdList), u'Доставлен'))
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
                    AND (APS.value LIKE '%s' OR APS.value LIKE '%s')
                    LIMIT 1) AS resultHospital
                    '''%(','.join(str(leavedId) for leavedId in leavedIdList), u'Исход госпитализации', u'умер%', u'смерть%'))
        cols.append('''(SELECT SUM(A.amount)
                        FROM Action AS A
                        INNER JOIN ActionType ON A.`actionType_id`=ActionType.`id`
                        LEFT JOIN rbService ON rbService.`id`=ActionType.`nomenclativeService_id`
                        WHERE A.`event_id` = Event.id AND (A.`deleted`=0) AND (ActionType.`deleted`=0)
                        AND (Client.`deleted`=0) AND (A.`endDate` IS NOT NULL)
                        AND ActionType.serviceType = %d
                        GROUP BY A.event_id) AS surgery'''%(CActionServiceType.operation))
        cond = [tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode('leaved%')),
                tableEvent['deleted'].eq(0),
                tableAction['begDate'].isNotNull(),
                tableAction['deleted'].eq(0),
                tableActionType['deleted'].eq(0),
                tableClient['deleted'].eq(0),
                tableEventType['deleted'].eq(0)
                ]
        if orgStructureIdList:
            cond.append(getDataOrgStructure(u'Отделение', orgStructureIdList))
        if eventTypeId:
            cond.append(tableEventType['id'].eq(eventTypeId))
        if order:
            cond.append(tableEvent['order'].eq(order))
        cond.append(tableRBMedicalAidType['code'].inlist([1, 2, 3]))
        if bool(begDate):
            cond.append(tableAction['endDate'].ge(begDate))
        if bool(endDate):
            cond.append(tableAction['endDate'].lt(endDate.addDays(1)))
        recordsOS = db.getRecordList('OrgStructure', 'id, name', '', 'name')
        orgStructureNameList = {}
        for recordOS in recordsOS:
            osId = forceRef(recordOS.value('id'))
            osName = forceString(recordOS.value('name'))
            orgStructureNameList[osId] = osName
        if isAdditionalMKB:
            table = table.innerJoin(tableDiagnostic, tableEvent['id'].eq(tableDiagnostic['event_id']))
            table = table.innerJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
            table = table.innerJoin(tableDiagnosisType, tableDiagnosisType['id'].eq(tableDiagnostic['diagnosisType_id']))
            cond.append(tableDiagnostic['deleted'].eq(0))
            cond.append(tableDiagnosis['deleted'].eq(0))
            cond.append('''Diagnosis.MKB IN ('K56', 'K35', 'K25.1', 'K25.2', 'K25.5', 'K25.6', 'K26.1',
                             'K26.2', 'K26.5', 'K26.6', 'K92.2', 'K40.0', 'K40.1', 'K40.3', 'K40.4', 'K41.0',
                             'K41.1', 'K41.3', 'K41.4', 'K42.0', 'K42.1', 'K43.0', 'K43.1', 'K44.0',
                             'K44.1', 'K45.0', 'K45.1', 'K46.0', 'K46.1', 'K80.0', 'K80.1', 'O00', 'K81.0', 'K25.0',
                             'K25.4', 'K26.4', 'K26.0') OR Diagnosis.MKB LIKE 'K56%' OR Diagnosis.MKB LIKE 'K35%' OR Diagnosis.MKB LIKE 'K85%' ''')
        elif MKBFilter:
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
        cond.append('''(rbDiagnosisType.code = '1'
OR (rbDiagnosisType.code = '2' AND Diagnostic.person_id = Event.execPerson_id
AND (NOT EXISTS (SELECT DC.id FROM Diagnostic AS DC
INNER JOIN rbDiagnosisType AS DT ON DT.id = DC.diagnosisType_id WHERE DT.code = '1'
AND DC.event_id = Event.id))))''')
        if diseaseCharacterId:
            cond.append(tableDiagnosis['character_id'].eq(diseaseCharacterId))
        if bool(timeDeliver and timeDeliver != u'не определено'):
            cond.append(getStringPropertyPrevEvent(receivedIdList, u'Доставлен', timeDeliver))
        table = table.join(tableMKB, 'MKB.DiagID=LEFT(Diagnosis.MKB,5)')
        if diseaseCharacterId:
            cond.append(tableDiagnosis['character_id'].eq(diseaseCharacterId))
        records = db.getRecordListGroupBy(table, cols, cond, 'Event.id')
        reportDataTotal = {}
        reportDataTotalAll = [0]*13
        reportDataTotalAll[0] = u'Итого'
        reportDataTotalAll[1] = u''
        reportDataTotalAll[2] = u''
        reportDataTotalAll[8] = u'Итого'
        reportLineTimeSurgery = {u'До 6ч':[0]*5, u'7-24ч':[0]*5, u'> 24ч':[0]*5}
        reportLineTimeSurgery[u'До 6ч'][0] = u'До 6ч'
        reportLineTimeSurgery[u'7-24ч'][0] = u'7-24ч'
        reportLineTimeSurgery[u'> 24ч'][0] = u'> 24ч'
        eventIdList = []
        actionIdList = []
        for record in records:
            eventId = forceRef(record.value('event_id'))
            surgery = forceBool(record.value('surgery'))
            deliver = forceString(record.value('deliver'))
            resultHospital =  forceInt(record.value('resultHospital'))
            MKBRec = normalizeMKB(forceString(record.value('MKB')))
            DiagName = forceString(record.value('DiagName'))
            if not deliver:
                deliver = u'без уточнения'
            reportLineData = reportDataTotal.get((MKBRec, DiagName), {})
            reportLine = reportLineData.get(deliver, [0]*9)
            reportLine[0] = MKBRec
            reportLine[1] = DiagName
            reportLine[2] = deliver
            reportLineTimeSurgery = reportLine[8]
            if not reportLineTimeSurgery:
                reportLineTimeSurgery = {u'До 6ч':[0]*5, u'7-24ч':[0]*5, u'> 24ч':[0]*5}
                reportLineTimeSurgery[u'До 6ч'][0] = u'До 6ч'
                reportLineTimeSurgery[u'7-24ч'][0] = u'7-24ч'
                reportLineTimeSurgery[u'> 24ч'][0] = u'> 24ч'
            prevEventSurgery = False
            surgeryRecords = self.getSurgeryRecords(eventId, movingIdList)
            for surgeryRecord in surgeryRecords:
                actionId = forceRef(surgeryRecord.value('actionId'))
                if actionId and actionId not in actionIdList:
                    actionIdList.append(actionId)
                    countSurgery = forceInt(surgeryRecord.value('countSurgery'))
                    begDateSurgery = forceDateTime(surgeryRecord.value('begDateSurgery'))
                    begDateMoving = forceDateTime(surgeryRecord.value('begDateMoving'))
                    if not surgery:
                        actionEventId = forceRef(surgeryRecord.value('eventId'))
                        prevEventSurgery = bool(countSurgery) and (actionEventId and actionEventId != eventId)
                    timeSurgery = 0
                    if begDateMoving and begDateSurgery:
                        timeSurgery = begDateMoving.secsTo(begDateSurgery)
                    if timeSurgery <= 21600:
                        reportLineTime = reportLineTimeSurgery.get(u'До 6ч', [])
                        reportLineTime[0] = u'До 6ч'
                        if countSurgery:
                            reportLineTime[1] += countSurgery
                            reportDataTotalAll[9] += countSurgery
                            if eventId and eventId not in eventIdList:
                                reportLineTime[2] += resultHospital
                                reportDataTotalAll[10] += resultHospital
                        reportLineTimeSurgery[u'До 6ч'] = reportLineTime
                    elif timeSurgery > 21600 and timeSurgery < 86400:
                        reportLineTime = reportLineTimeSurgery.get(u'7-24ч', [])
                        reportLineTime[0] = u'7-24ч'
                        if countSurgery:
                            reportLineTime[1] += countSurgery
                            reportDataTotalAll[9] += countSurgery
                            if eventId and eventId not in eventIdList:
                                reportLineTime[2] += resultHospital
                                reportDataTotalAll[10] += resultHospital
                        reportLineTimeSurgery[u'7-24ч'] = reportLineTime
                    elif timeSurgery >= 86400:
                        reportLineTime = reportLineTimeSurgery.get(u'> 24ч', [])
                        reportLineTime[0] = u'> 24ч'
                        if countSurgery:
                            reportLineTime[1] += countSurgery
                            reportDataTotalAll[9] += countSurgery
                            if eventId and eventId not in eventIdList:
                                reportLineTime[2] += resultHospital
                                reportDataTotalAll[10] += resultHospital
                        reportLineTimeSurgery[u'> 24ч'] = reportLineTime
            if eventId and eventId not in eventIdList:
                reportLine[3] += 1
                reportDataTotalAll[3] += 1
                if surgery or (prevEventSurgery and not surgery):
                    reportLine[6] += 1
                    reportLine[7] += resultHospital
                    reportDataTotalAll[6] += 1
                    reportDataTotalAll[7] += resultHospital
                else:
                    reportLine[4] += 1
                    reportLine[5] += resultHospital
                    reportDataTotalAll[4] += 1
                    reportDataTotalAll[5] += resultHospital
                eventIdList.append(eventId)
            reportLine[8] = reportLineTimeSurgery
            reportLineData[deliver] = reportLine
            reportDataTotal[(MKBRec, DiagName)] = reportLineData
        return reportDataTotal, reportDataTotalAll


    def getLeavedInfoGroupingOS(self, params):
        db = QtGui.qApp.db
        orgStructureId = params.get('orgStructureId', None)
        orgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', orgStructureId) if orgStructureId else []
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        order = params.get('order', 0)
        eventTypeId = params.get('eventTypeId', None)
        diseaseCharacterId = params.get('diseaseCharacterId', None)
        MKBFilter = params.get('MKBFilter', 0)
        MKBFrom = params.get('MKBFrom', 'A00')
        MKBTo = params.get('MKBTo',   'Z99.9')
        isAdditionalMKB = params.get('isAdditionalMKB', False)
        timeDeliver = params.get('timeDeliver', u'не определено')
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
        self.analiticReportsGeneralInfoSurgeryDialog.edtBegDate.setDate(begDate)
        self.analiticReportsGeneralInfoSurgeryDialog.edtEndDate.setDate(endDate)
        tableEvent = db.table('Event')
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        tableClient = db.table('Client')
        tableEventType = db.table('EventType')
        tableRBMedicalAidType = db.table('rbMedicalAidType')
        tableDiagnosis = db.table('Diagnosis')
        tableDiagnostic = db.table('Diagnostic')
        tableDiagnosisType = db.table('rbDiagnosisType')
        tableMKB = db.table('MKB')
        table = tableEvent.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
        table = table.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        table = table.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
        table = table.innerJoin(tableRBMedicalAidType, tableEventType['medicalAidType_id'].eq(tableRBMedicalAidType['id']))
        table = table.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
        leavedIdList = getActionTypeIdListByFlatCode('leaved%')
        movingIdList = getActionTypeIdListByFlatCode('moving%')
        receivedIdList = getActionTypeIdListByFlatCode('received%')
        cols = [tableAction['event_id'],
                tableAction['person_id'],
                tableEvent['setDate'],
                tableEvent['execDate'],
                tableAction['begDate'],
                tableAction['endDate'],
                tableEvent['order'],
                tableEvent['client_id'],
                tableDiagnosis['MKB'],
                tableMKB['DiagName'],
                tableEventType['name']
                ]
        cols.append(u'''(SELECT APS.value
                    FROM Action AS A
                    INNER JOIN ActionPropertyType AS APT ON APT.actionType_id=A.actionType_id
                    INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id
                    INNER JOIN ActionProperty_String AS APS ON APS.id=AP.id
                    WHERE A.`event_id` = getFirstEventId(Event.id) AND A.`deleted`=0
                    AND A.actionType_id IN (%s) AND AP.deleted=0
                    AND A.begDate IS NOT NULL AND AP.action_id=A.id
                    AND APT.deleted=0 AND APT.name = '%s' AND APS.value != ''
                    LIMIT 1) AS deliver'''%(','.join(str(receivedId) for receivedId in receivedIdList), u'Доставлен'))
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
                    AND (APS.value LIKE '%s' OR APS.value LIKE '%s')
                    LIMIT 1) AS resultHospital
                    '''%(','.join(str(leavedId) for leavedId in leavedIdList), u'Исход госпитализации', u'умер%', u'смерть%'))
        cols.append('''(SELECT SUM(A.amount)
                        FROM Action AS A
                        INNER JOIN ActionType ON A.`actionType_id`=ActionType.`id`
                        LEFT JOIN rbService ON rbService.`id`=ActionType.`nomenclativeService_id`
                        WHERE A.`event_id` = Event.id AND (A.`deleted`=0) AND (ActionType.`deleted`=0)
                        AND (Client.`deleted`=0) AND (A.`endDate` IS NOT NULL)
                        AND ActionType.serviceType = %d
                        GROUP BY A.event_id) AS surgery'''%(CActionServiceType.operation))
        cols.append('''(SELECT APOS2.value
                FROM Action AS A
                INNER JOIN ActionType AS AT ON A.`actionType_id`= AT.`id`
                INNER JOIN ActionProperty AS AP2 ON AP2.action_id=A.id
                INNER JOIN ActionPropertyType AS APT2 ON AP2.type_id=APT2.id
                INNER JOIN ActionProperty_OrgStructure AS APOS2 ON APOS2.id=AP2.id
                INNER JOIN OrgStructure AS OS2 ON OS2.id=APOS2.value
                WHERE A.`event_id` = Event.id AND A.id = Action.id AND A.`deleted`=0
                AND AT.`deleted`=0 AND A.begDate IS NOT NULL AND APT2.actionType_id=A.actionType_id
                AND APT2.deleted=0 AND APT2.name = '%s' AND OS2.type != 0
                AND OS2.deleted=0
                LIMIT 1) AS orgStructureId'''%(u'Отделение'))
        cond = [tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode('leaved%')),
                tableEvent['deleted'].eq(0),
                tableAction['begDate'].isNotNull(),
                tableAction['deleted'].eq(0),
                tableActionType['deleted'].eq(0),
                tableClient['deleted'].eq(0),
                tableEventType['deleted'].eq(0)
                ]
        if orgStructureIdList:
            cond.append(getDataOrgStructure(u'Отделение', orgStructureIdList))
        if eventTypeId:
            cond.append(tableEventType['id'].eq(eventTypeId))
        if order:
            cond.append(tableEvent['order'].eq(order))
        cond.append(tableRBMedicalAidType['code'].inlist([1, 2, 3]))
        if bool(begDate):
            cond.append(tableAction['endDate'].ge(begDate))
        if bool(endDate):
            cond.append(tableAction['endDate'].lt(endDate.addDays(1)))
        recordsOS = db.getRecordList('OrgStructure', 'id, name', '', 'name')
        orgStructureNameList = {}
        for recordOS in recordsOS:
            osId = forceRef(recordOS.value('id'))
            osName = forceString(recordOS.value('name'))
            orgStructureNameList[osId] = osName
        if isAdditionalMKB:
            table = table.innerJoin(tableDiagnostic, tableEvent['id'].eq(tableDiagnostic['event_id']))
            table = table.innerJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
            table = table.innerJoin(tableDiagnosisType, tableDiagnosisType['id'].eq(tableDiagnostic['diagnosisType_id']))
            cond.append(tableDiagnostic['deleted'].eq(0))
            cond.append(tableDiagnosis['deleted'].eq(0))
            cond.append('''Diagnosis.MKB IN ('K56', 'K35', 'K25.1', 'K25.2', 'K25.5', 'K25.6', 'K26.1',
                             'K26.2', 'K26.5', 'K26.6', 'K92.2', 'K40.0', 'K40.1', 'K40.3', 'K40.4', 'K41.0',
                             'K41.1', 'K41.3', 'K41.4', 'K42.0', 'K42.1', 'K43.0', 'K43.1', 'K44.0',
                             'K44.1', 'K45.0', 'K45.1', 'K46.0', 'K46.1', 'K80.0', 'K80.1', 'O00', 'K81.0', 'K25.0',
                             'K25.4', 'K26.4', 'K26.0') OR Diagnosis.MKB LIKE 'K56%' OR Diagnosis.MKB LIKE 'K35%' OR Diagnosis.MKB LIKE 'K85%' ''')
        elif MKBFilter:
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
        cond.append('''(rbDiagnosisType.code = '1'
OR (rbDiagnosisType.code = '2' AND Diagnostic.person_id = Event.execPerson_id
AND (NOT EXISTS (SELECT DC.id FROM Diagnostic AS DC
INNER JOIN rbDiagnosisType AS DT ON DT.id = DC.diagnosisType_id WHERE DT.code = '1'
AND DC.event_id = Event.id))))''')
        if diseaseCharacterId:
            cond.append(tableDiagnosis['character_id'].eq(diseaseCharacterId))
        if bool(timeDeliver and timeDeliver != u'не определено'):
            cond.append(getStringPropertyPrevEvent(receivedIdList, u'Доставлен', timeDeliver))
        table = table.join(tableMKB, 'MKB.DiagID=LEFT(Diagnosis.MKB,5)')
        if diseaseCharacterId:
            cond.append(tableDiagnosis['character_id'].eq(diseaseCharacterId))
        records = db.getRecordListGroupBy(table, cols, cond, 'Event.id')
        reportDataTotal = {}
        reportDataTotalAll = [0]*14
        reportDataTotalAll[0] = u'Итого'
        reportDataTotalAll[1] = u''
        reportDataTotalAll[2] = u''
        reportDataTotalAll[3] = u''
        reportDataTotalAll[9] = u'Итого'
        reportLineTimeSurgery = {u'До 6ч':[0]*5, u'7-24ч':[0]*5, u'> 24ч':[0]*5}
        reportLineTimeSurgery[u'До 6ч'][0] = u'До 6ч'
        reportLineTimeSurgery[u'7-24ч'][0] = u'7-24ч'
        reportLineTimeSurgery[u'> 24ч'][0] = u'> 24ч'
        eventIdList = []
        actionIdList = []
        for record in records:
            eventId = forceRef(record.value('event_id'))
            surgery = forceBool(record.value('surgery'))
            deliver = forceString(record.value('deliver'))
            resultHospital =  forceInt(record.value('resultHospital'))
            MKBRec = normalizeMKB(forceString(record.value('MKB')))
            DiagName = forceString(record.value('DiagName'))
            nameOSId = forceRef(record.value('orgStructureId'))
            if not deliver:
                deliver = u'без уточнения'
            reportData = reportDataTotal.get(nameOSId, {})
            reportLineData = reportData.get((MKBRec, DiagName), {})
            reportLine = reportLineData.get(deliver, [0]*10)
            reportLine[0] = orgStructureNameList.get(nameOSId, u'не определено')
            reportLine[1] = MKBRec
            reportLine[2] = DiagName
            reportLine[3] = deliver
            reportLineTimeSurgery = reportLine[9]
            if not reportLineTimeSurgery:
                reportLineTimeSurgery = {u'До 6ч':[0]*5, u'7-24ч':[0]*5, u'> 24ч':[0]*5}
                reportLineTimeSurgery[u'До 6ч'][0] = u'До 6ч'
                reportLineTimeSurgery[u'7-24ч'][0] = u'7-24ч'
                reportLineTimeSurgery[u'> 24ч'][0] = u'> 24ч'
            prevEventSurgery = False
            surgeryRecords = self.getSurgeryRecords(eventId, movingIdList)
            for surgeryRecord in surgeryRecords:
                actionId = forceRef(surgeryRecord.value('actionId'))
                if actionId and actionId not in actionIdList:
                    actionIdList.append(actionId)
                    countSurgery = forceInt(surgeryRecord.value('countSurgery'))
                    begDateSurgery = forceDateTime(surgeryRecord.value('begDateSurgery'))
                    begDateMoving = forceDateTime(surgeryRecord.value('begDateMoving'))
                    if not surgery:
                        actionEventId = forceRef(surgeryRecord.value('eventId'))
                        prevEventSurgery = bool(countSurgery) and (actionEventId and actionEventId != eventId)
                    timeSurgery = 0
                    if begDateMoving and begDateSurgery:
                        timeSurgery = begDateMoving.secsTo(begDateSurgery)
                    if timeSurgery <= 21600:
                        reportLineTime = reportLineTimeSurgery.get(u'До 6ч', [])
                        reportLineTime[0] = u'До 6ч'
                        if countSurgery:
                            reportLineTime[1] += countSurgery
                            reportDataTotalAll[10] += countSurgery
                            if eventId and eventId not in eventIdList:
                                reportLineTime[2] += resultHospital
                                reportDataTotalAll[11] += resultHospital
                        reportLineTimeSurgery[u'До 6ч'] = reportLineTime
                    elif timeSurgery > 21600 and timeSurgery < 86400:
                        reportLineTime = reportLineTimeSurgery.get(u'7-24ч', [])
                        reportLineTime[0] = u'7-24ч'
                        if countSurgery:
                            reportLineTime[1] += countSurgery
                            reportDataTotalAll[10] += countSurgery
                            if eventId and eventId not in eventIdList:
                                reportLineTime[2] += resultHospital
                                reportDataTotalAll[11] += resultHospital
                        reportLineTimeSurgery[u'7-24ч'] = reportLineTime
                    elif timeSurgery >= 86400:
                        reportLineTime = reportLineTimeSurgery.get(u'> 24ч', [])
                        reportLineTime[0] = u'> 24ч'
                        if countSurgery:
                            reportLineTime[1] += countSurgery
                            reportDataTotalAll[10] += countSurgery
                            if eventId and eventId not in eventIdList:
                                reportLineTime[2] += resultHospital
                                reportDataTotalAll[11] += resultHospital
                        reportLineTimeSurgery[u'> 24ч'] = reportLineTime
            if eventId and eventId not in eventIdList:
                reportLine[4] += 1
                reportDataTotalAll[4] += 1
                if surgery or (prevEventSurgery and not surgery):
                    reportLine[7] += 1
                    reportLine[8] += resultHospital
                    reportDataTotalAll[7] += 1
                    reportDataTotalAll[8] += resultHospital
                else:
                    reportLine[5] += 1
                    reportLine[6] += resultHospital
                    reportDataTotalAll[5] += 1
                    reportDataTotalAll[6] += resultHospital
                eventIdList.append(eventId)
            reportLine[9] = reportLineTimeSurgery
            reportLineData[deliver] = reportLine
            reportData[(MKBRec, DiagName)] = reportLineData
            reportDataTotal[nameOSId] = reportData
        return reportDataTotal, reportDataTotalAll


    def getSurgeryRecords(self, eventId, movingIdList):
        if not eventId:
            return None
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        tableEvent = db.table('Event')
        idList = set([])
        idListParents = set(db.getTheseAndParents(tableEvent, 'prevEvent_id', [eventId]))
        idList |= idListParents
        cols = [tableAction['id'].alias('actionId'),
                tableAction['event_id'].alias('eventId'),
                tableAction['amount'].alias('countSurgery'),
                tableAction['begDate'].alias('begDateSurgery')
                ]
        if movingIdList:
            cols.append('''(SELECT A.begDate
                            FROM Action AS A
                            INNER JOIN ActionType AS AT ON A.`actionType_id`= AT.`id`
                            WHERE A.`event_id` = Action.event_id AND A.`deleted`=0
                            AND A.actionType_id IN (%s) AND AT.`deleted`=0
                            AND A.begDate IS NOT NULL AND begDateSurgery IS NOT NULL
                            AND A.begDate <= begDateSurgery
                            AND A.endDate > begDateSurgery
                            LIMIT 1) AS begDateMoving'''%(','.join(str(movingId) for movingId in movingIdList)))
        cond = [tableAction['event_id'].inlist(idList),
                tableAction['deleted'].eq(0),
                tableAction['endDate'].isNotNull(),
                tableActionType['deleted'].eq(0)
                ]
        cond.append('''ActionType.serviceType = %d'''%(CActionServiceType.operation))
        table = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        return db.getRecordListGroupBy(table, cols, cond, u'Action.id')

