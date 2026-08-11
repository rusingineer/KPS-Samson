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
## Управление циклами
##
#############################################################################

import math
from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDateTime, QModelIndex, QVariant, pyqtSignature, QAbstractTableModel

from Events.ActionStatus         import CActionStatus
from Events.ActionTypeListDialog import CActionTypeListDialog
from Events.ActionProperty.JobTicketActionPropertyValueType import CJobTicketActionPropertyValueType
from library.database         import CTableRecordCache
from library.ItemsListDialog  import CItemEditorBaseDialog
from library.PreferencesMixin import CDialogPreferencesMixin
from library.Utils            import forceDate, forceTime, forceInt, forceRef, forceString, toVariant, forceDateTime, pyTime, getPref, setPref
from Resources.TreatmentAppointmentEditor import CTreatmentAppointmentEditor
from Resources.Utils          import TreatmentScheduleMinimumDuration

from Ui_TreatmentControlDialog  import Ui_TreatmentControlDialog


class CTreatmentControlDialog(CItemEditorBaseDialog, Ui_TreatmentControlDialog, CDialogPreferencesMixin):
    def __init__(self, parent):
        CItemEditorBaseDialog.__init__(self, parent, 'TreatmentScheme')
        self.addModels('TreatmentControl', CTreatmentControlModel(self))
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setWindowTitleEx(u'Управление циклами')
        self.params = {}
        self.dateSchedule = None
        self.tblTreatmentControl.setModel(self.modelTreatmentControl)
        #self.cmbTreatmentType.setTable('TreatmentType')
        self.modelTreatmentControl.setEventEditor(self)
        self.loadDialogPreferences()


    def destroy(self):
        pass


    def done(self, result):
        preferences = self.tblTreatmentControl.savePreferences()
        setPref(QtGui.qApp.preferences.windowPrefs, 'tblTreatmentControlDialog', preferences)
        return CItemEditorBaseDialog.done(self, result)


    @pyqtSignature('QModelIndex')
    def on_tblTreatmentControl_doubleClicked(self, index):
        self.updateTreatmentControl(index)


    @pyqtSignature('QModelIndex')
    def on_tblTreatmentControl_clicked(self, index):
        self.updateTreatmentControl(index)


    def updateTreatmentControl(self, index):
        if index.isValid():
            row = index.row()
            column = index.column()
            if column > 0 and row >= 0 and row < len(self.modelTreatmentControl.dates):
                datetimePrev, datetimeLast = self.modelTreatmentControl.dates[row]
                header = self.modelTreatmentControl.headers[column]
                if datetimePrev and datetimeLast and header and header[0]:
                    if header and header[0] and (((pyTime(datetimePrev), pyTime(datetimeLast)), header[0]) in self.modelTreatmentControl.items.keys()):
                        db = QtGui.qApp.db
                        clientCache = CTableRecordCache(db, db.forceTable('Client'), u'*', capacity=None)
                        dialog = CTreatmentAppointmentEditor(self, clientCache=clientCache)
                        try:
                            keyControl = ((pyTime(datetimePrev), pyTime(datetimeLast)), header[0])
                            actionTypeId, record, quantityItem, durationItem, actionTypeCountItem = self.modelTreatmentControl.items.get(keyControl, (None, None, 1, 1, 0))
                            datetime = QDateTime(forceDate(record.value('date')), forceTime(record.value('datetime'))) if record else None
                            datetimePrev = QDateTime(forceDate(record.value('date')), forceTime(datetimePrev)) if record else None
                            datetimeLast = QDateTime(forceDate(record.value('date')), forceTime(datetimeLast)) if record else None
                            dialog.loadData(datetime, actionTypeId, datetimePrev, datetimeLast, self.dateSchedule)
                            dialog.exec_()
                            self.updateData()
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
        params['dateSchedule'] = self.edtScheduleDate.date()
        #params['treatmentTypeId'] = self.cmbTreatmentType.value()
        params['actionTypeIdList'] = self.getActionTypeIdList()
        return params


    def checkDataEntered(self):
        return True


    def loadData(self):
        self.params = self.getParams()
        self.updateData()


    def updateData(self):
        #treatmentTypeId = self.params.get('treatmentTypeId', None)
        self.dateSchedule = self.params.get('dateSchedule', None)
        actionTypeIdList = self.params.get('actionTypeIdList', None)
        #if treatmentTypeId and actionTypeIdList and self.dateSchedule:
        if actionTypeIdList and self.dateSchedule:
            self.modelTreatmentControl.loadItems(self.params)
            headers = self.modelTreatmentControl.headers
            dates = self.modelTreatmentControl.dates
            items = self.modelTreatmentControl.items
            headers = self.modelTreatmentControl.headers
            dates = self.modelTreatmentControl.dates
            items = self.modelTreatmentControl.items
            for column, header in enumerate(headers):
                if column > 0:
                    for row, (datetimePrev, datetimeLast) in enumerate(dates):
                        self.tblTreatmentControl.setSpan(row, column, 1, 1)
            for column, header in enumerate(headers):
                if column > 0:
                    for row, (datetimePrev, datetimeLast) in enumerate(dates):
                        if header and (((pyTime(datetimePrev), pyTime(datetimeLast)), header[0]) in items.keys()):
                            item = items.get(((pyTime(datetimePrev), pyTime(datetimeLast)), header[0]), None)
                            if item and item[3]:
                                duration = item[3]
                                rowSpanCount = math.ceil(float(duration/self.modelTreatmentControl.minimumDuration))
                                self.tblTreatmentControl.setSpan(row, column, rowSpanCount, 1)


    def saveData(self):
        return True


    @pyqtSignature('')
    def on_btnGenerate_clicked(self):
#        if not self.cmbTreatmentType.value():
#            self.checkValueMessage(u'Требуется указать цикл!', False, self.cmbTreatmentType)
#            return
        self.loadData()
        self.tblTreatmentControl.loadPreferences(getPref(QtGui.qApp.preferences.windowPrefs, 'tblTreatmentControlDialog', {}))


class CTreatmentControlModel(QAbstractTableModel):
    def __init__(self, parent):
        QAbstractTableModel.__init__(self, parent)
        self.headers = []
        self.items = {}
        self.sourceItems = {}
        self.dates = []
        self.actionTypeIdList = []
        self.readOnly = False
        self.quantityMax = 0
        self.minimumDuration = TreatmentScheduleMinimumDuration
        self.eventEditor = None


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
                    if header and header[0] and (((pyTime(datetimePrev), pyTime(datetimeLast)), header[0]) in self.items.keys()):
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


    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if role == Qt.DisplayRole:
            if row < len(self.dates):
                datetimePrev, datetimeLast = self.dates[row]
                if column == 0:
                    if datetimePrev and datetimeLast:
                        return QVariant(datetimePrev.toString('hh:mm') + u' - ' + datetimeLast.toString('hh:mm'))
                else:
                    if self.headers[column] and self.headers[column][0] and (((pyTime(datetimePrev), pyTime(datetimeLast)), self.headers[column][0]) in self.items.keys()):
                        keyControl = ((pyTime(datetimePrev), pyTime(datetimeLast)), self.headers[column][0])
                        actionTypeId, record, quantity, duration, actionTypeCount = self.items.get(keyControl, (None, None, 0, 0, 0))
                        return toVariant(self.getActionTypeShowNameList(actionTypeId, quantity, actionTypeCount))
        elif role == Qt.EditRole:
            if row < len(self.dates):
                datetimePrev, datetimeLast = self.dates[row]
                if column == 0:
                    if datetimePrev and datetimeLast:
                        return QVariant(datetimePrev.toString('hh:mm') + u' - ' + datetimeLast.toString('hh:mm'))
                else:
                    if self.headers[column] and (((pyTime(datetimePrev), pyTime(datetimeLast)), self.headers[column]) in self.items.keys()):
                        keyControl = ((pyTime(datetimePrev), pyTime(datetimeLast)), self.headers[column][0])
                        actionTypeId, record, quantity, duration, actionTypeCount = self.items.get(keyControl, (None, None, 0, 0, 0))
                        return toVariant(self.getActionTypeShowNameList(actionTypeId, quantity, actionTypeCount))
        elif role == Qt.BackgroundRole:
            if row >= 0 and row < len(self.dates):
                if column > 0:
                    datetimePrev, datetimeLast = self.dates[row]
                    header = self.headers[column][0]
                    if datetimePrev and datetimeLast and header:
                        if header and (((pyTime(datetimePrev), pyTime(datetimeLast)), header) in self.items.keys()):
                            keyControl = ((pyTime(datetimePrev), pyTime(datetimeLast)), header)
                            actionTypeId, record, quantity, duration, actionTypeCount = self.items.get(keyControl, (None, None, 0, 0, 0))
                            if (quantity - actionTypeCount) > 0:
                                return QVariant(QtGui.QColor(Qt.cyan))
                return QVariant(QtGui.QColor(Qt.white))
        return QVariant()


    def getActionTypeShowNameList(self, actionTypeId, quantity, actionTypeCount):
        if actionTypeId:
            return u'(%d/%d)'%(actionTypeCount, (quantity-actionTypeCount))
        return u''


    def loadItems(self, params):
        dateSchedule = params.get('dateSchedule', None)
        #treatmentTypeId = params.get('treatmentTypeId', None)
        self.actionTypeIdList = params.get('actionTypeIdList', [])
        self.items = {}
        self.dates = []
        self.quantityMax = 0
        self.sourceItems = {}
        self.minimumDuration = TreatmentScheduleMinimumDuration
        treatmentSchemeIdList = []
        datetimeMin = None
        datetimeMax = None
        self.loadHeader()
        if len(self.headers) > 1 and dateSchedule: # and treatmentTypeId
            db = QtGui.qApp.db
            tableTreatmentSchedule = db.table('TreatmentSchedule')
            tableTreatmentScheme = db.table('TreatmentScheme')
            tableTreatmentSchemeSource = db.table('TreatmentScheme_Source')
            tableJobTicket = db.table('Job_Ticket')
            tableJob = db.table('Job')
            queryTable = tableTreatmentSchedule.innerJoin(tableTreatmentScheme, tableTreatmentSchedule['treatmentType_id'].eq(tableTreatmentScheme['treatmentType_id']))
            queryTable = queryTable.innerJoin(tableTreatmentSchemeSource, tableTreatmentSchemeSource['treatmentScheme_id'].eq(tableTreatmentScheme['id']))
            queryTable = queryTable.innerJoin(tableJobTicket, tableJobTicket['id'].eq(tableTreatmentScheme['jobTicket_id']))
            queryTable = queryTable.innerJoin(tableJob, tableJob['id'].eq(tableJobTicket['master_id']))
            condSource = [tableTreatmentSchedule['date'].eq(dateSchedule),
                          #tableTreatmentSchedule['treatmentType_id'].eq(treatmentTypeId),
                          tableTreatmentSchedule['isStart'].eq(0),
                          tableTreatmentSchedule['isEnd'].eq(0),
                          tableTreatmentSchedule['orgStructure_id'].eq(tableTreatmentSchemeSource['orgStructure_id']),
                          db.joinAnd([#tableTreatmentScheme['treatmentType_id'].eq(treatmentTypeId),
                                      tableTreatmentScheme['endDate'].dateGe(dateSchedule),
                                      tableJobTicket['datetime'].dateLe(dateSchedule),
                                     ])
                         ]
            if condSource:
                cond = [tableJobTicket['deleted'].eq(0),
                        tableJob['deleted'].eq(0),
                        ]
                cond.append(db.joinAnd(condSource))
                cols = [u'DISTINCT Job.id AS jobId',
                        tableJob['date'],
                        tableJob['begTime'],
                        tableJob['endTime'],
                        tableJob['quantity'],
                        tableTreatmentScheme['id'].alias('treatmentSchemeId')
                        ]
                order = [tableJob['begTime'].name(), tableJob['endTime'].name()]
                records = db.getRecordList(queryTable, cols, cond, order)
                for record in records:
                    quantity = forceInt(record.value('quantity'))
                    if quantity > self.quantityMax:
                        self.quantityMax = quantity
                    begTime = forceTime(record.value('begTime'))
                    endTime = forceTime(record.value('endTime'))
                    if not datetimeMin or datetimeMin > begTime:
                        datetimeMin = begTime
                    if not datetimeMax or datetimeMax < endTime:
                        datetimeMax = endTime
                    treatmentSchemeId = forceRef(record.value('treatmentSchemeId'))
                    if treatmentSchemeId and treatmentSchemeId not in treatmentSchemeIdList:
                        treatmentSchemeIdList.append(treatmentSchemeId)

                if self.minimumDuration and datetimeMin and datetimeMax:
                    datetimePrev = datetimeMin
                    while datetimePrev <= datetimeMax:
                        datetimeLast = datetimePrev.addSecs(self.minimumDuration)
                        self.dates.append((datetimePrev, datetimeLast))
                        datetimePrev = datetimeLast

                if self.dates and treatmentSchemeIdList:
                    tableRBJobType = db.table('rbJobType')
                    tableActionType = db.table('ActionType')
                    tableActionPropertyType = db.table('ActionPropertyType')
                    tableEvent = db.table('Event')
                    tableAction = db.table('Action')
                    tableAP = db.table('ActionProperty')
                    tableAPJT = db.table('ActionProperty_Job_Ticket')

                    cond = [tableEvent['deleted'].eq(0),
                            tableAction['deleted'].eq(0),
                            tableActionType['deleted'].eq(0),
                            tableActionPropertyType['deleted'].eq(0),
                            tableActionPropertyType['typeName'].like(CJobTicketActionPropertyValueType.name),
                            tableActionPropertyType['valueDomain'].isNotNull(),
                            tableActionType['isUsesCycles'].eq(1),
                            tableJob['deleted'].eq(0),
                            tableJobTicket['deleted'].eq(0),
                            tableJobTicket['datetime'].dateEq(dateSchedule),
                            tableJobTicket['id'].isNotNull(),
                            tableAPJT['value'].eq(tableJobTicket['id']),
                            tableAP['action_id'].eq(tableAction['id']),
                            tableAP['deleted'].eq(0),
                            tableAction['status'].notInlist([CActionStatus.canceled, CActionStatus.refused])
                            ]

                    cols = [tableJobTicket['id'].alias('jobTicketId'),
                            tableJobTicket['datetime'],
                            tableEvent['client_id'],
                            tableAction['status'],
                            tableActionPropertyType['actionType_id'].alias('actionTypeId'),
                            tableJob['jobType_id'],
                            tableJob['date'],
                            tableJob['begTime'],
                            tableJob['endTime'],
                            tableJob['capacity'],
                            tableJob['quantity'],
                            tableRBJobType['code'].alias('jobTypeCode'),
                            tableRBJobType['name'].alias('jobTypeName')
                            ]
                    queryTable = tableActionType.innerJoin(tableActionPropertyType, tableActionPropertyType['actionType_id'].eq(tableActionType['id']))
                    queryTable = queryTable.innerJoin(tableRBJobType, u'''rbJobType.code = IF(INSTR(ActionPropertyType.valueDomain, ';') > 0,
                    LEFT(ActionPropertyType.valueDomain, INSTR(ActionPropertyType.valueDomain, ';')-1), ActionPropertyType.valueDomain)''')
                    queryTable = queryTable.innerJoin(tableJob, tableJob['jobType_id'].eq(tableRBJobType['id']))
                    queryTable = queryTable.innerJoin(tableJobTicket, tableJobTicket['master_id'].eq(tableJob['id']))
                    queryTable = queryTable.innerJoin(tableAP, tableAP['type_id'].eq(tableActionPropertyType['id']))
                    queryTable = queryTable.innerJoin(tableAPJT, tableAP['id'].eq(tableAPJT['id']))
                    queryTable = queryTable.innerJoin(tableAction, tableAction['actionType_id'].eq(tableActionType['id']))
                    queryTable = queryTable.innerJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
                    order = [tableJobTicket['id'].name(), tableJobTicket['datetime'].name()]
                    records = db.getRecordList(queryTable, cols, cond, order)
                    for record in records:
                        actionTypeId = forceRef(record.value('actionTypeId'))
                        datetime = forceDateTime(record.value('datetime'))
                        begTime = forceTime(record.value('begTime'))
                        endTime = forceTime(record.value('endTime'))
                        timeToSecs = begTime.secsTo(endTime)
                        quantity = forceInt(record.value('quantity'))
                        duration = math.floor(float(timeToSecs)/quantity)
                        for datetimePrev, datetimeLast in self.dates:
                            if datetime.time() >= datetimePrev and datetime.time() < datetimeLast:
                                keyControl = ((pyTime(datetimePrev), pyTime(datetimeLast)), actionTypeId)
                                actionTypeIdItem, recordItem, quantityItem, durationItem, actionTypeCountItem = self.items.get(keyControl, (None, None, 1, 1, 0))
                                actionTypeCountItem += 1
                                self.items[keyControl] = (actionTypeId, record, forceInt(record.value('capacity')), duration, actionTypeCountItem)
                                break
        self.dates.sort()
        self.reset()

