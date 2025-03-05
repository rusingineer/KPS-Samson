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

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, pyqtSignature, QAbstractTableModel, QVariant, QDate, QModelIndex

from Events.Action import CAction
from Events.ActionCreateDialog import CActionCreateDialog
from library.DialogBase import CDialogBase
from library.TableModel import CCol
from library.Utils import forceDateTime, forceString, toVariant, forceRef, forceInt

from Registry.AmbCardMixin import CAmbCardMixin


from Ui_RelatedActionListPage import Ui_RelatedActionListPage


class CRelatedActionListPage(CDialogBase, CAmbCardMixin, Ui_RelatedActionListPage):
    def __init__(self, parent=None):
        CDialogBase.__init__(self, parent)
        self.addModels('RelatedEventList', CRelatedActionListModel(self))
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setModels(self.tblRelatedActionList,  self.modelRelatedEventList, self.selectionModelRelatedEventList)
        self.btnOpen.setEnabled(False)
        self.btnAdd.setEnabled(False)
        self.btnDel.setEnabled(False)


    def getSelectedRows(self):
        model = self.tblRelatedActionList.model()
        rowCount = model.realRowCount() if hasattr(model, 'realRowCount') else model.rowCount()
        rowSet = set([index.row() for index in self.tblRelatedActionList.selectionModel().selectedIndexes() if 0<=index.row()<rowCount])
        result = list(rowSet)
        result.sort()
        return result


    def getSelectedItems(self):
        items = self.tblRelatedActionList.model().items()
        return [items[row] for row in self.getSelectedRows()]

    
    def nomenclatureGroupingRows(self, rows):
        model = self.tblRelatedActionList.model()
        for proxyRow in rows:
            group = model.items[proxyRow]
            if group[10] != group[11]:
                for subrow in rows:
                    if model.items[subrow][11] == group[10]:
                        return True
                QtGui.QMessageBox().warning(self,
                            u'Предупреждение!',
                            u'Невозможно добавить действие ({}) без группирующего действия.'.format(forceString(model.items[proxyRow][2])),
                            QtGui.QMessageBox.Ok,
                            QtGui.QMessageBox.Ok)
                return False
        return True
    

    @pyqtSignature('')
    def on_btnClose_clicked(self):
        self.eventEditor.relDialog.close()


    @pyqtSignature('')
    def on_btnAdd_clicked(self):
        selectedRows = self.getSelectedRows()
        if selectedRows:
            masterIds = []
            model = self.tblRelatedActionList.model()
            actionsTabsList = self.eventEditor.getActionsTabsList()
            for row in selectedRows:
                if model.items[row][5]:
                    masterIds.append(model.items[row][5])
            for class_ in actionsTabsList:
                actionModel = class_.tblAPActions.model()
                for row in actionModel.items():
                    if row.id:
                        masterIds.append(row.id)
            for row in selectedRows:
                if model.items[row][9] and model.items[row][9] not in masterIds:
                        QtGui.QMessageBox.warning(self,
                                         u'Предупреждение',
                                         u'Нельзя добавить в событие подчиненное действие ({}) без родительского!'.format(forceString(model.items[row][2])),
                                         QtGui.QMessageBox.Ok,
                                         QtGui.QMessageBox.Ok)
                        return False
            if QtGui.QMessageBox.warning(self,
                                         u'Подтверждение',
                                         u'Добавить выбранные мероприятия?',
                                         QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel,
                                         QtGui.QMessageBox.Cancel) == QtGui.QMessageBox.Yes:
                db = QtGui.qApp.db
                actionModels = {}
                if not self.nomenclatureGroupingRows(selectedRows):
                    return False
                for row in selectedRows:
                    actionId = model.items[row][5]
                    action = CAction(record=db.getRecord('Action', '*', actionId))
                    actionTypeId = model.items[row][7]
                    class_ = model.items[row][8]

                    actionsTab = actionsTabsList[class_]
                    actionModel = actionsTab.tblAPActions.model()
                    index = actionModel.index(actionModel.rowCount() - 1, 0)
                    actionModel.setData(index, toVariant(actionTypeId), presetAction = action, related = False)
                    model.existsActionList.append(actionId)
                    actionModels[actionsTab] = actionModel

                for row in sorted(selectedRows, reverse=True):
                    model.beginRemoveRows(QModelIndex(), row, row)
                    del model.items[row]
                    model.endRemoveRows()
                for actionModel in actionModels.values():
                    actionModel._groups.clear()
                    actionModel._group() 
                model.reset()
                

    @pyqtSignature('')
    def on_btnDel_clicked(self):
        selectedRows = self.getSelectedRows()
        if selectedRows:
            if QtGui.QMessageBox.warning(self,
                                                  u'Подтверждение',
                                                  u'Удалить выбранные мероприятия?',
                                                  QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel,
                                                  QtGui.QMessageBox.Cancel) == QtGui.QMessageBox.Yes:
                db = QtGui.qApp.db
                model = self.tblRelatedActionList.model()
                for row in selectedRows:
                    actionId = model.items[row][5]
                    record = db.getRecord('Action', '*', actionId)
                    record.setValue('deleted', QVariant(1))
                    db.updateRecord('Action', record)

                for row in sorted(selectedRows, reverse=True):
                    model.beginRemoveRows(QModelIndex(), row, row)
                    del model.items[row]
                    model.endRemoveRows()

                model.reset()


    @pyqtSignature('')
    def on_btnOpen_clicked(self):
        index = self.tblRelatedActionList.currentIndex()
        if index.isValid():
            row = index.row()
            model = self.tblRelatedActionList.model()
            actionId = model.items[row][5]
            clientId = model.items[row][6]
            if actionId:
                try:
                    db = QtGui.qApp.db
                    dialog = CActionCreateDialog(self)
                    newAction = CAction(record=db.getRecord('Action', '*', actionId))
                    if not newAction:
                        return
                    dialog.load(newAction.getRecord(), newAction, clientId)
                    dialog.setRecord(newAction.getRecord())
                    dialog.setReduced(True)
                    dialog.chkIsUrgent.setEnabled(True)
                    if dialog.exec_() and dialog.checkDataEntered(secondTry=True):
                        action = dialog.getAction()
                        actionId = action.save(None, idx=-1, checkModifyDate=False)
                finally:
                    dialog.deleteLater()


    @pyqtSignature('bool')
    def on_chkCurrentEvent_toggled(self, checked):
        self.tblRelatedActionList.model().loadData(checked, self.chkCurrentDate.isChecked())


    @pyqtSignature('QItemSelection, QItemSelection')
    def on_selectionModelRelatedEventList_selectionChanged(self, selected, deselected):
        selectedRows = self.getSelectedRows()
        self.btnOpen.setEnabled(len(selectedRows) == 1)
        self.btnAdd.setEnabled(bool(selectedRows))
        self.btnDel.setEnabled(bool(selectedRows))


    @pyqtSignature('bool')
    def on_chkCurrentDate_toggled(self, checked):
        self.tblRelatedActionList.model().loadData(self.chkCurrentEvent.isChecked(), checked)


class CRelatedActionListModel(QAbstractTableModel):
    column = [u'Дата начала', u'Дата окончания', u'Мероприятие', u'Исполнитель', u'Автор']
    def __init__(self, parent):
        QAbstractTableModel.__init__(self, parent)
        self.items = []
        self._cols = []


    def cols(self):
        self._cols = [CCol(u'Дата начала', ['begDate'], 20, 'l'),
                      CCol(u'Дата окончания', ['endDate'], 20, 'l'),
                      CCol(u'Мероприятие', ['actionTitle'], 40, 'l'),
                      CCol(u'Исполнитель', ['person_id'], 20, 'l'),
                      CCol(u'Автор', ['person_id'], 20, 'l')
                      ]
        return self._cols


    def columnCount(self, index = None):
        return 5


    def rowCount(self, index = None):
        return len(self.items)


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


    def setExistsActionList(self, existsActionList):
        self.existsActionList = existsActionList


    def setCurrentEventId(self, currentEventId):
        self.currentEventId = currentEventId

    def setClientId(self, clientId):
        self.clientId = clientId


    def loadData(self, isCurrentEvent=True, isCurrentDate=True):
        self.items = []
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        tablePWS = db.table('vrbPersonWithSpeciality')
        tableCreatePWS = db.table('vrbPersonWithSpeciality').alias('CPWS')
        tableActionType = db.table('ActionType')
        tableAction = db.table('Action')
        tableEPI = db.table('ActionExecutionPlan_Item')
        cols = [tableEvent['id'].alias('eventId'),
                tableAction['id'],
                tableEvent['client_id'],
                tableActionType['id'].alias('actionTypeId'),
                tableActionType['class'],
                tableAction['begDate'],
                tableAction['endDate'],
                tableActionType['code'],
                tableActionType['name'],
                tablePWS['name'].alias('namePerson'),
                tableCreatePWS['name'].alias('nameCreatedPerson'),
                tableAction['master_id'],
                tableEPI['group_id'],
                tableEPI['id'].alias('EPIID')
                ]

        cond = [tableEvent['deleted'].eq(0),
                tableEventType['context'].like(u'relatedAction%'),
                tableAction['deleted'].eq(0),
                tableEvent['client_id'].eq(self.clientId)
                ]

        if self.existsActionList:
            cond.append(tableAction['id'].notInlist(self.existsActionList))

        if isCurrentEvent:
            cond.append(tableEvent['prevEvent_id'].eq(self.currentEventId))

        if isCurrentDate:
            cond.append(tableAction['begDate'].dateEq(QDate.currentDate()))

        table = tableEvent.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
        table = table.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
        table = table.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        table = table.leftJoin(tablePWS, tablePWS['id'].eq(tableAction['person_id']))
        table = table.leftJoin(tableCreatePWS, tableCreatePWS['id'].eq(tableAction['createPerson_id']))
        table = table.leftJoin(tableEPI, tableEPI['action_id'].eq(tableAction['id']))
        records = db.getRecordList(table, cols, cond, 'Action.begDate')
        for record in records:
            item = [forceDateTime(record.value('begDate')),
                    forceDateTime(record.value('endDate')),
                    forceString(record.value('code')) + u' | ' + forceString(record.value('name')),
                    forceString(record.value('namePerson')),
                    forceString(record.value('nameCreatedPerson')),
                    forceRef(record.value('id')),
                    forceRef(record.value('client_id')),
                    forceRef(record.value('actionTypeId')),
                    forceInt(record.value('class')),
                    forceInt(record.value('master_id')),
                    forceInt(record.value('group_id')),
                    forceInt(record.value('EPIID')),
                    ]
            self.items.append(item)
        self.reset()