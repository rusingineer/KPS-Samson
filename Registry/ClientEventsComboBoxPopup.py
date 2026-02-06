# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2012-2021 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################


from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QEvent, pyqtSignature, SIGNAL

from Events.Utils import orderTexts
from Registry.RegistryTable import codeIsPrimary
from library.crbcombobox import CRBComboBox
from library.database import CTableRecordCache
from library.TableModel import CTableModel, CDateCol, CEnumCol, CTextCol, CDesignationCol, CRefBookCol, CCol
from library.Utils import forceString, getPref, setPref, forceRef, toVariant

from Registry.Ui_ClientEventsComboBoxPopup import Ui_ClientEventsComboBoxPopup
__all__ = ['CClientEventsComboBoxPopup']


class CClientEventsComboBoxPopup(QtGui.QFrame, Ui_ClientEventsComboBoxPopup):
    __pyqtSignals__ = ('eventIdIdSelected(int)'
                       )

    def __init__(self, parent=None):
        QtGui.QFrame.__init__(self, parent, Qt.Popup)
        self.setFrameShape(QtGui.QFrame.StyledPanel)
        self.setAttribute(Qt.WA_WindowPropagation)
        self.tableModel = CClientEventsTableModel(self)
        self.tableSelectionModel = QtGui.QItemSelectionModel(self.tableModel, self)
        self.tableSelectionModel.setObjectName('tableSelectionModel')
        self.setupUi(self)
        self.tblClientEvents.setModel(self.tableModel)
        self.tblClientEvents.setSelectionModel(self.tableSelectionModel)
        self.clientId = None
        self.mkb = None
        self.begDate = None
        self.endDate = None
        self.eventId = None
        self.tblClientEvents.installEventFilter(self)
        preferences = getPref(QtGui.qApp.preferences.windowPrefs, 'CClientEventsComboBoxPopup', {})
        self.tblClientEvents.loadPreferences(preferences)

    def mousePressEvent(self, event):
        parent = self.parentWidget()
        if parent is not None:
            opt = QtGui.QStyleOptionComboBox()
            opt.init(parent)
            arrowRect = parent.style().subControlRect(QtGui.QStyle.CC_ComboBox, opt, QtGui.QStyle.SC_ComboBoxArrow, parent)
            arrowRect.moveTo(parent.mapToGlobal(arrowRect.topLeft()))
            if arrowRect.contains(event.globalPos()) or self.rect().contains(event.pos()):
                self.setAttribute(Qt.WA_NoMouseReplay)
        QtGui.QFrame.mousePressEvent(self, event)

    def closeEvent(self, event):
        preferences = self.tblClientEvents.savePreferences()
        setPref(QtGui.qApp.preferences.windowPrefs, 'CClientEventsComboBoxPopup', preferences)
        QtGui.QFrame.closeEvent(self, event)

    def eventFilter(self, watched, event):
        if watched == self.tblClientEvents:
            if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Select):
                event.accept()
                index = self.tblClientEvents.currentIndex()
                self.tblClientEvents.emit(SIGNAL('doubleClicked(QModelIndex)'), index)
                return True
        return QtGui.QFrame.eventFilter(self, watched, event)

    def getClientEventIdList(self, clientId, mkb=None, begDate=None, endDate=None):
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        tableEventTypePurpose = db.table('rbEventTypePurpose')
        queryTable = tableEvent.innerJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
        queryTable = queryTable.innerJoin(tableEventTypePurpose,
                                          tableEventTypePurpose['id'].eq(tableEventType['purpose_id']))
        cond = [tableEvent['deleted'].eq(0),
                tableEvent['client_id'].eq(clientId),
                tableEventType['context'].notlike(u'relatedAction%'),
                tableEventTypePurpose['code'].notlike('0')]
        if begDate:
            cond.append(tableEvent['execDate'].ge(begDate))
        if endDate:
            cond.append(tableEvent['execDate'].le(endDate))
        if mkb:
            tableDiagnosis = db.table('Diagnosis')
            queryTable = queryTable.leftJoin(tableDiagnosis, 'Diagnosis.id=getEventDiagnosis(Event.id)')
            cond.append(tableDiagnosis['MKB'].like(mkb))

        idList = db.getIdList(queryTable, tableEvent['id'].name(),
                              where=cond,
                              order='execDate DESC',
                              limit=50)
        return idList

    def setClientId(self, clientId):
        self.clientId = clientId

    def setMKB(self, mkb):
        self.mkb = mkb

    def setBegDate(self, begDate):
        self.begDate = begDate

    def setEndDate(self, endDate):
        self.endDate = endDate

    def setClientEventsTable(self):
        self.setClientEventIdList(self.getClientEventIdList(self.clientId, self.mkb, self.begDate, self.endDate), self.eventId)

    def setClientEventIdList(self, idList, posToId):
        self.tblClientEvents.setIdList(idList, posToId)
        self.tblClientEvents.setFocus(Qt.OtherFocusReason)

    @pyqtSignature('QModelIndex')
    def on_tblClientEvents_doubleClicked(self, index):
        if index.isValid():
            if Qt.ItemIsEnabled & self.tableModel.flags(index):
                self.eventId = self.tblClientEvents.currentItemId()
                self.emit(SIGNAL('eventIdIdSelected(int)'), self.eventId)
                self.close()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Backspace, Qt.Key_Delete):
            parent = self.parentWidget()
            parent.clearValue()
        QtGui.QFrame.keyPressEvent(self, event)


class CClientEventsTableModel(CTableModel):
    class CLocEventMKBColumn(CCol):
        def __init__(self, title, fields, defaultWidth, extraFields=[], alignment='l'):
            CCol.__init__(self, title, fields, defaultWidth, alignment)
            self.extraFields = extraFields
            self._cache = {}

        def format(self, values):
            eventId = forceRef(values[0])
            result = self._cache.get(eventId, None)
            if result is None:
                db = QtGui.qApp.db
                query = db.query('SELECT getEventDiagnosis(%d)' % eventId)
                if query.next():
                    diagnosisId = forceRef(query.value(0))
                    if diagnosisId:
                        table = db.table('Diagnosis')
                        record = db.getRecordEx(table, 'MKB', table['id'].eq(diagnosisId))
                        if record:
                            MKB = forceString(record.value('MKB'))
                            outText = MKB
                            result = toVariant(outText)
                            self._cache[eventId] = result
                    else:
                        result = CCol.invalid
                        self._cache[eventId] = result
                else:
                    result = CCol.invalid
                    self._cache[eventId] = result
            return result

        def invalidateRecordsCache(self):
            self._cache = {}

    class CLocEventMKBExColumn(CCol):
        def __init__(self, title, fields, defaultWidth, extraFields=[], alignment='l'):
            CCol.__init__(self, title, fields, defaultWidth, alignment)
            self.extraFields = extraFields
            self._cache = {}

        def format(self, values):
            eventId = forceRef(values[0])
            result = self._cache.get(eventId, None)
            if result is None:
                db = QtGui.qApp.db
                query = db.query('SELECT getEventDiagnosis(%d)' % eventId)
                if query.next():
                    diagnosisId = forceRef(query.value(0))
                    if diagnosisId:
                        table = db.table('Diagnosis')
                        record = db.getRecordEx(table, 'MKBEx', table['id'].eq(diagnosisId))
                        if record:
                            MKBEx = forceString(record.value('MKBEx'))
                            outText = MKBEx
                            result = toVariant(outText)
                            self._cache[eventId] = result
                    else:
                        result = CCol.invalid
                        self._cache[eventId] = result
                else:
                    result = CCol.invalid
                    self._cache[eventId] = result
            return result

        def invalidateRecordsCache(self):
            self._cache = {}

    class CLocEventHealthGroupColumn(CCol):
        def __init__(self, title, fields, defaultWidth, extraFields=[], alignment='l'):
            CCol.__init__(self, title, fields, defaultWidth, alignment)
            self.extraFields = extraFields
            self._cache = {}

        def format(self, values):
            eventId = forceRef(values[0])
            result = self._cache.get(eventId, None)
            if result is None:
                db = QtGui.qApp.db
                query = db.query('SELECT getEventHealthGroupDiagnostic(%d)' % eventId)
                if query.next():
                    healthGroupId = forceRef(query.value(0))
                    if healthGroupId:
                        result = db.translate('rbHealthGroup', 'id', healthGroupId, 'code')
                        self._cache[eventId] = result
                    else:
                        result = CCol.invalid
                        self._cache[eventId] = result
                else:
                    result = CCol.invalid
                    self._cache[eventId] = result
            return result

        def invalidateRecordsCache(self):
            self._cache = {}

    class CLocEventResultColumn(CCol):
        def __init__(self, title, fields, defaultWidth, extraFields=[], alignment='l'):
            CCol.__init__(self, title, fields, defaultWidth, alignment)
            self.extraFields = extraFields
            self._cache = {}

        def format(self, values):
            eventId = forceRef(values[0])
            result = self._cache.get(eventId, None)
            if result is None:
                db = QtGui.qApp.db
                query = db.query('SELECT getEventResultDiagnostic(%d)' % eventId)
                if query.next():
                    resultId = forceRef(query.value(0))
                    if resultId:
                        result = db.translate('rbDiagnosticResult', 'id', resultId, "concat(regionalCode, ' | ', name)")
                        self._cache[eventId] = result
                    else:
                        result = CCol.invalid
                        self._cache[eventId] = result
                else:
                    result = CCol.invalid
                    self._cache[eventId] = result
            return result

        def invalidateRecordsCache(self):
            self._cache = {}

    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.addColumn(CDateCol(u'Назначен', ['setDate'], 10))
        self.addColumn(CDateCol(u'Выполнен', ['execDate'], 10))
        self.addColumn(CDateCol(u'След. явка', ['nextEventDate'], 10))
        self.addColumn(CDesignationCol(u'Договор', ['contract_id'], ('vrbContract', 'code'), 20))
        self.addColumn(CRefBookCol(u'Тип', ['eventType_id'], 'EventType', 15))
        self.addColumn(CRefBookCol(u'МЭС', ['MES_id'], 'mes.MES', 15, CRBComboBox.showCode))
        self.addColumn(CClientEventsTableModel.CLocEventMKBColumn(u'MKB', ['id'], 7, ['MKB']))
        self.addColumn(CClientEventsTableModel.CLocEventMKBExColumn(u'MKBEx', ['id'], 7, ['MKBEx']))
        self.addColumn(CRefBookCol(u'Врач', ['execPerson_id'], 'vrbPersonWithSpecialityAndOrgStr', 15))
        self.addColumn(CEnumCol(u'Первичный', ['isPrimary'], codeIsPrimary, 8))
        self.addColumn(CEnumCol(u'Порядок', ['order'], orderTexts, 8))
        self.addColumn(CRefBookCol(u'Результат события', ['result_id'], 'rbResult', 40, showFields=CRBComboBox.showCodeAndName))
        self.addColumn(CClientEventsTableModel.CLocEventResultColumn(u'Результат осмотра', ['id'], 7, ['diagnosticResult_id']))
        self.addColumn(CTextCol(u'Номер документа', ['externalId'], 30))
        self.addColumn(CClientEventsTableModel.CLocEventHealthGroupColumn(u'Группа здоровья', ['id'], 7, ['healthGroup_id']))
        self.addColumn(CRefBookCol(u'Автор', ['createPerson_id'], 'vrbPerson', 15))

        self.loadField('createPerson_id')
        self.loadField('prevEvent_id')
        self.setTable('Event')

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def setTable(self, tableName, recordCacheCapacity=300):
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        loadFields = [u'''id, setDate, execDate, nextEventDate, contract_id, eventType_id, MES_id, execPerson_id,
                              isPrimary, `order`, result_id, externalId, createPerson_id''']
        self._table = tableEvent
        self._recordsCache = CTableRecordCache(db, self._table, loadFields)
