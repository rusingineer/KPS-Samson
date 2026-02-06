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
from PyQt4.QtCore import QVariant, SIGNAL, QObject, QDateTime #, QDate

from library.Counter import CCounterController
from library.InDocTable import CInDocTableView
from library.Utils import forceRef, forceStringEx
from Events.Utils import getActionTypeIdListByFlatCode
from Events.Action import CAction, CActionTypeCache
from F111.F111CreateDialog import CF111CreateDialog
from F111.F111EditDialog import CF111EditDialog
from Registry.Utils import preFillingActionRecordMSI


class CF025DiagnosticsInDocTableView(CInDocTableView):
    def __init__(self, parent):
        CInDocTableView.__init__(self, parent)
        self.__actCreateF111 = None
        self.__actUpdateF111 = None


    def on_popupMenu_aboutToShow(self):
        CInDocTableView.on_popupMenu_aboutToShow(self)
        isEnabled = False
        isVisible = False
        eventId = None
        actionId = None
        if self.__actCreateF111 or self.__actUpdateF111:
            if hasattr(self.model(), '_parent'):
                eventEditor = self.model()._parent
            elif hasattr(self.model(), 'eventEditor'):
                eventEditor = self.model().eventEditor
            else:
                eventEditor = QObject.parent(self.model()) # для 131 формы
            if eventEditor and eventEditor.clientId and eventEditor.clientSex == 2:
                isVisible = True
                db = QtGui.qApp.db
                tableEvent = db.table('Event')
                tableEventType = db.table('EventType')
                queryTable = tableEvent.innerJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
                cond = [tableEventType['code'].like(u'KBiR%'),
                        tableEvent['execDate'].isNull(),
                        tableEvent['client_id'].eq(eventEditor.clientId),
                        tableEvent['deleted'].eq(0),
                        tableEventType['deleted'].eq(0),
                        ]
                recordEvent = db.getRecordEx(queryTable, [tableEvent['id']], cond, u'Event.id DESC')
                eventId = forceRef(recordEvent.value('id')) if recordEvent else None
                row = self.currentIndex().row()
                model =self.model()
                rowCount = model.realRowCount() if hasattr(model, 'realRowCount') else model.rowCount()
                if 0 <= row < rowCount:
                    items = model.items()
                    item = items[row]
                    MKB = forceStringEx(item.value('MKB'))
                    if (MKB >= u'O00' and MKB <= u'O99.99') or (MKB >= u'Z30' and MKB <= u'Z39.99'):
                        isEnabled = True
                if isEnabled and eventId:
                    actionTypeIdListByKBiR = getActionTypeIdListByFlatCode(u'111/y-20')
                    if actionTypeIdListByKBiR:
                        tableAction = db.table('Action')
                        cond = [tableAction['event_id'].eq(eventId),
                                tableAction['deleted'].eq(0),
                                tableAction['actionType_id'].inlist(actionTypeIdListByKBiR),
                                tableAction['endDate'].isNull()
                                ]
                        record = db.getRecordEx(tableAction, [tableAction['id']], cond, u'Action.begDate DESC')
                        actionId = forceRef(record.value('id')) if record else None
        if self.__actCreateF111:
            self.__actCreateF111.setVisible(bool(eventEditor.clientSex == 2 and isVisible and not actionId))
            self.__actCreateF111.setEnabled(eventEditor.clientSex == 2 and isEnabled)
        if self.__actUpdateF111:
            self.__actUpdateF111.setVisible(eventEditor.clientSex == 2 and bool(isVisible and actionId))
            self.__actUpdateF111.setEnabled(eventEditor.clientSex == 2 and isEnabled)


    def addCreateF111(self, editor):
        if self._popupMenu is None:
            self.createPopupMenu()
        self.__actCreateF111 = QtGui.QAction(u'Создать карту беременной и родильницы', self)
        self._popupMenu.addAction(self.__actCreateF111)
        self.connect(self.__actCreateF111, SIGNAL('triggered()'), self.on_createF111)


    def on_createF111(self):
        if hasattr(self.model(), '_parent'):
            eventEditor = self.model()._parent
        elif hasattr(self.model(), 'eventEditor'):
            eventEditor = self.model().eventEditor
        else:
            eventEditor = QObject.parent(self.model()) # для 131 формы
        if eventEditor:
            if eventEditor.clientId and eventEditor.clientSex == 2:
                db = QtGui.qApp.db
                tableAction = db.table('Action')
                actionTypeIdList = getActionTypeIdListByFlatCode(u'111/y-20')
                if actionTypeIdList:
                    actionTypeId = actionTypeIdList[0]
#                    actionTypeId = None
#                    currentDate = QDate.currentDate()
#                    tableActionType = db.table('ActionType')
#                    cond =[tableActionType['id'].inlist(actionTypeIdList),
#                           tableActionType['deleted'].eq(0),
#                           db.joinOr([tableActionType['begDate'].isNull(), tableActionType['begDate'].dateLe(currentDate)]),
#                           db.joinOr([tableActionType['endDate'].isNull(), tableActionType['endDate'].dateGe(currentDate)]),
#                          ]
#                    record = db.getRecordEx(tableActionType, tableActionType['id'], cond)
#                    actionTypeId = forceRef(record.value('id')) if record else None
                    if actionTypeId:
                        dialog = CF111CreateDialog(self)
                        try:
                            actionType = CActionTypeCache.getById(actionTypeId)
                            defaultStatus = actionType.defaultStatus
                            defaultOrgId = actionType.defaultOrgId
                            defaultExecPersonId = actionType.defaultExecPersonId
                            newRecord = tableAction.newRecord()
                            newRecord.setValue('createDatetime', QVariant(QDateTime.currentDateTime()))
                            newRecord.setValue('createPerson_id',QVariant(QtGui.qApp.userId))
                            newRecord.setValue('modifyDatetime', QVariant(QDateTime.currentDateTime()))
                            newRecord.setValue('modifyPerson_id',QVariant(QtGui.qApp.userId))
                            newRecord.setValue('actionType_id',  QVariant(actionTypeId))
                            newRecord.setValue('status',         QVariant(defaultStatus))
                            newRecord.setValue('begDate',        QVariant(QDateTime.currentDateTime()))
                            newRecord.setValue('directionDate',  QVariant(QDateTime.currentDateTime()))
                            newRecord.setValue('org_id',         QVariant(defaultOrgId if defaultOrgId else QtGui.qApp.currentOrgId()))
                            newRecord.setValue('setPerson_id',   QVariant(QtGui.qApp.userId))
                            newRecord.setValue('person_id',      QVariant(defaultExecPersonId))
                            newRecord.setValue('id',             QVariant(None))
                            newRecord = preFillingActionRecordMSI(newRecord, actionTypeId)
                            prevMKB = None
                            row = self.currentIndex().row()
                            model =self.model()
                            rowCount = model.realRowCount() if hasattr(model, 'realRowCount') else model.rowCount()
                            if 0 <= row < rowCount:
                                items = model.items()
                                item = items[row]
                                prevMKB = forceStringEx(item.value('MKB'))
                            if prevMKB:
                                newRecord.setValue('MKB', QVariant(prevMKB))
                            newAction = CAction(record=newRecord)
                            if not newAction:
                                return
                            if u'Номер' in newAction.getType()._propertiesByName:
                                newAction[u'Номер'] = None
                            dialog.load(newAction.getRecord(), newAction, eventEditor.clientId)
                            if dialog.exec_():
                                pass
                        finally:
                            dialog.deleteLater()
                        counterController = QtGui.qApp.counterController()
                        if not counterController:
                            QtGui.qApp.setCounterController(CCounterController(self))


    def addUpdateF111(self, editor):
        if self._popupMenu is None:
            self.createPopupMenu()
        self.__actUpdateF111 = QtGui.QAction(u'Открыть карту беременной и родильницы', self)
        self._popupMenu.addAction(self.__actUpdateF111)
        self.connect(self.__actUpdateF111, SIGNAL('triggered()'), self.on_updateF111)


    def on_updateF111(self):
        if hasattr(self.model(), '_parent'):
            eventEditor = self.model()._parent
        elif hasattr(self.model(), 'eventEditor'):
            eventEditor = self.model().eventEditor
        else:
            eventEditor = QObject.parent(self.model()) # для 131 формы
        if eventEditor:
            if eventEditor.clientId and eventEditor.clientSex == 2:
                db = QtGui.qApp.db
                tableEvent = db.table('Event')
                tableEventType = db.table('EventType')
                queryTable = tableEvent.innerJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
                cond = [tableEventType['code'].like(u'KBiR%'),
                        tableEvent['execDate'].isNull(),
                        tableEvent['client_id'].eq(eventEditor.clientId),
                        tableEvent['deleted'].eq(0),
                        tableEventType['deleted'].eq(0),
                        ]
                recordEvent = db.getRecordEx(queryTable, [tableEvent['id']], cond, u'Event.id DESC')
                eventId = forceRef(recordEvent.value('id')) if recordEvent else None
                if eventId:
                    actionTypeIdListByKBiR = getActionTypeIdListByFlatCode(u'111/y-20')
                    if actionTypeIdListByKBiR:
                        tableAction = db.table('Action')
                        cond = [tableAction['event_id'].eq(eventId),
                                tableAction['deleted'].eq(0),
                                tableAction['actionType_id'].inlist(actionTypeIdListByKBiR),
                                tableAction['endDate'].isNull()
                                ]
                        record = db.getRecordEx(tableAction, [tableAction['id']], cond, u'Action.begDate DESC')
                        actionId = forceRef(record.value('id')) if record else None
                        if actionId:
                            dialog = CF111EditDialog(self)
                            try:
                                dialog.load(actionId)
                                if dialog.exec_():
                                    pass
                            finally:
                                dialog.deleteLater()

