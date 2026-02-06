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
from PyQt4.QtCore import Qt, QDate, QDateTime, QVariant

from library.Calendar   import wpSevenDays
from library.Utils      import forceDate, forceDouble, forceInt, forceRef, forceString, formatNum

from Events.Utils       import getEventDuration
from Reports.ReportBase import CReportBase, createTable
from Reports.ReportView import CReportViewDialog

from Ui_AnalyticsExecutionMesDialog import Ui_AnalyticsExecutionMesDialog

def showCheckMesDescription(parent):
    if parent is not None:
        while True:
            analyticsExecutionMesDialog = CAnalyticsExecutionMesDialog(parent)
            if analyticsExecutionMesDialog.exec_():
                QtGui.qApp.setWaitCursor()
                try:
                    params = analyticsExecutionMesDialog.params()
                    view = CReportViewDialog(parent)
                    view.setRepeatButtonVisible()
                    view.setWindowTitle(u'ПРОТОКОЛ СТАТИСТИЧЕСКОГО АНАЛИЗА ВЫПОЛНЕНИЯ МЭС')
                    view.setText(getMesDescription(parent, params))
                finally:
                    QtGui.qApp.restoreOverrideCursor()
                    view.showMaximized()
                    if not view.exec_():
                        break
            else:
                break


def getMesDescription(parent, params):
    doc = QtGui.QTextDocument()
    cursor = QtGui.QTextCursor(doc)
    db = QtGui.qApp.db
    tableMes = db.table('mes.MES')
    tableEvent = db.table('Event')
    mesIdForEventIdList = insertMainSection(parent, cursor, params)
    for mesId, value in mesIdForEventIdList.items():
        eventIdList, clientIdList = value
        actionTypeIdList = getActionTypeId(eventIdList)
        cursor.insertBlock()
        actionMesIdList = set()
        actionTypeMesIdList = set()
        mesRecord = db.getRecordEx(tableMes, '*', [tableMes['deleted'].eq(0), tableMes['id'].eq(mesId)])
        if mesRecord:
            cursor.insertText(u'МЭС: ' + u'"' + forceString(mesRecord.value('code')) + u'" (' + forceString(mesRecord.value('name')) + u')')
            eventIdSum = len(eventIdList)
            minDuration = forceInt(mesRecord.value('minDuration'))
            maxDuration = forceInt(mesRecord.value('maxDuration'))
            mesAvgDuration = forceDouble(mesRecord.value('avgDuration'))
            cursor.insertBlock()
            cursor.insertText(u'НОРМА: минимальная длительность: ' + formatNum(minDuration, (u'день', u'дня', u'дней'))) #str(minDuration))
            cursor.insertBlock()
            cursor.insertText(u'НОРМА: максимальная длительность: ' + formatNum(maxDuration, (u'день', u'дня', u'дней'))) #str(maxDuration))
            cursor.insertBlock()
            cursor.insertText(u'НОРМА: средняя длительность: ' + formatNum(mesAvgDuration, (u'день', u'дня', u'дней'))) #str(mesAvgDuration))
        else:
            cursor.insertText(u'МЭС: ' + u'????????????')
        cursor.insertBlock()
        minDurationDay = 0
        maxDurationDay = 0
        mesAvgDurationDay = 0
        durationDaySum = 0
        eventCount = 0
        firstDurationDay = False
        for eventId in eventIdList:
            eventRecord = db.getRecordEx(tableEvent, [tableEvent['setDate'], tableEvent['execDate'], tableEvent['eventType_id']], [tableEvent['deleted'].eq(0), tableEvent['id'].eq(eventId)])
            if eventRecord:
                setDate = forceDate(eventRecord.value('setDate'))
                execDate = forceDate(eventRecord.value('execDate'))
                eventTypeId = forceDate(eventRecord.value('eventType_id'))
                if not setDate:
                    setDate = QDate.currentDate()
                if not execDate:
                   execDate = QDate.currentDate()
                durationDay = getEventDuration(setDate, execDate, wpSevenDays, eventTypeId)
                if not firstDurationDay:
                    firstDurationDay = True
                    minDurationDay = durationDay
                    maxDurationDay = durationDay
                if durationDay and durationDay < minDurationDay:
                    minDurationDay = durationDay
                if durationDay and durationDay > maxDurationDay:
                    maxDurationDay = durationDay
                if not durationDay:
                    durationDay = 1
                eventCount += 1
                durationDaySum += durationDay
        if eventCount:
            mesAvgDurationDay = (durationDaySum / eventCount) if durationDaySum >= eventCount else 1
        else:
            mesAvgDurationDay = 0
        cursor.insertText(u'Минимальная длительность случая: ' + formatNum(minDurationDay, (u'день', u'дня', u'дней')))
        cursor.insertBlock()
        cursor.insertText(u'Максимальная длительность случая: ' + formatNum(maxDurationDay, (u'день', u'дня', u'дней')))
        cursor.insertBlock()
        cursor.insertText(u'Средняя длительность случая: ' + formatNum(mesAvgDurationDay, (u'день', u'дня', u'дней')))
        cursor.insertBlock()
        cursor.insertText(u'ВСЕГО СЛУЧАЕВ: ' + str(eventIdSum))
        cursor.insertBlock()
        cursor.insertText(u'ВСЕГО ПАЦИЕНТОВ: ' + str(len(clientIdList)))
        cursor.insertBlock()
#        mkbList = getDiagnosticByEventId(eventIdList)
#        insertMKBSection(parent, cursor, mkbList, mesId)
        visitTypeIdList, visitTypeList, personIdList = getVisitByEventId(eventIdList)
        insertPersonServicesSection(parent, cursor, visitTypeIdList, visitTypeList, personIdList, mesId, eventIdSum)
        actionMesIdList, actionTypeMesIdList = insertServiceSection(parent, cursor, actionTypeIdList, mesId, u'Услуги лечащего врача', u'в', actionMesIdList, actionTypeMesIdList, eventIdSum)
        actionMesIdList, actionTypeMesIdList = insertServiceSection(parent, cursor, actionTypeIdList, mesId, u'Лабораторные диагностические услуги', u'к', actionMesIdList, actionTypeMesIdList, eventIdSum)
        actionMesIdList, actionTypeMesIdList = insertServiceSection(parent, cursor, actionTypeIdList, mesId, u'Инструментальные диагностические услуги', u'д', actionMesIdList, actionTypeMesIdList, eventIdSum)
        actionMesIdList, actionTypeMesIdList = insertServiceSection(parent, cursor, actionTypeIdList, mesId, u'Немедикаментозная терапия', u'л', actionMesIdList, actionTypeMesIdList, eventIdSum)
        actionMesIdList, actionTypeMesIdList = insertServiceSection(parent, cursor, actionTypeIdList, mesId, u'Вспомогательные услуги', u'с', actionMesIdList, actionTypeMesIdList, eventIdSum)
        actionMesIdList, actionTypeMesIdList = insertServiceSection(parent, cursor, actionTypeIdList, mesId, u'Услуги по экспертизе', u'э', actionMesIdList, actionTypeMesIdList, eventIdSum)
        actionMesIdList, actionTypeMesIdList = insertServiceSection(parent, cursor, actionTypeIdList, mesId, u'Несгруппированные услуги', u'55', actionMesIdList, actionTypeMesIdList, eventIdSum)

        insertServiceNoSection(parent, cursor, actionTypeIdList, actionMesIdList, actionTypeMesIdList, eventIdSum)
#        insertMedicamentsSection(cursor, mesId)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()
    return doc


def getActionTypeId(eventIdList):
    actionTypeIdList = {}
    stmt = u'''
        SELECT Action.actionType_id, Action.endDate, Event.id AS eventId
        FROM Event INNER JOIN Action ON Action.event_id = Event.id
        WHERE Action.deleted = 0 AND Event.deleted = 0 AND Action.event_id IN (%s)
    ''' % (u','.join(str(eventId) for eventId in eventIdList if eventId))
    query = QtGui.qApp.db.query(stmt)
    while query.next():
        record = query.record()
        actionTypeId = forceRef(record.value('actionType_id'))
        endDate = forceDate(record.value('endDate'))
        eventId = forceRef(record.value('eventId'))
        if actionTypeId:
            countActionTypeId, actionTypeIdExecuted, eventIdList = actionTypeIdList.get(actionTypeId, (0, 0, []))
            if eventId and eventId not in eventIdList:
               eventIdList.append(eventId)
            actionTypeIdList[actionTypeId] = (countActionTypeId + 1, actionTypeIdExecuted + (1 if endDate else 0), eventIdList)
    return actionTypeIdList


def getVisitByEventId(eventIdList):
    visitTypeIdList = []
    personIdList = []
    visitTypeList = {}
    stmt = u'''
        SELECT Visit.visitType_id, Person.speciality_id, Visit.person_id
        FROM Visit
            LEFT JOIN Event ON Event.id = Visit.event_id
            LEFT JOIN Person ON Visit.person_id = Person.id
        WHERE Visit.deleted = 0 AND Event.deleted = 0 AND Person.deleted = 0 AND Visit.event_id IN (%s) AND DATE(Event.setDate) <= DATE(Visit.date)
    ''' % (u','.join(str(eventId) for eventId in eventIdList if eventId))
    query = QtGui.qApp.db.query(stmt)
    while query.next():
        record = query.record()
        visitTypeId = forceRef(record.value('visitType_id'))
        specialityId = forceRef(record.value('speciality_id'))
        personId = forceRef(record.value('person_id'))
        if visitTypeId:
            countVisitTypeId = visitTypeList.get((visitTypeId, specialityId), 0)
            visitTypeList[(visitTypeId, specialityId)] = countVisitTypeId + 1
            if personId not in personIdList:
                personIdList.append(personId)
            if visitTypeId not in visitTypeIdList:
                visitTypeIdList.append(visitTypeId)
    return visitTypeIdList, visitTypeList, personIdList


def getDiagnosticByEventId(eventIdList):
    mkbList = []
    stmt = u'''
        SELECT Diagnosis.MKB
        FROM Event
            INNER JOIN Diagnostic ON Diagnostic.event_id = Event.id
            INNER JOIN Diagnosis ON Diagnosis.id = Diagnostic.diagnosis_id
            INNER JOIN rbDiagnosisType ON rbDiagnosisType.id = Diagnostic.diagnosisType_id
        WHERE Diagnostic.deleted = 0 AND Event.deleted = 0 AND Diagnosis.deleted = 0 AND Event.id IN (%s) AND rbDiagnosisType.code = '1'
            OR (rbDiagnosisType.code = '2' AND Diagnostic.person_id = Event.execPerson_id
            AND (NOT EXISTS (SELECT DC.id FROM Diagnostic AS DC INNER JOIN rbDiagnosisType AS DT ON DT.id = DC.diagnosisType_id WHERE DT.code = '1'
            AND DC.event_id = Event.id LIMIT 1)))
        GROUP BY Diagnosis.MKB
        ''' % (u','.join(str(eventId) for eventId in eventIdList if eventId))
    query = QtGui.qApp.db .query(stmt)
    while query.next():
        record = query.record()
        MKB = forceString(record.value('MKB'))
        if MKB and MKB not in mkbList:
            mkbList.append(MKB)
    return mkbList


def insertMainSection(parent, cursor, params):
    def getRegion(region, type):
        return '''EXISTS(SELECT AddressHouse.id
                        FROM ClientAddress
                            INNER JOIN Address ON Address.id=ClientAddress.address_id
                            INNER JOIN AddressHouse ON AddressHouse.id=Address.house_id
                        WHERE ClientAddress.client_id=Client.id AND AddressHouse.deleted = 0 AND Address.deleted = 0
                            AND ClientAddress.deleted = 0 AND AddressHouse.KLADRCode = %s AND ClientAddress.type = %s
                        LIMIT 1)'''%(str(region), str(type))

    eventSetDateTime = params.get('begDate', QDate.currentDate())
    eventDate = params.get('endDate', QDate.currentDate())
    mesId = params.get('mesId', None)
    ageFrom = params.get('ageFrom', 0)
    ageTo = params.get('ageTo', 0)
    sex = params.get('sex', 0)
    compulsoryPolisCompanyId = params.get('compulsoryPolisCompany', 0)
    regRegion = params.get('regRegion', None)
    logRegion = params.get('logRegion', None)

    begDateEvent = eventSetDateTime if isinstance(eventSetDateTime, QDateTime) else (QDateTime(eventSetDateTime) if eventDate  else QDateTime())
    endDateEvent = eventDate if isinstance(eventDate, QDateTime) else (QDateTime(eventDate) if eventDate  else QDateTime())
    currentDateTime = QDateTime.currentDateTime()
    if not endDateEvent:
        endDateEvent = currentDateTime

    db = QtGui.qApp.db
    tableEvent = db.table('Event')
    tableClient = db.table('Client')
    tableMes = db.table('mes.MES')
    tableClientPolicy = db.table('ClientPolicy')
    queryTable = tableEvent.innerJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
    queryTable = queryTable.innerJoin(tableMes, tableMes['id'].eq(tableEvent['MES_id']))
    cols = [tableClient['id'],
            tableEvent['eventType_id'],
            tableEvent['id'].alias('eventId'),
            tableClient['id'].alias('clientId'),
            tableEvent['MES_id'],
            ]
    cols.append('mes.MES.*')
    cond = [tableEvent['MES_id'].isNotNull(),
            tableEvent['deleted'].eq(0),
            tableClient['deleted'].eq(0),
            tableMes['deleted'].eq(0)
            ]
    if mesId:
        cond.append(tableEvent['MES_id'].eq(mesId))
    if begDateEvent:
        cond.append(db.joinOr([tableEvent['setDate'].isNull(), tableEvent['setDate'].ge(begDateEvent)]))
    if endDateEvent:
        cond.append(db.joinOr([tableEvent['setDate'].isNull(), tableEvent['setDate'].lt(endDateEvent.addDays(1))]))
    if sex > 0:
        cond.append(tableClient['sex'].eq(sex))
    if ageFrom <= ageTo:
        cond.append('''(Event.setDate >= ADDDATE(Client.birthDate, INTERVAL %d YEAR)) AND (Event.setDate < ADDDATE(Client.birthDate, INTERVAL %d YEAR))''' % (ageFrom, ageTo+1))
    if compulsoryPolisCompanyId:
        queryTable = queryTable.innerJoin(tableClientPolicy, tableClientPolicy['client_id'].eq(tableClient['id']))
        cond.append(tableClientPolicy['deleted'].eq(0))
        cond.append(tableClientPolicy['insurer_id'].eq(compulsoryPolisCompanyId))
    if regRegion:
        cond.append(getRegion(regRegion, 0))
    if logRegion:
        cond.append(getRegion(logRegion, 1))
    mesRecords = db.getRecordList(queryTable, cols, cond)
    mesIdForEventIdList = {}
    for mesRecord in mesRecords:
        eventId = forceRef(mesRecord.value('eventId'))
        clientId = forceRef(mesRecord.value('clientId'))
        mesId = forceRef(mesRecord.value('MES_id'))
        if eventId and mesId:
            eventIdList, clientIdList = mesIdForEventIdList.get(mesId, ([], []))
            if eventId not in eventIdList:
                eventIdList.append(eventId)
            if clientId not in clientIdList:
                clientIdList.append(clientId)
            mesIdForEventIdList[mesId] = (eventIdList, clientIdList)
    bigChars = QtGui.QTextCharFormat()
    bigChars.setProperty(QtGui.QTextFormat.FontSizeIncrement, QVariant(2))
    bigChars.setFontWeight(QtGui.QFont.Bold)
    boldChars = QtGui.QTextCharFormat()
    boldChars.setProperty(QtGui.QTextFormat.FontSizeIncrement, QVariant(1))
    boldChars.setFontWeight(QtGui.QFont.Bold)
    cursor.setCharFormat(bigChars)
    cursor.insertText(u'ПРОТОКОЛ СТАТИСТИЧЕСКОГО АНАЛИЗА ВЫПОЛНЕНИЯ МЭС')
    cursor.insertBlock()
    charFormat = QtGui.QTextCharFormat()
    cursor.setCharFormat(charFormat)
    titleInfo = u'\n' +  u'период'
    if eventDate:
        titleInfo += u' с %s по %s'%(forceString(begDateEvent.date()), forceString(eventDate))
    else:
        titleInfo += u' от %s'%(forceString(begDateEvent))
    titleInfo += u'\n' +  u'возраст с %s по %s'%(ageFrom, ageTo)
    titleInfo += u'\n' +  u'пол %s'%([u'не определено', u'мужской', u'женский'][sex])
    titleInfo += u'\n' +  (u'СМО %s'%(forceString(db.translate('Organisation', u'id', compulsoryPolisCompanyId, 'shortName'))) if compulsoryPolisCompanyId else u'')
    cursor.insertText(titleInfo)
    cursor.movePosition(QtGui.QTextCursor.End)
    return mesIdForEventIdList


def insertMKBSection(parent, cursor, mkbList, mesId):
    boldChars = QtGui.QTextCharFormat()
    boldChars.setFontWeight(QtGui.QFont.Bold)
    cursor.insertText(u'Заболевания, входящие в МЭС (в формулировках МКБ)')
    cursor.insertBlock()
    charFormat = QtGui.QTextCharFormat()
    cursor.setCharFormat(charFormat)
    tableColumns = [
            ('5%',[u'№' ], CReportBase.AlignRight),
            ('15%',[u'Код диагноза по МКБ' ], CReportBase.AlignLeft),
            ('80%',[u'Диагноз' ],             CReportBase.AlignLeft),
            ]

    table = createTable(cursor, tableColumns)
    db = QtGui.qApp.db
    tableMKB = db.table('mes.MES_mkb')
    finalDiagnostic = False
    for MKB in mkbList:
        finalDiagnostic = True
        recordMES = db.getRecordEx(tableMKB, 'mkb', [tableMKB['master_id'].eq(mesId), tableMKB['deleted'].eq(0), tableMKB['mkb'].like(MKB)])
        mesMKB = forceString(recordMES.value('mkb')) if recordMES else u''
        if mesMKB:
            MKB = mesMKB
            brushColor = Qt.green
        else:
            brushColor = Qt.red
        diagName = forceString(db.translate('MKB', 'DiagID', MKB, 'DiagName'))
        i = table.addRow()
        table.setText(i, 0, i, boldChars, None, brushColor, True)
        table.setText(i, 1, MKB, boldChars, None, brushColor, True)
        table.setText(i, 2, diagName, boldChars, None, brushColor, True)
    if not finalDiagnostic:
        i = table.addRow()
        table.setText(i, 0, i, boldChars, None, Qt.red, True)
        table.setText(i, 1, u'', boldChars, None, Qt.red, True)
        table.setText(i, 2, u'Нет заключительного диагноза', boldChars, None, Qt.red, True)
    cursor.movePosition(QtGui.QTextCursor.End)


def getMesAmountVisitType(visitTypeIdList, visitTypeList, mesId, personIdList, groupAvailable, mesVisitResult):
    countedVisits = {}
    if personIdList and mesId:
        db = QtGui.qApp.db
        stmt = u'''
            SELECT
            mMV.groupCode  AS prvsGroup,
            mMV.averageQnt AS averageQnt,
            mMV.id AS mesVisitId,
            rbVisitType.id AS visitTypeId,
            Person.speciality_id,
            IF(mMV.visitType_id=mVT.id, 0, 1) AS visitTypeErr
            FROM Person
            LEFT JOIN rbSpeciality ON rbSpeciality.id = Person.speciality_id
            JOIN rbVisitType
            LEFT JOIN mes.mrbVisitType  AS mVT  ON rbVisitType.code = mVT.code
            LEFT JOIN mes.mrbSpeciality AS mS   ON mS.regionalCode = rbSpeciality.regionalCode
            LEFT JOIN mes.MES_visit     AS mMV  ON mMV.speciality_id = mS.id AND mMV.deleted = 0
            WHERE Person.id IN (%s) AND mS.deleted = 0 AND mVT.deleted = 0 AND rbVisitType.id IN (%s) AND mMV.master_id = %d
            ORDER BY mMV.groupCode
        ''' % (u','.join(str(personId) for personId in personIdList if personId), u','.join(str(visitTypeId) for visitTypeId in visitTypeIdList if visitTypeId), mesId)

        query = db.query(stmt)
        while query.next():
            record = query.record()
            visitTypeId = forceRef(record.value('visitTypeId'))
            specialityId = forceRef(record.value('speciality_id'))
            visitTypeError = forceInt(record.value('visitTypeErr'))
            if not visitTypeError and visitTypeId and not (countedVisits.get((visitTypeId, specialityId), 0)):
                prvsGroup = forceInt(record.value('prvsGroup'))
#                averageQnt = forceInt(record.value('averageQnt'))
                mesVisitId = forceRef(record.value('mesVisitId'))
#                available = groupAvailable.get(prvsGroup, averageQnt)
                available = groupAvailable.get(prvsGroup, 0)
                countVisitTypeId = visitTypeList.get((visitTypeId, specialityId), 0)
                visitIdCount = mesVisitResult.get(mesVisitId, 0)
                #groupAvailable[prvsGroup] = available - countVisitTypeId
                groupAvailable[prvsGroup] = available + countVisitTypeId
                countedVisits[(visitTypeId, specialityId)] = visitIdCount + countVisitTypeId
                mesVisitResult[mesVisitId] = visitIdCount + countVisitTypeId
    return mesVisitResult, groupAvailable, countedVisits


def insertPersonServicesSection(parent, cursor, visitTypeIdList, visitTypeList, personIdList, mesId, eventIdSum):
    db = QtGui.qApp.db
    cursor.insertText(u'Услуги лечащего и консультирующего врача (ВИЗИТЫ)')
    cursor.insertBlock()

    tableColumns = [
            ('5%',[u'№ группы' ],       CReportBase.AlignRight),
            ('10%',[u'Контроль' ],      CReportBase.AlignRight),
            ('10%',[u'Число Визитов' ], CReportBase.AlignRight),
            ('10%',[u'Ср.число визитов' ], CReportBase.AlignRight),
            ('30%',[u'Тип визита' ],    CReportBase.AlignLeft),
            ('35%',[u'Специальность' ], CReportBase.AlignLeft),
            ]
    mesVisitResult = {}
    groupAvailable = {}
    countedVisitType = []
    if visitTypeIdList and personIdList:
        mesVisitResult, groupAvailable, countedVisitType = getMesAmountVisitType(visitTypeIdList, visitTypeList, mesId, personIdList, groupAvailable, mesVisitResult)

    table = createTable(cursor, tableColumns)
    tableVisit = db.table('mes.MES_visit')
    tableVisitType  = db.table('mes.mrbVisitType')
    tableSpeciality = db.table('mes.mrbSpeciality')
    tableQuery = tableVisit.leftJoin(tableVisitType,  tableVisitType['id'].eq(tableVisit['visitType_id']))
    tableQuery = tableQuery.leftJoin(tableSpeciality, tableSpeciality['id'].eq(tableVisit['speciality_id']))
    cols = [tableVisit['groupCode'], tableVisit['averageQnt'], tableVisitType['name'], tableSpeciality['name'], tableVisit['id'].alias('mesVisitId') ]
    prevGroupCode = False
#    if mesId:
#        mesRecordKSGNorm = db.getRecordEx('mes.MES', 'KSGNorm', 'id = %d AND deleted = 0'%(mesId))
#        KSGNorm = forceInt(mesRecordKSGNorm.value('KSGNorm'))
#    else:
#        KSGNorm = 0
    for record in db.getRecordList(tableQuery, cols, [tableVisit['master_id'].eq(mesId), tableVisit['deleted'].eq(0), tableVisitType['deleted'].eq(0), tableSpeciality['deleted'].eq(0)], 'groupCode, '+tableSpeciality['name'].name()):
        i = table.addRow()
        groupCode  = forceString(record.value(0))
        averageQnt = forceInt(record.value(1))
        visitType  = forceString(record.value(2))
        speciality = forceString(record.value(3))
        mesVisitId = forceRef(record.value(4))
        if prevGroupCode != groupCode:
            table.setText(i, 0, groupCode)
            prevGroupCode = groupCode
        table.setText(i, 1, averageQnt)
        brusColor = Qt.red
        visitIdCount = 0
        if mesVisitResult:
            prvsGroup = forceInt(record.value(0))
            visitIdCount = mesVisitResult.get(mesVisitId, 0)
        available = 0
        if groupAvailable:
            available = groupAvailable.get(prvsGroup, 0)
        if round(float(averageQnt), 2) == round((float(available) / eventIdSum) if eventIdSum else 0.0, 2):
            brusColor = Qt.green
        avgVisitIdCount = round((float(visitIdCount) / eventIdSum) if eventIdSum else 0.0, 2)
        table.setText(i, 2, visitIdCount, None, None, brusColor)
        table.setText(i, 3, '%.2f'%(avgVisitIdCount), None, None, brusColor)
        table.setText(i, 4, visitType)
        table.setText(i, 5, speciality)
    if len(visitTypeList) > len(countedVisitType):
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()
        cursor.insertText(u'Услуги лечащего и консультирующего врача выходящие за пределы требования (ВИЗИТЫ)')
        cursor.insertBlock()

        tableColumns = [
                ('5%',[u'№' ], CReportBase.AlignRight),
                ('15%',[u'Количество' ],    CReportBase.AlignRight),
                ('40%',[u'Тип визита' ],    CReportBase.AlignLeft),
                ('40%',[u'Специальность' ], CReportBase.AlignLeft),
                ]
        table = createTable(cursor, tableColumns)
        visitNoMESList = {}
        visitDistinctIdList = {}
        tableSpeciality = db.table('rbSpeciality')
        tableVisitType = db.table('rbVisitType')
        for visitTypeId, specialityId in visitTypeList.keys():
            if not countedVisitType.get((visitTypeId, specialityId), 0):
                recordSpeciality = db.getRecordEx(tableSpeciality, 'rbSpeciality.name AS nameSpeciality, rbSpeciality.id AS specialityId', [tableSpeciality['id'].eq(specialityId)])
                recordVisitType = db.getRecordEx(tableVisitType, 'rbVisitType.id, rbVisitType.name AS nameVisitType', [tableVisitType['id'].eq(visitTypeId)])
                if recordVisitType:
                    visitTypeId  = forceRef(recordVisitType.value('id'))
                    if recordSpeciality:
                        specialityId = forceRef(recordSpeciality.value('specialityId'))
                        nameSpeciality = forceString(recordSpeciality.value('nameSpeciality'))
                    else:
                        specialityId = None
                        nameSpeciality = u''
                    if visitTypeId and not (visitDistinctIdList.get((visitTypeId, specialityId), 0)) and not countedVisitType.get((visitTypeId, specialityId), 0):
                        visitDistinctIdList[(visitTypeId, specialityId)] = 1
                        nameVisitType  = forceString(recordVisitType.value('nameVisitType'))
                        visitNoMES = visitNoMESList.get((visitTypeId, specialityId), None)
                        countVisitTypeId = visitTypeList.get((visitTypeId, specialityId), 0)
                        if visitNoMES:
                            visitNoMESList[(visitTypeId, specialityId)] = (visitNoMES[0] + countVisitTypeId, nameVisitType, nameSpeciality)
                        else:
                            visitNoMESList[(visitTypeId, specialityId)] = (countVisitTypeId, nameVisitType, nameSpeciality)
        for key, item in visitNoMESList.items():
            i = table.addRow()
            table.setText(i, 0, i, None, None, Qt.red)
            table.setText(i, 1, item[0], None, None, Qt.red)
            table.setText(i, 2, item[1], None, None, Qt.red)
            table.setText(i, 3, item[2], None, None, Qt.red)


def getMesAmountActionType(actionTypeIdList, mesId, groupId, actionTypeMesIdList, mesActionResult, mesActionAmount):
    db = QtGui.qApp.db
    stmt = u'''
        SELECT
        mMV.id AS mesActionId,
        ActionType.id AS actionTypeId,
        ActionType.amount
        FROM ActionType
        INNER JOIN rbService  ON rbService.id = ActionType.nomenclativeService_id
        INNER JOIN mes.mrbService  AS mSV ON rbService.code = mSV.code
        INNER JOIN mes.MES_service AS mMV ON mMV.service_id = mSV.id
        WHERE ActionType.deleted = 0 AND mMV.deleted = 0 AND mSV.deleted = 0 AND ActionType.id IN (%s) AND mMV.master_id = %d AND mSV.group_id = %d
        ORDER BY mSV.code, mSV.name, mSV.id
    ''' % (u','.join(str(actionTypeId) for actionTypeId in actionTypeIdList.keys() if actionTypeId), mesId, groupId)

    query = db.query(stmt)
    while query.next():
        record = query.record()
        actionTypeId = forceRef(record.value('actionTypeId'))
        if actionTypeId and (actionTypeId not in actionTypeMesIdList):
            mesActionId = forceRef(record.value('mesActionId'))
            amount = forceInt(record.value('amount'))
            if mesActionId:
                amountCount, amountCountExecuted = mesActionAmount.get(mesActionId, (0, 0))
                actionIdCount = mesActionResult.get(mesActionId, 0)
                countActionTypeId, actionTypeIdExecuted = actionTypeIdList.get(actionTypeId, (0, 0))
                actionTypeMesIdList.add(actionTypeId)
                mesActionAmount[mesActionId] = (amountCount + (amount * countActionTypeId), amountCountExecuted + (amount * actionTypeIdExecuted))
                mesActionResult[mesActionId] = actionIdCount + countActionTypeId
    return mesActionResult, mesActionAmount, actionTypeMesIdList


def getMesAmountActionTypeAlternative(actionTypeIdList, mesId, groupId, actionTypeMesIdList, mesActionResult, mesActionAmount):
    db = QtGui.qApp.db
    stmt = u'''
        SELECT
        mMV.id AS mesActionId,
        mMV.groupCode AS groupAlternative,
        ActionType.id AS actionTypeId,
        ActionType.amount
        FROM ActionType
        INNER JOIN rbService  ON rbService.id = ActionType.nomenclativeService_id
        INNER JOIN mes.mrbService  AS mSV ON rbService.code = mSV.code
        INNER JOIN mes.MES_service AS mMV ON mMV.service_id = mSV.id
        WHERE ActionType.deleted = 0 AND mMV.deleted = 0 AND mSV.deleted = 0 AND ActionType.id IN (%s) AND mMV.master_id = %d AND mSV.group_id = %d
        GROUP BY mSV.code
        ORDER BY groupAlternative, mSV.code, mSV.name, mSV.id
    ''' % (u','.join(str(actionTypeId) for actionTypeId in actionTypeIdList.keys() if actionTypeId), mesId, groupId)

    query = db.query(stmt)
    groupAlternativeList = {}
    while query.next():
        record = query.record()
        actionTypeId = forceRef(record.value('actionTypeId'))
        if actionTypeId and (actionTypeId not in actionTypeMesIdList):
            mesActionId = forceRef(record.value('mesActionId'))
            amount = forceInt(record.value('amount'))
            groupAlternativeNew = forceRef(record.value('groupAlternative'))
            if mesActionId:
                amountCount, amountCountExecuted, groupAlternative = mesActionAmount.get(mesActionId, (0, 0, None))
                actionIdCount = mesActionResult.get(mesActionId, 0)
                countActionTypeId, actionTypeIdExecuted, eventIdList = actionTypeIdList.get(actionTypeId, (0, 0, []))
                actionTypeMesIdList.add(actionTypeId)
                groupAlternativeCode = groupAlternative if (not groupAlternativeNew and groupAlternative) else groupAlternativeNew
                mesActionAmount[mesActionId] = (amountCount + (amount * countActionTypeId), amountCountExecuted + (amount * actionTypeIdExecuted), groupAlternativeCode, len(eventIdList))
                mesActionResult[mesActionId] = actionIdCount + countActionTypeId
                groupAlternativeCount = groupAlternativeList.get(groupAlternativeCode, 0)
                groupAlternativeList[groupAlternativeCode] = groupAlternativeCount + (1 if (amount * countActionTypeId) > 0 else 0)
    return mesActionResult, mesActionAmount, actionTypeMesIdList, groupAlternativeList


def insertServiceSection(parent, cursor, actionTypeIdList, mesId, title, code, actionMesIdList, actionTypeMesIdList, eventIdSum):
    cursor.movePosition(QtGui.QTextCursor.End)
    cursor.insertBlock()
    cursor.insertBlock()
    db = QtGui.qApp.db
    groupId = forceRef(db.translate('mes.mrbServiceGroup', 'code', code, 'id'))
    if groupId and mesId:
        columns = [
                ('5%',[u'№', u''],    CReportBase.AlignRight),
                ('15%',[u'Код', u''],  CReportBase.AlignLeft),
                ('35%',[title, u''],   CReportBase.AlignLeft),
                ('5%',[u'Группа', u''], CReportBase.AlignLeft),
                ('5%',[u'CK', u''],    CReportBase.AlignRight),
                ('5%',[u'Чп', u''],    CReportBase.AlignRight),
                ('5%',[u'ИП (МЭС)', u''], CReportBase.AlignRight),
                ('5%',[u'сумма услуг', u''], CReportBase.AlignRight),
                ('5%',[u'к-во случаев', u''], CReportBase.AlignRight),
                ('5%',[u'СК (факт)', u''], CReportBase.AlignRight),
                ('5%',[u'ЧП (факт)', u''], CReportBase.AlignRight),
                ('5%',[u'ИП (факт)', u''], CReportBase.AlignRight),
                ]
        table = createTable(cursor, columns)
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 2, 1)
        table.mergeCells(0, 3, 2, 1)
        table.mergeCells(0, 4, 2, 1)
        table.mergeCells(0, 5, 2, 1)
        table.mergeCells(0, 6, 2, 1)
        table.mergeCells(0, 7, 2, 1)
        table.mergeCells(0, 8, 2, 1)
        table.mergeCells(0, 9, 2, 1)
        table.mergeCells(0, 10, 2, 1)
        table.mergeCells(0, 11, 2, 1)
        mesActionResult = {}
        mesActionAmount = {}
        groupAlternativeCodeList = {}
        groupAlternativeList = []
        if actionTypeIdList:
            mesActionResult, mesActionAmount, actionTypeMesIdList, groupAlternativeCodeList = getMesAmountActionTypeAlternative(actionTypeIdList, mesId, groupId, actionTypeMesIdList, mesActionResult, mesActionAmount)
        stmt = '''
            SELECT mrbService.code, mrbService.name, MES_service.averageQnt, MES_service.necessity, mrbService.doctorWTU, mrbService.paramedicalWTU, MES_service.id AS mesServiceId, MES_service.groupCode AS groupAlternative
            FROM mes.mrbService
            LEFT JOIN mes.MES_service ON MES_service.service_id = mrbService.id
            WHERE MES_service.master_id = %d AND MES_service.deleted = 0 AND mrbService.deleted = 0 AND mrbService.group_id = %d
            GROUP BY mrbService.code
            ORDER BY groupAlternative, mrbService.code, mrbService.name, mrbService.id
            ''' % (mesId, groupId)
        query = QtGui.qApp.db.query(stmt)
        prevGroupCode = False
        start = 0
        totalIP_FACT = 0.0
        totalIP_MES = 0.0
        while query.next():
            record = query.record()
            code  = forceString(record.value('code'))
            name  = forceString(record.value('name'))
            averageQnt = forceInt(record.value('averageQnt'))
            necessity = forceDouble(record.value('necessity'))
            groupAlternativeNew = forceInt(record.value('groupAlternative'))
            groupAlternative = groupAlternativeNew
            if necessity >= 1:
                brusColor = Qt.red
                brusColorNecessity = Qt.red
            else:
                brusColor = Qt.lightGray
                brusColorNecessity = Qt.lightGray
            amountCount = 0
            amountCountExecuted = 0
            eventIdCount = 0
            groupAlternativeCodeCount = groupAlternativeCodeList.get(groupAlternative, 0) if groupAlternative else 0
            if mesActionResult and mesActionAmount:
                mesServiceId = forceInt(record.value('mesServiceId'))
                if mesServiceId in mesActionAmount.keys():
                    serviceAmoutCount, executedAmoutCount, groupAlternative, eventIdCount = mesActionAmount.get(mesServiceId, (0, 0, None))
                else:
                    serviceAmoutCount = 0
                    executedAmoutCount = 0,
                serviceIdCount = mesActionResult.get(mesServiceId, 0)
                if serviceIdCount == 0 and (not groupAlternative or not groupAlternativeCodeCount):
                    if necessity >= 1:
                        brusColorNecessity = Qt.red
                        brusColor = Qt.red
                    else:
                        brusColorNecessity = Qt.lightGray
                        brusColor = Qt.lightGray
                elif serviceIdCount > 0 and serviceAmoutCount == averageQnt and (not groupAlternative or (groupAlternative not in groupAlternativeList)):
                    brusColor = Qt.green
                    brusColorNecessity = None
                    amountCount = serviceAmoutCount
                    amountCountExecuted = executedAmoutCount
                elif (serviceIdCount > 0 and serviceAmoutCount != averageQnt) or (serviceIdCount > 0 and serviceAmoutCount == averageQnt and (groupAlternative and groupAlternative in groupAlternativeList)):
                    if necessity >= 1:
                        brusColorNecessity = None
                        brusColor = Qt.red
                    else:
                        brusColorNecessity = None
                        brusColor = Qt.lightGray
                    amountCount = serviceAmoutCount
                    amountCountExecuted = executedAmoutCount
                else:
                    brusColor = Qt.white
                    brusColorNecessity = Qt.white
                if serviceIdCount > 0 and groupAlternative and (groupAlternative not in groupAlternativeList):
                    groupAlternativeList.append(groupAlternative)
#            groupAlternativeCodeCount = groupAlternativeCodeList.get(groupAlternative, 0) if groupAlternative else 0
            brusColorGroupAltirnetive = brusColorNecessity
            if groupAlternativeCodeCount > 1:
                brusColorGroupAltirnetive = Qt.red
            elif groupAlternativeCodeCount == 1:
                brusColorGroupAltirnetive = Qt.green
            i = table.addRow()
            table.setText(i, 0, i-1, None, None, brusColorNecessity)
            table.setText(i, 1, code, None, None, brusColorNecessity)
            table.setText(i, 2, name, None, None, brusColorNecessity)
            if prevGroupCode != groupAlternativeNew:
                prevGroupCode = groupAlternativeNew
                start = i
                table.setText(i, 3, forceString(groupAlternativeNew), None, None, brusColorGroupAltirnetive)
            else:
                table.setText(i, 3, u'', None, None, brusColorNecessity)
                if start:
                    table.mergeCells(start, 3, i-start+1, 1)
            table.setText(i, 4, averageQnt, None, None, brusColorNecessity)
            table.setText(i, 5, '%.2f'%(round(necessity, 2)), None, None, brusColorNecessity)
            IP_MES = round(averageQnt*necessity, 2)
            table.setText(i, 6, '%.2f'%(IP_MES), None, None, brusColor)
            table.setText(i, 7, amountCountExecuted, None, None, brusColor, brusColor if amountCountExecuted == amountCount else Qt.red)
            table.setText(i, 8, eventIdCount, None, None, brusColor)
            SK_FACT = round(amountCountExecuted / float(eventIdCount), 2) if eventIdCount != 0 else 0.0
            table.setText(i, 9, '%.2f'%(SK_FACT), None, None, Qt.green if round(float(averageQnt), 2) == SK_FACT else Qt.red)
            CHP_Fact = round(eventIdCount / float(eventIdSum), 2) if eventIdSum != 0 else 0.0
            table.setText(i, 10, '%.2f'%(CHP_Fact), None, None, Qt.green if round(float(necessity), 2) == CHP_Fact else Qt.red)
            IP_FACT = round(SK_FACT * CHP_Fact, 2)
            table.setText(i, 11, '%.2f'%(IP_FACT), None, None, brusColor)
            totalIP_FACT += IP_FACT
            totalIP_MES += IP_MES
        i = table.addRow()
        table.setText(i, 2, u'ИП(факт) / ИП(МЭС) = %.2f'%(round(totalIP_FACT / totalIP_MES, 2) if totalIP_MES != 0 else 0.0))
        table.setText(i, 6, '%.2f'%(totalIP_MES))
        table.setText(i, 11, '%.2f'%(totalIP_FACT))
    return actionMesIdList, actionTypeMesIdList


def insertServiceNoSection(parent, cursor, actionTypeIdList, actionMesIdList, actionTypeMesIdList, eventIdSum):
    actionTypeNoMESIdList = {}
    for actionTypeId, value in actionTypeIdList.items():
        if actionTypeId not in actionTypeMesIdList:
            actionTypeNoMESIdList[actionTypeId] = value
    if actionTypeNoMESIdList:
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()
        cursor.insertText(u'Услуги выходящие за пределы требования')
        cursor.insertBlock()
        tableColumns = [
                ('5%',[u'№', u''],    CReportBase.AlignRight),
                ('23%',[u'Тип услуги', u'' ],    CReportBase.AlignRight),
                ('10%',[u'Код услуги', u''], CReportBase.AlignLeft),
                ('22%',[u'Название услуги', u''], CReportBase.AlignLeft),
                ('5%',[u'CK', u''],    CReportBase.AlignRight),
                ('5%',[u'Чп', u''],    CReportBase.AlignRight),
                ('5%',[u'ИП (МЭС)', u''], CReportBase.AlignRight),
                ('5%',[u'сумма услуг', u''], CReportBase.AlignRight),
                ('5%',[u'к-во случаев', u''], CReportBase.AlignRight),
                ('5%',[u'СК (факт)', u''], CReportBase.AlignRight),
                ('5%',[u'ЧП (факт)', u''], CReportBase.AlignRight),
                ('5%',[u'ИП (факт)', u''], CReportBase.AlignRight),
                ]
        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 2, 1)
        table.mergeCells(0, 2, 2, 1)
        table.mergeCells(0, 3, 2, 1)
        table.mergeCells(0, 4, 2, 1)
        table.mergeCells(0, 5, 2, 1)
        table.mergeCells(0, 6, 2, 1)
        table.mergeCells(0, 7, 2, 1)
        table.mergeCells(0, 8, 2, 1)
        table.mergeCells(0, 9, 2, 1)
        table.mergeCells(0, 10, 2, 1)
        table.mergeCells(0, 11, 2, 1)
        db = QtGui.qApp.db
        tableService = db.table('rbService')
        tableActionType = db.table('ActionType')
        tableQuery = tableActionType.leftJoin(tableService, tableService['id'].eq(tableActionType['nomenclativeService_id']))
        cols = [tableActionType['id'], tableService['code'].alias('codeService'), tableActionType['name'].alias('nameActionType'), tableService['name'].alias('nameService')]
        records =  db.getRecordList(tableQuery, cols, [tableActionType['id'].inlist(actionTypeNoMESIdList), tableActionType['deleted'].eq(0)])
        actionNoMESList = {}
        actionDistinctIdList = []
        for record in records:
            actionTypeId  = forceRef(record.value('id'))
            if actionTypeId and (actionTypeId not in actionDistinctIdList):
                actionDistinctIdList.append(actionTypeId)
                nameActionType  = forceString(record.value('nameActionType'))
                codeService = forceString(record.value('codeService'))
                nameService = forceString(record.value('nameService'))
                actionNoMES = actionNoMESList.get(actionTypeId, None)
                amountCount, countActionTypeNoMES, eventIdList = actionTypeNoMESIdList.get(actionTypeId, (0, 0, []))
                if actionNoMES:
                    actionNoMESList[actionTypeId] = (actionNoMES[0] + countActionTypeNoMES, nameActionType, codeService, nameService, len(eventIdList))
                else:
                    actionNoMESList[actionTypeId] = (countActionTypeNoMES, nameActionType, codeService, nameService, len(eventIdList))
        totalIP_FACT = 0.0
        totalIP_MES = 0.0
        for key, item in actionNoMESList.items():
            i = table.addRow()
            table.setText(i, 0, i-1, None, None, Qt.red)
            table.setText(i, 1, item[1], None, None, Qt.red)
            table.setText(i, 2, item[2], None, None, Qt.red)
            table.setText(i, 3, item[3], None, None, Qt.red)
            table.setText(i, 4, 0, None, None, Qt.red)
            table.setText(i, 5, 0, None, None, Qt.red)
            table.setText(i, 6, 0, None, None, Qt.red)
            table.setText(i, 7, item[0], None, None, Qt.red)
            table.setText(i, 8, item[4], None, None, Qt.red)
            SK_FACT = round(item[0] / float(item[4]), 2) if item[4] != 0 else 0.0
            table.setText(i, 9, '%.2f'%(SK_FACT), None, None, Qt.red)
            CHP_Fact = round(item[4] / float(eventIdSum), 2) if eventIdSum != 0 else 0.0
            table.setText(i, 10, '%.2f'%(CHP_Fact), None, None, Qt.red)
            IP_FACT = round(SK_FACT * CHP_Fact, 2)
            table.setText(i, 11, '%.2f'%(IP_FACT), None, None, Qt.red)
            totalIP_FACT += IP_FACT
        i = table.addRow()
        table.setText(i, 3, u'ИП(факт) / ИП(МЭС) = %.2f'%(round(totalIP_FACT / totalIP_MES, 2) if totalIP_MES != 0 else 0.0))
        table.setText(i, 6, '%.2f'%(totalIP_MES))
        table.setText(i, 11, '%.2f'%(totalIP_FACT))


def insertMedicamentsSection(cursor, mesId):
    cursor.movePosition(QtGui.QTextCursor.End)
    cursor.insertBlock()
    cursor.insertBlock()
    cursor.insertText(u'Лекарственные средства (МНН) в официнальной дозировке')
    cursor.insertBlock()
    columns = [
            ('5%',[u'№'],             CReportBase.AlignRight),
            ('15%',[u'Код'],          CReportBase.AlignLeft),
            ('70%',[u'Наименование'], CReportBase.AlignLeft),
            ('5%',[u'СЧЕ'],           CReportBase.AlignRight),
            ('5%',[u'Чн'],            CReportBase.AlignRight),
            ]
    table = createTable(cursor, columns)
    stmt = '''
        SELECT MES_medicament.medicamentCode as code, MES_medicament.dosage, MES_medicament.averageQnt, MES_medicament.necessity,
               mrbMedicamentDosageForm.name AS formName,
               mrbMedicament.name AS name, mrbMedicament.form AS medicamentForm, mrbMedicament.dosage AS medicamentDosage,
               G1.name AS groupName,
               G2.name AS subgroupName
        FROM mes.MES_medicament
        LEFT JOIN mes.mrbMedicamentDosageForm ON mrbMedicamentDosageForm.id = MES_medicament.dosageForm_id
        LEFT JOIN mes.mrbMedicament ON mrbMedicament.code = MES_medicament.medicamentCode
        LEFT JOIN mes.mrbMedicamentGroup AS G1 ON G1.code = SUBSTRING_INDEX(MES_medicament.medicamentCode, '.', 1)
        LEFT JOIN mes.mrbMedicamentGroup AS G2 ON G2.code = SUBSTRING_INDEX(MES_medicament.medicamentCode, '.', 2)
        WHERE MES_medicament.master_id=%d AND MES_medicament.deleted = 0 AND mrbMedicament.deleted = 0 AND mrbMedicamentDosageForm.deleted = 0 AND G1.deleted = 0 AND G2.deleted = 0
        ORDER BY MES_medicament.medicamentCode, mrbMedicament.name
        ''' % mesId
    query = QtGui.qApp.db.query(stmt)
    row = 0
    while query.next():
        row += 1
        record = query.record()
        groupName = forceString(record.value('groupName'))
        subgroupName = forceString(record.value('subgroupName'))
        code  = forceString(record.value('code'))
        name  = forceString(record.value('name'))
        averageQnt = forceInt(record.value('averageQnt'))
        necessity = forceDouble(record.value('necessity'))
        i = table.addRow()
        table.setText(i, 0, row)
        table.setText(i, 1, u'Группа')
        table.setText(i, 2, groupName)
        i = table.addRow()
        table.setText(i, 1, u'Подгруппа')
        table.setText(i, 2, subgroupName)
        i = table.addRow()
        table.setText(i, 1, code)
        table.setText(i, 2, name)
        table.setText(i, 3, averageQnt)
        table.setText(i, 4, necessity)
        table.mergeCells(i-2, 0, 3, 1)
        table.mergeCells(i-2, 2, 1, 3)
        table.mergeCells(i-1, 2, 1, 3)


class CAnalyticsExecutionMesDialog(QtGui.QDialog, Ui_AnalyticsExecutionMesDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.edtAgeFrom.setValue(0)
        self.edtAgeTo.setValue(150)


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.cmbMes.setValue(params.get('mesId', None))
        self.edtAgeFrom.setValue(params.get('ageFrom', 0))
        self.edtAgeTo.setValue(params.get('ageTo', 0))
        self.cmbSex.setCurrentIndex(params.get('sex', 0))
        self.cmbCompulsoryPolisCompany.setValue(params.get('compulsoryPolisCompany', 0))
        self.cmbRegRegion.setCode(params.get('regRegion', None))
        self.cmbLogRegion.setCode(params.get('logRegion', None))


    def params(self):
        params = {}
        params['begDate']     = self.edtBegDate.date()
        params['endDate']     = self.edtEndDate.date()
        params['mesId']       = self.cmbMes.value()
        params['ageFrom']     = self.edtAgeFrom.value()
        params['ageTo']       = self.edtAgeTo.value()
        params['sex']         = self.cmbSex.currentIndex()
        params['compulsoryPolisCompany'] = self.cmbCompulsoryPolisCompany.value()
        params['regRegion'] = self.cmbRegRegion.code()
        params['logRegion'] = self.cmbLogRegion.code()

        return params
