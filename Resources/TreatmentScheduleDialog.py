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
## График циклов
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDate, QModelIndex, QVariant, pyqtSignature, SIGNAL, QAbstractTableModel
from library.database        import CTableRecordCache
from library.ItemsListDialog import CItemEditorBaseDialog
from library.Utils           import pyDate, forceInt, forceRef, forceString, toVariant, forceDate
from library.TableModel      import CTableModel, CCol

from Ui_TreatmentScheduleDialog  import Ui_TreatmentScheduleDialog


class CTreatmentScheduleDialog(CItemEditorBaseDialog, Ui_TreatmentScheduleDialog):
    def __init__(self, parent):
        CItemEditorBaseDialog.__init__(self, parent, 'TreatmentSchedule')
        self.addModels('TreatmentSchedule', CTreatmentScheduleModel(self))
        self.addModels('TreatmentColorType', CTreatmentColorTypeModel(self))
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setWindowTitleEx(u'График циклов')
        self.setTreatmentTypeCache()
        self.params = {}
        self.tblTreatmentSchedule.setModel(self.modelTreatmentSchedule)
        self.tblTreatmentColorType.setModel(self.modelTreatmentColorType)
        self.tblTreatmentSchedule.addTreatmentFromRow()
        self.tblTreatmentSchedule.addStartFromRow()
        self.tblTreatmentSchedule.addEndFromRow()


    def setTreatmentTypeCache(self):
        db = QtGui.qApp.db
        self.treatmentTypeCache = CTableRecordCache(db, db.forceTable('TreatmentType'), u'*', capacity=None)


    def destroy(self):
        pass


    def getParams(self):
        params = {}
        params['begDate'] = self.edtBegDate.date()
        params['endDate'] = self.edtEndDate.date()
        return params


    def checkDataEntered(self):
        return True


    def loadData(self):
        self.params = self.getParams()
        self.modelTreatmentSchedule.loadItems(self.params, self.treatmentTypeCache)
        treatmentColorTypeList = self.modelTreatmentSchedule.getTreatmentColorTypeList()
        self.modelTreatmentColorType.setIdList(treatmentColorTypeList)


    def saveData(self):
        self.modelTreatmentSchedule.saveItems(self.params)
        return True


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelTreatmentSchedule_dataChanged(self, topLeft, bottomRight):
        treatmentColorTypeList = []
        items = self.modelTreatmentSchedule.items
        for item in items.values():
            treatmentTypeId = forceRef(item.value('treatmentType_id'))
            if treatmentTypeId and treatmentTypeId not in treatmentColorTypeList:
                treatmentColorTypeList.append(treatmentTypeId)
        self.modelTreatmentColorType.setIdList(treatmentColorTypeList)


    @pyqtSignature('')
    def on_btnGenerate_clicked(self):
        self.loadData()


class CTreatmentColorTypeModel(CTableModel):
    class CLocColorCol(CCol):
        def __init__(self, title, fields, defaultWidth, model):
            CCol.__init__(self, title, fields, defaultWidth, 'c')
            self._model = model
            db = QtGui.qApp.db
            self._cache = CTableRecordCache(db, db.forceTable('TreatmentType'), u'*', capacity=None)

        def getBackgroundColor(self, values):
            treatmentTypeId = forceRef(values[0])
            if treatmentTypeId:
                record = self._cache.get(treatmentTypeId)
                if record is None:
                    db = QtGui.qApp.db
                    cond = 'id=%d'%(treatmentTypeId)
                    record = db.getRecordEx('TreatmentType', '*', cond)
                    color = forceString(record.value('color')) if record else None
                    colorRes = QVariant(QtGui.QColor(color)) if color else QVariant()
                    self._cache[treatmentTypeId] = record
                else:
                    color = forceString(record.value('color')) if record else None
                    colorRes = QVariant(QtGui.QColor(color)) if color else QVariant()
                return colorRes
            return CCol.invalid

        def format(self, values):
            treatmentTypeId = forceRef(values[0])
            if treatmentTypeId:
                record = self._cache.get(treatmentTypeId)
                if record is None:
                    db = QtGui.qApp.db
                    cond = 'id=%d'%(treatmentTypeId)
                    record = db.getRecordEx('TreatmentType', '*', cond)
                    self._cache[treatmentTypeId] = record
                    name = forceString(record.value('name')) if record else None
                else:
                    name = forceString(record.value('name')) if record else None
                return QVariant(name) if name else QVariant()
            return CCol.invalid

    def __init__(self, parent):
        CTableModel.__init__(self, parent,
        [
        CTreatmentColorTypeModel.CLocColorCol(u'Легенда', ['id'], 10, self)
        ], 'TreatmentType')
        self.loadField('code')
        self.loadField('name')
        self.loadField('color')


class CTreatmentScheduleModel(QAbstractTableModel):
    def __init__(self, parent):
        QAbstractTableModel.__init__(self, parent)
        self.params = {}
        self.headers = []
        self.items = {}
        self.dates = []
        self.endDateMax = None
        self.begDateMin = None
        self.treatmentColorTypeList = []
        self.readOnly = False
        self.sourceType = {}
        self.treatmentTypeCache = {}
        self.showCodeNameOS = ['name', 'code'][forceInt(QtGui.qApp.preferences.appPrefs.get('showOrgStructureForTreatment', 0))]


    def items(self):
        return self.items


    def setReadOnly(self, value):
        self.readOnly = value


    def columnCount(self, index = None):
        return len(self.headers)


    def rowCount(self, index = None):
        return len(self.dates)+1


    def flags(self, index = QModelIndex()):
        column = index.column()
        if self.readOnly:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        row = index.row()
        if row >= 0 and row < len(self.dates)+1 and len(self.headers) > 1:
            if column == 0:
                return Qt.ItemIsSelectable|Qt.ItemIsEnabled|Qt.ItemIsEditable
            else:
                if not self.getSourceType(row, column):
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
        self.endDateMax = None
        self.begDateMin = None
        begDate = self.params.get('begDate', None)
        endDate = self.params.get('endDate', None)
        self.headers = [[None, u'Даты']]
        db = QtGui.qApp.db
        tableTreatmentScheme = db.table('TreatmentScheme')
        tableTreatmentSchemeSource = db.table('TreatmentScheme_Source')
        tableJobTicket = db.table('Job_Ticket')
        tableOrgStructure = db.table('OrgStructure')
        queryTable = tableTreatmentScheme.innerJoin(tableJobTicket, tableJobTicket['id'].eq(tableTreatmentScheme['jobTicket_id']))
        queryTable = queryTable.innerJoin(tableTreatmentSchemeSource, tableTreatmentSchemeSource['treatmentScheme_id'].eq(tableTreatmentScheme['id']))
        queryTable = queryTable.leftJoin(tableOrgStructure, tableOrgStructure['id'].eq(tableTreatmentSchemeSource['orgStructure_id']))
        cond = [tableTreatmentScheme['endDate'].dateGe(begDate),
                tableJobTicket['datetime'].dateLe(endDate),
                tableOrgStructure['deleted'].eq(0),
                tableJobTicket['deleted'].eq(0),
                ]
        cols = [u'DISTINCT TreatmentScheme_Source.orgStructure_id',
                tableOrgStructure[self.showCodeNameOS],
                tableTreatmentScheme['endDate'],
                u'DATE(Job_Ticket.datetime) AS begDateJT'
                ]
        records = db.getRecordList(queryTable, cols, cond, order='OrgStructure.%s'%(self.showCodeNameOS))
        for record in records:
            header = [forceRef(record.value('orgStructure_id')),
                      forceString(record.value(self.showCodeNameOS))
                      ]
            if header not in self.headers:
                self.headers.append(header)
            begDateJT = forceDate(record.value('begDateJT'))
            if not self.begDateMin or self.begDateMin > begDateJT:
                self.begDateMin = begDateJT
            endDate = forceDate(record.value('endDate'))
            if self.endDateMax < endDate:
                self.endDateMax = endDate
        self.reset()


    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if role == Qt.DisplayRole:
            if row >= 0 and row < len(self.dates):
                date = self.dates[row]
                if date:
                    if column == 0:
                        return QVariant(date)
                    else:
                        if self.headers[column] and self.headers[column][0] and ((pyDate(date), self.headers[column][0]) in self.items.keys()):
                            keySchedule = (pyDate(date), self.headers[column][0])
                            item = self.items.get(keySchedule, None)
                            if item:
                                treatmentTypeId = forceRef(item.value('treatmentType_id'))
                                if treatmentTypeId:
                                    record = self.treatmentTypeCache.get(treatmentTypeId)
                                    return QVariant(forceString(record.value('name'))) if record else QVariant()
                                isStart = forceInt(item.value('isStart'))
                                if isStart:
                                    return QVariant(u'заезд')
                                isEnd = forceInt(item.value('isEnd'))
                                if isEnd:
                                    return QVariant(u'разъезд')
                                return QVariant()
        elif role == Qt.EditRole:
            if row >= 0 and row < len(self.dates):
                date = self.dates[row]
                if date:
                    if column == 0:
                        return QVariant(date)
                    else:
                        if self.headers[column] and self.headers[column][0] and ((pyDate(date), self.headers[column][0]) in self.items.keys()):
                            keySchedule = (pyDate(date), self.headers[column][0])
                            item = self.items.get(keySchedule, None)
                            if item:
                                treatmentTypeId = forceRef(item.value('treatmentType_id'))
                                if treatmentTypeId:
                                    record = self.treatmentTypeCache.get(treatmentTypeId)
                                    return QVariant(treatmentTypeId)
                                isStart = forceInt(item.value('isStart'))
                                if isStart:
                                    return QVariant(isStart)
                                isEnd = forceInt(item.value('isEnd'))
                                if isEnd:
                                    return QVariant(isEnd)
                                return QVariant()
        elif role == Qt.BackgroundRole:
            date = None
            if row >= 0 and row < len(self.dates):
                date = self.dates[row]
                if column == 0:
                    if date and QtGui.qApp.calendarInfo.getDayOfWeek(date) in (6,7):
                        return QVariant(QtGui.QColor(Qt.red))
                    else:
                        return QVariant(QtGui.QColor(Qt.white))
                else:
                    header = self.headers[column]
                    if date and header and header[0]:
                        if header and header[0] and ((pyDate(date), header[0]) in self.items.keys()):
                            keySchedule = (pyDate(date), header[0])
                            item = self.items.get(keySchedule, None)
                            if item:
                                if date and QtGui.qApp.calendarInfo.getDayOfWeek(date) in (6,7):
                                    color = Qt.red
                                else:
                                    color = Qt.white
                                treatmentTypeId = forceRef(item.value('treatmentType_id'))
                                if treatmentTypeId:
                                    record = self.treatmentTypeCache.get(treatmentTypeId)
                                    color = forceString(record.value('color'))
                                return QVariant(QtGui.QColor(color))
            return QVariant(QtGui.QColor(Qt.red)) if (date and QtGui.qApp.calendarInfo.getDayOfWeek(date) in (6,7)) else QVariant(QtGui.QColor(Qt.white))
        return QVariant()


    def loadItems(self, params, treatmentTypeCache):
        self.params = params
        self.treatmentTypeCache = treatmentTypeCache
        begDate = self.params.get('begDate', None)
        endDate = self.params.get('endDate', None)
        self.items = {}
        self.dates = []
        self.treatmentColorTypeList = []
        orgStructureIdHeader = []
        self.loadHeader()
        if begDate and endDate and len(self.headers) > 1:
            newDate = self.begDateMin
            if newDate < begDate:
                newDate = begDate
            cancelDate = self.endDateMax
            if cancelDate > endDate:
                cancelDate = endDate
            while newDate <= cancelDate:
                self.setData(self.createIndex(len(self.dates), 0), QVariant(newDate), role=Qt.EditRole)
                newDate = newDate.addDays(1)
            for i, header in enumerate(self.headers):
                if i > 0:
                    orgStructureIdHeader.append(header[0])
            db = QtGui.qApp.db
            tableTreatmentSchedule = db.table('TreatmentSchedule')
            cond = [tableTreatmentSchedule['date'].ge(begDate),
                    tableTreatmentSchedule['date'].le(endDate),
                    tableTreatmentSchedule['orgStructure_id'].inlist(orgStructureIdHeader)
                    ]
            order = [tableTreatmentSchedule['date'].name()]
            records = db.getRecordList(tableTreatmentSchedule, u'*', cond, order)
            for record in records:
                orgStructureId = forceRef(record.value('orgStructure_id'))
                treatmentTypeId = forceRef(record.value('treatmentType_id'))
                date = forceDate(record.value('date'))
                sourceType = forceInt(record.value('isEnd'))
                if sourceType != 2:
                    sourceType = forceInt(record.value('isStart'))
                elif sourceType != 1:
                    sourceType = 0
                if date not in self.dates:
                    self.dates.append(date)
                self.items[(pyDate(date), orgStructureId)] = record
                self.sourceType[(pyDate(date), orgStructureId)] = sourceType
                if treatmentTypeId and treatmentTypeId not in self.treatmentColorTypeList:
                    self.treatmentColorTypeList.append(treatmentTypeId)
        self.reset()


    def setData(self, index, value, role=Qt.EditRole):
        column = index.column()
        row = index.row()
        if role == Qt.EditRole and len(self.headers) > 1:
            if column == 0:
                newDate = forceDate(value)
                if not newDate or (newDate in self.dates) or newDate > self.endDateMax or newDate < self.begDateMin:
                    return False
            if row == len(self.dates):
                if value.isNull():
                    return False
                for headerId, headerName in self.headers:
                    self.items[pyDate(QDate()), headerId] = self.getEmptyRecord()
                self.dates.append(QDate())
                vCnt = len(self.dates)
                vIndex = QModelIndex()
                self.beginInsertRows(vIndex, vCnt, vCnt)
                self.insertRows(vCnt, 1, vIndex)
                self.endInsertRows()
            date = self.dates[row]
            if row >= 0 and row < len(self.dates):
                if column == 0:
                    newDate = forceDate(value)
                    if newDate and (newDate not in self.dates):
                        self.dates[row] = newDate
                        if len(self.items) > 0:
                            for headerId, headerName in self.headers:
                                if headerId:
                                    for key, record in self.items.items():
                                        if key == (pyDate(date), headerId):
                                            if record:
                                                record.setValue('date', value)
                                                record.setValue('orgStructure_id', headerId)
                                            if (date, headerId) in self.items.keys():
                                                del self.items[(pyDate(date), headerId)]
                                            self.items[(pyDate(newDate), headerId)] = record
                    self.emitCellChanged(row, column)
                    return True
                else:
                    date = self.dates[row]
                    header = self.headers[column]
                    if date and header and header[0] and ((pyDate(date), header[0]) in self.items.keys()):
                        keySchedule = (pyDate(date), self.headers[column][0])
                    elif date and header and header[0]:
                        keySchedule = (pyDate(date), header[0])
                        record = self.getEmptyRecord()
                        record.setValue('date', toVariant(date))
                        record.setValue('orgStructure_id', toVariant(header[0]))
                        record.setValue('id', toVariant(None))
                        record.setValue('treatmentType_id', toVariant(None))
                        record.setValue('isStart', toVariant(0))
                        record.setValue('isEnd', toVariant(0))
                        self.items[keySchedule] = record
                    else:
                        keySchedule = None
                    if keySchedule:
                        record = self.items.get(keySchedule, None)
                        if record:
                            isEnd = 0
                            isStart = 0
                            treatmentTypeId = None
                            sourceType = self.getSourceType(row, column)
                            val = forceRef(value)
                            if sourceType == 2:
                                isEnd = val
                            elif sourceType == 1:
                                isStart = val
                            elif sourceType == 0:
                                treatmentTypeId = val
                            if treatmentTypeId:
                                record.setValue('treatmentType_id', toVariant(treatmentTypeId))
                                record.setValue('isStart', toVariant(0))
                                record.setValue('isEnd', toVariant(0))
                            elif isStart:
                                record.setValue('treatmentType_id', toVariant(None))
                                record.setValue('isStart', toVariant(1))
                                record.setValue('isEnd', toVariant(0))
                            elif isEnd:
                                record.setValue('treatmentType_id', toVariant(None))
                                record.setValue('isStart', toVariant(0))
                                record.setValue('isEnd', toVariant(1))
                            else:
                                record.setValue('treatmentType_id', toVariant(None))
                                record.setValue('isStart', toVariant(0))
                                record.setValue('isEnd', toVariant(0))
                            if treatmentTypeId and treatmentTypeId not in self.treatmentColorTypeList:
                                self.treatmentColorTypeList.append(treatmentTypeId)
                            self.items[keySchedule] = record
                    self.emitCellChanged(row, column)
                    return True
        return False


    def saveItems(self, params):
        begDate = params.get('begDate', None)
        endDate = params.get('endDate', None)
        treatmentScheduleIdList = []
        db = QtGui.qApp.db
        tableTreatmentSchedule = db.table('TreatmentSchedule')
        if self.items:
            for record in self.items.values():
                treatmentTypeId = forceRef(record.value('treatmentType_id'))
                isStart = 0
                isEnd = 0
                if not treatmentTypeId:
                    isStart = forceInt(record.value('isStart'))
                if not isStart:
                    isEnd = forceInt(record.value('isEnd'))
                if isEnd == 2:
                    record.setValue('isEnd', toVariant(1))
                if treatmentTypeId or isStart or isEnd:
                    treatmentScheduleId = db.insertOrUpdate(tableTreatmentSchedule, record)
                    record.setValue('id', toVariant(treatmentScheduleId))
                    treatmentScheduleIdList.append(treatmentScheduleId)
        filter = [tableTreatmentSchedule['date'].ge(begDate),
                  tableTreatmentSchedule['date'].le(endDate)
                 ]
        if treatmentScheduleIdList:
            filter.append(tableTreatmentSchedule['id'].notInlist(treatmentScheduleIdList))
        db.deleteRecord(tableTreatmentSchedule, filter)


    def getEmptyRecord(self):
        db = QtGui.qApp.db
        tableTreatmentSchedule = db.table('TreatmentSchedule')
        record = tableTreatmentSchedule.newRecord()
        return record


    def getSourceType(self, row, column):
        sourceType = 0
        if row >= 0 and row < len(self.dates):
            date = self.dates[row]
            header = self.headers[column]
            if date and header and header[0] and ((pyDate(date), header[0]) in self.items.keys()):
                keySchedule = (pyDate(date), self.headers[column][0])
                sourceType = self.sourceType.get(keySchedule, 0)
        return sourceType


    def setSourceType(self, row, column, sourceType):
        if row >= 0 and row < len(self.dates):
            date = self.dates[row]
            header = self.headers[column]
            if date and header and header[0] and ((pyDate(date), header[0]) in self.items.keys()):
                keySchedule = (pyDate(date), self.headers[column][0])
            elif date and header and header[0]:
                keySchedule = (pyDate(date), header[0])
            else:
                keySchedule = None
            if keySchedule:
                self.sourceType[keySchedule] = sourceType


    def getTreatmentColorTypeList(self):
        return self.treatmentColorTypeList


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

