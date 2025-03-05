# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2024 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignature, QDate

from library.database import addDateInRange
from library.Utils import (calcAgeInYears,
                            forceBool,
                            forceDate,
                            forceInt,
                            forceRef,
                            forceString,
                            trim)
from library.DialogBase import CDialogBase

from Orgs.Utils import getOrgStructureDescendants

from RefBooks.TempInvalidState import CTempInvalidState
from Reports.Report import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.ReportView import CPageFormat


def selectData(params):
    begDate = params.get('begDate', QDate())
    endDate = params.get('endDate', QDate())
    doctype = params.get('doctype', 0)
    tempInvalidReasonId = params.get('tempInvalidReason', None)
    onlyClosed = params.get('onlyClosed', True)
    orgStructureId = params.get('orgStructureId', None)
    personId = params.get('personId', None)
    insuranceOfficeMark = params.get('insuranceOfficeMark', 0)
    hasRegAddress = params.get('hasRegAddress', True)
    hasLocAddress = params.get('hasLocAddress', True)
    dateSort = params.get('dateSort', 0)
    isClientNameSort = params.get('isClientNameSort', False)
    isDateSort = params.get('isDateSort', False)
    isNumberSort = params.get('isNumberSort', False)
    byPeriodIssueDate = params.get('byPeriodIssueDate', 0)
    isNoExternal = params.get('isNoExternal', True)

    stmt="""
SELECT
   CONCAT_WS(_utf8' ', Client.lastName, Client.firstName, Client.patrName, CAST(Client.id AS CHAR)) AS clientName,
   Client.birthDate,
   Client.id AS clientId,
   TempInvalidDocument.id AS tempInvalidDocumentId,
   TempInvalidDocument.number,
   TempInvalidDocument.prevNumber,
   TempInvalidDocument.placeWork,
   TempInvalidDocument.busyness,
   TempInvalidDocument.duplicate,
   TempInvalidDocument.electronic,
   TempInvalidDocument.issueDate,
   TempInvalid.diagnosis_id,
   TempInvalid.receiver_id,
   TempInvalidDocument.person_id AS begPersonId,
   TempInvalidDocument.execPerson_id AS endPersonId,
   vrbPersonWithSpeciality.name AS personName,
   TempInvalidDocument.isExternal,

   (SELECT TID.isExternal
   FROM TempInvalidDocument TID
   WHERE TempInvalidDocument.prevNumber = TID.number LIMIT 1) AS isExternalPrev,

   IF((SELECT TD.prev_id
   FROM TempInvalidDocument AS TD
   WHERE TD.id = TempInvalidDocument.prev_id AND TD.deleted = 0) IS NOT NULL, 1, 0) AS isPreviousPrevId,

   TempInvalidDocument.idx,

   (SELECT CONCAT_WS(\' - \', D.MKB, D_MKB.DiagName)
   FROM TempInvalid_Period
   INNER JOIN Diagnosis AS D ON D.id = TempInvalid_Period.diagnosis_id
   INNER JOIN MKB AS D_MKB ON D_MKB.DiagID = D.MKB
   WHERE TempInvalid_Period.master_id = TempInvalid.id
   AND D.deleted = 0
   ORDER BY TempInvalid_Period.begDate ASC
   LIMIT 1) AS MKBFirstPeriod,

   IF(TempInvalid.state = 3, 1, 0) AS closedExternal,
   TempInvalid.caseBegDate,
   TempInvalid.begDate,
   %s,
   TempInvalid.age AS tage,
   TempInvalid.state,
   TempInvalid.id AS tempInvalidId,
   DATEDIFF(TempInvalid.endDate, TempInvalid.begDate)+1 AS duration,
   MKB.DiagID AS MKB,
   MKB.DiagName,
   IF(rbTempInvalidReason.grouping = 1 AND TempInvalid.type != 1, 1, 0) AS requiredOtherPerson,
   formatClientAddress(ClientAddress.id) AS address

   FROM TempInvalid
   INNER JOIN TempInvalidDocument ON TempInvalidDocument.master_id = TempInvalid.id
   LEFT JOIN TempInvalid AS NextTempInvalid ON (TempInvalid.id = NextTempInvalid.prev_id AND NextTempInvalid.deleted = 0)
   LEFT JOIN Diagnosis ON (Diagnosis.id = TempInvalid.diagnosis_id AND Diagnosis.deleted = 0)
   LEFT JOIN MKB ON MKB.DiagID = IFNULL(
        (SELECT TID_C.MKB
        FROM TempInvalidDocument_Care TID_C
        WHERE TID_C.master_id = TempInvalidDocument.id
        LIMIT 1), Diagnosis.MKB)
   LEFT JOIN rbTempInvalidReason ON rbTempInvalidReason.id = TempInvalid.tempInvalidReason_id
   LEFT JOIN vrbPersonWithSpeciality ON vrbPersonWithSpeciality.id = TempInvalid.person_id
   LEFT JOIN Client ON Client.id = TempInvalid.client_id
   LEFT JOIN ClientAddress ON
        ClientAddress.client_id = Client.id AND ClientAddress.deleted = 0 AND
        ClientAddress.id = (SELECT MAX(id) FROM ClientAddress AS CA WHERE CA.Type=%d AND CA.client_id = Client.id)
WHERE
   Client.deleted = 0 AND TempInvalidDocument.deleted = 0 AND
   %s
ORDER BY %s
    """
    db = QtGui.qApp.db
    table = db.table('TempInvalid')
    tableTempInvalidDocument = db.table('TempInvalidDocument')
    cond = []
    if doctype:
        cond.append(table['doctype_id'].eq(doctype))
    else:
        cond.append(table['type'].eq(0))
    cond.append(table['deleted'].eq(0))
    if isNoExternal:
        cond.append(tableTempInvalidDocument['isExternal'].eq(0))
        colsIsExternalPrev = u'''    TempInvalid.endDate AS endDate'''
    else:
        colsIsExternalPrev = u'''   IF(TempInvalidDocument.isExternal = 1,
                                       (SELECT TempInvalid_Period.endDate
                                        FROM TempInvalid_Period
                                        WHERE TempInvalid_Period.isExternal > 0 AND TempInvalid_Period.master_id = TempInvalid.id
                                        ORDER BY TempInvalid_Period.endDate DESC
                                        LIMIT 1), TempInvalid.endDate) AS endDate'''

    if tempInvalidReasonId:
        cond.append(table['tempInvalidReason_id'].eq(tempInvalidReasonId))
    if byPeriodIssueDate == 1:
        cond.append(table['caseBegDate'].le(endDate))
        cond.append(table['endDate'].ge(begDate))
    elif byPeriodIssueDate == 2:
        addDateInRange(cond, tableTempInvalidDocument['issueDate'], begDate, endDate)
    else:
        addDateInRange(cond, table['endDate'], begDate, endDate)
    if onlyClosed:
        cond.append(table['state'].eq(CTempInvalidState.closed))
    if orgStructureId:
        tablePerson = db.table('vrbPersonWithSpeciality')
        cond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureDescendants(orgStructureId)))
    if personId:
        cond.append(table['person_id'].eq(personId))
    if insuranceOfficeMark in (1, 2):
        cond.append(table['insuranceOfficeMark'].eq(insuranceOfficeMark-1))
    order = []
    if isDateSort:
        if dateSort == 0: # по дате начала случая
            order.append(u'TempInvalid.begDate')
        elif dateSort == 1: # по дате начала лн
            order.append(u'TempInvalid.caseBegDate')
        elif dateSort == 2: # по дате выдачи
            order.append(u'TempInvalidDocument.issueDate')
    if isClientNameSort:
        order.append(u'Client.lastName, Client.firstName, Client.patrName')
    if isNumberSort:
        order.append(u'TempInvalidDocument.number')
    order.append(u'TempInvalidDocument.busyness, TempInvalidDocument.duplicate')
    return db.query(stmt % (colsIsExternalPrev,
                            0 if hasRegAddress else (1 if hasLocAddress else 0),
                            db.joinAnd(cond),
                            u','.join(order)))


def getClientRelation(tempInvalidId, hasRegAddress, hasLocAddress):
    stmt = u'''SELECT DISTINCT CONCAT_WS(_utf8' ', Client.lastName, Client.firstName, Client.patrName, CAST(Client.id AS CHAR)) AS clientReceiverName,
       Client.birthDate AS birthDateReceiver,
       getClientLocAddress(Client.id) AS receiveraddress,
       CONCAT_WS(_utf8' - ', rbRelationType.leftName, rbRelationType.rightName) AS relation
FROM TempInvalid
    INNER JOIN TempInvalidDocument ON TempInvalidDocument.master_id = TempInvalid.id
    INNER JOIN TempInvalidDocument_Care ON TempInvalidDocument.id = TempInvalidDocument_Care.master_id
    INNER JOIN Client ON TempInvalidDocument_Care.client_id = Client.id
    JOIN ClientRelation
    INNER JOIN rbRelationType AS rbRelationType ON rbRelationType.id = ClientRelation.relativeType_id
WHERE TempInvalid.id = %d AND TempInvalidDocument.deleted = 0 AND Client.deleted = 0 AND TempInvalid.deleted = 0
    AND ClientRelation.deleted = 0
    AND ((ClientRelation.relative_id = TempInvalid.client_id AND ClientRelation.client_id = Client.id)
    OR (ClientRelation.client_id = TempInvalid.client_id AND ClientRelation.relative_id = Client.id))
                '''%(tempInvalidId)
    return QtGui.qApp.db.query(stmt)


def getBegDateAfterExternal(tempInvalidId, documentIdx):
    stmt = 'SELECT begDate FROM TempInvalid_Period WHERE master_id = %d LIMIT %d, 1' % (tempInvalidId, documentIdx)
    query = QtGui.qApp.db.query(stmt)
    if query.next():
        return forceDate(query.value(0))
    return None



class CTempInvalidBookF036(CReport):
    name = u'КНИГА РЕГИСТРАЦИИ ЛИСТКОВ НЕТРУДОСПОСОБНОСТИ (Ф.036)'

    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(self.name)
        self.orientation = CPageFormat.Landscape


    def getSetupDialog(self, parent):
        result = CTempInvalidF036SetupDialog(parent)
        result.setTitle(self.title())
        result.setCntUserVisible(True)
        result.setTempInvalidDuplicateVisible(True)
        result.setTempInvalidDuplicateWorkVisible(True)
        result.setClientNameSortVisible(True)
        result.setDateSortVisible(True)
        return result


    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.name)
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        showTempInvalidReceiver    = params.get('showTempInvalidReceiver', 0)
        isTempInvalidDuplicate     = params.get('isTempInvalidDuplicate', False)
        isTempInvalidDuplicateWork = params.get('isTempInvalidDuplicateWork', False)
        hasRegAddress              = params.get('hasRegAddress', True)
        hasLocAddress              = params.get('hasLocAddress', True)
        showMKBDescription         = params.get('showMKBDescription', True)
        showPersonSpeciality       = params.get('showPersonSpeciality', True)
        isNoExternal               = params.get('isNoExternal', True)
        showTempInvalidStatus      = params.get('showTempInvalidStatus', False)
        cursor.insertBlock()
        tableColumns = [
            ('2%', [u'N N п/п', u'', u''], CReportBase.AlignCenter),
            ('5%', [u'N листка нетрудоспособности, выданного данным леч. учреждением', u'первый', u''], CReportBase.AlignCenter),
            ('5%', [u'', u'продолжение', u''], CReportBase.AlignCenter),
            ('5%', [u'N листка нетрудоспособности, выданного другим учреждением', u'первый', u''], CReportBase.AlignCenter),
            ('5%', [u'', u'продолжение', u''], CReportBase.AlignCenter),
            ('5%', [u'Дата выдачи', u'', u''], CReportBase.AlignLeft),
            ('9%', [u'Фамилия, имя, отчество получателя/больного', u'', u''], CReportBase.AlignLeft),
            ('3%', [u'Возраст', u'', u''], CReportBase.AlignCenter),
            ('9%', [u'Адрес получателя/больного', u'', u''], CReportBase.AlignLeft),
            ('5%', [u'Место работы и выполняемая работа', u'', u''], CReportBase.AlignLeft),
            ('8%', [u'Диагноз', u'первичный', u''], CReportBase.AlignLeft),
            ('8%', [u'', u'заключительный', u''], CReportBase.AlignLeft),
            ('5%', [u'Фамилия врача', u'выдавшего листок нетрудоспособности', u''], CReportBase.AlignLeft),
            ('5%', [u'', u'закончившего листок нетрудоспособности', u''], CReportBase.AlignLeft),
            ('8%', [u'Освобожден от работы', u'с какого числа', u''], CReportBase.AlignCenter),
            ('8%', [u'', u'по какое число', u''], CReportBase.AlignCenter),
            ('5%', [u'Всего календарных дней освобождения от работы', u'', u''], CReportBase.AlignCenter),
            ('5%', [u'Отметка о направлении больного в другие лечебные учреждения', u'', u''], CReportBase.AlignLeft),
            ('5%', [u'Результат', u'', u''], CReportBase.AlignLeft),
        ]

        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 2, 1)
        table.mergeCells(0, 1, 1, 2)
        table.mergeCells(0, 3, 1, 2)
        table.mergeCells(0, 5, 2, 1)
        table.mergeCells(0, 6, 2, 1)
        table.mergeCells(0, 7, 2, 1)
        table.mergeCells(0, 8, 2, 1)
        table.mergeCells(0, 9, 2, 1)
        table.mergeCells(0, 10, 1, 2)
        table.mergeCells(0, 12, 1, 2)
        table.mergeCells(0, 14, 1, 2)
        table.mergeCells(0, 16, 2, 1)
        table.mergeCells(0, 17, 2, 1)
        if showTempInvalidStatus:
            table.mergeCells(0, 18, 2, 1)

        cnt = params.get('cntUser', 1)
        db = QtGui.qApp.db
        query = selectData(params)
        tempInvalidDocumentIdList = []
        tempInvalidDuplicateIdList = []
        clientMergeData = {}
        # busynessData = {}
        i = 0
        while query.next():
            record   = query.record()
            tempInvalidDocumentId = forceRef(record.value('tempInvalidDocumentId'))
            busyness = forceInt(record.value('busyness'))
            busynessType = [u'', u'основное', u'совместитель', u'на учете'][busyness]
            duplicate = forceBool(record.value('duplicate'))
            placeWork = forceString(record.value('placeWork')) + u', ' + busynessType
            number = forceString(record.value('number'))
            electronic = forceBool(record.value('electronic'))
            if electronic:
                number += u'\n(электронный)'
            clientName = forceString(record.value('clientName'))
            isExternalPrev = forceBool(record.value('isExternalPrev'))
            isExternal = forceBool(record.value('isExternal'))
            tempInvalidId = forceRef(record.value('tempInvalidId'))
            documentIdx = forceInt(record.value('idx'))
            begDateAfterExternal = getBegDateAfterExternal(tempInvalidId, documentIdx)
            # prevId = forceRef(record.value('prev_id'))
            caseBegDate = forceDate(record.value('caseBegDate'))
            clientId = forceRef(record.value('clientId'))
            prevNumber = forceString(record.value('prevNumber'))
            isPreviousPrevId = forceBool(record.value('isPreviousPrevId'))
            issueDate = forceString(record.value('issueDate'))
            age = calcAgeInYears(forceDate(record.value('birthDate')), caseBegDate)
            address = forceString(record.value('address'))
            # prevBusynessRow = busynessData.get(clientId, 2)

            if tempInvalidDocumentId and tempInvalidDocumentId not in tempInvalidDocumentIdList and not duplicate:
                tempInvalidDocumentIdList.append(tempInvalidDocumentId)
                if busyness == 2 and tempInvalidDocumentId not in tempInvalidDuplicateIdList:
                    tempInvalidDuplicateIdList.append(tempInvalidDocumentId)
                MKB = forceString(record.value('MKB'))
                DiagName = forceString(record.value('DiagName'))
                endDateTempInvalid = forceDate(record.value('endDate'))
                begDate = forceDate(record.value('begDate'))
                closedExternal = forceBool(record.value('closedExternal'))
                duration = abs(endDateTempInvalid.toJulianDay() - (begDateAfterExternal if (isExternal and not isNoExternal) else begDate).toJulianDay()) + 1
                begPersonId = forceRef(record.value('begPersonId'))
                endPersonId = forceRef(record.value('endPersonId'))

                if showPersonSpeciality:
                    begPersonName = forceString(db.translate('vrbPersonWithSpeciality', 'id', begPersonId, 'name')) if begPersonId else u''
                    endPersonName = forceString(db.translate('vrbPersonWithSpeciality', 'id', endPersonId, 'name')) if endPersonId else u''
                else:
                    begPersonName = forceString(db.translate('vrbPerson', 'id', begPersonId, 'name')) if begPersonId else u''
                    endPersonName = forceString(db.translate('vrbPerson', 'id', endPersonId, 'name')) if endPersonId else u''
                state = forceInt(record.value('state'))
                MKBFirstPeriod = forceString(record.value('MKBFirstPeriod'))
                i = table.addRow()
                table.setText(i, 0, cnt if not isExternal else u'-')
                if not isExternal:
                    if isExternalPrev:
                        table.setText(i, 2, number)
                        table.setText(i, 3, prevNumber)
                    elif isPreviousPrevId or trim(prevNumber):
                        table.setText(i, 1, prevNumber)
                        table.setText(i, 2, number)
                    else:
                        table.setText(i, 1, number)
                elif not isNoExternal:
                    table.setText(i, 3, number)
                    table.setText(i, 4, prevNumber)
                table.setText(i, 5, issueDate)

                if showTempInvalidReceiver == 0:
                    table.setText(i, 6, clientName)
                    table.setText(i, 7, forceString(age))
                    table.setText(i, 8, address)
                elif showTempInvalidReceiver == 1:
                    ageReceiver = u''
                    clientReceiverName = u''
                    receiveraddress = u''
                    if forceBool(record.value('requiredOtherPerson')) and tempInvalidId:
                        records = getClientRelation(tempInvalidId, hasRegAddress, hasLocAddress)
                        while records.next():
                            recordRL = records.record()
                            birthDateReceiver = forceDate(recordRL.value('birthDateReceiver'))
                            ageReceiver += (u' / ' + forceString(calcAgeInYears(birthDateReceiver, caseBegDate))) if birthDateReceiver else ''
                            relation = forceString(recordRL.value('relation'))
                            nameCR = forceString(recordRL.value('clientReceiverName'))
                            clientReceiverName += (u' / ' + nameCR if nameCR else u'') + ((', ' + relation) if relation else u'')
                            addressCR = forceString(recordRL.value('receiveraddress'))
                            receiveraddress += (u' / ' + addressCR) if addressCR else u''
                    table.setText(i, 6, clientName + clientReceiverName)
                    table.setText(i, 7, forceString(age) + ageReceiver)
                    table.setText(i, 8, address + receiveraddress)
                elif showTempInvalidReceiver == 2:
                    table.setText(i, 6, clientName)
                    table.setText(i, 7, forceString(age))
                    receiverId = forceRef(record.value('receiver_id'))
                    if receiverId:
                        query = QtGui.qApp.db.query('SELECT getClientLocAddress(%d)' % receiverId)
                        if query.next():
                            table.setText(i, 8, forceString(query.value(0)))

                table.setText(i, 9, placeWork)
                if showMKBDescription:
                    table.setText(i, 10, MKBFirstPeriod if MKBFirstPeriod else ((MKB + u' - ' + DiagName) if (MKB and DiagName) else u''))
                else:
                    table.setText(i, 10, MKBFirstPeriod if MKBFirstPeriod else ((MKB) if (MKB) else u''))
                if showMKBDescription:
                    table.setText(i, 11, (MKB + u' - ' + DiagName) if (MKB and DiagName) else u'')
                else:
                    table.setText(i, 11, (MKB) if (MKB) else u'')
                table.setText(i, 12, begPersonName)
                table.setText(i, 13, endPersonName if state !=CTempInvalidState.opened  else u'')
                table.setText(i, 14, begDateAfterExternal.toString('dd.MM.yyyy') if begDateAfterExternal else u'')
                table.setText(i, 15, (endDateTempInvalid.toString('dd.MM.yyyy') if endDateTempInvalid else u'') if state else u'')
                table.setText(i, 16, duration)
                table.setText(i, 17, u'Направлен в другое лечебное учреждение' if closedExternal else u'')
                table.setText(i, 18, CTempInvalidState.names[state])
                cnt += 1 if not isExternal else 0
                row, countRow = clientMergeData.get(clientId, (i, 0))
                clientMergeData[clientId] = (i, countRow + 1)
                # busynessData[clientId] = i
            if (isTempInvalidDuplicate or isTempInvalidDuplicateWork) and tempInvalidDocumentId and tempInvalidDocumentId not in tempInvalidDuplicateIdList:
                if isTempInvalidDuplicateWork and isTempInvalidDuplicate:
                    isDuplicate = bool(duplicate or busyness == 2)
                elif isTempInvalidDuplicateWork:
                    isDuplicate = duplicate
                elif isTempInvalidDuplicate:
                    isDuplicate = bool(not duplicate and busyness == 2)
                else:
                    isDuplicate = False
                if isDuplicate:
                    tempInvalidDuplicateIdList.append(tempInvalidDocumentId)
                    i = table.addRow()
                    table.setText(i, 0, cnt if not isExternal else u'-')
                    if duplicate:
                        number += u'\n(дубликат)'
                    if not isExternal:
                        if isExternalPrev:
                            table.setText(i, 2, number)
                            table.setText(i, 3, prevNumber)
                        elif isPreviousPrevId or trim(prevNumber):
                            table.setText(i, 1, prevNumber)
                            table.setText(i, 2, number)
                        else:
                            table.setText(i, 1, number)
                    elif not isNoExternal:
                        table.setText(i, 3, number)
                        table.setText(i, 4, prevNumber)
                    table.setText(i, 9, placeWork)
                    cnt += 1 if not isExternal else 0
                    row, countRow = clientMergeData.get(clientId, (i, 0))
                    if countRow > 0 and (row + countRow) == i:
                        for col in range(6, 19 if showTempInvalidStatus else 18):
                            if col != 9:
                                table.mergeCells(row, col, countRow + 1, 1)
                    else:
                        duration = forceInt(record.value('duration'))
                        MKB = forceString(record.value('MKB'))
                        DiagName = forceString(record.value('DiagName'))
                        endDateTempInvalid = forceDate(record.value('endDate'))
                        begDate = forceDate(record.value('begDate'))
                        closedExternal = forceBool(record.value('closedExternal'))
                        begPersonId = forceRef(record.value('begPersonId'))
                        begPersonName = forceString(db.translate('vrbPersonWithSpeciality', 'id', begPersonId, 'name')) if begPersonId else u''
                        endPersonId = forceRef(record.value('endPersonId'))
                        endPersonName = forceString(db.translate('vrbPersonWithSpeciality', 'id', endPersonId, 'name')) if endPersonId else u''
                        state = forceBool(record.value('state'))
                        MKBFirstPeriod = forceString(record.value('MKBFirstPeriod'))
                        table.setText(i, 5, issueDate)
                        table.setText(i, 6, (clientName + clientReceiverName) if (showTempInvalidReceiver == 1 and clientReceiverName) else clientName)
                        table.setText(i, 7, (forceString(age) + ageReceiver) if (showTempInvalidReceiver == 1 and ageReceiver) else forceString(age))
                        table.setText(i, 8, (address + receiveraddress) if (showTempInvalidReceiver == 1 and receiveraddress) else address)
                        if showMKBDescription:
                            table.setText(i, 10, MKBFirstPeriod if MKBFirstPeriod else ((MKB + u' - ' + DiagName) if (MKB and DiagName) else u''))
                        else:
                            table.setText(i, 10, MKBFirstPeriod if MKBFirstPeriod else ((MKB) if (MKB) else u''))
                        if showMKBDescription:
                            table.setText(i, 11, (MKB + u' - ' + DiagName) if (MKB and DiagName) else u'')
                        else:
                            table.setText(i, 11, (MKB) if (MKB) else u'')
                        table.setText(i, 12, begPersonName)
                        table.setText(i, 13, endPersonName if state else u'')
                        table.setText(i, 14, begDate.toString('dd.MM.yyyy') if begDate else u'')
                        table.setText(i, 15, (endDateTempInvalid.toString('dd.MM.yyyy') if endDateTempInvalid else u'') if state else u'')
                        table.setText(i, 16, duration)
                        table.setText(i, 17, u'Направлен в другое лечебное учреждение' if closedExternal else u'')
                        table.setText(i, 18, CTempInvalidState.names[state])
                    clientMergeData[clientId] = (row, countRow + 1)

        if not showTempInvalidStatus:
            table.table.removeColumns(18, 1)
        if params.get('dateSort') != 2:
            table.table.removeColumns(5, 1)
        # нумерация столбцов в заголовке
        for i in xrange(table.colCount()):
            table.setText(2, i, str(i+1), charFormat=CReportBase.TableHeader, blockFormat=CReportBase.AlignCenter)

        return doc


from Reports.Ui_TempInvalidF036Setup import Ui_TempInvalidF036SetupDialog

class CTempInvalidF036SetupDialog(CDialogBase, Ui_TempInvalidF036SetupDialog):
    def __init__(self, parent=None):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.setAnalysisMode(False)
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())
        filter = 'type=0'
        self.cmbDoctype.setTable('rbTempInvalidDocument', True, filter)
        self.cmbReason.setTable('rbTempInvalidReason', True, filter)
        self.cmbSocStatusType.setTable('vrbSocStatusType', True)
        self.setCntUserVisible(False)
        self.setTempInvalidDuplicateVisible(False)
        self.setTempInvalidDuplicateWorkVisible(False)
        self.setClientNameSortVisible(False)
        self.setDateSortVisible(False)


    def setCntUserVisible(self, value):
        self.isCntUserVisible = value
        self.lblCntUser.setVisible(value)
        self.edtCntUser.setVisible(value)


    def setTempInvalidDuplicateVisible(self, value):
        self.isTempInvalidDuplicateVisible = value
        self.chkTempInvalidDuplicate.setVisible(value)


    def setTempInvalidDuplicateWorkVisible(self, value):
        self.isTempInvalidDuplicateWorkVisible = value
        self.chkTempInvalidDuplicateWork.setVisible(value)


    def setClientNameSortVisible(self, value):
        self.clientNameSortVisible = value
        self.chkClientNameSort.setVisible(value)


    def setDateSortVisible(self, value):
        self.dateSortVisible = value
        self.chkDateSort.setVisible(value)
        self.cmbDateSort.setVisible(value)


    def setTitle(self, title):
        self.setWindowTitle(title)


    def setAnalysisMode(self, mode=True):
        for widget in (self.lblDuration, self.frmDuration,
                       self.lblSex,      self.frmSex,
                       self.lblAge,      self.frmAge,
                       self.lblSocStatusClass, self.cmbSocStatusClass,
                       self.lblSocStatusType,  self.cmbSocStatusType,
                       self.lblMKB,      self.frmMKB,
                      ):
            widget.setVisible(mode)
        self.analysisMode = True


    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate()))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.cmbPeriodIssueDate.setCurrentIndex(params.get('byPeriodIssueDate', 0))
        self.cmbDoctype.setValue(params.get('doctype', None))
        self.cmbReason.setValue(params.get('tempInvalidReason', None))
        self.chkOnlyClosed.setChecked(params.get('onlyClosed', True))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        self.cmbPerson.setValue(params.get('personId', None))
        self.edtDurationFrom.setValue(params.get('durationFrom', 0))
        self.edtDurationTo.setValue(params.get('durationTo', 0))
        self.cmbSex.setCurrentIndex(params.get('sex', 0))
        self.edtAgeFrom.setValue(params.get('ageFrom', 0))
        self.edtAgeTo.setValue(params.get('ageTo', 150))
        self.cmbSocStatusClass.setValue(params.get('socStatusClassId', None))
        self.cmbSocStatusType.setValue(params.get('socStatusTypeId', None))
        MKBFilter = params.get('MKBFilter', 0)
        self.cmbMKBFilter.setCurrentIndex(MKBFilter if MKBFilter else 0)
        self.edtMKBFrom.setText(params.get('MKBFrom', 'A00'))
        self.edtMKBTo.setText(params.get('MKBTo',   'Z99.9'))
        self.chkShowMKBDescription.setChecked(params.get('showMKBDescription', True))
        self.chkShowPersonSpeciality.setChecked(params.get('showPersonSpeciality', True))
        self.cmbInsuranceOfficeMark.setCurrentIndex(params.get('insuranceOfficeMark', 0))
        self.chkAverageDuration.setChecked(params.get('averageDuration', False))
        self.chkResultsForGroups.setChecked(params.get('resultsForGroups', False))
        self.chkRegAddress.setChecked(params.get('hasRegAddress', True))
        self.chkLocAddress.setChecked(params.get('hasLocAddress', True))
        self.chkBeginPerson.setChecked(params.get('hasBeginPerson', True))
        self.chkEndPerson.setChecked(params.get('hasEndPerson', True))
        self.chkPlaceWork.setChecked(params.get('placeWork', True))
        self.cmbShowTempInvalidReceiver.setCurrentIndex(params.get('showTempInvalidReceiver', 0))
        if self.isCntUserVisible:
            self.edtCntUser.setValue(params.get('cntUser', 1))
        if self.isTempInvalidDuplicateVisible:
            self.chkTempInvalidDuplicate.setChecked(params.get('isTempInvalidDuplicate', False))
        if self.isTempInvalidDuplicateWorkVisible:
            self.chkTempInvalidDuplicateWork.setChecked(params.get('isTempInvalidDuplicateWork', False))
        if self.clientNameSortVisible:
            self.chkClientNameSort.setChecked(params.get('isClientNameSort', False))
        if self.dateSortVisible:
            self.chkDateSort.setChecked(params.get('isDateSort', False))
            if self.chkDateSort.isChecked():
                self.cmbDateSort.setCurrentIndex(params.get('dateSort', 0))
        self.chkNumberSort.setChecked(params.get('isNumberSort', False))
        self.chkTempInvalidNoExternal.setChecked(params.get('isNoExternal', True))
        self.chkShowTempInvalidStatus.setChecked(params.get('showTempInvalidStatus', False))


    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['byPeriodIssueDate'] = self.cmbPeriodIssueDate.currentIndex()
        result['doctype'] = self.cmbDoctype.value()
        result['tempInvalidReason'] = self.cmbReason.value()
        result['onlyClosed'] = self.chkOnlyClosed.isChecked()
        result['orgStructureId'] = self.cmbOrgStructure.value()
        result['personId'] = self.cmbPerson.value()
        if self.analysisMode:
            result['durationFrom'] = self.edtDurationFrom.value()
            result['durationTo'] = self.edtDurationTo.value()
            result['sex'] = self.cmbSex.currentIndex()
            result['ageFrom'] = self.edtAgeFrom.value()
            result['ageTo'] = self.edtAgeTo.value()
            result['socStatusClassId'] = self.cmbSocStatusClass.value()
            result['socStatusTypeId'] = self.cmbSocStatusType.value()
            result['MKBFilter'] = self.cmbMKBFilter.currentIndex()
            result['MKBFrom']   = unicode(self.edtMKBFrom.text())
            result['MKBTo']     = unicode(self.edtMKBTo.text())
        result['showMKBDescription'] = self.chkShowMKBDescription.isChecked()
        result['showPersonSpeciality'] = self.chkShowPersonSpeciality.isChecked()
        result['insuranceOfficeMark'] = self.cmbInsuranceOfficeMark.currentIndex()
        result['averageDuration'] = self.chkAverageDuration.isChecked()
        result['resultsForGroups'] = self.chkResultsForGroups.isChecked()
        result['hasRegAddress'] = self.chkRegAddress.isChecked()
        result['hasLocAddress'] = self.chkLocAddress.isChecked()
        result['hasBeginPerson'] = self.chkBeginPerson.isChecked()
        result['hasEndPerson'] = self.chkEndPerson.isChecked()
        result['placeWork'] = self.chkPlaceWork.isChecked()
        result['showTempInvalidReceiver'] = self.cmbShowTempInvalidReceiver.currentIndex()
        if self.isCntUserVisible:
            result['cntUser'] = self.edtCntUser.value()
        if self.isTempInvalidDuplicateVisible:
            result['isTempInvalidDuplicate'] = self.chkTempInvalidDuplicate.isChecked()
        if self.isTempInvalidDuplicateWorkVisible:
            result['isTempInvalidDuplicateWork'] = self.chkTempInvalidDuplicateWork.isChecked()
        if self.clientNameSortVisible:
            result['isClientNameSort'] = self.chkClientNameSort.isChecked()
        if self.dateSortVisible and self.chkDateSort.isChecked():
            result['isDateSort'] = self.chkDateSort.isChecked()
            result['dateSort'] = self.cmbDateSort.currentIndex()
        result['isNumberSort'] = self.chkNumberSort.isChecked()
        result['isNoExternal'] = self.chkTempInvalidNoExternal.isChecked()
        result['showTempInvalidStatus'] = self.chkShowTempInvalidStatus.isChecked()
        return result


    @pyqtSignature('QDate')
    def on_edtBegDate_dateChanged(self, date):
        self.cmbPerson.setBegDate(date)


    @pyqtSignature('QDate')
    def on_edtEndDate_dateChanged(self, date):
        self.cmbPerson.setEndDate(date)


    @pyqtSignature('int')
    def on_cmbOrgStructure_currentIndexChanged(self, index):
        orgStructureId = self.cmbOrgStructure.value()
        self.cmbPerson.setOrgStructureId(orgStructureId)


    @pyqtSignature('int')
    def on_cmbSocStatusClass_currentIndexChanged(self, index):
        socStatusClassId = self.cmbSocStatusClass.value()
        filter = ('class_id=%d' % socStatusClassId) if socStatusClassId else ''
        self.cmbSocStatusType.setFilter(filter)


    @pyqtSignature('int')
    def on_cmbMKBFilter_currentIndexChanged(self, index):
        self.edtMKBFrom.setEnabled(index == 1)
        self.edtMKBTo.setEnabled(index == 1)

