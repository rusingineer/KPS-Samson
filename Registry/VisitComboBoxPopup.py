# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
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

from library.database   import CTableRecordCache
from library.TableModel import CTableModel, CTextCol, CDateCol, CRefBookCol
from library.Utils      import forceInt, getPref, setPref, forceStringEx, forceRef

from Registry.Ui_VisitComboBoxPopup import Ui_VisitComboBoxPopup

__all__ = [ 'CVisitComboBoxPopup',
          ]


class CVisitComboBoxPopup(QtGui.QFrame, Ui_VisitComboBoxPopup):
    __pyqtSignals__ = ('visitIdSelected(int)'
                      )

    def __init__(self, parent = None):
        QtGui.QFrame.__init__(self, parent, Qt.Popup)
        self.setAttribute(Qt.WA_WindowPropagation)
        self.tableModel = CVisitTableModel(self)
        self.tableSelectionModel = QtGui.QItemSelectionModel(self.tableModel, self)
        self.tableSelectionModel.setObjectName('tableSelectionModel')
        self.setupUi(self)
        self.tblVisit.setModel(self.tableModel)
        self.tblVisit.setSelectionModel(self.tableSelectionModel)
        self.visitId = None
        self.filter = []
        self.queryTable = []
        self.tblVisit.installEventFilter(self)
        preferences = getPref(QtGui.qApp.preferences.windowPrefs, 'CVisitComboBoxPopup', {})
        self.tblVisit.loadPreferences(preferences)


    def setFilter(self, filter, queryTable=[]):
        self.filter = filter
        self.queryTable = queryTable


    def mousePressEvent(self, event):
        parent = self.parentWidget()
        if parent!=None:
            opt=QtGui.QStyleOptionComboBox()
            opt.init(parent)
            arrowRect = parent.style().subControlRect(
                QtGui.QStyle.CC_ComboBox, opt, QtGui.QStyle.SC_ComboBoxArrow, parent)
            arrowRect.moveTo(parent.mapToGlobal(arrowRect.topLeft()))
            if (arrowRect.contains(event.globalPos()) or self.rect().contains(event.pos())):
                self.setAttribute(Qt.WA_NoMouseReplay)
        QtGui.QFrame.mousePressEvent(self, event)


    def closeEvent(self, event):
        preferences = self.tblVisit.savePreferences()
        setPref(QtGui.qApp.preferences.windowPrefs, 'CVisitComboBoxPopup', preferences)
        QtGui.QFrame.closeEvent(self, event)


    def eventFilter(self, watched, event):
        if watched == self.tblVisit:
            if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Select):
                event.accept()
                index = self.tblVisit.currentIndex()
                self.tblVisit.emit(SIGNAL('doubleClicked(QModelIndex)'), index)
                return True
        return QtGui.QFrame.eventFilter(self, watched, event)


    def on_buttonBox_apply(self):
        QtGui.qApp.setWaitCursor()
        try:
            crIdList = self.getVisitIdList()
            self.setVisitIdList(crIdList, None)
        finally:
            QtGui.qApp.restoreOverrideCursor()


    def setVisitIdList(self, idList, posToId):
        if idList:
            self.tblVisit.setIdList(idList, posToId)
            self.tblVisit.setFocus(Qt.OtherFocusReason)


    def getVisitIdList(self):
        db = QtGui.qApp.db
        tableVisit = db.table('Visit')
        cond = self.filter if self.filter else ''
        table = self.queryTable if self.queryTable else tableVisit
        idList = db.getDistinctIdList(table, tableVisit['id'].name(),
                              where=cond,
                              order=tableVisit['date'].name())
        return idList


    def setVisitId(self, visitId):
        db = QtGui.qApp.db
        table = db.table('Visit')
        self.visitId = visitId
        id = None
        if self.visitId:
            record = db.getRecordEx(table, [table['id']], [table['id'].eq(self.visitId), table['deleted'].eq(0)])
            id = forceInt(record.value(0)) if record else None
        self.tblVisit.setCurrentItemId(id)


    def selectVisitCode(self, visitId):
        self.visitId = visitId
        self.emit(SIGNAL('visitIdSelected(int)'), self.visitId)
        self.close()


    def getCurrentVisitId(self):
        db = QtGui.qApp.db
        table = db.table('Visit')
        id = self.tblVisit.currentItemId()
        if id:
            record = db.getRecordEx(table, [table['id']], [table['id'].eq(id)])
            if record:
                return forceInt(record.value(0))
        return None


    @pyqtSignature('QModelIndex')
    def on_tblVisit_doubleClicked(self, index):
        if index.isValid():
            if (Qt.ItemIsEnabled & self.tableModel.flags(index)):
                visitId = self.getCurrentVisitId()
                self.selectVisitCode(visitId)


class CVisitTableModel(CTableModel):
    class CEventTypeCol(CTextCol):
        def __init__(self, title, fields, defaultWidth, alignment='l'):
            CTextCol.__init__(self, title, fields, defaultWidth, alignment)
            self.cache = {}

        def format(self, values):
            eventTypeName = u''
            eventId = forceRef(values[0])
            record = self.cache.get(eventId)
            if not record and eventId:
                db = QtGui.qApp.db
                table = db.table('Event')
                tableET = db.table('EventType')
                queryTable = table.innerJoin(tableET, tableET['id'].eq(table['eventType_id']))
                cond = [table['id'].eq(eventId),
                        table['deleted'].eq(0),
                        tableET['deleted'].eq(0)
                        ]
                record = db.getRecordEx(queryTable, 'EventType.code, EventType.name', cond)
                self.cache[eventId] = record
            if record:
                code = forceStringEx(record.value('code'))
                name = forceStringEx(record.value('name'))
                if code:
                    eventTypeName = code + u' - '
                if name:
                    eventTypeName += name
            return eventTypeName

        def invalidateRecordsCache(self):
            self.cache.clear()


    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.addColumn(CDateCol(u'Дата визита', ['date'], 30))
        self.addColumn(CRefBookCol(u'Врач', ['person_id'], 'vrbPersonWithSpeciality', 10),)
        self.addColumn(CVisitTableModel.CEventTypeCol(u'Тип события', ['event_id'], 30))
        self.setTable('Visit')


    def flags(self, index):
        return Qt.ItemIsEnabled|Qt.ItemIsSelectable


    def setTable(self, tableName):
        db = QtGui.qApp.db
        table = db.table('Visit')
        loadFields = []
        loadFields.append(u'''DISTINCT id, date, person_id, event_id''')
        self._table = table
        self._recordsCache = CTableRecordCache(db, self._table, loadFields)

