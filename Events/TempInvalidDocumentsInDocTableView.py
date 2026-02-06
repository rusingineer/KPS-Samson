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
from PyQt4.QtCore import Qt, SIGNAL, QVariant, QDate, QDateTime, QEvent

from library.Utils                         import copyFields, exceptionToUnicode, forceBool, forceRef, forceStringEx, toVariant, forceString, forceDateTime, forceDate, forceInt
from library.InDocTable                    import CInDocTableView, CLocItemDelegate
from library.Counter                       import CCounterController
#from Registry.ClientRelationSimpleComboBox import CClientRelationSimpleComboBox
from Registry.Utils                        import getRightEditTempInvalid, deleteTempInvalidDocument, getDocumentExportSuccess, getTempInvalidDocumentPrevFssStatus, getDocumentExportId
from Events.Action                         import CAction, CActionTypeCache
from Events.Utils                          import getActionTypeIdListByFlatCode, checkTissueJournalStatusByActions
from Events.ActionTypeDialog               import CActionTypeDialogTableModel
from Events.ActionCreateDialog             import CTempInvalidActionCreateDialog
from Users.Rights                          import urRegTabEditExpertMC


#class CClientRelationDelegate(QtGui.QItemDelegate):
#    def __init__(self, parent=None):
#        QtGui.QItemDelegate.__init__(self, parent)
#
#
#    def commit(self):
#        editor = self.sender()
#        self.emit(SIGNAL('commitData(QWidget *)'), editor)
#
#
#    def commitAndCloseEditor(self):
#        editor = self.sender()
#        self.emit(SIGNAL('commitData(QWidget *)'), editor)
#        self.emit(SIGNAL('closeEditor(QWidget *,QAbstractItemDelegate::EndEditHint)'), editor, QtGui.QAbstractItemDelegate.NoHint)
#
#
#    def createEditor(self, parent, option, index):
#        model = index.model()
#        clientId = model.getTempInvalidClientId()
#        clientLowerId = None
#        if index.isValid():
#            row = index.row()
#            items = model.items()
#            if row >= 0 and row < len(items):
#                column = index.column()
#                item = items[row]
#                if column == CTempInvalidDocumentsInDocTableView.Col_ClientPrimumId:
#                    clientLowerId = forceRef(item.value(item.fieldName(CTempInvalidDocumentsInDocTableView.Col_ClientSecondId)))
#                elif column == CTempInvalidDocumentsInDocTableView.Col_ClientSecondId:
#                    clientLowerId = forceRef(item.value(item.fieldName(CTempInvalidDocumentsInDocTableView.Col_ClientPrimumId)))
#        editor = CClientRelationSimpleComboBox(parent, clientId)
#        editor.setClientLowerId(clientLowerId)
#        self.connect(editor, SIGNAL('commit()'), self.commit)
#        self.connect(editor, SIGNAL('editingFinished()'), self.commitAndCloseEditor)
#        return editor
#
#
#    def alignment(self):
#        return QVariant(Qt.AlignLeft + Qt.AlignTop)
#
#
#    def setEditorData(self, editor, index):
#        model = index.model()
#        value = model.data(index, Qt.EditRole)
#        editor.setValue(forceRef(value))
#
#
#    def setModelData(self, editor, model, index):
#        model = index.model()
#        value = editor.value()
#        model.setData(index, toVariant(value))


class CPlaceWorkItemDelegate(CLocItemDelegate):
    def __init__(self, parent):
        CLocItemDelegate.__init__(self, parent)


    def eventFilter(self, object, event):
        def editorIsEmpty():
            if isinstance(self.editor, QtGui.QLineEdit):
                return self.editor.text() == ''
            if  isinstance(self.editor, QtGui.QComboBox):
                return self.editor.currentIndex() == 0
#            if  isinstance(self.editor, CDateEdit):
#                return not self.editor.dateIsChanged()
            if  isinstance(self.editor, QtGui.QDateEdit):
                return not self.editor.date().isValid()
            return False
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Tab or event.key() == Qt.Key_Backtab:
                if self.editor is not None:
                    self.editor.keyPressEvent(event)
                self.parent().keyPressEvent(event)
                return True
            elif event.key() == Qt.Key_Return:
                return True
        return QtGui.QItemDelegate.eventFilter(self, object, event)


class CTempInvalidDocumentsInDocTableView(CInDocTableView):

    Col_IsExternal      = 0
    Col_Electronic      = 1
    Col_IssueDate       = 2
    Col_Serial          = 3
    Col_Number          = 4
    Col_Duplicate       = 5
    Col_DuplicateReason = 6
    Col_Busyness        = 7
    Col_PlaceWork       = 8
    Col_PrevNumber      = 9
    Col_PrevId          = 10
    Col_IssuePersonId   = 11
    Col_ExecPersonId    = 12
    Col_ChairPersonId   = 13
#    Col_ClientPrimumId  = 14
#    Col_ClientSecondId  = 15
    Col_LastId          = 14
    Col_Note            = 15
    Col_AnnulmentReason = 16

    def __init__(self, parent):
        CInDocTableView.__init__(self, parent)
#        self.clientRelationDelegate = CClientRelationDelegate(self)
#        self.setItemDelegateForColumn(CTempInvalidDocumentsInDocTableView.Col_ClientPrimumId, self.clientRelationDelegate)
#        self.setItemDelegateForColumn(CTempInvalidDocumentsInDocTableView.Col_ClientSecondId, self.clientRelationDelegate)
        self.placeWorkItemDelegate = CPlaceWorkItemDelegate(self)
        self.setItemDelegateForColumn(CTempInvalidDocumentsInDocTableView.Col_PlaceWork, self.placeWorkItemDelegate)
        self.resizeRowsToContents()
        self._CInDocTableView__actDirectionMC = None


    def enableColHide(self, column):
        header = self.horizontalHeader()
        header.hideSection(column)


    def showColHide(self, column):
        header = self.horizontalHeader()
        if header.isSectionHidden(column):
            header.showSection(column)


    def addPopupDuplicateCurrentRow(self):
        if self._popupMenu is None:
            self.createPopupMenu()
        self._CInDocTableView__actDuplicateCurrentRow = QtGui.QAction(u'Создать дубликат документа', self)
        self._CInDocTableView__actDuplicateCurrentRow.setObjectName('actDuplicateCurrentRow')
        self._popupMenu.addAction(self._CInDocTableView__actDuplicateCurrentRow)
        self.connect(self._CInDocTableView__actDuplicateCurrentRow, SIGNAL('triggered()'), self.on_duplicateCurrentRow)


    def addPopupDirectionMC(self):
        if self._popupMenu is None:
            self.createPopupMenu()
        self._CInDocTableView__actDirectionMC = QtGui.QAction(u'Создать направление на ВК', self)
        self._CInDocTableView__actDirectionMC.setObjectName('actDirectionMC')
        self._popupMenu.addAction(self._CInDocTableView__actDirectionMC)
        self.connect(self._CInDocTableView__actDirectionMC, SIGNAL('triggered()'), self.on_directionMC)


    def on_directionMC(self):
        eventEditor = self.model().eventEditor
        if eventEditor and eventEditor.preCreateDirectionMC():
            if not QtGui.qApp.counterController():
                QtGui.qApp.setCounterController(CCounterController(self))
            actions = []
            db = QtGui.qApp.db
            clientId = self.model().getTempInvalidClientId()
            tempInvalidId = self.model().getTempInvalidId()
            items = self.model().items()
            selectRowList = self.getSelectedRows()
            if selectRowList:
                selectRowList.sort()
                actionTypeIdList = getActionTypeIdListByFlatCode(u'inspection_disability%')
                if actionTypeIdList:
                    tableActionType = db.table('ActionType')
                    actionTypeIdList = db.getDistinctIdList(tableActionType, 'id', [tableActionType['id'].inlist(actionTypeIdList), tableActionType['showInForm'].eq(1), tableActionType['deleted'].eq(0)])
                    actionTypeId = None
                    if len(actionTypeIdList) > 1:
                        try:
                            dialog = CActionTypeDialogTableModel(self, actionTypeIdList)
                            if dialog.exec_():
                                actionTypeId = dialog.currentItemId()
                        finally:
                            dialog.deleteLater()
                    else:
                        actionTypeId = actionTypeIdList[0]
                    if actionTypeId and selectRowList:
                        action = None
                        tableAction = db.table('Action')
                        dialog = CTempInvalidActionCreateDialog(self)
                        try:
                            actionType = CActionTypeCache.getById(actionTypeId)
                            defaultStatus = actionType.defaultStatus
                            defaultOrgId = actionType.defaultOrgId
                            newRecord = tableAction.newRecord()
                            newRecord.setValue('createDatetime',  toVariant(QDateTime.currentDateTime()))
                            newRecord.setValue('createPerson_id', toVariant(QtGui.qApp.userId))
                            newRecord.setValue('modifyDatetime',  toVariant(QDateTime.currentDateTime()))
                            newRecord.setValue('modifyPerson_id', toVariant(QtGui.qApp.userId))
                            newRecord.setValue('actionType_id',   toVariant(actionTypeId))
                            newRecord.setValue('status',          toVariant(defaultStatus))
                            newRecord.setValue('begDate',         toVariant(QDateTime.currentDateTime()))
                            newRecord.setValue('directionDate',   toVariant(QDateTime.currentDateTime()))
                            newRecord.setValue('org_id',          toVariant(defaultOrgId if defaultOrgId else QtGui.qApp.currentOrgId()))
                            newRecord.setValue('setPerson_id',    toVariant(QtGui.qApp.userId))
                            begDateLastPeriod = eventEditor.begDateLastPeriod()
                            newRecord.setValue('plannedEndDate',   toVariant(begDateLastPeriod if (begDateLastPeriod and begDateLastPeriod > QDate.currentDate()) else QDateTime.currentDateTime()))
                            if eventEditor._record.value('diagnosis_id').toInt()[0] != 0:
                                tableDiagnosis = db.table('Diagnosis')
                                queryDiagnosis = db.query(db.selectDistinctStmt(tableDiagnosis, where=[tableDiagnosis['id'].eq(eventEditor._record.value('diagnosis_id').toInt()[0])]))
                                if queryDiagnosis.next():
                                    recordDiagnosis = queryDiagnosis.record()
                                    mkb = forceString(recordDiagnosis.value('MKB'))
                                    if mkb:
                                        newRecord.setValue('MKB', toVariant(mkb))
                            newAction = CAction(record=newRecord)
                            newAction.updatePresetValuesConditions({'clientId': eventEditor.clientId})
                            newAction.initPresetValues()
                            record = items[selectRowList[0]]
                            newAction = self.setNumberVUT(newAction, record, tempInvalidId, clientId)
                            if not newAction:
                                QtGui.qApp.setCounterController(None)
                                return
                            dialog.load(newAction.getRecord(), newAction, clientId)
                            dialog.btnPrint.setEnabled(False)
                            if dialog.exec_() and dialog.checkDataEntered(secondTry=True):
                                action = dialog.getAction()
                                dialog.btnPrint.setEnabled(True)
                        finally:
                            dialog.deleteLater()
                        if action:
                            actions.append(action)
                            selectRowList.pop(0)
                            for row in selectRowList:
                                record = items[row]
                                newRecord = tableAction.newRecord()
                                copyFields(newRecord, action.getRecord())
                                newRecord.setValue('id', toVariant(None))
                                newRecord.setValue('idx', toVariant(0))
                                newAction = CAction(record=newRecord)
                                newAction.updateByAction(action)
                                newAction = self.setNumberVUT(newAction, record, tempInvalidId, clientId)
                                if not newAction:
                                    QtGui.qApp.setCounterController(None)
                                    return
                                actions.append(newAction)
                            if actions:
                                tableEvent = db.table('Event')
                                tableEventType = db.table('EventType')
#                                tempInvalidId = self.model().getTempInvalidId()
                                if tempInvalidId:
                                    queryTable = tableEvent.innerJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
                                    cond = [tableEvent['tempInvalid_id'].eq(tempInvalidId),
                                            tableEventType['context'].like(u'inspection%'),
                                            tableEvent['execDate'].isNull(),
                                            tableEvent['client_id'].eq(clientId),
                                            tableEvent['deleted'].eq(0),
                                            tableEventType['deleted'].eq(0),
                                            ]
                                    recordEvent = db.getRecordEx(queryTable, 'Event.*', cond, u'Event.id DESC')
                                    eventId = forceRef(recordEvent.value('id')) if recordEvent else None
                                    if eventId:
                                        self.saveMedicalCommissionActions(actions, recordEvent, eventId)
                                    else:
                                        recordEventType = db.getRecordEx(tableEventType, [tableEventType['id']], [tableEventType['context'].like(u'inspection%'), tableEventType['deleted'].eq(0)], u'EventType.id')
                                        eventTypeId = forceRef(recordEventType.value('id')) if recordEventType else None
                                        if eventTypeId:
                                            recordEvent = tableEvent.newRecord()
                                            recordEvent.setValue('createDatetime', toVariant(QDateTime.currentDateTime()))
                                            recordEvent.setValue('createPerson_id',toVariant(QtGui.qApp.userId))
                                            recordEvent.setValue('modifyDatetime', toVariant(QDateTime.currentDateTime()))
                                            recordEvent.setValue('modifyPerson_id',toVariant(QtGui.qApp.userId))
                                            recordEvent.setValue('setDate',        toVariant(QDateTime.currentDateTime()))
                                            recordEvent.setValue('eventType_id',   toVariant(eventTypeId))
                                            recordEvent.setValue('client_id',      toVariant(clientId))
                                            recordEvent.setValue('relegatePerson_id', toVariant(QtGui.qApp.userId))
                                            recordEvent.setValue('relegateOrg_id', toVariant(QtGui.qApp.currentOrgId()))
                                            recordEvent.setValue('tempInvalid_id', toVariant(tempInvalidId))
                                            eventId = db.insertRecord(tableEvent, recordEvent)
                                            if eventId:
                                                recordEvent.setValue('id', toVariant(eventId))
                                                self.saveMedicalCommissionActions(actions, recordEvent, eventId)
            QtGui.qApp.setCounterController(None)
            eventEditor.medicalCommissionLoadItems()


    def setNumberVUT(self, action, record, tempInvalidId, clientId):
        eventEditor = self.model().eventEditor
        if eventEditor:
            currentRow = self.currentIndex().row()
            actionType = action.getType()
            number = forceString(record.value('number'))
            if number:
                if u'Номер ЛН' in actionType._propertiesByName:
                    action[u'Номер ЛН'] = number
                else:
                    eventEditor.checkValueMessage(u'Создание Действия ВК!\nОтсутствует Свойство "Номер ЛН"!\nРегистрация направления на ВК невозможна!', False, eventEditor.tblDocuments, currentRow, self.model().items()[currentRow].indexOf('number'))
                    return None
            else:
                isNumberDisabilityFill = QtGui.qApp.controlNumberDisabilityFill()
                tempInvalidNextId = None
                if isNumberDisabilityFill and tempInvalidId:
                    db = QtGui.qApp.db
                    table = db.table('TempInvalid')
                    lastRecord = db.getRecordEx(table, [table['id']], [table['prev_id'].eq(tempInvalidId), table['deleted'].eq(0), table['client_id'].eq(clientId), table['type'].eq(eventEditor.type_)], 'endDate ASC')
                    tempInvalidNextId = forceRef(lastRecord.value('id')) if lastRecord else None
                skipable = bool(not forceBool(record.value('electronic')) and not forceRef(record.value('last_id')) and not tempInvalidNextId) if isNumberDisabilityFill else False
                res = eventEditor.checkValueMessage( u'Создание Действия ВК!\nОтсутствует номер документа ВУТ!\nРегистрация направления на ВК невозможна!', skipable, eventEditor.tblDocuments, currentRow, self.model().items()[currentRow].indexOf('number'))
                if not res:
                    return None
                elif skipable:
                    tempInvalidDocumentId = forceString(record.value('id'))
                    if tempInvalidDocumentId:
                        if u'Номер ЛН' in actionType._propertiesByName:
                            action[u'Номер ЛН'] = u'#' + tempInvalidDocumentId
                        else:
                            eventEditor.checkValueMessage(u'Создание Действия ВК!\nОтсутствует Свойство "Номер ЛН"!\nРегистрация направления на ВК невозможна!', False, eventEditor.tblDocuments, currentRow, self.model().items()[currentRow].indexOf('number'))
                            return None
                    else:
                        eventEditor.checkValueMessage(u'Создание Действия ВК!\nОтсутствует id документа ВУТ!\nРегистрация направления на ВК невозможна!', False, eventEditor.tblDocuments, currentRow, self.model().items()[currentRow].indexOf('number'))
                        return None
            return action
        else:
            return None


    def saveMedicalCommissionActions(self, actions, recordEvent = None, eventId = None):
        actionIdList = []
        try:
            try:
                db = QtGui.qApp.db
                db.transaction()
                for idx, action in enumerate(actions):
                    id = action.save(eventId, idx, checkModifyDate = False)
                    if id:
                        actionIdList.append(id)
                        action.getRecord().setValue('id', toVariant(id))
                        checkTissueJournalStatusByActions([(action.getRecord(), action)])
                        if action.getType().closeEvent and recordEvent:
                            eventExecDate = forceDate(recordEvent.value('execDate'))
                            actionEndDate = forceDateTime(action.getRecord().value('endDate'))
                            if not eventExecDate and actionEndDate:
                                recordEvent.setValue('execDate', QVariant(actionEndDate))
                                recordEvent.setValue('isClosed', QVariant(1))
                    if recordEvent:
                        db.updateRecord('Event', recordEvent)
                db.commit()
            except:
                db.rollback()
                raise
        except Exception, e:
            QtGui.qApp.logCurrentException()
            QtGui.QMessageBox.critical( self,
                                        u'',
                                        exceptionToUnicode(e),
                                        QtGui.QMessageBox.Close)
        return actionIdList


    def addPopupDelRow(self):
        if self._popupMenu is None:
            self.createPopupMenu()
        self._CInDocTableView__actDeleteRows = QtGui.QAction(u'Удалить строку', self)
        self._CInDocTableView__actDeleteRows.setObjectName('actDeleteRows')
        self._popupMenu.addAction(self._CInDocTableView__actDeleteRows)
        self.connect(self._CInDocTableView__actDeleteRows, SIGNAL('triggered()'), self.on_deleteCurrentRow)


    def on_deleteCurrentRow(self):
        if QtGui.QMessageBox.question(self,
                u'Удаление документа', u'Вы действительно хотите удалить документ?',
                QtGui.QMessageBox.Yes|QtGui.QMessageBox.No,
                QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
            currentRow = self.currentIndex().row()
            items = self.model().items()
            if currentRow < len(items):
                item = items[currentRow]
                tempInvalidId = self.model().getTempInvalidId()
                clientId = self.model().getTempInvalidClientId()
                tempInvalidDocumentId = forceRef(item.value('id'))
                if not tempInvalidId:
                    tempInvalidId = forceRef(item.value('master_id'))
                if tempInvalidId and getRightEditTempInvalid(tempInvalidId):
                    if tempInvalidDocumentId:
                        res1, res2 = QtGui.qApp.call(self, deleteTempInvalidDocument, (self, clientId, tempInvalidId, tempInvalidDocumentId,))
                        if res1 and res2:
                            self.model().removeRow(currentRow)
                    else:
                        self.model().removeRow(currentRow)
                elif not tempInvalidId and not tempInvalidDocumentId:
                    self.model().removeRow(currentRow)


    def on_duplicateCurrentRow(self):
        currentRow = self.currentIndex().row()
        items = self.model().items()
        if currentRow < len(items):
            item = items[currentRow]
            newRecord = self.model().getEmptyRecord()
            copyFields(newRecord, item)
            newRecord.setValue('id', None)
            newRecord.setValue('issueDate', QDate.currentDate())
            newRecord.setValue('serial',   '')
            newRecord.setValue('number',   '')
            newRecord.setValue('duplicate', True)
#            userId = QtGui.qApp.userId
#            self.chairUser = forceBool(QtGui.qApp.db.translate('Person', 'id', userId, 'chairPerson')) if userId else False
#            if self.chairUser:
#                newRecord.setValue('chairPerson_id', toVariant(userId))
            newRecord.setValue('person_id',     QtGui.qApp.userId)
            newRecord.setValue('execPerson_id', QtGui.qApp.userId)
            newRecord.setValue('electronic', False)
            newRecord.setValue('prevDuplicate_id', item.value('id'))
            newRecord.setValue('note', '')
            newRecord.setValue('annulmentReason_id', None)
            newRecord.setValue(self.model()._idFieldName, toVariant(None))
            newCareRecords = []
            db = QtGui.qApp.db
            careItems = item.tempInvalidCare.getItems()
            for careItem in careItems:
                newCareRecord = db.table('TempInvalidDocument_Care').newRecord()
                copyFields(newCareRecord, careItem)
                newCareRecord.setValue('id', toVariant(None))
                newCareRecords.append(newCareRecord)
            newRecord.tempInvalidCare.setItems(newCareRecords)
            self.model().insertRecord(currentRow+1, newRecord)


    def addPopupDetermineContinued(self):
        if self._popupMenu is None:
            self.createPopupMenu()
        self._CInDocTableView__actDetermineContinued = QtGui.QAction(u'Определить продолжение ЛН', self)
        self._CInDocTableView__actDetermineContinued.setObjectName('actDetermineContinued')
        self._popupMenu.addAction(self._CInDocTableView__actDetermineContinued)
        self.connect(self._CInDocTableView__actDetermineContinued, SIGNAL('triggered()'), self.on_determineContinued)


    def on_determineContinued(self):
        from Events.TempInvalidEditDialog import CTempInvalidDocumentProlongDialog
        nextItems = []
        resItems = []
        nextDocumentId = None
        model = self.model()
        currentRow = self.currentIndex().row()
        items = model.items()
        lastId = model.getTempInvalidLastId()
        item = self.model().items()[currentRow]
        docLastId = forceRef(item.value('last_id'))
        if not docLastId and lastId and currentRow >= 0 and currentRow < len(items):
            placeWork = forceStringEx(item.value('placeWork'))
            busyness = forceInt(item.value('busyness'))
            db = QtGui.qApp.db
            table = db.table('TempInvalidDocument')
            cond = [table['master_id'].eq(lastId),
                    table['placeWork'].eq(placeWork),
                    table['busyness'].eq(busyness),
                    table['deleted'].eq(0),
                    table['prev_id'].isNull(),
                    u'''TempInvalidDocument.prevNumber = '' '''
                   ]
            nextItems = db.getRecordList(table, u'*', cond, u'TempInvalidDocument.issueDate DESC')
            if nextItems:
                resItems = []
                dialog = CTempInvalidDocumentProlongDialog(self, model.clientCache, nextItems)
                try:
                    dialog.setWindowTitle(u'Выбрать Документ потомок!')
                    if dialog.exec_():
                        resItems = dialog.getItems()
                finally:
                    dialog.deleteLater()
            for resItem in resItems:
                nextDocumentId = forceRef(resItem.value('id'))
                personId = forceRef(resItem.value('person_id'))
            if nextDocumentId:
                self.model().items()[currentRow].setValue('last_id', toVariant(nextDocumentId))
                self.model().items()[currentRow].setValue('execPerson_id', toVariant(personId))
            self.model().reset()


    def on_popupMenu_aboutToShow(self):
        CInDocTableView.on_popupMenu_aboutToShow(self)
        model = self.model()
        row = self.currentIndex().row()
        rowCount = model.realRowCount() if hasattr(model, 'realRowCount') else model.rowCount()
        if self._CInDocTableView__actDeleteRows:
            self._CInDocTableView__actDeleteRows.setText(u'Удалить текущую строку')
            enabledDeleteRows = bool(0 <= row < rowCount)
            if model.documentsSignatureR:
                enabledDeleteRows = False
            if model.documentsSignatureExternalR:
                if 0 <= row < len(model._items):
                    record = model._items[row]
                    if forceBool(record.value('isExternal')):
                        enabledDeleteRows = False
            if model.documentsSignatures:
                if 0 <= row < len(model._items):
                    record = model._items[row]
                    documentId = forceRef(record.value('id'))
                    documentExportId = getDocumentExportSuccess(documentId)
                    if not documentExportId:
                        documentExportId = getTempInvalidDocumentPrevFssStatus(documentId)
                    if documentExportId:
                        enabledDeleteRows = False
                    else:
                        documentExportId = getDocumentExportId(documentId)
                        if not documentExportId:
                            documentsSignaturesDict = model.documentsSignatures.get(documentId, {})
                            documentsSignaturesLineC = documentsSignaturesDict.get(u'C', [])
                            if documentsSignaturesLineC:
                                enabledDeleteRows = False
                            else:
                                documentsSignaturesLineD = documentsSignaturesDict.get(u'D', [])
                                if documentsSignaturesLineD:
                                    enabledDeleteRows = False
            elif 0 <= row < len(model._items):
                record = model._items[row]
                documentId = forceRef(record.value('id'))
                documentExportId = getDocumentExportSuccess(documentId)
                if not documentExportId:
                    documentExportId = getTempInvalidDocumentPrevFssStatus(documentId)
                if documentExportId:
                    enabledDeleteRows = False
            self._CInDocTableView__actDeleteRows.setEnabled(enabledDeleteRows)
        if self._CInDocTableView__actDuplicateCurrentRow:
            isEnabled = False
            if 0 <= row < rowCount:
                item = model.items()[row]
                if not forceBool(item.value('duplicate')) and forceStringEx(item.value('number')):
                   isEnabled = True
            self._CInDocTableView__actDuplicateCurrentRow.setEnabled(isEnabled)
        if self._CInDocTableView__actDirectionMC:
            self._CInDocTableView__actDirectionMC.setEnabled(0 <= row < rowCount and QtGui.qApp.userHasRight(urRegTabEditExpertMC))
        if self._CInDocTableView__actDetermineContinued:
            isEnabled = False
            if 0 <= row < rowCount:
                item = model.items()[row]
                if not forceRef(item.value('last_id')) and  forceInt(item.value('busyness')) > 1 and model.getTempInvalidLastId():
                   isEnabled = True
            self._CInDocTableView__actDetermineContinued.setEnabled(isEnabled)

