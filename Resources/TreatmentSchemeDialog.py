# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2017 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
##
## План цикла
##
#############################################################################

import math
from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDateTime, QModelIndex, QVariant, pyqtSignature, SIGNAL, QAbstractTableModel

from Events.ActionTypeListDialog import CActionTypeListDialog
from Events.ActionProperty.JobTicketActionPropertyValueType import CJobTicketActionPropertyValueType
from Orgs.OrgStructureListDialog import COrgStructureListDialog
from library.database         import CTableRecordCache
from library.ItemsListDialog  import CItemEditorBaseDialog
from library.Utils            import pyDateTime, forceDate, forceTime, forceInt, forceRef, forceString, toVariant, forceDateTime, forceStringEx, pyDate, getPref, setPref
from library.DialogBase       import CDialogBase
from library.TableModel import CTableModel, CRefBookCol, CDateCol, CCol
from library.PreferencesMixin import CDialogPreferencesMixin
from Resources.Utils          import TreatmentScheduleMinimumDuration

from Ui_TreatmentSchemeDialog  import Ui_TreatmentSchemeDialog
from Ui_TreatmentSchemeTypeDialog import Ui_TreatmentSchemeTypeDialog


class CTreatmentSchemeDialog(CItemEditorBaseDialog, Ui_TreatmentSchemeDialog, CDialogPreferencesMixin):
    def __init__(self, parent):
        CItemEditorBaseDialog.__init__(self, parent, 'TreatmentScheme')
        self.addModels('TreatmentScheme', CTreatmentSchemeModel(self))
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setWindowTitleEx(u'План цикла')
        self.setOrgStructureCache()
        self.params = {}
        self.tblTreatmentScheme.setModel(self.modelTreatmentScheme)
        self.cmbTreatmentType.setTable('TreatmentType')
        self.modelTreatmentScheme.setEventEditor(self)
        self.loadDialogPreferences()


    def done(self, result):
        preferences = self.tblTreatmentScheme.savePreferences()
        setPref(QtGui.qApp.preferences.windowPrefs, 'tblTreatmentSchemeDialog', preferences)
        return CItemEditorBaseDialog.done(self, result)


    def setOrgStructureCache(self):
        db = QtGui.qApp.db
        self.orgStructureCache = CTableRecordCache(db, db.forceTable('OrgStructure'), u'*', capacity=None)


    def destroy(self):
        pass


    @pyqtSignature('QModelIndex')
    def on_tblTreatmentScheme_doubleClicked(self, index):
        self.updateTreatmentScheme(index)


    @pyqtSignature('QModelIndex')
    def on_tblTreatmentScheme_clicked(self, index):
        self.updateTreatmentScheme(index)


    def updateTreatmentScheme(self, index):
        if index.isValid():
            row = index.row()
            column = index.column()
            if column > 0 and row >= 0 and row < len(self.modelTreatmentScheme.dates):
                datetimePrev, datetimeLast = self.modelTreatmentScheme.dates[row]
                header = self.modelTreatmentScheme.headers[column]
                if datetimePrev and datetimeLast and header and header[0]:
                    if header and header[0] and (((pyDateTime(datetimePrev), pyDateTime(datetimeLast)), header[0]) in self.modelTreatmentScheme.items.keys()):
                        orgStructureIdList = []
                        dialog = COrgStructureListDialog(self, filter='OrgStructure.hasHospitalBeds = 1')
                        try:
                            data = self.modelTreatmentScheme.data(index, Qt.EditRole)
                            dialog.setValues(data.toList())
                            if dialog.exec_():
                                dialog.getOrgStructureList()
                                orgStructureIdList = dialog.values()
                                self.modelTreatmentScheme.setData(index, toVariant(orgStructureIdList))
                        finally:
                            dialog.deleteLater()


    def getActionTypeIdList(self):
        actionTypeIdList = []
        dialog = CActionTypeListDialog(self, filter=u'isUsesCycles = 1')
        try:
            if dialog.exec_():
                dialog.getCheckedIdList()
                actionTypeIdList = dialog.values()
        finally:
            dialog.deleteLater()
        return actionTypeIdList


    def getParams(self):
        params = {}
        params['begDate'] = self.edtBegDate.date()
        params['endDate'] = self.edtEndDate.date()
        params['treatmentTypeId'] = self.cmbTreatmentType.value()
        params['actionTypeIdList'] = self.getActionTypeIdList()
        return params


    def checkDataEntered(self):
        return True


    def loadData(self):
        self.params = self.getParams()
        actionTypeIdList = self.params.get('actionTypeIdList', None)
        if actionTypeIdList:
            self.modelTreatmentScheme.loadItems(self.params, self.orgStructureCache)
            self.treatmentSchemeSpan()


    def treatmentSchemeSpan(self):
        headers = self.modelTreatmentScheme.headers
        dates = self.modelTreatmentScheme.dates
        items = self.modelTreatmentScheme.items
        for column, header in enumerate(headers):
            for row, (datetimePrev, datetimeLast) in enumerate(dates):
                if header and header[0] and (((pyDateTime(datetimePrev), pyDateTime(datetimeLast)), header[0]) in items.keys()):
                    item = items.get(((pyDateTime(datetimePrev), pyDateTime(datetimeLast)), header[0]), None)
                    if item and item[3]:
                        duration = item[3]
                        rowSpanCount = math.ceil(float(duration/self.modelTreatmentScheme.minimumDuration))
                        self.tblTreatmentScheme.setSpan(row, column, rowSpanCount, 1)


    def saveData(self):
        self.modelTreatmentScheme.saveItems(self.params)
        return True


    @pyqtSignature('')
    def on_btnGenerate_clicked(self):
        if not self.edtBegDate.date():
            self.checkValueMessage(u'Требуется указать Дату начала!', False, self.edtBegDate)
            return
        if not self.edtEndDate.date():
            self.checkValueMessage(u'Требуется указать Дату окончания!', False, self.edtEndDate)
            return
        if not self.cmbTreatmentType.value():
            self.checkValueMessage(u'Требуется указать цикл!', False, self.cmbTreatmentType)
            return
        self.loadData()
        self.tblTreatmentScheme.loadPreferences(getPref(QtGui.qApp.preferences.windowPrefs, 'tblTreatmentSchemeDialog', {}))


    @pyqtSignature('')
    def on_btnTreatmentHistory_clicked(self):
        treatmentSchemeId = None
        actionTypeIdList = []
        begDate = self.edtBegDate.date()
        endDate = self.edtEndDate.date()
        db = QtGui.qApp.db
        tableTreatmentScheme = db.table('TreatmentScheme')
        tableTreatmentType = db.table('TreatmentType')
        tableJob = db.table('Job')
        tableJobTicket = db.table('Job_Ticket')
        tableRBJobType = db.table('rbJobType')
        tableActionType = db.table('ActionType')
        tableActionPropertyType = db.table('ActionPropertyType')
        treatmentSchemeDict = {}
        recordsSchemeDict = {}
        selectTreatmentSchemeIdList = []
        cond = [tableActionType['deleted'].eq(0),
                tableActionPropertyType['deleted'].eq(0),
                tableActionPropertyType['typeName'].like(CJobTicketActionPropertyValueType.name),
                tableActionPropertyType['valueDomain'].isNotNull(),
                tableTreatmentScheme['actionType_id'].isNotNull(),
                tableJob['deleted'].eq(0),
                tableJobTicket['deleted'].eq(0),
                tableJobTicket['datetime'].dateLe(endDate),
                tableActionPropertyType['actionType_id'].eq(tableTreatmentScheme['actionType_id']),
                tableTreatmentScheme['endDate'].dateGe(begDate)
                ]
        queryTable = tableActionType.innerJoin(tableActionPropertyType, tableActionPropertyType['actionType_id'].eq(tableActionType['id']))
        queryTable = queryTable.innerJoin(tableRBJobType, u'''rbJobType.code = IF(INSTR(ActionPropertyType.valueDomain, ';') > 0,
        LEFT(ActionPropertyType.valueDomain, INSTR(ActionPropertyType.valueDomain, ';')-1), ActionPropertyType.valueDomain)''')
        queryTable = queryTable.innerJoin(tableJob, tableJob['jobType_id'].eq(tableRBJobType['id']))
        queryTable = queryTable.innerJoin(tableJobTicket, tableJobTicket['master_id'].eq(tableJob['id']))
        queryTable = queryTable.innerJoin(tableTreatmentScheme, tableTreatmentScheme['jobTicket_id'].eq(tableJobTicket['id']))
        queryTable = queryTable.innerJoin(tableTreatmentType, tableTreatmentType['id'].eq(tableTreatmentScheme['treatmentType_id']))
        cols = [u'DISTINCT DATE(Job_Ticket.datetime) AS begDate',
                tableTreatmentScheme['treatmentType_id'],
                tableTreatmentScheme['id'],
                tableTreatmentScheme['endDate'],
                tableTreatmentType['name'].alias('treatmentTypeName'),
                tableTreatmentScheme['actionType_id']
                ]
        order = [u'begDate, endDate, treatmentTypeName']
        records = db.getRecordList(queryTable, cols, cond, order)
        for record in records:
            treatmentSchemeId = forceRef(record.value('id'))
            treatmentTypeId = forceRef(record.value('treatmentType_id'))
            actionTypeId = forceRef(record.value('actionType_id'))
            begDateScheme = pyDate(forceDate(record.value('begDate')))
            endDateScheme = pyDate(forceDate(record.value('endDate')))
            if treatmentSchemeId and actionTypeId:
                if actionTypeId and actionTypeId not in actionTypeIdList:
                    actionTypeIdList.append(actionTypeId)
                if (treatmentTypeId, (begDateScheme, endDateScheme)) not in treatmentSchemeDict.keys() and treatmentSchemeId not in selectTreatmentSchemeIdList:
                    selectTreatmentSchemeIdList.append(treatmentSchemeId)
                treatmentSchemeLine = treatmentSchemeDict.get((treatmentTypeId, (begDateScheme, endDateScheme)), {})
                if treatmentSchemeId not in treatmentSchemeLine.keys():
                    treatmentSchemeLine[treatmentSchemeId] = record
                    treatmentSchemeDict[(treatmentTypeId, (begDateScheme, endDateScheme))] = treatmentSchemeLine
                if treatmentSchemeId not in recordsSchemeDict.keys():
                    recordsSchemeDict[treatmentSchemeId] = record
        if selectTreatmentSchemeIdList:
            try:
                dialog = CTreatmentSchemeTypeDialogTableModel(self, selectTreatmentSchemeIdList, recordsSchemeDict, treatmentSchemeDict)
                dialog.setWindowTitle(u'История')
                if dialog.exec_():
                    treatmentSchemeId = dialog.currentItemId()
                    if treatmentSchemeId:
                        cond = [tableActionType['deleted'].eq(0),
                                tableActionType['isUsesCycles'].eq(1)
                                ]
                        actionTypeIdList = db.getDistinctIdList(tableActionType, 'id', cond, order=u'ActionType.code ASC, ActionType.name ASC')
                        if actionTypeIdList:
                            recordScheme = recordsSchemeDict.get(treatmentSchemeId, None)
                            if recordScheme:
                                self.edtBegDate.setDate(forceDate(recordScheme.value('begDate')))
                                self.edtEndDate.setDate(forceDate(recordScheme.value('endDate')))
                                self.cmbTreatmentType.setValue(forceRef(recordScheme.value('treatmentType_id')))
            finally:
                dialog.deleteLater()
            if treatmentSchemeId and actionTypeIdList:
                if not self.edtBegDate.date():
                    self.checkValueMessage(u'Требуется указать Дату начала!', False, self.edtBegDate)
                    return
                if not self.edtEndDate.date():
                    self.checkValueMessage(u'Требуется указать Дату окончания!', False, self.edtEndDate)
                    return
                if not self.cmbTreatmentType.value():
                    self.checkValueMessage(u'Требуется указать цикл!', False, self.cmbTreatmentType)
                    return
                params = {}
                params['begDate'] = self.edtBegDate.date()
                params['endDate'] = self.edtEndDate.date()
                params['treatmentTypeId'] = self.cmbTreatmentType.value()
                params['actionTypeIdList'] = actionTypeIdList
                self.modelTreatmentScheme.loadTreatmentHistoryItems(params, self.orgStructureCache, treatmentSchemeId, treatmentSchemeDict, recordsSchemeDict)
                self.treatmentSchemeSpan()
                self.tblTreatmentScheme.loadPreferences(getPref(QtGui.qApp.preferences.windowPrefs, 'tblTreatmentSchemeDialog', {}))


class CTreatmentSchemeModel(QAbstractTableModel):
    def __init__(self, parent):
        QAbstractTableModel.__init__(self, parent)
        self.headers = []
        self.items = {}
        self.sourceItems = {}
        self.dates = []
        self.actionTypeIdList = []
        self.readOnly = False
        self.quantityMax = 0
        self.quantityDict = {}
        self.minimumDuration = TreatmentScheduleMinimumDuration
        self.orgStructureCache = {}
        self.treatmentSchemeDict = {}
        self.recordsSchemeDict = {}
        self.treatmentSchemeIdList = []
        self.treatmentSchemeSourceIdList = []
        self.eventEditor = None
        self.showCodeNameOS = ['name', 'code'][forceInt(QtGui.qApp.preferences.appPrefs.get('showOrgStructureForTreatment', 0))]


    def items(self):
        return self.items


    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor


    def setReadOnly(self, value):
        self.readOnly = value


    def columnCount(self, index = None):
        return len(self.headers)


    def rowCount(self, index = None):
        return len(self.dates)-1


    def flags(self, index = QModelIndex()):
        column = index.column()
        if self.readOnly or column == 0:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        row = index.row()
        if row >= 0 and row < len(self.dates):
            if column != 0:
                datetimePrev, datetimeLast = self.dates[row]
                header = self.headers[column]
                if datetimePrev and datetimeLast and header and header[0]:
                    if header and header[0] and (((pyDateTime(datetimePrev), pyDateTime(datetimeLast)), header[0]) in self.items.keys()):
                        return Qt.ItemIsSelectable|Qt.ItemIsEnabled|Qt.ItemIsEditable
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled


    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                header = self.headers[section]
                if header:
                    return QVariant(header[1])
        return QVariant()


    def loadHeader(self):
        self.headers = [[None, u'Сеансы']]
        if self.actionTypeIdList:
            db = QtGui.qApp.db
            tableActionType = db.table('ActionType')
            tableActionPropertyType = db.table('ActionPropertyType')
            tableRBJobType = db.table('rbJobType')
            queryTable = tableActionType.innerJoin(tableActionPropertyType, tableActionPropertyType['actionType_id'].eq(tableActionType['id']))
            queryTable = queryTable.innerJoin(tableRBJobType, u'''rbJobType.code = IF(INSTR(ActionPropertyType.valueDomain, ';') > 0,
            LEFT(ActionPropertyType.valueDomain, INSTR(ActionPropertyType.valueDomain, ';')-1), ActionPropertyType.valueDomain)''')
            cond = [tableActionType['deleted'].eq(0),
                    tableActionPropertyType['deleted'].eq(0),
                    tableActionPropertyType['typeName'].like(CJobTicketActionPropertyValueType.name),
                    tableActionPropertyType['valueDomain'].isNotNull(),
                    tableActionType['isUsesCycles'].eq(1)
                    ]
            if self.actionTypeIdList:
                cond.append(tableActionType['id'].inlist(self.actionTypeIdList))
            cols = [tableActionType['id'],
                    tableActionType['name']
                    ]
            records = db.getRecordList(queryTable, cols, cond, order='ActionType.code, ActionType.name')
            for record in records:
                header = [forceRef(record.value('id')),
                          forceString(record.value('name'))
                          ]
                self.headers.append(header)
        self.reset()


    def getOrgStructureShowNameList(self, item):
        showNameList = []
        for i in item:
            orgStructureId = forceRef(i.value('orgStructure_id'))
            if orgStructureId:
                record = self.orgStructureCache.get(orgStructureId)
                if record:
                    showNameList.append(forceStringEx(record.value(self.showCodeNameOS)))
        return showNameList


    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if role == Qt.DisplayRole:
            if row < len(self.dates)-1:
                datetimePrev, datetimeLast = self.dates[row]
                if column == 0:
                    if datetimePrev and datetimeLast:
                        timePrev = datetimePrev.time()
                        timeLast = datetimeLast.time()
                        return QVariant(timePrev.toString('hh:mm') + u' - ' + timeLast.toString('hh:mm'))
                else:
                    if self.headers[column] and self.headers[column][0] and (((pyDateTime(datetimePrev), pyDateTime(datetimeLast)), self.headers[column][0]) in self.items.keys()):
                        keyScheme = ((pyDateTime(datetimePrev), pyDateTime(datetimeLast)), self.headers[column][0])
                        item = self.sourceItems.get(keyScheme, None)
                        if item:
                            showNameList = self.getOrgStructureShowNameList(item)
                            return toVariant(u','.join(i for i in showNameList))
        elif role == Qt.EditRole:
            if row < len(self.dates)-1:
                datetimePrev, datetimeLast = self.dates[row]
                if column == 0:
                    if datetimePrev and datetimeLast:
                        timePrev = datetimePrev.time()
                        timeLast = datetimeLast.time()
                        return QVariant(timePrev.toString('hh:mm') + u' - ' + timeLast.toString('hh:mm'))
                else:
                    if self.headers[column] and self.headers[column][0] and (((pyDateTime(datetimePrev), pyDateTime(datetimeLast)), self.headers[column][0]) in self.items.keys()):
                        keyScheme = ((pyDateTime(datetimePrev), pyDateTime(datetimeLast)), self.headers[column][0])
                        item = self.sourceItems.get(keyScheme, None)
                        if item:
                            showNameList = self.getOrgStructureShowNameList(item)
                            return toVariant(u','.join(i for i in showNameList))
        elif role == Qt.BackgroundRole:
            if row >= 0 and row < len(self.dates)-1:
                if column == 0:
                    return QVariant(QtGui.QColor(Qt.white))
                else:
                    datetimePrev, datetimeLast = self.dates[row]
                    header = self.headers[column]
                    if datetimePrev and datetimeLast and header and header[0]:
                        if header and header[0] and (((pyDateTime(datetimePrev), pyDateTime(datetimeLast)), header[0]) in self.items.keys()):
                            return QVariant(QtGui.QColor(Qt.white))
            return QVariant(QtGui.QColor(Qt.gray))
        return QVariant()


    def loadTreatmentHistoryItems(self, params, orgStructureCache, treatmentSchemeId, treatmentSchemeDict, recordsSchemeDict):
        self.orgStructureCache = orgStructureCache
        begDate = params.get('begDate', None)
        endDate = params.get('endDate', None)
        treatmentTypeId = params.get('treatmentTypeId', None)
        self.actionTypeIdList = params.get('actionTypeIdList', [])
        self.items = {}
        self.dates = []
        self.quantityMax = 0
        self.quantityDict = {}
        self.sourceItems = {}
        self.minimumDuration = TreatmentScheduleMinimumDuration
        actionTypeIdHeader = []
        treatmentSchemeIdList = []
        datetimeMin = None
        datetimeMax = None
        self.loadHeader()
        if treatmentSchemeId and treatmentSchemeDict and recordsSchemeDict and begDate and endDate and treatmentTypeId and self.actionTypeIdList and len(self.headers) > 1:
            for i, header in enumerate(self.headers):
                if i > 0:
                    actionTypeIdHeader.append(header[0])
            db = QtGui.qApp.db
            tableTreatmentScheme = db.table('TreatmentScheme')
            tableJob = db.table('Job')
            tableJobTicket = db.table('Job_Ticket')
            tableRBJobType = db.table('rbJobType')
            tableActionType = db.table('ActionType')
            tableActionPropertyType = db.table('ActionPropertyType')

            cond = [tableActionType['deleted'].eq(0),
                    tableActionPropertyType['deleted'].eq(0),
                    tableActionType['id'].inlist(actionTypeIdHeader),
                    tableActionPropertyType['typeName'].like(CJobTicketActionPropertyValueType.name),
                    tableActionPropertyType['valueDomain'].isNotNull(),
                    tableJob['deleted'].eq(0),
                    tableJob['date'].dateEq(begDate),
                    tableJobTicket['deleted'].eq(0),
                    tableJobTicket['datetime'].dateEq(begDate)
                    ]
            cols = ['DISTINCT Job.id AS jobId',
                    tableJob['date'],
                    tableJob['begTime'],
                    tableJob['endTime'],
                    tableJob['quantity']
                    ]
            queryTable = tableActionType.innerJoin(tableActionPropertyType, tableActionPropertyType['actionType_id'].eq(tableActionType['id']))
            queryTable = queryTable.innerJoin(tableRBJobType, u'''rbJobType.code = IF(INSTR(ActionPropertyType.valueDomain, ';') > 0,
            LEFT(ActionPropertyType.valueDomain, INSTR(ActionPropertyType.valueDomain, ';')-1), ActionPropertyType.valueDomain)''')
            queryTable = queryTable.innerJoin(tableJob, tableJob['jobType_id'].eq(tableRBJobType['id']))
            queryTable = queryTable.innerJoin(tableJobTicket, tableJobTicket['master_id'].eq(tableJob['id']))
            order = [tableJob['begTime'].name(), tableJob['endTime'].name()]
            records = db.getRecordList(queryTable, cols, cond, order)
            for record in records:
                quantity = forceInt(record.value('quantity'))
                if quantity > self.quantityMax:
                    self.quantityMax = quantity
                begTime = QDateTime(forceDate(record.value('date')), forceTime(record.value('begTime')))
                endTime = QDateTime(forceDate(record.value('date')), forceTime(record.value('endTime')))
                if not datetimeMin or datetimeMin > begTime:
                    datetimeMin = begTime
                if not datetimeMax or datetimeMax < endTime:
                    datetimeMax = endTime

            if self.minimumDuration and datetimeMin and datetimeMax:
                datetimePrev = datetimeMin
                while datetimePrev <= datetimeMax:
                    datetimeLast = datetimePrev.addSecs(self.minimumDuration)
                    self.dates.append((datetimePrev, datetimeLast))
                    datetimePrev = datetimeLast

            if self.dates:
                cond = [tableActionType['deleted'].eq(0),
                        tableActionPropertyType['deleted'].eq(0),
                        tableActionType['id'].inlist(actionTypeIdHeader),
                        tableActionPropertyType['typeName'].like(CJobTicketActionPropertyValueType.name),
                        tableActionPropertyType['valueDomain'].isNotNull(),
                        tableJob['deleted'].eq(0),
                        tableJob['date'].dateEq(begDate),
                        tableJobTicket['deleted'].eq(0),
                        tableJobTicket['datetime'].dateEq(begDate)
                        ]
                cols = [tableJobTicket['id'].alias('jobTickedId'),
                        tableJobTicket['datetime'],
                        tableJob['quantity'],
                        tableActionPropertyType['actionType_id'].alias('actionTypeId'),
                        tableJob['jobType_id'],
                        tableJob['date'],
                        tableJob['begTime'],
                        tableJob['endTime']
                        ]
                queryTable = tableActionType.innerJoin(tableActionPropertyType, tableActionPropertyType['actionType_id'].eq(tableActionType['id']))
                queryTable = queryTable.innerJoin(tableRBJobType, u'''rbJobType.code = IF(INSTR(ActionPropertyType.valueDomain, ';') > 0,
                LEFT(ActionPropertyType.valueDomain, INSTR(ActionPropertyType.valueDomain, ';')-1), ActionPropertyType.valueDomain)''')
                queryTable = queryTable.innerJoin(tableJob, tableJob['jobType_id'].eq(tableRBJobType['id']))
                queryTable = queryTable.innerJoin(tableJobTicket, tableJobTicket['master_id'].eq(tableJob['id']))
                order = [tableJobTicket['id'].name(), tableJobTicket['datetime'].name()]
                records = db.getRecordList(queryTable, cols, cond, order)
                for record in records:
                    actionTypeId = forceRef(record.value('actionTypeId'))
                    datetime = forceDateTime(record.value('datetime'))
                    begTime = QDateTime(forceDate(record.value('date')), forceTime(record.value('begTime')))
                    endTime = QDateTime(forceDate(record.value('date')), forceTime(record.value('endTime')))
                    timeToSecs = begTime.secsTo(endTime)
                    quantity = forceInt(record.value('quantity'))
                    duration = math.floor(float(timeToSecs)/quantity)
                    for datetimePrev, datetimeLast in self.dates:
                        if datetime >= datetimePrev and datetime < datetimeLast:
                            newRecord = self.getEmptyRecord()
                            newRecord.setValue('actionType_id', toVariant(actionTypeId))
                            newRecord.setValue('jobTicket_id', toVariant(forceRef(record.value('jobTickedId'))))
                            newRecord.setValue('treatmentType_id', toVariant(treatmentTypeId))
                            newRecord.setValue('id', toVariant(None))
                            newRecord.setValue('endDate', toVariant(endDate))
                            self.items[((pyDateTime(datetimePrev), pyDateTime(datetimeLast)), actionTypeId)] = (None, newRecord, quantity, duration)
                            break

                self.treatmentSchemeIdList = []
                self.treatmentSchemeSourceIdList = []
                self.treatmentSchemeDict = treatmentSchemeDict
                self.recordsSchemeDict = recordsSchemeDict
                treatmentSchemeIdKeys = []
                recordScheme = self.recordsSchemeDict.get(treatmentSchemeId, None)
                if recordScheme:
                    treatmentTypeId = forceRef(recordScheme.value('treatmentType_id'))
                    begDateScheme = pyDate(forceDate(recordScheme.value('begDate')))
                    endDateScheme = pyDate(forceDate(recordScheme.value('endDate')))
                    treatmentSchemeLine = self.treatmentSchemeDict.get((treatmentTypeId, (begDateScheme, endDateScheme)), {})
                    treatmentSchemeIdKeys = treatmentSchemeLine.keys()
                if treatmentSchemeIdKeys:
                    tableJobTicket = db.table('Job_Ticket').alias('JobTicketScheme')
                    cond = [tableTreatmentScheme['id'].inlist(treatmentSchemeIdKeys),
                            tableActionType['deleted'].eq(0),
                            tableActionPropertyType['deleted'].eq(0),
                            tableActionType['id'].inlist(actionTypeIdHeader),
                            tableActionPropertyType['typeName'].like(CJobTicketActionPropertyValueType.name),
                            tableActionPropertyType['valueDomain'].isNotNull(),
                            tableTreatmentScheme['treatmentType_id'].eq(treatmentTypeId),
                            tableTreatmentScheme['actionType_id'].inlist(actionTypeIdHeader),
                            tableJob['deleted'].eq(0),
                            tableJobTicket['deleted'].eq(0),
                            tableActionPropertyType['actionType_id'].eq(tableTreatmentScheme['actionType_id']),
                            ]
                queryTable = tableActionType.innerJoin(tableActionPropertyType, tableActionPropertyType['actionType_id'].eq(tableActionType['id']))
                queryTable = queryTable.innerJoin(tableRBJobType, u'''rbJobType.code = IF(INSTR(ActionPropertyType.valueDomain, ';') > 0,
                LEFT(ActionPropertyType.valueDomain, INSTR(ActionPropertyType.valueDomain, ';')-1), ActionPropertyType.valueDomain)''')
                queryTable = queryTable.innerJoin(tableJob, tableJob['jobType_id'].eq(tableRBJobType['id']))
                queryTable = queryTable.innerJoin(tableJobTicket, tableJobTicket['master_id'].eq(tableJob['id']))
                queryTable = queryTable.innerJoin(tableTreatmentScheme, tableTreatmentScheme['jobTicket_id'].eq(tableJobTicket['id']))
                cols = [tableJobTicket['id'].alias('jobTickedId'),
                        tableJobTicket['datetime'],
                        tableJob['quantity'],
                        tableJob['jobType_id'],
                        tableTreatmentScheme['actionType_id'],
                        tableTreatmentScheme['jobTicket_id'],
                        tableTreatmentScheme['treatmentType_id'],
                        tableTreatmentScheme['id'],
                        tableTreatmentScheme['endDate'],
                        tableJob['date'],
                        tableJob['begTime'],
                        tableJob['endTime']
                        ]
                order = [tableJobTicket['id'].name(), tableJob['quantity'].name()]
                records = db.getRecordList(queryTable, cols, cond, order)
                for record in records:
                    datetime = forceDateTime(record.value('datetime'))
                    newDateTime = QDateTime(begDate, forceTime(record.value('datetime')))
                    begTime = QDateTime(forceDate(record.value('date')), forceTime(record.value('begTime')))
                    endTime = QDateTime(forceDate(record.value('date')), forceTime(record.value('endTime')))
                    timeToSecs = begTime.secsTo(endTime)
                    quantity = forceInt(record.value('quantity'))
                    duration = math.floor(float(timeToSecs)/quantity)
                    for datetimePrev, datetimeLast in self.dates:
                        if newDateTime >= datetimePrev and newDateTime < datetimeLast:
                            treatmentSchemeId = forceRef(record.value('id'))
                            if treatmentSchemeId and treatmentSchemeId not in self.treatmentSchemeIdList:
                                self.treatmentSchemeIdList.append(treatmentSchemeId)
                                if newDateTime == datetime:
                                    newRecord = self.getEmptyRecord()
                                    newRecord.setValue('actionType_id', toVariant(forceRef(record.value('actionType_id'))))
                                    newRecord.setValue('jobTicket_id', toVariant(forceRef(record.value('jobTicket_id'))))
                                    newRecord.setValue('treatmentType_id', toVariant(forceRef(record.value('treatmentType_id'))))
                                    newRecord.setValue('id', toVariant(treatmentSchemeId))
                                    newRecord.setValue('endDate', toVariant(forceDate(record.value('endDate'))))
                                else:
                                    newTreatmentSchemeId, newRecord, newQuantity, newDuration = self.items.get(((pyDateTime(datetimePrev), pyDateTime(datetimeLast)), forceRef(record.value('actionType_id'))), (None, None, 0, 0))
                                self.items[((pyDateTime(datetimePrev), pyDateTime(datetimeLast)), forceRef(record.value('actionType_id')))] = (treatmentSchemeId, newRecord, quantity, duration)
                                break

                if self.treatmentSchemeIdList:
                    tableTreatmentSchemeSource = db.table('TreatmentScheme_Source')
                    cond = [tableTreatmentSchemeSource['treatmentScheme_id'].inlist(self.treatmentSchemeIdList),
                            tableTreatmentSchemeSource['orgStructure_id'].isNotNull()
                            ]
                    records = db.getRecordList(tableTreatmentSchemeSource, u'*', cond)
                    for record in records:
                        treatmentSchemeId = forceRef(record.value('treatmentScheme_id'))
                        treatmentSchemeSourceId = forceRef(record.value('id'))
                        if treatmentSchemeSourceId and treatmentSchemeSourceId not in self.treatmentSchemeSourceIdList:
                            self.treatmentSchemeSourceIdList.append(treatmentSchemeSourceId)
                        for keyScheme, item in self.items.items():
                            if item and treatmentSchemeId == item[0]:
                                sourceItem = self.sourceItems.get(keyScheme, [])
                                sourceItem.append(record)
                                self.sourceItems[keyScheme] = sourceItem
        self.reset()


    def loadItems(self, params, orgStructureCache):
        self.orgStructureCache = orgStructureCache
        begDate = params.get('begDate', None)
        endDate = params.get('endDate', None)
        treatmentTypeId = params.get('treatmentTypeId', None)
        self.actionTypeIdList = params.get('actionTypeIdList', [])
        self.items = {}
        self.dates = []
        self.quantityMax = 0
        self.quantityDict = {}
        self.sourceItems = {}
        self.minimumDuration = TreatmentScheduleMinimumDuration
        actionTypeIdHeader = []
        treatmentSchemeIdList = []
        datetimeMin = None
        datetimeMax = None
        self.loadHeader()
        if begDate and endDate and treatmentTypeId and self.actionTypeIdList and len(self.headers) > 1:
            for i, header in enumerate(self.headers):
                if i > 0:
                    actionTypeIdHeader.append(header[0])
            db = QtGui.qApp.db
            tableTreatmentScheme = db.table('TreatmentScheme')
            tableJob = db.table('Job')
            tableJobTicket = db.table('Job_Ticket')
            tableRBJobType = db.table('rbJobType')
            tableActionType = db.table('ActionType')
            tableActionPropertyType = db.table('ActionPropertyType')

            cond = [tableActionType['deleted'].eq(0),
                    tableActionPropertyType['deleted'].eq(0),
                    tableActionType['id'].inlist(actionTypeIdHeader),
                    tableActionPropertyType['typeName'].like(CJobTicketActionPropertyValueType.name),
                    tableActionPropertyType['valueDomain'].isNotNull(),
                    tableJob['deleted'].eq(0),
                    tableJob['date'].dateEq(begDate),
                    tableJobTicket['deleted'].eq(0),
                    tableJobTicket['datetime'].dateEq(begDate)
                    ]
            cols = ['DISTINCT Job.id AS jobId',
                    tableJob['date'],
                    tableJob['begTime'],
                    tableJob['endTime'],
                    tableJob['quantity']
                    ]
            queryTable = tableActionType.innerJoin(tableActionPropertyType, tableActionPropertyType['actionType_id'].eq(tableActionType['id']))
            queryTable = queryTable.innerJoin(tableRBJobType, u'''rbJobType.code = IF(INSTR(ActionPropertyType.valueDomain, ';') > 0,
            LEFT(ActionPropertyType.valueDomain, INSTR(ActionPropertyType.valueDomain, ';')-1), ActionPropertyType.valueDomain)''')
            queryTable = queryTable.innerJoin(tableJob, tableJob['jobType_id'].eq(tableRBJobType['id']))
            queryTable = queryTable.innerJoin(tableJobTicket, tableJobTicket['master_id'].eq(tableJob['id']))
            order = [tableJob['begTime'].name(), tableJob['endTime'].name()]
            records = db.getRecordList(queryTable, cols, cond, order)
            for record in records:
                quantity = forceInt(record.value('quantity'))
                if quantity > self.quantityMax:
                    self.quantityMax = quantity
                begTime = QDateTime(forceDate(record.value('date')), forceTime(record.value('begTime')))
                endTime = QDateTime(forceDate(record.value('date')), forceTime(record.value('endTime')))
                if not datetimeMin or datetimeMin > begTime:
                    datetimeMin = begTime
                if not datetimeMax or datetimeMax < endTime:
                    datetimeMax = endTime

            if self.minimumDuration and datetimeMin and datetimeMax:
                datetimePrev = datetimeMin
                while datetimePrev <= datetimeMax:
                    datetimeLast = datetimePrev.addSecs(self.minimumDuration)
                    self.dates.append((datetimePrev, datetimeLast))
                    datetimePrev = datetimeLast

            if self.dates:
                cond = [tableActionType['deleted'].eq(0),
                        tableActionPropertyType['deleted'].eq(0),
                        tableActionType['id'].inlist(actionTypeIdHeader),
                        tableActionPropertyType['typeName'].like(CJobTicketActionPropertyValueType.name),
                        tableActionPropertyType['valueDomain'].isNotNull(),
                        tableJob['deleted'].eq(0),
                        tableJob['date'].dateEq(begDate),
                        tableJobTicket['deleted'].eq(0),
                        tableJobTicket['datetime'].dateEq(begDate)
                        ]
                cols = [tableJobTicket['id'].alias('jobTickedId'),
                        tableJobTicket['datetime'],
                        tableJob['quantity'],
                        tableActionPropertyType['actionType_id'].alias('actionTypeId'),
                        tableJob['jobType_id'],
                        tableJob['date'],
                        tableJob['begTime'],
                        tableJob['endTime']
                        ]
                queryTable = tableActionType.innerJoin(tableActionPropertyType, tableActionPropertyType['actionType_id'].eq(tableActionType['id']))
                queryTable = queryTable.innerJoin(tableRBJobType, u'''rbJobType.code = IF(INSTR(ActionPropertyType.valueDomain, ';') > 0,
                LEFT(ActionPropertyType.valueDomain, INSTR(ActionPropertyType.valueDomain, ';')-1), ActionPropertyType.valueDomain)''')
                queryTable = queryTable.innerJoin(tableJob, tableJob['jobType_id'].eq(tableRBJobType['id']))
                queryTable = queryTable.innerJoin(tableJobTicket, tableJobTicket['master_id'].eq(tableJob['id']))
                order = [tableJobTicket['id'].name(), tableJobTicket['datetime'].name()]
                records = db.getRecordList(queryTable, cols, cond, order)
                for record in records:
                    actionTypeId = forceRef(record.value('actionTypeId'))
                    datetime = forceDateTime(record.value('datetime'))
                    begTime = QDateTime(forceDate(record.value('date')), forceTime(record.value('begTime')))
                    endTime = QDateTime(forceDate(record.value('date')), forceTime(record.value('endTime')))
                    timeToSecs = begTime.secsTo(endTime)
                    quantity = forceInt(record.value('quantity'))
                    duration = math.floor(float(timeToSecs)/quantity)
                    for datetimePrev, datetimeLast in self.dates:
                        if datetime >= datetimePrev and datetime < datetimeLast:
                            newRecord = self.getEmptyRecord()
                            newRecord.setValue('actionType_id', toVariant(actionTypeId))
                            newRecord.setValue('jobTicket_id', toVariant(forceRef(record.value('jobTickedId'))))
                            newRecord.setValue('treatmentType_id', toVariant(treatmentTypeId))
                            newRecord.setValue('id', toVariant(None))
                            newRecord.setValue('endDate', toVariant(endDate))
                            self.items[((pyDateTime(datetimePrev), pyDateTime(datetimeLast)), actionTypeId)] = (None, newRecord, quantity, duration)
                            break

                self.treatmentSchemeIdList = []
                self.treatmentSchemeSourceIdList = []
                self.treatmentSchemeDict = {}
                self.recordsSchemeDict = {}
                selectTreatmentSchemeIdList = []
                cond = [tableActionType['deleted'].eq(0),
                        tableActionPropertyType['deleted'].eq(0),
                        tableActionType['id'].inlist(actionTypeIdHeader),
                        tableActionPropertyType['typeName'].like(CJobTicketActionPropertyValueType.name),
                        tableActionPropertyType['valueDomain'].isNotNull(),
                        tableTreatmentScheme['treatmentType_id'].eq(treatmentTypeId),
                        tableTreatmentScheme['actionType_id'].inlist(actionTypeIdHeader),
                        tableJob['deleted'].eq(0),
                        tableJobTicket['deleted'].eq(0),
                        tableJobTicket['datetime'].dateLe(endDate),
                        tableActionPropertyType['actionType_id'].eq(tableTreatmentScheme['actionType_id']),
                        tableTreatmentScheme['endDate'].dateGe(begDate)
                        ]
                queryTable = tableActionType.innerJoin(tableActionPropertyType, tableActionPropertyType['actionType_id'].eq(tableActionType['id']))
                queryTable = queryTable.innerJoin(tableRBJobType, u'''rbJobType.code = IF(INSTR(ActionPropertyType.valueDomain, ';') > 0,
                LEFT(ActionPropertyType.valueDomain, INSTR(ActionPropertyType.valueDomain, ';')-1), ActionPropertyType.valueDomain)''')
                queryTable = queryTable.innerJoin(tableJob, tableJob['jobType_id'].eq(tableRBJobType['id']))
                queryTable = queryTable.innerJoin(tableJobTicket, tableJobTicket['master_id'].eq(tableJob['id']))
                queryTable = queryTable.innerJoin(tableTreatmentScheme, tableTreatmentScheme['jobTicket_id'].eq(tableJobTicket['id']))
                cols = [u'DISTINCT DATE(Job_Ticket.datetime) AS begDate',
                        tableTreatmentScheme['treatmentType_id'],
                        tableTreatmentScheme['id'],
                        tableTreatmentScheme['endDate']
                        ]
                order = [u'begDate']
                records = db.getRecordList(queryTable, cols, cond, order)
                for record in records:
                    treatmentSchemeId = forceRef(record.value('id'))
                    treatmentTypeId = forceRef(record.value('treatmentType_id'))
                    begDateScheme = pyDate(forceDate(record.value('begDate')))
                    endDateScheme = pyDate(forceDate(record.value('endDate')))
                    if treatmentSchemeId:
                        if (treatmentTypeId, (begDateScheme, endDateScheme)) not in self.treatmentSchemeDict.keys() and treatmentSchemeId not in selectTreatmentSchemeIdList:
                            selectTreatmentSchemeIdList.append(treatmentSchemeId)
                        treatmentSchemeLine = self.treatmentSchemeDict.get((treatmentTypeId, (begDateScheme, endDateScheme)), {})
                        treatmentSchemeLine[treatmentSchemeId] = record
                        self.treatmentSchemeDict[(treatmentTypeId, (begDateScheme, endDateScheme))] = treatmentSchemeLine
                        self.recordsSchemeDict[treatmentSchemeId] = record

                treatmentSchemeId = None
                if len(selectTreatmentSchemeIdList) > 0:
                    try:
                        dialog = CTreatmentSchemeTypeDialogTableModel(self.eventEditor, selectTreatmentSchemeIdList, self.recordsSchemeDict, self.treatmentSchemeDict)
                        dialog.setWindowTitle(u'Выберите План цикла')
                        if dialog.exec_():
                            treatmentSchemeId = dialog.currentItemId()
                        else:
                            self.items = {}
                            self.dates = []
                            self.quantityMax = 0
                            self.quantityDict = {}
                            self.sourceItems = {}
                            self.minimumDuration = TreatmentScheduleMinimumDuration
                    finally:
                        dialog.deleteLater()

                if treatmentSchemeId:
                    treatmentSchemeIdKeys = []
                    recordScheme = self.recordsSchemeDict.get(treatmentSchemeId, None)
                    if recordScheme:
                        treatmentTypeId = forceRef(recordScheme.value('treatmentType_id'))
                        begDateScheme = pyDate(forceDate(recordScheme.value('begDate')))
                        endDateScheme = pyDate(forceDate(recordScheme.value('endDate')))
                        treatmentSchemeLine = self.treatmentSchemeDict.get((treatmentTypeId, (begDateScheme, endDateScheme)), {})
                        treatmentSchemeIdKeys = treatmentSchemeLine.keys()
                    if treatmentSchemeIdKeys:
                        tableJobTicket = db.table('Job_Ticket').alias('JobTicketScheme')
                        cond = [tableTreatmentScheme['id'].inlist(treatmentSchemeIdKeys),
                                tableActionType['deleted'].eq(0),
                                tableActionPropertyType['deleted'].eq(0),
                                tableActionType['id'].inlist(actionTypeIdHeader),
                                tableActionPropertyType['typeName'].like(CJobTicketActionPropertyValueType.name),
                                tableActionPropertyType['valueDomain'].isNotNull(),
                                tableTreatmentScheme['treatmentType_id'].eq(treatmentTypeId),
                                tableTreatmentScheme['actionType_id'].inlist(actionTypeIdHeader),
                                tableJob['deleted'].eq(0),
                                tableJobTicket['deleted'].eq(0),
                                tableActionPropertyType['actionType_id'].eq(tableTreatmentScheme['actionType_id']),
                                ]
                    queryTable = tableActionType.innerJoin(tableActionPropertyType, tableActionPropertyType['actionType_id'].eq(tableActionType['id']))
                    queryTable = queryTable.innerJoin(tableRBJobType, u'''rbJobType.code = IF(INSTR(ActionPropertyType.valueDomain, ';') > 0,
                    LEFT(ActionPropertyType.valueDomain, INSTR(ActionPropertyType.valueDomain, ';')-1), ActionPropertyType.valueDomain)''')
                    queryTable = queryTable.innerJoin(tableJob, tableJob['jobType_id'].eq(tableRBJobType['id']))
                    queryTable = queryTable.innerJoin(tableJobTicket, tableJobTicket['master_id'].eq(tableJob['id']))
                    queryTable = queryTable.innerJoin(tableTreatmentScheme, tableTreatmentScheme['jobTicket_id'].eq(tableJobTicket['id']))
                    cols = [tableJobTicket['id'].alias('jobTickedId'),
                            tableJobTicket['datetime'],
                            tableJob['quantity'],
                            tableJob['jobType_id'],
                            tableTreatmentScheme['actionType_id'],
                            tableTreatmentScheme['jobTicket_id'],
                            tableTreatmentScheme['treatmentType_id'],
                            tableTreatmentScheme['id'],
                            tableTreatmentScheme['endDate'],
                            tableJob['date'],
                            tableJob['begTime'],
                            tableJob['endTime']
                            ]
                    order = [tableJobTicket['id'].name(), tableJob['quantity'].name()]
                    records = db.getRecordList(queryTable, cols, cond, order)
                    for record in records:
                        datetime = forceDateTime(record.value('datetime'))
                        newDateTime = QDateTime(begDate, forceTime(record.value('datetime')))
                        begTime = QDateTime(forceDate(record.value('date')), forceTime(record.value('begTime')))
                        endTime = QDateTime(forceDate(record.value('date')), forceTime(record.value('endTime')))
                        timeToSecs = begTime.secsTo(endTime)
                        quantity = forceInt(record.value('quantity'))
                        duration = math.floor(float(timeToSecs)/quantity)
                        for datetimePrev, datetimeLast in self.dates:
                            if newDateTime >= datetimePrev and newDateTime < datetimeLast:
                                treatmentSchemeId = forceRef(record.value('id'))
                                if treatmentSchemeId and treatmentSchemeId not in self.treatmentSchemeIdList:
                                    self.treatmentSchemeIdList.append(treatmentSchemeId)
                                    if newDateTime == datetime:
                                        newRecord = self.getEmptyRecord()
                                        newRecord.setValue('actionType_id', toVariant(forceRef(record.value('actionType_id'))))
                                        newRecord.setValue('jobTicket_id', toVariant(forceRef(record.value('jobTicket_id'))))
                                        newRecord.setValue('treatmentType_id', toVariant(forceRef(record.value('treatmentType_id'))))
                                        newRecord.setValue('id', toVariant(treatmentSchemeId))
                                        newRecord.setValue('endDate', toVariant(forceDate(record.value('endDate'))))
                                    else:
                                        newTreatmentSchemeId, newRecord, newQuantity, newDuration = self.items.get(((pyDateTime(datetimePrev), pyDateTime(datetimeLast)), forceRef(record.value('actionType_id'))), (None, None, 0, 0))
                                    self.items[((pyDateTime(datetimePrev), pyDateTime(datetimeLast)), forceRef(record.value('actionType_id')))] = (treatmentSchemeId, newRecord, quantity, duration)
                                    break

                    if self.treatmentSchemeIdList:
                        tableTreatmentSchemeSource = db.table('TreatmentScheme_Source')
                        cond = [tableTreatmentSchemeSource['treatmentScheme_id'].inlist(self.treatmentSchemeIdList),
                                tableTreatmentSchemeSource['orgStructure_id'].isNotNull()
                                ]
                        records = db.getRecordList(tableTreatmentSchemeSource, u'*', cond)
                        for record in records:
                            treatmentSchemeId = forceRef(record.value('treatmentScheme_id'))
                            treatmentSchemeSourceId = forceRef(record.value('id'))
                            if treatmentSchemeSourceId and treatmentSchemeSourceId not in self.treatmentSchemeSourceIdList:
                                self.treatmentSchemeSourceIdList.append(treatmentSchemeSourceId)
                            for keyScheme, item in self.items.items():
                                if item and treatmentSchemeId == item[0]:
                                    sourceItem = self.sourceItems.get(keyScheme, [])
                                    sourceItem.append(record)
                                    self.sourceItems[keyScheme] = sourceItem
        self.reset()


    def setData(self, index, value, role=Qt.EditRole):
        column = index.column()
        row = index.row()
        if role == Qt.EditRole:
            if row >= 0 and row < len(self.dates):
                if column != 0:
                    datetimePrev, datetimeLast = self.dates[row]
                    header = self.headers[column]
                    if datetimePrev and datetimeLast and header and header[0]:
                        if header and header[0] and (((pyDateTime(datetimePrev), pyDateTime(datetimeLast)), header[0]) in self.items.keys()):
                            keyScheme = ((pyDateTime(datetimePrev), pyDateTime(datetimeLast)), header[0])
                            itemValue = self.items.get(keyScheme, None)
                            if itemValue:
                                orgStructureIdList = []
                                sourceItems = []
                                treatmentSchemeId, record, quantity, duration = itemValue
                                oldSourceItems = self.sourceItems.get(keyScheme, [])
                                valueList = value.toList() if value else []
                                for orgStructureId in valueList:
                                    if orgStructureId and orgStructureId not in orgStructureIdList:
                                        orgStructureIdList.append(orgStructureId)
                                        newRecord = self.getEmptyRecordSource()
                                        newRecord.setValue('id', toVariant(None))
                                        newRecord.setValue('treatmentScheme_id', toVariant(treatmentSchemeId))
                                        newRecord.setValue('orgStructure_id', toVariant(orgStructureId))
                                        for oldSourceItem in oldSourceItems:
                                            oldTreatmentSchemeId = forceRef(oldSourceItem.value('treatmentScheme_id'))
                                            oldOrgStructureId = forceRef(oldSourceItem.value('orgStructure_id'))
                                            if oldOrgStructureId and oldOrgStructureId == forceRef(newRecord.value('orgStructure_id')) and oldTreatmentSchemeId and oldTreatmentSchemeId == forceRef(newRecord.value('treatmentScheme_id')):
                                                newRecord.setValue('id', toVariant(forceRef(oldSourceItem.value('id'))))
                                        sourceItems.append(newRecord)
                                self.sourceItems[keyScheme] = sourceItems
                        self.emitCellChanged(row, column)
                        return True
        return False


    def saveItems(self, params):
        begDate = params.get('begDate', None)
        endDate = params.get('endDate', None)
        treatmentTypeId = params.get('treatmentTypeId', None)
        self.actionTypeIdList = params.get('actionTypeIdList', [])
        treatmentSIdList = []
        treatmentSSIdList = []
        db = QtGui.qApp.db
        tableTreatmentScheme = db.table('TreatmentScheme')
        tableTreatmentSchemeSource = db.table('TreatmentScheme_Source')
        if self.items and self.sourceItems:
            for keyScheme, item in self.items.items():
                if item:
                    record = item[1]
                    treatmentSchemeId = forceRef(record.value('id'))
                    sourceItems = self.sourceItems.get(keyScheme, [])
                    if sourceItems:
                        treatmentSchemeId = db.insertOrUpdate(tableTreatmentScheme, record)
                        record.setValue('id', toVariant(treatmentSchemeId))
                        treatmentSIdList.append(treatmentSchemeId)
                        if treatmentSchemeId:
                            for sourceItem in sourceItems:
                                sourceItem.setValue('treatmentScheme_id', toVariant(treatmentSchemeId))
                                treatmentSchemeSourceId = db.insertOrUpdate(tableTreatmentSchemeSource, sourceItem)
                                sourceItem.setValue('id', toVariant(treatmentSchemeSourceId))
                                treatmentSSIdList.append(treatmentSchemeSourceId)
        if self.treatmentSchemeIdList:
            if self.treatmentSchemeSourceIdList:
                filter = [tableTreatmentSchemeSource['treatmentScheme_id'].inlist(self.treatmentSchemeIdList)]
                if treatmentSIdList:
                    filter.append(tableTreatmentSchemeSource['treatmentScheme_id'].notInlist(treatmentSIdList))
                filter.append(tableTreatmentSchemeSource['id'].inlist(self.treatmentSchemeSourceIdList))
                if treatmentSSIdList:
                   filter.append(tableTreatmentSchemeSource['id'].notInlist(treatmentSSIdList))
                db.deleteRecord(tableTreatmentSchemeSource, filter)
            filter = [tableTreatmentScheme['id'].inlist(self.treatmentSchemeIdList)]
            if treatmentSIdList:
                filter.append(tableTreatmentScheme['id'].notInlist(treatmentSIdList))
            db.deleteRecord(tableTreatmentScheme, filter)


    def getEmptyRecord(self):
        db = QtGui.qApp.db
        tableTreatmentScheme = db.table('TreatmentScheme')
        record = tableTreatmentScheme.newRecord()
        return record


    def getEmptyRecordSource(self):
        db = QtGui.qApp.db
        tableTreatmentSchemeSource = db.table('TreatmentScheme_Source')
        record = tableTreatmentSchemeSource.newRecord()
        return record


    def emitItemsCountChanged(self):
        self.emit(SIGNAL('itemsCountChanged(int)'), len(self.dates) if self.dates else 0)


    def emitCellChanged(self, row, column):
        index = self.index(row, column)
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)


    def emitRowsChanged(self, row1, row2):
        index1 = self.index(row1, 0)
        index2 = self.index(row2, self.columnCount())
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index1, index2)


    def emitColumnChanged(self, column):
        index1 = self.index(0, column)
        index2 = self.index(self.rowCount(), column)
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index1, index2)


class CTreatmentSchemeTypeTableModel(CTableModel):
    def __init__(self, parent, cols, tableName, records, treatmentSchemeDict):
        CTableModel.__init__(self, parent, cols, tableName)
        self.records = records
        self.treatmentSchemeDict = treatmentSchemeDict


    def beforeRemoveItem(self, itemId):
        pass


    def afterRemoveItem(self, itemId):
        pass


    def removeRow(self, row, parent = QModelIndex()):
        itemIdList = self.idList()
        if 0 <= row < len(itemIdList):
            itemId = itemIdList[row]
            if itemId and self.canRemoveItem(itemId):
                QtGui.qApp.setWaitCursor()
                try:
                    db = QtGui.qApp.db
                    tableTreatmentScheme = db.table('TreatmentScheme')
                    tableTreatmentSchemeSource = db.table('TreatmentScheme_Source')
                    db.transaction()
                    try:
                        self.beforeRemoveItem(itemId)
                        recordScheme = self.records.get(itemId, None)
                        if recordScheme:
                            treatmentTypeId = forceRef(recordScheme.value('treatmentType_id'))
                            begDateScheme = pyDate(forceDate(recordScheme.value('begDate')))
                            endDateScheme = pyDate(forceDate(recordScheme.value('endDate')))
                            treatmentSchemeLine = self.treatmentSchemeDict.get((treatmentTypeId, (begDateScheme, endDateScheme)), {})
                            treatmentSchemeIdKeys = treatmentSchemeLine.keys()
                            if treatmentSchemeIdKeys:
                                db.deleteRecord(tableTreatmentSchemeSource, [tableTreatmentSchemeSource['treatmentScheme_id'].inlist(treatmentSchemeIdKeys)])
                                db.deleteRecord(tableTreatmentScheme, [tableTreatmentScheme['id'].inlist(treatmentSchemeIdKeys)])
                        self.afterRemoveItem(itemId)
                        db.commit()
                    except:
                        db.rollback()
                        raise
                    self.beginRemoveRows(parent, row, row)
                    del self._idList[row]
                    self.endRemoveRows()
                    self.emitItemsCountChanged()
                    return True
                finally:
                    QtGui.qApp.restoreOverrideCursor()
        return False


    def canRemoveRow(self, row):
        itemId = None
        itemIdList = self.idList()
        if 0 <= row < len(itemIdList):
            itemId = itemIdList[row]
        return self.canRemoveItem(itemId)


    def canRemoveItem(self, itemId):
        return True


    def confirmRemoveRow(self, view, row, multiple=False):
        itemId = None
        itemIdList = self.idList()
        if 0 <= row < len(itemIdList):
            itemId = itemIdList[row]
        return self.confirmRemoveItem(view, itemId, multiple)


    def confirmRemoveItem(self, view, itemId, multiple=False):
        buttons = QtGui.QMessageBox.Yes|QtGui.QMessageBox.No
        if multiple:
            buttons |= QtGui.QMessageBox.Cancel
        mbResult = QtGui.QMessageBox.question(view, u'Внимание!', u'Действительно удалить?', buttons, QtGui.QMessageBox.No)
        return {QtGui.QMessageBox.Yes: True,
                QtGui.QMessageBox.No: False}.get(mbResult, None)


class CTreatmentSchemeTypeDialog(CDialogBase, Ui_TreatmentSchemeTypeDialog):
    def __init__(self, parent, cols, tableName, order, forSelect=False, filterClass=None, idList=[], records=None, treatmentSchemeDict={}):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.tblTreatmentSchemeType.addPopupDelRow()
        self.filterClass = filterClass
        self.props = {}
        self.order = order
        self.records = records
        self.treatmentSchemeDict = treatmentSchemeDict
        self.model = CTreatmentSchemeTypeTableModel(self, cols, tableName, self.records, self.treatmentSchemeDict)
        self.model.setIdList(idList)
        self.tblTreatmentSchemeType.setModel(self.model)
        if idList:
            self.tblTreatmentSchemeType.selectRow(0)


    def selectItem(self):
        return self.exec_()


    def setCurrentItemId(self, itemId):
        self.tblTreatmentSchemeType.setCurrentItemId(itemId)


    def currentItemId(self):
        return self.tblTreatmentSchemeType.currentItemId()


class CTreatmentSchemeTypeDialogTableModel(CTreatmentSchemeTypeDialog):
    class CLocDateCol(CDateCol):
        def __init__(self, title, fields, defaultWidth, records):
            CDateCol.__init__(self, title, fields, defaultWidth, 'l')
            self.records = records

        def format(self, values):
            id  = forceRef(values[0])
            record = self.records.get(id, None)
            if record:
                return toVariant(forceDate(record.value('begDate')))
            return CCol.invalid

    def __init__(self, parent, idList, records, treatmentSchemeDict):
        CTreatmentSchemeTypeDialog.__init__(self, parent, [
            CTreatmentSchemeTypeDialogTableModel.CLocDateCol(u'Дата начала', ['id'], 10, records),
            CDateCol(u'Дата окончания', ['endDate'], 10),
            CRefBookCol(u'Тип', ['treatmentType_id'], 'TreatmentType', 20)
            ], 'TreatmentScheme', ['begDate', 'endDate', 'treatmentType_id'], False, None, idList, records, treatmentSchemeDict)

