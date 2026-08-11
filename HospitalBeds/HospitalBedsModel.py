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

from collections import namedtuple

from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import (Qt,
                          pyqtSignature,
                          QAbstractTableModel,
                          QDate,
                          QDateTime,
                          QString,
                          QTime,
                          QVariant,
                         )

from Users.Rights import urHBVisibleOwnEventsParentOrgStructureOnly, urHBVisibleOwnEventsOrgStructureOnly
from library.Calendar import wpFiveDays, wpSixDays, wpSevenDays
from library.database import CTableRecordCache, CRecordCache, addCondLike
from library.InDocTable           import (CDateInDocTableCol, 
                                          CEnumInDocTableCol,
                                          CInDocTableCol, 
                                          CInDocTableModel,
                                          CRecordListModel)
from library.PrintInfo            import CDateInfo, CDateTimeInfo
from library.TableModel           import (CBoolCol,
                                          CCol,
                                          CDateCol,
                                          CDateTimeFixedCol,
                                          CEnumCol,
                                          CIntCol,
                                          CRefBookCol,
                                          CTableModel,
                                          CTextCol,
                                         )

from library.Utils                import (calcAge,
                                          forceBool,
                                          forceDate,
                                          forceDateTime,
                                          forceInt,
                                          forceRef,
                                          forceString,
                                          forceDouble,
                                          formatShortNameInt,
                                          getAgeRangeCond,
                                          getDataOSHB,
                                          getHospDocumentLocationInfo,
                                          getMKB,
                                          isMKB,
                                          toVariant,
                                          getBasic_MKB)

from Events.ActionServiceType     import CActionServiceType
from Events.ActionStatus          import CActionStatus
from Events.ActionTypeCol         import CActionTypeCol
from Events.Utils import getActionTypeIdListByFlatCode, getRealPayed, getEventDuration, CEventTypeDescription

from Reports.Utils import (getActionClientPolicyForDate, getActionQueueClientPolicyForDate,
                           getActionTypeStringPropertyValue, getClientPolicyForDate, getContractClientPolicyForDate,
                           getDataOrgStructure, getDataOrgStructureName, getDataOrgStructureNameMoving,
                           getPropertyAPHBP, getStringProperty, getStringPropertyValue, getTransferPropertyIn,
                           isActionToServiceTypeForEvent, getStringPropertyEventYes, updateLIKE,
                           getPropertyHospitalBedProfile, getPropertyAPHBPNoProfile, )

from Resources.JobTicketChooser   import getJobTicketAsText
from Orgs.Orgs          import selectOrganisation
from Orgs.Utils import getOrganisationShortName, getParentOrgStructureId, getOrgStructureDescendants

from Ui_ReportF001Setup           import Ui_ReportF001SetupDialog
from Ui_HospitalizationExecDialog import Ui_HospitalizationExecDialog
from Ui_HBPatronEditorDialog      import Ui_HBPatronEditorDialog


class CHospitalBedsModel(QAbstractTableModel):
    column = [u'Код', u'Штат', u'Тип', u'Профиль', u'Смены', u'Режим', u'Начало', u'Окончание', u'Подразделение', u'Наименование', u'Возраст', u'Пол']
    sex = [u'', u'М', u'Ж']
    defaultOrderCol = 0
    isPermanentCol = 1
    reliefCol = 4
    begDateCol = 6
    endDateCol = 7
    idColumn = 12
    busyCol = 13
    involuteCol = 14


    def __init__(self, parent):
        QAbstractTableModel.__init__(self, parent)
        self.items = []
        self.headerSortingCol = {}
        self._cols = []
        self.cntAll = 0
        self.cntInvolute = 0
        self.cntFree = 0
        self.cntBusy = 0

    def getItemId(self, row):
        return self.items[row][self.idColumn]

    def getStatistics(self):
        return self.cntAll, self.cntInvolute, self.cntFree, self.cntBusy

    def cols(self):
        self._cols = [CCol(u'Код',           ['code'], 10, 'l'),
                      CCol(u'Штат',          ['isPermanent'], 10, 'l'),
                      CCol(u'Тип',           ['type_id'], 10, 'l'),
                      CCol(u'Профиль',       ['profile_id'], 10, 'l'),
                      CCol(u'Смены',         ['relief'], 6, 'l'),
                      CCol(u'Режим',         ['schedule_id'], 15, 'l'),
                      CCol(u'Начало',        ['begDate'], 20, 'l'),
                      CCol(u'Окончание',     ['endDate'], 20, 'l'),
                      CCol(u'Подразделение', ['master_id'], 8, 'l'),
                      CCol(u'Наименование',  ['name'], 20, 'l'),
                      CCol(u'Возраст',       ['age'], 10, 'l'),
                      CCol(u'Пол',           ['sex'], 10, 'l')
                      ]
        return self._cols

    def columnCount(self, index=None, *args, **kwargs):
        return len(self.column)

    def rowCount(self, index=None, *args, **kwargs):
        return len(self.items)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return QVariant(self.column[section])
        return QVariant()

    def isBusy(self, index):
        return self.items[index.row()][self.busyCol]

    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if role == Qt.DisplayRole:
            if column in [self.begDateCol, self.endDateCol]:
                item = self.items[row]
                return toVariant(item[column].toString('dd.MM.yyyy hh:mm'))
            elif column == self.isPermanentCol:
                return QVariant()
            else:
                item = self.items[row]
                return toVariant(item[column])
        elif role == Qt.CheckStateRole:
            if column == self.isPermanentCol:
                item = self.items[row]
                return toVariant(Qt.Checked if item[column] else Qt.Unchecked)
        elif role == Qt.BackgroundColorRole:
            item = self.items[row]
            isBusy = item[self.busyCol]
            if isBusy == 2:
                return toVariant(QtGui.QColor(200, 230, 240))
            elif isBusy == 1:
                return toVariant(QtGui.QColor(255, 250, 205))
        return QVariant()

    def loadData(self, dialogParams):
        self.items = []
        self.cntAll = 0
        self.cntInvolute = 0
        self.cntFree = 0
        self.cntBusy = 0
        codeBeds = dialogParams.get('codeBeds', None)
        permanent = dialogParams.get('permanent', None)
        typeBeds = dialogParams.get('type', None)
        bedProfile = dialogParams.get('bedProfile', None)
        schedule = dialogParams.get('scheduleBed', None)
        sexIndexBed = dialogParams.get('sexIndexBed', None)
        ageForBed = dialogParams.get('ageForBed', None)
        ageToBed = dialogParams.get('ageToBed', None)
        involution = dialogParams.get('involution', None)
        busy = dialogParams.get('busy', None)
        isPlacementChecked = dialogParams.get('isPlacementChecked', None)
        placementId = dialogParams.get('placementId', None)
        activeBeds = dialogParams.get('activeBeds', None)
        orgStructureIdList = dialogParams.get('orgStructureIdList', [])
        begDate = dialogParams.get('filterBegDate', None)
        endDate = dialogParams.get('filterEndDate', None)
        begTime = dialogParams.get('filterBegTime', None)
        endTime = dialogParams.get('filterEndTime', None)
        if not begTime.isNull():
            begDateTime = QDateTime(begDate, begTime)
            begDate = begDateTime
        if not endTime.isNull():
            endDateTime = QDateTime(endDate, endTime)
            endDate = endDateTime

        db = QtGui.qApp.db
        table = db.table('vHospitalBed')
        tableHospitalBedType = db.table('rbHospitalBedType')
        tableHospitalBedProfile = db.table('rbHospitalBedProfile')
        tableHospitalBedShedule = db.table('rbHospitalBedShedule')
        tableOrgStructure = db.table('OrgStructure')
        queryTable = table.leftJoin(tableOrgStructure, tableOrgStructure['id'].eq(table['master_id']))
        queryTable = queryTable.leftJoin(tableHospitalBedType, tableHospitalBedType['id'].eq(table['type_id']))
        queryTable = queryTable.leftJoin(tableHospitalBedProfile, tableHospitalBedProfile['id'].eq(table['profile_id']))
        queryTable = queryTable.leftJoin(tableHospitalBedShedule, tableHospitalBedShedule['id'].eq(table['schedule_id']))

        cols = [table['code'],
                table['isPermanent'],
                tableHospitalBedType['name'].alias('typeName'),
                tableHospitalBedProfile['name'].alias('profileName'),
                table['relief'],
                tableHospitalBedShedule['name'].alias('scheduleName'),
                table['begDate'],
                table['endDate'],
                tableOrgStructure['name'].alias('orgStructureName'),
                table['isBusy'],
                table['name'],
                table['age'],
                table['sex'],
                table['id'],
                u"""EXISTS(SELECT NULL FROM OrgStructure_HospitalBed_Involution oshbi WHERE oshbi.master_id = vHospitalBed.id 
AND oshbi.involutionType > 0
AND (NOW() BETWEEN oshbi.begDate AND oshbi.endDate
    OR (oshbi.begDate <= NOW() AND oshbi.endDate IS NULL)
    OR (oshbi.begDate IS NULL AND oshbi.endDate IS NULL))) as involute"""
                ]

        cond = [table['master_id'].inlist(orgStructureIdList)]
        addCondLike(cond, table['code'], codeBeds)
        if permanent != 0:
            cond.append(table['isPermanent'].eq(permanent-1))
        if typeBeds:
            cond.append(table['type_id'].eq(typeBeds))
        if bedProfile:
            cond.append(table['profile_id'].eq(bedProfile))
        if schedule:
            cond.append(table['schedule_id'].eq(schedule))
        if sexIndexBed:
            cond.append(table['sex'].eq(sexIndexBed))
        if ageForBed <= ageToBed and not (ageForBed == 0 and ageToBed == 150):
            ageForBedCount = ageForBed
            if ageForBed == 0:
                ageList = [u'']
            else:
                ageList = []
            while ageForBedCount <= ageToBed:
                ageList.append(str(ageForBedCount))
                ageForBedCount += 1
            if ageList:
                cond.append(u'''(SELECT TRIM(BOTH 'г'
                FROM (SELECT TRIM(BOTH '-'
                FROM vHospitalBed.age)))) IN (%s)''' % (u','.join(age for age in ageList if age)))
        if involution is not None:
            cond.append(u"""EXISTS(SELECT NULL
                                  FROM OrgStructure_HospitalBed_Involution oshbi
                                  WHERE oshbi.master_id = vHospitalBed.id 
                                  AND oshbi.involutionType = {0}
                                  AND (NOW() BETWEEN oshbi.begDate AND oshbi.endDate
                                    OR (oshbi.begDate <= NOW() AND oshbi.endDate IS NULL)
                                    OR (oshbi.begDate IS NULL AND oshbi.endDate IS NULL)))""".format(involution + 1))
        if busy == 1:
            cond.append('isHospitalBedBusy(vHospitalBed.id, NOW()) != 2')
        elif busy == 2:
            cond.append('isHospitalBedBusy(vHospitalBed.id, NOW()) = 2')
        if activeBeds:
            cond.append(db.joinOr([table['endDate'].ge(QDateTime.currentDateTime()), table['endDate'].isNull()]))
        if begDate:
            cond.append(db.joinOr([table['begDate'].le(begDate), table['begDate'].isNull()]))
        if endDate:
            cond.append(db.joinOr([table['endDate'].ge(endDate), table['endDate'].isNull()]))

        records = db.getRecordList(queryTable, cols, cond)
        for record in records:
            item = [
                forceString(record.value('code')),
                forceBool(record.value('isPermanent')),
                forceString(record.value('typeName')),
                forceString(record.value('profileName')),
                forceInt(record.value('relief')),
                forceString(record.value('scheduleName')),
                forceDateTime(record.value('begDate')),
                forceDateTime(record.value('endDate')),
                forceString(record.value('orgStructureName')),
                forceString(record.value('name')),
                forceString(record.value('age')),
                self.sex[forceInt(record.value('sex'))],
                forceRef(record.value('id')),
                forceInt(record.value('isBusy')),
                forceBool(record.value('involute'))
            ]
            self.items.append(item)
            self.cntAll += 1
            if item[self.busyCol] == 2:
                self.cntBusy += 1
            elif item[self.involuteCol]:
                self.cntInvolute += 1
            else:
                self.cntFree += 1

        for col, order in self.headerSortingCol.items():
            self.sort(col, order)

    def sort(self, col, order=Qt.AscendingOrder):
        self.headerSortingCol = {col: order}
        reverse = order == Qt.DescendingOrder
        if col == self.isPermanentCol:
            self.items.sort(key=lambda x: forceBool(x[col]), reverse=reverse)
        elif col == self.reliefCol:
            self.items.sort(key=lambda x: forceInt(x[col]) if x else None, reverse=reverse)
        elif col in [self.begDateCol, self.endDateCol]:
            self.items.sort(key=lambda x: forceDateTime(x[col]) if x else None, reverse=reverse)
        else:
            self.items.sort(key=lambda x: forceString(x[col]).lower() if x else None, reverse=reverse)
        self.reset()


class CInvoluteBedsModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'OrgStructure_HospitalBed_Involution', 'id', 'master_id', parent)
        self.addCol(CEnumInDocTableCol(u'Причина сворачивания', 'involutionType', 16, [u'нет сворачивания', u'ремонт', u'карантин',  u'иные причины',  u'проветривание'])).setReadOnly()
        self.addCol(CDateInDocTableCol(u'Начало сворачивания', 'begDate', 20, canBeEmpty=True)).setReadOnly()
        self.addCol(CDateInDocTableCol(u'Окончание сворачивания', 'endDate', 20, canBeEmpty=True)).setReadOnly()
        self.headerSortingCol = {}

    def loadItems(self, masterId):
        db = QtGui.qApp.db
        cols = []
        for col in self._cols:
            if not col.external():
                cols.append(col.fieldName())
        cols.append(self._idFieldName)
        cols.append(self._masterIdFieldName)
        if self._idxFieldName:
            cols.append(self._idxFieldName)
        for col in self._hiddenCols:
            cols.append(col)
        table = self._table
        filter = [table[self._masterIdFieldName].eq(masterId)]
        if self._filter:
            filter.append(self._filter)
        if table.hasField('deleted'):
            filter.append(table['deleted'].eq(0))
        orderBY = "id"
        for key, value in self.headerSortingCol.items():
            if value:
                ASC = u'ASC'
            else:
                ASC = u'DESC'
            if key == 0:
                orderBY = 'involutionType %s' % ASC
            if key == 1:
                orderBY = 'begDate %s' % ASC
            if key == 2:
                orderBY = 'endDate %s' % ASC


        self._items = db.getRecordList(table, cols, filter, orderBY)
        if self._extColsPresent:
            extSqlFields = []
            for col in self._cols:
                if col.external():
                    fieldName = col.fieldName()
                    if fieldName not in cols:
                        extSqlFields.append(QtSql.QSqlField(fieldName, col.valueType()))
            if extSqlFields:
                for item in self._items:
                    for field in extSqlFields:
                        item.append(field)
        self.reset()


class CMonitoringModel(QAbstractTableModel):
    column = [u'И', u'Номер', u'ФИО', u'Пол', u'Дата рождения', u'Поступил', u'Выбыл', u'Койка', u'Подразделение', u'Лечащий врач']
    sex = [u'', u'М', u'Ж']
    clientColumn = 1
    eventColumn = 1

    def __init__(self, parent):
        QAbstractTableModel.__init__(self, parent)
        self.items = []
        self.clientDeath = 8
        self.headerSortingCol = {}
        self.movingActionTypeIdList = parent.movingActionTypeIdList
        self.receivedActionTypeIdList = parent.receivedActionTypeIdList
        self.leavedActionTypeIdList = parent.leavedActionTypeIdList
        self.planningActionTypeIdList = parent.planningActionTypeIdList
        self.comfortableActionTypeIdList = parent.comfortableActionTypeIdList
        self.movingAPTOrgStructure = parent.movingAPTOrgStructure

    def columnCount(self, index=None, *args, **kwargs):
        return len(self.column)

    def rowCount(self, index=None, *args, **kwargs):
        return len(self.items)

    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return QVariant(self.column[section])
            elif role == Qt.ToolTipRole:
                if section == 0:
                    return QVariant(u'Статус наблюдения пациента')
                elif section == 1:
                    return QVariant(u'Источник финансирования (код)')
                elif section == 2:
                    return QVariant(u'Договор')
                elif section == self.eventColumn:
                    return QVariant(u'Код события')
        return QVariant()

    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if role == Qt.DisplayRole:
            item = self.items[row]
            return toVariant(item[column])
        elif role == Qt.ToolTipRole:
            if column == 0:
                item = self.items[row]
                return QVariant(item[0] + u' ' + item[19])
            elif column == 1:
                item = self.items[row]
                return QVariant(item[17] + u' ' + item[1])
            elif column == 13:
                item = self.items[row]
                return QVariant(item[13] + u' ' + item[18])
        elif role == Qt.BackgroundColorRole:
            if column == 0 and self.items[row][0]:
               return toVariant(QtGui.QColor(self.items[row][20]))
        return QVariant()

    def getClientId(self, row):
        return self.items[row][self.clientColumn]

    def getEventId(self, row):
        return self.items[row][self.eventColumn]

    def getOrgStructureIdList(self, treeIndex):
        treeItem = treeIndex.internalPointer() if treeIndex.isValid() else None
        return treeItem.getItemIdList() if treeItem else []

    def getQuotingTypeIdList(self, quotingType):
        db = QtGui.qApp.db
        table = db.table('QuotaType')
        quotingTypeClass, quotingTypeId = quotingType
        if not quotingTypeId and (quotingTypeClass == 0 or quotingTypeClass == 1):
            return db.getIdList(table, [table['id']], [table['deleted'].eq(0), table['class'].eq(quotingTypeClass)])
        elif quotingTypeId:
            groupCond = forceString(db.translate(table, 'id', quotingTypeId, 'code'))
            return self.getDescendantGroups(table, 'group_code', groupCond, quotingTypeId)
        return None

    def getDescendantGroups(self, table, groupCol, groupCond, groupId):
        db = QtGui.qApp.db
        db.checkdb()
        table = db.forceTable(table)
        group = table[groupCol]

        result = set([groupId])
        parents = set([groupCond])

        while parents:
            childrenId = set(db.getIdList(table, where=group.inlist(parents)))
            newChildrenId = childrenId-result
            result |= newChildrenId
            records = db.getRecordList(table, [table['code']], [table['id'].inlist(newChildrenId), table['deleted'].eq(0)])
            childrenCode = set([forceString(record.value('code')) for record in records])
            newChildrenCode = childrenCode-parents
            parents = newChildrenCode
        return list(result)


class CPresenceModel(CMonitoringModel):
    column = [u'C', u'И', u'Д', u'П', u'ПпУ', u'Лицо по уходу', u'К', u'Номер', u'Код', u'Карта', u'ФИО', u'Пол', u'Дата рождения', u'Госпитализирован', u'Поступил', u'Плановая дата выбытия', u'MKB', u'Профиль', u'Койка', u'Помещение', u'Подразделение', u'Лечащий врач', u'Исполнитель', u'Гражданство',  u'А|МН П',  u'А|МН пУ',  u'ГрКр', u'Патронаж', u'М', u'Койко-дни', u'Направитель', u'Порядок обращения', u'Кем доставлен']
    statusObservationCol = 0
    financeCol = 1
    feedColumn = 3
    extraFeedColumn = 4
    patronColumn = 5
    comfortableDateCol = 6
    clientColumn = 7
    eventColumn = 8
    clientFIOColumn = 9
    defaultOrderCol = 10
    birthDateCol = 12
    hospDateCol = 13
    receivedDateCol = 14
    plannedEndDateColumn = 15
    MKBColumn = 16
    profileCol = 17
    bedColumn = 18
    placementColumn = 19
    namePersonColumn = 22
    clientFeaturesCol = 24
    patronFeaturesCol = 25
    documentLocationCol = 28
    bedDaysCol = 29
    codeFinanceCol = 33
    bedNameCol = 34
    statusObservationNameCol = 36
    actionIdColumn      = 37
    actionTypeIdColumn  = 38
    colorStatusObservationCol = 39
    comfortablePayStatusCol = 40
    setDateColumn       = 41
    actionEndDateColumn = 42
    patronIdColumn      = 43
    refusalToEatClientCol = 44
    refusalToEatPatronCol = 45
    isActionToServiceTypeCol = 46
    docLocalColorCol = 47
    colorFinanceCol = 48
    ageCol = 49

    def __init__(self, parent):
        CMonitoringModel.__init__(self, parent)
        self.items = []
        self.eventIdList = []
        self.itemByName = {}
        self.feedTextValueItems = {}
        self.extraFeedTextValueItems = {}
        self._cols = []
        self.begDays = 0
        self.statusObservation = None

    def cols(self):
        self._cols = [CCol(u'Статус наблюдения',     ['statusObservation'], 20, 'l'),
                      CCol(u'Код ИФ',                ['nameFinance'], 20, 'l'),
                      CCol(u'Договор',               ['contract'], 20, 'l'),
                      CCol(u'Питание',               ['feed'], 20, 'l'),
                      CCol(u'Питание по уходу',      ['extraFeed'], 20, 'l'),
                      CCol(u'Лицо по уходу',         ['patronName'], 20, 'l'),
                      CCol(u'Комфортность',          ['comfortableDate'], 20, 'l'),
                      CCol(u'Номер',                 ['client_id'], 20, 'l'),
                      CCol(u'Код события',           ['event_id'], 20, 'l'),
                      CCol(u'Карта',                 ['externalId'], 20, 'l'),
                      CCol(u'ФИО',                   ['lastName', 'firstName', 'patrName'], 30, 'l'),
                      CCol(u'Пол',                   ['sex'], 15, 'l'),
                      CCol(u'Дата рождения',         ['birthDate'], 20, 'l'),
                      CCol(u'Госпитализирован',      ['begDate'], 20, 'l'),
                      CCol(u'Поступил',              ['endDate'], 20, 'l'),
                      CCol(u'Плановая дата выбытия', ['plannedEndDate'], 20, 'l'),
                      CCol(u'MKB',                   ['MKB'], 20, 'l'),
                      CCol(u'Профиль',               ['profileName'], 20, 'l'),
                      CCol(u'Койка',                 ['codeBed', 'nameBed'], 30, 'l'),
                      CCol(u'Помещение',             ['placement'], 30, 'l'),
                      CCol(u'Подразделение',         ['nameOrgStructure'], 30, 'l'),
                      CCol(u'Лечащий врач',          ['namePerson'], 30, 'l'),
                      CCol(u'Исполнитель',           ['execPerson'], 30, 'l'),
                      CCol(u'Гражданство',           ['citizenship'], 30, 'l'),
                      CCol(u'Аллергия|Медикаментозная непереносимость пациента',         ['clientFeatures'], 20, 'l'), 
                      CCol(u'Аллергия|Медикаментозная непереносимость лица по уходу',    ['patronFeatures'], 20, 'l'),
                      CCol(u'Группа крови',          ['bloodType'], 20, 'l'),
                      CCol(u'Патронаж',              ['relative'], 20, 'l'),
                      CCol(u'Место нахождение учетного документа',['hospDocumentLocation'], 20, 'l'),
                      CCol(u'Койко-дни',             ['bedDays'], 20, 'l'),
                      CCol(u'Направитель',           ['relegateOrg_id'], 30, 'l'),
                      CCol(u'Порядок обращения',     ['eventOrder'], 30, 'l'),
                      CCol(u'Кем доставлен',         ['delivered'], 30, 'l'),
                      ]
        return self._cols

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return QVariant(self.column[section])
            elif role == Qt.ToolTipRole:
                if section == 0:
                    return QVariant(u'Статус наблюдения пациента')
                elif section == 1:
                    return QVariant(u'Источник финансирования (код)')
                elif section == 2:
                    return QVariant(u'Договор')
                elif section == 3:
                    return QVariant(u'Питание пациента')
                elif section == 4:
                    return QVariant(u'Питание по уходу')
                elif section == 6:
                    return QVariant(u'Комфортность')
                elif section == self.eventColumn:
                    return QVariant(u'Код события')
                elif section == 16:
                    return QVariant(u'Профиль лечения')
                elif section == 23:
                    return QVariant(u'Аллергия|Медикаментозная непереносимость пациента')
                elif section == 24:
                    return QVariant(u'Аллергия|Медикаментозная непереносимость лица по уходу')
                elif section == 25:
                    return QVariant(u'Группа крови')
                elif section == 27:
                    return QVariant(u'Место нахождение учетного документа')
        return QVariant()

    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if role == Qt.DisplayRole:
            if column in [self.hospDateCol, self.receivedDateCol]:
                item = self.items[row]
                return toVariant(item[column].toString('dd.MM.yyyy hh:mm'))
            elif column == self.birthDateCol:
                item = self.items[row]
                return toVariant(forceString(item[column]) + u' (' + item[self.ageCol] + u')')
            elif column == self.feedColumn:
                return toVariant(self.feedTextValueItems[self.getEventId(row)])
            elif column == self.extraFeedColumn:
                return toVariant(self.extraFeedTextValueItems[self.getEventId(row)])
            else:
                item = self.items[row]
                return toVariant(item[column])
        elif role == Qt.CheckStateRole:
            if column in [self.feedColumn, self.extraFeedColumn]:
                item = self.items[row]
                if column == self.extraFeedColumn and not item[self.refusalToEatPatronCol]:
                    return QVariant()
                return toVariant(Qt.Checked if item[column] else Qt.Unchecked)
        elif role == Qt.ToolTipRole:
            if column == self.statusObservationCol:
                item = self.items[row]
                if item[self.statusObservationCol]:
                    return QVariant(item[self.statusObservationCol] + u' ' + item[self.statusObservationNameCol])
                else:
                    return QVariant()
            elif column == self.financeCol:
                item = self.items[row]
                return QVariant(item[self.codeFinanceCol] + u' ' + item[column])
            elif column == self.profileCol:
                item = self.items[row]
                return QVariant(forceString(item[column]) + u' ' + item[self.bedNameCol])
        elif role == Qt.FontRole:
            if column == self.comfortableDateCol and self.items[row][self.comfortableDateCol]:
                comfortDate = self.items[row][self.comfortableDateCol]
                if comfortDate.date() == QDate().currentDate():
                    result = QtGui.QFont()
                    result.setBold(True)
                    return QVariant(result)
            elif column in [self.feedColumn, self.extraFeedColumn]:
                if 0 <= row < len(self.items):
                    item = self.items[row]
                    if item:
                        if (column == self.feedColumn and item[self.refusalToEatClientCol]) or (column == self.extraFeedColumn and item[self.refusalToEatPatronCol]):
                            result = QtGui.QFont()
                            result.setBold(True)
                            result.setStrikeOut(True)
                            return QVariant(result)
            elif column in [self.clientFeaturesCol, self.patronFeaturesCol]:
                clientFeatures = self.items[row][self.clientFeaturesCol].split('|')
                patronFeatures = self.items[row][self.patronFeaturesCol].split('|')
                if len(clientFeatures) > 0 and (int(clientFeatures[0]) >= 3 or int(clientFeatures[1]) >= 3) and column == self.clientFeaturesCol:
                    result = QtGui.QFont()
                    result.setBold(True)
                    return QVariant(result)
                if len(patronFeatures) > 0 and (int(patronFeatures[0]) >= 3 or int(patronFeatures[1]) >= 3) and column == self.patronFeaturesCol:
                    result = QtGui.QFont()
                    result.setBold(True)
                    return QVariant(result)
            if self.items[row][self.isActionToServiceTypeCol]:
                result = QtGui.QFont()
                result.setBold(True)
                result.setItalic(True)
                return QVariant(result)
        elif role == Qt.BackgroundColorRole:
            if column == self.statusObservationCol and self.items[row][column]:
                return toVariant(QtGui.QColor(self.items[row][self.colorStatusObservationCol]))
            elif column == self.financeCol:
                colorFinance = self.items[row][self.colorFinanceCol]
                if colorFinance:
                    return toVariant(colorFinance)
            elif column == self.documentLocationCol:
                docLocalColor = self.items[row][self.docLocalColorCol]
                if docLocalColor:
                    return toVariant(QtGui.QColor(docLocalColor))
            elif column == self.comfortableDateCol and self.items[row][column] and not self.items[row][self.comfortablePayStatusCol]:
                return toVariant(QtGui.QColor(Qt.red))
        elif role == Qt.TextColorRole:
            if column in [self.clientFeaturesCol, self.patronFeaturesCol]:
                clientFeatures = self.items[row][self.clientFeaturesCol].split('|')
                patronFeatures = self.items[row][self.patronFeaturesCol].split('|')
                if len(clientFeatures) > 0 and (int(clientFeatures[0]) > 3 or int(clientFeatures[1]) > 3) and column == self.clientFeaturesCol:
                    return toVariant(QtGui.QColor(Qt.red))
                if len(patronFeatures) > 0 and (int(patronFeatures[0]) > 3 or int(patronFeatures[1]) > 3) and column == self.patronFeaturesCol:
                    return toVariant(QtGui.QColor(Qt.red))
        return QVariant()

    def loadData(self, dialogParams):
        self.begDays = 0
        self.items = []
        self.itemByName = {}
        self.feedTextValueItems = {}
        self.extraFeedTextValueItems = {}
        self.eventIdList = []
        filterBegDate = dialogParams.get('filterBegDate', None)
        filterEndDate = dialogParams.get('filterEndDate', None)
        filterBegTime = dialogParams.get('filterBegTime', QTime())
        filterEndTime = dialogParams.get('filterEndTime', QTime())
        begDateTime = None
        endDateTime = None
        if filterBegDate and filterBegTime:
            begDateTime = QDateTime(filterBegDate, filterBegTime)
        if filterEndDate and filterEndTime:
            endDateTime = QDateTime(filterEndDate, filterEndTime)
        indexSex = dialogParams.get('indexSex', 0)
        ageFor = dialogParams.get('ageFor', 0)
        ageTo = dialogParams.get('ageTo', 150)
        order = dialogParams.get('order', 0)
        eventTypeId = dialogParams.get('eventTypeId', None)
        orgStructureId = dialogParams.get('orgStructureId', None)
        permanent = dialogParams.get('permanent', None)
        _type = dialogParams.get('type', None)
        bedProfile = dialogParams.get('bedProfile', None)
        treatmentProfile = dialogParams.get('treatmentProfile', None)
        presenceDay = dialogParams.get('presenceDay', None)
        codeAttachType = dialogParams.get('codeAttachType', None)
        indexLocalClient = dialogParams.get('indexLocalClient', None)
        showLocatedInReanimation = dialogParams.get('showLocatedInReanimation', True)
        finance = dialogParams.get('finance', None)
        contractId = dialogParams.get('contractId', None)
        feed = dialogParams.get('feed', None)
        dateFeed = dialogParams.get('dateFeed', None)
        personId = dialogParams.get('personId', None)
        insurerId = dialogParams.get('insurerId', None)
        regionSMO, regionTypeSMO, regionSMOCode = dialogParams.get('regionSMO', (False, 0, None))
        personExecId = dialogParams.get('personExecId', None)
        quotingType = dialogParams.get('quotingType', None)
        accountingSystemId = dialogParams.get('accountingSystemId', None)
        filterClientId = dialogParams.get('filterClientId', None)
        filterEventId = dialogParams.get('filterEventId', None)
        statusObservation = dialogParams.get('statusObservation', None)
        codeBeds = dialogParams.get('codeBeds', None)
        placementId = dialogParams.get('placementId', None)
        isPlacementChecked = dialogParams.get('isPlacementChecked', None)
        dietId = dialogParams.get('dietId', None)
        documentTypeForTracking = dialogParams.get('documentTypeForTracking', None)
        resultSee = dialogParams.get('resultSee', None)
        documentLocation = dialogParams.get('documentLocation', None)
        relegateOrg = dialogParams.get('relegateOrg', None)
        MKBFilter = dialogParams['MKBFilter']
        MKBFrom   = dialogParams['MKBFrom']
        MKBTo     = dialogParams['MKBTo']
        isPresenceActionActiviti = dialogParams.get('isPresenceActionActiviti', True)
        scheduleId = dialogParams.get('scheduleId', None)
        diagnosisTypeId = dialogParams.get('diagnosisTypeId', None)
        deliverBy = dialogParams.get('deliverBy', None)

        self.statusObservation = statusObservation
        defaultOrgStructureEventTypeIdList = dialogParams.get('defaultOrgStructureEventTypeIdList', [])
        db = QtGui.qApp.db
        tableAPT = db.table('ActionPropertyType')
        tableAP = db.table('ActionProperty')
        tableActionType = db.table('ActionType')
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        tableMAT = db.table('rbMedicalAidType')
        tableEventFeed = db.table('Event_Feed')
        tableClient = db.table('Client')
        tableClientPolicy = db.table('ClientPolicy')
        tableOS = db.table('OrgStructure')
        tableAPOS = db.table('ActionProperty_OrgStructure')
        tablePWS = db.table('vrbPersonWithSpeciality')
        tableClientAttach = db.table('ClientAttach')
        tableRBAttachType = db.table('rbAttachType')
        tableContract = db.table('Contract')
        tableRBFinance = db.table('rbFinance')
        tableRBFinanceBC = db.table('rbFinance').alias('rbFinanceByContract')
        tableStatusObservation = db.table('Client_StatusObservation')
        leavedActionTypeIdList = self.leavedActionTypeIdList
        tableOrg = db.table('Organisation')

        currentDate = QDate.currentDate()
        currentDateTime = QDateTime.currentDateTime()


        def hasDiagnosisTypeId(diagnosisTypeId):
            return ('(EXISTS(SELECT Diagnostic.id FROM Diagnostic '
                'WHERE Diagnostic.event_id = Event.id AND Diagnostic.deleted = 0 '
                'AND Diagnostic.person_id = Event.execPerson_id '
                'AND Diagnostic.diagnosisType_id = %d))' % diagnosisTypeId)


        def isMKBWithDiagnosisType(MKBFrom, MKBTo, diagnosisTypeId=None):
            return ("(EXISTS(SELECT Diagnosis.id FROM Diagnosis "
                "JOIN Diagnostic ON Diagnostic.diagnosis_id = Diagnosis.id "
                "WHERE Diagnostic.event_id = Event.id AND Diagnosis.deleted = 0 AND Diagnostic.deleted = 0 "
                "AND Diagnostic.person_id = Event.execPerson_id " +
                (("AND Diagnostic.diagnosisType_id = %d " % diagnosisTypeId) if diagnosisTypeId else '') +
                "AND Diagnosis.MKB >= '%s' AND Diagnosis.MKB <= '%s'))" % (MKBFrom, MKBTo))


        def getDataMoving(orgStructureId, indexSex=0, ageFor=0, ageTo=150, permanent=None, type=None,
                          bedProfile=None, presenceDay=None, codeAttachType=None, finance=None,
                          feed=None, dateFeed=None, localClient=0, quotingTypeList=None,
                          accountingSystemId=None, filterClientId=None, filterEventId=None,
                          codeBeds=None, defaultOrgStructureEventTypeIdList=[], begDate=None, endDate=None):
            groupBY = ''
            cols = [tableAction['id'].alias('actionId'),
                    tableEvent['id'].alias('eventId'),
                    tableEvent['client_id'],
                    tableEvent['externalId'],
                    tableEvent['relative_id'],
                    tableEvent['eventType_id'],
                    tableEvent['setDate'],
                    tableEvent['execDate'],
                    tableClient['lastName'],
                    tableClient['firstName'],
                    tableClient['patrName'],
                    tableClient['sex'],
                    tableClient['birthDate'],
                    tableAction['begDate'],
                    tableAction['endDate'],
                    tableAction['plannedEndDate'],
                    tableAction['actionType_id'],
                    tableAction['finance_id'],
                    tableEvent['contract_id'],
                    tableContract['number'].alias('numberContract'),
                    tableContract['date'].alias('dateContract'),
                    tableContract['resolution'].alias('resolutionContract'),
                    tablePWS['name'].alias('namePerson'),
                    tableOrg['shortName'].alias('relegateOrg')
                    ]
            cols.append(getMKB())
            cols.append(getBasic_MKB())
            cols.append(isActionToServiceTypeForEvent(CActionServiceType.reanimation))
            cols.append('''(SELECT EP.name FROM vrbPersonWithSpeciality AS EP WHERE EP.id = Event.execPerson_id) AS execPerson''')
            cols.append(getReceivedBegDate(self.receivedActionTypeIdList))
            cols.append(getLeavedEndDate(self.leavedActionTypeIdList))
            cols.append("(IF(Event.relative_id IS NOT NULL, (SELECT CONCAT_WS(_utf8' ', ClientE.lastName, ClientE.firstName,"
                        "ClientE.patrName) FROM Client AS ClientE WHERE ClientE.deleted = 0 AND ClientE.id = Event.relative_id), _utf8'')) AS patronName")
            cols.append(u'IF(OrgStructure.id IS NOT NULL AND OrgStructure.deleted=0, OrgStructure.name, NULL) AS nameOrgStructure')
            if not dateFeed:
                dateFeed = currentDate.addDays(1)
            cols.append(getEventFeedId(u'0', db.formatDate(dateFeed), u''' AS countEventClientFeedId'''))
            cols.append(getEventFeedId(u'1', db.formatDate(dateFeed), u''' AS countEventPatronFeedId'''))
            cols.append(getDietCode(u'0', db.formatDate(dateFeed), u''' AS clientDiet'''))
            cols.append(getDietCode(u'1', db.formatDate(dateFeed), u''' AS patronDiet'''))
            cols.append(getEventRefusalToEat(u'0', db.formatDate(dateFeed), u''' AS refusalToEatClient'''))
            cols.append(getEventRefusalToEat(u'1', db.formatDate(dateFeed), u''' AS refusalToEatPatron'''))
            cols.append(getDataOSHB())
            cols.append(getHBProfileFromBed())
            cols.append(getHospDocumentLocationInfo())
            comfortableIdList = self.comfortableActionTypeIdList
            if comfortableIdList:
                cols.append(getActionByFlatCode(comfortableIdList))
            cols.append(getStatusObservation())
            cols.append(getPlacement())
            cols.append('%s AS patronag' % (getStringPropertyValue(u'Патронаж')))
            cols.append("""getClientCitizenshipTitle(Client.id, CURDATE()) as citizenship""")
            cols.append('(SELECT name from rbBloodType where id = Client.bloodType_id) as bloodType')
            cols.append(getClientFeatures())
            cols.append(getPatronFeatures())
            queryTable = tableAction.leftJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
            queryTable = queryTable.leftJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.leftJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
            queryTable = queryTable.leftJoin(tableMAT, tableEventType['medicalAidType_id'].eq(tableMAT['id']))
            queryTable = queryTable.leftJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
            queryTable = queryTable.leftJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
            queryTable = queryTable.leftJoin(tableAP,  db.joinAnd([tableAP['action_id'].eq(tableAction['id']), tableAP['type_id'].eq(tableAPT['id'])]))
            queryTable = queryTable.leftJoin(tablePWS, tablePWS['id'].eq(tableAction['person_id']))
            queryTable = queryTable.leftJoin(tableAPOS, tableAPOS['id'].eq(tableAP['id']))
            queryTable = queryTable.leftJoin(tableOS, tableOS['id'].eq(tableAPOS['value']))
            queryTable = queryTable.leftJoin(tableOrg, tableEvent['relegateOrg_id'].eq(tableOrg['id']))
            cond = [tableAction['actionType_id'].inlist(self.movingActionTypeIdList),
                    tableAPT['id'].inlist(self.movingAPTOrgStructure),
                    tableMAT['code'].inlist(['1', '2', '3', '7']),
                    tableAction['deleted'].eq(0),
                    tableEvent['deleted'].eq(0),
                    tableAP['deleted'].eq(0),
                    tableClient['deleted'].eq(0)
                    ]
            if scheduleId:
                cond.append(isScheduleBeds(scheduleId))
            if contractId:
                cond.append(tableContract['id'].eq(contractId))
            if diagnosisTypeId and not MKBFilter:
                cond.append(hasDiagnosisTypeId(diagnosisTypeId))
            if MKBFilter and diagnosisTypeId:
                cond.append(isMKBWithDiagnosisType(MKBFrom, MKBTo, diagnosisTypeId))
            if MKBFilter and not diagnosisTypeId:
                cond.append(isMKB(MKBFrom, MKBTo))
            if order:
                cond.append(tableEvent['order'].eq(order))
            if eventTypeId:
                cond.append(tableEvent['eventType_id'].eq(eventTypeId))

            if QtGui.qApp.userHasAnyRight([urHBVisibleOwnEventsParentOrgStructureOnly, urHBVisibleOwnEventsOrgStructureOnly]):
                tableExecPerson = db.table('Person')
                queryTable = queryTable.leftJoin(tableExecPerson, tableExecPerson['id'].eq(tableEvent['execPerson_id']))
                uOrgStructureId = forceRef(db.translate('Person', 'id', QtGui.qApp.userId, 'orgStructure_id'))
                if QtGui.qApp.userHasRight(urHBVisibleOwnEventsParentOrgStructureOnly):
                    parentOrgStructure = getParentOrgStructureId(uOrgStructureId)
                    uOrgStructureList = getOrgStructureDescendants(parentOrgStructure if parentOrgStructure else uOrgStructureId)
                    cond.append(db.joinOr([tableExecPerson['orgStructure_id'].inlist(uOrgStructureList), tableEventType['ignoreVisibleRights'].eq(1)]))
                elif QtGui.qApp.userHasRight(urHBVisibleOwnEventsOrgStructureOnly):
                    uOrgStructureList = getOrgStructureDescendants(uOrgStructureId)
                    cond.append(db.joinOr([tableExecPerson['orgStructure_id'].inlist(uOrgStructureList), tableEventType['ignoreVisibleRights'].eq(1)]))

            if defaultOrgStructureEventTypeIdList:
                cond.append(tableEvent['eventType_id'].inlist(defaultOrgStructureEventTypeIdList))
            if personId:
                cond.append(tableEvent['execPerson_id'].eq(personId))
            if personExecId:
                cond.append(tableAction['person_id'].eq(personExecId))
            if self.statusObservation:
                cond.append(existsStatusObservation(self.statusObservation))
            if accountingSystemId and filterClientId:
                tableIdentification = db.table('ClientIdentification')
                queryTable = queryTable.innerJoin(tableIdentification, tableIdentification['client_id'].eq(tableClient['id']))
                cond.append(tableIdentification['accountingSystem_id'].eq(accountingSystemId))
                cond.append(tableIdentification['identifier'].eq(filterClientId))
                cond.append(tableIdentification['deleted'].eq(0))
            elif filterClientId:
                cond.append(tableClient['id'].eq(filterClientId))
            if filterEventId:
                cond.append(tableEvent['externalId'].eq(filterEventId))
            if feed == 1:
                cond.append('NOT %s' % (getEventFeedId(u'', db.formatDate(dateFeed))))
            elif feed == 2:
                cond.append('%s' % (getEventFeedId(u'', db.formatDate(dateFeed), alias=u'', refusalToEat=0)))
            elif feed == 3:
                cond.append('%s' % (getEventFeedId(u'', db.formatDate(dateFeed), alias=u'', refusalToEat=1)))
            if orgStructureIdList:
                cond.append(tableOS['deleted'].eq(0))
                # cond.append(getDataOrgStructure(u'Отделение пребывания', orgStructureIdList, False))
                cond.append(tableAPOS['value'].inlist(orgStructureIdList))
            if quotingTypeList:
                quotingTypeIdList, quotingTypeClass = quotingTypeList
                if quotingTypeClass is not None:
                    cond.append(getDataClientQuoting(u'Квота', quotingTypeIdList))
            if forceInt(codeAttachType) > 0:
                cond.append(tableRBAttachType['code'].eq(codeAttachType))
                queryTable = queryTable.innerJoin(tableClientAttach, tableClient['id'].eq(tableClientAttach['client_id']))
                queryTable = queryTable.innerJoin(tableRBAttachType, tableClientAttach['attachType_id'].eq(tableRBAttachType['id']))
            if indexSex > 0:
                cond.append(tableClient['sex'].eq(indexSex))
            if ageFor <= ageTo and not (ageFor == 0 and ageTo == 150):
                cond.append(getAgeRangeCond(ageFor, ageTo))
            if deliverBy:
                cond.append(getDeliverByCond(deliverBy))

            if isPresenceActionActiviti:
                cond.append(tableAction['endDate'].isNull())
            else:
                if begDate and endDate:
                    cond.append(db.joinOr([tableAction['endDate'].ge(begDate), tableAction['endDate'].isNull()]))
                elif begDate:
                    cond.append(db.joinOr([tableAction['endDate'].isNull(), tableAction['endDate'].ge(begDate)]))
                elif endDate:
                    cond.append(db.joinOr([tableAction['endDate'].isNull(), tableAction['endDate'].le(endDate)]))
                else:
                    cond.append(db.joinAnd([tableAction['begDate'].le(currentDateTime),
                                            db.joinOr([tableAction['endDate'].isNull(), tableAction['endDate'].ge(currentDateTime)])]))
            if presenceDay:
                datePresence = endDate.addDays(-presenceDay + 1) if endDate else currentDate.addDays(-presenceDay + 1)
                cond.append(tableAction['begDate'].lt(datePresence))
            if QtGui.qApp.defaultHospitalBedFinanceByMoving() == 2:
                cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.code, IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinanceByContract.code, NULL)) AS codeFinance')
                cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.name, IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinanceByContract.name, NULL)) AS nameFinance')
                cols.append(getClientPolicyForDate())
                if finance:
                    cond.append('''((Action.finance_id IS NOT NULL AND Action.deleted=0 AND Action.finance_id = %s) OR (Contract.id IS NOT NULL AND Contract.deleted=0 AND Contract.finance_id = %s))''' % (str(finance), str(finance)))
                    queryTable = queryTable.innerJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
                    queryTable = queryTable.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.innerJoin(tableRBFinanceBC, tableRBFinanceBC['id'].eq(tableContract['finance_id']))
                else:
                    queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
                    queryTable = queryTable.leftJoin(tableContract, db.joinAnd([tableContract['id'].eq(tableEvent['contract_id']), tableContract['deleted'].eq(0)]))
                    queryTable = queryTable.leftJoin(tableRBFinanceBC, tableRBFinanceBC['id'].eq(tableContract['finance_id']))
            elif QtGui.qApp.defaultHospitalBedFinanceByMoving() == 1:
                cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.code, NULL) AS codeFinance')
                cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.name, NULL) AS nameFinance')
                cols.append(getActionClientPolicyForDate())
                queryTable = queryTable.leftJoin(tableContract, db.joinAnd([tableContract['id'].eq(tableEvent['contract_id']), tableContract['deleted'].eq(0)]))
                if finance:
                    cond.append('''(Action.finance_id IS NOT NULL AND Action.deleted=0 AND Action.finance_id = %s)''' % (str(finance)))
                    queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
                else:
                    queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
            else:
                cols.append(u'rbFinance.code AS codeFinance')
                cols.append(u'rbFinance.name AS nameFinance')
                cols.append(getContractClientPolicyForDate())
                if finance:
                    cond.append(tableRBFinance['id'].eq(finance))
                    queryTable = queryTable.leftJoin(tableContract, db.joinAnd([tableContract['id'].eq(tableEvent['contract_id']), tableContract['deleted'].eq(0)]))
                    queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
                else:
                    queryTable = queryTable.leftJoin(tableContract, db.joinAnd([tableContract['id'].eq(tableEvent['contract_id']), tableContract['deleted'].eq(0)]))
                    queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
            if localClient == 2:
                cond.append('''NOT %s''' % (getDataAPHB()))
            elif localClient == 1:
                cond.append('''%s''' % (getDataAPHB(permanent, _type, bedProfile, codeBeds)))
            else:
                if (permanent and permanent > 0) or _type or bedProfile or codeBeds:
                    cond.append('''%s''' % (getDataAPHB(permanent, _type, bedProfile, codeBeds)))
            if isPlacementChecked:
                cond.append(getPlacementCond(placementId))
            if treatmentProfile:
                cond.append(getHospitalBedProfileFromBed(treatmentProfile))
            if dietId:
                dateParam = dateFeed if dateFeed else QDate().currentDate()
                feedCond = [
                    tableEventFeed['event_id'].eq(tableEvent['id']), 
                    tableEventFeed['diet_id'].eq(dietId), 
                    tableEventFeed['date'].eq(dateParam)
                ]
                cond.append(db.existsStmt(tableEventFeed, feedCond))
            tableDocumentTypeForTracking = db.table('Client_DocumentTracking')
            if documentTypeForTracking:
                if documentTypeForTracking != u'specialValueID':
                    cond.append(tableDocumentTypeForTracking['deleted'].eq(0))
                    queryTable = queryTable.leftJoin(tableDocumentTypeForTracking, tableClient['id'].eq(tableDocumentTypeForTracking['client_id']))
                    cond.append(tableDocumentTypeForTracking['documentTypeForTracking_id'].eq(documentTypeForTracking))
                    cond.append(tableDocumentTypeForTracking['documentNumber'].eq(tableEvent['externalId']))
                    groupBY = 'Event.id'
            if resultSee:
                tableDiagnostic = db.table('Diagnostic')
                tablerbDiagnosticResult = db.table('rbDiagnosticResult')
                queryTable = queryTable.leftJoin(tableDiagnostic, tableDiagnostic['event_id'].eq(tableEvent['id']))
                queryTable = queryTable.leftJoin(tablerbDiagnosticResult, tablerbDiagnosticResult['id'].eq(tableDiagnostic['result_id']))
                cond.append(tablerbDiagnosticResult['id'].eq(resultSee))
            if documentLocation:
                tableDocumentLocation = db.table('Client_DocumentTrackingItem')
                if not documentTypeForTracking:
                    queryTable = queryTable.leftJoin(tableDocumentTypeForTracking, tableClient['id'].eq(tableDocumentTypeForTracking['client_id']))
                    cond.append(tableDocumentTypeForTracking['documentNumber'].eq(tableEvent['externalId']))
                queryTable = queryTable.leftJoin(tableDocumentLocation, tableDocumentTypeForTracking['id'].eq(tableDocumentLocation['master_id']))
                tableDocumentLocationLimit = db.table('Client_DocumentTrackingItem').alias('tableDocumentLocationLimit')
                cond.append(tableDocumentLocation['documentLocation_id'].inlist(documentLocation))
                cond.append(u'Client_DocumentTracking.documentNumber = Event.externalId')
                cond.append(tableDocumentLocation['id'].eqEx('(%s)' % db.selectStmt(tableDocumentLocationLimit, tableDocumentLocationLimit['id'], tableDocumentLocationLimit['master_id'].eq(tableDocumentLocation['master_id']), 'documentLocationDate desc, documentLocationTime desc limit 1')))
                if groupBY == '':
                    groupBY = 'Event.id'
            if relegateOrg:
                cond.append(tableEvent['relegateOrg_id'].eq(relegateOrg))
            if insurerId or regionSMO:
                queryTable = queryTable.innerJoin(tableClientPolicy,
                                                  u'''(ClientPolicy.id = getClientPolicyIdForDate(Client.id, IF(Contract.id IS NOT NULL AND Contract.deleted=0, IF(rbFinance.code = 2, 1, IF(rbFinance.code = 3, 0, 1)), 1), IF(Event.execDate IS NOT NULL, Event.execDate, Event.setDate), Event.id))''')
                if not regionSMO:
                    cond.append(tableClientPolicy['insurer_id'].eq(insurerId))
                else:
                    tableOrganisation = db.table('Organisation').alias('Org_Area')
                    queryTable = queryTable.innerJoin(tableOrganisation, [tableOrganisation['id'].eq(tableClientPolicy['insurer_id']), tableOrganisation['deleted'].eq(0)])
                    if regionSMOCode:
                        if regionTypeSMO:
                            cond.append(tableOrganisation['area'].notlike(regionSMOCode))
                        else:
                            cond.append(tableOrganisation['area'].like(regionSMOCode))
            if not isPresenceActionActiviti:
                if groupBY != '':
                    groupBY += u', ' + u'Event.externalId'
                else:
                    groupBY = u'Event.externalId'
            if not showLocatedInReanimation:
                cond.append(u"""
                            NOT EXISTS (SELECT
                            A.id
                            FROM
                            Action A
                            JOIN ActionType AT ON A.actionType_id = AT.id
                            LEFT JOIN ActionProperty AP_OS ON AP_OS.action_id = A.id AND AP_OS.deleted = 0
                            LEFT JOIN ActionPropertyType APT_OS ON AP_OS.type_id = APT_OS.id
                                                                    AND APT_OS.deleted = 0
                                                                    AND APT_OS.name = 'Отделение пребывания'
                            LEFT JOIN ActionProperty_OrgStructure APOS ON AP_OS.id = APOS.id
                            LEFT JOIN ActionProperty AP_HB ON AP_HB.action_id = A.id AND AP_HB.deleted = 0
                            LEFT JOIN ActionPropertyType APT_HB ON AP_HB.type_id = APT_HB.id
                                                                    AND APT_HB.deleted = 0
                                                                    AND APT_HB.name = 'койка'
                            LEFT JOIN ActionProperty_HospitalBed APHB ON AP_HB.id = APHB.id
                            WHERE
                            A.deleted = 0
                            AND AT.deleted = 0
                            AND AT.flatCode LIKE 'reanimation%'
                            AND A.event_id = Action.event_id
                            AND A.status = 0)""")
            cols.append(u"""CASE Event.`order` WHEN 1 THEN 'плановый'
                                               WHEN 2 THEN 'экстренный'
                                               WHEN 3 THEN 'самотёком' 
                                               WHEN 4 THEN 'принудительный' 
                                               WHEN 5 THEN 'внутренний перевод' 
                                               WHEN 6 THEN 'неотложная' END as eventOrder"""
                        )
            cols.append(getReceivedPropertyString(u'Кем доставлен', u'delivered', self.receivedActionTypeIdList))
            if groupBY != '':
                records = db.getRecordListGroupBy(queryTable, cols, cond, groupBY)
            else:
                records = db.getRecordList(queryTable, cols, cond)
            for record in records:
                documentLocationInfo  = forceString(record.value('documentLocationInfo')).split("  ")
                hospDocumentLocation  = forceString(documentLocationInfo[0]) if len(documentLocationInfo) >= 1 else ''
                documentLocationColor = forceString(documentLocationInfo[1]) if len(documentLocationInfo) > 1 else ''
                if documentTypeForTracking == u'specialValueID':
                    if hospDocumentLocation != '':
                        continue
                countEventClientFeedId = forceBool(record.value('countEventClientFeedId'))
                countEventPatronFeedId = forceBool(record.value('countEventPatronFeedId'))
                refusalToEatClient = forceBool(record.value('refusalToEatClient'))
                refusalToEatPatron = forceBool(record.value('refusalToEatPatron'))
                if (feed == 1 and not (countEventClientFeedId + countEventPatronFeedId)) or (feed == 2 and (countEventClientFeedId + countEventPatronFeedId)) or not feed or feed == 3 or feed == 4:
                    bedCodeName = forceString(record.value('bedCodeName')).split("  ")
                    bedCode = forceString(bedCodeName[0]) if len(bedCodeName)>=1 else ''
                    bedName = forceString(bedCodeName[1]) if len(bedCodeName)>=2 else ''
                    bedSex = forceString(bedCodeName[2]) if len(bedCodeName)>=3 else ''
                    eventId = forceRef(record.value('eventId'))
                    clientId = forceRef(record.value('client_id'))
                    statusObservation = forceString(record.value('statusObservation')).split('|')
                    statusObservationCode = forceString(statusObservation[0]) if len(statusObservation) >= 1 else u''
                    statusObservationName = forceString(statusObservation[1]) if len(statusObservation) >= 2 else u''
                    statusObservationColor = forceString(statusObservation[2]) if len(statusObservation) >= 3 else u''
                    statusObservationDate = forceString(statusObservation[3]) if len(statusObservation) >= 4 else u''
                    statusObservationPerson = forceString(statusObservation[4]) if len(statusObservation) >= 5 else u''
                    comfortable = forceString(record.value('comfortable'))
                    comfortableList = []
                    if comfortable:
                        comfortableList = comfortable.split("  ")
                    comfortableDate = forceDateTime(QVariant(comfortableList[0])) if len(comfortableList) >= 1 else ''
                    comfortableStatus = forceInt(QVariant(comfortableList[1])) if len(comfortableList) >= 2 else 0
                    if comfortableStatus:
                        comfortablePayStatus = getRealPayed(comfortableStatus)
                    else:
                        comfortablePayStatus = False
                    setDate = forceDate(record.value('setDate'))
                    execDate = forceDate(record.value('execDate'))
                    bedDays = updateDurationEvent(setDate, execDate if execDate.isValid() else QDate().currentDate(), begDate, endDate, forceRef(record.value('eventType_id')), isPresence=True)
                    self.begDays += forceInt(bedDays) if bedDays != u'-' else 0
                    begDate = forceDateTime(record.value('begDate'))
                    endDate = forceDateTime(record.value('endDate'))
                    policyEndDate = forceDate(record.value('policyEndDate'))
                    colorFinance = None
                    if policyEndDate:
                        if forceDate(begDate) < policyEndDate <= forceDate(begDate).addDays(3):
                            colorFinance = QtGui.QColor(Qt.yellow)
                        elif forceDate(begDate) >= policyEndDate:
                            colorFinance = QtGui.QColor(Qt.red)
                    receivedBegDateTime = forceDateTime(record.value('receivedBegDate'))
                    relativeId = forceRef(record.value('relative_id'))
                    patron = forceString(record.value('patronName'))
                    clientAllergy = forceString(record.value('clientAllergy'))
                    clientIntoleranceMedicament = forceString(record.value('clientIntoleranceMedicament'))
                    clientFeatures = '%s|%s' % (clientAllergy,  clientIntoleranceMedicament)
                    patronAllergy = forceString(record.value('patronAllergy'))
                    patronIntoleranceMedicament = forceString(record.value('patronIntoleranceMedicament'))
                    patronFeatures = '%s|%s' % (patronAllergy,  patronIntoleranceMedicament)
                    patronag = forceString(record.value('patronag'))
                    nameContract = ' '.join([forceString(record.value(name)) for name in ('numberContract', 'dateContract', 'resolutionContract')])
                    isActionToServiceType = forceBool(record.value('isActionToServiceType'))
                    basicMKB = forceString(record.value('Basic_MKB'))
                    MKB = forceString(record.value('MKB'))
                    if basicMKB or MKB:
                        strMKB = (basicMKB if basicMKB else u'?') + u';' + (MKB if MKB else u'?')
                    else:
                        strMKB = u''
                    item = [statusObservationCode,
                            forceString(record.value('nameFinance')),
                            nameContract,
                            countEventClientFeedId,
                            countEventPatronFeedId,
                            patron,
                            comfortableDate,
                            clientId,
                            eventId,
                            forceString(record.value('externalId')),
                            forceString(record.value('lastName')) + u' ' + forceString(record.value('firstName')) + u' ' + forceString(record.value('patrName')),
                            self.sex[forceInt(record.value('sex'))],
                            forceDate(record.value('birthDate')),
                            receivedBegDateTime,
                            begDate,
                            forceDate(record.value('plannedEndDate')),
                            strMKB,
                            forceString(record.value('profileName')),
                            bedCode + bedSex,
                            forceString(record.value('placement')),
                            forceString(record.value('nameOrgStructure')),
                            forceString(record.value('execPerson')),
                            forceString(record.value('namePerson')),
                            forceString(record.value('citizenship')),
                            clientFeatures,
                            patronFeatures,
                            forceString(record.value('bloodType')),
                            patronag,
                            hospDocumentLocation,
                            bedDays,
                            forceString(record.value('relegateOrg')),
                            forceString(record.value('eventOrder')),
                            forceString(record.value('delivered')),
                            forceString(record.value('codeFinance')),
                            bedName,
                            endDate.toString('dd.MM.yyyy hh:mm'),
                            statusObservationName + u' (' + (statusObservationDate if statusObservationDate else u'') + u' ' + (statusObservationPerson if statusObservationPerson else u'') + u')',
                            forceRef(record.value('actionId')),
                            forceRef(record.value('actionType_id')),
                            statusObservationColor,
                            comfortablePayStatus,
                            begDate,
                            endDate,
                            relativeId,
                            refusalToEatClient,
                            refusalToEatPatron,
                            isActionToServiceType,
                            documentLocationColor,
                            colorFinance,
                            forceString(calcAge(forceDate(record.value('birthDate')), forceDate(record.value('endDate'))))
                            ]
                    if eventId and eventId not in self.eventIdList:
                        self.eventIdList.append(eventId)
                    self.feedTextValueItems[eventId] = forceString(record.value('clientDiet'))
                    self.extraFeedTextValueItems[eventId] = forceString(record.value('patronDiet'))
                    self.items.append(item)
                    _dict = {
                        'observationCode': statusObservationCode,
                        'finance': forceString(record.value('nameFinance')),
                        'contract': nameContract,
                        'clientFeed': forceString(record.value('clientDiet')) if countEventClientFeedId else '',
                        'patronFeed': forceString(record.value('patronDiet')) if countEventPatronFeedId else '',
                        'comfortableDate': comfortableDate,
                        'bedCode': bedCode + bedSex,
                        'orgStructure': forceString(record.value('nameOrgStructure')),
                        'financeCode': forceString(record.value('codeFinance')),
                        'bedName': bedName,
                        'observationName': statusObservationName,
                        'observationColor': statusObservationColor,
                        'setDate': CDateTimeInfo(receivedBegDateTime),
                        'begDate': CDateTimeInfo(begDate),
                        'plannedEndDate': CDateTimeInfo(forceDateTime(record.value('plannedEndDate'))),
                        'refusalToEatClient': forceBool(record.value('refusalToEatClient')),
                        'refusalToEatPatron': forceBool(record.value('refusalToEatPatron')),
                        'profile': forceString(record.value('profileName')),
                        'placement': forceString(record.value('placement'))
                    }
                    self.itemByName[eventId] = _dict


        def findReceivedNoEnd(orgStructureIdList=[], dateFeed=None, quotingTypeList=None, accountingSystemId=None, filterClientId=None,
                              filterEventId=None, defaultOrgStructureEventTypeIdList=defaultOrgStructureEventTypeIdList, hospitalWard=False,
                              endDateTime=None, begDateTimeFilter=None, endDateTimeFilter=None):
            groupBY = ''
            cols = [tableAction['id'].alias('actionId'),
                    tableEvent['id'].alias('eventId'),
                    tableEvent['client_id'],
                    tableEvent['externalId'],
                    tableEvent['relative_id'],
                    tableEvent['eventType_id'],
                    tableEvent['setDate'],
                    tableEvent['execDate'],
                    tableClient['lastName'],
                    tableClient['firstName'],
                    tableClient['patrName'],
                    tableClient['sex'],
                    tableClient['birthDate'],
                    tableAction['begDate'],
                    tableAction['endDate'],
                    tableEvent['setDate'],
                    tableAction['plannedEndDate'],
                    tableAction['actionType_id'],
                    tableContract['number'].alias('numberContract'),
                    tableContract['date'].alias('dateContract'),
                    tableContract['resolution'].alias('resolutionContract'),
                    tablePWS['name'].alias('namePerson'),
                    tableOrg['shortName'].alias('relegateOrg')
                    ]
            cols.append(getMKB())
            cols.append(getBasic_MKB())
            cols.append(isActionToServiceTypeForEvent(CActionServiceType.reanimation))
            cols.append('''(SELECT EP.name FROM vrbPersonWithSpeciality AS EP WHERE EP.id = Event.execPerson_id) AS execPerson''')
            cols.append(getReceivedBegDate(self.receivedActionTypeIdList))
            cols.append(getLeavedEndDate(self.leavedActionTypeIdList))
            cols.append("(IF(Event.relative_id IS NOT NULL, (SELECT CONCAT_WS(_utf8' ', ClientE.lastName, ClientE.firstName,"
                        "ClientE.patrName, CAST( ClientE.id AS CHAR)) FROM Client AS ClientE WHERE ClientE.deleted = 0 AND ClientE.id = Event.relative_id LIMIT 1), _utf8'')) AS patronName")
            nameProperty = u'Направлен в отделение'
            cols.append(getDataOrgStructureName(nameProperty))
            cols.append('%s AS patronag' % (getStringPropertyEventYes(self.movingActionTypeIdList, u'Патронаж')))
            cols.append(getHospDocumentLocationInfo())
            if not dateFeed:
                dateFeed = currentDate.addDays(1)
            comfortableIdList = self.comfortableActionTypeIdList
            if comfortableIdList:
                cols.append(getActionByFlatCode(comfortableIdList))
            cols.append(getEventFeedId(u'0', db.formatDate(dateFeed), u''' AS countEventClientFeedId'''))
            cols.append(getEventFeedId(u'1', db.formatDate(dateFeed), u''' AS countEventPatronFeedId'''))
            cols.append(getDietCode(u'0', db.formatDate(dateFeed), u''' AS clientDiet'''))
            cols.append(getDietCode(u'1', db.formatDate(dateFeed), u''' AS patronDiet'''))
            cols.append(getEventRefusalToEat(u'0', db.formatDate(dateFeed), u''' AS refusalToEatClient'''))
            cols.append(getEventRefusalToEat(u'1', db.formatDate(dateFeed), u''' AS refusalToEatPatron'''))
            cols.append(getStatusObservation())
            cols.append(getPlacement())
            cols.append(getOSHBP())
            cols.append("""getClientCitizenshipTitle(Client.id, CURDATE()) as citizenship""")
            cols.append('(SELECT name from rbBloodType where id = Client.bloodType_id) as bloodType')
            cols.append(getClientFeatures())
            cols.append(getPatronFeatures())
            queryTable = tableAction.leftJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.leftJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
            queryTable = queryTable.leftJoin(tableMAT, tableEventType['medicalAidType_id'].eq(tableMAT['id']))
            queryTable = queryTable.leftJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
            queryTable = queryTable.leftJoin(tablePWS, tablePWS['id'].eq(tableAction['person_id']))
            queryTable = queryTable.leftJoin(tableOrg, tableEvent['relegateOrg_id'].eq(tableOrg['id']))
            cond = [tableAction['actionType_id'].inlist(self.receivedActionTypeIdList),
                    tableMAT['code'].inlist(['1', '2', '3', '7']),
                    tableAction['deleted'].eq(0),
                    tableEvent['deleted'].eq(0),
                    tableClient['deleted'].eq(0),
                    tableAction['endDate'].isNull()
                    ]
            if scheduleId:
                cond.append(isScheduleBeds(scheduleId))
            if contractId:
                cond.append(tableContract['id'].eq(contractId))
            if treatmentProfile:
                cond.append(getHospitalBedProfile(treatmentProfile))
            if diagnosisTypeId and not MKBFilter:
                cond.append(hasDiagnosisTypeId(diagnosisTypeId))
            if MKBFilter and diagnosisTypeId:
                cond.append(isMKBWithDiagnosisType(MKBFrom, MKBTo, diagnosisTypeId))
            if MKBFilter and not diagnosisTypeId:
                cond.append(isMKB(MKBFrom, MKBTo))
            if relegateOrg:
                cond.append(tableEvent['relegateOrg_id'].eq(relegateOrg))
            if order:
                cond.append(tableEvent['order'].eq(order))
            if eventTypeId:
                cond.append(tableEvent['eventType_id'].eq(eventTypeId))

            if QtGui.qApp.userHasAnyRight([urHBVisibleOwnEventsParentOrgStructureOnly, urHBVisibleOwnEventsOrgStructureOnly]):
                tableExecPerson = db.table('Person')
                queryTable = queryTable.leftJoin(tableExecPerson, tableExecPerson['id'].eq(tableEvent['execPerson_id']))
                uOrgStructureId = forceRef(db.translate('Person', 'id', QtGui.qApp.userId, 'orgStructure_id'))
                if QtGui.qApp.userHasRight(urHBVisibleOwnEventsParentOrgStructureOnly):
                    parentOrgStructure = getParentOrgStructureId(uOrgStructureId)
                    uOrgStructureList = getOrgStructureDescendants(parentOrgStructure if parentOrgStructure else uOrgStructureId)
                    cond.append(db.joinOr([tableExecPerson['orgStructure_id'].inlist(uOrgStructureList), tableEventType['ignoreVisibleRights'].eq(1)]))
                elif QtGui.qApp.userHasRight(urHBVisibleOwnEventsOrgStructureOnly):
                    uOrgStructureList = getOrgStructureDescendants(uOrgStructureId)
                    cond.append(db.joinOr([tableExecPerson['orgStructure_id'].inlist(uOrgStructureList), tableEventType['ignoreVisibleRights'].eq(1)]))

            if defaultOrgStructureEventTypeIdList:
                cond.append(tableEvent['eventType_id'].inlist(defaultOrgStructureEventTypeIdList))
            if personId:
                cond.append(tableEvent['execPerson_id'].eq(personId))
            if personExecId:
                cond.append(tableAction['person_id'].eq(personExecId))
            if self.statusObservation:
                cond.append(existsStatusObservation(self.statusObservation))
            if accountingSystemId and filterClientId:
                tableIdentification = db.table('ClientIdentification')
                queryTable = queryTable.innerJoin(tableIdentification, tableIdentification['client_id'].eq(tableClient['id']))
                cond.append(tableIdentification['accountingSystem_id'].eq(accountingSystemId))
                cond.append(tableIdentification['identifier'].eq(filterClientId))
                cond.append(tableIdentification['deleted'].eq(0))
            elif filterClientId:
                cond.append(tableClient['id'].eq(filterClientId))
            if filterEventId:
                cond.append(tableEvent['externalId'].eq(filterEventId))
            if orgStructureIdList and not hospitalWard:
                pigeonHole = db.joinAnd([getActionPropertyTypeName(u'Приемное отделение'),
                getDataOrgStructure(u'Приемное отделение', orgStructureIdList, False)])
                notPigeonHole = db.joinAnd(['NOT %s' % (getActionPropertyTypeName(u'Приемное отделение'))])
                cond.append(db.joinOr([getDataOrgStructure(nameProperty, orgStructureIdList, False), pigeonHole, notPigeonHole]))
            if quotingTypeList:
                quotingTypeIdList, quotingTypeClass = quotingTypeList
                if quotingTypeClass is not None:
                    cond.append(getDataClientQuoting(u'Квота', quotingTypeIdList))
            if QtGui.qApp.defaultHospitalBedFinanceByMoving() in (0, 2):
                cols.append(u'rbFinance.code AS codeFinance')
                cols.append(u'rbFinance.name AS nameFinance')
                if finance:
                    cond.append(tableRBFinance['id'].eq(finance))
                    queryTable = queryTable.leftJoin(tableContract, db.joinAnd([tableContract['id'].eq(tableEvent['contract_id']), tableContract['deleted'].eq(0)]))
                    queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
                else:
                    queryTable = queryTable.leftJoin(tableContract, db.joinAnd([tableContract['id'].eq(tableEvent['contract_id']), tableContract['deleted'].eq(0)]))
                    queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
            else:
                queryTable = queryTable.leftJoin(tableContract, db.joinAnd([tableContract['id'].eq(tableEvent['contract_id']), tableContract['deleted'].eq(0)]))

            cols.append(getContractClientPolicyForDate())
            if feed == 1:
                cond.append('NOT %s' % (getEventFeedId(u'', db.formatDate(dateFeed))))
            elif feed == 2:
                cond.append('%s' % (getEventFeedId(u'', db.formatDate(dateFeed), alias=u'', refusalToEat=0)))
            elif feed == 3:
                cond.append('%s' % (getEventFeedId(u'', db.formatDate(dateFeed), alias=u'', refusalToEat=1)))
            if presenceDay:
                datePresence = currentDate.addDays(-presenceDay + 1)
                cond.append(tableAction['begDate'].lt(datePresence))
            else:
                if endDateTimeFilter:
                    cond.append(tableAction['begDate'].le(endDateTimeFilter))
                else:
                    cond.append(tableAction['begDate'].le(currentDateTime))
            if forceInt(codeAttachType) > 0:
                cond.append(tableRBAttachType['code'].eq(codeAttachType))
                queryTable = queryTable.innerJoin(tableClientAttach, tableClient['id'].eq(tableClientAttach['client_id']))
                queryTable = queryTable.innerJoin(tableRBAttachType, tableClientAttach['attachType_id'].eq(tableRBAttachType['id']))
            if indexSex > 0:
                cond.append(tableClient['sex'].eq(indexSex))
            if ageFor <= ageTo and not (ageFor == 0 and ageTo == 150):
                cond.append(getAgeRangeCond(ageFor, ageTo))
            if isPlacementChecked:
                cond.append(getPlacementCond(placementId))
            tableDocumentTypeForTracking = db.table('Client_DocumentTracking')
            if documentTypeForTracking:
                if documentTypeForTracking != u'specialValueID':
                    cond.append(tableDocumentTypeForTracking['deleted'].eq(0))
                    queryTable = queryTable.leftJoin(tableDocumentTypeForTracking, tableClient['id'].eq(tableDocumentTypeForTracking['client_id']))
                    cond.append(tableDocumentTypeForTracking['documentTypeForTracking_id'].eq(documentTypeForTracking))
                    cond.append(tableDocumentTypeForTracking['documentNumber'].eq(tableEvent['externalId']))
                    groupBY = 'Event.id'
            if resultSee:
                tableDiagnostic = db.table('Diagnostic')
                tablerbDiagnosticResult = db.table('rbDiagnosticResult')
                queryTable = queryTable.leftJoin(tableDiagnostic, tableDiagnostic['event_id'].eq(tableEvent['id']))
                queryTable = queryTable.leftJoin(tablerbDiagnosticResult, tablerbDiagnosticResult['id'].eq(tableDiagnostic['result_id']))
                cond.append(tablerbDiagnosticResult['id'].eq(resultSee))
            if documentLocation:
                tableDocumentLocation = db.table('Client_DocumentTrackingItem')
                if not documentTypeForTracking:
                    queryTable = queryTable.leftJoin(tableDocumentTypeForTracking, tableClient['id'].eq(tableDocumentTypeForTracking['client_id']))
                    cond.append(tableDocumentTypeForTracking['documentNumber'].eq(tableEvent['externalId']))
                queryTable = queryTable.leftJoin(tableDocumentLocation, tableDocumentTypeForTracking['id'].eq(tableDocumentLocation['master_id']))
                tableDocumentLocationLimit = db.table('Client_DocumentTrackingItem').alias('tableDocumentLocationLimit')
                cond.append(tableDocumentLocation['documentLocation_id'].inlist(documentLocation))
                cond.append(tableDocumentLocation['id'].eqEx('(%s)'%db.selectStmt(tableDocumentLocationLimit, tableDocumentLocationLimit['id'], tableDocumentLocationLimit['master_id'].eq(tableDocumentLocation['master_id']), 'documentLocationDate desc, documentLocationTime desc limit 1')))
                if groupBY == '':
                    groupBY = 'Event.id'
            if insurerId or regionSMO:
                queryTable = queryTable.innerJoin(tableClientPolicy,
                                                  u'''(ClientPolicy.id = getClientPolicyIdForDate(Client.id, IF(Contract.id IS NOT NULL AND Contract.deleted=0, IF(rbFinance.code = 2, 1, IF(rbFinance.code = 3, 0, 1)), 1), IF(Event.execDate IS NOT NULL, Event.execDate, Event.setDate), Event.id))''')
                if not regionSMO:
                    cond.append(tableClientPolicy['insurer_id'].eq(insurerId))
                else:
                    tableOrganisation = db.table('Organisation').alias('Org_Area')
                    queryTable = queryTable.innerJoin(tableOrganisation, [tableOrganisation['id'].eq(tableClientPolicy['insurer_id']), tableOrganisation['deleted'].eq(0)])
                    if regionSMOCode:
                        if regionTypeSMO:
                            cond.append(tableOrganisation['area'].notlike(regionSMOCode))
                        else:
                            cond.append(tableOrganisation['area'].like(regionSMOCode))
            cols.append(u"""CASE Event.`order` WHEN 1 THEN 'плановый'
                                                           WHEN 2 THEN 'экстренный'
                                                           WHEN 3 THEN 'самотёком' 
                                                           WHEN 4 THEN 'принудительный' 
                                                           WHEN 5 THEN 'внутренний перевод' 
                                                           WHEN 6 THEN 'неотложная' END as eventOrder"""
                        )
            cols.append(getReceivedPropertyString(u'Кем доставлен', u'delivered', self.receivedActionTypeIdList))
            if deliverBy:
                cond.append(getDeliverByCond(deliverBy))
            if groupBY != '':
                recordsReceived = db.getRecordListGroupBy(queryTable, cols, cond, groupBY)
            else:
                recordsReceived = db.getRecordList(queryTable, cols, cond)
            for record in recordsReceived:
                documentLocationInfo = forceString(record.value('documentLocationInfo')).split("  ")
                hospDocumentLocation = forceString(documentLocationInfo[0]) if len(documentLocationInfo) >= 1 else ''
                documentLocationColor = forceString(documentLocationInfo[1]) if len(documentLocationInfo) > 1 else ''
                if documentTypeForTracking == u'specialValueID':
                    if hospDocumentLocation != '':
                        continue
                countEventClientFeedId = forceBool(record.value('countEventClientFeedId'))
                countEventPatronFeedId = forceBool(record.value('countEventPatronFeedId'))
                refusalToEatClient = forceBool(record.value('refusalToEatClient'))
                refusalToEatPatron = forceBool(record.value('refusalToEatPatron'))
                if (feed == 1 and not (countEventClientFeedId + countEventPatronFeedId)) or (feed == 2 and (countEventClientFeedId + countEventPatronFeedId)) or not feed or feed == 3 or feed == 4:
                    eventId = forceRef(record.value('eventId'))
                    statusObservation = forceString(record.value('statusObservation')).split('|')
                    statusObservationCode = forceString(statusObservation[0]) if len(statusObservation) >= 1 else u''
                    statusObservationName = forceString(statusObservation[1]) if len(statusObservation) >= 2 else u''
                    statusObservationColor = forceString(statusObservation[2]) if len(statusObservation) >= 3 else u''
                    statusObservationDate = forceString(statusObservation[3]) if len(statusObservation) >= 4 else u''
                    statusObservationPerson = forceString(statusObservation[4]) if len(statusObservation) >= 5 else u''
                    comfortable = forceString(record.value('comfortable'))
                    nameContract = ' '.join([forceString(record.value(name)) for name in ('numberContract', 'dateContract', 'resolutionContract')])
                    comfortableList = []
                    if comfortable:
                        comfortableList = comfortable.split("  ")
                    comfortableDate = forceDateTime(QVariant(comfortableList[0])) if len(comfortableList) >= 1 else ''
                    comfortableStatus = forceInt(QVariant(comfortableList[1])) if len(comfortableList) >= 2 else 0
                    begDate = forceDateTime(record.value('begDate'))
                    endDate = forceDateTime(record.value('endDate'))
                    policyEndDate = forceDate(record.value('policyEndDate'))
                    colorFinance = None
                    if policyEndDate:
                        if forceDate(begDate) < policyEndDate <= forceDate(begDate).addDays(3):
                            colorFinance = QtGui.QColor(Qt.yellow)
                        elif forceDate(begDate) >= policyEndDate:
                            colorFinance = QtGui.QColor(Qt.red)
                    receivedBegDateTime = forceDateTime(record.value('receivedBegDate'))
                    relativeId = forceRef(record.value('relative_id'))
                    patron = forceString(record.value('patronName'))
                    clientAllergy = forceString(record.value('clientAllergy'))
                    clientIntoleranceMedicament = forceString(record.value('clientIntoleranceMedicament'))
                    clientFeatures = '%s|%s' % (clientAllergy,  clientIntoleranceMedicament)
                    patronAllergy = forceString(record.value('patronAllergy'))
                    patronIntoleranceMedicament = forceString(record.value('patronIntoleranceMedicament'))
                    patronag = forceBool(record.value('patronag'))
                    patronFeatures = '%s|%s' % (patronAllergy,  patronIntoleranceMedicament)
                    isActionToServiceType = forceBool(record.value('isActionToServiceType'))
                    setDate = forceDate(record.value('setDate'))
                    execDate = forceDate(record.value('execDate'))
                    bedDays = updateDurationEvent(setDate, execDate if execDate.isValid() else QDate().currentDate(), begDateTimeFilter, endDateTimeFilter, forceRef(record.value('eventType_id')), isPresence=True)
                    self.begDays += forceInt(bedDays) if bedDays != u'-' else 0
                    basicMKB = forceString(record.value('Basic_MKB'))
                    MKB = forceString(record.value('MKB'))
                    if basicMKB or MKB:
                        strMKB = (basicMKB if basicMKB else u'?') + u';' + (MKB if MKB else u'?')
                    else:
                        strMKB = u''
                    item = [statusObservationCode,
                            forceString(record.value('nameFinance')),
                            nameContract,
                            countEventClientFeedId,
                            countEventPatronFeedId,
                            patron,
                            comfortableDate,
                            forceRef(record.value('client_id')),
                            eventId,
                            forceString(record.value('externalId')),
                            forceString(record.value('lastName')) + u' ' + forceString(record.value('firstName')) + u' ' + forceString(record.value('patrName')),
                            self.sex[forceInt(record.value('sex'))],
                            forceDate(record.value('birthDate')),
                            receivedBegDateTime,
                            begDate,
                            forceDate(record.value('plannedEndDate')),
                            strMKB,
                            forceString(record.value('profileName')),
                            forceString(record.value('codeBed')),
                            forceString(record.value('placement')),
                            forceString(record.value('nameOrgStructure')),
                            forceString(record.value('execPerson')),
                            forceString(record.value('namePerson')),
                            forceString(record.value('citizenship')),
                            clientFeatures,
                            patronFeatures,
                            forceString(record.value('bloodType')),
                            u'Да' if patronag else u'Нет',
                            hospDocumentLocation,
                            bedDays,
                            forceString(record.value('relegateOrg')),
                            forceString(record.value('eventOrder')),
                            forceString(record.value('delivered')),
                            forceString(record.value('codeFinance')),
                            forceString(record.value('nameBed')),
                            endDate.toString('dd.MM.yyyy hh:mm'),
                            statusObservationName + u' (' + (statusObservationDate if statusObservationDate else u'') + u' ' + (statusObservationPerson if statusObservationPerson else u'') + u')',
                            forceRef(record.value('actionId')),
                            forceRef(record.value('actionType_id')),
                            statusObservationColor,
                            comfortableStatus,
                            setDate,
                            endDate,
                            relativeId,
                            refusalToEatClient,
                            refusalToEatPatron,
                            isActionToServiceType,
                            documentLocationColor,
                            colorFinance,
                            forceString(calcAge(forceDate(record.value('birthDate')), forceDate(record.value('endDate'))))
                            ]
                    if eventId and eventId not in self.eventIdList:
                        self.eventIdList.append(eventId)
                    self.feedTextValueItems[eventId] = forceString(record.value('clientDiet'))
                    self.extraFeedTextValueItems[eventId] = forceString(record.value('patronDiet'))
                    self.items.append(item)
                    _dict = {
                        'observationCode': statusObservationCode,
                        'finance': forceString(record.value('nameFinance')),
                        'contract': nameContract,
                        'clientFeed': forceString(record.value('clientDiet')) if countEventClientFeedId else '',
                        'patronFeed': forceString(record.value('patronDiet'))if countEventPatronFeedId else '',
                        'comfortableDate': comfortableDate,
                        'bedCode': forceString(record.value('codeBed')),
                        'orgStructure': forceString(record.value('nameOrgStructure')),
                        'financeCode': forceString(record.value('codeFinance')),
                        'bedName': forceString(record.value('nameBed')),
                        'observationName': statusObservationName,
                        'observationColor': statusObservationColor,
                        'setDate': CDateTimeInfo(receivedBegDateTime),
                        'begDate': CDateTimeInfo(begDate),
                        'plannedEndDate': CDateTimeInfo(forceDateTime(record.value('plannedEndDate'))),
                        'refusalToEatClient': forceBool(record.value('refusalToEatClient')),
                        'refusalToEatPatron': forceBool(record.value('refusalToEatPatron'))
                    }
                    self.itemByName[eventId] = _dict

        movingOSIdList = []
        receivedOSIdList = []
        orgStructureIdList = []
        if quotingType:
            quotingTypeClass, quotingTypeId = quotingType
            quotingTypeList = self.getQuotingTypeIdList(quotingType)
        else:
            quotingTypeClass = None
            quotingTypeList = None
        if orgStructureId:
            treeItem = orgStructureId.internalPointer() if orgStructureId.isValid() else None
            orgStructureIdList = self.getOrgStructureIdList(orgStructureId) if treeItem and treeItem._id else []
            if orgStructureIdList:
                movingOSIdList = db.getIdList(tableOS, tableOS['id'], [tableOS['id'].inlist(orgStructureIdList), tableOS['type'].ne(4), tableOS['deleted'].eq(0)])
                receivedOSIdList = db.getIdList(tableOS, tableOS['id'], [tableOS['id'].inlist(orgStructureIdList), tableOS['type'].eq(4), tableOS['deleted'].eq(0)])


        if indexLocalClient == 2:
            if orgStructureIdList:
                if receivedOSIdList:
                    findReceivedNoEnd(orgStructureIdList, dateFeed, (quotingTypeList, quotingTypeClass), accountingSystemId, filterClientId, filterEventId, defaultOrgStructureEventTypeIdList, endDateTime = filterEndDate, begDateTimeFilter = begDateTime, endDateTimeFilter = endDateTime)
                if movingOSIdList:
                    getDataMoving(movingOSIdList, indexSex, ageFor, ageTo, permanent, _type, bedProfile, presenceDay, codeAttachType, finance, feed, dateFeed, indexLocalClient, (quotingTypeList, quotingTypeClass), accountingSystemId, filterClientId, filterEventId, codeBeds, defaultOrgStructureEventTypeIdList, begDateTime, endDateTime)
            else:
                getDataMoving([], indexSex, ageFor, ageTo, permanent, _type, bedProfile, presenceDay, codeAttachType, finance, feed, dateFeed, indexLocalClient, (quotingTypeList, quotingTypeClass), accountingSystemId, filterClientId, filterEventId, codeBeds, defaultOrgStructureEventTypeIdList, begDateTime, endDateTime)
        elif indexLocalClient == 1:
            if orgStructureIdList:
                if movingOSIdList:
                    getDataMoving(movingOSIdList, indexSex, ageFor, ageTo, permanent, _type, bedProfile, presenceDay, codeAttachType, finance, feed, dateFeed, indexLocalClient, (quotingTypeList, quotingTypeClass), accountingSystemId, filterClientId, filterEventId, codeBeds, defaultOrgStructureEventTypeIdList, begDateTime, endDateTime)
            else:
                getDataMoving([], indexSex, ageFor, ageTo, permanent, _type, bedProfile, presenceDay, codeAttachType, finance, feed, dateFeed, indexLocalClient, (quotingTypeList, quotingTypeClass), accountingSystemId, filterClientId, filterEventId, codeBeds, defaultOrgStructureEventTypeIdList, begDateTime, endDateTime)
        else:
            if orgStructureIdList:
                if receivedOSIdList:
                    findReceivedNoEnd(receivedOSIdList, dateFeed, (quotingTypeList, quotingTypeClass), accountingSystemId, filterClientId, filterEventId, defaultOrgStructureEventTypeIdList, endDateTime=filterEndDate, begDateTimeFilter=begDateTime, endDateTimeFilter=endDateTime)
                if movingOSIdList:
                    getDataMoving(movingOSIdList, indexSex, ageFor, ageTo, permanent, _type, bedProfile, presenceDay, codeAttachType, finance, feed, dateFeed, indexLocalClient, (quotingTypeList, quotingTypeClass), accountingSystemId, filterClientId, filterEventId, codeBeds, defaultOrgStructureEventTypeIdList, begDateTime, endDateTime)
            else:
                findReceivedNoEnd([], dateFeed, (quotingTypeList, quotingTypeClass), accountingSystemId, filterClientId, filterEventId, defaultOrgStructureEventTypeIdList, endDateTime = filterEndDate, begDateTimeFilter = begDateTime, endDateTimeFilter = endDateTime)
                getDataMoving([], indexSex, ageFor, ageTo, permanent, _type, bedProfile, presenceDay, codeAttachType, finance, feed, dateFeed, indexLocalClient, (quotingTypeList, quotingTypeClass), accountingSystemId, filterClientId, filterEventId, codeBeds, defaultOrgStructureEventTypeIdList, begDateTime, endDateTime)
        for col, order in self.headerSortingCol.items():
            self.sort(col, order)

    def getClientFIO(self, row):
        return self.items[row][self.clientFIOColumn]

    def getPatronId(self, row):
        return self.items[row][self.patronIdColumn]

    def getReceivedDate(self, row):
        return self.items[row][self.receivedDateCol]

    def getActionId(self, row):
        return self.items[row][self.actionIdColumn]

    def getActionTypeId(self, row):
        return self.items[row][self.actionTypeIdColumn]

    def getSetDate(self, row):
        return self.items[row][self.setDateColumn]

    def getEndDate(self, row):
        return self.items[row][self.actionEndDateColumn]

    def getPersonName(self, row):
        return self.items[row][self.namePersonColumn]

    def getBegDays(self):
        return self.begDays

    def sort(self, col, order=Qt.AscendingOrder):
        self.headerSortingCol = {col: order}
        reverse = order == Qt.DescendingOrder
        alphabet = u'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
        alphabet_dict = {char: index for index, char in enumerate(alphabet)}
        def sortByRussia(x):
            customString = forceString(x[col]).lower() if x else u''
            return [alphabet_dict.get(char, len(alphabet)) for char in customString]

        if col == self.bedDaysCol:
            self.items.sort(key=lambda x: forceInt(0 if x[col] == '-' else x[col]) if x else None, reverse=reverse)
        elif col in [self.clientColumn, self.eventColumn]:
            self.items.sort(key=lambda x: forceInt(x[col]) if x else None, reverse=reverse)
        elif col in [self.birthDateCol, self.hospDateCol, self.receivedDateCol, self.plannedEndDateColumn]:
            self.items.sort(key=lambda x: forceDateTime(x[col]) if x else None, reverse=reverse)
        elif col in [self.defaultOrderCol]:
            self.items.sort(key=sortByRussia, reverse = reverse)
        else:
            self.items.sort(key=lambda x: forceString(x[col]).lower() if x else None, reverse=reverse)
        self.reset()






class CReceivedModel(CMonitoringModel):
    column = [u'С', u'И', u'Д', u'П', u'Номер', u'Код', u'Карта', u'ФИО', u'Пол', u'Дата рождения', u'Госпитализирован', u'Поступил', u'Выбыл', u'MKB', u'Профиль', u'Подразделение', u'Лечащий врач', u'Гражданство',  u'Место вызова', u'М', u'Направитель']
    statusObservationCol = 0
    financeCol = 1
    feedCol = 3
    clientColumn = 4
    eventColumn = 5
    defaultOrderCol = 7
    birthDateCol = 9
    hospDateCol = 10
    receivedDateCol = 11
    leavedDateCol = 12
    MKBColumn = 13
    profileCol = 14
    documentLocationCol = 19
    codeFinanceCol = 21
    bedNameCol = 22
    statusObservationNameCol = 23
    colorStatusObservationCol = 24
    docLocalColorCol = 25
    colorFinanceCol = 26
    actionIdColumn = 27
    ageCol = 28

    def __init__(self, parent):
        CMonitoringModel.__init__(self, parent)
        self.items = []
        self._cols = []
        self.statusObservation = None
        self.itemByName = {}
        self.feedTextValueItems = {}
        self.headerSortingCol = {}

    def getActionId(self, row):
        return self.items[row][self.actionIdColumn]

    def cols(self):
        self._cols = [CCol(u'Статус наблюдения',     ['statusObservation'], 20, 'l'),
                      CCol(u'Код ИФ',                ['nameFinance'], 20, 'l'),
                      CCol(u'Договор',               ['contract'], 20, 'l'),
                      CCol(u'Питание',               ['feed'], 20, 'l'),
                      CCol(u'Номер',                 ['client_id'], 20, 'l'),
                      CCol(u'Код события',                         ['event_id'], 20, 'l'),
                      CCol(u'Карта',                 ['externalId'], 20, 'l'),
                      CCol(u'ФИО',                   ['lastName', 'firstName', 'patrName'], 30, 'l'),
                      CCol(u'Пол',                   ['sex'], 15, 'l'),
                      CCol(u'Дата рождения',         ['birthDate'], 20, 'l'),
                      CCol(u'Госпитализирован',      ['begDateReceived'], 20, 'l'),
                      CCol(u'Поступил',              ['begDate'], 20, 'l'),
                      CCol(u'Выбыл',                 ['endDate'], 20, 'l'),
                      CCol(u'MKB',                   ['MKB'], 20, 'l'),
                      CCol(u'Профиль',                 ['profileName'], 30, 'l'),
                      CCol(u'Подразделение',         ['nameOS'], 30, 'l'),
                      CCol(u'Лечащий врач',         ['namePerson'], 30, 'l'),
                      CCol(u'Гражданство',           ['citizenship'], 30, 'l'),
                      CCol(u'Место вызова',          ['placeCallValue'], 30, 'l'),
                      CCol(u'Место нахождения учетного документа',['hospDocumentLocation'], 30, 'l'),
                      CCol(u'Направитель', ['relegateOrg'], 30, 'l'),
                      ]
        return self._cols

    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return QVariant(self.column[section])
            elif role == Qt.ToolTipRole:
                if section == 0:
                    return QVariant(u'Статус наблюдения пациента')
                elif section == 1:
                    return QVariant(u'Источник финансирования (код)')
                elif section == 2:
                    return QVariant(u'Договор')
                elif section == 3:
                    return QVariant(u'Питание')
                elif section == self.MKBColumn:
                    return QVariant(u'Диагноз направителя;Текущий диагноз')
                elif section == 18:
                    return QVariant(u'Место нахождения учетного документа')
                elif section == self.eventColumn:
                    return QVariant(u'Код события')
        return QVariant()

    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if role == Qt.BackgroundColorRole:
            if column == self.statusObservationCol and self.items[row][column]:
                return toVariant(QtGui.QColor(self.items[row][self.colorStatusObservationCol]))
            elif len(forceString(self.items[row][self.MKBColumn])) <= 0:
               return toVariant(QtGui.QColor(200, 230, 240))
            elif column == self.financeCol:
                colorFinance = self.items[row][self.colorFinanceCol]
                if colorFinance:
                    return toVariant(colorFinance)
            elif column == self.documentLocationCol:
                docLocalColor = self.items[row][self.docLocalColorCol]
                if docLocalColor:
                    return toVariant(QtGui.QColor(docLocalColor))
        if role == Qt.DisplayRole:
            if column in [self.hospDateCol, self.receivedDateCol, self.leavedDateCol]:
                item = self.items[row]
                return toVariant(item[column].toString('dd.MM.yyyy hh:mm'))
            elif column == self.birthDateCol:
                item = self.items[row]
                return toVariant(forceString(item[column]) + u' (' + item[self.ageCol] + u')')
            elif column == self.feedCol:
                return toVariant(self.feedTextValueItems[self.getEventId(row)])
            else:
                item = self.items[row]
                return toVariant(item[column])
        elif role == Qt.CheckStateRole:
            if column == self.feedCol:
                item = self.items[row]
                return toVariant(Qt.Checked if item[column] else Qt.Unchecked)
        elif role == Qt.ToolTipRole:
            if column == self.statusObservationCol:
                item = self.items[row]
                if item[self.statusObservationCol]:
                    return QVariant(item[self.statusObservationCol] + u' ' + item[self.statusObservationNameCol])
                else:
                    return QVariant()
            elif column == self.financeCol:
                item = self.items[row]
                return QVariant(item[self.codeFinanceCol] + u' ' + item[column])
            elif column == self.MKBColumn:
                return QVariant(u'Диагноз направителя;Текущий диагноз')
            elif column == self.profileCol:
                item = self.items[row]
                return QVariant(forceString(item[column]) + u' ' + item[self.bedNameCol])
        return QVariant()

    def loadData(self, dialogParams):
        self.items = []
        self.itemByName = {}
        self.feedTextValueItems = {}
        filterBegDate = dialogParams.get('filterBegDate', None)
        filterEndDate = dialogParams.get('filterEndDate', None)
        filterBegTime = dialogParams.get('filterBegTime', None)
        filterEndTime = dialogParams.get('filterEndTime', None)
        if not filterBegTime.isNull():
            begDateTime = QDateTime(filterBegDate, filterBegTime)
            filterBegDate = begDateTime
        if not filterEndTime.isNull():
            endDateTime = QDateTime(filterEndDate, filterEndTime)
            filterEndDate = endDateTime
        indexSex = dialogParams.get('indexSex', 0)
        ageFor = dialogParams.get('ageFor', 0)
        ageTo = dialogParams.get('ageTo', 150)
        order = dialogParams.get('order', -1)
        eventTypeId = dialogParams.get('eventTypeId', None)
        placeCall = dialogParams.get('placeCall', '')
        orgStructureId = dialogParams.get('orgStructureId', None)
        profile = dialogParams.get('treatmentProfile', None)
        codeAttachType = dialogParams.get('codeAttachType', None)
        indexLocalClient = dialogParams.get('indexLocalClient', None)
        finance = dialogParams.get('finance', None)
        contractId = dialogParams.get('contractId', None)
        feed = dialogParams.get('feed', None)
        dateFeed = dialogParams.get('dateFeed', None)
        personId = dialogParams.get('personId', None)
        insurerId = dialogParams.get('insurerId', None)
        regionSMO, regionTypeSMO, regionSMOCode = dialogParams.get('regionSMO', (False, 0, None))
        personExecId = dialogParams.get('personExecId', None)
        quotingType = dialogParams.get('quotingType', None)
        accountingSystemId = dialogParams.get('accountingSystemId', None)
        filterClientId = dialogParams.get('filterClientId', None)
        filterEventId = dialogParams.get('filterEventId', None)
        statusObservation = dialogParams.get('statusObservation', None)
        index = dialogParams.get('receivedIndex', 0)
        defaultOrgStructureEventTypeIdList = dialogParams.get('defaultOrgStructureEventTypeIdList', [])
        deliverBy = dialogParams.get('deliverBy', None)
        MKBFilter = dialogParams['MKBFilter']
        MKBFrom   = dialogParams['MKBFrom']
        MKBTo     = dialogParams['MKBTo']
        relegateOrg = dialogParams.get('relegateOrg', None)
        orgStructureIdList = []

        self.statusObservation = statusObservation
        if orgStructureId:
            treeItem = orgStructureId.internalPointer() if orgStructureId.isValid() else None
            orgStructureIdList = self.getOrgStructureIdList(orgStructureId) if treeItem and treeItem._id else []
        if quotingType:
            quotingTypeClass, quotingTypeId = quotingType
            quotingTypeList = self.getQuotingTypeIdList(quotingType)
        else:
            quotingTypeClass = None
            quotingTypeList = None
        db = QtGui.qApp.db
        tableAPT = db.table('ActionPropertyType')
        tableAP = db.table('ActionProperty')
        tableActionType = db.table('ActionType')
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        tableClient = db.table('Client')
        tableClientPolicy = db.table('ClientPolicy')
        tableOS = db.table('OrgStructure')
        tablePWS = db.table('vrbPersonWithSpeciality')
        tableAPOS = db.table('ActionProperty_OrgStructure')
        tableClientAttach = db.table('ClientAttach')
        tableRBAttachType = db.table('rbAttachType')
        tableContract = db.table('Contract')
        tableRBFinance = db.table('rbFinance')
        tableRBFinanceBC = db.table('rbFinance').alias('rbFinanceByContract')
        tableEvent_Feed = db.table('Event_Feed')
        tableStatusObservation= db.table('Client_StatusObservation')
        tableOrg = db.table('Organisation')


        def getActionIdList(dialogParams, actionTypeIdListByFlatCode):
            filterBegDate = dialogParams.get('filterBegDate', None)
            filterEndDate = dialogParams.get('filterEndDate', None)
            filterBegTime = dialogParams.get('filterBegTime', None)
            filterEndTime = dialogParams.get('filterEndTime', None)
            if not filterBegTime.isNull():
                begDateTime = QDateTime(filterBegDate, filterBegTime)
                filterBegDate = begDateTime
            if not filterEndTime.isNull():
                endDateTime = QDateTime(filterEndDate, filterEndTime)
                filterEndDate = endDateTime
            db = QtGui.qApp.db
            tableAction = db.table('Action')
            cond = [ tableAction['actionType_id'].inlist(actionTypeIdListByFlatCode),
                     tableAction['deleted'].eq(0),
                   ]
            if not forceBool(filterBegDate.date()):
                filterBegDate = QDate.currentDate()
                cond.append(db.joinOr([tableAction['begDate'].isNull(), tableAction['begDate'].eq(filterBegDate)]))
            else:
                cond.append(tableAction['begDate'].isNotNull())
                cond.append(tableAction['begDate'].ge(filterBegDate))
            if forceBool(filterEndDate.date()):
                cond.append(tableAction['begDate'].isNotNull())
                cond.append(tableAction['begDate'].le(filterEndDate))
            return db.getDistinctIdList(tableAction, [tableAction['id']], cond)



        def findMovingAfterReceived(filterBegDate = None, filterEndDate = None, indexLocalClient = 0, dateFeed = None, orgStructureIdList = [], quotingTypeList = None, accountingSystemId = None, filterClientId = None, filterEventId = None, defaultOrgStructureEventTypeIdList=[]):
            if not movingActionIdList:
                self.items = []
                self.reset()
                return
            nameProperty = u'Отделение пребывания'
            cols = [tableAction['id'],
                    tableEvent['id'].alias('eventId'),
                    tableEvent['client_id'],
                    tableEvent['externalId'],
                    tableClient['lastName'],
                    tableClient['firstName'],
                    tableClient['patrName'],
                    tableClient['sex'],
                    tableClient['birthDate'],
                    tableAction['begDate'],
                    tableAction['endDate'],
                    tableAction['MKB'].alias(u'actionMKB'),
                    tableEvent['setDate'],
                    tableContract['number'].alias('numberContract'),
                    tableContract['date'].alias('dateContract'),
                    tableContract['resolution'].alias('resolutionContract'),
                    tablePWS['name'].alias('namePerson'),
                    tableOrg['shortName'].alias('relegateOrg')
                    ]
            cols.append(getReceivedMKB())
            cols.append(getHospDocumentLocationInfo())
            cols.append(getReceivedBegDate(self.receivedActionTypeIdList))
            cols.append(u'IF(OrgStructure.id IS NOT NULL AND OrgStructure.deleted=0, OrgStructure.name, NULL) AS nameOS')
            if not dateFeed:
                dateFeed = QDate().currentDate().addDays(1)
            cols.append(getEventFeedId(u'', tableEvent_Feed['date'].formatValue(dateFeed), u''' AS countEventFeedId'''))
            cols.append(getDietCode(u'0', db.formatDate(dateFeed), u''' AS clientDiet'''))
            cols.append(getHBProfileFromBed())
            cols.append(getStatusObservation())
            cols.append("""getClientCitizenshipTitle(Client.id, Action.begDate) as citizenship""")
            cols.append('%s as placeCallValue'%getStringPropertyValue(u'Место вызова'))
            queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
            queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
            queryTable = queryTable.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
            queryTable = queryTable.innerJoin(tableAP, tableAP['type_id'].eq(tableAPT['id']))
            queryTable = queryTable.leftJoin(tableAPOS, tableAPOS['id'].eq(tableAP['id']))
            queryTable = queryTable.leftJoin(tableOS, tableOS['id'].eq(tableAPOS['value']))
            queryTable = queryTable.leftJoin(tablePWS, tablePWS['id'].eq(tableAction['person_id']))
            queryTable = queryTable.leftJoin(tableOrg, tableEvent['relegateOrg_id'].eq(tableOrg['id']))
            cond = [tableAction['actionType_id'].inlist(self.movingActionTypeIdList),
                    tableAction['deleted'].eq(0),
                    tableEvent['deleted'].eq(0),
                    tableAP['deleted'].eq(0),
                    tableAPT['deleted'].eq(0),
                    tableClient['deleted'].eq(0),
                    tableAP['action_id'].eq(tableAction['id'])
                   ]
            if contractId:
                cond.append(tableContract['id'].eq(contractId))
            if MKBFilter:
                cond.append(isMKB(MKBFrom, MKBTo))
            if order:
               cond.append(tableEvent['order'].eq(order))
            if eventTypeId:
               cond.append(tableEvent['eventType_id'].eq(eventTypeId))
            if placeCall and placeCall != u'не определено':
                cond.append(getActionTypeStringPropertyValue(u'Место вызова', self.receivedActionTypeIdList, placeCall))
            tableEventType = db.table('EventType')
            queryTable = queryTable.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))

            if QtGui.qApp.userHasAnyRight([urHBVisibleOwnEventsParentOrgStructureOnly, urHBVisibleOwnEventsOrgStructureOnly]):
                tableExecPerson = db.table('Person')
                queryTable = queryTable.leftJoin(tableExecPerson, tableExecPerson['id'].eq(tableEvent['execPerson_id']))
                uOrgStructureId = forceRef(db.translate('Person', 'id', QtGui.qApp.userId, 'orgStructure_id'))
                if QtGui.qApp.userHasRight(urHBVisibleOwnEventsParentOrgStructureOnly):
                    parentOrgStructure = getParentOrgStructureId(uOrgStructureId)
                    uOrgStructureList = getOrgStructureDescendants(parentOrgStructure if parentOrgStructure else uOrgStructureId)
                    cond.append(db.joinOr([tableExecPerson['orgStructure_id'].inlist(uOrgStructureList), tableEventType['ignoreVisibleRights'].eq(1)]))
                elif QtGui.qApp.userHasRight(urHBVisibleOwnEventsOrgStructureOnly):
                    uOrgStructureList = getOrgStructureDescendants(uOrgStructureId)
                    cond.append(db.joinOr([tableExecPerson['orgStructure_id'].inlist(uOrgStructureList), tableEventType['ignoreVisibleRights'].eq(1)]))

            cond.append(u"(EventType.medicalAidType_id IN (SELECT rbMedicalAidType.id from rbMedicalAidType where rbMedicalAidType.code IN ('1', '2', '3', '7')))")
            cond.append(tableAPT['name'].like(nameProperty))
            if defaultOrgStructureEventTypeIdList:
                cond.append(tableEvent['eventType_id'].inlist(defaultOrgStructureEventTypeIdList))
            if personId:
               cond.append(tableEvent['execPerson_id'].eq(personId))
            if personExecId:
               cond.append(tableAction['person_id'].eq(personExecId))
            if self.statusObservation:
                cond.append(existsStatusObservation(self.statusObservation))
            if accountingSystemId and filterClientId:
                tableIdentification = db.table('ClientIdentification')
                queryTable = queryTable.innerJoin(tableIdentification, tableIdentification['client_id'].eq(tableClient['id']))
                cond.append(tableIdentification['accountingSystem_id'].eq(accountingSystemId))
                cond.append(tableIdentification['identifier'].eq(filterClientId))
                cond.append(tableIdentification['deleted'].eq(0))
            elif filterClientId:
                cond.append(tableClient['id'].eq(filterClientId))
            if filterEventId:
                cond.append(tableEvent['externalId'].eq(filterEventId))
            if not forceBool(filterBegDate.date()):
                filterBegDate = QDate().currentDate()
                cond.append(db.joinOr([tableAction['begDate'].isNull(), tableAction['begDate'].eq(filterBegDate)]))
            else:
                cond.append(tableAction['begDate'].isNotNull())
                cond.append(tableAction['begDate'].ge(filterBegDate))
            if forceBool(filterEndDate.date()):
                cond.append(tableAction['begDate'].isNotNull())
                cond.append(tableAction['begDate'].le(filterEndDate))
            if orgStructureIdList:
                cond.append(tableOS['deleted'].eq(0))
                cond.append(tableAPOS['value'].inlist(orgStructureIdList))
            if relegateOrg:
                cond.append(tableEvent['relegateOrg_id'].eq(relegateOrg))
            if quotingTypeList:
                quotingTypeIdList, quotingTypeClass = quotingTypeList
                if quotingTypeClass is not None:
                    cond.append(getDataClientQuoting(u'Квота', quotingTypeIdList))
            if feed == 1:
                cond.append('NOT %s'%(getEventFeedId(u'',tableEvent_Feed['date'].formatValue(dateFeed))))
            elif feed == 2:
                cond.append('%s'%(getEventFeedId(u'',tableEvent_Feed['date'].formatValue(dateFeed), alias=u'', refusalToEat = 0)))
            elif feed == 3:
                cond.append('%s'%(getEventFeedId(u'',tableEvent_Feed['date'].formatValue(dateFeed), alias=u'', refusalToEat = 1)))
            if QtGui.qApp.defaultHospitalBedFinanceByMoving() == 2:
                cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.code, IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinanceByContract.code, NULL)) AS codeFinance')
                cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.name, IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinanceByContract.name, NULL)) AS nameFinance')
                cols.append(getClientPolicyForDate())
                if finance:
                    cond.append('''((Action.finance_id IS NOT NULL AND Action.deleted=0 AND Action.finance_id = %s) OR (Contract.id IS NOT NULL AND Contract.deleted=0 AND Contract.finance_id = %s))'''%(str(finance), str(finance)))
                    queryTable = queryTable.innerJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
                    queryTable = queryTable.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.innerJoin(tableRBFinanceBC, tableRBFinanceBC['id'].eq(tableContract['finance_id']))
                else:
                    queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
                    queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.leftJoin(tableRBFinanceBC, tableRBFinanceBC['id'].eq(tableContract['finance_id']))
            elif QtGui.qApp.defaultHospitalBedFinanceByMoving() == 1:
                cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.code, NULL) AS codeFinance')
                cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.name, NULL) AS nameFinance')
                queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                if finance:
                    cond.append('''(Action.finance_id IS NOT NULL AND Action.deleted=0 AND Action.finance_id = %s)'''%(str(finance)))
                    queryTable = queryTable.innerJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
                else:
                    queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
                cols.append(getActionClientPolicyForDate())
            else:
                cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.code, NULL) AS codeFinance')
                cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.name, NULL) AS nameFinance')
                cols.append(getContractClientPolicyForDate())
                if finance:
                    cond.append(tableContract['deleted'].eq(0))
                    cond.append(tableRBFinance['id'].eq(finance))
                    queryTable = queryTable.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.innerJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
                else:
                    queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
            cond.append('(Contract.id IS NOT NULL AND Contract.deleted=0) OR (Contract.id IS NULL)')
            if forceInt(codeAttachType) > 0:
                cond.append(tableRBAttachType['code'].eq(codeAttachType))
                queryTable = queryTable.innerJoin(tableClientAttach, tableClient['id'].eq(tableClientAttach['client_id']))
                queryTable = queryTable.innerJoin(tableRBAttachType, tableClientAttach['attachType_id'].eq(tableRBAttachType['id']))
            if indexSex > 0:
                cond.append(tableClient['sex'].eq(indexSex))
            if ageFor <= ageTo:
                cond.append(getAgeRangeCond(ageFor, ageTo))
            cond.append('''NOT %s'''%(getTransferPropertyIn(u'Переведен из отделения')))
            if profile:
                cond.append(getHospitalBedProfileFromBed(profile))
            if deliverBy:
                cond.append(getDeliverByCond(deliverBy))
            if insurerId or regionSMO:
                queryTable = queryTable.innerJoin(tableClientPolicy,
                                                  u'''(ClientPolicy.id = getClientPolicyIdForDate(Client.id, IF(Contract.id IS NOT NULL AND Contract.deleted=0, IF(rbFinance.code = 2, 1, IF(rbFinance.code = 3, 0, 1)), 1), IF(Event.execDate IS NOT NULL, Event.execDate, Event.setDate), Event.id))''')
                if not regionSMO:
                    cond.append(tableClientPolicy['insurer_id'].eq(insurerId))
                else:
                    tableOrganisation = db.table('Organisation').alias('Org_Area')
                    queryTable = queryTable.innerJoin(tableOrganisation, [tableOrganisation['id'].eq(tableClientPolicy['insurer_id']), tableOrganisation['deleted'].eq(0)])
                    if regionSMOCode:
                        if regionTypeSMO:
                            cond.append(tableOrganisation['area'].notlike(regionSMOCode))
                        else:
                            cond.append(tableOrganisation['area'].like(regionSMOCode))
            recordsMoving = db.getRecordList(queryTable, cols, cond)
            for record in recordsMoving:
                countEventFeedId = forceBool(record.value('countEventFeedId'))
                if (feed == 1 and not countEventFeedId) or (feed == 2 and countEventFeedId) or not feed or feed == 3:
                    statusObservation = forceString(record.value('statusObservation')).split('|')
                    statusObservationCode = forceString(statusObservation[0]) if len(statusObservation)>=1 else u''
                    statusObservationName = forceString(statusObservation[1]) if len(statusObservation)>=2 else u''
                    statusObservationColor = forceString(statusObservation[2]) if len(statusObservation)>=3 else u''
                    statusObservationDate = forceString(statusObservation[3]) if len(statusObservation)>=4 else u''
                    statusObservationPerson = forceString(statusObservation[4]) if len(statusObservation)>=5 else u''
                    begDate = forceDate(record.value('begDate'))
                    policyEndDate = forceDate(record.value('policyEndDate'))
                    colorFinance = None
                    if policyEndDate:
                        if begDate < policyEndDate <= begDate.addDays(3):
                           colorFinance = QtGui.QColor(Qt.yellow)
                        elif begDate >= policyEndDate:
                            colorFinance = QtGui.QColor(Qt.red)
                    nameContract = ' '.join([forceString(record.value(name)) for name in ('numberContract', 'dateContract', 'resolutionContract')])
                    documentLocationInfo  = forceString(record.value('documentLocationInfo')).split("  ")
                    hospDocumentLocation  = forceString(documentLocationInfo[0]) if len(documentLocationInfo)>=1 else ''
                    documentLocationColor = forceString(documentLocationInfo[1]) if len(documentLocationInfo)>1 else ''
                    actionMKB = forceString(record.value('actionMKB'))
                    MKB = forceString(record.value('MKB'))
                    if actionMKB or MKB:
                        strMKB = (actionMKB if actionMKB else u'?') + u';' + (MKB if MKB else u'?')
                    else:
                        strMKB = u''
                    item = [statusObservationCode,
                            forceString(record.value('nameFinance')),
                            nameContract,
                            countEventFeedId,
                            forceRef(record.value('client_id')),
                            forceRef(record.value('eventId')),
                            forceString(record.value('externalId')),
                            forceString(record.value('lastName')) + u' ' + forceString(record.value('firstName')) + u' ' + forceString(record.value('patrName')),
                            self.sex[forceInt(record.value('sex'))],
                            forceDate(record.value('birthDate')),
                            forceDateTime(record.value('receivedBegDate')),
                            forceDateTime(record.value('begDate')),
                            forceDateTime(record.value('endDate')),
                            strMKB,
                            forceString(record.value('profileName')),
                            forceString(record.value('nameOrgStructure')),
                            forceString(record.value('namePerson')),
                            forceString(record.value('citizenship')),
                            forceString(record.value('placeCallValue')), 
                            hospDocumentLocation,
                            forceString(record.value('relegateOrg')),
                            forceString(record.value('codeFinance')),
                            '', #bedName
                            statusObservationName + u' (' + (statusObservationDate if statusObservationDate else u'') + u' ' + (statusObservationPerson if statusObservationPerson else u'') + u')',
                            statusObservationColor,
                            documentLocationColor,
                            colorFinance,
                            forceRef(record.value('id')), # actionId
                            forceString(calcAge(forceDate(record.value('birthDate')), forceDate(record.value('endDate'))))
                            ]
                    eventId = forceRef(record.value('eventId'))
                    self.feedTextValueItems[eventId] = forceString(record.value('clientDiet'))
                    self.items.append(item)
                    _dict = {
                            'observationCode': statusObservationCode,
                            'finance': forceString(record.value('nameFinance')),
                            'clientFeed': countEventFeedId,
                            'contract': nameContract,
                            'bedCode': '',
                            'orgStructure': forceString(record.value('nameOrgStructure')),
                            'person': forceString(record.value('namePerson')),
                            'financeCode': forceString(record.value('codeFinance')),
                            'bedName': '',
                            'observationName': statusObservationName,
                            'observationColor': statusObservationColor,
                            'setDate': CDateTimeInfo(forceDateTime(record.value('receivedBegDate'))),
                            'begDate': CDateTimeInfo(forceDateTime(record.value('begDate'))),
                            'endDate': CDateTimeInfo(forceDateTime(record.value('endDate'))),
                            'profile' : forceString(record.value('profileName'))
                        }
                    self.itemByName[eventId] = _dict
            return None

        def findReceived(filterBegDate = None, filterEndDate = None, orgStructureIdList = [], dateFeed = None, quotingTypeList = None, accountingSystemId = None, filterClientId = None, filterEventId = None, defaultOrgStructureEventTypeIdList=[], noMovingAndLeaved = False, isAmbulanceReceived = False):
            if not receivedActionIdList:
                self.items = []
                self.reset()
                return
            cols = [tableAction['id'],
                    tableEvent['id'].alias('eventId'),
                    tableEvent['client_id'],
                    tableEvent['externalId'],
                    tableClient['lastName'],
                    tableClient['firstName'],
                    tableClient['patrName'],
                    tableClient['sex'],
                    tableClient['birthDate'],
                    tableAction['begDate'],
                    tableAction['endDate'],
                    tableAction['MKB'].alias(u'actionMKB'),
                    tableEvent['setDate'],
                    tableEvent['execDate'],
                    tableContract['number'].alias('numberContract'),
                    tableContract['date'].alias('dateContract'),
                    tableContract['resolution'].alias('resolutionContract'),
                    getDataOrgStructureName(u'Направлен в отделение'),
                    tablePWS['name'].alias('namePerson'),
                    tableOrg['shortName'].alias('relegateOrg')
                    ]
            cols.append(getReceivedMKB())
            cols.append(getReceivedBegDate(self.receivedActionTypeIdList))
            cols.append(getOSHBP())
            cols.append("""getClientCitizenshipTitle(Client.id, Action.begDate) as citizenship""")
            cols.append('%s as placeCallValue'%getStringPropertyValue(u'Место вызова'))
            if not dateFeed:
                dateFeed = QDate().currentDate().addDays(1)
            cols.append(getEventFeedId(u'', db.formatDate(dateFeed), u''' AS countEventFeedId'''))
            cols.append(getDietCode(u'0', db.formatDate(dateFeed), u''' AS clientDiet'''))
            cols.append(getStatusObservation())
            cols.append(getHospDocumentLocationInfo())
            queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
            queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
            queryTable = queryTable.leftJoin(tablePWS, tablePWS['id'].eq(tableAction['person_id']))
            queryTable = queryTable.leftJoin(tableOrg, tableEvent['relegateOrg_id'].eq(tableOrg['id']))
            cond = [tableAction['actionType_id'].inlist(self.receivedActionTypeIdList),
                    tableAction['deleted'].eq(0),
                    tableEvent['deleted'].eq(0),
                    tableClient['deleted'].eq(0),
                    tableAction['endDate'].isNotNull()
                   ]
            if contractId:
                cond.append(tableContract['id'].eq(contractId))
            if MKBFilter:
                cond.append(isMKB(MKBFrom, MKBTo))
            if relegateOrg:
                cond.append(tableEvent['relegateOrg_id'].eq(relegateOrg))
            if order:
               cond.append(tableEvent['order'].eq(order))
            if eventTypeId:
               cond.append(tableEvent['eventType_id'].eq(eventTypeId))
            if placeCall and placeCall != u'не определено':
                cond.append(getActionTypeStringPropertyValue(u'Место вызова', self.receivedActionTypeIdList, placeCall))
            if profile:
                cond.append(getPropertyAPHBP(profile, False))
            tableEventType = db.table('EventType')
            queryTable = queryTable.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))

            if QtGui.qApp.userHasAnyRight([urHBVisibleOwnEventsParentOrgStructureOnly, urHBVisibleOwnEventsOrgStructureOnly]):
                tableExecPerson = db.table('Person')
                queryTable = queryTable.leftJoin(tableExecPerson, tableExecPerson['id'].eq(tableEvent['execPerson_id']))
                uOrgStructureId = forceRef(db.translate('Person', 'id', QtGui.qApp.userId, 'orgStructure_id'))
                if QtGui.qApp.userHasRight(urHBVisibleOwnEventsParentOrgStructureOnly):
                    parentOrgStructure = getParentOrgStructureId(uOrgStructureId)
                    uOrgStructureList = getOrgStructureDescendants(parentOrgStructure if parentOrgStructure else uOrgStructureId)
                    cond.append(db.joinOr([tableExecPerson['orgStructure_id'].inlist(uOrgStructureList), tableEventType['ignoreVisibleRights'].eq(1)]))
                elif QtGui.qApp.userHasRight(urHBVisibleOwnEventsOrgStructureOnly):
                    uOrgStructureList = getOrgStructureDescendants(uOrgStructureId)
                    cond.append(db.joinOr([tableExecPerson['orgStructure_id'].inlist(uOrgStructureList), tableEventType['ignoreVisibleRights'].eq(1)]))

            cond.append(u"(EventType.medicalAidType_id IN (SELECT rbMedicalAidType.id from rbMedicalAidType where rbMedicalAidType.code IN ('1', '2', '3', '7')))")
            if defaultOrgStructureEventTypeIdList:
                cond.append(tableEvent['eventType_id'].inlist(defaultOrgStructureEventTypeIdList))
            if personId:
               cond.append(tableEvent['execPerson_id'].eq(personId))
            if personExecId:
               cond.append(tableAction['person_id'].eq(personExecId))
            if self.statusObservation:
                cond.append(existsStatusObservation(self.statusObservation))
            if accountingSystemId and filterClientId:
                tableIdentification = db.table('ClientIdentification')
                queryTable = queryTable.innerJoin(tableIdentification, tableIdentification['client_id'].eq(tableClient['id']))
                cond.append(tableIdentification['accountingSystem_id'].eq(accountingSystemId))
                cond.append(tableIdentification['identifier'].eq(filterClientId))
                cond.append(tableIdentification['deleted'].eq(0))
            elif filterClientId:
                cond.append(tableClient['id'].eq(filterClientId))
            if filterEventId:
                cond.append(tableEvent['externalId'].eq(filterEventId))
            if not forceBool(filterBegDate.date()):
                filterBegDate = QDate().currentDate()
                cond.append(db.joinOr([tableAction['begDate'].isNull(), tableAction['begDate'].eq(filterBegDate)]))
            else:
                cond.append(tableAction['begDate'].isNotNull())
                cond.append(tableAction['begDate'].ge(filterBegDate))
            if forceBool(filterEndDate.date()):
                cond.append(tableAction['begDate'].isNotNull())
                cond.append(tableAction['begDate'].le(filterEndDate))
            if quotingTypeList:
                quotingTypeIdList, quotingTypeClass = quotingTypeList
                if quotingTypeClass is not None:
                    cond.append(getDataClientQuoting(u'Квота', quotingTypeIdList))
            if not isAmbulanceReceived:
                queryTable = queryTable.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
                queryTable = queryTable.innerJoin(tableAP, tableAP['type_id'].eq(tableAPT['id']))
                queryTable = queryTable.innerJoin(tableAPOS, tableAPOS['id'].eq(tableAP['id']))
                queryTable = queryTable.innerJoin(tableOS, tableOS['id'].eq(tableAPOS['value']))
                cond.append(tableAPT['name'].like(u'Направлен в отделение'))
                cond.append(tableAP['deleted'].eq(0))
                cond.append(tableAPT['deleted'].eq(0))
                cond.append(tableAP['action_id'].eq(tableAction['id']))
                cond.append(tableOS['deleted'].eq(0))
                if orgStructureIdList:
                    cond.append(tableAPOS['value'].inlist(orgStructureIdList))
            else:
                cond.append('''NOT %s'''% (getActionPropertyTypeName(u'Направлен в отделение')))
            if noMovingAndLeaved:
                movingIdList = self.movingActionTypeIdList
                leavedIdList = self.leavedActionTypeIdList
                cond.append('''NOT EXISTS(SELECT AM.id FROM Action AS AM WHERE AM.actionType_id IN (%s) AND AM.deleted=0 AND
AM.event_id = Event.id)'''%(','.join(forceString(movingId) for movingId in self.movingActionTypeIdList if movingId)))
                if not isAmbulanceReceived:
                    cond.append('''NOT EXISTS(SELECT AM.id FROM Action AS AM WHERE AM.actionType_id IN (%s) AND AM.deleted=0 AND
AM.event_id = Event.id)'''%(','.join(forceString(leavedId) for leavedId in leavedIdList if leavedId)))
            if QtGui.qApp.defaultHospitalBedFinanceByMoving() in (0, 2):
                cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.code, NULL) AS codeFinance')
                cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.name, NULL) AS nameFinance')
                if finance:
                    cond.append(tableContract['deleted'].eq(0))
                    cond.append(tableRBFinance['id'].eq(finance))
                    queryTable = queryTable.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.innerJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
                else:
                    queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
            else:
                queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
            cols.append(getContractClientPolicyForDate())
            cond.append('(Contract.id IS NOT NULL AND Contract.deleted=0) OR (Contract.id IS NULL)')
            if feed == 1:
                cond.append('NOT %s'%(getEventFeedId(u'',db.formatDate(dateFeed))))
            elif feed == 2:
                cond.append('%s'%(getEventFeedId(u'',db.formatDate(dateFeed), alias=u'', refusalToEat = 0)))
            elif feed == 3:
                cond.append('%s'%(getEventFeedId(u'',db.formatDate(dateFeed), alias=u'', refusalToEat = 1)))
            if forceInt(codeAttachType) > 0:
                cond.append(tableRBAttachType['code'].eq(codeAttachType))
                queryTable = queryTable.innerJoin(tableClientAttach, tableClient['id'].eq(tableClientAttach['client_id']))
                queryTable = queryTable.innerJoin(tableRBAttachType, tableClientAttach['attachType_id'].eq(tableRBAttachType['id']))
            if indexSex > 0:
                cond.append(tableClient['sex'].eq(indexSex))
            if ageFor <= ageTo:
                cond.append(getAgeRangeCond(ageFor, ageTo))
            if deliverBy:
                cond.append(getDeliverByCond(deliverBy))
            if profile:
                cond.append(getHospitalBedProfile(profile))
            if insurerId or regionSMO:
                queryTable = queryTable.innerJoin(tableClientPolicy,
                                                  u'''(ClientPolicy.id = getClientPolicyIdForDate(Client.id, IF(Contract.id IS NOT NULL AND Contract.deleted=0, IF(rbFinance.code = 2, 1, IF(rbFinance.code = 3, 0, 1)), 1), IF(Event.execDate IS NOT NULL, Event.execDate, Event.setDate), Event.id))''')
                if not regionSMO:
                    cond.append(tableClientPolicy['insurer_id'].eq(insurerId))
                else:
                    tableOrganisation = db.table('Organisation').alias('Org_Area')
                    queryTable = queryTable.innerJoin(tableOrganisation, [tableOrganisation['id'].eq(tableClientPolicy['insurer_id']), tableOrganisation['deleted'].eq(0)])
                    if regionSMOCode:
                        if regionTypeSMO:
                            cond.append(tableOrganisation['area'].notlike(regionSMOCode))
                        else:
                            cond.append(tableOrganisation['area'].like(regionSMOCode))
            recordsReceived = db.getRecordList(queryTable, cols, cond)
            for record in recordsReceived:
                countEventFeedId = forceBool(record.value('countEventFeedId'))
                if (feed == 1 and not countEventFeedId) or (feed == 2 and countEventFeedId) or not feed or feed == 3:
                    statusObservation = forceString(record.value('statusObservation')).split('|')
                    statusObservationCode = forceString(statusObservation[0]) if len(statusObservation)>=1 else u''
                    statusObservationName = forceString(statusObservation[1]) if len(statusObservation)>=2 else u''
                    statusObservationColor = forceString(statusObservation[2]) if len(statusObservation)>=3 else u''
                    statusObservationDate = forceString(statusObservation[3]) if len(statusObservation)>=4 else u''
                    statusObservationPerson = forceString(statusObservation[4]) if len(statusObservation)>=5 else u''
                    nameContract = ' '.join([forceString(record.value(name)) for name in ('numberContract', 'dateContract', 'resolutionContract')])
                    begDate = forceDateTime(record.value('begDate'))
                    policyEndDate = forceDate(record.value('policyEndDate'))
                    colorFinance = None
                    if policyEndDate:
                        if forceDate(begDate) < policyEndDate <= forceDate(begDate).addDays(3):
                           colorFinance = QtGui.QColor(Qt.yellow)
                        elif forceDate(begDate) >= policyEndDate:
                            colorFinance = QtGui.QColor(Qt.red)
                    documentLocationInfo  = forceString(record.value('documentLocationInfo')).split("  ")
                    hospDocumentLocation  = forceString(documentLocationInfo[0]) if len(documentLocationInfo)>=1 else ''
                    documentLocationColor = forceString(documentLocationInfo[1]) if len(documentLocationInfo)>1 else ''
                    actionMKB = forceString(record.value('actionMKB'))
                    MKB = forceString(record.value('MKB'))
                    if actionMKB or MKB:
                        strMKB = (actionMKB if actionMKB else u'?') + u';' + (MKB if MKB else u'?')
                    else:
                        strMKB = u''
                    item = [statusObservationCode,
                            forceString(record.value('nameFinance')),
                            nameContract,
                            countEventFeedId,
                            forceRef(record.value('client_id')),
                            forceRef(record.value('eventId')),
                            forceString(record.value('externalId')),
                            forceString(record.value('lastName')) + u' ' + forceString(record.value('firstName')) + u' ' + forceString(record.value('patrName')),
                            self.sex[forceInt(record.value('sex'))],
                            forceDate(record.value('birthDate')),
                            forceDateTime(record.value('receivedBegDate')),
                            begDate,
                            forceDateTime(record.value('execDate')),
                            strMKB,
                            forceString(record.value('profileName')),
                            forceString(record.value('nameOrgStructure')),
                            forceString(record.value('namePerson')),
                            forceString(record.value('citizenship')),
                            forceString(record.value('placeCallValue')), 
                            hospDocumentLocation,
                            forceString(record.value('relegateOrg')),
                            forceString(record.value('codeFinance')),
                            '',
                            statusObservationName + u' (' + (statusObservationDate if statusObservationDate else u'') + u' ' + (statusObservationPerson if statusObservationPerson else u'') + u')',
                            statusObservationColor,
                            documentLocationColor,
                            colorFinance,
                            forceRef(record.value('id')), # actionId
                            forceString(calcAge(forceDate(record.value('birthDate')), forceDate(record.value('endDate'))))
                            ]
                    eventId = forceRef(record.value('eventId'))
                    self.feedTextValueItems[eventId] = forceString(record.value('clientDiet'))
                    self.items.append(item)
                    _dict = {
                        'observationCode': statusObservationCode,
                        'finance': forceString(record.value('nameFinance')),
                        'clientFeed': countEventFeedId,
                        'contract': nameContract,
                        'bedCode': '',
                        'financeCode': forceString(record.value('codeFinance')),
                        'bedName': '',
                        'observationName': statusObservationName,
                        'observationColor': statusObservationColor,
                        'orgStructure': forceString(record.value('nameOrgStructure')),
                        'person': forceString(record.value('namePerson')),
                        'setDate': CDateTimeInfo(forceDateTime(record.value('receivedBegDate'))),
                        'begDate': CDateTimeInfo(forceDateTime(record.value('begDate'))),
                        'endDate': CDateTimeInfo(forceDateTime(record.value('execDate'))),
                        'profile' : forceString(record.value('profileName'))
                    }
                    self.itemByName[eventId] = _dict


        def findReceivedWithoutSpecification(filterBegDate = None, filterEndDate = None, orgStructureIdList = [], dateFeed = None, quotingTypeList = None, accountingSystemId = None, filterClientId = None, filterEventId = None, defaultOrgStructureEventTypeIdList=[]):
            if not receivedActionIdList:
                self.items = []
                self.reset()
                return
            cols = [tableAction['id'],
                    tableEvent['id'].alias('eventId'),
                    tableEvent['client_id'],
                    tableEvent['externalId'],
                    tableClient['lastName'],
                    tableClient['firstName'],
                    tableClient['patrName'],
                    tableClient['sex'],
                    tableClient['birthDate'],
                    tableAction['begDate'],
                    tableAction['endDate'],
                    tableAction['MKB'].alias(u'actionMKB'),
                    tableEvent['setDate'],
                    tableEvent['execDate'],
                    tableContract['number'].alias('numberContract'),
                    tableContract['date'].alias('dateContract'),
                    tableContract['resolution'].alias('resolutionContract'),
                    getDataOrgStructureName(u'Направлен в отделение'),
                    tablePWS['name'].alias('namePerson'),
                    tableOrg['shortName'].alias('relegateOrg')
                    ]
            cols.append(getReceivedMKB())
            cols.append(getReceivedBegDate(self.receivedActionTypeIdList))
            cols.append(getOSHBP())
            cols.append(getHospDocumentLocationInfo())
            cols.append("""getClientCitizenshipTitle(Client.id, Action.begDate) as citizenship""")
            cols.append('%s as placeCallValue'%getStringPropertyValue(u'Место вызова'))
            if not dateFeed:
                dateFeed = QDate().currentDate().addDays(1)
            cols.append(getEventFeedId(u'', db.formatDate(dateFeed), u''' AS countEventFeedId'''))
            cols.append(getDietCode(u'0', db.formatDate(dateFeed), u''' AS clientDiet'''))
            cols.append(getStatusObservation())
            queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
            queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
            queryTable = queryTable.leftJoin(tablePWS, tablePWS['id'].eq(tableAction['person_id']))
            queryTable = queryTable.leftJoin(tableOrg, tableEvent['relegateOrg_id'].eq(tableOrg['id']))
            cond = [tableAction['actionType_id'].inlist(self.receivedActionTypeIdList),
                    tableAction['deleted'].eq(0),
                    tableEvent['deleted'].eq(0),
                    tableClient['deleted'].eq(0),
                   ]
            if contractId:
                cond.append(tableContract['id'].eq(contractId))
            if MKBFilter:
                cond.append(isMKB(MKBFrom, MKBTo))
            if order:
               cond.append(tableEvent['order'].eq(order))
            if eventTypeId:
               cond.append(tableEvent['eventType_id'].eq(eventTypeId))
            if placeCall and placeCall != u'не определено':
               cond.append(getStringProperty(u'Место вызова', u'''APS.value %s'''%(updateLIKE(placeCall))))
            if profile:
                cond.append(getPropertyAPHBP(profile, False))
            tableEventType = db.table('EventType')
            queryTable = queryTable.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))

            if QtGui.qApp.userHasAnyRight([urHBVisibleOwnEventsParentOrgStructureOnly, urHBVisibleOwnEventsOrgStructureOnly]):
                tableExecPerson = db.table('Person')
                queryTable = queryTable.leftJoin(tableExecPerson, tableExecPerson['id'].eq(tableEvent['execPerson_id']))
                uOrgStructureId = forceRef(db.translate('Person', 'id', QtGui.qApp.userId, 'orgStructure_id'))
                if QtGui.qApp.userHasRight(urHBVisibleOwnEventsParentOrgStructureOnly):
                    parentOrgStructure = getParentOrgStructureId(uOrgStructureId)
                    uOrgStructureList = getOrgStructureDescendants(parentOrgStructure if parentOrgStructure else uOrgStructureId)
                    cond.append(db.joinOr([tableExecPerson['orgStructure_id'].inlist(uOrgStructureList), tableEventType['ignoreVisibleRights'].eq(1)]))
                elif QtGui.qApp.userHasRight(urHBVisibleOwnEventsOrgStructureOnly):
                    uOrgStructureList = getOrgStructureDescendants(uOrgStructureId)
                    cond.append(db.joinOr([tableExecPerson['orgStructure_id'].inlist(uOrgStructureList), tableEventType['ignoreVisibleRights'].eq(1)]))

            cond.append(u"(EventType.medicalAidType_id IN (SELECT rbMedicalAidType.id from rbMedicalAidType where rbMedicalAidType.code IN ('1', '2', '3', '7')))")
            if defaultOrgStructureEventTypeIdList:
                cond.append(tableEvent['eventType_id'].inlist(defaultOrgStructureEventTypeIdList))
            if personId:
               cond.append(tableEvent['execPerson_id'].eq(personId))
            if relegateOrg:
                cond.append(tableEvent['relegateOrg_id'].eq(relegateOrg))
            if personExecId:
               cond.append(tableAction['person_id'].eq(personExecId))
            if self.statusObservation:
                cond.append(existsStatusObservation(self.statusObservation))
            if accountingSystemId and filterClientId:
                tableIdentification = db.table('ClientIdentification')
                queryTable = queryTable.innerJoin(tableIdentification, tableIdentification['client_id'].eq(tableClient['id']))
                cond.append(tableIdentification['accountingSystem_id'].eq(accountingSystemId))
                cond.append(tableIdentification['identifier'].eq(filterClientId))
                cond.append(tableIdentification['deleted'].eq(0))
            elif filterClientId:
                cond.append(tableClient['id'].eq(filterClientId))
            if filterEventId:
                cond.append(tableEvent['externalId'].eq(filterEventId))
            if not forceBool(filterBegDate.date()):
                filterBegDate = QDate().currentDate()
                cond.append(db.joinOr([tableAction['begDate'].isNull(), tableAction['begDate'].eq(filterBegDate)]))
            else:
                cond.append(tableAction['begDate'].isNotNull())
                cond.append(tableAction['begDate'].ge(filterBegDate))
            if forceBool(filterEndDate.date()):
                cond.append(tableAction['begDate'].isNotNull())
                cond.append(tableAction['begDate'].le(filterEndDate))
            if quotingTypeList:
                quotingTypeIdList, quotingTypeClass = quotingTypeList
                if quotingTypeClass is not None:
                    cond.append(getDataClientQuoting(u'Квота', quotingTypeIdList))
            if orgStructureIdList:
                cond.append(tableAPOS['value'].inlist(orgStructureIdList))
                queryTable = queryTable.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
                queryTable = queryTable.innerJoin(tableAP, tableAP['type_id'].eq(tableAPT['id']))
                queryTable = queryTable.innerJoin(tableAPOS, tableAPOS['id'].eq(tableAP['id']))
                queryTable = queryTable.innerJoin(tableOS, tableOS['id'].eq(tableAPOS['value']))
                cond.append(tableAPT['name'].like(u'Направлен в отделение'))
                cond.append(tableAP['deleted'].eq(0))
                cond.append(tableAPT['deleted'].eq(0))
                cond.append(tableAP['action_id'].eq(tableAction['id']))
                cond.append(tableOS['deleted'].eq(0))
            if QtGui.qApp.defaultHospitalBedFinanceByMoving() in (0, 2):
                cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.code, NULL) AS codeFinance')
                cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.name, NULL) AS nameFinance')
                if finance:
                    cond.append(tableContract['deleted'].eq(0))
                    cond.append(tableRBFinance['id'].eq(finance))
                    queryTable = queryTable.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.innerJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
                else:
                    queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
            else:
                queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
            cols.append(getContractClientPolicyForDate())
            cond.append('(Contract.id IS NOT NULL AND Contract.deleted=0) OR (Contract.id IS NULL)')
            if feed == 1:
                cond.append('NOT %s'%(getEventFeedId(u'',db.formatDate(dateFeed))))
            elif feed == 2:
                cond.append('%s'%(getEventFeedId(u'',db.formatDate(dateFeed), alias=u'', refusalToEat = 0)))
            elif feed == 3:
                cond.append('%s'%(getEventFeedId(u'',db.formatDate(dateFeed), alias=u'', refusalToEat = 1)))
            if forceInt(codeAttachType) > 0:
                cond.append(tableRBAttachType['code'].eq(codeAttachType))
                queryTable = queryTable.innerJoin(tableClientAttach, tableClient['id'].eq(tableClientAttach['client_id']))
                queryTable = queryTable.innerJoin(tableRBAttachType, tableClientAttach['attachType_id'].eq(tableRBAttachType['id']))
            if indexSex > 0:
                cond.append(tableClient['sex'].eq(indexSex))
            if ageFor <= ageTo:
                cond.append(getAgeRangeCond(ageFor, ageTo))
            if deliverBy:
                cond.append(getDeliverByCond(deliverBy))
            if profile:
                cond.append(getHospitalBedProfile(profile))
            if insurerId or regionSMO:
                queryTable = queryTable.innerJoin(tableClientPolicy,
                                                  u'''(ClientPolicy.id = getClientPolicyIdForDate(Client.id, IF(Contract.id IS NOT NULL AND Contract.deleted=0, IF(rbFinance.code = 2, 1, IF(rbFinance.code = 3, 0, 1)), 1), IF(Event.execDate IS NOT NULL, Event.execDate, Event.setDate), Event.id))''')
                if not regionSMO:
                    cond.append(tableClientPolicy['insurer_id'].eq(insurerId))
                else:
                    tableOrganisation = db.table('Organisation').alias('Org_Area')
                    queryTable = queryTable.innerJoin(tableOrganisation, [tableOrganisation['id'].eq(tableClientPolicy['insurer_id']), tableOrganisation['deleted'].eq(0)])
                    if regionSMOCode:
                        if regionTypeSMO:
                            cond.append(tableOrganisation['area'].notlike(regionSMOCode))
                        else:
                            cond.append(tableOrganisation['area'].like(regionSMOCode))
            recordsReceived = db.getRecordList(queryTable, cols, cond)
            for record in recordsReceived:
                countEventFeedId = forceBool(record.value('countEventFeedId'))
                if (feed == 1 and not countEventFeedId) or (feed == 2 and countEventFeedId) or not feed or feed == 3:
                    statusObservation = forceString(record.value('statusObservation')).split('|')
                    statusObservationCode = forceString(statusObservation[0]) if len(statusObservation)>=1 else u''
                    statusObservationName = forceString(statusObservation[1]) if len(statusObservation)>=2 else u''
                    statusObservationColor = forceString(statusObservation[2]) if len(statusObservation)>=3 else u''
                    statusObservationDate = forceString(statusObservation[3]) if len(statusObservation)>=4 else u''
                    statusObservationPerson = forceString(statusObservation[4]) if len(statusObservation)>=5 else u''
                    nameContract = ' '.join([forceString(record.value(name)) for name in ('numberContract', 'dateContract', 'resolutionContract')])
                    begDate = forceDateTime(record.value('begDate'))
                    policyEndDate = forceDate(record.value('policyEndDate'))
                    colorFinance = None
                    if policyEndDate:
                        if forceDate(begDate) < policyEndDate <= forceDate(begDate).addDays(3):
                           colorFinance = QtGui.QColor(Qt.yellow)
                        elif forceDate(begDate) >= policyEndDate:
                            colorFinance = QtGui.QColor(Qt.red)
                    documentLocationInfo  = forceString(record.value('documentLocationInfo')).split("  ")
                    hospDocumentLocation  = forceString(documentLocationInfo[0]) if len(documentLocationInfo)>=1 else ''
                    documentLocationColor = forceString(documentLocationInfo[1]) if len(documentLocationInfo)>1 else ''
                    actionMKB = forceString(record.value('actionMKB'))
                    MKB = forceString(record.value('MKB'))
                    if actionMKB or MKB:
                        strMKB = (actionMKB if actionMKB else u'?') + u';' + (MKB if MKB else u'?')
                    else:
                        strMKB = u''
                    item = [statusObservationCode,
                            forceString(record.value('nameFinance')),
                            nameContract,
                            countEventFeedId,
                            forceRef(record.value('client_id')),
                            forceRef(record.value('eventId')),
                            forceString(record.value('externalId')),
                            forceString(record.value('lastName')) + u' ' + forceString(record.value('firstName')) + u' ' + forceString(record.value('patrName')),
                            self.sex[forceInt(record.value('sex'))],
                            forceDate(record.value('birthDate')),
                            forceDateTime(record.value('receivedBegDate')),
                            begDate,
                            forceDateTime(record.value('execDate')),
                            strMKB,
                            forceString(record.value('profileName')),
                            forceString(record.value('nameOrgStructure')),
                            forceString(record.value('namePerson')),
                            forceString(record.value('citizenship')),
                            forceString(record.value('placeCallValue')), 
                            hospDocumentLocation,
                            forceString(record.value('relegateOrg')),
                            forceString(record.value('codeFinance')),
                            '',
                            statusObservationName + u' (' + (statusObservationDate if statusObservationDate else u'') + u' ' + (statusObservationPerson if statusObservationPerson else u'') + u')',
                            statusObservationColor,
                            documentLocationColor,
                            colorFinance,
                            forceRef(record.value('id')), # actionId
                            forceString(calcAge(forceDate(record.value('birthDate')), forceDate(record.value('endDate'))))
                            ]
                    eventId = forceRef(record.value('eventId'))
                    self.feedTextValueItems[eventId] = forceString(record.value('clientDiet'))
                    self.items.append(item)
                    _dict = {
                        'observationCode': statusObservationCode,
                        'finance': forceString(record.value('nameFinance')),
                        'clientFeed': countEventFeedId,
                        'contract': nameContract,
                        'bedCode': '',
                        'financeCode': forceString(record.value('codeFinance')),
                        'bedName': '',
                        'observationName': statusObservationName,
                        'observationColor': statusObservationColor,
                        'orgStructure': forceString(record.value('nameOrgStructure')),
                        'person': forceString(record.value('namePerson')),
                        'setDate': CDateTimeInfo(forceDateTime(record.value('receivedBegDate'))),
                        'begDate': CDateTimeInfo(forceDateTime(record.value('begDate'))),
                        'endDate': CDateTimeInfo(forceDateTime(record.value('execDate'))),
                        'profile' : forceString(record.value('profileName'))
                    }
                    self.itemByName[eventId] = _dict

        def findReceivedNoEnd(filterBegDate = None, filterEndDate = None, orgStructureIdList = [], dateFeed = None, orgStructureId = 0, quotingTypeList = None, accountingSystemId = None, filterClientId = None, filterEventId = None, defaultOrgStructureEventTypeIdList=[]):
            if not receivedActionIdList:
                self.items = []
                self.reset()
                return
            cols = [tableAction['id'],
                    tableEvent['id'].alias('eventId'),
                    tableEvent['client_id'],
                    tableEvent['externalId'],
                    tableClient['lastName'],
                    tableClient['firstName'],
                    tableClient['patrName'],
                    tableClient['sex'],
                    tableClient['birthDate'],
                    tableAction['begDate'],
                    tableAction['endDate'],
                    tableAction['MKB'].alias(u'actionMKB'),
                    tableEvent['setDate'],
                    tableContract['number'].alias('numberContract'),
                    tableContract['date'].alias('dateContract'),
                    tableContract['resolution'].alias('resolutionContract'),
                    tablePWS['name'].alias('namePerson'),
                    tableOrg['shortName'].alias('relegateOrg')
                    ]
            cols.append(getReceivedMKB())
            cols.append(getReceivedBegDate(self.receivedActionTypeIdList))
            cols.append(getOSHBP())
            cols.append(getHospDocumentLocationInfo())
            nameProperty = u'Направлен в отделение'
            cols.append(getDataOrgStructureName(nameProperty))
            if not dateFeed:
                dateFeed = QDate().currentDate().addDays(1)
            cols.append(getEventFeedId(u'', db.formatDate(dateFeed), u''' AS countEventFeedId'''))
            cols.append(getDietCode(u'0', db.formatDate(dateFeed), u''' AS clientDiet'''))
            cols.append(getStatusObservation())
            cols.append("""getClientCitizenshipTitle(Client.id, Action.begDate) as citizenship""")
            cols.append('%s as placeCallValue'%getStringPropertyValue(u'Место вызова'))
            queryTable = tableAction.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
            queryTable = queryTable.leftJoin(tablePWS, tablePWS['id'].eq(tableAction['person_id']))
            queryTable = queryTable.leftJoin(tableOrg, tableEvent['relegateOrg_id'].eq(tableOrg['id']))
            cond = [tableAction['actionType_id'].inlist(self.receivedActionTypeIdList),
                    tableAction['deleted'].eq(0),
                    tableEvent['deleted'].eq(0),
                    tableClient['deleted'].eq(0),
                   ]
            if contractId:
                cond.append(tableContract['id'].eq(contractId))
            if MKBFilter:
                cond.append(isMKB(MKBFrom, MKBTo))
            if order:
               cond.append(tableEvent['order'].eq(order))
            if eventTypeId:
               cond.append(tableEvent['eventType_id'].eq(eventTypeId))
            if placeCall and placeCall != u'не определено':
               cond.append(getStringProperty(u'Место вызова', u'''APS.value %s'''%(updateLIKE(placeCall))))
            tableEventType = db.table('EventType')
            queryTable = queryTable.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))

            if QtGui.qApp.userHasAnyRight([urHBVisibleOwnEventsParentOrgStructureOnly, urHBVisibleOwnEventsOrgStructureOnly]):
                tableExecPerson = db.table('Person')
                queryTable = queryTable.leftJoin(tableExecPerson, tableExecPerson['id'].eq(tableEvent['execPerson_id']))
                uOrgStructureId = forceRef(db.translate('Person', 'id', QtGui.qApp.userId, 'orgStructure_id'))
                if QtGui.qApp.userHasRight(urHBVisibleOwnEventsParentOrgStructureOnly):
                    parentOrgStructure = getParentOrgStructureId(uOrgStructureId)
                    uOrgStructureList = getOrgStructureDescendants(parentOrgStructure if parentOrgStructure else uOrgStructureId)
                    cond.append(db.joinOr([tableExecPerson['orgStructure_id'].inlist(uOrgStructureList), tableEventType['ignoreVisibleRights'].eq(1)]))
                elif QtGui.qApp.userHasRight(urHBVisibleOwnEventsOrgStructureOnly):
                    uOrgStructureList = getOrgStructureDescendants(uOrgStructureId)
                    cond.append(db.joinOr([tableExecPerson['orgStructure_id'].inlist(uOrgStructureList), tableEventType['ignoreVisibleRights'].eq(1)]))

            cond.append(u"(EventType.medicalAidType_id IN (SELECT rbMedicalAidType.id from rbMedicalAidType where rbMedicalAidType.code IN ('1', '2', '3', '7')))")
            if defaultOrgStructureEventTypeIdList:
                cond.append(tableEvent['eventType_id'].inlist(defaultOrgStructureEventTypeIdList))
            if personId:
               cond.append(tableEvent['execPerson_id'].eq(personId))
            if personExecId:
               cond.append(tableAction['person_id'].eq(personExecId))
            if profile:
                cond.append(getPropertyAPHBP(profile, False))
            if relegateOrg:
                cond.append(tableEvent['relegateOrg_id'].eq(relegateOrg))
            if self.statusObservation:
                cond.append(existsStatusObservation(self.statusObservation))
            if accountingSystemId and filterClientId:
                tableIdentification = db.table('ClientIdentification')
                queryTable = queryTable.innerJoin(tableIdentification, tableIdentification['client_id'].eq(tableClient['id']))
                cond.append(tableIdentification['accountingSystem_id'].eq(accountingSystemId))
                cond.append(tableIdentification['identifier'].eq(filterClientId))
                cond.append(tableIdentification['deleted'].eq(0))
            elif filterClientId:
                cond.append(tableClient['id'].eq(filterClientId))
            if filterEventId:
                cond.append(tableEvent['externalId'].eq(filterEventId))
            if not forceBool(filterBegDate.date()):
                filterBegDate = QDate().currentDate()
                cond.append(db.joinOr([tableAction['begDate'].isNull(), tableAction['begDate'].eq(filterBegDate)]))
            else:
                cond.append(tableAction['begDate'].isNotNull())
                cond.append(tableAction['begDate'].ge(filterBegDate))
            if forceBool(filterEndDate.date()):
                cond.append(tableAction['begDate'].isNotNull())
                cond.append(tableAction['begDate'].le(filterEndDate))
            if orgStructureIdList:
                cond.append(db.joinOr([getDataOrgStructure(nameProperty, orgStructureIdList, False), getDataOrgStructure(u'Приемное отделение', orgStructureIdList, False)]))
            if quotingTypeList:
                quotingTypeIdList, quotingTypeClass = quotingTypeList
                if quotingTypeClass is not None:
                    cond.append(getDataClientQuoting(u'Квота', quotingTypeIdList))
            if QtGui.qApp.defaultHospitalBedFinanceByMoving() in (0, 2):
                cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.code, NULL) AS codeFinance')
                cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.name, NULL) AS nameFinance')
                if finance:
                    cond.append(tableContract['deleted'].eq(0))
                    cond.append(tableRBFinance['id'].eq(finance))
                    queryTable = queryTable.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.innerJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
                else:
                    queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
            else:
                queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
            cols.append(getContractClientPolicyForDate())
            cond.append('(Contract.id IS NOT NULL AND Contract.deleted=0) OR (Contract.id IS NULL)')
            if feed == 1:
                cond.append('NOT %s'%(getEventFeedId(u'',db.formatDate(dateFeed))))
            elif feed == 2:
                cond.append('%s'%(getEventFeedId(u'',db.formatDate(dateFeed), alias=u'', refusalToEat = 0)))
            elif feed == 3:
                cond.append('%s'%(getEventFeedId(u'',db.formatDate(dateFeed), alias=u'', refusalToEat = 1)))
            if forceInt(codeAttachType) > 0:
                cond.append(tableRBAttachType['code'].eq(codeAttachType))
                queryTable = queryTable.innerJoin(tableClientAttach, tableClient['id'].eq(tableClientAttach['client_id']))
                queryTable = queryTable.innerJoin(tableRBAttachType, tableClientAttach['attachType_id'].eq(tableRBAttachType['id']))
            if indexSex > 0:
                cond.append(tableClient['sex'].eq(indexSex))
            if ageFor <= ageTo:
                cond.append(getAgeRangeCond(ageFor, ageTo))
            if deliverBy:
                cond.append(getDeliverByCond(deliverBy))
            if profile:
                cond.append(getHospitalBedProfile(profile))
            if insurerId or regionSMO:
                queryTable = queryTable.innerJoin(tableClientPolicy,
                                                  u'''(ClientPolicy.id = getClientPolicyIdForDate(Client.id, IF(Contract.id IS NOT NULL AND Contract.deleted=0, IF(rbFinance.code = 2, 1, IF(rbFinance.code = 3, 0, 1)), 1), IF(Event.execDate IS NOT NULL, Event.execDate, Event.setDate), Event.id))''')
                if not regionSMO:
                    cond.append(tableClientPolicy['insurer_id'].eq(insurerId))
                else:
                    tableOrganisation = db.table('Organisation').alias('Org_Area')
                    queryTable = queryTable.innerJoin(tableOrganisation, [tableOrganisation['id'].eq(tableClientPolicy['insurer_id']), tableOrganisation['deleted'].eq(0)])
                    if regionSMOCode:
                        if regionTypeSMO:
                            cond.append(tableOrganisation['area'].notlike(regionSMOCode))
                        else:
                            cond.append(tableOrganisation['area'].like(regionSMOCode))
            recordsReceived = db.getRecordList(queryTable, cols, cond)
            for record in recordsReceived:
                countEventFeedId = forceBool(record.value('countEventFeedId'))
                if (feed == 1 and not countEventFeedId) or (feed == 2 and countEventFeedId) or not feed or feed == 3:
                    statusObservation = forceString(record.value('statusObservation')).split('|')
                    statusObservationCode = forceString(statusObservation[0]) if len(statusObservation)>=1 else u''
                    statusObservationName = forceString(statusObservation[1]) if len(statusObservation)>=2 else u''
                    statusObservationColor = forceString(statusObservation[2]) if len(statusObservation)>=3 else u''
                    statusObservationDate = forceString(statusObservation[3]) if len(statusObservation)>=4 else u''
                    statusObservationPerson = forceString(statusObservation[4]) if len(statusObservation)>=5 else u''
                    nameContract = ' '.join([forceString(record.value(name)) for name in ('numberContract', 'dateContract', 'resolutionContract')])
                    begDate = forceDateTime(record.value('begDate'))
                    policyEndDate = forceDate(record.value('policyEndDate'))
                    colorFinance = None
                    if policyEndDate:
                        if forceDate(begDate) < policyEndDate <= forceDate(begDate).addDays(3):
                           colorFinance = QtGui.QColor(Qt.yellow)
                        elif forceDate(begDate) >= policyEndDate:
                            colorFinance = QtGui.QColor(Qt.red)
                    documentLocationInfo  = forceString(record.value('documentLocationInfo')).split("  ")
                    hospDocumentLocation  = forceString(documentLocationInfo[0]) if len(documentLocationInfo)>=1 else ''
                    documentLocationColor = forceString(documentLocationInfo[1]) if len(documentLocationInfo)>1 else ''
                    actionMKB = forceString(record.value('actionMKB'))
                    MKB = forceString(record.value('MKB'))
                    if actionMKB or MKB:
                        strMKB = (actionMKB if actionMKB else u'?') + u';' + (MKB if MKB else u'?')
                    else:
                        strMKB = u''
                    item = [statusObservationCode,
                            forceString(record.value('nameFinance')),
                            nameContract,
                            countEventFeedId,
                            forceRef(record.value('client_id')),
                            forceRef(record.value('eventId')),
                            forceString(record.value('externalId')),
                            forceString(record.value('lastName')) + u' ' + forceString(record.value('firstName')) + u' ' + forceString(record.value('patrName')),
                            self.sex[forceInt(record.value('sex'))],
                            forceDate(record.value('birthDate')),
                            forceDateTime(record.value('receivedBegDate')),
                            begDate,
                            forceDateTime(record.value('endDate')),
                            strMKB,
                            forceString(record.value('profileName')),
                            forceString(record.value('nameOrgStructure')),
                            forceString(record.value('namePerson')),
                            forceString(record.value('citizenship')),
                            forceString(record.value('placeCallValue')), 
                            hospDocumentLocation,
                            forceString(record.value('relegateOrg')),
                            forceString(record.value('codeFinance')),
                            '',
                            statusObservationName + u' (' + (statusObservationDate if statusObservationDate else u'') + u' ' + (statusObservationPerson if statusObservationPerson else u'') + u')',
                            statusObservationColor,
                            documentLocationColor,
                            colorFinance,
                            forceRef(record.value('id')), # actionId
                            forceString(calcAge(forceDate(record.value('birthDate')), forceDate(record.value('endDate'))))
                            ]
                    eventId = forceRef(record.value('eventId'))
                    self.feedTextValueItems[eventId] = forceString(record.value('clientDiet'))
                    self.items.append(item)
                    _dict = {
                            'observationCode': statusObservationCode,
                            'finance': forceString(record.value('nameFinance')),
                            'clientFeed': countEventFeedId,
                            'contract': nameContract,
                            'bedCode': '',
                            'orgStructure': forceString(record.value('nameOrgStructure')),
                            'financeCode': forceString(record.value('codeFinance')),
                            'bedName': '',
                            'observationName': statusObservationName,
                            'observationColor': statusObservationColor,
                            'setDate': CDateTimeInfo(forceDateTime(record.value('receivedBegDate'))),
                            'begDate': CDateTimeInfo(forceDateTime(record.value('begDate'))),
                            'endDate': CDateTimeInfo(forceDateTime(record.value('endDate'))),
                            'profile' : forceString(record.value('profileName'))
                        }
                    self.itemByName[eventId] = _dict
        if index == 1:
            movingActionIdList = getActionIdList(dialogParams, self.movingActionTypeIdList)
        else:
            receivedActionIdList = getActionIdList(dialogParams, self.receivedActionTypeIdList)
        if index == 0:
            self.items = []
            findReceived(filterBegDate, filterEndDate, orgStructureIdList, dateFeed, (quotingTypeList, quotingTypeClass), accountingSystemId, filterClientId, filterEventId, defaultOrgStructureEventTypeIdList)
        elif index == 1:
            self.items = []
            findMovingAfterReceived(filterBegDate, filterEndDate, indexLocalClient, dateFeed, orgStructureIdList, (quotingTypeList, quotingTypeClass), accountingSystemId, filterClientId, filterEventId, defaultOrgStructureEventTypeIdList)
        elif index == 2:
            self.items = []
            findReceivedNoEnd(filterBegDate, filterEndDate, orgStructureIdList, dateFeed, orgStructureId, (quotingTypeList, quotingTypeClass), accountingSystemId, filterClientId, filterEventId, defaultOrgStructureEventTypeIdList)
        elif index == 3:
            self.items = []
            findReceived(filterBegDate, filterEndDate, orgStructureIdList, dateFeed, (quotingTypeList, quotingTypeClass), accountingSystemId, filterClientId, filterEventId, defaultOrgStructureEventTypeIdList, True)
        elif index == 4:
            self.items = []
            findReceived(filterBegDate, filterEndDate, orgStructureIdList, dateFeed, (quotingTypeList, quotingTypeClass), accountingSystemId, filterClientId, filterEventId, defaultOrgStructureEventTypeIdList, True, True)
        elif index == 5:
            self.items = []
            findReceivedWithoutSpecification(filterBegDate, filterEndDate, orgStructureIdList, dateFeed, (quotingTypeList, quotingTypeClass), accountingSystemId, filterClientId, filterEventId, defaultOrgStructureEventTypeIdList)
        for col, order in self.headerSortingCol.items():
            self.sort(col, order)

    def sort(self, col, order=Qt.AscendingOrder):
        self.headerSortingCol = {col: order}
        reverse = order == Qt.DescendingOrder
        if col in [self.clientColumn, self.eventColumn]:
            self.items.sort(key=lambda x: forceInt(x[col]) if x else None, reverse=reverse)
        elif col in [self.birthDateCol, self.receivedDateCol, self.leavedDateCol]:
            self.items.sort(key=lambda x: forceDateTime(x[col]) if x else None, reverse=reverse)
        else:
            self.items.sort(key=lambda x: forceString(x[col]).lower() if x else None, reverse=reverse)
        self.reset()


class CTransferModel(CMonitoringModel):
    column = [u'С', u'И', u'Д', u'П', u'Номер', u'Код', u'Карта', u'ФИО', u'Пол', u'Дата рождения', u'Госпитализирован', u'Поступил', u'Выбыл', u'MKB', u'Профиль', u'Подразделение', u'Переведен из', u'Лечащий врач', u'Гражданство', u'М']
    statusObservationCol = 0
    financeCol = 1
    feedCol = 3
    clientColumn = 4
    eventColumn = 5
    defaultOrderCol = 7
    birthDateCol = 9
    hospDateCol = 10
    receivedDateCol = 11
    leavedDateCol = 12
    MKBColumn = 13
    profileCol = 14
    documentLocationCol = 19
    codeFinanceCol = 20
    bedNameCol = 21
    statusObservationNameCol = 22
    colorStatusObservationCol = 23
    docLocalColorCol = 24
    colorFinanceCol = 25
    ageCol = 26

    def __init__(self, parent):
        CMonitoringModel.__init__(self, parent)
        self.items = []
        self._cols = []
        self.transfer = 0
        self.itemByName = {}
        self.feedTextValueItems = {}
        self.statusObservation = None

    def cols(self):
        self._cols = [CCol(u'Статус наблюдения',     ['statusObservation'], 20, 'l'),
                      CCol(u'Код ИФ',                ['nameFinance'], 20, 'l'),
                      CCol(u'Договор',               ['contract'], 20, 'l'),
                      CCol(u'Питание',               ['feed'], 20, 'l'),
                      CCol(u'Номер',                 ['client_id'], 20, 'l'),
                      CCol(u'Код события',           ['event_id'], 20, 'l'),
                      CCol(u'Карта',                 ['externalId'], 20, 'l'),
                      CCol(u'ФИО',                   ['lastName', 'firstName', 'patrName'], 30, 'l'),
                      CCol(u'Пол',                   ['sex'], 15, 'l'),
                      CCol(u'Дата рождения',         ['birthDate'], 20, 'l'),
                      CCol(u'Госпитализирован',      ['begDateReceived'], 20, 'l'),
                      CCol(u'Поступил',              ['begDate'], 20, 'l'),
                      CCol(u'Выбыл',                 ['endDate'], 20, 'l'),
                      CCol(u'MKB',                   ['MKB'], 20, 'l'),
                      CCol(u'Профиль',               ['profileName'], 30, 'l'),
                      CCol(u'Подразделение',         ['nameOS'], 30, 'l'),
                      CCol(u'Переведен в',           ['transferOS'], 30, 'l') if self.transfer else CCol(u'Переведен из', ['nameOS'], 30, 'l'),
                      CCol(u'Лечащий врач',          ['namePerson'], 30, 'l'),
                      CCol(u'Гражданство',           ['citizenship'], 30, 'l'),
                      CCol(u'Место нахождения учетного документа',['hospDocumentLocation'], 30, 'l')
                      ]
        return self._cols

    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return QVariant(self.column[section])
            elif role == Qt.ToolTipRole:
                if section == 0:
                    return QVariant(u'Статус наблюдения пациента')
                elif section == 1:
                    return QVariant(u'Источник финансирования (код)')
                elif section == 2:
                    return QVariant(u'Договор')
                elif section == 3:
                    return QVariant(u'Питание')
                elif section == 18:
                    return QVariant(u'Место нахождения учетного документа')
                elif section == self.eventColumn:
                    return QVariant(u'Код события')
        return QVariant()

    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if role == Qt.BackgroundColorRole:
            if column == self.statusObservationCol and self.items[row][column]:
                return toVariant(QtGui.QColor(self.items[row][self.colorStatusObservationCol]))
            elif len(forceString(self.items[row][self.MKBColumn])) <= 0:
               return toVariant(QtGui.QColor(200, 230, 240))
            elif column == self.financeCol:
                colorFinance = self.items[row][self.colorFinanceCol]
                if colorFinance:
                    return toVariant(colorFinance)
            elif column == self.documentLocationCol:
                docLocalColor = self.items[row][self.docLocalColorCol]
                if docLocalColor:
                    return toVariant(QtGui.QColor(docLocalColor))
        if role == Qt.DisplayRole:
            if column in [self.hospDateCol, self.receivedDateCol, self.leavedDateCol]:
                item = self.items[row]
                return toVariant(item[column].toString('dd.MM.yyyy hh:mm'))
            elif column == self.birthDateCol:
                item = self.items[row]
                return toVariant(forceString(item[column]) + u' (' + item[self.ageCol] + u')')
            elif column == self.feedCol:
                return toVariant(self.feedTextValueItems[self.getEventId(row)])
            else:
                item = self.items[row]
                return toVariant(item[column])
        elif role == Qt.CheckStateRole:
            if column == self.feedCol:
                item = self.items[row]
                return toVariant(Qt.Checked if item[column] else Qt.Unchecked)
        elif role == Qt.ToolTipRole:
            if column == self.statusObservationCol:
                item = self.items[row]
                if item[self.statusObservationCol]:
                    return QVariant(item[self.statusObservationCol] + u' ' + item[self.statusObservationNameCol])
                else:
                    return QVariant()
            elif column == self.financeCol:
                item = self.items[row]
                return QVariant(item[self.codeFinanceCol] + u' ' + item[column])
            elif column == self.profileCol:
                item = self.items[row]
                return QVariant(forceString(item[column]) + u' ' + item[self.bedNameCol])
        return QVariant()

    def loadData(self, dialogParams):
        self.items = []
        self.itemByName = {}
        self.feedTextValueItems = {}
        orgStructureIdList = []
        filterBegDate = dialogParams.get('filterBegDate', None)
        filterEndDate = dialogParams.get('filterEndDate', None)
        filterBegTime = dialogParams.get('filterBegTime', None)
        filterEndTime = dialogParams.get('filterEndTime', None)
        if not filterBegTime.isNull():
            begDateTime = QDateTime(filterBegDate, filterBegTime)
            filterBegDate = begDateTime
        if not filterEndTime.isNull():
            endDateTime = QDateTime(filterEndDate, filterEndTime)
            filterEndDate = endDateTime
        indexSex = dialogParams.get('indexSex', 0)
        ageFor = dialogParams.get('ageFor', 0)
        ageTo = dialogParams.get('ageTo', 150)
        order = dialogParams.get('order', -1)
        eventTypeId = dialogParams.get('eventTypeId', None)
        orgStructureId = dialogParams.get('orgStructureId', None)
        permanent = dialogParams.get('permanent', None)
        _type = dialogParams.get('type', None)
        profile = dialogParams.get('treatmentProfile', None)
        codeAttachType = dialogParams.get('codeAttachType', None)
        indexLocalClient = dialogParams.get('indexLocalClient', None)
        finance = dialogParams.get('finance', None)
        contractId = dialogParams.get('contractId', None)
        feed = dialogParams.get('feed', None)
        dateFeed = dialogParams.get('dateFeed', None)
        personId = dialogParams.get('personId', None)
        insurerId = dialogParams.get('insurerId', None)
        regionSMO, regionTypeSMO, regionSMOCode = dialogParams.get('regionSMO', (False, 0, None))
        personExecId = dialogParams.get('personExecId', None)
        accountingSystemId = dialogParams.get('accountingSystemId', None)
        filterClientId = dialogParams.get('filterClientId', None)
        filterEventId = dialogParams.get('filterEventId', None)
        statusObservation = dialogParams.get('statusObservation', None)
        self.transfer = dialogParams.get('transfer', 0)
        stayOrgStructure = dialogParams.get('stayOrgStructure', 1)
        MKBFilter = dialogParams['MKBFilter']
        MKBFrom   = dialogParams['MKBFrom']
        MKBTo     = dialogParams['MKBTo']
        scheduleId = dialogParams.get('scheduleId', None)
        self.statusObservation = statusObservation
        if orgStructureId:
            treeItem = orgStructureId.internalPointer() if orgStructureId.isValid() else None
            orgStructureIdList = self.getOrgStructureIdList(orgStructureId) if treeItem and treeItem._id else []
        db = QtGui.qApp.db
        tableAPT = db.table('ActionPropertyType')
        tableAP = db.table('ActionProperty')
        tableActionType = db.table('ActionType')
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        tableClient = db.table('Client')
        tableClientPolicy = db.table('ClientPolicy')
        tableOS = db.table('OrgStructure')
        tablePWS = db.table('vrbPersonWithSpeciality')
        tableAPOS = db.table('ActionProperty_OrgStructure')
        tableClientAttach = db.table('ClientAttach')
        tableRBAttachType = db.table('rbAttachType')
        tableContract = db.table('Contract')
        tableRBFinance = db.table('rbFinance')
        tableRBFinanceBC = db.table('rbFinance').alias('rbFinanceByContract')
        tableEvent_Feed = db.table('Event_Feed')
        tableStatusObservation= db.table('Client_StatusObservation')
        nameReceivedOS = u'Отделение пребывания'
        if self.transfer:
            nameTransferOS = u'Переведен в отделение'
            self.column[16] = u'Переведен в'
        else:
            nameTransferOS = u'Переведен из отделения'
            self.column[16] = u'Переведен из'

        def getActionIdList(dialogParams, actionTypeIdListByFlatCode):
            filterBegDate = dialogParams.get('filterBegDate', None)
            filterEndDate = dialogParams.get('filterEndDate', None)
            filterBegTime = dialogParams.get('filterBegTime', None)
            filterEndTime = dialogParams.get('filterEndTime', None)
            if not filterBegTime.isNull():
                begDateTime = QDateTime(filterBegDate, filterBegTime)
                filterBegDate = begDateTime
            if not filterEndTime.isNull():
                endDateTime = QDateTime(filterEndDate, filterEndTime)
                filterEndDate = endDateTime
            db = QtGui.qApp.db
            tableAction = db.table('Action')
            cond = [ tableAction['actionType_id'].inlist(actionTypeIdListByFlatCode),
                     tableAction['deleted'].eq(0),
                   ]
            if not forceBool(filterBegDate.date()):
                filterBegDate = QDate.currentDate()
                cond.append(db.joinOr([tableAction['begDate'].isNull(), tableAction['begDate'].eq(filterBegDate)]))
            else:
                cond.append(tableAction['begDate'].isNotNull())
                cond.append(tableAction['begDate'].ge(filterBegDate))
            if forceBool(filterEndDate.date()):
                cond.append(tableAction['begDate'].isNotNull())
                cond.append(tableAction['begDate'].le(filterEndDate))
            return db.getDistinctIdList(tableAction, [tableAction['id']], cond)

        def getTransfer(orgStructureIdList, filterBegDate = None, filterEndDate = None, indexSex = 0, ageFor = 0, ageTo = 150, permanent = None, type = None, profile = None, codeAttachType = None, finance = None, localClient = 0, feed = None, dateFeed = None, quotingTypeList = None, accountingSystemId = None, filterClientId = None, filterEventId = None):
            if not movingActionIdList:
                return []
            cols = [tableAction['id'],
                tableEvent['id'].alias('eventId'),
                tableEvent['client_id'],
                tableEvent['externalId'],
                tableClient['lastName'],
                tableClient['firstName'],
                tableClient['patrName'],
                tableClient['sex'],
                tableClient['birthDate'],
                tableAction['begDate'],
                tableAction['endDate'],
                tableEvent['setDate'],
                tableOS['name'].alias('nameFromOS'),
                tableContract['number'].alias('numberContract'),
                tableContract['date'].alias('dateContract'),
                tableContract['resolution'].alias('resolutionContract'),
                tablePWS['name'].alias('namePerson')
                ]
            cols.append(getMKB())
            cols.append(getHospDocumentLocationInfo())
            cols.append(getReceivedBegDate(self.receivedActionTypeIdList))
            if not dateFeed:
                dateFeed = QDate().currentDate().addDays(1)
            cols.append(getEventFeedId(u'', tableEvent_Feed['date'].formatValue(dateFeed), u''' AS countEventFeedId'''))
            cols.append(getDietCode(u'0', db.formatDate(dateFeed), u''' AS clientDiet'''))
            cols.append(getDataOrgStructureName(nameReceivedOS))
            cols.append(getHBProfileFromBed())
            cols.append(getStatusObservation())
            cols.append("""getClientCitizenshipTitle(Client.id, Action.begDate) as citizenship""")
            queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
            queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
            queryTable = queryTable.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
            queryTable = queryTable.innerJoin(tableAP, tableAP['type_id'].eq(tableAPT['id']))
            queryTable = queryTable.innerJoin(tableAPOS, tableAPOS['id'].eq(tableAP['id']))
            queryTable = queryTable.innerJoin(tableOS, tableOS['id'].eq(tableAPOS['value']))
            queryTable = queryTable.leftJoin(tablePWS, tablePWS['id'].eq(tableAction['person_id']))
            cond = [tableAction['actionType_id'].inlist(self.movingActionTypeIdList),
                    tableAction['deleted'].eq(0),
                    tableEvent['deleted'].eq(0),
                    tableAP['deleted'].eq(0),
                    tableAPT['deleted'].eq(0),
                    tableClient['deleted'].eq(0),
                    tableAP['action_id'].eq(tableAction['id']),
                    tableOS['deleted'].eq(0)
                   ]
            if scheduleId:
                cond.append(isScheduleBeds(scheduleId))
            if contractId:
                cond.append(tableContract['id'].eq(contractId))
            if MKBFilter:
                cond.append(isMKB(MKBFrom, MKBTo))
            if order:
               cond.append(tableEvent['order'].eq(order))
            if eventTypeId:
               cond.append(tableEvent['eventType_id'].eq(eventTypeId))
            tableEventType = db.table('EventType')
            queryTable = queryTable.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))

            if QtGui.qApp.userHasAnyRight([urHBVisibleOwnEventsParentOrgStructureOnly, urHBVisibleOwnEventsOrgStructureOnly]):
                tableExecPerson = db.table('Person')
                queryTable = queryTable.leftJoin(tableExecPerson, tableExecPerson['id'].eq(tableEvent['execPerson_id']))
                uOrgStructureId = forceRef(db.translate('Person', 'id', QtGui.qApp.userId, 'orgStructure_id'))
                if QtGui.qApp.userHasRight(urHBVisibleOwnEventsParentOrgStructureOnly):
                    parentOrgStructure = getParentOrgStructureId(uOrgStructureId)
                    uOrgStructureList = getOrgStructureDescendants(parentOrgStructure if parentOrgStructure else uOrgStructureId)
                    cond.append(db.joinOr([tableExecPerson['orgStructure_id'].inlist(uOrgStructureList), tableEventType['ignoreVisibleRights'].eq(1)]))
                elif QtGui.qApp.userHasRight(urHBVisibleOwnEventsOrgStructureOnly):
                    uOrgStructureList = getOrgStructureDescendants(uOrgStructureId)
                    cond.append(db.joinOr([tableExecPerson['orgStructure_id'].inlist(uOrgStructureList), tableEventType['ignoreVisibleRights'].eq(1)]))

            cond.append(u"(EventType.medicalAidType_id IN (SELECT rbMedicalAidType.id from rbMedicalAidType where rbMedicalAidType.code IN ('1', '2', '3', '7')))")
            cond.append(tableAPT['name'].like(nameTransferOS))
            if personId:
               cond.append(tableEvent['execPerson_id'].eq(personId))
            if personExecId:
               cond.append(tableAction['person_id'].eq(personExecId))
            if self.statusObservation:
                cond.append(existsStatusObservation(self.statusObservation))
            if accountingSystemId and filterClientId:
                tableIdentification = db.table('ClientIdentification')
                queryTable = queryTable.innerJoin(tableIdentification, tableIdentification['client_id'].eq(tableClient['id']))
                cond.append(tableIdentification['accountingSystem_id'].eq(accountingSystemId))
                cond.append(tableIdentification['identifier'].eq(filterClientId))
                cond.append(tableIdentification['deleted'].eq(0))
            elif filterClientId:
                cond.append(tableClient['id'].eq(filterClientId))
            if filterEventId:
                cond.append(tableEvent['externalId'].eq(filterEventId))
            if not forceBool(filterBegDate.date()):
                filterBegDate = QDate().currentDate()
                cond.append(db.joinOr([tableAction['begDate'].isNull(), tableAction['begDate'].eq(filterBegDate)]))
            else:
                cond.append(tableAction['begDate'].isNotNull())
                cond.append(tableAction['begDate'].ge(filterBegDate))
            if forceBool(filterEndDate.date()):
                cond.append(tableAction['begDate'].isNotNull())
                cond.append(tableAction['begDate'].le(filterEndDate))
            cond.append('(Contract.id IS NOT NULL AND Contract.deleted=0) OR (Contract.id IS NULL)')
            if feed == 1:
                cond.append('NOT %s'%(getEventFeedId(u'',tableEvent_Feed['date'].formatValue(dateFeed))))
            elif feed == 2:
                cond.append('%s'%(getEventFeedId(u'',tableEvent_Feed['date'].formatValue(dateFeed), alias=u'', refusalToEat = 0)))
            elif feed == 3:
                cond.append('%s'%(getEventFeedId(u'',tableEvent_Feed['date'].formatValue(dateFeed), alias=u'', refusalToEat = 1)))
            if QtGui.qApp.defaultHospitalBedFinanceByMoving() == 2:
                cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.code, IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinanceByContract.code, NULL)) AS codeFinance')
                cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.name, IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinanceByContract.name, NULL)) AS nameFinance')
                cols.append(getContractClientPolicyForDate())
                if finance:
                    cond.append('''((Action.finance_id IS NOT NULL AND Action.deleted=0 AND Action.finance_id = %s) OR (Contract.id IS NOT NULL AND Contract.deleted=0 AND Contract.finance_id = %s))'''%(str(finance), str(finance)))
                    queryTable = queryTable.innerJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
                    queryTable = queryTable.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.innerJoin(tableRBFinanceBC, tableRBFinanceBC['id'].eq(tableContract['finance_id']))
                else:
                    queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
                    queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.leftJoin(tableRBFinanceBC, tableRBFinanceBC['id'].eq(tableContract['finance_id']))
            elif QtGui.qApp.defaultHospitalBedFinanceByMoving() == 1:
                cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.code, NULL) AS codeFinance')
                cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.name, NULL) AS nameFinance')
                cols.append(getActionClientPolicyForDate())
                queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                if finance:
                    cond.append('''(Action.finance_id IS NOT NULL AND Action.deleted=0 AND Action.finance_id = %s)'''%(str(finance)))
                    queryTable = queryTable.innerJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
                else:
                    queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
            else:
                cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.code, NULL) AS codeFinance')
                cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.name, NULL) AS nameFinance')
                cols.append(getContractClientPolicyForDate())
                if finance:
                    cond.append(tableContract['deleted'].eq(0))
                    cond.append(tableRBFinance['id'].eq(finance))
                    queryTable = queryTable.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.innerJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
                else:
                    queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
            if forceInt(codeAttachType) > 0:
                cond.append(tableRBAttachType['code'].eq(codeAttachType))
                queryTable = queryTable.innerJoin(tableClientAttach, tableClient['id'].eq(tableClientAttach['client_id']))
                queryTable = queryTable.innerJoin(tableRBAttachType, tableClientAttach['attachType_id'].eq(tableRBAttachType['id']))
            if indexSex > 0:
                cond.append(tableClient['sex'].eq(indexSex))
            if ageFor <= ageTo:
                cond.append(getAgeRangeCond(ageFor, ageTo))
            if orgStructureIdList:
                if stayOrgStructure:
                    cond.append(getDataOrgStructure(nameReceivedOS, orgStructureIdList, False))
                else:
                    cond.append(getDataOrgStructure(nameTransferOS, orgStructureIdList, False))
            if quotingTypeList:
                quotingTypeIdList, quotingTypeClass = quotingTypeList
                if quotingTypeClass is not None:
                    cond.append(getDataClientQuoting(u'Квота', quotingTypeIdList))
            if profile:
                cond.append(getHospitalBedProfileFromBed(profile))
            if insurerId or regionSMO:
                queryTable = queryTable.innerJoin(tableClientPolicy,
                                                  u'''(ClientPolicy.id = getClientPolicyIdForDate(Client.id, IF(Contract.id IS NOT NULL AND Contract.deleted=0, IF(rbFinance.code = 2, 1, IF(rbFinance.code = 3, 0, 1)), 1), IF(Event.execDate IS NOT NULL, Event.execDate, Event.setDate), Event.id))''')
                if not regionSMO:
                    cond.append(tableClientPolicy['insurer_id'].eq(insurerId))
                else:
                    tableOrganisation = db.table('Organisation').alias('Org_Area')
                    queryTable = queryTable.innerJoin(tableOrganisation, [tableOrganisation['id'].eq(tableClientPolicy['insurer_id']), tableOrganisation['deleted'].eq(0)])
                    if regionSMOCode:
                        if regionTypeSMO:
                            cond.append(tableOrganisation['area'].notlike(regionSMOCode))
                        else:
                            cond.append(tableOrganisation['area'].like(regionSMOCode))
            return db.getRecordList(queryTable, cols, cond)

        movingActionIdList = getActionIdList(dialogParams, self.movingActionTypeIdList)
        recordsMoving = getTransfer(orgStructureIdList, filterBegDate, filterEndDate, indexSex, ageFor, ageTo, permanent, type, profile, codeAttachType, finance, indexLocalClient, feed, dateFeed, None, accountingSystemId, filterClientId, filterEventId)
        for record in recordsMoving:
            countEventFeedId = forceBool(record.value('countEventFeedId'))
            if (feed == 1 and not countEventFeedId) or (feed == 2 and countEventFeedId) or not feed or feed == 3:
                statusObservation = forceString(record.value('statusObservation')).split('|')
                statusObservationCode = forceString(statusObservation[0]) if len(statusObservation)>=1 else u''
                statusObservationName = forceString(statusObservation[1]) if len(statusObservation)>=2 else u''
                statusObservationColor = forceString(statusObservation[2]) if len(statusObservation)>=3 else u''
                statusObservationDate = forceString(statusObservation[3]) if len(statusObservation)>=4 else u''
                statusObservationPerson = forceString(statusObservation[4]) if len(statusObservation)>=5 else u''
                nameContract = ' '.join([forceString(record.value(name)) for name in ('numberContract', 'dateContract', 'resolutionContract')])
                begDate = forceDate(record.value('begDate'))
                policyEndDate = forceDate(record.value('policyEndDate'))
                colorFinance = None
                if policyEndDate:
                    if begDate < policyEndDate <= begDate.addDays(3):
                       colorFinance = QtGui.QColor(Qt.yellow)
                    elif begDate >= policyEndDate:
                        colorFinance = QtGui.QColor(Qt.red)
                documentLocationInfo  = forceString(record.value('documentLocationInfo')).split("  ")
                hospDocumentLocation  = forceString(documentLocationInfo[0]) if len(documentLocationInfo)>=1 else ''
                documentLocationColor = forceString(documentLocationInfo[1]) if len(documentLocationInfo)>1 else ''
                item = [statusObservationCode,
                        forceString(record.value('nameFinance')),
                        nameContract,
                        countEventFeedId,
                        forceRef(record.value('client_id')),
                        forceRef(record.value('eventId')),
                        forceString(record.value('externalId')),
                        forceString(record.value('lastName')) + u' ' + forceString(record.value('firstName')) + u' ' + forceString(record.value('patrName')),
                        self.sex[forceInt(record.value('sex'))],
                        forceDate(record.value('birthDate')),
                        forceDateTime(record.value('receivedBegDate')),
                        forceDateTime(record.value('begDate')),
                        forceDateTime(record.value('endDate')),
                        forceString(record.value('MKB')),
                        forceString(record.value('profileName')),
                        forceString(record.value('nameOrgStructure')),
                        forceString(record.value('nameFromOS')),
                        forceString(record.value('namePerson')),
                        forceString(record.value('citizenship')),
                        hospDocumentLocation,
                        forceString(record.value('codeFinance')),
                        '',
                        statusObservationName + u' (' + (statusObservationDate if statusObservationDate else u'') + u' ' + (statusObservationPerson if statusObservationPerson else u'') + u')',
                        statusObservationColor,
                        documentLocationColor,
                        colorFinance,
                        forceString(calcAge(forceDate(record.value('birthDate')), forceDate(record.value('endDate'))))
                        ]
                eventId = forceRef(record.value('eventId'))
                self.feedTextValueItems[eventId] = forceString(record.value('clientDiet'))
                self.items.append(item)
                _dict = {
                        'observationCode': statusObservationCode,
                        'finance': forceString(record.value('nameFinance')),
                        'clientFeed': countEventFeedId,
                        'contract': nameContract,
                        'bedCode': '',
                        'financeCode': forceString(record.value('codeFinance')),
                        'bedName': '',
                        'orgStructure': forceString(record.value('nameOrgStructure')),
                        'orgStructureFrom': forceString(record.value('nameFromOS')),
                        'observationName': statusObservationName,
                        'observationColor': statusObservationColor,
                        'setDate': CDateTimeInfo(forceDateTime(record.value('receivedBegDate'))),
                        'begDate': CDateTimeInfo(forceDateTime(record.value('begDate'))),
                        'endDate': CDateTimeInfo(forceDateTime(record.value('endDate')))
                    }
                self.itemByName[eventId] = _dict
        for col, order in self.headerSortingCol.items():
            self.sort(col, order)

    def sort(self, col, order=Qt.AscendingOrder):
        self.headerSortingCol = {col: order}
        reverse = order == Qt.DescendingOrder
        if col in [self.clientColumn, self.eventColumn]:
            self.items.sort(key=lambda x: forceInt(x[col]) if x else None, reverse=reverse)
        elif col in [self.birthDateCol, self.hospDateCol, self.receivedDateCol, self.leavedDateCol]:
            self.items.sort(key=lambda x: forceDateTime(x[col]) if x else None, reverse=reverse)
        else:
            self.items.sort(key=lambda x: forceString(x[col]).lower() if x else None, reverse=reverse)
        self.reset()


class CLeavedModel(CMonitoringModel):
    column = [u'С', u'И', u'Д', u'Номер', u'Код', u'Карта', u'ФИО', u'Пол', u'Дата рождения', u'Госпитализирован', u'Поступил', u'Выбыл', u'МЭС', u'MKB', u'Профиль', u'Подразделение', u'Лечащий врач', u'Гражданство', u'М', u'Койко-дни', u'Направитель']
    statusObservationCol = 0
    financeCol = 1
    clientColumn = 3
    eventColumn = 4
    defaultOrderCol = 6
    birthDateCol = 8
    hospDateCol = 9
    receivedDateCol = 10
    leavedDateCol = 11
    MKBColumn = 12
    profileCol = 14
    documentLocationCol = 18
    bedDaysCol = 19
    codeFinanceCol = 21
    bedNameCol = 22
    statusObservationNameCol = 24
    colorStatusObservationCol = 25
    docLocalColorCol = 26
    colorFinanceCol = 27
    ageCol = 28

    def __init__(self, parent):
        CMonitoringModel.__init__(self, parent)
        self.items = []
        self._cols = []
        self.begDays = 0
        self.itemByName = {}
        self.statusObservation = None

    def getBegDays(self):
        return self.begDays

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return QVariant(self.column[section])
            elif role == Qt.ToolTipRole:
                if section == 17:
                    return QVariant(u'Место нахождение учетного документа')
                elif section == self.eventColumn:
                    return QVariant(u'Код события')
        return QVariant()

    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if role == Qt.DisplayRole:
            if column in [self.hospDateCol, self.receivedDateCol, self.leavedDateCol]:
                item = self.items[row]
                return toVariant(item[column].toString('dd.MM.yyyy hh:mm'))
            elif column == self.birthDateCol:
                item = self.items[row]
                return toVariant(forceString(item[column]) + u' (' + item[self.ageCol] + u')')
            else:
                item = self.items[row]
            return toVariant(item[column])
        elif role == Qt.ToolTipRole:
            if column == self.statusObservationCol:
                item = self.items[row]
                if item[self.statusObservationCol]:
                    return QVariant(item[self.statusObservationCol] + u' ' + item[self.statusObservationNameCol])
                else:
                    return QVariant()
            elif column == self.financeCol:
                item = self.items[row]
                return QVariant(unicode(item[self.codeFinanceCol]) + u' ' + item[column])
            elif column == self.profileCol:
                item = self.items[row]
                if item[column]:
                    return QVariant(forceString(item[column]) + u' ' + item[self.bedNameCol])
                else:
                    return QVariant()
        elif role == Qt.BackgroundColorRole:
            if column == self.statusObservationCol and self.items[row][column]:
                return toVariant(QtGui.QColor(self.items[row][self.colorStatusObservationCol]))
            elif column == self.financeCol:
                colorFinance = self.items[row][self.colorFinanceCol]
                if colorFinance:
                    return toVariant(colorFinance)
            elif column == self.documentLocationCol:
                docLocalColor = self.items[row][self.docLocalColorCol]
                if docLocalColor:
                    return toVariant(QtGui.QColor(docLocalColor))
        return QVariant()

    def getClientId(self, row):
        return self.items[row][3]

    def cols(self):
        self._cols = [CCol(u'Статус наблюдения',                   ['statusObservation'], 20, 'l'),
                      CCol(u'Код ИФ',                              ['nameFinance'], 20, 'l'),
                      CCol(u'Договор',                             ['contract'], 20, 'l'),
                      CCol(u'Номер',                               ['client_id'], 20, 'l'),
                      CCol(u'Код события',                         ['event_id'], 20, 'l'),
                      CCol(u'Карта',                               ['externalId'], 20, 'l'),
                      CCol(u'ФИО',                                 ['lastName', 'firstName', 'patrName'], 30, 'l'),
                      CCol(u'Пол',                                 ['sex'], 15, 'l'),
                      CCol(u'Дата рождения',                       ['birthDate'], 20, 'l'),
                      CCol(u'Госпитализирован',                    ['begDateReceived'], 20, 'l'),
                      CCol(u'Поступил',                            ['begDate'], 20, 'l'),
                      CCol(u'Выбыл',                               ['endDate'], 20, 'l'),
                      CCol(u'МЭС',                                 ['mes'], 20, 'l'),
                      CCol(u'MKB',                                 ['MKB'], 20, 'l'),
                      CCol(u'Профиль',                             ['profileName'], 30, 'l'),
                      CCol(u'Подразделение',                       ['nameOS'], 30, 'l'),
                      CCol(u'Лечащий врач',                        ['namePerson'], 30, 'l'),
                      CCol(u'Гражданство',                         ['citizenship'], 30, 'l'),
                      CCol(u'Место нахождение учетного документа', ['hospDocumentLocation'], 30, 'l'),
                      CCol(u'Койко-дни',                           ['bedDays'], 20, 'l'),
                      CCol(u'Направитель',                         ['relegateOrg'], 30, 'l')
                      ]
        return self._cols

    def loadData(self, dialogParams):
        self.begDays = 0
        self.items = []
        self.itemByName = {}
        orgStructureIdList = []
        filterBegDate = dialogParams.get('filterBegDate', None)
        filterEndDate = dialogParams.get('filterEndDate', None)
        filterBegTime = dialogParams.get('filterBegTime', None)
        filterEndTime = dialogParams.get('filterEndTime', None)
        if not filterBegTime.isNull():
            begDateTime = QDateTime(filterBegDate, filterBegTime)
            filterBegDate = begDateTime
        if not filterEndTime.isNull():
            endDateTime = QDateTime(filterEndDate, filterEndTime)
            filterEndDate = endDateTime
        indexSex = dialogParams.get('indexSex', 0)
        ageFor = dialogParams.get('ageFor', 0)
        ageTo = dialogParams.get('ageTo', 150)
        order = dialogParams.get('order', -1)
        eventTypeId = dialogParams.get('eventTypeId', None)
        orgStructureId = dialogParams.get('orgStructureId', None)
        profile = dialogParams.get('treatmentProfile', None)
        codeAttachType = dialogParams.get('codeAttachType', None)
        finance = dialogParams.get('finance', None)
        contractId = dialogParams.get('contractId', None)
        personId = dialogParams.get('personId', None)
        insurerId = dialogParams.get('insurerId', None)
        regionSMO, regionTypeSMO, regionSMOCode = dialogParams.get('regionSMO', (False, 0, None))
        personExecId = dialogParams.get('personExecId', None)
        quotingType = dialogParams.get('quotingType', None)
        accountingSystemId = dialogParams.get('accountingSystemId', None)
        filterClientId = dialogParams.get('filterClientId', None)
        filterEventId = dialogParams.get('filterEventId', None)
        statusObservation = dialogParams.get('statusObservation', None)
        conclusion = dialogParams.get('conclusion', 0)
        assistantId = dialogParams.get('assistantId', None)
        assistantChecked = dialogParams.get('assistantChecked', False)
        leavedIndex = dialogParams.get('leavedIndex', 0)
        eventClosedType = dialogParams.get('eventClosedType', 0)
        filterMES = dialogParams.get('filterMES', u'')
        documentTypeForTracking = dialogParams.get('documentTypeForTracking', None)
        documentLocation = dialogParams.get('documentLocation', None)
        scheduleId = dialogParams.get('scheduleId', None)
        self.statusObservation = statusObservation
        MKBFilter = dialogParams['MKBFilter']
        MKBFrom = dialogParams['MKBFrom']
        MKBTo = dialogParams['MKBTo']
        relegateOrg = dialogParams.get('relegateOrg', None)

        db = QtGui.qApp.db
        tableAPT = db.table('ActionPropertyType')
        tableAP = db.table('ActionProperty')
        tableActionType = db.table('ActionType')
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        tableMAT = db.table('rbMedicalAidType')
        tableMes = db.table('mes.MES')
        tableClient = db.table('Client')
        tableClientPolicy = db.table('ClientPolicy')
        tableAPOS = db.table('ActionProperty_OrgStructure')
        tableOS = db.table('OrgStructure')
        tablePWS = db.table('vrbPersonWithSpeciality')
        tableClientAttach = db.table('ClientAttach')
        tableRBAttachType = db.table('rbAttachType')
        tableContract = db.table('Contract')
        tableRBFinance = db.table('rbFinance')
        tableRBFinanceBC = db.table('rbFinance').alias('rbFinanceByContract')
        tableStatusObservation = db.table('Client_StatusObservation')
        tableOrg = db.table('Organisation')
        tableDocumentTypeForTracking = db.table('Client_DocumentTracking')

        if orgStructureId:
            treeItem = orgStructureId.internalPointer() if orgStructureId.isValid() else None
            orgStructureIdList = self.getOrgStructureIdList(orgStructureId) if treeItem and treeItem._id else []

        if quotingType:
            quotingTypeClass, quotingTypeId = quotingType
            quotingTypeList = self.getQuotingTypeIdList(quotingType)
        else:
            quotingTypeClass = None
            quotingTypeList = None

        groupBY = u''
        cols = [tableAction['begDate'],
                tableAction['id'],
                tableEvent['id'].alias('eventId'),
                tableEvent['externalId'],
                tableEvent['client_id'],
                tableEvent['eventType_id'],
                tableEvent['setDate'],
                tableEvent['execDate'],
                tableClient['lastName'],
                tableClient['firstName'],
                tableClient['patrName'],
                tableClient['sex'],
                tableClient['birthDate'],
                tableAction['endDate'],
                tableMes['code'],
                tableContract['number'].alias('numberContract'),
                tableContract['date'].alias('dateContract'),
                tableContract['resolution'].alias('resolutionContract'),
                tablePWS['name'].alias('namePerson'),
                tableOrg['shortName'].alias('relegateOrg'),
                getMKB(),
                getDataOrgStructureName(u'Отделение'),
                getReceivedBegDate(self.receivedActionTypeIdList),
                getReceivedEndDate(u'Направлен в отделение', self.receivedActionTypeIdList),
                getOSHBP(),
                getStatusObservation(),
                getHospDocumentLocationInfo(),
                """getClientCitizenshipTitle(Client.id, Action.begDate) as citizenship"""
                ]

        queryTable = tableAction.leftJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        queryTable = queryTable.leftJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
        queryTable = queryTable.leftJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
        queryTable = queryTable.leftJoin(tableMAT, tableMAT['id'].eq(tableEventType['medicalAidType_id']))
        queryTable = queryTable.leftJoin(tableMes, tableMes['id'].eq(tableEvent['MES_id']))
        queryTable = queryTable.leftJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
        queryTable = queryTable.leftJoin(tablePWS, tablePWS['id'].eq(tableAction['person_id']))
        queryTable = queryTable.leftJoin(tableOrg, tableEvent['relegateOrg_id'].eq(tableOrg['id']))
        cond = [tableAction['actionType_id'].inlist(self.leavedActionTypeIdList),
                tableAction['deleted'].eq(0),
                tableClient['deleted'].eq(0),
                tableEvent['deleted'].eq(0),
                tableAction['endDate'].isNotNull(),
                tableMAT['code'].inlist(['1', '2', '3', '7']),
                ]
        if scheduleId:
            cond.append(isScheduleBeds(scheduleId))
        if contractId:
            cond.append(tableContract['id'].eq(contractId))
        if MKBFilter:
            cond.append(isMKB(MKBFrom, MKBTo))
        if order:
            cond.append(tableEvent['order'].eq(order))
        if eventTypeId:
            cond.append(tableEvent['eventType_id'].eq(eventTypeId))
        if filterMES:
            cond.append(tableMes['code'].eq(filterMES))

        if eventClosedType == 1:
            cond.append(tableEvent['execDate'].isNotNull())
        elif eventClosedType == 2:
            cond.append(tableEvent['execDate'].isNull())

        if personId:
            cond.append(tableEvent['execPerson_id'].eq(personId))
        if personExecId:
            cond.append(tableAction['person_id'].eq(personExecId))
        if relegateOrg:
            cond.append(tableEvent['relegateOrg_id'].eq(relegateOrg))
        if self.statusObservation:
            queryTable = queryTable.leftJoin(tableStatusObservation,
                                             tableStatusObservation['master_id'].eq(tableClient['id']))
            cond.append(tableStatusObservation['deleted'].eq(0))
            cond.append(tableStatusObservation['statusObservationType_id'].eq(self.statusObservation))
        if accountingSystemId and filterClientId:
            tableIdentification = db.table('ClientIdentification')
            queryTable = queryTable.leftJoin(tableIdentification,
                                             tableIdentification['client_id'].eq(tableClient['id']))
            cond.append(tableIdentification['accountingSystem_id'].eq(accountingSystemId))
            cond.append(tableIdentification['identifier'].eq(filterClientId))
            cond.append(tableIdentification['deleted'].eq(0))
        elif filterClientId:
            cond.append(tableClient['id'].eq(filterClientId))
        if filterEventId:
            cond.append(tableEvent['externalId'].eq(filterEventId))
        if assistantChecked:
            if assistantId:
                cond.append(tableAction['assistant_id'].eq(assistantId))
            else:
                cond.append(tableAction['assistant_id'].isNull())
        if profile:
            cond.append(getHospitalBedProfile(profile))

        if forceInt(codeAttachType) > 0:
            cond.append(tableRBAttachType['code'].eq(codeAttachType))
            queryTable = queryTable.leftJoin(tableClientAttach, tableClient['id'].eq(tableClientAttach['client_id']))
            queryTable = queryTable.leftJoin(tableRBAttachType, tableClientAttach['attachType_id'].eq(tableRBAttachType['id']))

        if indexSex > 0:
            cond.append(tableClient['sex'].eq(indexSex))
        if ageFor <= ageTo and not (ageFor == 0 and ageTo == 150):
            cond.append(getAgeRangeCond(ageFor, ageTo))

        if forceBool(filterBegDate.date()):
            cond.append(tableAction['endDate'].ge(filterBegDate))
        if forceBool(filterEndDate.date()):
            cond.append(tableAction['endDate'].le(filterEndDate))

        if conclusion and conclusion != u'не определено':
            cond.append(getStringProperty(u'Исход госпитализации', u'(APS.value %s)' % (updateLIKE(conclusion))))

        if insurerId or regionSMO:
            queryTable = queryTable.innerJoin(tableClientPolicy,
                                              u'''(ClientPolicy.id = getClientPolicyIdForDate(Client.id, IF(Contract.id IS NOT NULL AND Contract.deleted=0, IF(rbFinance.code = 2, 1, IF(rbFinance.code = 3, 0, 1)), 1), IF(Event.execDate IS NOT NULL, Event.execDate, Event.setDate), Event.id))''')
            if not regionSMO:
                cond.append(tableClientPolicy['insurer_id'].eq(insurerId))
            else:
                tableOrganisation = db.table('Organisation').alias('Org_Area')
                queryTable = queryTable.innerJoin(tableOrganisation,
                                                  [tableOrganisation['id'].eq(tableClientPolicy['insurer_id']),
                                                   tableOrganisation['deleted'].eq(0)])
                if regionSMOCode:
                    if regionTypeSMO:
                        cond.append(tableOrganisation['area'].notlike(regionSMOCode))
                    else:
                        cond.append(tableOrganisation['area'].like(regionSMOCode))

        if quotingTypeClass is not None:
            cond.append(getDataClientQuoting(u'Квота', quotingTypeList))

        if QtGui.qApp.defaultHospitalBedFinanceByMoving() == 2:
            cols.append(
                u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.code, IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinanceByContract.code, NULL)) AS codeFinance')
            cols.append(
                u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.name, IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinanceByContract.name, NULL)) AS nameFinance')
            cols.append(getClientPolicyForDate())
            if finance:
                cond.append(
                    '''((Action.finance_id IS NOT NULL AND Action.deleted=0 AND Action.finance_id = %s) OR (Contract.finance_id = %s))''' % (
                    str(finance), str(finance)))
                queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
                queryTable = queryTable.leftJoin(tableContract, [tableContract['id'].eq(tableEvent['contract_id']),
                                                                 tableContract['deleted'].eq(0)])
                queryTable = queryTable.leftJoin(tableRBFinanceBC,
                                                 tableRBFinanceBC['id'].eq(tableContract['finance_id']))
            else:
                queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
                queryTable = queryTable.leftJoin(tableContract, [tableContract['id'].eq(tableEvent['contract_id']),
                                                                 tableContract['deleted'].eq(0)])
                queryTable = queryTable.leftJoin(tableRBFinanceBC,
                                                 tableRBFinanceBC['id'].eq(tableContract['finance_id']))
        elif QtGui.qApp.defaultHospitalBedFinanceByMoving() == 1:
            cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.code, NULL) AS codeFinance')
            cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.name, NULL) AS nameFinance')
            cols.append(getActionClientPolicyForDate())
            queryTable = queryTable.leftJoin(tableContract, [tableContract['id'].eq(tableEvent['contract_id']),
                                                             tableContract['deleted'].eq(0)])
            if finance:
                cond.append('''(Action.finance_id IS NOT NULL AND Action.deleted=0 AND Action.finance_id = %s)''' % (
                    str(finance)))
                queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
            else:
                queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
        else:
            cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.code, NULL) AS codeFinance')
            cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.name, NULL) AS nameFinance')
            cols.append(getContractClientPolicyForDate())
            if finance:
                cond.append(tableRBFinance['id'].eq(finance))
                queryTable = queryTable.leftJoin(tableContract, [tableContract['id'].eq(tableEvent['contract_id']),
                                                                 tableContract['deleted'].eq(0)])
                queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
            else:
                queryTable = queryTable.leftJoin(tableContract, [tableContract['id'].eq(tableEvent['contract_id']),
                                                                 tableContract['deleted'].eq(0)])
                queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))

        if documentTypeForTracking:
            if documentTypeForTracking != u'specialValueID':
                cond.append(tableDocumentTypeForTracking['deleted'].eq(0))
                queryTable = queryTable.leftJoin(tableDocumentTypeForTracking,
                                                 tableClient['id'].eq(tableDocumentTypeForTracking['client_id']))
                cond.append(tableDocumentTypeForTracking['documentTypeForTracking_id'].eq(documentTypeForTracking))
                cond.append(tableDocumentTypeForTracking['documentNumber'].eq(tableEvent['externalId']))
                groupBY = 'Event.id'
        if documentLocation:
            tableDocumentLocation = db.table('Client_DocumentTrackingItem')
            if not documentTypeForTracking:
                queryTable = queryTable.leftJoin(tableDocumentTypeForTracking,
                                                 tableClient['id'].eq(tableDocumentTypeForTracking['client_id']))
                cond.append(tableDocumentTypeForTracking['documentNumber'].eq(tableEvent['externalId']))
            queryTable = queryTable.leftJoin(tableDocumentLocation,
                                             tableDocumentTypeForTracking['id'].eq(tableDocumentLocation['master_id']))
            tableDocumentLocationLimit = db.table('Client_DocumentTrackingItem').alias('tableDocumentLocationLimit')
            cond.append(tableDocumentLocation['documentLocation_id'].inlist(documentLocation))
            cond.append(tableDocumentLocation['id'].eqEx(
                '(%s)' % db.selectStmt(tableDocumentLocationLimit, tableDocumentLocationLimit['id'],
                                       tableDocumentLocationLimit['master_id'].eq(tableDocumentLocation['master_id']),
                                       'documentLocationDate desc, documentLocationTime desc limit 1')))
            if groupBY == '':
                groupBY = 'Event.id'

        if QtGui.qApp.userHasAnyRight([urHBVisibleOwnEventsParentOrgStructureOnly, urHBVisibleOwnEventsOrgStructureOnly]):
            tableExecPerson = db.table('Person')
            queryTable = queryTable.leftJoin(tableExecPerson, tableExecPerson['id'].eq(tableEvent['execPerson_id']))
            uOrgStructureId = forceRef(db.translate('Person', 'id', QtGui.qApp.userId, 'orgStructure_id'))
            if QtGui.qApp.userHasRight(urHBVisibleOwnEventsParentOrgStructureOnly):
                parentOrgStructure = getParentOrgStructureId(uOrgStructureId)
                uOrgStructureList = getOrgStructureDescendants(parentOrgStructure if parentOrgStructure else uOrgStructureId)
                cond.append(db.joinOr([tableExecPerson['orgStructure_id'].inlist(uOrgStructureList), tableEventType['ignoreVisibleRights'].eq(1)]))
            elif QtGui.qApp.userHasRight(urHBVisibleOwnEventsOrgStructureOnly):
                uOrgStructureList = getOrgStructureDescendants(uOrgStructureId)
                cond.append(db.joinOr([tableExecPerson['orgStructure_id'].inlist(uOrgStructureList), tableEventType['ignoreVisibleRights'].eq(1)]))

        if leavedIndex == 1 or leavedIndex == 2:
            queryTable = queryTable.leftJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
            queryTable = queryTable.leftJoin(tableAP, tableAP['type_id'].eq(tableAPT['id']))
            queryTable = queryTable.leftJoin(tableAPOS, tableAPOS['id'].eq(tableAP['id']))
            queryTable = queryTable.leftJoin(tableOS, tableOS['id'].eq(tableAPOS['value']))

            cond.append(tableAPT['name'].like(u'Отделение пребывания'))
            cond.append(tableAP['action_id'].eq(tableAction['id']))
            cond.append(tableAP['deleted'].eq(0))

            cols.append(getLeavedEndDate(self.leavedActionTypeIdList))

            if orgStructureIdList:
                cond.append(tableOS['deleted'].eq(0))
                cond.append(tableAPOS['value'].inlist(orgStructureIdList))

            if leavedIndex == 1:
                cond.append('''NOT %s''' % (getTransferPropertyIn(u'Переведен в отделение')))

        elif leavedIndex == 0 or leavedIndex == 3 or leavedIndex == 4:
            cols.append(tableAction['endDate'].alias('leavedEndDate'))
            if orgStructureIdList:
                cond.append(getDataOrgStructure(u'Отделение', orgStructureIdList, False))

            if leavedIndex == 3:
                cond.append(u'''EXISTS(SELECT A.id
                                FROM Action AS A
                                WHERE A.event_id = Event.id AND A.deleted = 0
                                AND A.actionType_id IN (%s))''' % (','.join(str(movingId) for movingId in self.movingActionTypeIdList if movingId)))
            elif leavedIndex == 4:
                cond.append(u'''NOT EXISTS(SELECT A.id
                                FROM Action AS A
                                WHERE A.event_id = Event.id AND A.deleted = 0
                                AND A.actionType_id IN (%s))''' % (','.join(str(movingId) for movingId in self.movingActionTypeIdList if movingId)))

        if groupBY != '':
            records = db.getRecordListGroupBy(queryTable, cols, cond, groupBY)
        else:
            records = db.getRecordList(queryTable, cols, cond)
        for record in records:
            documentLocationInfo = forceString(record.value('documentLocationInfo')).split("  ")
            hospDocumentLocation = forceString(documentLocationInfo[0]) if len(documentLocationInfo) >= 1 else ''
            documentLocationColor = forceString(documentLocationInfo[1]) if len(documentLocationInfo) > 1 else ''
            if documentTypeForTracking == u'specialValueID':
                if hospDocumentLocation != '':
                    continue
            statusObservation = forceString(record.value('statusObservation')).split('|')
            statusObservationCode = forceString(statusObservation[0]) if len(statusObservation) >= 1 else u''
            statusObservationName = forceString(statusObservation[1]) if len(statusObservation) >= 2 else u''
            statusObservationColor = forceString(statusObservation[2]) if len(statusObservation) >= 3 else u''
            statusObservationDate = forceString(statusObservation[3]) if len(statusObservation) >= 4 else u''
            statusObservationPerson = forceString(statusObservation[4]) if len(statusObservation) >= 5 else u''
            begDate = forceDate(record.value('receivedBegDate'))
            policyEndDate = forceDate(record.value('policyEndDate'))
            colorFinance = None
            if policyEndDate:
                if begDate < policyEndDate <= begDate.addDays(3):
                    colorFinance = QtGui.QColor(Qt.yellow)
                elif begDate >= policyEndDate:
                    colorFinance = QtGui.QColor(Qt.red)
            nameContract = ' '.join([forceString(record.value(name)) for name in ('numberContract', 'dateContract', 'resolutionContract')])
            setDate = forceDate(record.value('setDate'))
            execDate = forceDate(record.value('execDate'))
            bedDays = updateDurationEvent(setDate, execDate if execDate.isValid() else QDate().currentDate(), filterBegDate, filterEndDate, forceRef(record.value('eventType_id')), isPresence=False)
            self.begDays += forceInt(bedDays) if bedDays != u'-' else 0
            item = [statusObservationCode,
                    forceString(record.value('nameFinance')),
                    nameContract,
                    forceRef(record.value('client_id')),
                    forceRef(record.value('eventId')),
                    forceString(record.value('externalId')),
                    forceString(record.value('lastName')) + u' ' + forceString(record.value('firstName')) + u' ' + forceString(record.value('patrName')),
                    self.sex[forceInt(record.value('sex'))],
                    forceDate(record.value('birthDate')),
                    forceDateTime(record.value('receivedBegDate')),
                    forceDateTime(record.value('receivedEndDate')),
                    forceDateTime(record.value('endDate')),
                    forceString(record.value('code')),
                    forceString(record.value('MKB')),
                    forceString(record.value('profileName')),
                    forceString(record.value('nameOrgStructure')),
                    forceString(record.value('namePerson')),
                    forceString(record.value('citizenship')),
                    hospDocumentLocation,
                    bedDays,
                    forceString(record.value('relegateOrg')),
                    forceString(record.value('codeFinance')),
                    '',
                    forceString(record.value('externalId')),
                    statusObservationName + u' (' + (statusObservationDate if statusObservationDate else u'') + u' ' + (statusObservationPerson if statusObservationPerson else u'') + u')',
                    statusObservationColor,
                    documentLocationColor,
                    colorFinance,
                    forceString(calcAge(forceDate(record.value('birthDate')), forceDate(record.value('endDate'))))
                    ]
            self.items.append(item)
            eventId = forceRef(record.value('eventId'))
            _dict = {
                    'observationCode': statusObservationCode,
                    'finance': forceString(record.value('nameFinance')),
                    'contract': nameContract,
                    'orgStructure': forceString(record.value('nameOrgStructure')),
                    'financeCode': forceString(record.value('codeFinance')),
                    'observationName': statusObservationName,
                    'observationColor': statusObservationColor,
                    'setDate': CDateTimeInfo(forceDateTime(record.value('receivedBegDate'))),
                    'begDate': CDateTimeInfo(forceDateTime(record.value('receivedEndDate'))),
                    'endDate': CDateTimeInfo(forceDateTime(record.value('endDate'))),
                    'profile': forceString(record.value('profileName'))
                }
            self.itemByName[eventId] = _dict

        for col, order in self.headerSortingCol.items():
            self.sort(col, order)


    def sort(self, col, order=Qt.AscendingOrder):
        self.headerSortingCol = {col: order}
        reverse = order == Qt.DescendingOrder
        if col == self.bedDaysCol:
            self.items.sort(key=lambda x: forceInt(0 if x[col] == '-' else x[col]) if x else None, reverse=reverse)
        elif col in [self.clientColumn, self.eventColumn]:
            self.items.sort(key=lambda x: forceInt(x[col]) if x else None, reverse=reverse)
        elif col in [self.birthDateCol, self.hospDateCol, self.receivedDateCol, self.leavedDateCol]:
            self.items.sort(key=lambda x: forceDateTime(x[col]) if x else None, reverse=reverse)
        else:
            self.items.sort(key=lambda x: forceString(x[col]).lower() if x else None, reverse=reverse)
        self.reset()


class CReabyToLeaveModel(CMonitoringModel):
    column = [u'С', u'И', u'Д', u'П', u'Номер', u'Код', u'Карта', u'ФИО', u'Пол', u'Дата рождения', u'Госпитализирован', u'Поступил', u'Плановая дата выбытия', u'MKB', u'Профиль', u'Подразделение', u'Лечащий врач', u'Гражданство', u'М', u'Направитель']
    statusObservationCol = 0
    financeCol = 1
    feedCol = 3
    clientColumn = 4
    eventColumn = 5
    defaultOrderCol = 7
    birthDateCol = 9
    hospDateCol = 10
    receivedDateCol = 11
    planLeavedDateCol = 12
    MKBColumn = 13
    profileCol = 14
    documentLocationCol = 18
    codeFinanceCol = 20
    bedNameCol = 21
    statusObservationNameCol = 22
    colorStatusObservationCol = 23
    docLocalColorCol = 24
    colorFinanceCol = 25
    ageCol = 26

    def __init__(self, parent):
        CMonitoringModel.__init__(self, parent)
        self.items = []
        self._cols = []
        self.itemByName = {}
        self.headerSortingCol = {}
        self.statusObservation = None

    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return QVariant(self.column[section])
            elif role == Qt.ToolTipRole:
                if section == 0:
                    return QVariant(u'Статус наблюдения пациента')
                elif section == 1:
                    return QVariant(u'Источник финансирования (код)')
                elif section == 2:
                    return QVariant(u'Договор')
                elif section == 3:
                    return QVariant(u'Питание')
                elif section == 17:
                    return QVariant(u'Место нахождения учетного документа')
                elif section == self.eventColumn:
                    return QVariant(u'Код события')
        return QVariant()

    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if role == Qt.DisplayRole:
            if column in [self.hospDateCol, self.receivedDateCol, self.planLeavedDateCol]:
                item = self.items[row]
                return toVariant(item[column].toString('dd.MM.yyyy hh:mm'))
            elif column == self.birthDateCol:
                item = self.items[row]
                return toVariant(forceString(item[column]) + u' (' + item[self.ageCol] + u')')
            elif column == self.feedCol:
                return QVariant()
            else:
                item = self.items[row]
                return toVariant(item[column])
        elif role == Qt.CheckStateRole:
            if column == self.feedCol:
                item = self.items[row]
                return toVariant(Qt.Checked if item[column] else Qt.Unchecked)
        elif role == Qt.ToolTipRole:
            if column == self.statusObservationCol:
                item = self.items[row]
                if item[column]:
                    return QVariant(forceString(item[column]) + u' ' + item[self.statusObservationNameCol])
                else:
                    return QVariant()
            elif column == self.financeCol:
                item = self.items[row]
                return QVariant(item[self.codeFinanceCol] + u' ' + item[column])
            elif column == self.profileCol:
                item = self.items[row]
                return QVariant(forceString(item[column]) + u' ' + item[self.bedNameCol])
        elif role == Qt.BackgroundColorRole:
            if column == self.statusObservationCol and self.items[row][column]:
                return toVariant(QtGui.QColor(self.items[row][self.colorStatusObservationCol]))
            elif column == self.financeCol:
                colorFinance = self.items[row][self.colorFinanceCol]
                if colorFinance:
                    return toVariant(colorFinance)
            elif column == self.documentLocationCol:
                docLocalColor = self.items[row][self.docLocalColorCol]
                if docLocalColor:
                    return toVariant(QtGui.QColor(docLocalColor))
        return QVariant()

    def cols(self):
        self._cols = [CCol(u'Статус наблюдения',                   ['statusObservation'], 20, 'l'),
                      CCol(u'Код ИФ',                              ['nameFinance'], 20, 'l'),
                      CCol(u'Договор',                             ['contract'], 20, 'l'),
                      CCol(u'Питание',                             ['feed'], 20, 'l'),
                      CCol(u'Номер',                               ['client_id'], 20, 'l'),
                      CCol(u'Код события',                         ['event_id'], 20, 'l'),
                      CCol(u'Карта',                               ['externalId'], 20, 'l'),
                      CCol(u'ФИО',                                 ['lastName', 'firstName', 'patrName'], 30, 'l'),
                      CCol(u'Пол',                                 ['sex'], 15, 'l'),
                      CCol(u'Дата рождения',                       ['birthDate'], 20, 'l'),
                      CCol(u'Госпитализирован',                    ['begDateReceived'], 20, 'l'),
                      CCol(u'Поступил',                            ['begDate'], 20, 'l'),
                      CCol(u'Плановая дата выбытия',               ['plannedEndDate'], 20, 'l'),
                      CCol(u'MKB',                                 ['MKB'], 20, 'l'),
                      CCol(u'Профиль',                             ['profileName'], 30, 'l'),
                      CCol(u'Подразделение',                       ['nameOS'], 30, 'l'),
                      CCol(u'Лечащий врач',                        ['namePerson'], 30, 'l'),
                      CCol(u'Гражданство',                         ['citizenship'], 30, 'l'),
                      CCol(u'Место нахождения учетного документа', ['hospDocumentLocation'], 30, 'l'),
                      CCol(u'Направитель',                         ['relegateOrg'], 30, 'l')
                      ]
        return self._cols

    def loadData(self, dialogParams):
        self.items = []
        self.itemByName = {}
        orgStructureIdList = []
        filterBegDate = dialogParams.get('filterBegDate', None)
        filterEndDate = dialogParams.get('filterEndDate', None)
        filterBegTime = dialogParams.get('filterBegTime', None)
        filterEndTime = dialogParams.get('filterEndTime', None)
        if not filterBegTime.isNull():
            begDateTime = QDateTime(filterBegDate, filterBegTime)
            filterBegDate = begDateTime
        if not filterEndTime.isNull():
            endDateTime = QDateTime(filterEndDate, filterEndTime)
            filterEndDate = endDateTime
        typeReabyToLeave = dialogParams.get('leavedIndex', 0)
        indexSex = dialogParams.get('indexSex', 0)
        ageFor = dialogParams.get('ageFor', 0)
        ageTo = dialogParams.get('ageTo', 150)
        order = dialogParams.get('order', -1)
        eventTypeId = dialogParams.get('eventTypeId', None)
        orgStructureId = dialogParams.get('orgStructureId', None)
        profile = dialogParams.get('treatmentProfile', None)
        codeAttachType = dialogParams.get('codeAttachType', None)
        finance = dialogParams.get('finance', None)
        contractId = dialogParams.get('contractId', None)
        feed = dialogParams.get('feed', None)
        dateFeed = dialogParams.get('dateFeed', None)
        personId = dialogParams.get('personId', None)
        insurerId = dialogParams.get('insurerId', None)
        regionSMO, regionTypeSMO, regionSMOCode = dialogParams.get('regionSMO', (False, 0, None))
        personExecId = dialogParams.get('personExecId', None)
        quotingType = dialogParams.get('quotingType', None)
        accountingSystemId = dialogParams.get('accountingSystemId', None)
        filterClientId = dialogParams.get('filterClientId', None)
        filterEventId = dialogParams.get('filterEventId', None)
        statusObservation = dialogParams.get('statusObservation', None)
        filterMES = dialogParams.get('filterMES', u'')
        MKBFilter = dialogParams['MKBFilter']
        MKBFrom   = dialogParams['MKBFrom']
        MKBTo     = dialogParams['MKBTo']
        self.statusObservation = statusObservation
        if orgStructureId:
            treeItem = orgStructureId.internalPointer() if orgStructureId.isValid() else None
            orgStructureIdList = self.getOrgStructureIdList(orgStructureId) if treeItem and treeItem._id else []
        if quotingType:
            quotingTypeClass, quotingTypeId = quotingType
            quotingTypeList = self.getQuotingTypeIdList(quotingType)
        else:
            quotingTypeClass = None
            quotingTypeList = None

        db = QtGui.qApp.db
        tableAPT = db.table('ActionPropertyType')
        tableAP = db.table('ActionProperty')
        tableActionType = db.table('ActionType')
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        tableClient = db.table('Client')
        tableClientPolicy = db.table('ClientPolicy')
        tableOS = db.table('OrgStructure')
        tablePWS = db.table('vrbPersonWithSpeciality')
        tableAPOS = db.table('ActionProperty_OrgStructure')
        tableClientAttach = db.table('ClientAttach')
        tableRBAttachType = db.table('rbAttachType')
        tableContract = db.table('Contract')
        tableRBFinance = db.table('rbFinance')
        tableRBFinanceBC = db.table('rbFinance').alias('rbFinanceByContract')
        tableEvent_Feed = db.table('Event_Feed')
        tableStatusObservation= db.table('Client_StatusObservation')
        tableOrg = db.table('Organisation')

        def getActionIdList(dialogParams, actionTypeIdListByFlatCode):
            filterBegDate = dialogParams.get('filterBegDate', None)
            filterEndDate = dialogParams.get('filterEndDate', None)
            filterBegTime = dialogParams.get('filterBegTime', None)
            filterEndTime = dialogParams.get('filterEndTime', None)
            if not filterBegTime.isNull():
                begDateTime = QDateTime(filterBegDate, filterBegTime)
                filterBegDate = begDateTime
            if not filterEndTime.isNull():
                endDateTime = QDateTime(filterEndDate, filterEndTime)
                filterEndDate = endDateTime
            db = QtGui.qApp.db
            tableAction = db.table('Action')
            cond = [ tableAction['actionType_id'].inlist(actionTypeIdListByFlatCode),
                     tableAction['deleted'].eq(0),
                   ]
            if not forceBool(filterBegDate.date()):
                filterBegDate = QDate.currentDate()
                cond.append(db.joinOr([tableAction['plannedEndDate'].isNull(), tableAction['plannedEndDate'].eq(filterBegDate)]))
            else:
                cond.append(tableAction['plannedEndDate'].isNotNull())
                cond.append(tableAction['plannedEndDate'].ge(filterBegDate))
            if forceBool(filterEndDate.date()):
                cond.append(tableAction['plannedEndDate'].isNotNull())
                cond.append(tableAction['plannedEndDate'].le(filterEndDate))
            return db.getDistinctIdList(tableAction, [tableAction['id']], cond)

        movingActionIdList = getActionIdList(dialogParams, self.movingActionTypeIdList)
        if not movingActionIdList:
            self.items = []
            self.reset()
            return
        cols = [tableAction['id'],
                tableEvent['id'].alias('eventId'),
                tableEvent['client_id'],
                tableEvent['externalId'],
                tableClient['lastName'],
                tableClient['firstName'],
                tableClient['patrName'],
                tableClient['sex'],
                tableClient['birthDate'],
                tableAction['begDate'],
                tableAction['endDate'],
                tableAction['plannedEndDate'],
                tableEvent['setDate'],
                tableContract['number'].alias('numberContract'),
                tableContract['date'].alias('dateContract'),
                tableContract['resolution'].alias('resolutionContract'),
                tablePWS['name'].alias('namePerson'),
                tableOrg['shortName'].alias('relegateOrg')
                ]
        cols.append(getMKB())
        cols.append(getHospDocumentLocationInfo())
        cols.append(getReceivedBegDate(self.receivedActionTypeIdList))
        if not dateFeed:
            dateFeed = QDate().currentDate().addDays(1)
        cols.append(getEventFeedId(u'', tableEvent_Feed['date'].formatValue(dateFeed), u''' AS countEventFeedId'''))
        cols.append(getHBProfileFromBed())
        cols.append(getStatusObservation())
        cols.append("""getClientCitizenshipTitle(Client.id, Action.plannedEndDate) as citizenship""")
        cols.append(u'IF(OrgStructure.id IS NOT NULL AND OrgStructure.deleted=0, OrgStructure.name, NULL) AS orgStructureName')
        queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
        queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
        queryTable = queryTable.leftJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
        queryTable = queryTable.leftJoin(tableAP, tableAP['type_id'].eq(tableAPT['id']))
        queryTable = queryTable.leftJoin(tableAPOS, tableAPOS['id'].eq(tableAP['id']))
        queryTable = queryTable.leftJoin(tableOS, tableOS['id'].eq(tableAPOS['value']))
        queryTable = queryTable.leftJoin(tablePWS, tablePWS['id'].eq(tableAction['person_id']))
        queryTable = queryTable.leftJoin(tableOrg, tableEvent['relegateOrg_id'].eq(tableOrg['id']))
        cond = [tableAction['actionType_id'].inlist(self.movingActionTypeIdList),
                tableAction['deleted'].eq(0),
                tableEvent['deleted'].eq(0),
                tableAP['deleted'].eq(0),
                tableAPT['deleted'].eq(0),
                tableClient['deleted'].eq(0),
                tableAP['action_id'].eq(tableAction['id']),
                tableAPT['name'].like(u'Отделение пребывания')
               ]

        if contractId:
            cond.append(tableContract['id'].eq(contractId))
        if MKBFilter:
            cond.append(isMKB(MKBFrom, MKBTo))
        if order:
           cond.append(tableEvent['order'].eq(order))
        if eventTypeId:
           cond.append(tableEvent['eventType_id'].eq(eventTypeId))
        if filterMES:
            tableMes = db.table('mes.MES')
            queryTable = queryTable.leftJoin(tableMes, tableMes['id'].eq(tableEvent['MES_id']))
            cond.append(tableMes['code'].eq(filterMES))
        tableEventType = db.table('EventType')
        queryTable = queryTable.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))

        if QtGui.qApp.userHasAnyRight([urHBVisibleOwnEventsParentOrgStructureOnly, urHBVisibleOwnEventsOrgStructureOnly]):
            tableExecPerson = db.table('Person')
            queryTable = queryTable.leftJoin(tableExecPerson, tableExecPerson['id'].eq(tableEvent['execPerson_id']))
            uOrgStructureId = forceRef(db.translate('Person', 'id', QtGui.qApp.userId, 'orgStructure_id'))
            if QtGui.qApp.userHasRight(urHBVisibleOwnEventsParentOrgStructureOnly):
                parentOrgStructure = getParentOrgStructureId(uOrgStructureId)
                uOrgStructureList = getOrgStructureDescendants(parentOrgStructure if parentOrgStructure else uOrgStructureId)
                cond.append(db.joinOr([tableExecPerson['orgStructure_id'].inlist(uOrgStructureList), tableEventType['ignoreVisibleRights'].eq(1)]))
            elif QtGui.qApp.userHasRight(urHBVisibleOwnEventsOrgStructureOnly):
                uOrgStructureList = getOrgStructureDescendants(uOrgStructureId)
                cond.append(db.joinOr([tableExecPerson['orgStructure_id'].inlist(uOrgStructureList), tableEventType['ignoreVisibleRights'].eq(1)]))

        cond.append(u"(EventType.medicalAidType_id IN (SELECT rbMedicalAidType.id from rbMedicalAidType where rbMedicalAidType.code IN ('1', '2', '3', '7')))")
        cond.append(tableAction['endDate'].isNull())
        # cond.append(u'Action.plannedEndDate IS NOT NULL')
        if personId:
            cond.append(tableEvent['execPerson_id'].eq(personId))
        if personExecId:
           cond.append(tableAction['person_id'].eq(personExecId))
        if self.statusObservation:
            cond.append(existsStatusObservation(self.statusObservation))
        if accountingSystemId and filterClientId:
            tableIdentification = db.table('ClientIdentification')
            queryTable = queryTable.innerJoin(tableIdentification, tableIdentification['client_id'].eq(tableClient['id']))
            cond.append(tableIdentification['accountingSystem_id'].eq(accountingSystemId))
            cond.append(tableIdentification['identifier'].eq(filterClientId))
            cond.append(tableIdentification['deleted'].eq(0))
        elif filterClientId:
            cond.append(tableClient['id'].eq(filterClientId))
        if filterEventId:
            cond.append(tableEvent['externalId'].eq(filterEventId))
        if not forceBool(filterBegDate.date()):
            filterBegDate = QDate().currentDate()
            cond.append(db.joinOr([tableAction['plannedEndDate'].isNull(), tableAction['plannedEndDate'].eq(filterBegDate)]))
        else:
            cond.append(tableAction['plannedEndDate'].isNotNull())
            cond.append(tableAction['plannedEndDate'].ge(filterBegDate))
        if forceBool(filterEndDate.date()):
            cond.append(tableAction['plannedEndDate'].isNotNull())
            cond.append(tableAction['plannedEndDate'].le(filterEndDate))
        if orgStructureIdList:
            cond.append(tableOS['deleted'].eq(0))
            cond.append(tableAPOS['value'].inlist(orgStructureIdList))
        if quotingTypeClass is not None:
            cond.append(getDataClientQuoting(u'Квота', quotingTypeList))
        if feed == 1:
            cond.append('NOT %s'%(getEventFeedId(u'',tableEvent_Feed['date'].formatValue(dateFeed))))
        elif feed == 2:
            cond.append('%s'%(getEventFeedId(u'',tableEvent_Feed['date'].formatValue(dateFeed), alias=u'', refusalToEat = 0)))
        elif feed == 3:
            cond.append('%s'%(getEventFeedId(u'',tableEvent_Feed['date'].formatValue(dateFeed), alias=u'', refusalToEat = 1)))
        if QtGui.qApp.defaultHospitalBedFinanceByMoving() == 2:
            cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.code, IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinanceByContract.code, NULL)) AS codeFinance')
            cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.name, IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinanceByContract.name, NULL)) AS nameFinance')
            cols.append(getClientPolicyForDate())
            if finance:
                cond.append('''((Action.finance_id IS NOT NULL AND Action.deleted=0 AND Action.finance_id = %s) OR (Contract.id IS NOT NULL AND Contract.deleted=0 AND Contract.finance_id = %s))'''%(str(finance), str(finance)))
                queryTable = queryTable.innerJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
                queryTable = queryTable.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                queryTable = queryTable.innerJoin(tableRBFinanceBC, tableRBFinanceBC['id'].eq(tableContract['finance_id']))
            else:
                queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
                queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                queryTable = queryTable.leftJoin(tableRBFinanceBC, tableRBFinanceBC['id'].eq(tableContract['finance_id']))
        elif QtGui.qApp.defaultHospitalBedFinanceByMoving() == 1:
            cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.code, NULL) AS codeFinance')
            cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.name, NULL) AS nameFinance')
            cols.append(getActionClientPolicyForDate())
            queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
            if finance:
                cond.append('''(Action.finance_id IS NOT NULL AND Action.deleted=0 AND Action.finance_id = %s)'''%(str(finance)))
                queryTable = queryTable.innerJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
            else:
                queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
        else:
            cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.code, NULL) AS codeFinance')
            cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.name, NULL) AS nameFinance')
            cols.append(getContractClientPolicyForDate())
            if finance:
                cond.append(tableContract['deleted'].eq(0))
                cond.append(tableRBFinance['id'].eq(finance))
                queryTable = queryTable.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                queryTable = queryTable.innerJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
            else:
                queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
        cond.append('(Contract.id IS NOT NULL AND Contract.deleted=0) OR (Contract.id IS NULL)')
        if forceInt(codeAttachType) > 0:
            cond.append(tableRBAttachType['code'].eq(codeAttachType))
            queryTable = queryTable.innerJoin(tableClientAttach, tableClient['id'].eq(tableClientAttach['client_id']))
            queryTable = queryTable.innerJoin(tableRBAttachType, tableClientAttach['attachType_id'].eq(tableRBAttachType['id']))
        if indexSex > 0:
            cond.append(tableClient['sex'].eq(indexSex))
        if ageFor <= ageTo:
            cond.append(getAgeRangeCond(ageFor, ageTo))
        if typeReabyToLeave:
            cond.append('''%s'''%(getTransferPropertyIn(u'Переведен в отделение')))
        else:
            cond.append('''NOT %s'''%(getTransferPropertyIn(u'Переведен в отделение')))
        if profile:
            cond.append(getHospitalBedProfileFromBed(profile))

        if insurerId or regionSMO:
            queryTable = queryTable.innerJoin(tableClientPolicy,
                                              u'''(ClientPolicy.id = getClientPolicyIdForDate(Client.id, IF(Contract.id IS NOT NULL AND Contract.deleted=0, IF(rbFinance.code = 2, 1, IF(rbFinance.code = 3, 0, 1)), 1), IF(Event.execDate IS NOT NULL, Event.execDate, Event.setDate), Event.id))''')
            if not regionSMO:
                cond.append(tableClientPolicy['insurer_id'].eq(insurerId))
            else:
                tableOrganisation = db.table('Organisation').alias('Org_Area')
                queryTable = queryTable.innerJoin(tableOrganisation, [tableOrganisation['id'].eq(tableClientPolicy['insurer_id']), tableOrganisation['deleted'].eq(0)])
                if regionSMOCode:
                    if regionTypeSMO:
                        cond.append(tableOrganisation['area'].notlike(regionSMOCode))
                    else:
                        cond.append(tableOrganisation['area'].like(regionSMOCode))

        recordsMoving = db.getRecordList(queryTable, cols, cond)
        for record in recordsMoving:
            countEventFeedId = forceBool(record.value('countEventFeedId'))
            if (feed == 1 and not countEventFeedId) or (feed == 2 and countEventFeedId) or not feed or feed == 3:
                eventId = forceRef(record.value('eventId'))
                statusObservation = forceString(record.value('statusObservation')).split('|')
                statusObservationCode = forceString(statusObservation[0]) if len(statusObservation)>=1 else u''
                statusObservationName = forceString(statusObservation[1]) if len(statusObservation)>=2 else u''
                statusObservationColor = forceString(statusObservation[2]) if len(statusObservation)>=3 else u''
                statusObservationDate = forceString(statusObservation[3]) if len(statusObservation)>=4 else u''
                statusObservationPerson = forceString(statusObservation[4]) if len(statusObservation)>=5 else u''
                nameFinance = forceString(record.value('nameFinance'))
                begDate = forceDate(record.value('begDate'))
                policyEndDate = forceDate(record.value('policyEndDate'))
                colorFinance = None
                if policyEndDate:
                    if begDate < policyEndDate <= begDate.addDays(3):
                       colorFinance = QtGui.QColor(Qt.yellow)
                    elif begDate >= policyEndDate:
                        colorFinance = QtGui.QColor(Qt.red)
                nameContract = ' '.join([forceString(record.value(name)) for name in ('numberContract', 'dateContract', 'resolutionContract')])
                documentLocationInfo  = forceString(record.value('documentLocationInfo')).split("  ")
                hospDocumentLocation  = forceString(documentLocationInfo[0]) if len(documentLocationInfo)>=1 else ''
                documentLocationColor = forceString(documentLocationInfo[1]) if len(documentLocationInfo)>1 else ''
                item = [statusObservationCode,
                        nameFinance,
                        nameContract,
                        countEventFeedId,
                        forceRef(record.value('client_id')),
                        eventId,
                        forceString(record.value('externalId')),
                        forceString(record.value('lastName')) + u' ' + forceString(record.value('firstName')) + u' ' + forceString(record.value('patrName')),
                        self.sex[forceInt(record.value('sex'))],
                        forceDate(record.value('birthDate')),
                        forceDateTime(record.value('receivedBegDate')),
                        forceDateTime(record.value('begDate')),
                        forceDateTime(record.value('plannedEndDate')),
                        forceString(record.value('MKB')),
                        forceString(record.value('profileName')),
                        forceString(record.value('orgStructureName')),
                        forceString(record.value('namePerson')),
                        forceString(record.value('citizenship')),
                        hospDocumentLocation,
                        forceString(record.value('relegateOrg')),
                        forceString(record.value('codeFinance')),
                        '',
                        statusObservationName + u' (' + (statusObservationDate if statusObservationDate else u'') + u' ' + (statusObservationPerson if statusObservationPerson else u'') + u')',
                        statusObservationColor,
                        documentLocationColor,
                        colorFinance,
                        forceString(calcAge(forceDate(record.value('birthDate')), forceDate(record.value('endDate'))))
                        ]
                self.items.append(item)
                _dict = {
                        'observationCode': statusObservationCode,
                        'finance': nameFinance,
                        'contract': nameContract,
                        'bedCode': '',
                        'orgStructure': forceString(record.value('orgStructureName')),
                        'financeCode': forceString(record.value('codeFinance')),
                        'bedName': '',
                        'observationName': statusObservationName,
                        'observationColor': statusObservationColor
                    }
                self.itemByName[eventId] = _dict
        for col, order in self.headerSortingCol.items():
            self.sort(col, order)

    def sort(self, col, order=Qt.AscendingOrder):
        self.headerSortingCol = {col: order}
        reverse = order == Qt.DescendingOrder
        if col in [self.clientColumn, self.eventColumn]:
            self.items.sort(key=lambda x: forceInt(x[col]) if x else None, reverse=reverse)
        elif col in [self.birthDateCol, self.hospDateCol, self.receivedDateCol, self.planLeavedDateCol]:
            self.items.sort(key=lambda x: forceDateTime(x[col]) if x else None, reverse=reverse)
        else:
            self.items.sort(key=lambda x: forceString(x[col]).lower() if x else None, reverse=reverse)
        self.reset()


class CQueueModel(CMonitoringModel):
    column = [u'С', u'И', u'Номер', u'Код', u'Карта', u'ФИО', u'Пол', u'Дата рождения', u'Поставлен', u'Завершение планирования', u'Плановая дата госпитализации', u'Статус', u'Ожидание', u'MKB', u'Профиль', u'Подразделение', u'Ответственный', u'Гражданство', u'М', u'Направитель', u'Номер направления', u'Плановая дата госпитализации из АПУ', u'Порядок']
    statusObservationCol = 0
    financeCol = 1
    clientColumn = 2
    eventColumn = 3
    externalIdCol = 4
    defaultOrderCol = 5
    birthDateCol = 7
    hospDateCol = 8
    receivedDateCol = 9
    leavedDateCol = 10
    waitingCol = 12
    MKBColumn = 13
    profileCol = 14
    documentLocationCol = 18
    policlinicPlannedDateCol = 21
    orderDirectionCol = 22
    codeFinanceCol = 23
    statusObservationNameCol = 25
    colorStatusObservationCol = 26
    docLocalColorCol = 28
    colorFinanceCol = 29
    ageCol = 30
    planningActionIdCol = 31

    def __init__(self, parent):
        CMonitoringModel.__init__(self, parent)
        self.items = []
        self._cols = []
        self.itemByName = {}
        self.statusObservation = None

    def cols(self):
        self._cols = [CCol(u'Статус наблюдения',                   ['statusObservation'], 20, 'l'),
                      CCol(u'Код ИФ',                              ['nameFinance'], 20, 'l'),
                      CCol(u'Номер',                               ['client_id'], 20, 'l'),
                      CCol(u'Код события',                         ['event_id'], 20, 'l'),
                      CCol(u'Карта',                               ['externalId'], 20, 'l'),
                      CCol(u'ФИО',                                 ['lastName', 'firstName', 'patrName'], 30, 'l'),
                      CCol(u'Пол',                                 ['sex'], 15, 'l'),
                      CCol(u'Дата рождения',                       ['birthDate'], 20, 'l'),
                      CCol(u'Поставлен',                           ['begDate'], 20, 'l'),
                      CCol(u'Завершение планирования',             ['endDate'], 20, 'l'),
                      CCol(u'Плановая дата госпитализации',        ['plannedEndDate'], 20, 'l'),
                      CCol(u'Статус',                              ['status'], 20, 'l'),
                      CCol(u'Ожидание',                            ['plannedEndDate'], 20, 'l'),
                      CCol(u'MKB',                                 ['MKB'], 20, 'l'),
                      CCol(u'Профиль',                             ['profileName'], 30, 'l'),
                      CCol(u'Подразделение',                       ['nameOS'], 30, 'l'),
                      CCol(u'Ответственный',                       ['namePerson'], 30, 'l'),
                      CCol(u'Гражданство',                         ['citizenship'], 30, 'l'),
                      CCol(u'Место нахождения учетного документа', ['hospDocumentLocation'], 30, 'l'),
                      CCol(u'Направитель',                         ['relegateOrg'], 30, 'l'),
                      CCol(u'Номер направления',                   ['srcNumber'], 30, 'l'),
                      CCol(u'Плановая дата госпитализации из АПУ', ['policlinicPlannedDate'], 30, 'l'),
                      CCol(u'Порядок направления',                 ['orderDirection'], 30, 'l')
                      ]
        return self._cols

    def getExternalId(self, row):
        return self.items[row][self.externalIdCol]

    def getRelegateOrgId(self, row):
        return self.items[row][len(self.items[row])-6]

    def getRelegatePersonId(self, row):
        return self.items[row][len(self.items[row])-5]

    def getSrcDate(self, row):
        return self.items[row][len(self.items[row])-4]

    def getSrcNumber(self, row):
        return self.items[row][len(self.items[row])-3]

    def getDirectionDate(self, row):
        return self.items[row][len(self.items[row])-2]

    def getSetPersonId(self, row):
        return self.items[row][len(self.items[row])-1]

    def getMKB(self, row):
        return self.items[row][self.MKBColumn]
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return QVariant(self.column[section])
            elif role == Qt.ToolTipRole:
                if section == self.statusObservationCol:
                    return QVariant(u'Статус наблюдения пациента')
                elif section == self.financeCol:
                    return QVariant(u'Источник финансирования (код)')
                elif section == self.eventColumn:
                    return QVariant(u'Код события')
                elif section == self.documentLocationCol:
                    return QVariant(u'Место нахождения учетного документа')
                elif section == self.policlinicPlannedDateCol:
                    return QVariant(u'Плановая дата госпитализации поликлиники')
                elif section == self.orderDirectionCol:
                    return QVariant(u'Порядок направления')
        return QVariant()


    def getPlanningActionId(self, row):
        return self.items[row][self.planningActionIdCol]


    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if role == Qt.BackgroundColorRole:
            if column == self.statusObservationCol and self.items[row][column]:
                return toVariant(QtGui.QColor(self.items[row][self.colorStatusObservationCol]))
            elif column == self.financeCol:
                colorFinance = self.items[row][self.colorFinanceCol]
                if colorFinance:
                    return toVariant(colorFinance)
            elif column == self.documentLocationCol:
                docLocalColor = self.items[row][self.docLocalColorCol]
                if docLocalColor:
                    return toVariant(QtGui.QColor(docLocalColor))
        if role == Qt.DisplayRole:
            if column in [self.hospDateCol, self.receivedDateCol, self.leavedDateCol]:
                item = self.items[row]
                return toVariant(item[column].toString('dd.MM.yyyy'))
            elif column == self.birthDateCol:
                item = self.items[row]
                return toVariant(forceString(item[column]) + u' (' + item[self.ageCol] + u')')
            else:
                item = self.items[row]
            return toVariant(item[column])
        elif role == Qt.ToolTipRole:
            if column == self.statusObservationCol:
                item = self.items[row]
                if item[self.statusObservationCol]:
                    return QVariant(item[self.statusObservationCol] + u' ' + item[self.statusObservationNameCol])
                else:
                    return QVariant()
            elif column == self.financeCol:
                item = self.items[row]
                return QVariant(item[self.codeFinanceCol] + u' ' + item[column])
        return QVariant()

    def loadData(self, dialogParams):
        self.items = []
        self.itemByName = {}
        indexSex = dialogParams.get('indexSexPlaning', 0)
        ageFor = dialogParams.get('ageForPlaning', 0)
        ageTo = dialogParams.get('ageToPlaning', 150)
        order = dialogParams.get('order', -1)
        eventTypeId = dialogParams.get('eventTypeId', None)
        orgStructureId = dialogParams.get('orgStructureId', None)
        permanent = dialogParams.get('permanent', None)
        _type = dialogParams.get('type', None)
        profile = dialogParams.get('treatmentProfile', None)
        presenceDay = dialogParams.get('presenceDayPlaning', None)
        codeAttachType = dialogParams.get('codeAttachTypePlaning', None)
        finance = dialogParams.get('financePlaning', None)
        contractId = dialogParams.get('contractIdPlaning', None)
        personId = dialogParams.get('personIdPlaning', None)
        insurerId = dialogParams.get('insurerIdPlaning', None)
        regionSMO, regionTypeSMO, regionSMOCode = dialogParams.get('regionSMOPlaning', (False, 0, None))
        personExecId = dialogParams.get('personExecIdPlaning', None)
        quotingType = dialogParams.get('quotingTypePlaning', None)
        accountingSystemId = dialogParams.get('accountingSystemIdPlaning', None)
        filterClientId = dialogParams.get('filterClientIdPlaning', None)
        filterEventId = dialogParams.get('filterEventIdPlaning', None)
        isHospitalization = dialogParams.get('isHospitalization', 0)

        statusObservation = dialogParams.get('statusObservationPlaning', None)
        MKBFilter = dialogParams['MKBFilter']
        MKBFrom   = dialogParams['MKBFrom']
        MKBTo     = dialogParams['MKBTo']

        relegateOrg = dialogParams.get('relegateOrgPlaning', None)
        actionStatus = dialogParams.get('actionStatus', None)
        profileDirectionsId = dialogParams.get('profileDirectionsId', None)
        eventSrcNumber = dialogParams.get('eventSrcNumber', None)
        actionTypePlaningId = dialogParams.get('actionTypePlaningId', None)
        isNoPlannedEndDate = dialogParams.get('isNoPlannedEndDate', False)
        planActionBegDate  = dialogParams.get('planActionBegDate', None)
        planActionEndDate    = dialogParams.get('planActionEndDate', None)
        plannedBegDate         = dialogParams.get('plannedBegDate', None)
        plannedEndDate         = dialogParams.get('plannedEndDate', None)
        planWaitingBegDate     = dialogParams.get('planWaitingBegDate', None)
        planWaitingEndDate     = dialogParams.get('planWaitingEndDate', None)
        planBeforeOnsetBegDate = dialogParams.get('planBeforeOnsetBegDate', None)
        planBeforeOnsetEndDate = dialogParams.get('planBeforeOnsetEndDate', None)
        planExceedingDays      = dialogParams.get('planExceedingDays', None)

        self.statusObservation = statusObservation

        db = QtGui.qApp.db
        tableActionType = db.table('ActionType')
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        tableContract = db.table('Contract')
        tableClient = db.table('Client')
        tableClientPolicy = db.table('ClientPolicy')
        tableOrg = db.table('Organisation')
        tableRelegateOrg = db.table('Organisation').alias('relegateOrg')
        tablePWS = db.table('vrbPersonWithSpeciality')
        tableClientAttach = db.table('ClientAttach')
        tableRBAttachType = db.table('rbAttachType')
        tableOrgStruct = db.table('OrgStructure').alias('PersonOrgStructure')
        tableOrgStruct1 = db.table('OrgStructure').alias('Parent1')
        tableOrgStruct2 = db.table('OrgStructure').alias('Parent2')
        tableOrgStruct3 = db.table('OrgStructure').alias('Parent3')
        tableOrgStruct4 = db.table('OrgStructure').alias('Parent4')
        tableOrgStruct5 = db.table('OrgStructure').alias('Parent5')
        currentDate = QDate().currentDate()

        colsDirection = [tableEvent['relegateOrg_id'],
                        tableEvent['relegatePerson_id'],
                        tableEvent['srcDate'],
                        tableEvent['srcNumber'],
                        tableAction['directionDate'],
                        tableAction['setPerson_id'],
                        ]

        def getPlanning(orgStructureIdList, indexSex=0, ageFor=0, ageTo=150, permanent=None, type=None, profile=None,
                        presenceDay=None, codeAttachType=None, finance=None, noBeds=False, personId=None,
                        quotingTypeList=None, accountingSystemId=None, filterClientId=None, filterEventId=None,
                        personExecId=None, ageForCurDate=0, ageToCurDate=150):
            nameProperty = u'подразделение'
            groupBy = u''
            cols = [tableAction['id'].alias('planningActionId'),
                    tableEvent['id'].alias('eventId'),
                    tableEvent['client_id'],
                    tableEvent['externalId'],
                    tableClient['lastName'],
                    tableClient['firstName'],
                    tableClient['patrName'],
                    tableClient['sex'],
                    tableClient['birthDate'],
                    tableAction['begDate'],
                    tableAction['endDate'],
                    tableAction['directionDate'],
                    tableAction['plannedEndDate'],
                    tableAction['setPerson_id'],
                    tableAction['status'],
                    tablePWS['name'].alias('namePerson'),
                    tableRelegateOrg['id'].alias('relegateOrg_id'),
                    tableAction['MKB'].alias('ActionMKB')
                    ]
            cols.append(u"concat_ws(' | ', relegateOrg.infisCode, relegateOrg.shortName) as relegateOrgTitle")
            cols.append(u'''(SELECT ActionProperty_String.value FROM ActionProperty_String
                LEFT JOIN ActionProperty ON ActionProperty.id = ActionProperty_String.id
                LEFT JOIN ActionPropertyType ON ActionPropertyType.id = ActionProperty.type_id
                WHERE ActionProperty.action_id = Action.id AND ActionProperty.deleted = 0
                AND ActionPropertyType.name = 'Номер направления') as srcNumber''')
            cols.append(u'''(SELECT ActionProperty_String.value FROM ActionProperty_String
                            LEFT JOIN ActionProperty ON ActionProperty.id = ActionProperty_String.id
                            LEFT JOIN ActionPropertyType ON ActionPropertyType.id = ActionProperty.type_id
                            WHERE ActionProperty.action_id = Action.id AND ActionProperty.deleted = 0
                            AND ActionPropertyType.name = 'Порядок направления') as orderDirection''')
            cols.append(getMKB())
            cols.append(getOSHBP())
            cols.append(getDataOrgStructureName(nameProperty))
            cols.append(getStatusObservation())
            cols.append(getPropertyAPOS(u'Направлен в отделение', self.receivedActionTypeIdList))
            cols.append(getMovingActionForPlannedDate(self.movingActionTypeIdList))
            cols.append(getHospDocumentLocationInfo())
            cols.append("""getClientCitizenshipTitle(Client.id, Action.plannedEndDate) as citizenship""")
            cols.append(u'''(SELECT ActionProperty_Date.value FROM ActionProperty_Date
                                        LEFT JOIN ActionProperty ON ActionProperty.id = ActionProperty_Date.id
                                        LEFT JOIN Action AS ACT ON ACT.id = ActionProperty.action_id
                                        LEFT JOIN ActionPropertyType ON ActionPropertyType.id = ActionProperty.type_id
                                        WHERE ACT.id = Action.id AND ActionProperty.deleted = 0
                                        AND ActionPropertyType.name = 'Плановая дата госпитализации поликлиники') as policlinicPlannedDate''')
            queryTable = tableAction.leftJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
            queryTable = queryTable.leftJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.leftJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
            queryTable = queryTable.leftJoin(tablePWS, tablePWS['id'].eq(tableAction['person_id']))
            queryTable = queryTable.leftJoin(tableOrgStruct, tablePWS['orgStructure_id'].eq(tableOrgStruct['id']))
            queryTable = queryTable.leftJoin(tableOrgStruct1, tableOrgStruct['parent_id'].eq(tableOrgStruct1['id']))
            queryTable = queryTable.leftJoin(tableOrgStruct2, tableOrgStruct1['parent_id'].eq(tableOrgStruct2['id']))
            queryTable = queryTable.leftJoin(tableOrgStruct3, tableOrgStruct2['parent_id'].eq(tableOrgStruct3['id']))
            queryTable = queryTable.leftJoin(tableOrgStruct4, tableOrgStruct3['parent_id'].eq(tableOrgStruct4['id']))
            queryTable = queryTable.leftJoin(tableOrgStruct5, tableOrgStruct4['parent_id'].eq(tableOrgStruct5['id']))
            queryTable = queryTable.leftJoin(tableOrg, u"""Organisation.infisCode = COALESCE(
                                IF(LENGTH(PersonOrgStructure.bookkeeperCode) = 5, PersonOrgStructure.bookkeeperCode, NULL),
                                IF(LENGTH(Parent1.bookkeeperCode) = 5, Parent1.bookkeeperCode, NULL),
                                IF(LENGTH(Parent2.bookkeeperCode) = 5, Parent2.bookkeeperCode, NULL),
                                IF(LENGTH(Parent3.bookkeeperCode) = 5, Parent3.bookkeeperCode, NULL),
                                IF(LENGTH(Parent4.bookkeeperCode) = 5, Parent4.bookkeeperCode, NULL),
                                IF(LENGTH(Parent5.bookkeeperCode) = 5, Parent5.bookkeeperCode, NULL)
                            ) and Organisation.deleted = 0 and Organisation.isActive = 1 AND Organisation.isInsurer = 0""")
            queryTable = queryTable.leftJoin(tableRelegateOrg, 'relegateOrg.id = ifnull(Action.org_id, Organisation.id)')
            cond = [tableAction['actionType_id'].inlist(self.planningActionTypeIdList),
                    tableAction['deleted'].eq(0),
                    tableEvent['deleted'].eq(0),
                    tableClient['deleted'].eq(0)
                    ]
            tableEventType = db.table('EventType')
            queryTable = queryTable.leftJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))

            if planActionBegDate:
                cond.append(tableAction['begDate'].ge(planActionBegDate))
            if planActionEndDate:
                cond.append(tableAction['begDate'].lt(planActionEndDate.addDays(1)))
            if plannedBegDate:
                cond.append(tableAction['plannedEndDate'].ge(plannedBegDate))
            if plannedEndDate:
                cond.append(tableAction['plannedEndDate'].lt(plannedEndDate.addDays(1)))
            if planWaitingBegDate:
                cond.append(u'''ADDDATE(Action.begDate, %d) <= IFNULL(Action.endDate, CURDATE())''' % planWaitingBegDate)
            if planWaitingEndDate:
                cond.append(u'''ADDDATE(Action.begDate, %d) >= IFNULL(Action.endDate, CURDATE())''' % planWaitingEndDate)
            if planBeforeOnsetBegDate:
                cond.append(u'''Action.plannedEndDate IS NOT NULL AND ADDDATE(CURDATE(), %d) <= Action.plannedEndDate''' % planBeforeOnsetBegDate)
            if planBeforeOnsetEndDate:
                cond.append(u'''Action.plannedEndDate IS NOT NULL AND ADDDATE(CURDATE(), %d) >= Action.plannedEndDate''' % planBeforeOnsetEndDate)
            if planExceedingDays:
                cond.append(u'''(Action.plannedEndDate IS NOT NULL AND (DATE_ADD(Action.plannedEndDate, INTERVAL %d DAY) < CURDATE()))
                OR ((Action.begDate IS NOT NULL AND Action.plannedEndDate IS NULL) AND (DATE_ADD(Action.begDate, INTERVAL %d DAY) < CURDATE()))''' % (planExceedingDays, planExceedingDays))
            if isNoPlannedEndDate:
                cond.append(tableAction['plannedEndDate'].isNull())
            if actionStatus:
                cond.append(tableAction['status'].inlist(actionStatus))
            if profileDirectionsId > 0:
                cond.append(getPropertyHospitalBedProfile(u'Профиль койки', profileDirectionsId))
            elif profileDirectionsId == 0:
                groupBy = u'Action.id HAVING profileName is NULL'
            if eventSrcNumber:
                cond.append(u"""EXISTS (SELECT NULL FROM ActionProperty_String
                LEFT JOIN ActionProperty ON ActionProperty.id = ActionProperty_String.id
                LEFT JOIN Action AS ACT ON ACT.id = ActionProperty.action_id
                LEFT JOIN ActionPropertyType ON ActionPropertyType.id = ActionProperty.type_id
                WHERE ACT.id = Action.id AND ActionProperty.deleted = 0 AND ActionPropertyType.name = 'Номер направления' and ActionProperty_String.value = '{0}')""".format(eventSrcNumber))
            if actionTypePlaningId:
                cond.append(tableAction['actionType_id'].eq(actionTypePlaningId))
            if MKBFilter:
                cond.append(isMKB(MKBFrom, MKBTo))
            if order:
                cond.append(tableEvent['order'].eq(order))
            if eventTypeId:
                cond.append(tableEvent['eventType_id'].eq(eventTypeId))
            if personId:
                cond.append(tableAction['person_id'].eq(personId))
            if personExecId:
                cond.append(tableAction['person_id'].eq(personExecId))
            if self.statusObservation:
                cond.append(existsStatusObservation(self.statusObservation))
            if accountingSystemId and filterClientId:
                tableIdentification = db.table('ClientIdentification')
                queryTable = queryTable.leftJoin(tableIdentification, tableIdentification['client_id'].eq(tableClient['id']))
                cond.append(tableIdentification['accountingSystem_id'].eq(accountingSystemId))
                cond.append(tableIdentification['identifier'].eq(filterClientId))
                cond.append(tableIdentification['deleted'].eq(0))
            elif filterClientId:
                cond.append(tableClient['id'].eq(filterClientId))
            if filterEventId:
                cond.append(tableEvent['externalId'].eq(filterEventId))
            if relegateOrg:
                cond.append(tableRelegateOrg['id'].eq(relegateOrg))
            if finance:
                condFinance = u' AND ActionProperty_rbFinance.value = %d' % finance
            else:
                condFinance = u''
            cols.append(u'''(SELECT CONCAT_WS(' ', CONVERT(rbFinance.id,CHAR(11)), rbFinance.code, rbFinance.name)
                            FROM  ActionType AS AT
                                INNER JOIN Action AS A ON AT.id=A.actionType_id
                                INNER JOIN ActionPropertyType AS APT ON APT.actionType_id=AT.id
                                LEFT JOIN ActionProperty AS AP ON AP.type_id=APT.id AND AP.action_id = A.id
                                LEFT JOIN ActionProperty_rbFinance ON ActionProperty_rbFinance.id=AP.id
                                LEFT JOIN rbFinance ON rbFinance.id=ActionProperty_rbFinance.value
                            WHERE  A.deleted=0 AND AT.deleted=0 AND AP.deleted = 0 AND APT.deleted=0 AND A.id = Action.id AND APT.name = 'источник финансирования'%s) AS financeCodeName''' % condFinance)
            cols.append(getActionQueueClientPolicyForDate())
            if forceInt(codeAttachType) > 0:
                cond.append(tableRBAttachType['code'].eq(codeAttachType))
                queryTable = queryTable.leftJoin(tableClientAttach, tableClient['id'].eq(tableClientAttach['client_id']))
                queryTable = queryTable.leftJoin(tableRBAttachType, tableClientAttach['attachType_id'].eq(tableRBAttachType['id']))
            if indexSex > 0:
                cond.append(tableClient['sex'].eq(indexSex))
            if ageFor <= ageTo and not (ageFor == 0 and ageTo == 150):
                cond.append(getAgeRangeCond(ageFor, ageTo))
            if orgStructureIdList:
                cond.append(db.joinOr([getDataOrgStructure(nameProperty, orgStructureIdList, False), 'NOT %s' % (getActionPropertyTypeName(nameProperty))]))
            if quotingTypeList:
                quotingTypeIdList, quotingTypeClass = quotingTypeList
                if quotingTypeClass is not None:
                    cond.append(getDataClientQuoting(u'Квота', quotingTypeIdList))
            if profile:
                cond.append(getHospitalBedProfile(profile))
            if insurerId or regionSMO:
                tableRBFinance = db.table('rbFinance')
                tableRBFinanceBC = db.table('rbFinance').alias('rbFinanceByContract')
                if QtGui.qApp.defaultHospitalBedFinanceByMoving() == 2:
                    cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.code, IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinanceByContract.code, NULL)) AS codeFinance')
                    cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.name, IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinanceByContract.name, NULL)) AS nameFinance')
                    cols.append(getClientPolicyForDate())
                    if finance:
                        cond.append('''((Action.finance_id IS NOT NULL AND Action.deleted=0 AND Action.finance_id = %s) OR (Contract.id IS NOT NULL AND Contract.deleted=0 AND Contract.finance_id = %s))''' % (str(finance), str(finance)))
                        queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
                        queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                        queryTable = queryTable.leftJoin(tableRBFinanceBC, tableRBFinanceBC['id'].eq(tableContract['finance_id']))
                    else:
                        queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
                        queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                        queryTable = queryTable.leftJoin(tableRBFinanceBC, tableRBFinanceBC['id'].eq(tableContract['finance_id']))
                elif QtGui.qApp.defaultHospitalBedFinanceByMoving() == 1:
                    cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.code, NULL) AS codeFinance')
                    cols.append(u'IF(Action.finance_id IS NOT NULL AND Action.deleted=0, rbFinance.name, NULL) AS nameFinance')
                    cols.append(getActionClientPolicyForDate())
                    queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    if finance:
                        cond.append('''(Action.finance_id IS NOT NULL AND Action.deleted=0 AND Action.finance_id = %s)''' % (str(finance)))
                        queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
                    else:
                        queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableAction['finance_id']))
                else:
                    cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.code, NULL) AS codeFinance')
                    cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.name, NULL) AS nameFinance')
                    cols.append(getContractClientPolicyForDate())
                    if finance:
                        cond.append(tableContract['deleted'].eq(0))
                        cond.append(tableRBFinance['id'].eq(finance))
                        queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                        queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
                    else:
                        queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                        queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
                cond.append('(Contract.id IS NOT NULL AND Contract.deleted=0) OR (Contract.id IS NULL)')
                queryTable = queryTable.leftJoin(tableClientPolicy,
                                                  u'''(ClientPolicy.id = getClientPolicyIdForDate(Client.id, IF(Contract.id IS NOT NULL AND Contract.deleted=0, IF(rbFinance.code = 2, 1, IF(rbFinance.code = 3, 0, 1)), 1), IF(Event.execDate IS NOT NULL, Event.execDate, Event.setDate), Event.id))''')
                if not regionSMO:
                    cond.append(tableClientPolicy['insurer_id'].eq(insurerId))
                else:
                    tableOrganisation = db.table('Organisation').alias('Org_Area')
                    queryTable = queryTable.leftJoin(tableOrganisation, [tableOrganisation['id'].eq(tableClientPolicy['insurer_id']), tableOrganisation['deleted'].eq(0)])
                    if regionSMOCode:
                        if regionTypeSMO:
                            cond.append(tableOrganisation['area'].notlike(regionSMOCode))
                        else:
                            cond.append(tableOrganisation['area'].like(regionSMOCode))
            if contractId:
                cond.append(isContractPropertyValue(u'Договор', contractId))
            if isHospitalization == 1:
                cond.append(isPlanningToHospitalization())
            elif isHospitalization == 2:
                cond.append(u'NOT %s' % (isPlanningToHospitalization()))
            cols.extend(colsDirection)
            recordsList = db.getRecordListGroupBy(queryTable, cols, cond, groupBy)
            return recordsList

        orgStructureIdList = []
        if orgStructureId:
            treeItem = orgStructureId.internalPointer() if orgStructureId.isValid() else None
            orgStructureIdList = self.getOrgStructureIdList(orgStructureId) if treeItem and treeItem._id else []
        if quotingType:
            quotingTypeClass, quotingTypeId = quotingType
            quotingTypeList = self.getQuotingTypeIdList(quotingType)
        else:
            quotingTypeClass = None
            quotingTypeList = None

        records = getPlanning(orgStructureIdList, indexSex, ageFor, ageTo, permanent, type, profile, presenceDay, codeAttachType, finance, False, personId, (quotingTypeList, quotingTypeClass), accountingSystemId, filterClientId, filterEventId, personExecId)
        for record in records:
            financeCodeName = forceString(record.value('financeCodeName')).split(" ")
            if len(financeCodeName) >= 2:
                idFinance = forceRef(financeCodeName[0]) if len(financeCodeName) >= 1 else 0
                nameFinance = forceString(financeCodeName[2]) if len(financeCodeName) >= 3 else u''
                codeFinance = forceString(financeCodeName[1]) if len(financeCodeName) >= 3 else u''
            else:
                idFinance = 0
                nameFinance = u''
                codeFinance = u''
            if not finance or (finance and finance == forceInt(idFinance)):
                begDateAction = forceDate(record.value('begDate'))
                endDateAction = forceDate(record.value('endDate'))
                waitingDays = begDateAction.daysTo(endDateAction) if endDateAction else begDateAction.daysTo(currentDate)
                statusObservation = forceString(record.value('statusObservation')).split('|')
                statusObservationCode = forceString(statusObservation[0]) if len(statusObservation) >= 1 else u''
                statusObservationName = forceString(statusObservation[1]) if len(statusObservation) >= 2 else u''
                statusObservationColor = forceString(statusObservation[2]) if len(statusObservation) >= 3 else u''
                statusObservationDate = forceString(statusObservation[3]) if len(statusObservation) >= 4 else u''
                statusObservationPerson = forceString(statusObservation[4]) if len(statusObservation) >= 5 else u''
                policyEndDate = forceDate(record.value('policyEndDate'))
                colorFinance = None
                if policyEndDate:
                    if begDateAction < policyEndDate <= begDateAction.addDays(3):
                       colorFinance = QtGui.QColor(Qt.yellow)
                    elif begDateAction >= policyEndDate:
                        colorFinance = QtGui.QColor(Qt.red)
                documentLocationInfo  = forceString(record.value('documentLocationInfo')).split("  ")
                hospDocumentLocation  = forceString(documentLocationInfo[0]) if len(documentLocationInfo) >= 1 else ''
                documentLocationColor = forceString(documentLocationInfo[1]) if len(documentLocationInfo) > 1 else ''
                itemDirection = [
                                    forceRef(record.value('relegateOrg_id')),
                                    forceRef(record.value('setPerson_id')),
                                    forceDate(record.value('directionDate')),
                                    forceString(record.value('srcNumber')),
                                    forceDate(record.value('directionDate')),
                                    forceRef(record.value('setPerson_id')),
                                ]
                item = [statusObservationCode,
                        nameFinance,
                        forceRef(record.value('client_id')),
                        forceRef(record.value('eventId')),
                        forceString(record.value('externalId')),
                        forceString(record.value('lastName')) + u' ' + forceString(record.value('firstName')) + u' ' + forceString(record.value('patrName')),
                        self.sex[forceInt(record.value('sex'))],
                        forceDate(record.value('birthDate')),
                        begDateAction,
                        endDateAction,
                        forceDate(record.value('plannedEndDate')),
                        CActionStatus.names[forceInt(record.value('status'))],
                        waitingDays,
                        forceString(record.value('MKB')) if forceString(record.value('MKB')) else forceString(record.value('ActionMKB')),
                        forceString(record.value('profileName')),
                        forceString(record.value('nameOrgStructure')),
                        forceString(record.value('namePerson')),
                        forceString(record.value('citizenship')),
                        hospDocumentLocation,
                        forceString(record.value('relegateOrgTitle')),
                        forceString(record.value('srcNumber')),
                        forceDate(record.value('policlinicPlannedDate')),
                        forceString(record.value('orderDirection')),
                        codeFinance,
                        forceBool(record.value('APOS_value')),
                        statusObservationName + u' (' + (statusObservationDate if statusObservationDate else u'') + u' ' + (statusObservationPerson if statusObservationPerson else u'') + u')',
                        statusObservationColor,
                        forceRef(record.value('movingActionId')),
                        documentLocationColor,
                        colorFinance,
                        forceString(calcAge(forceDate(record.value('birthDate')), None)),
                        forceRef(record.value('planningActionId'))
                        ]

                item.extend(itemDirection)
                self.items.append(item)
                eventId = forceRef(record.value('eventId'))
                _dict = {
                        'observationCode': statusObservationCode,
                        'finance': nameFinance,
                        'bedCode': '',
                        'orgStructure': forceString(record.value('nameOrgStructure')),
                        'bedName': '',
                        'waitingDays': waitingDays,
                        'begDate': CDateInfo(begDateAction),
                        'plannedBegDate': CDateInfo(forceDate(record.value('plannedEndDate'))),
                        'observationName': statusObservationName,
                        'observationColor': statusObservationColor
                    }
                self.itemByName[eventId] = _dict
        for col, order in self.headerSortingCol.items():
            self.sort(col, order)

    def sort(self, col, order=Qt.AscendingOrder):
        self.headerSortingCol = {col: order}
        reverse = order == Qt.DescendingOrder
        if col in [self.clientColumn, self.eventColumn, self.waitingCol]:
            self.items.sort(key=lambda x: forceInt(x[col]) if x else None, reverse=reverse)
        elif col in [self.birthDateCol, self.hospDateCol, self.receivedDateCol, self.leavedDateCol, self.policlinicPlannedDateCol]:
            self.items.sort(key=lambda x: forceDateTime(x[col]) if x else None, reverse=reverse)
        else:
            self.items.sort(key=lambda x: forceString(x[col]).lower() if x else None, reverse=reverse)
        self.reset()


class CSmpCallStatus:
    names = (u'Не госпитализирован', # 0
             u'Госпитализирован',    # 1
             u'Отменен',             # 2
            )
    notHospitalized = 0
    hospitalized    = 1
    canceled        = 2


class CEmergencyModel(CMonitoringModel):
    column = [u'Номер', u'ФИО', u'Пол', u'Дата рождения', u'Дата вызова', u'Дата госпитализации', u'МКБ', u'Повод вызова', u'Адрес вызова', u'Номер вызова', u'Госпитализирован', u'Вызов завершен']
    smpSex = [u'М', u'Ж']
    CEmergencyRecord = namedtuple('CEmergencyRecord', [
        'smpItemId',
        'personFullName',
        'personSex',
        'personBirthDateText',
        'callDateTime',
        'hospitalizationDate',
        'mkb',
        'callOccasion',
        'addressCall',
        'idCallNumber',
        'hospitalizationEventId',
        'isFinish',
        'clientId',
        'personLastName',
        'personName',
        'personPatronymic',
        'personBirthDate',
        'personAge',
        'team',
        'mkbSub',
        'urgencyCategory',
        'callNumber',
        'renderedAid',
        'medicmtAid',
        'anamnesis',
        'patientTransferWay',
        'temperatureBefore',
        'arterialPressureBefore',
        'pulseBefore',
        'heartRateBefore',
        'temperatureAfter',
        'arterialPressureAfter',
        'pulseAfter',
        'heartRateAfter',
        'realHospitalizationEventId',
    ])

    def __init__(self, parent):
        CMonitoringModel.__init__(self, parent)
        self.items = []
        self._cols = []
        self.headerSortingCol = {}

    def cols(self):
        self._cols = [
                      CCol(u'Номер',               [], 20, 'l'),
                      CCol(u'ФИО',                 [], 30, 'l'),
                      CCol(u'Пол',                 [], 15, 'l'),
                      CCol(u'Дата рождения',       [], 20, 'l'),
                      CCol(u'Дата вызова',         [], 20, 'l'),
                      CCol(u'Дата госпитализации', [], 20, 'l'),
                      CCol(u'МКБ',                 [], 20, 'l'),
                      CCol(u'Повод вызова',        [], 30, 'l'),
                      CCol(u'Адрес вызова',        [], 20, 'l'),
                      CCol(u'Номер вызова',        [], 20, 'l'),
                      CCol(u'Госпитализирован',    [], 20, 'l'),
                      CCol(u'Вызов завершен',      [], 20, 'c'),
                      ]
        return self._cols


    def getClientId(self, row):
        return self.items[row].clientId


    def getEventId(self, row):
        return self.items[row].realHospitalizationEventId


    def getSmpItemId(self, row):
        return self.items[row].smpItemId

    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return QVariant(self.column[section])
        return QVariant()


    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if role == Qt.DisplayRole:
            item = self.items[row]
            return toVariant(item[column])
        return QVariant()
    
    def getInitialSmpItems(self):
        db = QtGui.qApp.db
        tableSmpItem = db.table('smp_stacItem')
        self.numNewRequests = 0
        self.numFinishedRequests = 0
        self.numCanceledRequests = 0
        self.actualSmpItemIds = db.getIdList(tableSmpItem, where=tableSmpItem['isActual'].eq(1))
    
    def checkNewSmpItems(self):
        db = QtGui.qApp.db
        tableSmpItem = db.table('smp_stacItem')
        self.numNewRequests = db.getCount(
            tableSmpItem,
            where=db.joinAnd([
                tableSmpItem['isActual'].eq(1),
                tableSmpItem['id'].notInlist(self.actualSmpItemIds)
            ])
        )
        self.numFinishedRequests = db.getCount(
            tableSmpItem,
            where=db.joinAnd([
                tableSmpItem['isFinish'].eq(1),
                tableSmpItem['isCanceled'].eq(0),
                tableSmpItem['id'].inlist(self.actualSmpItemIds)
            ])
        )
        self.numCanceledRequests = db.getCount(
            tableSmpItem,
            where=db.joinAnd([
                tableSmpItem['isCanceled'].eq(1),
                tableSmpItem['id'].inlist(self.actualSmpItemIds)
            ])
        )

    def loadData(self, dialogParams):
        self.items = []
        self.itemByName = {}
        self.getInitialSmpItems()
        idCallNumber = dialogParams.get('idCallNumber', None)
        smpCallDateFrom  = dialogParams.get('smpCallDateFrom', None)
        smpCallDateTo    = dialogParams.get('smpCallDateTo', None)
        hospitalizationDateFrom  = dialogParams.get('hospitalizationDateFrom', None)
        hospitalizationDateTo    = dialogParams.get('hospitalizationDateTo', None)
        smpCallStatus = dialogParams.get('smpCallStatus', None)

        db = QtGui.qApp.db
        tableSmpItem = db.table('smp_stacItem')
        tableSmpInfo = db.table('smp_stacInfo')
        tableHospitalizationEvent = db.table('Event').alias('HospitalizationEvent')
        tableHospitalizationEventType = db.table('EventType').alias('HospitalizationEventType')
        tableHospitalizationEventMedicalAidType = db.table('rbMedicalAidType').alias('HospitalizationEventMedicalAidType')
        currentDate = QDate().currentDate()

        def getOrderBy():
            orderBY = u'smp_stacItem.id ASC'
            for key, value in self.headerSortingCol.items():
                if value:
                    ASC = u'ASC'
                else:
                    ASC = u'DESC'
                if key == 0:
                    orderBY = u'smp_stacItem.id %s' % ASC
                elif key == 1:
                    orderBY = u'smp_stacInfo.personLastName %s' % ASC
                elif key == 2:
                    orderBY = u'smp_stacInfo.personSex %s' % ASC
                elif key == 3:
                    orderBY = u'smp_stacInfo.personBirthDate %s' % ASC
                elif key == 4:
                    orderBY = u'smp_stacInfo.callDateTime %s' % ASC
                elif key == 5:
                    orderBY = u'HospitalizationEvent.setDate %s' % ASC
                elif key == 6:
                    orderBY = u'smp_stacInfo.mkb %s' % ASC
                elif key == 7:
                    orderBY = u'smp_stacInfo.callOccasion %s' % ASC
                elif key == 8:
                    orderBY = u'smp_stacInfo.addressCall %s' % ASC
                elif key == 9:
                    orderBY = u'smp_stacItem.idCallNumber %s' % ASC
                elif key == 10:
                    orderBY = u'HospitalizationEvent.id %s' % ASC
                elif key == 11:
                    orderBY = u'smp_stacItem.isFinish %s' % ASC
            return orderBY

        def getEmergency():
            groupBy = u''
            cols = [tableSmpItem['id'].alias('smpItem_id'),
                    tableSmpInfo['personLastName'],
                    tableSmpInfo['personName'],
                    tableSmpInfo['personPatronymic'],
                    tableSmpInfo['personSex'],
                    tableSmpInfo['personBirthDate'],
                    tableSmpInfo['callDateTime'],
                    tableHospitalizationEvent['setDate'].alias('hospitalizationDate'),
                    tableSmpInfo['mkb'],
                    tableSmpInfo['callOccasion'],
                    tableSmpInfo['addressCall'],
                    tableSmpItem['idCallNumber'],
                    tableHospitalizationEvent['id'].alias('hospitalizationEvent_id'),
                    tableHospitalizationEventMedicalAidType['regionalCode'].alias('hospitalizationEventMedicalAidTypeCode'),
                    tableSmpItem['isFinish'],
                    tableHospitalizationEvent['client_id'],
                    tableSmpInfo['personLastName'],
                    tableSmpInfo['personName'],
                    tableSmpInfo['personPatronymic'],
                    tableSmpInfo['personAge'],
                    tableSmpInfo['team'],
                    tableSmpInfo['mkbSub'],
                    tableSmpInfo['urgencyCategory'],
                    tableSmpInfo['callNumber'],
                    tableSmpInfo['renderedAid'],
                    tableSmpInfo['medicmtAid'],
                    tableSmpInfo['anamnesis'],
                    tableSmpInfo['patientTransferWay'],
                    tableSmpInfo['temperatureBefore'],
                    tableSmpInfo['arterialPressureBefore'],
                    tableSmpInfo['pulseBefore'],
                    tableSmpInfo['heartRateBefore'],
                    tableSmpInfo['temperatureAfter'],
                    tableSmpInfo['arterialPressureAfter'],
                    tableSmpInfo['pulseAfter'],
                    tableSmpInfo['heartRateAfter'],
                    ]
            queryTable = tableSmpItem.innerJoin(tableSmpInfo, tableSmpInfo['idCallNumber'].eq(tableSmpItem['idCallNumber']))
            queryTable = queryTable.leftJoin(tableHospitalizationEvent, db.joinAnd([
                tableHospitalizationEvent['id'].eq(tableSmpItem['hospitalizationEvent_id']),
                tableHospitalizationEvent['deleted'].eq(0)
            ]))
            queryTable = queryTable.leftJoin(tableHospitalizationEventType, db.joinAnd([
                tableHospitalizationEventType['id'].eq(tableHospitalizationEvent['eventType_id']),
                tableHospitalizationEventType['deleted'].eq(0)
            ]))
            queryTable = queryTable.leftJoin(tableHospitalizationEventMedicalAidType, tableHospitalizationEventMedicalAidType['id'].eq(tableHospitalizationEventType['medicalAidType_id']))

            cond = []
            if smpCallDateFrom:
                cond.append(tableSmpInfo['callDateTime'].dateGe(smpCallDateFrom))
            if smpCallDateTo:
                cond.append(tableSmpInfo['callDateTime'].dateLe(smpCallDateTo))
            if hospitalizationDateFrom:
                cond.append(tableHospitalizationEvent['setDate'].dateGe(hospitalizationDateFrom))
            if hospitalizationDateTo:
                cond.append(tableHospitalizationEvent['setDate'].dateLe(hospitalizationDateTo))
            if idCallNumber:
                cond.append(tableSmpItem['idCallNumber'].eq(idCallNumber))
            if smpCallStatus:
                statusCond = []
                if CSmpCallStatus.notHospitalized in smpCallStatus:
                    statusCond.append(db.joinAnd([
                        tableSmpItem['hospitalizationEvent_id'].isNull(),
                        tableSmpItem['isCanceled'].eq(0)
                    ]))
                if CSmpCallStatus.hospitalized in smpCallStatus:
                    statusCond.append(db.joinAnd([
                        tableSmpItem['hospitalizationEvent_id'].isNotNull(),
                        tableSmpItem['isCanceled'].eq(0)
                    ]))
                if CSmpCallStatus.canceled in smpCallStatus:
                    statusCond.append(tableSmpItem['isCanceled'].eq(1))
                cond.append(db.joinOr(statusCond))
            orderBy = getOrderBy()
            records = db.getRecordListGroupBy(queryTable, cols, cond, groupBy, orderBy)
            return records

        records = getEmergency()
        for record in records:
            hospitalizationEventMedicalAidTypeCode = forceString(record.value('hospitalizationEventMedicalAidTypeCode'))
            hospitalizationEventId = forceRef(record.value('hospitalizationEvent_id')) if hospitalizationEventMedicalAidTypeCode not in ['111', '112'] else None
            personBirthDate = forceDate(record.value('personBirthDate'))
            personAge = forceString(record.value('personAge'))
            if personBirthDate.isValid():
                personBirthDateText = forceString(personBirthDate) + u' (' + calcAge(personBirthDate) + u')'
            else:
                personBirthDateText = u'Не указана'
                if personAge:
                    personBirthDateText += u' (%s)' % personAge
            item = self.CEmergencyRecord(
                # поля в колонках таблицы
                smpItemId = forceRef(record.value('smpItem_id')),
                personFullName = forceString(record.value('personLastName')) + u' ' + forceString(record.value('personName')) + u' ' + forceString(record.value('personPatronymic')),
                personSex = u'' if record.isNull('personSex') else self.smpSex[forceInt(record.value('personSex'))],
                personBirthDateText = personBirthDateText,
                callDateTime = forceDateTime(record.value('callDateTime')),
                hospitalizationDate = forceDateTime(record.value('hospitalizationDate')),
                mkb = forceString(record.value('mkb')),
                callOccasion = forceString(record.value('callOccasion')),
                addressCall = forceString(record.value('addressCall')),
                idCallNumber = forceString(record.value('idCallNumber')),
                hospitalizationEventId = hospitalizationEventId,
                isFinish = u'Да' if forceBool(record.value('isFinish')) else u'Нет',
                # прочие поля
                clientId = forceRef(record.value('clientId')),
                personLastName = forceString(record.value('personLastName')),
                personName = forceString(record.value('personName')),
                personPatronymic = forceString(record.value('personPatronymic')),
                personBirthDate = personBirthDate,
                personAge = personAge,
                team = forceString(record.value('team')),
                mkbSub = forceString(record.value('mkbSub')),
                urgencyCategory = forceString(record.value('urgencyCategory')),
                callNumber = forceString(record.value('callNumber')),
                renderedAid = forceString(record.value('renderedAid')),
                medicmtAid = forceString(record.value('medicmtAid')),
                anamnesis = forceString(record.value('anamnesis')),
                patientTransferWay = forceString(record.value('patientTransferWay')),
                temperatureBefore = forceDouble(record.value('temperatureBefore')),
                arterialPressureBefore = forceString(record.value('arterialPressureBefore')),
                pulseBefore = forceInt(record.value('pulseBefore')),
                heartRateBefore = forceInt(record.value('heartRateBefore')),
                temperatureAfter = forceDouble(record.value('temperatureAfter')),
                arterialPressureAfter = forceString(record.value('arterialPressureAfter')),
                pulseAfter = forceInt(record.value('pulseAfter')),
                heartRateAfter = forceInt(record.value('heartRateAfter')),
                realHospitalizationEventId = forceRef(record.value('hospitalizationEvent_id')),
            )
            self.items.append(item)
        self.reset()

    def getInfoText(self, row):
        def formatField(name, value):
            if value is None or len(forceString(value).strip()) == 0:
                return u''
            else:
                return u'<div><b>%s:</b> %s</div>' % (name, forceString(value))
        record = self.items[row]
        text = u'''<style> 
            .header {
                font: bold large; 
                margin-bottom: 5px; 
                margin-left: 20px;
            }
            </style>'''
        text += u'<div class="header">Пациент</div>'
        text += formatField(u'Фамилия', record.personLastName)
        text += formatField(u'Имя', record.personName)
        text += formatField(u'Отчество', record.personPatronymic)
        text += formatField(u'Пол', record.personSex)
        text += formatField(u'Возраст', record.personAge)
        text += u'<hr>'

        text += u'<div class="header">Вызов</div>'
        text += formatField(u'Дата и время вызова', record.callDateTime)
        text += formatField(u'Бригада СМП', record.team)
        text += formatField(u'Диагноз СМП', record.mkb)
        text += formatField(u'Сопутствующий диагноз СМП', record.mkbSub)
        text += formatField(u'Повод вызова', record.callOccasion)
        text += formatField(u'Срочность вызова', record.urgencyCategory)
        text += formatField(u'Адрес вызова', record.addressCall)
        text += formatField(u'Идентификатор вызова', record.idCallNumber)
        text += formatField(u'Номер вызова', record.callNumber)
        text += formatField(u'Оказанная помощь', record.renderedAid)
        text += formatField(u'Медикаменты', record.medicmtAid)
        text += u'<hr>'
        
        text += u'<div class="header">Сигнальный лист</div>'
        text += formatField(u'Анамнез', record.anamnesis)
        text += formatField(u'Способ доставки', record.patientTransferWay)
        measurementsBefore = []
        if record.temperatureBefore > 0:
            measurementsBefore.append(u'<br>- температура: %.2f' % record.temperatureBefore)
        if record.arterialPressureBefore:
            measurementsBefore.append(u'<br>- давление: %s' % record.arterialPressureBefore)
        if record.pulseBefore > 0:
            measurementsBefore.append(u'<br>- пульс: %d' % record.pulseBefore)
        if record.heartRateBefore > 0:
            measurementsBefore.append(u'<br>- ЧСС: %d' % record.heartRateBefore)
        if measurementsBefore:
            text += formatField(u'До оказания помощи', u''.join(measurementsBefore))
        measurementsAfter = []
        if record.temperatureAfter > 0:
            measurementsAfter.append(u'<br>- температура: %.2f' % record.temperatureAfter)
        if record.arterialPressureAfter:
            measurementsAfter.append(u'<br>- давление: %s' % record.arterialPressureAfter)
        if record.pulseAfter > 0:
            measurementsAfter.append(u'<br>- пульс: %d' % record.pulseAfter)
        if record.heartRateAfter > 0:
            measurementsAfter.append(u'<br>- ЧСС: %d' % record.heartRateAfter)
        if measurementsAfter:
            text += formatField(u'После оказания помощи', u''.join(measurementsAfter))
        text += u'<hr>'
        return text


class CRenunciationModel(CMonitoringModel):
    column = [u'С', u'И', u'Д', u'Номер', u'Код', u'Карта', u'ФИО', u'Пол', u'Дата рождения', u'Госпитализирован', u'Выбыл', u'Причина отказа', u'МЭС', u'MKB', u'Профиль', u'Подразделение', u'Лечащий врач', u'Гражданство', u'М']
    statusObservationCol = 0
    financeCol = 1
    clientColumn = 3
    eventColumn = 4
    defaultOrderCol = 6
    birthDateCol = 8
    receivedDateCol = 9
    leavedDateCol = 10
    MKBColumn = 13
    profileCol = 14
    documentLocationCol = 18
    codeFinanceCol = 19
    bedNameCol = 20
    statusObservationNameCol = 21
    colorStatusObservationCol = 22
    docLocalColorCol = 23
    colorFinanceCol = 24
    ageCol = 25

    def __init__(self, parent):
        CMonitoringModel.__init__(self, parent)
        self.items = []
        self._cols = []
        self.itemByName = {}
        self.indexModel = 0
        self.statusObservation = None


    def cols(self):
        self._cols = [CCol(u'Статус наблюдения',     ['statusObservation'], 20, 'l'),
                      CCol(u'Код ИФ',                ['nameFinance'], 20, 'l'),
                      CCol(u'Договор',               ['numberContract'], 20, 'l'),
                      CCol(u'Номер',                 ['client_id'], 20, 'l'),
                      CCol(u'Код события',                         ['event_id'], 20, 'l'),
                      CCol(u'Карта',                 ['externalId'], 20, 'l'),
                      CCol(u'ФИО',                   ['lastName', 'firstName', 'patrName'], 30, 'l'),
                      CCol(u'Пол',                   ['sex'], 15, 'l'),
                      CCol(u'Дата рождения',         ['birthDate'], 20, 'l'),
                      CCol(u'Поступил',              ['begDate'], 20, 'l') if self.indexModel else CCol(u'Госпитализирован', ['begDate'], 20, 'l'),
                      CCol(u'Выбыл',                 ['endDate'], 20, 'l'),
                      CCol(u'Причина отказа',        ['nameRenunciate'], 20, 'l'),
                      CCol(u'МЭС',                   ['mes'], 20, 'l'),
                      CCol(u'MKB',                   ['MKB'], 20, 'l'),
                      CCol(u'Профиль',                 ['profileName'], 30, 'l'),
                      CCol(u'Подразделение',         ['nameOS'], 30, 'l'),
                      CCol(u'Лечащий врач',         ['namePerson'], 30, 'l'),
                      CCol(u'Гражданство',           ['citizenship'], 30, 'l'),
                      CCol(u'Место нахождения учетного документа',['hospDocumentLocation'], 30, 'l')
                      ]
        return self._cols

    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if role == Qt.DisplayRole:
            if column in [self.receivedDateCol, self.leavedDateCol]:
                item = self.items[row]
                return toVariant(item[column].toString('dd.MM.yyyy hh:mm'))
            elif column == self.birthDateCol:
                item = self.items[row]
                return toVariant(forceString(item[column]) + u' (' + item[self.ageCol] + u')')
            else:
                item = self.items[row]
            return toVariant(item[column])
        elif role == Qt.ToolTipRole:
            if column == self.statusObservationCol:
                item = self.items[row]
                if item[self.statusObservationCol]:
                    return QVariant(item[self.statusObservationCol] + u' ' + item[self.statusObservationNameCol])
                else:
                    return QVariant()
            elif column == self.financeCol:
                item = self.items[row]
                return QVariant(item[self.codeFinanceCol] + u' ' + item[column])
        elif role == Qt.BackgroundColorRole:
            if column == self.statusObservationCol and self.items[row][column]:
                return toVariant(QtGui.QColor(self.items[row][self.colorStatusObservationCol]))
            elif column == self.financeCol:
                colorFinance = self.items[row][self.colorFinanceCol]
                if colorFinance:
                    return toVariant(colorFinance)
            elif column == self.documentLocationCol:
                docLocalColor = self.items[row][self.docLocalColorCol]
                if docLocalColor:
                    return toVariant(QtGui.QColor(docLocalColor))
        return QVariant()

    def loadData(self, dialogParams):
        self.items = []
        self.itemByName = {}
        filterBegDate = dialogParams.get('filterBegDate', None)
        filterEndDate = dialogParams.get('filterEndDate', None)
        filterBegTime = dialogParams.get('filterBegTime', None)
        filterEndTime = dialogParams.get('filterEndTime', None)
        if not filterBegTime.isNull():
            begDateTime = QDateTime(filterBegDate, filterBegTime)
            filterBegDate = begDateTime
        if not filterEndTime.isNull():
            endDateTime = QDateTime(filterEndDate, filterEndTime)
            filterEndDate = endDateTime
        indexSex = dialogParams.get('indexSex', 0)
        ageFor = dialogParams.get('ageFor', 0)
        ageTo = dialogParams.get('ageTo', 150)
        order = dialogParams.get('order', -1)
        eventTypeId = dialogParams.get('eventTypeId', None)
        orgStructureId = dialogParams.get('orgStructureId', None)
        profile = dialogParams.get('treatmentProfile', None)
        codeAttachType = dialogParams.get('codeAttachType', None)
        finance = dialogParams.get('finance', None)
        contractId = dialogParams.get('contractId', None)
        personId = dialogParams.get('personId', None)
        insurerId = dialogParams.get('insurerId', None)
        regionSMO, regionTypeSMO, regionSMOCode = dialogParams.get('regionSMO', (False, 0, None))
        personExecId = dialogParams.get('personExecId', None)
        quotingType = dialogParams.get('quotingType', None)
        accountingSystemId = dialogParams.get('accountingSystemId', None)
        filterClientId = dialogParams.get('filterClientId', None)
        filterEventId = dialogParams.get('filterEventId', None)
        statusObservation = dialogParams.get('statusObservation', None)
        reason = dialogParams.get('reason', None)
        index = dialogParams.get('renunciationActionIndex', 0)
        deliverBy = dialogParams.get('deliverBy', None)
        filterMES = dialogParams.get('filterMES', u'')
        MKBFilter = dialogParams['MKBFilter']
        MKBFrom   = dialogParams['MKBFrom']
        MKBTo     = dialogParams['MKBTo']
        self.statusObservation = statusObservation
        self.indexModel = index

        db = QtGui.qApp.db
        tableAPT = db.table('ActionPropertyType')
        tableAP = db.table('ActionProperty')
        tableActionType = db.table('ActionType')
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        tableMes = db.table('mes.MES')
        tableClient = db.table('Client')
        tableClientPolicy = db.table('ClientPolicy')
        tablePWS = db.table('vrbPersonWithSpeciality')
        tableAPS = db.table('ActionProperty_String')
        tableClientAttach = db.table('ClientAttach')
        tableRBAttachType = db.table('rbAttachType')
        tableContract = db.table('Contract')
        tableRBFinance = db.table('rbFinance')
        tableStatusObservation= db.table('Client_StatusObservation')

        def getActionIdList(dialogParams, actionTypeIdListByFlatCode):
            filterBegDate = dialogParams.get('filterBegDate', None)
            filterEndDate = dialogParams.get('filterEndDate', None)
            filterBegTime = dialogParams.get('filterBegTime', None)
            filterEndTime = dialogParams.get('filterEndTime', None)
            if not filterBegTime.isNull():
                begDateTime = QDateTime(filterBegDate, filterBegTime)
                filterBegDate = begDateTime
            if not filterEndTime.isNull():
                endDateTime = QDateTime(filterEndDate, filterEndTime)
                filterEndDate = endDateTime
            db = QtGui.qApp.db
            tableAction = db.table('Action')
            cond = [ tableAction['actionType_id'].inlist(actionTypeIdListByFlatCode),
                     tableAction['deleted'].eq(0),
                   ]
            if not forceBool(filterBegDate.date()):
                filterBegDate = QDate.currentDate()
                cond.append(u'Action.begDate IS NULL OR Date(Action.begDate) = \'%s\'' % (filterBegDate.toString('yyyy-MM-dd')))
            else:
                cond.append(tableAction['begDate'].isNotNull())
                cond.append(tableAction['begDate'].ge(filterBegDate))
            if forceBool(filterEndDate.date()):
                cond.append(tableAction['begDate'].isNotNull())
                cond.append(tableAction['begDate'].le(filterEndDate))
            return db.getDistinctIdList(tableAction, [tableAction['id']], cond)

        def findRenunciate(flatCode, filterBegDate = None, filterEndDate = None, indexRenunciate = 0, quotingTypeList = None, accountingSystemId = None,
        filterClientId = None, filterEventId = None, actionIdList = []):
            if not actionIdList:
                return []
            cols = [tableAction['id'],
                    tableEvent['id'].alias('eventId'),
                    tableEvent['client_id'],
                    tableEvent['externalId'],
                    tableClient['lastName'],
                    tableClient['firstName'],
                    tableClient['patrName'],
                    tableClient['sex'],
                    tableClient['birthDate'],
                    tableAction['begDate'],
                    tableAction['endDate'],
                    tableMes['code'],
                    tableContract['number'].alias('numberContract'),
                    tableContract['date'].alias('dateContract'),
                    tableContract['resolution'].alias('resolutionContract'),
                    tablePWS['name'].alias('namePerson')
                    ]
            cols.append(getMKB())
            cols.append(getReceivedBegDate(self.receivedActionTypeIdList))
            cols.append(getOSHBP())
            cols.append(getHospDocumentLocationInfo())
            cols.append(tableAPS['value'].alias('nameRenunciate'))
            cols.append(getStatusObservation())
            cols.append("""getClientCitizenshipTitle(Client.id, Action.begDate) as citizenship""")
            cond = [tableAction['id'].inlist(actionIdList),
                    #tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode(flatCode)),
                    tableAction['deleted'].eq(0),
                    tableEvent['deleted'].eq(0),
                    tableAP['deleted'].eq(0),
                    tableAPT['deleted'].eq(0),
                    tableClient['deleted'].eq(0),
                    tableAP['action_id'].eq(tableAction['id']),
                    tableAction['endDate'].isNotNull()
                   ]
            if contractId:
                cond.append(tableContract['id'].eq(contractId))
            if MKBFilter:
                cond.append(isMKB(MKBFrom, MKBTo))
            if order:
               cond.append(tableEvent['order'].eq(order))
            if eventTypeId:
               cond.append(tableEvent['eventType_id'].eq(eventTypeId))
            if filterMES:
                cond.append(tableMes['code'].eq(filterMES))
            queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
            queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.leftJoin(tableMes, tableMes['id'].eq(tableEvent['MES_id']))
            queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
            queryTable = queryTable.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
            queryTable = queryTable.innerJoin(tableAP, tableAP['type_id'].eq(tableAPT['id']))
            queryTable = queryTable.innerJoin(tableAPS, tableAPS['id'].eq(tableAP['id']))

            if QtGui.qApp.userHasAnyRight([urHBVisibleOwnEventsParentOrgStructureOnly, urHBVisibleOwnEventsOrgStructureOnly]):
                tableExecPerson = db.table('Person')
                tableEventType = db.table('EventType')
                queryTable = queryTable.leftJoin(tableExecPerson, tableExecPerson['id'].eq(tableEvent['execPerson_id']))
                queryTable = queryTable.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
                uOrgStructureId = forceRef(db.translate('Person', 'id', QtGui.qApp.userId, 'orgStructure_id'))
                if QtGui.qApp.userHasRight(urHBVisibleOwnEventsParentOrgStructureOnly):
                    parentOrgStructure = getParentOrgStructureId(uOrgStructureId)
                    uOrgStructureList = getOrgStructureDescendants(parentOrgStructure if parentOrgStructure else uOrgStructureId)
                    cond.append(db.joinOr([tableExecPerson['orgStructure_id'].inlist(uOrgStructureList), tableEventType['ignoreVisibleRights'].eq(1)]))
                elif QtGui.qApp.userHasRight(urHBVisibleOwnEventsOrgStructureOnly):
                    uOrgStructureList = getOrgStructureDescendants(uOrgStructureId)
                    cond.append(db.joinOr([tableExecPerson['orgStructure_id'].inlist(uOrgStructureList), tableEventType['ignoreVisibleRights'].eq(1)]))

            cond.append(tableAPT['name'].like(u'Причина отказа%'))
            cond.append(u'ActionProperty_String.value != \' \'')
            if personId:
                cond.append(tableEvent['execPerson_id'].eq(personId))
            if personExecId:
               cond.append(tableAction['person_id'].eq(personExecId))
            if self.statusObservation:
                cond.append(existsStatusObservation(self.statusObservation))
            if accountingSystemId and filterClientId:
                tableIdentification = db.table('ClientIdentification')
                queryTable = queryTable.innerJoin(tableIdentification, tableIdentification['client_id'].eq(tableClient['id']))
                cond.append(tableIdentification['accountingSystem_id'].eq(accountingSystemId))
                cond.append(tableIdentification['identifier'].eq(filterClientId))
                cond.append(tableIdentification['deleted'].eq(0))
            elif filterClientId:
                cond.append(tableClient['id'].eq(filterClientId))
            if filterEventId:
                cond.append(tableEvent['externalId'].eq(filterEventId))
            if reason and reason != u'не определено':
                cond.append(tableAPS['value'].eq(reason))
            nameProperty = ''
            if indexRenunciate == 1:
                nameProperty = u'Отделение'
            elif indexRenunciate == 2:
                nameProperty = u'Подразделение'
            if indexRenunciate == 1 or indexRenunciate == 2:
                orgStructureIdList = []
                if orgStructureId:
                    treeItem = orgStructureId.internalPointer() if orgStructureId.isValid() else None
                    orgStructureIdList = self.getOrgStructureIdList(orgStructureId) if treeItem and treeItem._id else []
                if orgStructureIdList:
                    cond.append(getDataOrgStructure(nameProperty, orgStructureIdList, False))
                cols.append(getDataOrgStructureName(nameProperty))
            if profile:
                cond.append(getHospitalBedProfile(profile))
            queryTable = queryTable.leftJoin(tablePWS, tablePWS['id'].eq(tableAction['person_id']))
            if quotingTypeList:
                quotingTypeIdList, quotingTypeClass = quotingTypeList
                if quotingTypeClass is not None:
                    cond.append(getDataClientQuoting(u'Квота', quotingTypeIdList))
            if QtGui.qApp.defaultHospitalBedFinanceByMoving() in (0, 2):
                cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.code, NULL) AS codeFinance')
                cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.name, NULL) AS nameFinance')
                if finance:
                    cond.append(tableContract['deleted'].eq(0))
                    cond.append(tableRBFinance['id'].eq(finance))
                    queryTable = queryTable.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.innerJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
                else:
                    queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
            else:
                queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
            cols.append(getContractClientPolicyForDate())
            cond.append('(Contract.id IS NOT NULL AND Contract.deleted=0) OR (Contract.id IS NULL)')
            if forceInt(codeAttachType) > 0:
                cond.append(tableRBAttachType['code'].eq(codeAttachType))
                queryTable = queryTable.innerJoin(tableClientAttach, tableClient['id'].eq(tableClientAttach['client_id']))
                queryTable = queryTable.innerJoin(tableRBAttachType, tableClientAttach['attachType_id'].eq(tableRBAttachType['id']))
            if indexSex > 0:
                cond.append(tableClient['sex'].eq(indexSex))
            if ageFor <= ageTo:
                cond.append(getAgeRangeCond(ageFor, ageTo))
            if not forceBool(filterBegDate.date()):
                filterBegDate = QDate().currentDate()
                cond.append(u'Action.begDate IS NULL OR Date(Action.begDate) = \'%s\'' % (filterBegDate.toString('yyyy-MM-dd')))
            else:
                cond.append(tableAction['begDate'].isNotNull())
                cond.append(tableAction['begDate'].ge(filterBegDate))
            if forceBool(filterEndDate.date()):
                cond.append(tableAction['begDate'].isNotNull())
                cond.append(tableAction['begDate'].le(filterEndDate))
            if deliverBy:
                cond.append(getDeliverByCond(deliverBy))
            if insurerId or regionSMO:
                queryTable = queryTable.innerJoin(tableClientPolicy,
                                                  u'''(ClientPolicy.id = getClientPolicyIdForDate(Client.id, IF(Contract.id IS NOT NULL AND Contract.deleted=0, IF(rbFinance.code = 2, 1, IF(rbFinance.code = 3, 0, 1)), 1), IF(Event.execDate IS NOT NULL, Event.execDate, Event.setDate), Event.id))''')
                if not regionSMO:
                    cond.append(tableClientPolicy['insurer_id'].eq(insurerId))
                else:
                    tableOrganisation = db.table('Organisation').alias('Org_Area')
                    queryTable = queryTable.innerJoin(tableOrganisation, [tableOrganisation['id'].eq(tableClientPolicy['insurer_id']), tableOrganisation['deleted'].eq(0)])
                    if regionSMOCode:
                        if regionTypeSMO:
                            cond.append(tableOrganisation['area'].notlike(regionSMOCode))
                        else:
                            cond.append(tableOrganisation['area'].like(regionSMOCode))
            return db.getRecordList(queryTable, cols, cond)
        if quotingType:
            quotingTypeClass, quotingTypeId = quotingType
            quotingTypeList = self.getQuotingTypeIdList(quotingType)
        else:
            quotingTypeClass = None
            quotingTypeList = None
        if index == 0:
            self.column[self.receivedDateCol] = u'Госпитализирован'
            receivedActionIdList = getActionIdList(dialogParams, self.receivedActionTypeIdList)
            recordsRenunciation = findRenunciate(u'received%', filterBegDate, filterEndDate, index, (quotingTypeList, quotingTypeClass), accountingSystemId, filterClientId, filterEventId, actionIdList=receivedActionIdList)
            for record in recordsRenunciation:
                statusObservation = forceString(record.value('statusObservation')).split('|')
                statusObservationCode = forceString(statusObservation[0]) if len(statusObservation)>=1 else u''
                statusObservationName = forceString(statusObservation[1]) if len(statusObservation)>=2 else u''
                statusObservationColor = forceString(statusObservation[2]) if len(statusObservation)>=3 else u''
                statusObservationDate = forceString(statusObservation[3]) if len(statusObservation)>=4 else u''
                statusObservationPerson = forceString(statusObservation[4]) if len(statusObservation)>=5 else u''
                begDate = forceDate(record.value('receivedBegDate'))
                policyEndDate = forceDate(record.value('policyEndDate'))
                colorFinance = None
                if policyEndDate:
                    if begDate < policyEndDate <= begDate.addDays(3):
                        colorFinance = QtGui.QColor(Qt.yellow)
                    elif begDate >= policyEndDate:
                        colorFinance = QtGui.QColor(Qt.red)
                nameContract = ' '.join([forceString(record.value(name)) for name in ('numberContract', 'dateContract', 'resolutionContract')])
                documentLocationInfo  = forceString(record.value('documentLocationInfo')).split("  ")
                hospDocumentLocation  = forceString(documentLocationInfo[0]) if len(documentLocationInfo)>=1 else ''
                documentLocationColor = forceString(documentLocationInfo[1]) if len(documentLocationInfo)>1 else ''
                item = [statusObservationCode,
                        forceString(record.value('nameFinance')),
                        nameContract,
                        forceRef(record.value('client_id')),
                        forceRef(record.value('eventId')),
                        forceString(record.value('externalId')),
                        forceString(record.value('lastName')) + u' ' + forceString(record.value('firstName')) + u' ' + forceString(record.value('patrName')),
                        self.sex[forceInt(record.value('sex'))],
                        forceDate(record.value('birthDate')),
                        forceDateTime(record.value('receivedBegDate')),
                        forceDateTime(record.value('endDate')),
                        forceString(record.value('nameRenunciate')),
                        forceString(record.value('code')),
                        forceString(record.value('MKB')),
                        forceString(record.value('profileName')),
                        forceString(record.value('nameOrgStructure')),
                        forceString(record.value('namePerson')),
                        forceString(record.value('citizenship')),
                        hospDocumentLocation,
                        forceString(record.value('codeFinance')),
                        '',
                        statusObservationName + u' (' + (statusObservationDate if statusObservationDate else u'') + u' ' + (statusObservationPerson if statusObservationPerson else u'') + u')',
                        statusObservationColor,
                        documentLocationColor,
                        colorFinance,
                        forceString(calcAge(forceDate(record.value('birthDate')), forceDate(record.value('endDate'))))
                        ]
                self.items.append(item)
                eventId = forceRef(record.value('eventId'))
                _dict = {
                        'observationCode': statusObservationCode,
                        'finance': forceString(record.value('nameFinance')),
                        'contract': nameContract,
                        'bedCode': '',
                        'begDate' : CDateTimeInfo(forceDateTime(record.value('receivedBegDate'))),
                        'endDate' : CDateTimeInfo(forceDateTime(record.value('endDate'))),
                        'orgStructure': forceString(record.value('nameOrgStructure')),
                        'financeCode': forceString(record.value('codeFinance')),
                        'bedName': '',
                        'observationName': statusObservationName,
                        'observationColor': statusObservationColor,
                        'renunciateReason': forceString(record.value('nameRenunciate')),
                        'responsiblePerson': forceString(record.value('namePerson'))
                    }
                self.itemByName[eventId] = _dict
        elif index == 1:
            self.column[self.receivedDateCol] = u'Госпитализирован'
            leavedActionIdList = getActionIdList(dialogParams, self.leavedActionTypeIdList)
            recordsRenunciation = findRenunciate(u'leaved%', filterBegDate, filterEndDate, index, (quotingTypeList, quotingTypeClass), accountingSystemId, filterClientId, filterEventId, actionIdList=leavedActionIdList)
            for record in recordsRenunciation:
                statusObservation = forceString(record.value('statusObservation')).split('|')
                statusObservationCode = forceString(statusObservation[0]) if len(statusObservation)>=1 else u''
                statusObservationName = forceString(statusObservation[1]) if len(statusObservation)>=2 else u''
                statusObservationColor = forceString(statusObservation[2]) if len(statusObservation)>=3 else u''
                statusObservationDate = forceString(statusObservation[3]) if len(statusObservation)>=4 else u''
                statusObservationPerson = forceString(statusObservation[4]) if len(statusObservation)>=5 else u''
                begDate = forceDate(record.value('receivedBegDate'))
                policyEndDate = forceDate(record.value('policyEndDate'))
                colorFinance = None
                if policyEndDate:
                    if begDate < policyEndDate <= begDate.addDays(3):
                       colorFinance = QtGui.QColor(Qt.yellow)
                    elif begDate >= policyEndDate:
                        colorFinance = QtGui.QColor(Qt.red)
                nameContract = ' '.join([forceString(record.value(name)) for name in ('numberContract', 'dateContract', 'resolutionContract')])
                documentLocationInfo  = forceString(record.value('documentLocationInfo')).split("  ")
                hospDocumentLocation  = forceString(documentLocationInfo[0]) if len(documentLocationInfo)>=1 else ''
                documentLocationColor = forceString(documentLocationInfo[1]) if len(documentLocationInfo)>1 else ''
                item = [statusObservationCode,
                        forceString(record.value('nameFinance')),
                        nameContract,
                        forceRef(record.value('client_id')),
                        forceRef(record.value('eventId')),
                        forceString(record.value('externalId')),
                        forceString(record.value('lastName')) + u' ' + forceString(record.value('firstName')) + u' ' + forceString(record.value('patrName')),
                        self.sex[forceInt(record.value('sex'))],
                        forceDate(record.value('birthDate')),
                        forceDateTime(record.value('receivedBegDate')),
                        forceDateTime(record.value('endDate')),
                        forceString(record.value('nameRenunciate')),
                        forceString(record.value('code')),
                        forceString(record.value('MKB')),
                        forceString(record.value('profileName')),
                        forceString(record.value('nameOrgStructure')),
                        forceString(record.value('namePerson')),
                        forceString(record.value('citizenship')),
                        hospDocumentLocation,
                        forceString(record.value('codeFinance')),
                        '',
                        statusObservationName + u' (' + (statusObservationDate if statusObservationDate else u'') + u' ' + (statusObservationPerson if statusObservationPerson else u'') + u')',
                        statusObservationColor,
                        documentLocationColor,
                        colorFinance,
                        forceString(calcAge(forceDate(record.value('birthDate')), forceDate(record.value('endDate'))))
                        ]
                self.items.append(item)
                eventId = forceRef(record.value('eventId'))
                _dict = {
                        'observationCode': statusObservationCode,
                        'finance': forceString(record.value('nameFinance')),
                        'contract': nameContract,
                        'bedCode': '',
                        'begDate' : CDateTimeInfo(forceDateTime(record.value('receivedBegDate'))),
                        'endDate' : CDateTimeInfo(forceDateTime(record.value('endDate'))),
                        'orgStructure': forceString(record.value('nameOrgStructure')),
                        'financeCode': forceString(record.value('codeFinance')),
                        'bedName': '',
                        'observationName': statusObservationName,
                        'observationColor': statusObservationColor,
                        'renunciateReason': forceString(record.value('nameRenunciate')),
                        'responsiblePerson': forceString(record.value('namePerson'))
                    }
                self.itemByName[eventId] = _dict
        elif index == 2:
            self.column[self.receivedDateCol] = u'Поставлен'
            planningActionIdList = getActionIdList(dialogParams, self.planningActionTypeIdList)
            records = findRenunciate(u'planning%', filterBegDate, filterEndDate, index, (quotingTypeList, quotingTypeClass), accountingSystemId, filterClientId, filterEventId, actionIdList=planningActionIdList)
            for record in records:
                statusObservation = forceString(record.value('statusObservation')).split('|')
                statusObservationCode = forceString(statusObservation[0]) if len(statusObservation)>=1 else u''
                statusObservationName = forceString(statusObservation[1]) if len(statusObservation)>=2 else u''
                statusObservationColor = forceString(statusObservation[2]) if len(statusObservation)>=3 else u''
                statusObservationDate = forceString(statusObservation[3]) if len(statusObservation)>=4 else u''
                statusObservationPerson = forceString(statusObservation[4]) if len(statusObservation)>=5 else u''
                begDate = forceDate(record.value('receivedBegDate'))
                policyEndDate = forceDate(record.value('policyEndDate'))
                colorFinance = None
                if policyEndDate:
                    if begDate < policyEndDate <= begDate.addDays(3):
                       colorFinance = QtGui.QColor(Qt.yellow)
                    elif begDate >= policyEndDate:
                        colorFinance = QtGui.QColor(Qt.red)
                nameContract = ' '.join([forceString(record.value(name)) for name in ('numberContract', 'dateContract', 'resolutionContract')])
                documentLocationInfo  = forceString(record.value('documentLocationInfo')).split("  ")
                hospDocumentLocation  = forceString(documentLocationInfo[0]) if len(documentLocationInfo)>=1 else ''
                documentLocationColor = forceString(documentLocationInfo[1]) if len(documentLocationInfo)>1 else ''
                item = [statusObservationCode,
                        forceString(record.value('nameFinance')),
                        nameContract,
                        forceRef(record.value('client_id')),
                        forceRef(record.value('eventId')),
                        forceString(record.value('externalId')),
                        forceString(record.value('lastName')) + u' ' + forceString(record.value('firstName')) + u' ' + forceString(record.value('patrName')),
                        self.sex[forceInt(record.value('sex'))],
                        forceDate(record.value('birthDate')),
                        forceDateTime(record.value('receivedBegDate')),
                        forceDateTime(record.value('endDate')),
                        forceString(record.value('nameRenunciate')),
                        forceString(record.value('code')),
                        forceString(record.value('MKB')),
                        forceString(record.value('profileName')),
                        forceString(record.value('nameOrgStructure')),
                        forceString(record.value('namePerson')),
                        forceString(record.value('citizenship')),
                        hospDocumentLocation,
                        forceString(record.value('codeFinance')),
                        '',
                        statusObservationName + u' (' + (statusObservationDate if statusObservationDate else u'') + u' ' + (statusObservationPerson if statusObservationPerson else u'') + u')',
                        statusObservationColor,
                        documentLocationColor,
                        colorFinance,
                        forceString(calcAge(forceDate(record.value('birthDate')), forceDate(record.value('endDate'))))
                        ]
                self.items.append(item)
                eventId = forceRef(record.value('eventId'))
                _dict = {
                        'observationCode': statusObservationCode,
                        'finance': forceString(record.value('nameFinance')),
                        'contract': nameContract,
                        'bedCode': '',
                        'begDate' : CDateTimeInfo(forceDateTime(record.value('receivedBegDate'))),
                        'endDate' : CDateTimeInfo(forceDateTime(record.value('endDate'))),
                        'orgStructure': forceString(record.value('nameOrgStructure')),
                        'financeCode': forceString(record.value('codeFinance')),
                        'bedName': '',
                        'observationName': statusObservationName,
                        'observationColor': statusObservationColor,
                        'renunciateReason': forceString(record.value('nameRenunciate')),
                        'responsiblePerson': forceString(record.value('namePerson'))
                    }
                self.itemByName[eventId] = _dict
        for col, order in self.headerSortingCol.items():
            self.sort(col, order)

    def sort(self, col, order=Qt.AscendingOrder):
        self.headerSortingCol = {col: order}
        reverse = order == Qt.DescendingOrder
        if col in [self.clientColumn, self.eventColumn]:
            self.items.sort(key=lambda x: forceInt(x[col]) if x else None, reverse=reverse)
        elif col in [self.birthDateCol, self.receivedDateCol, self.leavedDateCol]:
            self.items.sort(key=lambda x: forceDateTime(x[col]) if x else None, reverse=reverse)
        else:
            self.items.sort(key=lambda x: forceString(x[col]).lower() if x else None, reverse=reverse)
        self.reset()


class CDeathModel(CMonitoringModel):
    column = [u'С', u'И', u'Д', u'Номер', u'Код', u'Карта', u'ФИО', u'Пол', u'Дата рождения', u'Госпитализирован', u'Выбыл', u'Подразделение',  u'Ответственный', u'MKB', u'Профиль', u'Гражданство', u'М', u'Койко-дни', u'Направитель']
    statusObservationCol = 0
    financeCol = 1
    clientColumn = 3
    eventColumn = 4
    defaultOrderCol = 6
    birthDateCol = 8
    receivedDateCol = 9
    leavedDateCol = 10
    MKBColumn = 13
    profileCol = 14
    documentLocationCol = 16
    bedDaysCol = 17
    codeFinanceCol = 19
    statusObservationNameCol = 20
    colorStatusObservationCol = 21
    docLocalColorCol = 23
    colorFinanceCol = 24
    ageCol = 25

    def __init__(self, parent):
        CMonitoringModel.__init__(self, parent)
        self.items = []
        self._cols = []
        self.begDays = 0
        self.itemByName = {}
        self.statusObservation = None


    def getBegDays(self):
        return self.begDays

    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if role == Qt.DisplayRole:
            if column in [self.receivedDateCol, self.leavedDateCol]:
                item = self.items[row]
                return toVariant(item[column].toString('dd.MM.yyyy hh:mm'))
            elif column == self.birthDateCol:
                item = self.items[row]
                return toVariant(forceString(item[column]) + u' (' + item[self.ageCol] + u')')
            else:
                item = self.items[row]
            return toVariant(item[column])
        elif role == Qt.ToolTipRole:
            if column == self.statusObservationCol:
                item = self.items[row]
                if item[self.statusObservationCol]:
                    return QVariant(item[self.statusObservationCol] + u' ' + item[self.statusObservationNameCol])
                else:
                    return QVariant()
            elif column == self.financeCol:
                item = self.items[row]
                return QVariant(item[self.codeFinanceCol] + u' ' + item[column])
            elif column == self.profileCol:
                item = self.items[row]
                return QVariant(forceString(item[column]) + u' ' + item[self.bedNameCol])
        elif role == Qt.BackgroundColorRole:
            if column == self.statusObservationCol and self.items[row][column]:
                return toVariant(QtGui.QColor(self.items[row][self.colorStatusObservationCol]))
            elif column == self.financeCol:
                colorFinance = self.items[row][self.colorFinanceCol]
                if colorFinance:
                    return toVariant(colorFinance)
            elif column == self.documentLocationCol:
                docLocalColor = self.items[row][self.docLocalColorCol]
                if docLocalColor:
                    return toVariant(QtGui.QColor(docLocalColor))
        return QVariant()

    def cols(self):
        self._cols = [CCol(u'Статус наблюдения',                   ['statusObservation'], 20, 'l'),
                      CCol(u'Код ИФ',                              ['nameFinance'], 20, 'l'),
                      CCol(u'Договор',                             ['contract'], 20, 'l'),
                      CCol(u'Номер',                               ['client_id'], 20, 'l'),
                      CCol(u'Код события',                         ['event_id'], 20, 'l'),
                      CCol(u'Карта',                               ['externalId'], 20, 'l'),
                      CCol(u'ФИО',                                 ['lastName', 'firstName', 'patrName'], 30, 'l'),
                      CCol(u'Пол',                                 ['sex'], 15, 'l'),
                      CCol(u'Дата рождения',                       ['birthDate'], 20, 'l'),
                      CCol(u'Госпитализирован',                    ['begDateReceived'], 20, 'l'),
                      CCol(u'Выбыл',                               ['endDate'], 20, 'l'),
                      CCol(u'Подразделение',                       ['nameOS'], 30, 'l'),
                      CCol(u'Ответственный',                       ['namePerson'], 30, 'l'),
                      CCol(u'MKB',                                 ['MKB'], 20, 'l'),
                      CCol(u'Профиль',                             ['profileName'], 20, 'l'),
                      CCol(u'Гражданство',                         ['citizenship'], 50, 'l'),
                      CCol(u'Место нахождения учетного документа', ['hospDocumentLocation'], 20, 'l'),
                      CCol(u'Койко-дни',                           ['bedDays'], 20, 'l'),
                      CCol(u'Направитель',                         ['relegateOrg'], 30, 'l')
                      ]
        return self._cols

    def loadData(self, dialogParams):
        self.begDays = 0
        self.items = []
        self.itemByName = {}
        filterBegDate = dialogParams.get('filterBegDate', None)
        filterEndDate = dialogParams.get('filterEndDate', None)
        filterBegTime = dialogParams.get('filterBegTime', None)
        filterEndTime = dialogParams.get('filterEndTime', None)
        if not filterBegTime.isNull():
            begDateTime = QDateTime(filterBegDate, filterBegTime)
            filterBegDate = begDateTime
        if not filterEndTime.isNull():
            endDateTime = QDateTime(filterEndDate, filterEndTime)
            filterEndDate = endDateTime
        indexSex = dialogParams.get('indexSex', 0)
        ageFor = dialogParams.get('ageFor', 0)
        ageTo = dialogParams.get('ageTo', 150)
        order = dialogParams.get('order', -1)
        eventTypeId = dialogParams.get('eventTypeId', None)
        orgStructureId = dialogParams.get('orgStructureId', None)
        codeAttachType = dialogParams.get('codeAttachType', None)
        finance = dialogParams.get('finance', None)
        contractId = dialogParams.get('contractId', None)
        personId = dialogParams.get('personId', None)
        insurerId = dialogParams.get('insurerId', None)
        regionSMO, regionTypeSMO, regionSMOCode = dialogParams.get('regionSMO', (False, 0, None))
        personExecId = dialogParams.get('personExecId', None)
        quotingType = dialogParams.get('quotingType', None)
        accountingSystemId = dialogParams.get('accountingSystemId', None)
        filterClientId = dialogParams.get('filterClientId', None)
        filterEventId = dialogParams.get('filterEventId', None)
        statusObservation = dialogParams.get('statusObservation', None)
        reason = dialogParams.get('renunciationActionIndex', 0)
        profile = dialogParams.get('treatmentProfile', None)
        filterMES = dialogParams.get('filterMES', u'')
        MKBFilter = dialogParams['MKBFilter']
        MKBFrom   = dialogParams['MKBFrom']
        MKBTo     = dialogParams['MKBTo']
        scheduleId = dialogParams.get('scheduleId', None)
        self.statusObservation = statusObservation

        db = QtGui.qApp.db
        tableAPT = db.table('ActionPropertyType')
        tableAP = db.table('ActionProperty')
        tableActionType = db.table('ActionType')
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        tableClient = db.table('Client')
        tableClientPolicy = db.table('ClientPolicy')
        tablePWS = db.table('vrbPersonWithSpeciality')
        tableClientAttach = db.table('ClientAttach')
        tableRBAttachType = db.table('rbAttachType')
        tableContract = db.table('Contract')
        tableRBFinance = db.table('rbFinance')
        tableAPS = db.table('ActionProperty_String')
        tableStatusObservation = db.table('Client_StatusObservation')
        tableEventTypePurpose = db.table('rbEventTypePurpose')
        tableOrg = db.table('Organisation')

        def getActionIdList(dialogParams, actionTypeIdListByFlatCode):
            filterBegDate = dialogParams.get('filterBegDate', None)
            filterEndDate = dialogParams.get('filterEndDate', None)
            filterBegTime = dialogParams.get('filterBegTime', None)
            filterEndTime = dialogParams.get('filterEndTime', None)
            if not filterBegTime.isNull():
                begDateTime = QDateTime(filterBegDate, filterBegTime)
                filterBegDate = begDateTime
            if not filterEndTime.isNull():
                endDateTime = QDateTime(filterEndDate, filterEndTime)
                filterEndDate = endDateTime
            db = QtGui.qApp.db
            tableAction = db.table('Action')
            cond = [ tableAction['actionType_id'].inlist(actionTypeIdListByFlatCode),
                     tableAction['deleted'].eq(0),
                     tableAction['endDate'].isNotNull()
                   ]
            if not forceBool(filterBegDate.date()):
                filterBegDate = QDate.currentDate()
                cond.append(u'Action.begDate IS NULL OR Date(Action.begDate) = \'%s\'' % (filterBegDate.toString('yyyy-MM-dd')))
            else:
                cond.append(tableAction['begDate'].isNotNull())
                cond.append(tableAction['begDate'].ge(filterBegDate))
            if forceBool(filterEndDate.date()):
                cond.append(tableAction['begDate'].isNotNull())
                cond.append(tableAction['begDate'].le(filterEndDate))
            return db.getDistinctIdList(tableAction, [tableAction['id']], cond)

        def getDeath(filterBegDate, filterEndDate, reason = 0, orgStructureId = None, quotingTypeList = None, accountingSystemId = None, filterClientId = None, filterEventId = None):
            if not leavedActionIdList:
                return []
            cols = [tableAction['id'],
                    tableEvent['id'].alias('eventId'),
                    tableEvent['client_id'],
                    tableEvent['externalId'],
                    tableEvent['eventType_id'],
                    tableEvent['execDate'],
                    tableClient['lastName'],
                    tableClient['firstName'],
                    tableClient['patrName'],
                    tableClient['sex'],
                    tableClient['birthDate'],
                    tableAction['begDate'],
                    tableAction['endDate'],
                    tableEvent['setDate'],
                    tableContract['number'].alias('numberContract'),
                    tableContract['date'].alias('dateContract'),
                    tableContract['resolution'].alias('resolutionContract'),
                    tablePWS['name'].alias('namePerson'),
                    tableOrg['shortName'].alias('relegateOrg')
                    ]
            cols.append(getMKB())
            cols.append(getReceivedBegDate(self.receivedActionTypeIdList))
            cols.append(getLeavedEndDate(self.leavedActionTypeIdList))
            cols.append(getOSHBP())
            cols.append(getDataOrgStructureName(u'Отделение'))
            cols.append("""getClientCitizenshipTitle(Client.id, Action.begDate) as citizenship""")
            cols.append(getStatusObservation())
            cols.append(getHospDocumentLocationInfo())
            queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
            queryTable = queryTable.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
            queryTable = queryTable.innerJoin(tableAP, tableAP['type_id'].eq(tableAPT['id']))
            queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
            queryTable = queryTable.leftJoin(tablePWS, tablePWS['id'].eq(tableAction['person_id']))
            queryTable = queryTable.innerJoin(tableAPS, tableAPS['id'].eq(tableAP['id']))
            queryTable = queryTable.leftJoin(tableOrg, tableEvent['relegateOrg_id'].eq(tableOrg['id']))
            cond = [tableAction['id'].inlist(leavedActionIdList),
                    #tableAction['actionType_id'].inlist(self.leavedActionTypeIdList),
                    tableAction['deleted'].eq(0),
                    tableEvent['deleted'].eq(0),
                    tableAP['deleted'].eq(0),
                    tableClient['deleted'].eq(0),
                    tableAPT['name'].like(u'Исход госпитализации'),
                    tableAP['action_id'].eq(tableAction['id']),
                    tableAction['endDate'].isNotNull()
                   ]
            if scheduleId:
                cond.append(isScheduleBeds(scheduleId))
            if contractId:
                cond.append(tableContract['id'].eq(contractId))
            if MKBFilter:
                cond.append(isMKB(MKBFrom, MKBTo))
            if order:
               cond.append(tableEvent['order'].eq(order))
            if eventTypeId:
               cond.append(tableEvent['eventType_id'].eq(eventTypeId))
            if filterMES:
                tableMes = db.table('mes.MES')
                queryTable = queryTable.leftJoin(tableMes, tableMes['id'].eq(tableEvent['MES_id']))
                cond.append(tableMes['code'].eq(filterMES))
            tableEventType = db.table('EventType')
            queryTable = queryTable.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))

            if QtGui.qApp.userHasAnyRight([urHBVisibleOwnEventsParentOrgStructureOnly, urHBVisibleOwnEventsOrgStructureOnly]):
                tableExecPerson = db.table('Person')
                queryTable = queryTable.leftJoin(tableExecPerson, tableExecPerson['id'].eq(tableEvent['execPerson_id']))
                uOrgStructureId = forceRef(db.translate('Person', 'id', QtGui.qApp.userId, 'orgStructure_id'))
                if QtGui.qApp.userHasRight(urHBVisibleOwnEventsParentOrgStructureOnly):
                    parentOrgStructure = getParentOrgStructureId(uOrgStructureId)
                    uOrgStructureList = getOrgStructureDescendants(parentOrgStructure if parentOrgStructure else uOrgStructureId)
                    cond.append(db.joinOr([tableExecPerson['orgStructure_id'].inlist(uOrgStructureList), tableEventType['ignoreVisibleRights'].eq(1)]))
                elif QtGui.qApp.userHasRight(urHBVisibleOwnEventsOrgStructureOnly):
                    uOrgStructureList = getOrgStructureDescendants(uOrgStructureId)
                    cond.append(db.joinOr([tableExecPerson['orgStructure_id'].inlist(uOrgStructureList), tableEventType['ignoreVisibleRights'].eq(1)]))

            cond.append(u"(EventType.medicalAidType_id IN (SELECT rbMedicalAidType.id from rbMedicalAidType where rbMedicalAidType.code IN ('1', '2', '3', '7')))")
            cond.append('(Contract.id IS NOT NULL AND Contract.deleted=0) OR (Contract.id IS NULL)')
            if personId:
                cond.append(tableEvent['execPerson_id'].eq(personId))
            if personExecId:
               cond.append(tableAction['person_id'].eq(personExecId))
            if self.statusObservation:
                cond.append(existsStatusObservation(self.statusObservation))
            if accountingSystemId and filterClientId:
                tableIdentification = db.table('ClientIdentification')
                queryTable = queryTable.innerJoin(tableIdentification, tableIdentification['client_id'].eq(tableClient['id']))
                cond.append(tableIdentification['accountingSystem_id'].eq(accountingSystemId))
                cond.append(tableIdentification['identifier'].eq(filterClientId))
                cond.append(tableIdentification['deleted'].eq(0))
            elif filterClientId:
                cond.append(tableClient['id'].eq(filterClientId))
            if filterEventId:
                cond.append(tableEvent['externalId'].eq(filterEventId))
            if reason and reason != u'не определено':
                cond.append(u'''ActionProperty_String.value %s'''%(updateLIKE(reason)))
            else:
                cond.append(db.joinOr([tableAPS['value'].like(u'умер%'), tableAPS['value'].like(u'смерть%')]))
            if orgStructureId:
                treeItem = orgStructureId.internalPointer() if orgStructureId.isValid() else None
                orgStructureIdList = self.getOrgStructureIdList(orgStructureId) if treeItem and treeItem._id else []
                if orgStructureIdList:
                    cond.append(getDataOrgStructure(u'Отделение', orgStructureIdList, False))
            if quotingTypeList:
                quotingTypeIdList, quotingTypeClass = quotingTypeList
                if quotingTypeClass is not None:
                    cond.append(getDataClientQuoting(u'Квота', quotingTypeIdList))
            if QtGui.qApp.defaultHospitalBedFinanceByMoving() in (0, 2):
                cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.code, NULL) AS codeFinance')
                cols.append(u'IF(Contract.id IS NOT NULL AND Contract.deleted=0, rbFinance.name, NULL) AS nameFinance')
                if finance:
                    cond.append(tableContract['deleted'].eq(0))
                    cond.append(tableRBFinance['id'].eq(finance))
                    queryTable = queryTable.innerJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.innerJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
                else:
                    queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
                    queryTable = queryTable.leftJoin(tableRBFinance, tableRBFinance['id'].eq(tableContract['finance_id']))
            else:
                queryTable = queryTable.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))
            cols.append(getContractClientPolicyForDate())
            if forceInt(codeAttachType) > 0:
                queryTable = queryTable.innerJoin(tableClientAttach, tableClient['id'].eq(tableClientAttach['client_id']))
                queryTable = queryTable.innerJoin(tableRBAttachType, tableClientAttach['attachType_id'].eq(tableRBAttachType['id']))
                cond.append(tableRBAttachType['code'].eq(codeAttachType))
                cond.append(tableClientAttach['deleted'].eq(0))
            if indexSex > 0:
                cond.append(tableClient['sex'].eq(indexSex))
            if ageFor <= ageTo:
                cond.append(getAgeRangeCond(ageFor, ageTo))
            if not forceBool(filterBegDate.date()):
                filterBegDate = QDate().currentDate()
                cond.append(u'Action.begDate IS NULL OR Date(Action.begDate) = \'%s\'' % (filterBegDate.toString('yyyy-MM-dd')))
            else:
                cond.append(tableAction['begDate'].isNotNull())
                cond.append(tableAction['begDate'].ge(filterBegDate))
            if forceBool(filterEndDate.date()):
                cond.append(tableAction['begDate'].isNotNull())
                cond.append(tableAction['begDate'].le(filterEndDate))
            if profile:
                cond.append(getHospitalBedProfile(profile))

            if insurerId or regionSMO:
                queryTable = queryTable.innerJoin(tableClientPolicy,
                                                  u'''(ClientPolicy.id = getClientPolicyIdForDate(Client.id, IF(Contract.id IS NOT NULL AND Contract.deleted=0, IF(rbFinance.code = 2, 1, IF(rbFinance.code = 3, 0, 1)), 1), IF(Event.execDate IS NOT NULL, Event.execDate, Event.setDate), Event.id))''')
                if not regionSMO:
                    cond.append(tableClientPolicy['insurer_id'].eq(insurerId))
                else:
                    tableOrganisation = db.table('Organisation').alias('Org_Area')
                    queryTable = queryTable.innerJoin(tableOrganisation, [tableOrganisation['id'].eq(tableClientPolicy['insurer_id']), tableOrganisation['deleted'].eq(0)])
                    if regionSMOCode:
                        if regionTypeSMO:
                            cond.append(tableOrganisation['area'].notlike(regionSMOCode))
                        else:
                            cond.append(tableOrganisation['area'].like(regionSMOCode))
            return db.getRecordList(queryTable, cols, cond)
        self.items = []
        if quotingType:
            quotingTypeClass, quotingTypeId = quotingType
            quotingTypeList = self.getQuotingTypeIdList(quotingType)
        else:
            quotingTypeClass = None
            quotingTypeList = None
        leavedActionIdList = getActionIdList(dialogParams, self.leavedActionTypeIdList)
        recordsReceived = getDeath(filterBegDate, filterEndDate, reason, orgStructureId, (quotingTypeList, quotingTypeClass), accountingSystemId, filterClientId, filterEventId)
        queryTableDeatch = tableEvent.leftJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
        queryTableDeatch = queryTableDeatch.leftJoin(tableEventTypePurpose, tableEventTypePurpose['id'].eq(tableEventType['purpose_id']))
        for record in recordsReceived:
            statusObservation = forceString(record.value('statusObservation')).split('|')
            statusObservationCode = forceString(statusObservation[0]) if len(statusObservation)>=1 else u''
            statusObservationName = forceString(statusObservation[1]) if len(statusObservation)>=2 else u''
            statusObservationColor = forceString(statusObservation[2]) if len(statusObservation)>=3 else u''
            statusObservationDate = forceString(statusObservation[3]) if len(statusObservation)>=4 else u''
            statusObservationPerson = forceString(statusObservation[4]) if len(statusObservation)>=5 else u''
            nameContract = ' '.join([forceString(record.value(name)) for name in ('numberContract', 'dateContract', 'resolutionContract')])
            clientId = forceRef(record.value('client_id'))
            begDate = forceDate(record.value('receivedBegDate'))
            leavedEndDate = forceDate(record.value('leavedEndDate'))
            policyEndDate = forceDate(record.value('policyEndDate'))
            colorFinance = None
            if policyEndDate:
                if begDate < policyEndDate <= begDate.addDays(3):
                   colorFinance = QtGui.QColor(Qt.yellow)
                elif begDate >= policyEndDate:
                    colorFinance = QtGui.QColor(Qt.red)
            deatchEventId = None
            if clientId:
                condDeatch = [tableEvent['deleted'].eq(0),
                              tableEventType['deleted'].eq(0),
                              tableEvent['client_id'].eq(clientId),
                              tableEventTypePurpose['code'].eq(5)
                              ]
                recordDeatch = db.getRecordEx(queryTableDeatch, [tableEvent['id'].alias('deatchEventId')], condDeatch, u'Event.id DESC')
                if recordDeatch:
                    deatchEventId = forceRef(recordDeatch.value('deatchEventId'))
            documentLocationInfo  = forceString(record.value('documentLocationInfo')).split("  ")
            hospDocumentLocation  = forceString(documentLocationInfo[0]) if len(documentLocationInfo) >= 1 else ''
            documentLocationColor = forceString(documentLocationInfo[1]) if len(documentLocationInfo) > 1 else ''
            setDate = forceDate(record.value('setDate'))
            execDate = forceDate(record.value('execDate'))
            bedDays = updateDurationEvent(setDate, execDate if execDate.isValid() else QDate().currentDate(),
                                          filterBegDate, filterEndDate, forceRef(record.value('eventType_id')),
                                          isPresence=False)
            self.begDays += forceInt(bedDays) if bedDays != u'-' else 0
            item = [statusObservationCode,
                    forceString(record.value('nameFinance')),
                    nameContract,
                    clientId,
                    forceRef(record.value('eventId')),
                    forceString(record.value('externalId')),
                    forceString(record.value('lastName')) + u' ' + forceString(record.value('firstName')) + u' ' + forceString(record.value('patrName')),
                    self.sex[forceInt(record.value('sex'))],
                    forceDate(record.value('birthDate')),
                    forceDateTime(record.value('receivedBegDate')),
                    forceDateTime(record.value('endDate')),
                    forceString(record.value('nameOrgStructure')),
                    forceString(record.value('namePerson')),
                    forceString(record.value('MKB')),
                    forceString(record.value('profileName')),
                    forceString(record.value('citizenship')),
                    hospDocumentLocation,
                    bedDays,
                    forceString(record.value('relegateOrg')),
                    forceString(record.value('codeFinance')),
                    statusObservationName + u' (' + (statusObservationDate if statusObservationDate else u'') + u' ' + (statusObservationPerson if statusObservationPerson else u'') + u')',
                    statusObservationColor,
                    deatchEventId,
                    documentLocationColor,
                    colorFinance,
                    forceString(calcAge(forceDate(record.value('birthDate')), forceDate(record.value('endDate'))))
                    ]
            self.items.append(item)
            eventId = forceRef(record.value('eventId'))
            _dict = {
                        'observationCode': statusObservationCode,
                        'finance': forceString(record.value('nameFinance')),
                        'contract': nameContract,
                        'bedCode': '',
                        'begDate' : CDateTimeInfo(forceDateTime(record.value('receivedBegDate'))),
                        'endDate' : CDateTimeInfo(forceDateTime(record.value('endDate'))),
                        'orgStructure': forceString(record.value('nameOrgStructure')),
                        'financeCode': forceString(record.value('codeFinance')),
                        'bedName': '',
                        'observationName': statusObservationName,
                        'observationColor': statusObservationColor
                    }
            self.itemByName[eventId] = _dict
        for col, order in self.headerSortingCol.items():
            self.sort(col, order)

    def sort(self, col, order=Qt.AscendingOrder):
        self.headerSortingCol = {col: order}
        reverse = order == Qt.DescendingOrder
        if col in [self.clientColumn, self.bedDaysCol, self.eventColumn]:
            self.items.sort(key=lambda x: forceInt(x[col]) if x else None, reverse=reverse)
        elif col in [self.birthDateCol, self.receivedDateCol, self.leavedDateCol]:
            self.items.sort(key=lambda x: forceDateTime(x[col]) if x else None, reverse=reverse)
        else:
            self.items.sort(key=lambda x: forceString(x[col]).lower() if x else None, reverse=reverse)
        self.reset()


class CReanimationModel(CRecordListModel):
    defaultOrderCol = 5
    def __init__(self, parent):
        CRecordListModel.__init__(self, parent)
        self.headerSortingCol = {}  # для openEvent в CHospitalBedsDialog
        self.addCol(CInDocTableCol(u'Статус наблюдения', 'statusObservation', 20, readOnly=True))
        self.addCol(CInDocTableCol(u'Код ИФ', 'nameFinance', 20, readOnly=True))
        self.addCol(CInDocTableCol(u'Договор', 'contract', 20, readOnly=True))
        self.addCol(CInDocTableCol(u'Номер', 'client_id', 20, readOnly=True))
        self.addCol(CInDocTableCol(u'Карта', 'externalId', 20, readOnly=True))
        self.addCol(CInDocTableCol(u'ФИО', 'nameClient', 30, readOnly=True))
        self.addCol(CEnumInDocTableCol(u'Пол', 'sex', 15, values=(u'', u'М', u'Ж'), readOnly=True))
        self.addCol(CDateInDocTableCol(u'Госпитализирован', 'receivedBegDate', 20, readOnly=True))
        self.addCol(CDateInDocTableCol(u'Поступил', 'begDate', 20, readOnly=True))
        self.addCol(CDateInDocTableCol(u'Выбыл', 'execDate', 20, readOnly=True))
        self.addCol(CInDocTableCol(u'МКБ', 'MKB', 20, readOnly=True))
        self.addCol(CInDocTableCol(u'Профиль', 'profileName', 20, readOnly=True))
        self.addCol(CInDocTableCol(u'Подразделение', 'nameOrgStructure', 20, readOnly=True))
        self.addCol(CInDocTableCol(u'Лечащий врач', 'namePerson', 20, readOnly=True))


    def loadData(self, dialogParams):
        begDateTime = QDateTime(dialogParams.get('filterBegDate', QDate()),
                                dialogParams.get('filterBegTime', QTime()))
        endDateTime = QDateTime(dialogParams.get('filterEndDate', QDate()),
                                dialogParams.get('filterEndTime', QTime()))
        indexSex = dialogParams.get('indexSex', 0)
        ageFor = dialogParams.get('ageFor', 0)
        ageTo = dialogParams.get('ageTo', 150)
        order = dialogParams.get('order', -1)
        eventTypeId = dialogParams.get('eventTypeId', None)
        orgStructureId = dialogParams.get('orgStructureId', None)
        codeAttachType = dialogParams.get('codeAttachType', None)
        finance = dialogParams.get('finance', None)
        contractId = dialogParams.get('contractId', None)
        personId = dialogParams.get('personId', None)
        # insurerId = dialogParams.get('insurerId', None)
        # regionSMO, regionTypeSMO, regionSMOCode = dialogParams.get('regionSMO', (False, 0, None))
        # personExecId = dialogParams.get('personExecId', None)
        # quotingType = dialogParams.get('quotingType', None)
        # accountingSystemId = dialogParams.get('accountingSystemId', None)
        # filterClientId = dialogParams.get('filterClientId', None)
        # filterEventId = dialogParams.get('filterEventId', None)
        # statusObservation = dialogParams.get('statusObservation', None)
        # reason = dialogParams.get('renunciationActionIndex', 0)
        treatmentProfile = dialogParams.get('treatmentProfile', None)
        # filterMES = dialogParams.get('filterMES', u'')
        MKBFilter = dialogParams['MKBFilter']
        MKBFrom = dialogParams['MKBFrom']
        MKBTo = dialogParams['MKBTo']
        # scheduleId = dialogParams.get('scheduleId', None)

        db = QtGui.qApp.db
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        tableContract = db.table('Contract')
        tableEvent = db.table('Event')
        tableFinance = db.table('rbFinance')
        tableClient = db.table('Client')
        tableClientAttach = db.table('ClientAttach')
        tableRBAttachType = db.table('rbAttachType')

        queryTable = tableAction
        queryTable = queryTable.innerJoin(tableActionType, tableAction['actionType_id'].eq(tableActionType['id']))
        queryTable = queryTable.innerJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
        queryTable = queryTable.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
        queryTable = queryTable.leftJoin(tableContract, db.joinAnd([tableEvent['contract_id'].eq(tableContract['id']), tableContract['deleted'].eq(0)]))
        queryTable = queryTable.leftJoin(tableFinance, tableAction['finance_id'].eq(tableFinance['id']))

        cols = [
            tableAction['id'],
            tableAction['event_id'],
            getStatusObservation(),
            tableFinance['name'].alias('nameFinance'),
            "CONCAT_WS(' ', Contract.number, DATE_FORMAT(Contract.date, '%d.%m.%Y'), Contract.resolution) AS contract",
            tableEvent['client_id'],
            tableEvent['externalId'],
            "CONCAT_WS(' ', Client.lastName, Client.firstName, Client.patrName) AS nameClient",
            tableClient['sex'],
            getReceivedBegDate(getActionTypeIdListByFlatCode('received%')),
            tableAction['begDate'],
            tableEvent['execDate'],
            tableAction['MKB'],
            
            getHBProfileFromBed(),
            
            '(SELECT name FROM OrgStructure WHERE id = Action.orgStructure_id) AS nameOrgStructure',
            
            '(SELECT name FROM vrbPersonWithSpeciality WHERE id = Action.person_id) AS namePerson',
        ]
        cond = [
            tableEvent['deleted'].eq(0),
            tableAction['deleted'].eq(0),
            tableActionType['deleted'].eq(0),
            tableActionType['flatCode'].eq('reanimation'),
            tableAction['status'].eq(CActionStatus.started),
        ]
        
        # не использовать фильтр по дате
        # if begDateTime:
        #     cond.append(tableAction['begDate'].ge(begDateTime))
        # if endDateTime:
        #     cond.append(tableAction['begDate'].le(endDateTime))
        if indexSex > 0:
            cond.append(tableClient['sex'].eq(indexSex))
        if ageFor <= ageTo:
            cond.append(getAgeRangeCond(ageFor, ageTo))
        if order:
           cond.append(tableEvent['order'].eq(order))
        if eventTypeId:
            cond.append(tableEvent['eventType_id'].eq(eventTypeId))
        if orgStructureId:
            treeItem = orgStructureId.internalPointer() if orgStructureId.isValid() else None
            orgStructureIdList = self.getOrgStructureIdList(orgStructureId) if treeItem and treeItem._id else []
            if orgStructureIdList:
                cond.append(tableAction['orgStructure_id'].inlist(orgStructureIdList))
        if forceInt(codeAttachType) > 0:
            queryTable = queryTable.innerJoin(tableClientAttach, tableClient['id'].eq(tableClientAttach['client_id']))
            queryTable = queryTable.innerJoin(tableRBAttachType, tableClientAttach['attachType_id'].eq(tableRBAttachType['id']))
            cond.append(tableRBAttachType['code'].eq(codeAttachType))
            cond.append(tableClientAttach['deleted'].eq(0))
        if finance:
            cond.append(tableFinance['id'].eq(finance))
        if contractId:
            cond.append(tableContract['id'].eq(contractId))
        if personId:
            cond.append(tableAction['person_id'].eq(personId))
        if treatmentProfile:
            cond.append(getHospitalBedProfile(treatmentProfile))
        if MKBFilter:
            cond.append(tableAction['MKB'].ge(MKBFrom))
            cond.append(tableAction['MKB'].le(MKBTo))

        self.setItems(db.getRecordList(queryTable, cols, cond))


    def getClientId(self, row):
        return forceInt(self.getRecordByRow(row).value('client_id'))


    def getEventId(self, row):
        return forceInt(self.getRecordByRow(row).value('event_id'))


    def getOrgStructureIdList(self, treeIndex):
        treeItem = treeIndex.internalPointer() if treeIndex.isValid() else None
        return treeItem.getItemIdList() if treeItem else []
    
    
    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if role == Qt.DisplayRole:
            if column == 0:
                statusObservation = forceString(self.getRecordByRow(row).value('statusObservation')).split('|')
                if statusObservation[0]:
                    return toVariant(statusObservation[0])
            return CRecordListModel.data(self, index, role)
        elif role == Qt.BackgroundColorRole:
            if column == 0:
                statusObservation = forceString(self.getRecordByRow(row).value('statusObservation')).split('|')
                statusObservationColor = forceString(statusObservation[2]) if len(statusObservation)>=3 else u''
                if statusObservationColor:
                    return toVariant(QtGui.QColor(statusObservationColor))
            return CRecordListModel.data(self, index, role)
        else:
            return CRecordListModel.data(self, index, role)
    
    
    def sort(self, col, order=Qt.AscendingOrder):
        self.headerSortingCol = {col: order}
        reverse = order == Qt.DescendingOrder
        if col in [7, 8, 9]:
            self._items.sort(key=lambda x: forceDateTime(x.value(col+2)) if x else None, reverse=reverse)
        elif col in [3]:
            self._items.sort(key=lambda x: forceInt(x.value(col+2)) if x else None, reverse=reverse)
        else:
            self._items.sort(key=lambda x: forceString(x.value(col+2)).lower() if x else None, reverse=reverse)
        self.reset()


class CAttendanceActionsTableModel(CTableModel):
    class CLocPresenceOSColumn(CCol):
        def __init__(self, title, fields, defaultWidth):
            CCol.__init__(self, title, fields, defaultWidth, 'l')


        def format(self, values):
            val = values[0]
            eventId  = forceRef(val)
            clientId = None
            if eventId:
                db = QtGui.qApp.db
                table = db.table('Event')
                clientRecord = db.getRecordEx(table, [table['client_id']], [table['deleted'].eq(0), table['id'].eq(eventId)])
                if clientRecord:
                    clientId = forceRef(clientRecord.value('client_id'))
                if not clientId:
                    return CCol.invalid
                record = values[1]
                actionDate = forceDate(record.value('directionDate'))
                if not actionDate:
                    actionDate = forceDate(record.value('begDate'))
                if not actionDate:
                    return CCol.invalid
                query = QtGui.qApp.db.query(getDataOrgStructureNameMoving(u'Отделение пребывания', actionDate, clientId, u'moving%%'))
                if query.first():
                    record=query.record()
                    return record.value('nameOrgStructure')
                return CCol.invalid
            return CCol.invalid


    class CLocJobTicketColumn(CCol):
        def __init__(self, title, fields, defaultWidth):
            CCol.__init__(self, title, fields, defaultWidth, 'l')


        def format(self, values):
            val = values[0]
            actionId  = forceRef(val)
            if actionId:
                db = QtGui.qApp.db
                tableAction = db.table('Action')
                tableAP = db.table('ActionProperty')
                tableAPT = db.table('ActionPropertyType')
                tableAPJT = db.table('ActionProperty_Job_Ticket')
                tableJT = db.table('Job_Ticket')
                table = tableAction.innerJoin(tableAP, tableAP['action_id'].eq(tableAction['id']))
                table = table.innerJoin(tableAPT, tableAPT['id'].eq(tableAP['type_id']))
                table = table.innerJoin(tableAPJT, tableAP['id'].eq(tableAPJT['id']))
                table = table.innerJoin(tableJT, tableAPJT['value'].eq(tableJT['id']))
                cond = [tableAction['id'].eq(actionId),
                        tableJT['deleted'].eq(0),
                        tableAPT['deleted'].eq(0),
                        tableAPT['actionType_id'].eq(tableAction['actionType_id']),
                        tableAP['action_id'].eq(tableAction['id']),
                        tableAPT['typeName'].like('JobTicket'),
                        tableJT['id'].isNotNull()
                        ]
                record = db.getRecordEx(table, [tableAPJT['value']], cond, order=tableAPJT['id'].name())
                if record:
                    jobTicketId = forceRef(record.value('value'))
                    return toVariant(getJobTicketAsText(jobTicketId)) if jobTicketId else QVariant()
                return CCol.invalid
            return CCol.invalid


    class CLocClientColumn(CCol):
        def __init__(self, title, fields, defaultWidth):
            CCol.__init__(self, title, fields, defaultWidth, 'l')


        def format(self, values):
            val = values[0]
            eventId  = forceRef(val)
            if eventId:
                db = QtGui.qApp.db
                tableEvent = db.table('Event')
                tableClient = db.table('Client')
                table = tableEvent.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))

                clientRecord = db.getRecordEx(table, [tableClient['lastName'], tableClient['firstName'], tableClient['patrName']], [tableEvent['deleted'].eq(0), tableClient['deleted'].eq(0), tableEvent['id'].eq(eventId)])
                if clientRecord:
                    name  = formatShortNameInt(forceString(clientRecord.value('lastName')),
                                                    forceString(clientRecord.value('firstName')),
                                                    forceString(clientRecord.value('patrName')))
                    return toVariant(name)
                return CCol.invalid
            return CCol.invalid


    class CLocClientIdentifierColumn(CCol):
        def __init__(self, title, fields, defaultWidth):
            CCol.__init__(self, title, fields, defaultWidth, 'l')
            self.identifiersCache = CRecordCache()


        def getClientIdentifier(self, clientId):
            identifier = self.identifiersCache.get(clientId)
            if identifier is None:
                accountingSystemId = QtGui.qApp.defaultAccountingSystemId()
                if accountingSystemId is None:
                    identifier = clientId
                else:
                    db = QtGui.qApp.db
                    tableClientIdentification = db.table('ClientIdentification')
                    cond = [tableClientIdentification['client_id'].eq(clientId),
                            tableClientIdentification['accountingSystem_id'].eq(accountingSystemId)]
                    record = db.getRecordEx(tableClientIdentification, tableClientIdentification['identifier'], cond)
                    identifier = forceString(record.value(0)) if record else ''
                self.identifiersCache.put(clientId, identifier)
            return identifier


        def format(self, values):
            val = values[0]
            eventId = forceRef(val)
            if eventId:
                db = QtGui.qApp.db
                table = db.table('Event')
                clientRecord = db.getRecordEx(table, [table['client_id'], table['externalId']], [table['deleted'].eq(0), table['id'].eq(eventId)])
                if clientRecord:
                    clientId = forceRef(clientRecord.value('client_id'))
                    externalId = forceString(clientRecord.value('externalId'))
                    return toVariant(forceString(self.getClientIdentifier(clientId)) + (u', карта %s'%(externalId) if externalId else u''))
            return CCol.invalid


    class CLocClientBirthDateColumn(CCol):
        def __init__(self, title, fields, defaultWidth):
            CCol.__init__(self, title, fields, defaultWidth, 'l')


        def format(self, values):
            val = values[0]
            eventId  = forceRef(val)
            if eventId:
                db = QtGui.qApp.db
                tableEvent = db.table('Event')
                tableClient = db.table('Client')
                table = tableEvent.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
                clientRecord = db.getRecordEx(table, [tableClient['birthDate']], [tableEvent['deleted'].eq(0), tableClient['deleted'].eq(0), tableEvent['id'].eq(eventId)])
                if clientRecord:
                    return toVariant(forceString(clientRecord.value('birthDate')))
            return CCol.invalid


    class CLocClientSexColumn(CCol):
        def __init__(self, title, fields, defaultWidth):
            CCol.__init__(self, title, fields, defaultWidth, 'l')


        def format(self, values):
            val = values[0]
            eventId  = forceRef(val)
            if eventId:
                db = QtGui.qApp.db
                tableEvent = db.table('Event')
                tableClient = db.table('Client')
                table = tableEvent.innerJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
                clientRecord = db.getRecordEx(table, [tableClient['sex']], [tableEvent['deleted'].eq(0), tableClient['deleted'].eq(0), tableEvent['id'].eq(eventId)])
                if clientRecord:
                    return toVariant([u'', u'М', u'Ж'][forceInt(clientRecord.value('sex'))])
            return CCol.invalid


    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.clientCol   = CAttendanceActionsTableModel.CLocClientColumn( u'Ф.И.О.', ['event_id'], 60)
        self.clientIdentifierCol = CAttendanceActionsTableModel.CLocClientIdentifierColumn(u'Идентификатор', ['event_id'], 30)
        self.clientBirthDateCol = CAttendanceActionsTableModel.CLocClientBirthDateColumn(u'Дата рожд.', ['event_id'], 20)
        self.clientSexCol = CAttendanceActionsTableModel.CLocClientSexColumn(u'Пол', ['event_id'], 5)
        self.addColumn(self.clientCol)
        self.addColumn(self.clientBirthDateCol)
        self.addColumn(self.clientSexCol)
        self.addColumn(CDateTimeFixedCol(u'Назначено',      ['directionDate'], 15))
        self.addColumn(CAttendanceActionsTableModel.CLocPresenceOSColumn( u'Отделение пребывания', ['event_id'], 60))
        self.addColumn(CAttendanceActionsTableModel.CLocJobTicketColumn( u'Номерок', ['id'], 60))
        self.addColumn(CActionTypeCol(u'Действие', 15))
        self.addColumn(CBoolCol(u'Срочно',         ['isUrgent'],      15))
        self.addColumn(CIntCol(u'Д',               ['duration'],      15))
        self.addColumn(CIntCol(u'И',               ['periodicity'],   15))
        self.addColumn(CIntCol(u'К',               ['aliquoticity'],  15))
        self.addColumn(CEnumCol(u'Состояние',      ['status'], CActionStatus.names, 4))
        self.addColumn(CDateTimeFixedCol(u'Начато',     ['begDate'],       15))
        self.addColumn(CDateTimeFixedCol(u'Окончено',   ['endDate'],       15))
        self.addColumn(CDateTimeFixedCol(u'План',       ['plannedEndDate'],15))
        self.addColumn(CRefBookCol(u'Назначил',    ['setPerson_id'], 'vrbPersonWithSpeciality', 20))
        self.addColumn(CRefBookCol(u'Выполнил',    ['person_id'],    'vrbPersonWithSpeciality', 20))
        self.addColumn(CTextCol(u'Каб',            ['office'],                                6))
        self.addColumn(CTextCol(u'Примечания',     ['note'],                                  6))
        self.setTable('Action')
        self.headerSortingCol = {}
        self._mapColumnToOrder = {u'event_id'           :u'CONCAT(Client.lastName, Client.firstName, Client.patrName)',
                                 u'birthDate'          :u'Client.birthDate',
                                 u'sex'                :u'Client.sex',
                                 u'directionDate'      :u'Action.directionDate',
                                 u'actionType_id'      :u'AT.name',
                                 u'duration'           :u'Action.duration',
                                 u'periodicity'        :u'Action.periodicity',
                                 u'aliquoticity'       :u'Action.aliquoticity',
                                 u'isUrgent'           :u'Action.isUrgent',
                                 u'status'             :u'Action.status',
                                 u'plannedEndDate'     :u'Action.plannedEndDate',
                                 u'begDate'            :u'Action.begDate',
                                 u'endDate'            :u'Action.endDate',
                                 u'setPerson_id'       :u'vrbSetPersonWithSpeciality.name',
                                 u'person_id'          :u'vrbPersonWithSpeciality.name',
                                 u'office'             :u'Action.office',
                                 u'note'               :u'Action.note',
                                 u'id'                 :u'ActionProperty_Job_Ticket.value'
                                 }


    def getOrder(self, fieldName, column):
        if hasattr(self._cols[column], 'extraFields'):
            if len(self._cols[column].extraFields) > 0:
                fieldName = self._cols[column].extraFields[0]
        return self._mapColumnToOrder[fieldName]


    def getEventId(self, row):
        if row is not None and row >= 0:
            record = self.getRecordByRow(row)
            return forceRef(record.value('event_id')) if record else None
        return None


    def getClientId(self, row):
        if row is not None and row >= 0:
            record = self.getRecordByRow(row)
            eventId = forceRef(record.value('event_id')) if record else None
            if eventId:
                db = QtGui.qApp.db
                tableEvent = db.table('Event')
                recordEvent = db.getRecordEx(tableEvent, [tableEvent['client_id']], [tableEvent['id'].eq(eventId), tableEvent['deleted'].eq(0)])
                return forceRef(recordEvent.value('client_id')) if recordEvent else None
        return None


    def headerData(self, section, orientation, role=Qt.DisplayRole):
        return CTableModel.headerData(self, section, orientation, role)


    def flags(self, index):
        enabled = True
        if enabled:
            return Qt.ItemIsEnabled|Qt.ItemIsSelectable
        else:
            return Qt.ItemIsSelectable


    def setTable(self, tableName):
        db = QtGui.qApp.db
        tableClient = db.table('Client')
        tableEvent = db.table('Event')
        tableAction = db.table('Action')
        loadFields = []
        loadFields.append(u'''Client.id AS clientId, CONCAT_WS(' ', Client.lastName, Client.firstName,
        Client.patrName) AS FIO, Client.birthDate, Client.sex, Action.id, Action.event_id,
        Action.directionDate, Action.isUrgent, Action.plannedEndDate,
        Action.begDate, Action.endDate, Action.actionType_id, Action.status, Action.setPerson_id,
        Action.person_id, Action.office, Action.note, Action.specifiedName, Action.duration,
        Action.periodicity, Action.aliquoticity''')
        queryTable = tableAction.leftJoin(tableEvent, tableAction['event_id'].eq(tableEvent['id']))
        queryTable = queryTable.leftJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
        self._table = queryTable
        self._recordsCache = CTableRecordCache(db, self._table, loadFields)


class CHospitalActionsTableModel(CAttendanceActionsTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.addColumn(CDateTimeFixedCol(u'Назначено',      ['directionDate'], 15))
        self.addColumn(CAttendanceActionsTableModel.CLocJobTicketColumn( u'Номерок', ['id'], 60))
        self.addColumn(CActionTypeCol(u'Действие', 15))
        self.addColumn(CBoolCol(u'Срочно',         ['isUrgent'],      15))
        self.addColumn(CIntCol(u'Д',               ['duration'],      15))
        self.addColumn(CIntCol(u'И',               ['periodicity'],   15))
        self.addColumn(CIntCol(u'К',               ['aliquoticity'],  15))
        self.addColumn(CEnumCol(u'Состояние',      ['status'], CActionStatus.names, 4))
        self.addColumn(CDateTimeFixedCol(u'Начато',     ['begDate'],       15))
        self.addColumn(CDateTimeFixedCol(u'Окончено',   ['endDate'],       15))
        self.addColumn(CDateTimeFixedCol(u'План',           ['plannedEndDate'],15))
        self.addColumn(CRefBookCol(u'Назначил',    ['setPerson_id'], 'vrbPersonWithSpeciality', 20))
        self.addColumn(CRefBookCol(u'Выполнил',    ['person_id'],    'vrbPersonWithSpeciality', 20))
        self.addColumn(CTextCol(u'Каб',            ['office'],                                6))
        self.addColumn(CTextCol(u'Примечания',     ['note'],                                  6))
        self.addColumn(CTextCol(u'Ф.И.О.', ['FIO'], 60))
        self.addColumn(CDateCol(u'Дата рожд.', ['birthDate'], 20, highlightRedDate=False))
        self.addColumn(CEnumCol(u'Пол', ['sex'], ['', u'М', u'Ж'], 5))
        self.setTable('Action')
        self.headerSortingCol = {}

    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.ToolTipRole:
                if section == 3:
                    return QVariant(u'Длительность курса лечения в днях.')
                elif section == 4:
                    return QVariant(u'''Интервал: 0 - каждый день,
                                        1 - через 1 день,
                                        2 - через 2 дня,
                                        3 - через 3 дня,
                                        и т.д.''')
                elif section == 5:
                    return QVariant(u'Сколько раз в сутки.')
        return CAttendanceActionsTableModel.headerData(self, section, orientation, role)


def getDateReceivedCol():
    db = QtGui.qApp.db
    table = db.table('Action').alias('AR')
    return '(SELECT MIN(`AR`.`endDate`) '\
            'FROM `Action` AS `AR` '\
            'WHERE `AR`.`event_id`=`Action`.`event_id` '\
            'AND `AR`.`deleted`=0 '\
            'AND %s '\
            'AND `AR`.`status`=2) AS begDateReceived' % table['actionType_id'].inlist(getActionTypeIdListByFlatCode(u'received%'))


def getDateLeavedCol():
    db = QtGui.qApp.db
    table = db.table('Action').alias('AL')
    return '(SELECT MAX(`AL`.`endDate`) '\
            'FROM `Action` AS `AL` '\
            'WHERE `AL`.`event_id`=`Action`.`event_id` '\
            'AND `AL`.`deleted`=0 '\
            'AND %s '\
            'AND `AL`.`status`=2) AS endDateLeaved' % table['actionType_id'].inlist(getActionTypeIdListByFlatCode(u'leaved%'))


def getDeliverByCond(deliverBy):
    cond = ''
    if deliverBy:
        if deliverBy == u'без уточнения':
            cond = ' is NULL '
        else:
            cond = '= \'%s\' ' % deliverBy
    else:
        'as \'deliveredBy\''
    return u'''
    (select APS.value from
            ActionType as AT
            left join Action as A on A.actionType_id = AT.id
            left join ActionPropertyType as APT on APT.actionType_id = AT.id
            left join ActionProperty AS AP on AP.type_id = APT.id
            left join ActionProperty_String AS APS ON APS.id = AP.id

            where AT.flatCode = 'received'
            and A.deleted = 0
            and A.event_id = Event.id
            and AP.action_id = A.id
            and AT.deleted = 0
            and APT.name = 'Кем доставлен') %s
    ''' % cond


def getPlacement():
    return u'''(SELECT
            OSP.name
        FROM
            ActionPropertyType AS APT
                INNER JOIN
            ActionProperty AS AP ON AP.type_id = APT.id
                INNER JOIN
            ActionProperty_OrgStructure_Placement AS APOS ON APOS.id = AP.id
                INNER JOIN
            OrgStructure_Placement as OSP on OSP.id = APOS.value
        WHERE
            (AP.action_id = Action.id)
                AND (APT.actionType_id = Action.actionType_id
                AND APT.deleted = 0
                AND APT.name = 'Помещение') LIMIT 1) as \'placement\' '''


def getPlacementCond(placement):
    placementCond = ('EXISTS',  'AND OSP.id = %i'%placement, '') if placement else ('', '', 'is NULL')
    return u'''%s(SELECT
            OSP.name
        FROM
            ActionPropertyType AS APT
                INNER JOIN
            ActionProperty AS AP ON AP.type_id = APT.id
                INNER JOIN
            ActionProperty_OrgStructure_Placement AS APOS ON APOS.id = AP.id
                INNER JOIN
            OrgStructure_Placement as OSP on OSP.id = APOS.value
        WHERE
            (AP.action_id = Action.id)
                %s
                AND (APT.actionType_id = Action.actionType_id
                AND APT.deleted = 0
                AND APT.name = 'Помещение')) %s ''' % (placementCond[0], placementCond[1], placementCond[2])


def getClientFeatures():
    return u'''(SELECT MAX(ClientAllergy.power) FROM ClientAllergy where Client.id=ClientAllergy.client_id) as clientAllergy,
                    (SELECT MAX(ClientIntoleranceMedicament.power) FROM ClientIntoleranceMedicament where Client.id=ClientIntoleranceMedicament.client_id) as clientIntoleranceMedicament'''


def getPatronFeatures():
    return u'''(SELECT MAX(ClientAllergy.power) FROM ClientAllergy where Event.relative_id=ClientAllergy.client_id) as patronAllergy,
                    (SELECT MAX(ClientIntoleranceMedicament.power) FROM ClientIntoleranceMedicament where Event.relative_id=ClientIntoleranceMedicament.client_id) as patronIntoleranceMedicament'''


def getStatusObservation():
    return '''(SELECT CONCAT_WS('|', IF(rbStatusObservationClientType.code IS NOT NULL, rbStatusObservationClientType.code, ''), IF(rbStatusObservationClientType.name IS NOT NULL, rbStatusObservationClientType.name, ''), IF(rbStatusObservationClientType.color IS NOT NULL, rbStatusObservationClientType.color, ''),
    CONCAT_WS(' ', DATE_FORMAT(Client_StatusObservation.createDatetime, '%d.%m.%Y'), TIME_FORMAT(Client_StatusObservation.createDatetime, '%H:%i:%S')), vrbPersonWithSpeciality.name)
FROM Client_StatusObservation
LEFT JOIN rbStatusObservationClientType ON rbStatusObservationClientType.id = Client_StatusObservation.statusObservationType_id
LEFT JOIN vrbPersonWithSpeciality ON vrbPersonWithSpeciality.id = Client_StatusObservation.createPerson_id
WHERE Client_StatusObservation.deleted = 0 AND Client_StatusObservation.master_id = Client.id
ORDER BY Client_StatusObservation.createDatetime DESC
LIMIT 0,1) AS statusObservation'''


def existsStatusObservation(statusObservation):
    return '''(SELECT Client_StatusObservation.statusObservationType_id
FROM Client_StatusObservation
WHERE Client_StatusObservation.deleted = 0 AND Client_StatusObservation.master_id = Client.id
ORDER BY Client_StatusObservation.createDatetime DESC
LIMIT 0,1 ) = %s''' % (str(statusObservation))


def getCurrentOSHB():
    return '''(SELECT CONCAT_WS('  ', OSHB.code, OSHB.name, IF(OSHB.sex=1, \'%s\', IF(OSHB.sex=2, \'%s\', ' ')))
FROM Action AS A
INNER JOIN ActionType AS AT ON AT.id=A.actionType_id
INNER JOIN ActionPropertyType AS APT ON APT.actionType_id=AT.id
INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id
INNER JOIN ActionProperty_HospitalBed AS APHB ON APHB.id=AP.id
INNER JOIN OrgStructure_HospitalBed AS OSHB ON OSHB.id=APHB.value
INNER JOIN OrgStructure AS OS ON OS.id=OSHB.master_id
WHERE (A.event_id=Event.id) AND (A.deleted=0) AND (AP.deleted=0) AND (OS.deleted=0)
AND (APT.typeName = 'HospitalBed') AND (AP.action_id=A.id)
AND (A.endDate IS NULL)
) AS bedCodeName'''%(forceString(u''' /М'''), forceString(u''' /Ж'''))


def getDataAPHB(permanent=0, type=0, profile=0, codeBeds=None):
    strFilter = u''''''
    strSelected = u''''''
    if permanent and permanent > 0:
        strFilter += u''' AND OSHB.isPermanent=%s'''%(forceString(permanent - 1))
    if type:
        strFilter += u''' AND OSHB.type_id=%s'''%(forceString(type))
    if codeBeds:
        strFilter += u''' AND OSHB.code %s '''%(updateLIKE(codeBeds))
    if profile:
        if QtGui.qApp.defaultHospitalBedProfileByMoving():
            strSelected = getHospitalBedProfile([profile]) + u''' AND '''
        else:
            strFilter += u''' AND OSHB.profile_id=%s'''%(forceString(profile))
    strSelected += '''EXISTS(SELECT APHB.value
FROM ActionPropertyType AS APT
INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id
INNER JOIN ActionProperty_HospitalBed AS APHB ON APHB.id=AP.id
INNER JOIN OrgStructure_HospitalBed AS OSHB ON OSHB.id=APHB.value
WHERE APT.actionType_id=Action.actionType_id AND AP.action_id=Action.id
AND AP.deleted=0 AND APT.deleted=0 AND APT.typeName = 'HospitalBed'%s)'''%(strFilter)
    return strSelected


def isScheduleBeds(scheduleId):
    return '''EXISTS(SELECT APHB.value
FROM ActionPropertyType AS APT
INNER JOIN ActionProperty AS AP ON AP.type_id = APT.id
INNER JOIN ActionProperty_HospitalBed AS APHB ON APHB.id = AP.id
INNER JOIN OrgStructure_HospitalBed AS OSHB ON OSHB.id = APHB.value
WHERE APT.actionType_id = Action.actionType_id AND AP.action_id = Action.id
AND AP.deleted = 0 AND APT.deleted = 0 AND APT.typeName = 'HospitalBed'
AND OSHB.schedule_id = %s)'''%(scheduleId)


def getHospitalBedProfile(profileList):
    return '''EXISTS(SELECT APHBP.value
FROM ActionPropertyType AS APT_Profile
INNER JOIN ActionProperty AS AP_Profile ON AP_Profile.type_id=APT_Profile.id
INNER JOIN ActionProperty_rbHospitalBedProfile AS APHBP ON APHBP.id=AP_Profile.id
INNER JOIN rbHospitalBedProfile AS RBHBP ON RBHBP.id=APHBP.value
WHERE APT_Profile.actionType_id = Action.actionType_id
AND AP_Profile.action_id = Action.id
AND AP_Profile.deleted = 0
AND APT_Profile.deleted = 0
AND APT_Profile.typeName = 'rbHospitalBedProfile'
AND APHBP.value IN (%s))'''%(','.join(str(profileId) for profileId in profileList if profileId))


def getOSHBP():
    return '''(SELECT RBHBP.name
FROM ActionPropertyType AS APT_Profile
INNER JOIN ActionProperty AS AP_Profile ON AP_Profile.type_id=APT_Profile.id
INNER JOIN ActionProperty_rbHospitalBedProfile AS APHBP ON APHBP.id=AP_Profile.id
INNER JOIN rbHospitalBedProfile AS RBHBP ON RBHBP.id=APHBP.value
WHERE APT_Profile.actionType_id = Action.actionType_id
AND AP_Profile.action_id = Action.id
AND AP_Profile.deleted = 0
AND APT_Profile.deleted = 0
AND APT_Profile.typeName = 'rbHospitalBedProfile'
LIMIT 1) as 'profileName'
'''

def getHBProfileFromBed():
    return '''(SELECT RBHBP.name
FROM ActionPropertyType AS APT_HB
INNER JOIN ActionProperty AS AP_HB ON AP_HB.type_id = APT_HB.id
INNER JOIN ActionProperty_HospitalBed AS APHB ON APHB.id = AP_HB.id
INNER JOIN OrgStructure_HospitalBed as OSHB ON OSHB.id = APHB.value
INNER JOIN rbHospitalBedProfile AS RBHBP ON RBHBP.id = OSHB.profile_id
WHERE APT_HB.actionType_id = Action.actionType_id
AND AP_HB.action_id = Action.id
AND AP_HB.deleted = 0
AND APT_HB.deleted = 0
AND APT_HB.typeName = 'HospitalBed'
LIMIT 1) as 'profileName'
'''

def getReceivedPropertyString(nameProperty, alias, actionTypeIdList):
    return u'''(SELECT APS.value
    FROM Event AS E
    INNER JOIN Action AS A ON A.event_id = E.id
    INNER JOIN ActionType AS AT ON AT.id=A.actionType_id
    INNER JOIN ActionPropertyType AS APT ON AT.id = APT.actionType_id
    INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id AND AP.action_id = A.id
    INNER JOIN ActionProperty_String AS APS ON APS.id=AP.id
    WHERE E.id = getActionReceivedFirstEventId(Event.id) AND E.deleted = 0 AND A.deleted = 0 AND AT.deleted = 0 AND AP.deleted = 0
    AND APT.deleted=0 AND APT.name %s AND A.actionType_id IN (%s) LIMIT 1) AS %s''' % (updateLIKE(nameProperty), ','.join(str(actionTypeId) for actionTypeId in actionTypeIdList if actionTypeId), alias)

def getHospitalBedProfileFromBed(profileList):
    return '''EXISTS(SELECT OSHB.profile_id
FROM ActionPropertyType AS APT_HB
INNER JOIN ActionProperty AS AP_HB ON AP_HB.type_id = APT_HB.id
INNER JOIN ActionProperty_HospitalBed AS APHB ON APHB.id = AP_HB.id
INNER JOIN OrgStructure_HospitalBed as OSHB ON OSHB.id = APHB.value
WHERE APT_HB.actionType_id = Action.actionType_id
AND AP_HB.action_id = Action.id
AND AP_HB.deleted = 0
AND APT_HB.deleted = 0
AND APT_HB.typeName = 'HospitalBed'
AND OSHB.profile_id IN (%s))'''%(','.join(str(profileId) for profileId in profileList if profileId))


def getDataClientQuoting(nameProperty, quotingTypeIdList):
    quotingTypeList = [u'NULL']
    for quotingTypeId in quotingTypeIdList:
        quotingTypeList.append(forceString(quotingTypeId))
    return '''EXISTS(SELECT APOS.value
    FROM ActionPropertyType AS APT
    INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id
    INNER JOIN ActionProperty_Client_Quoting AS APOS ON APOS.id=AP.id
    INNER JOIN Client_Quoting AS CQ ON CQ.id=APOS.value
    INNER JOIN QuotaType AS QT ON CQ.quotaType_id=QT.id
    WHERE APT.actionType_id=Action.actionType_id AND AP.action_id=Action.id
    AND APT.deleted=0 AND QT.deleted = 0
    AND APT.name %s AND CQ.deleted=0
    AND QT.id %s)'''%(updateLIKE(nameProperty), u' IN ('+(','.join(quotingTypeList))+')')


def getActionPropertyTypeName(nameProperty):
    return '''EXISTS(SELECT APT.id
FROM ActionPropertyType AS APT
INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id
INNER JOIN ActionProperty_OrgStructure AS APOS ON APOS.id=AP.id
WHERE (AP.action_id=Action.id)
AND (APT.actionType_id=Action.actionType_id AND APT.deleted=0 AND APT.name %s))'''%(updateLIKE(nameProperty))


def getEventFeedId(typeFeed, dateFeed, alias=u'', refusalToEat = -1):
    return u'''EXISTS(SELECT EF.id
    FROM Event_Feed AS EF
    WHERE EF.event_id = Action.event_id AND EF.deleted = 0%s%s
    AND DATE(EF.date) = %s%s)%s'''%(u' AND EF.typeFeed = %s' % (typeFeed) if typeFeed else u'',
    u' AND EF.refusalToEat = %s'%(refusalToEat) if refusalToEat > -1 else u'',
    dateFeed,
    u' ORDER BY EF.refusalToEat DESC' if refusalToEat > -1 else u'',
    alias)


def getDietCode(typeFeed, dateFeed, alias=u'', refusalToEat = -1):
    return u'''(SELECT rbDiet.code
    FROM Event_Feed AS EF
    INNER JOIN rbDiet ON rbDiet.id = EF.diet_id
    WHERE EF.id = (SELECT MAX(EF2.id)
               FROM Event_Feed AS EF2
               WHERE EF2.event_id = Action.event_id AND EF2.deleted = 0%s%s
    AND DATE(EF2.date) = %s%s))%s'''%(u' AND EF2.typeFeed = %s' % (typeFeed) if typeFeed else u'',
    u' AND EF2.refusalToEat = %s'%(refusalToEat) if refusalToEat > -1 else u'',
    dateFeed,
    u' ORDER BY EF2.refusalToEat DESC' if refusalToEat > -1 else u'',
    alias)


def getEventRefusalToEat(typeFeed, dateFeed, alias=u''):
    return u'''(SELECT EF.refusalToEat
    FROM Event_Feed AS EF
    WHERE EF.event_id = Action.event_id AND EF.deleted = 0%s
    AND DATE(EF.date) = %s
    ORDER BY EF.refusalToEat DESC
    LIMIT 1)%s'''%(u' AND EF.typeFeed = %s' % (typeFeed) if typeFeed else u'', dateFeed, alias)


def getPropertyAPOS(nameProperty, actionTypeIdList):
    return u'''(EXISTS(SELECT APOS.value
    FROM Event AS E
    INNER JOIN Action AS A ON A.event_id = E.id
    INNER JOIN ActionType AS AT ON AT.id=A.actionType_id
    INNER JOIN ActionPropertyType AS APT ON AT.id = APT.actionType_id
    INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id AND AP.action_id = A.id
    INNER JOIN ActionProperty_OrgStructure AS APOS ON APOS.id=AP.id
    WHERE E.client_id = Event.client_id AND E.deleted = 0 AND A.deleted = 0 AND AT.deleted = 0 AND AP.deleted = 0
    AND A.endDate IS NOT NULL AND (Action.plannedEndDate IS NULL OR (DATE(A.begDate) <= DATE(Action.plannedEndDate)
    AND DATE(Action.plannedEndDate) <= DATE(A.endDate))) AND APT.deleted=0 AND APT.name %s
    AND A.actionType_id IN (%s))) AS APOS_value'''%(updateLIKE(nameProperty), ','.join(str(actionTypeId) for actionTypeId in actionTypeIdList if actionTypeId))


def getReceivedEndDate(nameProperty, actionTypeIdList):
    return u'''(SELECT A.endDate
    FROM Event AS E
    INNER JOIN Action AS A ON A.event_id = E.id
    INNER JOIN ActionType AS AT ON AT.id=A.actionType_id
    INNER JOIN ActionPropertyType AS APT ON AT.id = APT.actionType_id
    INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id AND AP.action_id = A.id
    INNER JOIN ActionProperty_OrgStructure AS APOS ON APOS.id=AP.id
    WHERE E.id = getActionReceivedFirstEventId(Event.id) AND E.deleted = 0 AND A.deleted = 0 AND AT.deleted = 0 AND AP.deleted = 0 AND APOS.value IS NOT NULL
    AND APT.deleted=0 AND APT.name %s AND A.actionType_id IN (%s) LIMIT 1) AS receivedEndDate'''%(updateLIKE(nameProperty),
    ','.join(str(actionTypeId) for actionTypeId in actionTypeIdList if actionTypeId))


def getReceivedBegDate(actionTypeIdList):
    return u'''(SELECT MIN(A.begDate) begDate
    FROM Event AS E
    INNER JOIN Action AS A ON A.event_id = E.id
    WHERE E.id = getActionReceivedFirstEventId(Event.id) AND E.deleted = 0 AND A.deleted = 0
    AND A.actionType_id IN (%s)
    /*ORDER BY A.begDate LIMIT 1*/) AS receivedBegDate''' % (','.join(str(actionTypeId) for actionTypeId in actionTypeIdList if actionTypeId))


def getLeavedEndDate(actionTypeIdList):
    return u'''(SELECT MAX(A.endDate) endDate
    FROM Event AS E
    INNER JOIN Action AS A ON A.event_id = E.id
    WHERE E.id = getActionLeavedLastEventId(Event.id) AND E.deleted = 0 AND A.deleted = 0
    AND A.actionType_id IN (%s)
    /*ORDER BY A.endDate LIMIT 1*/) AS leavedEndDate''' % (','.join(str(actionTypeId) for actionTypeId in actionTypeIdList if actionTypeId))


def getActionByFlatCode(actionTypeIdList):
    db = QtGui.qApp.db
    tableAction = db.table('Action')
    return '''(SELECT CONCAT_WS('  ', A.plannedEndDate, A.payStatus)
FROM Action AS A
WHERE A.event_id = Event.id AND A.actionType_id IN (%s) AND A.deleted=0 AND A.plannedEndDate >= %s
ORDER BY A.plannedEndDate ASC
LIMIT 1) AS comfortable'''%(u', '.join(str(actionTypeId) for actionTypeId in actionTypeIdList if actionTypeId) , tableAction['begDate'].formatValue(QDateTime().currentDateTime()))


def getMovingActionForPlannedDate(actionTypeIdList):
    return u'''(SELECT A.id
    FROM Event AS E
    INNER JOIN Action AS A ON A.event_id = E.id
    WHERE E.client_id = Event.client_id AND E.deleted = 0 AND A.deleted = 0
    AND A.begDate IS NOT NULL AND (DATE(A.begDate) <= DATE(Action.plannedEndDate)
    AND DATE(Action.endDate) <= DATE(A.begDate))
    AND A.actionType_id IN (%s)
    ORDER BY A.begDate ASC
    LIMIT 1) AS movingActionId'''%(','.join(str(actionTypeId) for actionTypeId in actionTypeIdList if actionTypeId))


def isPlanningToHospitalization():
    return u'''EXISTS(SELECT E.id
    FROM Event AS E
    INNER JOIN EventType AS ET ON ET.id = E.eventType_id
    WHERE E.prevEvent_id = Action.event_id AND E.deleted = 0 AND ET.deleted = 0
    AND Action.deleted = 0 AND (ET.medicalAidType_id IN (SELECT MAT.id from rbMedicalAidType AS MAT where MAT.code IN ('1', '2', '3', '7')))
    )'''


class CReportF001SetupDialog(QtGui.QDialog, Ui_ReportF001SetupDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)


    def setParams(self, params):
        self.cmbCondSort.setCurrentIndex(params.get('condSort', 0))
        self.cmbCondOrgStructure.setCurrentIndex(params.get('condOrgStructure', 0))


    def params(self):
        result = {}
        result['condsort'] = self.cmbCondSort.currentIndex()
        result['condorgstructure'] = self.cmbCondOrgStructure.currentIndex()
        return result


class CHospitalizationExecDialog(QtGui.QDialog, Ui_HospitalizationExecDialog):
    def __init__(self, eventId, parent = None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.edtExecDate.setFocus(Qt.OtherFocusReason)
        self.edtExecDate.setDate(QDate().currentDate())
        self.edtExecTime.setTime(QTime().currentTime())
        db = QtGui.qApp.db
        tableAT = db.table('ActionType')
        tableAP = db.table('ActionPropertyType')
        table = tableAT.leftJoin(tableAP, tableAT['id'].eq(tableAP['actionType_id']))
        cond = [tableAT['deleted'].eq(0),
                    tableAT['flatCode'].eq('leaved'),
                    tableAP['deleted'].eq(0),
                    tableAP['name'].like(u'Исход госпитализации'),
                    tableAP['typeName'].eq('String')
                ]
        record = db.getRecordEx(table, 'valueDomain', cond)
        self.values = []
        if record:
            values = forceString(record.value(0))
            self.values = values.replace('\'', '').split(',')
            self.values.insert(0, '')
            self.cmbExec.insertItems(0, self.values)

        self.cmbMesSpecification.setTable('rbMesSpecification')
        tableEvent = db.table('Event')
        record = db.getRecordEx(tableEvent, [tableEvent['MES_id'].name(), tableEvent['mesSpecification_id'].name(), tableEvent['execPerson_id'].name()],
                                                [tableEvent['id'].eq(eventId)])
        if record:
            self.cmbMes.setValue(forceRef(record.value(0)))
            self.cmbMesSpecification.setValue(forceRef(record.value(1)))
            self.cmbPerson.setValue(forceRef(record.value('execPerson_id')))

        currentOrgId = QtGui.qApp.currentOrgId()
        currentOrgStructureId = QtGui.qApp.currentOrgStructureId()
        if currentOrgStructureId:
            self.cmbPerson.setOrganisationId(currentOrgId)
            self.cmbPerson.setOrgStructureId(currentOrgStructureId)


    def params(self):
        result = {}
        date = self.edtExecDate.date()
        time = self.edtExecTime.time()
        result['ExecDateTime'] = QDateTime(date, QTime(time.hour(), time.minute()))
        result['ExecPerson'] = self.cmbPerson.value()
        result['ExecResult'] = self.values[self.cmbExec.currentIndex()]
        result['mesId'] = self.cmbMes.value()
        result['mesSpecification'] = self.cmbMesSpecification.value()
        if self.edtTransferTo.isEnabled():
            result['transferTo'] = self.edtTransferTo.text()
        return result


    @pyqtSignature('QString')
    def on_cmbExec_currentIndexChanged(self, string):
        flag = string.contains(QString(u'другой стационар'))
        self.lblTransferTo.setEnabled(flag)
        self.edtTransferTo.setEnabled(flag)
        self.btnSelectTransferToOrganisation.setEnabled(flag)


    @pyqtSignature('')
    def on_btnSelectTransferToOrganisation_clicked(self):
        orgId = selectOrganisation(self, None, False, filter='isMedical != 0')
        if orgId:
            self.edtTransferTo.setText(getOrganisationShortName(orgId))


    def done(self, r):
        if r > 0:
            dateTime = QDateTime(self.edtExecDate.date(), self.edtExecTime.time())
            if dateTime > QDateTime().currentDateTime():
                messageBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning,
                                               u'Внимание!',
                                               u'Вы указали будущее время для данного Действия!',
                                               QtGui.QMessageBox.Ok | QtGui.QMessageBox.Ignore)
                messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
                res = messageBox.exec_()
                if res == QtGui.QMessageBox.Ok:
                    self.edtExecDate.setFocus(Qt.ShortcutFocusReason)
                    return
            if self.edtTransferTo.isEnabled():
                if self.edtTransferTo.text() == u'':
                    messageBox = QtGui.QMessageBox(QtGui.QMessageBox.Critical,
                                                   u'Внимание!',
                                                   u'Необходимо заполнить поле "Переведен в стационар".',
                                                   QtGui.QMessageBox.Ok)
                    messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
                    messageBox.exec_()
                    return
        QtGui.QDialog.done(self, r)


class CHBPatronEditorDialog(QtGui.QDialog, Ui_HBPatronEditorDialog):
    def __init__(self, parent = None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)

    def setClientId(self, clientId):
        self.cmbPatron.setClientId(clientId)

    def setCurrentPatronId(self, patronId):
        self.cmbPatron.setValue(patronId)

    def getPatronId(self):
        return self.cmbPatron.value()


def updateDurationEvent(begDate, endDate, begDateFilter, endDateFilter, eventTypeId, isPresence):
    def getWeekProfile(index):
            return {0: wpFiveDays,
             1: wpSixDays,
             2: wpSevenDays}.get(index, wpSevenDays)

    if not endDate:
        if isPresence:
            endDate = endDateFilter.date() if endDateFilter else QDate().currentDate()
        else:
            endDate = QDate().currentDate()
    text = '-'
    weekProfile = getWeekProfile(CEventTypeDescription.get(eventTypeId).weekProfileCode)
    if begDate:
        duration = getEventDuration(begDate, endDate, weekProfile, eventTypeId)
        if duration > 0:
            text = str(duration)
    return text


def getReceivedMKB():
    return '''(SELECT Diagnosis.MKB
FROM Diagnosis INNER JOIN Diagnostic ON Diagnostic.diagnosis_id=Diagnosis.id
INNER JOIN rbDiagnosisType ON Diagnostic.diagnosisType_id=rbDiagnosisType.id
WHERE Diagnostic.event_id = Event.id AND Diagnosis.deleted = 0 AND Diagnostic.deleted = 0
AND (rbDiagnosisType.code = '1'
OR (rbDiagnosisType.code = '2' AND Diagnostic.person_id = Event.execPerson_id
AND (NOT EXISTS (SELECT DC.id FROM Diagnostic AS DC
INNER JOIN rbDiagnosisType AS DT ON DT.id = DC.diagnosisType_id WHERE DT.code = '1'
AND DC.event_id = Event.id AND DC.deleted = 0
LIMIT 1)))
OR (rbDiagnosisType.code = '7' AND Diagnostic.person_id = Event.execPerson_id
AND (NOT EXISTS (SELECT DC.id FROM Diagnostic AS DC
INNER JOIN rbDiagnosisType AS DT ON DT.id = DC.diagnosisType_id WHERE DT.code = '1'
AND DC.event_id = Event.id AND DC.deleted = 0
LIMIT 1)) AND (NOT EXISTS (SELECT DC.id FROM Diagnostic AS DC
INNER JOIN rbDiagnosisType AS DT ON DT.id = DC.diagnosisType_id WHERE DT.code = '2'
AND DC.event_id = Event.id AND DC.deleted = 0
LIMIT 1))))
ORDER BY Diagnosis.id
LIMIT 1) AS MKB'''


def isContractPropertyValue(nameProperty, value):
    return u'''EXISTS(SELECT APC.id
    FROM ActionProperty AS AP
    INNER JOIN ActionPropertyType AS APT ON AP.type_id = APT.id
    INNER JOIN ActionProperty_Contract AS APC ON APC.id = AP.id
    INNER JOIN Contract AS C ON C.id = APC.value
    WHERE AP.action_id = Action.id AND APT.actionType_id = Action.actionType_id
    AND  Action.id IS NOT NULL AND C.deleted = 0 AND Action.deleted = 0
    AND APT.deleted=0 AND AP.deleted=0 AND APT.name %s AND APC.value = %s
    )'''%(updateLIKE(nameProperty), value)
