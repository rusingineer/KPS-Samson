# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2025 SAMSON Group. All rights reserved.
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

from library.Utils              import forceDate, forceInt, forceRef, forceString
from Events.ActionStatus        import CActionStatus
from Reports.Report             import CReport
from Reports.ReportBase         import CReportBase, createTable
from Orgs.Utils                 import getOrgStructurePersonIdList
from Reports.ReportSetupDialog  import CReportSetupDialog
from Events.Utils               import getActionTypeIdListByFlatCode


def getActionsList(params):
    db = QtGui.qApp.db
    begDate = params.get('begDate')
    endDate = params.get('endDate')
    dispType = params.get('dispType', 0)
    if (not begDate) or (not endDate):
        return []
    record = db.getRecordEx('rbAccountingSystem', 'id', "urn = 'urn:oid:131o'")
    if not record:
        return []
    systemId = forceInt(record.value('id'))
    begDateStr = db.formatDate(begDate)
    endDateStr = db.formatDate(endDate)
    actionTypeIdList = set()
    actionTypeIdList.update(getActionTypeIdListByFlatCode('inspection_disability%'))
    actionTypeIdList.update(getActionTypeIdListByFlatCode('inspection_mse%'))
    if len(actionTypeIdList) == 0:
        actionTypeIdList.add(0)
    if dispType == 0:
        dispTypeStr = u"'8011', '8008', '8009','8014','8015'"
    elif dispType == 1:
        dispTypeStr = u"'8008', '8009','8014','8015'"
    else:
        dispTypeStr = u"'8011'"
    stmt = u'''
SELECT DISTINCT Action.id
FROM Action
INNER JOIN Event ON Action.event_id = Event.id
LEFT JOIN EventType ON EventType.id=Event.eventType_id AND EventType.context!='flag' AND EventType.code!='flag'
WHERE Event.deleted = 0 AND Action.deleted = 0 AND Action.actionType_id NOT IN (%s)
AND (Action.event_id IN (
        SELECT DISTINCT Event.id
        FROM Event
        JOIN EventType ON EventType.id=Event.eventType_id
        LEFT JOIN rbEventProfile ON rbEventProfile.id = EventType.eventProfile_id
        LEFT JOIN Action ON Action.event_id = Event.id
        LEFT JOIN ActionType ON Action.actionType_id = ActionType.id
        LEFT JOIN rbService ON rbService.id = ActionType.nomenclativeService_id
        LEFT JOIN rbService_Identification ON rbService_Identification.master_id = rbService.id
        LEFT JOIN rbAccountingSystem ON rbAccountingSystem.id = rbService_Identification.system_id
        JOIN rbEventTypePurpose ON rbEventTypePurpose.id=EventType.purpose_id

        WHERE Event.deleted = 0 AND EventType.context NOT LIKE 'inspection%%'
            AND rbEventTypePurpose.code NOT LIKE '0'
            AND DATE(Event.execDate) >= DATE(%s)
            AND DATE(Event.execDate) <= DATE(%s)
            AND rbAccountingSystem.code = '131o'
            AND rbEventProfile.code IN (%s)))
    '''
    query = db.query(stmt%(','.join(str(i) for i in actionTypeIdList), begDateStr, endDateStr, dispTypeStr))
    idList = []
    while query.next():
        idList.append(forceInt(query.value(0)))
    return idList


def selectData(params):
    begDate = params.get('begDate', QDate())
    endDate = params.get('endDate', QDate())
    orgStructureId = params.get('orgStructureId', None)
    dispType = params.get('dispType', 0)
    if not endDate:
        return None
    db = QtGui.qApp.db
    record = db.getRecordEx('rbAccountingSystem', 'id', "urn = 'urn:oid:131o'")
    if not record:
        return None
    systemId = forceInt(record.value('id'))
    orgStructure = u''
    if orgStructureId:
        personIdList = getOrgStructurePersonIdList(orgStructureId)
        if personIdList:
            orgStructure = u''' AND Event.execPerson_id IN (%s)'''%(u','.join(str(personId) for personId in personIdList if personId))
    mesDispansIdList = params.get('mesDispansIdList', [])
    if mesDispansIdList:
        mesDispans = u''' AND Event.MES_id IN (%s)'''%(u','.join(forceString(mesId) for mesId in mesDispansIdList if mesId))
    else:
        mesDispans = u''

    if dispType == 0:
        dispTypeStr = u"'8011', '8008', '8014'"
    elif dispType == 1:
        dispTypeStr = u"'8008', '8014'"
    else:
        dispTypeStr = u"'8011'"

    actionsList = getActionsList(params)
    if len(actionsList) == 0:
        actionsList = [0]
    stmt = u'''
SELECT
    Client.id AS clientId,
    Event.id AS eventId,
    Action.MKB AS MKB,
    Action.status,
    Action.endDate,
    age(Client.birthDate, Event.execDate) AS ageClient,
    DATE(Action.endDate) < DATE(Event.setDate) AS isActionExecPrev,
    rbEventProfile.code AS eventTypeIdentification,
    rbService_Identification.value AS serviceIdentification,
    EXISTS(SELECT 1
      FROM Visit JOIN rbService_Identification AS rbSI ON Visit.service_id = rbSI.master_id
      WHERE Visit.event_id = Event.id AND rbSI.system_id = %(systemId)d
        AND Visit.deleted = 0 AND rbSI.value = 'B01.047.01' AND rbSI.deleted = 0
    ) AS isPropertyServiceCode,
    rbService.code AS serviceCode,
    rbResult.regionalCode AS resultCode,

    IF(rbService.code = 'A25.12.004', (SELECT APT.shortName
    FROM Action AS A
    JOIN ActionPropertyType AS APT ON APT.actionType_id = A.actionType_id
    JOIN ActionProperty AS AP  ON (APT.id = AP.type_id AND AP.action_id = A.id)
    JOIN ActionProperty_Integer AS APS ON APS.id = AP.id
    WHERE Action.id IS NOT NULL AND APT.deleted = 0 AND A.id = Action.id AND A.deleted = 0
    AND AP.deleted = 0
    AND APT.name LIKE '%%относительный сердечно-сосудистый риск%%'
    AND APS.value > 1
    AND AP.action_id = Action.id
    ORDER BY APS.id DESC
    LIMIT 1), 0) AS propertyDescr1,

    IF(rbService.code = 'A25.12.004', (SELECT APT.shortName
    FROM Action AS A
    JOIN ActionPropertyType AS APT ON APT.actionType_id = A.actionType_id
    JOIN ActionProperty AS AP  ON (APT.id = AP.type_id AND AP.action_id = A.id)
    JOIN ActionProperty_Integer AS APS ON APS.id = AP.id
    WHERE Action.id IS NOT NULL AND APT.deleted = 0 AND A.id = Action.id AND A.deleted = 0
    AND AP.deleted = 0
    AND APT.name LIKE '%%абсолютный сердечно-сосудистый риск%%'
    AND APS.value > 5
    AND AP.action_id = Action.id
    ORDER BY APS.id DESC
    LIMIT 1), 0) AS propertyDescr2,

    EXISTS(SELECT 1
           FROM ActionProperty
           WHERE ActionProperty.action_id = Action.id
             AND ActionProperty.deleted = 0
             AND ActionProperty.evaluation IS NOT NULL
             AND ActionProperty.evaluation != 0
          ) AS propertyEvaluation,
          
      EXISTS(SELECT apb.value 
        FROM ActionType atp 
        left JOIN Action a1et ON a1et.actionType_id = atp.id
        LEFT JOIN ActionPropertyType apt1et ON atp.id = apt1et.actionType_id  AND apt1et.deleted = 0
        LEFT JOIN ActionProperty ap1et on ap1et.action_id = a1et.id AND ap1et.type_id = apt1et.id AND ap1et.deleted = 0
        left JOIN ActionProperty_Boolean apb ON ap1et.id = apb.id
      WHERE atp.flatCode = 'disp_1et_act' AND a1et.deleted = 0 AND a1et.event_id = Event.id AND ((apt1et.shortName = rbService_Identification.value or apt1et.shortName = rbService.code) or (apt1et.shortName IN ('A09.05.023', 'A09.05.026') AND rbService_Identification.value = 'A09.05.026.006'))
      AND apb.value = 1 LIMIT 1) AS pat

FROM Event
LEFT JOIN Action ON Action.event_id = Event.id
LEFT JOIN ActionType ON Action.actionType_id = ActionType.id
LEFT JOIN rbService ON rbService.id = ActionType.nomenclativeService_id
LEFT JOIN Person ON Person.id = Action.person_id
LEFT JOIN Client ON Client.id = Event.client_id
LEFT JOIN rbResult ON Event.result_id = rbResult.id
LEFT JOIN rbService_Identification ON rbService_Identification.master_id = rbService.id
LEFT JOIN rbAccountingSystem ON rbAccountingSystem.id = rbService_Identification.system_id
LEFT JOIN EventType ON Event.eventType_id = EventType.id
LEFT JOIN rbEventProfile ON rbEventProfile.id = EventType.eventProfile_id
WHERE Event.deleted = 0
  AND Event.prevEvent_id IS NULL
  AND (Event.execDate >= %(begDate)s AND Event.execDate < %(endDate)s)
  %(orgStructure)s
  %(mesDispans)s
  AND Action.deleted = 0
  AND Client.deleted = 0
  AND ActionType.deleted = 0
  AND rbService_Identification.deleted = 0
  AND rbEventProfile.code IN (%(dispType)s)
  AND rbAccountingSystem.code = '131o'
''' % { 'orgStructure':orgStructure,
        'begDate': db.formatDate(begDate),
        'endDate': db.formatDate(endDate.addDays(1)),
        'mesDispans' : mesDispans,
        'dispType' : dispTypeStr,
        'systemId' : systemId,
        'actionIdList': ','.join(str(i) for i in actionsList),
      }
    return db.query(stmt)


class CReportForm131_o_2000_2021(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Сведения о первом этапе диспансеризации определенных групп взрослого населения (2021)')
        self.mapCodeToRow = {
            'A01.31.024':   0,
            'A02.07.004':   1,
            'A02.12.002':   2,
            'A09.05.026':   3,
            'A09.05.023':   4,
            'A09.05.026.006': 4,
            'A25.12.004.1':  5,
            'A25.12.004.2': 6,
            'A06.09.007':   7,
            'A05.10.001':   8,
            'A02.26.015':   9,
            'A08.20.019':   10,
            'A08.20.019.12':11,
            'A06.20.006':   12,
            'A09.19.002':   13,
            'A09.05.135':   14,
            'A03.16.001':   15,
            'B03.016.02':   16,
            'A01.047.01':   17,
            'B01.047.01':  (18, 19, 20),
            'A01.30.009.20':21
        }
        self.rowDescr = [
            (u'', u'Опрос (анкетирование)', u'1'),
            (u'', u'Расчет на основании антропометрии (измерение роста, массы тела, окружности талии) индекса массы тела', u'2'),
            (u'', u'Измерение артериального давления на периферических артериях', u'3'),
            (u'', u'Определение уровня общего холестерина в крови', u'4'),
            (u'', u'Определение уровня глюкозы в крови натощак', u'5'),
            (u'', u'Определение относительного сердечно-сосудистого риска', u'6'),
            (u'', u'Определение абсолютного сердечно-сосудистого риска', u'7'),
            (u'', u'Флюорография легких или рентгенография легких', u'8'),
            (u'', u'Электрокардиография в покое', u'9'),
            (u'', u'Измерение внутриглазного давления', u'10'),
            (u'', u'Осмотр фельдшером (акушеркой) или врачом акушером-гинекологом', u'11'),
            (u'', u'Взятие с использованием щетки цитологической цервикальной мазка (соскоба) с поверхности шейки матки (наружного маточного зева) и цервикального канала на цитологическое исследование, цитологическое исследование мазка с шейки матки', u'12'),
            (u'', u'Маммография обеих молочных желез в двух проекциях', u'13'),
            (u'', u'Исследование кала на скрытую кровь иммунохимическим методом', u'14'),
            (u'', u'Определение простат-специфического антигена в крови', u'15'),
            (u'', u'Эзофагогастродуоденоскопия', u'16'),
            (u'', u'Общий анализ крови', u'17'),
            (u'', u'Краткое индивидуальное профилактическое консультирование', u'18'),
            (u'', u'Прием (осмотр) по результатам профилактического медицинского осмотра фельдшером фельдшерского здравпункта или фельдшерско-акушерского пункта, врачом-терапевтом или врачом по медицинской профилактике отделения (кабинета) медицинской профилактики или центра здоровья граждан в возрасте 18 лет и старше, 1 раз в год такой услуги', u'19'),
            (u'Прием (осмотр) врачом-терапевтом по результатам первого этапа диспансеризации', u'а) граждан в возрасте от 18 лет до 39 лет 1 раз в 3 года', u'19.1'),
            (u'', u'б) граждан в возрасте 40 лет и старше 1 раз в год', u'19.2'),
            (u'', u'Осмотр на выявление визуальных и иных локализаций онкологических заболеваний, включающий осмотр кожных покровов, слизистых губ и ротовой полости, пальпацию щитовидной железы, лимфатических узлов', u'20'),
        ]


    def getSetupDialog(self, parent):
        result = CReportForm131SetupDialog2021(parent)
        result.setTitle(self.title())
        return result


    def _getDefault(self):
        result = [ [0, 0, 0, 0] for row in self.rowDescr ]
        return result


    def _checkResultCodeFor2001(self, resultCode):
        code = forceInt(resultCode)
        if code in (353, 357, 358):
            return True
        return False


    def getReportData(self, query):
        sets = {18:[set(),set()], 19:[set(),set()], 20:[set(),set()]}
        uniqueClient2001 = set()
        reportData = self._getDefault()
        reportDataTotal = [0, 0, 0, 0]
        while query.next():
            record = query.record()
            clientId = forceRef(record.value('clientId'))
            eventId = forceRef(record.value('eventId'))
            actionMkb = forceString(record.value('MKB'))
            propertyDescr1 = forceString(record.value('propertyDescr1'))
            propertyDescr2 = forceString(record.value('propertyDescr2'))
            serviceCode = forceString(record.value('serviceIdentification'))
            serviceCode2 = forceString(record.value('serviceCode'))
            eventTypeCode = forceString(record.value('eventTypeIdentification'))
            isPropertyServiceCode = forceInt(record.value('isPropertyServiceCode'))
            resultCode = forceString(record.value('resultCode')).lower()
            ageClient = forceInt(record.value('ageClient'))
            actionExecPrev = forceInt(record.value('isActionExecPrev'))
            # isActionPrev = forceInt(record.value('isActionPrev'))
            propertyEvaluation = forceInt(record.value('propertyEvaluation'))
            endDate = forceDate(record.value('endDate'))
            status = forceInt(record.value('status'))
            patology = forceInt(record.value('pat'))

            if eventTypeCode in ('8008', '8014') and self._checkResultCodeFor2001(resultCode):
                uniqueClient2001.add(clientId)
            for code in ((serviceCode, 'B01.047.01') if isPropertyServiceCode else ((serviceCode, ) if serviceCode == serviceCode2 else (serviceCode, serviceCode2))):
                actionExecRefusal = (not endDate) and (status == CActionStatus.refused)
                if code not in self.mapCodeToRow:
                    continue
                targetRow = self.mapCodeToRow.get(code, None)
                if code == 'A09.05.026.006':
                    reportLine2 = reportData[3]
                    if endDate and status != CActionStatus.refused:
                        if endDate and status == CActionStatus.finished and not actionExecPrev:
                            reportLine2[0] += 1
                            reportDataTotal[0] += 1
                        if actionExecPrev:
                            reportLine2[1] += 1
                            reportDataTotal[1] += 1
                    if (actionMkb and 'A00' <= actionMkb <= 'T98') or patology:
                        reportLine2[3] += 1
                        reportDataTotal[3] += 1
                    if actionExecRefusal:
                        reportLine2[2] += 1
                        reportDataTotal[2] += 1


                if targetRow == (5, 6):
                    if ageClient >= 40 and propertyDescr2:
                        targetRow = 6
                    elif ageClient < 40 and propertyDescr1:
                        targetRow = 5
                    else:
                        continue
                elif targetRow == (18, 19, 20):
                    if eventTypeCode == '8011' and ageClient >= 18:
                        targetRow = 18
                    elif eventTypeCode in ('8008', '8014'):
                        if 18 <= ageClient <= 39:
                            targetRow = 19
                        elif ageClient >= 40:
                            targetRow = 20
                        else:
                            continue
                    else:
                        continue

                if targetRow is not None:
                    reportLine = reportData[targetRow]
                    uniqueSet = sets.get(targetRow)
                    if endDate and status != CActionStatus.refused:
                        if targetRow not in (18, 19, 20):
                            if endDate and status == CActionStatus.finished and not actionExecPrev:
                                reportLine[0] += 1
                                reportDataTotal[0] += 1
                            if actionExecPrev:
                                reportLine[1] += 1
                                reportDataTotal[1] += 1
                        else:
                            if uniqueSet and eventId not in uniqueSet[0]:
                                uniqueSet[0].add(eventId)
                                reportLine[0] += 1
                                reportDataTotal[0] += 1
                    if (actionMkb and 'A00' <= actionMkb <= 'T98') or patology:
                        if targetRow in (18, 19, 20) and uniqueSet and eventId not in uniqueSet[1]:
                            uniqueSet[1].add(eventId)
                            reportLine[3] += 1
                            reportDataTotal[3] += 1
                        elif targetRow not in (18, 19, 20):
                            reportLine[3] += 1
                            reportDataTotal[3] += 1
                    if actionExecRefusal:
                        if targetRow not in (18,19,20):
                            reportLine[2] += 1
                            reportDataTotal[2] += 1

        return reportData, reportDataTotal, len(uniqueClient2001)


    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Сведения о приемах (осмотрах), консультациях, исследованиях и иных медицинских вмешательствах, входящих в объем профилактического медицинского осмотра и первого этапа диспансеризации')
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()
        cursor.insertText(u'(2000)')
        cursor.insertBlock()
        tableColumns = [
            ('18%', [u'Прием (осмотр), консультация, исследование и иное медицинское вмешательство (далее - медицинское мероприятие), входящее в объем профилактического медицинского осмотра/первого этапа диспансеризации', u'1'], CReportBase.AlignLeft),
            ('18%', [u'', u''], CReportBase.AlignLeft),
            ('4%' , [u'№ строки', u'2'], CReportBase.AlignRight),
            ('15%', [u'Проведено медицинских мероприятий', u'3'], CReportBase.AlignRight),
            ('15%', [u'Учтено из числа выполненных ранее (в предшествующие 12 мес.)', u'4'], CReportBase.AlignRight),
            ('15%', [u'Число отказов', u'5'], CReportBase.AlignRight),
            ('15%', [u'Выявлены патологические состояния', u'6'], CReportBase.AlignRight),
        ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0,0, 1,2)
        table.mergeCells(1,0, 1,2)
        query = selectData(params)
        if not query:
            return doc
        reportData, reportDataTotal, clients2001 = self.getReportData(query)

        for row, descr in enumerate(self.rowDescr):
            reportLine = reportData[row]
            i = table.addRow()
            if row not in (19, 20):
                table.mergeCells(i,0, 1,2)
            table.setText(i, 0, descr[0])
            table.setText(i, 1, descr[1])
            table.setText(i, 2, descr[2])
            table.setText(i, 3, reportLine[0])
            table.setText(i, 4, reportLine[1])
            table.setText(i, 5, reportLine[2])
            table.setText(i, 6, reportLine[3])

        table.mergeCells(21,0, 2,1)
        i = table.addRow()
        table.mergeCells(i, 0, 1, 3)
        table.setText(i, 0, u'Всего')
        table.setText(i, 3, reportDataTotal[0])
        table.setText(i, 4, reportDataTotal[1])
        table.setText(i, 5, reportDataTotal[2])
        table.setText(i, 6, reportDataTotal[3])

        table.setText(2 , 4, 'X')
        table.setText(20, 4, 'X')
        table.setText(21, 4, 'X')
        table.setText(22, 4, 'X')
        table.setText(23, 4, 'X')
        table.setText(20, 5, 'X')
        table.setText(21, 5, 'X')
        table.setText(22, 5, 'X')
        table.setText(23, 5, 'X')

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        table = createTable(cursor, [('50%', [''], CReportBase.AlignLeft), ('50%', [''], CReportBase.AlignLeft)])
        fmt = table.table.format()
        fmt.setBorder(0)
        table.table.setFormat(fmt)
        table.setText(0, 0, u'(2001)')
        table.setText(0, 1, u'Код по ОКЕИ: человек - 792')
        cursor.movePosition(QtGui.QTextCursor.End)

        cursor.insertBlock()
        cursor.insertText(u'Число лиц, которые по результатам первого этапа диспансеризации направлены на второй этап ')
        cursor.insertText(str(clients2001))
        return doc



class CReportForm131SetupDialog2021(CReportSetupDialog):
    def __init__(self, parent=None):
        CReportSetupDialog.__init__(self, parent)
        self.setEventTypeVisible(False)
        # self.setMesDispansListVisible(True)
        self.setOnlyPermanentAttachVisible(False)
        self.setOrgStructureVisible(True)
        self.resize(0, 0)
        self.cmbDispanserization = QtGui.QComboBox()
        self.cmbDispanserization.addItems((u'все', u'диспансеризация', u'профилактический осмотр'))
        row = self.gridLayout.rowCount() - 3
        cols = self.gridLayout.columnCount()
        self.gridLayout.addWidget(QtGui.QLabel(u'Тип'), row, 0)
        self.gridLayout.addWidget(self.cmbDispanserization, row, 1, 1, cols - 1)


    def setParams(self, params):
        CReportSetupDialog.setParams(self, params)
        self.cmbDispanserization.setCurrentIndex(params.get('dispType', 0))


    def params(self):
        result = CReportSetupDialog.params(self)
        result['dispType'] = self.cmbDispanserization.currentIndex()
        return result
