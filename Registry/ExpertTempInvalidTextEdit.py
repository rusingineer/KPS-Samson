# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2019 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui

from library.crbcombobox       import CRBComboBox
from library.Utils             import forceInt, forceRef, forceString, formatSex, formatShortNameInt, forceBool, forceDate

from RefBooks.TempInvalidState import CTempInvalidState


class CExpertTempInvalidTextEdit(QtGui.QTextEdit):
    def __init__(self, parent):
        QtGui.QTextEdit.__init__(self, parent)
        self.setReadOnly(True)
        self.setLineWrapMode(QtGui.QTextEdit.WidgetWidth)
        self.setWordWrapMode(QtGui.QTextOption.WrapAtWordBoundaryOrAnywhere)


    def setDataCache(self, tempInvalidReasonCache, vrbPersonCache, tempInvalidDocumentCache, tempInvalidBreakCache, tempInvalidResultCache, tempInvalidRegimeCache):
        self.tempInvalidReasonCache = tempInvalidReasonCache
        self.vrbPersonCache = vrbPersonCache
        self.tempInvalidDocumentCache = tempInvalidDocumentCache
        self.tempInvalidBreakCache = tempInvalidBreakCache
        self.tempInvalidResultCache = tempInvalidResultCache
        self.tempInvalidRegimeCache = tempInvalidRegimeCache


    def formatClient(self, clientRecord, clientId):
        name = u''
        if clientId and clientRecord:
            name = u'Ф.И.О.: ' + formatShortNameInt(forceString(clientRecord.value('lastName')),
               forceString(clientRecord.value('firstName')),
               forceString(clientRecord.value('patrName')))
            name += u', Дата рожд.: ' + forceString(clientRecord.value('birthDate')) + u', Пол: ' + formatSex(clientRecord.value('clientSex'))
        return name


    def formatRBRecord(self, dataCache, recordId):
        if recordId and dataCache:
            return forceString(dataCache.getStringById(recordId, CRBComboBox.showName))
        return u''


    def loadData(self, tempInvalidId, documentId = None):
        expertTempInvalidInfoList = []
        self.tempInvalidId = tempInvalidId
        if self.tempInvalidId:
            db = QtGui.qApp.db
            table = db.table('TempInvalid')
            tableDiagnosis = db.table('Diagnosis')
            tableClient = db.table('Client')
            cols = u'''TempInvalid.*, Client.lastName, Client.firstName, Client.patrName, Client.birthDate, Client.sex AS clientSex, Diagnosis.MKB, (SELECT COUNT(Visit.id)
                FROM TempInvalid AS TI
                INNER JOIN Event ON TI.client_id = Event.client_id
                INNER JOIN Visit ON Visit.event_id = Event.id
                WHERE TI.id = TempInvalid.id AND Event.deleted = 0 AND Visit.deleted = 0 AND TI.deleted = 0
                AND DATE(Visit.date) >= TI.begDate AND DATE(Visit.date) <= TI.endDate) AS visitCount'''
            queryTable = table.leftJoin(tableClient, db.joinAnd([tableClient['id'].eq(table['client_id']), tableClient['deleted'].eq(0)]))
            queryTable = queryTable.leftJoin(tableDiagnosis, db.joinAnd([tableDiagnosis['id'].eq(table['diagnosis_id']), tableDiagnosis['deleted'].eq(0)]))
            tempInvalidRecord = db.getRecordEx(queryTable, cols, [table['id'].eq(self.tempInvalidId), table['deleted'].eq(0)])
            if tempInvalidRecord:
                expertTempInvalidInfoList.append(self.formatClient(tempInvalidRecord, forceRef(tempInvalidRecord.value('client_id'))))
                expertTempInvalidInfoList.append(u'\nСтСт: ' + (u'да' if forceBool(tempInvalidRecord.value('insuranceOfficeMark')) else u'нет'))
                expertTempInvalidInfoList.append(u'\nПричина нетрудоспособности: ' + self.formatRBRecord(self.tempInvalidReasonCache, forceRef(tempInvalidRecord.value('tempInvalidReason_id'))))
                expertTempInvalidInfoList.append(u' Дата начала ВУТ: ' + forceString(forceDate(tempInvalidRecord.value('caseBegDate'))))
                expertTempInvalidInfoList.append(u' Начало: ' + forceString(forceDate(tempInvalidRecord.value('begDate'))))
                expertTempInvalidInfoList.append(u' Окончание: ' + forceString(forceDate(tempInvalidRecord.value('endDate'))))
                expertTempInvalidInfoList.append(u' Врач: ' + self.formatRBRecord(self.vrbPersonCache, forceRef(tempInvalidRecord.value('person_id'))))
                expertTempInvalidInfoList.append(u' МКБ: ' + forceString(tempInvalidRecord.value('MKB')))
                expertTempInvalidInfoList.append(u'\nСостояние: ' + CTempInvalidState.text(forceInt(tempInvalidRecord.value('state'))))
                expertTempInvalidInfoList.append(u' Длительность: ' + forceString(forceInt(tempInvalidRecord.value('duration'))))
                expertTempInvalidInfoList.append(u' Визиты: ' + forceString(forceInt(tempInvalidRecord.value('visitCount'))))
                expertTempInvalidInfoList.append(u'\nТип: ' + self.formatRBRecord(self.tempInvalidDocumentCache, forceRef(tempInvalidRecord.value('doctype_id'))))
                expertTempInvalidInfoList.append(u'\nВ стационаре "с": ' + forceString(forceDate(tempInvalidRecord.value('begDateStationary'))))
                expertTempInvalidInfoList.append(u' В стационаре "по": ' + forceString(forceDate(tempInvalidRecord.value('endDateStationary'))))
                expertTempInvalidInfoList.append(u' Нарушение режима: ' + self.formatRBRecord(self.tempInvalidBreakCache, forceRef(tempInvalidRecord.value('break_id'))))
                expertTempInvalidInfoList.append(u' Дата нарушения режима: ' + forceString(forceDate(tempInvalidRecord.value('breakDate'))))
                expertTempInvalidInfoList.append(u'\nРезультат: ' + self.formatRBRecord(self.tempInvalidResultCache, forceRef(tempInvalidRecord.value('result_id'))))
                expertTempInvalidInfoList.append(u' Дата результата - Приступить к работе: ' + forceString(forceDate(tempInvalidRecord.value('resultDate'))))
                expertTempInvalidInfoList.append(u' Дата результата - Иное: ' + forceString(forceDate(tempInvalidRecord.value('resultOtherwiseDate'))))
                expertTempInvalidInfoList.append(u'\nНомер путевки: ' + forceString(tempInvalidRecord.value('numberPermit')))
                expertTempInvalidInfoList.append(u' Дата начала путевки: ' + forceString(forceDate(tempInvalidRecord.value('begDatePermit'))))
                expertTempInvalidInfoList.append(u' Дата окончания путевки: ' + forceString(forceDate(tempInvalidRecord.value('endDatePermit'))))
                expertTempInvalidInfoList.append(u'\nИнвалидность: ' + self.formatRBRecord(self.tempInvalidRegimeCache, forceRef(tempInvalidRecord.value('disability_id'))))
        if documentId:
            db = QtGui.qApp.db
            table = db.table('TempInvalidDocument_Care')
            tableClient = db.table('Client')
            cols = ['Client.lastName, Client.firstName, Client.patrName, TempInvalidDocument_Care.begDate, TempInvalidDocument_Care.endDate, TempInvalidDocument_Care.MKB']
            queryTable = table.leftJoin(tableClient, db.joinAnd([tableClient['id'].eq(table['client_id']), tableClient['deleted'].eq(0)]))
            tempCareRecords = db.getRecordList(queryTable, cols, [table['master_id'].eq(documentId)])
            if tempCareRecords:
                expertTempInvalidInfoList.append(u'\nПатронаж: ')
            for tempCareRecord in tempCareRecords:
                expertTempInvalidInfoList.append(u'\nФ.И.О.: ' + formatShortNameInt(forceString(tempCareRecord.value('lastName')),
                                                    forceString(tempCareRecord.value('firstName')),
                                                    forceString(tempCareRecord.value('patrName'))))
                expertTempInvalidInfoList.append(u'\nДата начала периода: ' + forceString(forceDate(tempCareRecord.value('begDate'))))
                expertTempInvalidInfoList.append(u' Дата окончания периода: ' + forceString(forceDate(tempCareRecord.value('endDate'))))
                expertTempInvalidInfoList.append(u'\nМКБ: ' + forceString(tempCareRecord.value('MKB')))
        self.setPlainText(u', '.join(expertTempInvalidInfo for expertTempInvalidInfo in expertTempInvalidInfoList if expertTempInvalidInfo))

