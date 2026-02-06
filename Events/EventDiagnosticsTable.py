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
from PyQt4.QtCore import QVariant, SIGNAL, Qt, QObject, QDateTime

from library.Counter import CCounterController
from library.InDocTable import CInDocTableView
from library.Utils import forceRef, forceString, forceStringEx
from Events.Utils import getActionTypeIdListByFlatCode
from Events.Action import CAction, CActionTypeCache
from F111.F111CreateDialog import CF111CreateDialog
from F111.F111EditDialog import CF111EditDialog
from Registry.Utils import preFillingActionRecordMSI


class CDiagnosticsInDocTableView(CInDocTableView):
    def __init__(self, parent):
        CInDocTableView.__init__(self, parent)
        self.addPopupDelRow()
        self.setDelRowsChecker(self._delChecker)
        self.__actCopyDiagnosisToFinal = None
        self.__actCreateF111 = None
        self.__actUpdateF111 = None
        self._diagnisticsBridge = None
        self.connect(self._popupMenu, SIGNAL('aboutToShow()'), self.on_aboutToShow)

    def on_aboutToShow(self):
        if self.__actCopyDiagnosisToFinal:
            canCopyDiagnosisToFinal = bool(self._diagnisticsBridge) and self._diagnisticsBridge.canCopyDiagnosisToFinal(self.currentIndex())
            self.__actCopyDiagnosisToFinal.setEnabled(canCopyDiagnosisToFinal)
        isEnabled = False
        isVisible = False
        eventId = None
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
        if self.__actCreateF111:
            self.__actCreateF111.setVisible(bool(eventEditor.clientSex == 2 and isVisible and not eventId))
            self.__actCreateF111.setEnabled(eventEditor.clientSex == 2 and isEnabled)
        if self.__actUpdateF111:
            self.__actUpdateF111.setVisible(eventEditor.clientSex == 2 and bool(isVisible and eventId))
            self.__actUpdateF111.setEnabled(eventEditor.clientSex == 2 and isEnabled)


    def addCopyDiagnosisToFinal(self, editor):
        self._diagnisticsBridge = createDiagnosticBridge(editor, self.model())
        if self._diagnisticsBridge:
            if self._popupMenu is None:
                self.createPopupMenu()
            self.__actCopyDiagnosisToFinal = QtGui.QAction(u'Копировать в заключительный диагноз', self)
            self._popupMenu.addAction(self.__actCopyDiagnosisToFinal)
            self.connect(self.__actCopyDiagnosisToFinal, SIGNAL('triggered()'), self.on_copyDiagnosisToFinal)


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


    def _delChecker(self, rows):
        canRemove = False
        for row in rows:
            canRemove = self.model().payStatus(row) == 0
            if not canRemove:
                break
        return canRemove


    def on_deleteRows(self):
        rows = self.getSelectedRows()
        rows.sort(reverse=True)
        for row in rows:
            self.model().removeRowEx(row)

    def on_copyDiagnosisToFinal(self):
        if self._diagnisticsBridge:
            self._diagnisticsBridge.copyDiagnosisToFinal(self.currentIndex())


    def keyPressEvent(self, event):
        key = event.key()
        if key in (Qt.Key_Return, Qt.Key_Enter):
            QtGui.QTableView.keyPressEvent(self, event)
        else:
            CInDocTableView.keyPressEvent(self, event)



def createDiagnosticBridge(eventEditor, currentModel):
    modelFinalDiagnostics = modelPreliminaryDiagnostics = None
    if hasattr(eventEditor, 'modelPreliminaryDiagnostics'):
        modelPreliminaryDiagnostics = getattr(eventEditor, 'modelPreliminaryDiagnostics')
    if hasattr(eventEditor, 'modelFinalDiagnostics'):
        modelFinalDiagnostics = getattr(eventEditor, 'modelFinalDiagnostics')

    if not (modelFinalDiagnostics and modelPreliminaryDiagnostics) or currentModel != modelPreliminaryDiagnostics:
        return

    return CDiagnosticBridge(modelPreliminaryDiagnostics, modelFinalDiagnostics, eventEditor)


class CDiagnosticBridge(object):
    mainPreliminaryDiagnosisTypeId = None
    finalDiagnosisTypeId = None
    preliminaryDeathDiagnosisTypeId = None # for F106
    finalDeathDiagnosisTypeId = None
    def __init__(self, modelPreliminaryDiagnostics, modelFinalDiagnostics, eventEditor):
        self.modelPreliminaryDiagnostics = modelPreliminaryDiagnostics
        self.modelFinalDiagnostics = modelFinalDiagnostics
        self.eventEditor = eventEditor
        self._setProperties()

    @classmethod
    def _setProperties(cls):
        if cls.mainPreliminaryDiagnosisTypeId is None:
            cls.mainPreliminaryDiagnosisTypeId = forceRef(QtGui.qApp.db.translate('rbDiagnosisType', 'code', '7', 'id'))
        if cls.finalDiagnosisTypeId is None:
            cls.finalDiagnosisTypeId = forceRef(QtGui.qApp.db.translate('rbDiagnosisType', 'code', '1', 'id'))
        if cls.preliminaryDeathDiagnosisTypeId is None:
            cls.preliminaryDeathDiagnosisTypeId = forceRef(QtGui.qApp.db.translate('rbDiagnosisType', 'code', '8', 'id'))
        if cls.finalDeathDiagnosisTypeId is None:
            cls.finalDeathDiagnosisTypeId = forceRef(QtGui.qApp.db.translate('rbDiagnosisType', 'code', '4', 'id'))

    def copyDiagnosisToFinal(self, preliminaryIndex):
        if preliminaryIndex.isValid():
            preliminaryRow = preliminaryIndex.row()
            preliminaryRecord = self.modelPreliminaryDiagnostics.items()[preliminaryRow]
            newFinalRecord = self.modelFinalDiagnostics.getEmptyRecord()

            for idx in xrange(newFinalRecord.count()):
                fieldName = forceString(newFinalRecord.fieldName(idx))
                if fieldName == 'id':
                    value = QVariant()
                elif fieldName == 'person_id':
                    value = QVariant(self.eventEditor.getExecPersonId())
                elif fieldName == 'diagnosisType_id':
                    value = QVariant(self.getFinalDiagnosisTypeId())
                else:
                    value = preliminaryRecord.value(fieldName)
                newFinalRecord.setValue(fieldName, value)
            self.modelFinalDiagnostics.addRecord(newFinalRecord)
            self.modelFinalDiagnostics.emitAllChanged()


    def canCopyDiagnosisToFinal(self, preliminaryIndex):
        if preliminaryIndex.isValid():
            preliminaryRow = preliminaryIndex.row()
            if 0 <= preliminaryRow < len(self.modelPreliminaryDiagnostics.items()):
                preliminaryRecord = self.modelPreliminaryDiagnostics.items()[preliminaryRow]
                if forceRef(preliminaryRecord.value('diagnosisType_id')) == self.getMainPreliminaryDiagnosisTypeId():
                    eixistFinalDiagnosisTypeId = False
                    finalDiagnosisTypeId = self.getFinalDiagnosisTypeId()
                    for finalRecord in self.modelFinalDiagnostics.items():
                        if forceRef(finalRecord.value('diagnosisType_id')) == finalDiagnosisTypeId:
                            eixistFinalDiagnosisTypeId = True
                            break
                    return not eixistFinalDiagnosisTypeId
        return False


    def getMainPreliminaryDiagnosisTypeId(self):
        try:
            if self.modelPreliminaryDiagnostics.deathDiagnosisTypes:
                return CDiagnosticBridge.preliminaryDeathDiagnosisTypeId
        except:
            return CDiagnosticBridge.mainPreliminaryDiagnosisTypeId


    def getFinalDiagnosisTypeId(self):
        try:
            if self.modelFinalDiagnostics.deathDiagnosisTypes:
                return CDiagnosticBridge.finalDeathDiagnosisTypeId
        except:
            return CDiagnosticBridge.finalDiagnosisTypeId
