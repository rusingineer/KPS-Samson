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
from PyQt4.QtCore import Qt, QDate, QDateTime, pyqtSignature, SIGNAL, QString

from library.database        import CTableRecordCache
from library.DialogBase      import CDialogBase
from library.interchange import setLineEditValue, getLineEditValue, setTextEditHTML, getTextEditHTML, setCheckBoxValue, \
    getCheckBoxValue
from library.ItemsListDialog import CItemsListDialog, CItemEditorBaseDialog
from library.TableModel      import CTableModel, CCol, CTextCol, CDateTimeCol, CRefBookCol, CDesignationCol
from library.Utils           import toVariant, forceString, forceDateTime, forceRef, formatSex, formatShortNameInt, forceStringEx
from Users.Rights            import urSessionInformerExternal
from Orgs.Utils              import getOrgStructureName

from Users.Ui_InformerEditor import Ui_InformerMessageEditorDialog
from Users.Ui_InformerViewer import Ui_InformerPage
from Users.Ui_InformerFilter import Ui_InformerFilterDialog


class CInformerList(CItemsListDialog):
    def __init__(self, parent, forSelect=False):
        CItemsListDialog.__init__(self, parent, [
            CRefBookCol( u'Автор',        ['createPerson_id'], 'vrbPerson', 10),
            CDateTimeCol(u'Дата и время', ['createDatetime'], 20),
            CTextCol(    u'Тема',         ['subject'], 20),
            ], 'InformerMessage', ['createDatetime DESC'], filterClass=CInformerFilterClass)
        self.setWindowTitleEx(u'Список сообщений информатора')

        self._actDeleteRow = QtGui.QAction(u'Удалить запись', self)
        self._actDeleteRow.setObjectName('actDeleteRow')
        self.connect(self._actDeleteRow, SIGNAL('triggered()'), self.removeCurrentRow)
        self.tblItems.addPopupAction(self._actDeleteRow)


    def removeCurrentRow(self):
        db = QtGui.qApp.db
        itemId = self.tblItems.currentItemId()
        model = self.tblItems.model()
        cols = [ '`deleted` = 1',
                 '`modifyPerson_id` = %d' % (QtGui.qApp.userId),
                 "`modifyDatetime` = '%s'" % str(QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')),
               ]
        if model.confirmRemoveItem(self.parent(), itemId):
            QtGui.qApp.setWaitCursor()
            db.transaction()
            try:
                db.query('UPDATE `InformerMessage` SET %s WHERE `id` = %d' % (','.join(cols), itemId))
                db.commit()
                self.renewListAndSetTo()
            except:
                db.rollback()
                raise
            finally:
                QtGui.qApp.restoreOverrideCursor()


    def getItemEditor(self):
        return CInformerEditor(self)


    def select(self, props):
        table = self.model.table()
        cond = [ table['deleted'].eq(0) ]
        if props.get('chkAuthor', False):
            cond.append(table['createPerson_id'].eq(props.get('author', None)))
        if props.get('chkDate', False):
            cond.append(table['createDatetime'].dateGe(props.get('begDate', QDate())))
            cond.append(table['createDatetime'].dateLe(props.get('endDate', QDate())))
        if props.get('chkSubject', False):
            cond.append(table['subject'].contain(props.get('subject', '')))
        if props.get('chkRevisionInfo', False):
            cond.append(table['isRevisionInfo'].eq(1 if props.get('revisionInfo', 0)==0 else 0))
        if props.get('chkConstant', False):
            cond.append(table['isConstant'].eq(1 if props.get('constant', 0)==0 else 0))
        return QtGui.qApp.db.getIdList(table.name(), self.idFieldName, cond, self.order)


class CInformerFilterClass(CDialogBase, Ui_InformerFilterDialog):
    def __init__(self, parent = None):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.cmbAuthor.setSpecialityPresent(False)


    def setProps(self, props):
        self.chkConstant.setChecked(props.get('chkConstant', False))
        self.cmbConstant.setCurrentIndex(props.get('constant', 0))
        self.chkRevisionInfo.setChecked(props.get('chkRevisionInfo', False))
        self.cmbRevisionInfo.setCurrentIndex(props.get('revisionInfo', 0))
        self.chkSubject.setChecked(props.get('chkSubject', False))
        self.edtSubject.setText(props.get('subject', ''))
        self.chkAuthor.setChecked(props.get('chkAuthor', False))
        self.cmbAuthor.setValue(props.get('author', None))
        self.chkDate.setChecked(props.get('chkDate', False))
        self.edtBegDate.setDate(props.get('begDate', QDate()))
        self.edtEndDate.setDate(props.get('endDate', QDate()))


    def props(self):
        result = {}
        result['chkAuthor'] = self.chkAuthor.isChecked()
        result['chkRevisionInfo'] = self.chkRevisionInfo.isChecked()
        result['revisionInfo'] = self.cmbRevisionInfo.currentIndex()
        result['chkConstant'] = self.chkConstant.isChecked()
        result['constant'] = self.cmbConstant.currentIndex()
        result['chkSubject'] = self.chkSubject.isChecked()
        result['subject'] = self.edtSubject.text()
        result['author'] = self.cmbAuthor.value()
        result['chkDate'] = self.chkDate.isChecked()
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        return result


#
# ##########################################################################
#

class CInformerEditor(CItemEditorBaseDialog, Ui_InformerMessageEditorDialog):
    def __init__(self,  parent):
        CItemEditorBaseDialog.__init__(self, parent, 'InformerMessage')
        self.setupUi(self)
        self.setWindowTitleEx(u'Сообщение информатора')
        self.setupDirtyCather()


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        setLineEditValue( self.edtSubject, record, 'subject')
        setTextEditHTML(  self.edtText,    record, 'text')
        setCheckBoxValue(self.chkIsConstant, record, 'isConstant')
        self.setIsDirty(False)


    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        getLineEditValue( self.edtSubject, record, 'subject')
        getTextEditHTML(  self.edtText,    record, 'text')
        getCheckBoxValue(self.chkIsConstant, record, 'isConstant')
        return record


    def checkDataEntered(self):
        return True

#
# ##########################################################################
#

def getForShowInformer(quiet):
    db = QtGui.qApp.db
    personId = QtGui.qApp.userId
    tablePersonOrder = db.table('Person_Order')
    personOrderRecord = db.getRecordEx(tablePersonOrder,
                                       'max(date)',
                                       [ tablePersonOrder['master_id'].eq(personId),
                                         tablePersonOrder['type'].eq(0),
                                       ],
                                      )
    if personOrderRecord and not personOrderRecord.isNull(0):
        minDateTime = forceDateTime(personOrderRecord.value(0))
    else:
        minDateTime = None

    if not minDateTime:
        # fallback: если приёма на работу нет, то берём дату создания записи
        minDateTime = forceDateTime(db.translate('Person', 'id', personId, 'createDatetime'))

    table = db.table('InformerMessage')
    tableReadMark = db.table('InformerMessage_ReadMark')
    cond = [ tableReadMark['id'].isNull(),
             table['createDatetime'].ge(minDateTime),
             table['deleted'].eq(0),
           ]
    messageIdList = db.getDistinctIdList( table.leftJoin(tableReadMark,
                                                 [tableReadMark['master_id'].eq(table['id']), tableReadMark['person_id'].eq(QtGui.qApp.userId)]),
                                  table['id'].name(),
                                  cond,
                                  table['createDatetime'].name()
                                )
    tableEvent = db.table('Event')
    tableEventType = db.table('EventType')
    queryTable = tableEvent.innerJoin(tableEventType, db.joinAnd([tableEventType['id'].eq(tableEvent['eventType_id']),
                                                      db.joinAnd([tableEventType['context'].eq(u'flag'),
                                                                 tableEventType['code'].eq(u'flag')])]))
    cond = [tableEvent['execDate'].isNull(), tableEvent['deleted'].eq(0)]
    condCloseEvent = [tableEvent['execDate'].isNotNull(), tableEvent['deleted'].eq(0)]
    condPersonSNILS = []
    tablePerson = db.table('Person')
    if QtGui.qApp.informerShowPersonSNILS():
        SNILS = forceString(db.translate('Person', 'id', QtGui.qApp.userId, 'SNILS'))
        if not QtGui.qApp.informerShowNoSNILS():
            queryTable = queryTable.innerJoin(tablePerson, tablePerson['id'].eq(tableEvent['setPerson_id']))
        condPersonSNILS.append(tablePerson['deleted'].eq(0))
        condPersonSNILS.append(tablePerson['SNILS'].eq(SNILS))
    if QtGui.qApp.informerShowNoSNILS():
        if condPersonSNILS:
            queryTable = queryTable.leftJoin(tablePerson, db.joinAnd([tablePerson['id'].eq(tableEvent['setPerson_id']), tablePerson['deleted'].eq(0)]))
            cond.append(db.joinOr([db.joinAnd(condPersonSNILS), tableEvent['setPerson_id'].isNull()]))
            condCloseEvent.append(db.joinOr([db.joinAnd(condPersonSNILS), tableEvent['setPerson_id'].isNull()]))
        else:
            cond.append(tableEvent['setPerson_id'].isNull())
            condCloseEvent.append(tableEvent['setPerson_id'].isNull())
    elif condPersonSNILS:
        cond.append(db.joinAnd(condPersonSNILS))
        condCloseEvent.append(db.joinAnd(condPersonSNILS))
    tablePersonArea = db.table('Person').alias('PersonArea')
    if QtGui.qApp.informerShowByUserArea():
        if not QtGui.qApp.informerShowByUserNotArea():
            queryTable = queryTable.innerJoin(tablePersonArea, db.joinAnd([tablePersonArea['id'].eq(QtGui.qApp.userId), tablePersonArea['deleted'].eq(0)]))
        else:
            queryTable = queryTable.leftJoin(tablePersonArea, db.joinAnd([tablePersonArea['id'].eq(QtGui.qApp.userId), tablePersonArea['deleted'].eq(0)]))
    else:
        queryTable = queryTable.leftJoin(tablePersonArea, db.joinAnd([tablePersonArea['id'].eq(QtGui.qApp.userId), tablePersonArea['deleted'].eq(0)]))
    if QtGui.qApp.informerShowByUserArea():
        if not QtGui.qApp.informerShowByUserNotArea():
            cond.append('''(SELECT getPersonAttachCombinedAreaId(PersonArea.id, Event.client_id, PersonArea.orgStructure_id, %s)) IS NOT NULL'''%(db.formatDate(QDate.currentDate())))
            condCloseEvent.append('''(SELECT getPersonAttachCombinedAreaId(PersonArea.id, Event.client_id, PersonArea.orgStructure_id, %s)) IS NOT NULL'''%(db.formatDate(QDate.currentDate())))
        else:
            cond.append('''((SELECT getPersonAttachCombinedAreaId(PersonArea.id, Event.client_id, PersonArea.orgStructure_id, %s)) IS NOT NULL)
            OR ((SELECT getClientAreaIdForDate(Event.client_id, %s)) IS NULL)'''%(db.formatDate(QDate.currentDate()), db.formatDate(QDate.currentDate())))
            condCloseEvent.append('''((SELECT getPersonAttachCombinedAreaId(PersonArea.id, Event.client_id, PersonArea.orgStructure_id, %s)) IS NOT NULL)
            OR ((SELECT getClientAreaIdForDate(Event.client_id, %s)) IS NULL)'''%(db.formatDate(QDate.currentDate()), db.formatDate(QDate.currentDate())))
    if QtGui.qApp.informerShowByUserNotArea():
        if not QtGui.qApp.informerShowByUserArea():
            cond.append('(SELECT getClientAreaIdForDate(Event.client_id, %s)) IS NULL'%(db.formatDate(QDate.currentDate())))
            condCloseEvent.append('(SELECT getClientAreaIdForDate(Event.client_id, %s)) IS NULL'%(db.formatDate(QDate.currentDate())))
    cols = [tableEvent['id'].name()]
    if QtGui.qApp.informerShowByUserArea():
        cols.append('getClientAreaIdForDate(Event.client_id, %s) AS clientAreaId'%(db.formatDate(QDate.currentDate())))
    elif QtGui.qApp.informerShowByUserNotArea():
        cols.append(''' NULL AS clientAreaId''')
    else:
        cols.append('getClientAreaIdForDate(Event.client_id, %s) AS clientAreaId'%(db.formatDate(QDate.currentDate())))
    openEventIdList = []
    openEventIdDict = {}
    clientAreaCache = {}
    openEventRecords = db.getRecordList(queryTable,
                                  cols,
                                  cond,
                                  u'Event.setDate DESC'
                                )
    for openEventRecord in openEventRecords:
        openEventId = forceRef(openEventRecord.value('id'))
        if openEventId and openEventId not in openEventIdList:
            openEventIdList.append(openEventId)
            clientAreaId = forceRef(openEventRecord.value('clientAreaId'))
            clientAreaName = clientAreaCache.get(clientAreaId, u'')
            if not clientAreaName:
                clientAreaName = getOrgStructureName(clientAreaId)
                clientAreaCache[clientAreaId] = clientAreaName
            openEventIdDict[openEventId] = forceStringEx(clientAreaName)
    closeEventIdList = []
    closeEventIdDict = {}
    closeEventRecords = []
    if not quiet:
        closeEventRecords = db.getRecordList(queryTable,
                                      cols,
                                      condCloseEvent,
                                      u'Event.execDate DESC'
                                    )
    for closeEventRecord in closeEventRecords:
        closeEventId = forceRef(closeEventRecord.value('id'))
        if closeEventId and closeEventId not in closeEventIdList:
            closeEventIdList.append(closeEventId)
            clientAreaId = forceRef(closeEventRecord.value('clientAreaId'))
            clientAreaName = clientAreaCache.get(clientAreaId, u'')
            if not clientAreaName:
                clientAreaName = getOrgStructureName(clientAreaId)
                clientAreaCache[clientAreaId] = clientAreaName
            closeEventIdDict[closeEventId] = forceStringEx(clientAreaName)
    return db, messageIdList, openEventIdList, closeEventIdList, openEventIdDict, closeEventIdDict


def showInformer(widget, quiet):
    db, messageIdList, openEventIdList, closeEventIdList, openEventIdDict, closeEventIdDict = getForShowInformer(quiet)
    if messageIdList or (QtGui.qApp.userHasRight(urSessionInformerExternal) and (openEventIdList or (not quiet and closeEventIdList))):
        clientCache = CTableRecordCache(db, db.forceTable('Client'), u'*', capacity=None)
        informer = CInformer(widget, clientCache)
        informer.setCurrentWidget(0 if messageIdList else (1 if (openEventIdList or closeEventIdList) else 0))
        informer.setIdList(messageIdList)
        informer.setOpenEventIdList(openEventIdList)
        informer.setOpenEventIdDict(openEventIdDict)
        informer.setCloseEventIdList(closeEventIdList)
        informer.setCloseEventIdDict(closeEventIdDict)
        informer.setExternalEventFirstOpen()
        informer.exec_()
    elif not quiet:
        if not messageIdList:
            message = u'Нет непрочитанных сообщений'
        if (openEventIdList or closeEventIdList) and not QtGui.qApp.userHasRight(urSessionInformerExternal):
            message = u'Нет права доступа к внешним уведомлениям'
        QtGui.QMessageBox.information(widget,
                    u'Информатор',
                    message,
                    QtGui.QMessageBox.Close)


class CInformer(CDialogBase, Ui_InformerPage):
    def __init__(self, parent=None, clientCache={}):
        CDialogBase.__init__(self, parent)
        self.addModels('ExternalEvent', CExternalEventsTableModel(self, clientCache))
        self.addObject('btnPrev', QtGui.QPushButton(u'Предыдущее', self))
        self.addObject('btnNext',  QtGui.QPushButton(u'Следующее',  self))
        self.setupUi(self)
        self.setModels(self.tblExternalEvent, self.modelExternalEvent, self.selectionModelExternalEvent)
        self.tblExternalEvent.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.systemButtonBox.addButton(self.btnPrev, QtGui.QDialogButtonBox.ActionRole)
        self.systemButtonBox.addButton(self.btnNext, QtGui.QDialogButtonBox.ActionRole)
        db = QtGui.qApp.db
        self.messageCache = CTableRecordCache(db, 'InformerMessage')
        self.personCache = CTableRecordCache(db, 'vrbPerson')
        self.clientCache = clientCache
        self.idList = []
        self.openEventIdList = []
        self.openEventIdDict = {}
        self.closeEventIdList = []
        self.closeEventIdDict = {}
        self.markList = []
        self.currentIndex = None
        self.tabExternal.setFocusProxy(self.tblExternalEvent)
        self.setWindowTitleEx(u'Сообщение')
        self.tabInformer.setTabEnabled(self.tabInformer.indexOf(self.tabExternal), QtGui.qApp.userHasRight(urSessionInformerExternal))


    def setCurrentWidget(self, currentIndex=0):
        self.tabInformer.setCurrentIndex(currentIndex)


    def setIdList(self, idList):
        self.idList = idList
        self.markList = [None]*len(self.idList)
        self.setCurrentIndex(0)


    def setOpenEventIdList(self, openEventIdList):
        self.openEventIdList = openEventIdList


    def setCloseEventIdList(self, closeEventIdList):
        self.closeEventIdList = closeEventIdList


    def setOpenEventIdDict(self, openEventIdDict):
        self.openEventIdDict = openEventIdDict


    def setCloseEventIdDict(self, closeEventIdDict):
        self.closeEventIdDict = closeEventIdDict


    def setExternalEventFirstOpen(self):
        self.tblExternalEvent.setIdList(self.closeEventIdList if self.chkExternalShowEventsClosed.isChecked() else self.openEventIdList)
        self.tblExternalEvent.model().setEventIdDict(self.closeEventIdDict if self.chkExternalShowEventsClosed.isChecked() else self.openEventIdDict)


    def setCurrentIndex(self, index):
        notFirst = index>0
        notLast  = index<len(self.idList)-1
        self.currentIndex = index
        self.btnPrev.setEnabled(notFirst)
        self.btnNext.setEnabled(notLast)
        message = self.messageCache.get(self.idList[self.currentIndex]) if (0 < len(self.idList) and self.currentIndex < len(self.idList)) else None
        if message:
            createPersonId = forceRef(message.value('createPerson_id'))
            person = self.personCache.get(createPersonId)
            if person:
                personName = forceString(person.value('name'))
            else:
                personName = ''
            createDateTime = message.value('createDatetime').toDateTime()
            subject        = forceString(message.value('subject'))
            text           = forceString(message.value('text'))
        else:
            personName     = ''
            createDateTime = QDateTime()
            subject        = ''
            text           = ''
        self.lblSystemCreatePersonValue.setText(personName)
        self.lblSystemCreateDatetimeValue.setText(createDateTime.toString(Qt.LocaleDate))
        self.lblSystemSubjectValue.setText(subject)
        self.edtSystemText.setHtml(text)
        if message.value('isConstant') == 1:
            self.chkSystemMarkViewed.setEnabled(False)
            self.chkSystemMarkViewed.setChecked(False)
        else:
            self.chkSystemMarkViewed.setEnabled(True)
            self.chkSystemMarkViewed.setChecked(self.markList[self.currentIndex]==False if (0 < len(self.markList) and self.currentIndex < len(self.markList)) else False)
        if notLast:
            self.btnNext.setFocus(Qt.OtherFocusReason)
        else:
            self.buttonBox.button(QtGui.QDialogButtonBox.Close).setFocus(Qt.OtherFocusReason)


    def askSaveDiscardContinueEdit(self):
        for messageId, mark in zip(self.idList, self.markList):
            if mark == True: # т.к. бывает True/False/None
                self.markViewed(messageId)
            elif mark == False: # т.к. бывает True/False/None
                self.unmarkViewed(messageId)
        return self.cdDiscard


    def markViewed(self, messageId):
        db = QtGui.qApp.db
        table = db.table('InformerMessage_ReadMark')
        if not db.getRecordEx(table, '*', [table['master_id'].eq(messageId), table['person_id'].eq(QtGui.qApp.userId)]):
            record = table.newRecord()
            record.setValue('master_id', toVariant(messageId))
            record.setValue('person_id', toVariant(QtGui.qApp.userId))
            record.setValue('datetime', toVariant(QDateTime.currentDateTime()))
            db.insertRecord(table, record)


    def unmarkViewed(self, messageId):
        db = QtGui.qApp.db
        table = db.table('InformerMessage_ReadMark')
        db.deleteRecord(table, [table['master_id'].eq(messageId), table['person_id'].eq(QtGui.qApp.userId)])


    @pyqtSignature('bool')
    def on_chkSystemMarkViewed_toggled(self, checked):
        if 0 < len(self.markList) and self.currentIndex < len(self.markList):
            self.markList[self.currentIndex] = checked


    @pyqtSignature('')
    def on_btnPrev_clicked(self):
        if self.currentIndex>0 and 0 < len(self.markList) and self.currentIndex < len(self.markList):
            self.markList[self.currentIndex] = self.chkSystemMarkViewed.isChecked()
            self.setCurrentIndex(self.currentIndex-1)


    @pyqtSignature('')
    def on_btnNext_clicked(self):
        if self.currentIndex<len(self.idList)-1 and 0 < len(self.markList) and self.currentIndex < len(self.markList):
            self.markList[self.currentIndex] = self.chkSystemMarkViewed.isChecked()
            self.setCurrentIndex(self.currentIndex+1)


    @pyqtSignature('')
    def on_buttonBox_rejected(self):
        if 0 < len(self.markList) and self.currentIndex < len(self.markList):
            self.markList[self.currentIndex] = self.chkSystemMarkViewed.isChecked()
        self.close()


    @pyqtSignature('bool')
    def on_chkExternalShowEventsClosed_toggled(self, checked):
        QtGui.qApp.setWaitCursor()
        try:
            if not self.closeEventIdList and checked:
                db, messageIdList, openEventIdList, closeEventIdList, openEventIdDict, closeEventIdDict = getForShowInformer(False)
                self.setIdList(messageIdList)
                self.setOpenEventIdList(openEventIdList)
                self.setOpenEventIdDict(openEventIdDict)
                self.setCloseEventIdList(closeEventIdList)
                self.setCloseEventIdDict(closeEventIdDict)
                self.setExternalEventFirstOpen()
            else:
                self.setExternalEventFirstOpen()
            self.tblExternalEvent.model().reset()
            self.chkExternalMarkViewed.setChecked(False)
            self.chkExternalMarkViewed.setEnabled(not checked)
        finally:
            QtGui.qApp.restoreOverrideCursor()


    @pyqtSignature('bool')
    def on_chkExternalMarkViewed_toggled(self, checked):
        selectedIdList = self.tblExternalEvent.selectedItemIdList()
        if checked and selectedIdList and not self.chkExternalShowEventsClosed.isChecked():
            db = QtGui.qApp.db
            db.transaction()
            try:
                tableEvent = db.table('Event')
                db.updateRecords(tableEvent.name(), tableEvent['execDate'].eq(QDateTime.currentDateTime()), [tableEvent['id'].inlist(selectedIdList), tableEvent['deleted'].eq(0)])
                db.commit()
            except:
                db.rollback()
                raise
            QtGui.qApp.callWithWaitCursor(self, self.updateExternalEvent)


    def updateExternalEvent(self):
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        queryTable = tableEvent.innerJoin(tableEventType, db.joinAnd([tableEventType['id'].eq(tableEvent['eventType_id']),
                                                          db.joinAnd([tableEventType['context'].eq(u'flag'),
                                                                     tableEventType['code'].eq(u'flag')])]))
        self.closeEventIdList = db.getDistinctIdList(queryTable,
                                      tableEvent['id'].name(),
                                      [tableEvent['execDate'].isNotNull(), tableEvent['deleted'].eq(0)],
                                      u'Event.execDate DESC'
                                    )
        self.openEventIdList = db.getDistinctIdList(queryTable,
                                      tableEvent['id'].name(),
                                      [tableEvent['execDate'].isNull(), tableEvent['deleted'].eq(0)],
                                      u'Event.setDate DESC'
                                    )
        self.tblExternalEvent.setIdList(self.closeEventIdList if self.chkExternalShowEventsClosed.isChecked() else self.openEventIdList)
        self.tblExternalEvent.model().reset()


class CExternalEventsTableModel(CTableModel):
    class CLocClientColumn(CCol):
        def __init__(self, title, fields, defaultWidth, clientCache):
            CCol.__init__(self, title, fields, defaultWidth, 'l')
            self.clientCache = clientCache

        def format(self, values):
            val = values[0]
            clientId  = forceRef(val)
            clientRecord = self.clientCache.get(clientId)
            if clientRecord:
                name = formatShortNameInt(forceString(clientRecord.value('lastName')),
                   forceString(clientRecord.value('firstName')),
                   forceString(clientRecord.value('patrName')))
                name += u', ' + formatSex(clientRecord.value('sex'))
                name += u', ' + forceString(clientRecord.value('birthDate')) + u' (' +  forceString(clientRecord.value('id')) + u')'
                return toVariant(name)
            return CCol.invalid


    class CLocNoteCol(CTextCol):
        def __init__(self, title, fields, defaultWidth, alignment='l'):
            CTextCol.__init__(self, title, fields, defaultWidth, alignment)

        def format(self, values):
            charCount = self.defaultWidth()
            note = forceStringEx(values[0])
            if len(note) > charCount:
                noteLeft = QString(note).left(charCount) + u'...'
            else:
                noteLeft = note
            return toVariant(noteLeft)


    class CLocAreaCol(CTextCol):
        def __init__(self, title, fields, defaultWidth, alignment='l'):
            CTextCol.__init__(self, title, fields, defaultWidth, alignment)
            self.areaCache = {}

        def setAreaCache(self, cache):
            self.areaCache = cache

        def format(self, values):
            areaName = u''
            eventId = forceRef(values[0])
            if eventId:
                areaName = self.areaCache.get(eventId, None)
            return toVariant(areaName)


    def __init__(self, parent, clientCache):
        CTableModel.__init__(self, parent)
        self.addColumn(CExternalEventsTableModel.CLocClientColumn( u'Пациент', ['client_id'], 60, clientCache))
        self.addColumn(CDateTimeCol(u'Дата и время', ['createDatetime'],  10))
        self.addColumn(CExternalEventsTableModel.CLocNoteCol(u'Уведомление', ['note'], 128))
        self.addColumn(CDesignationCol(u'СНИЛС', ['setPerson_id'], ('Person', 'SNILS'), 20))
        self.addColumn(CExternalEventsTableModel.CLocAreaCol(u'Участок', ['id'], 128))
        self.clientCache = clientCache
        self.eventIdDict = {}
        self.setTable('Event')


    def setEventIdDict(self, eventIdDict):
        self.eventIdDict = eventIdDict
        self.cols()[4].setAreaCache(self.eventIdDict)


    def data(self, index, role=Qt.DisplayRole):
        row    = index.row()
        column = index.column()
        if column == 2:
            if role == Qt.ToolTipRole:
                (col, values) = self.getRecordValues(column, row)
                val = forceStringEx(values[0])
                note = u'''<html><head/><body><p><span><pre width="90%%" style="white-space: pre-wrap; white-space: -moz-pre-wrap; white-space: -pre-wrap; white-space: -o-pre-wrap; word-wrap: break-word">%s </pre></span></p></body></html>'''%(val)
                return toVariant(note)
        return CTableModel.data(self, index, role)

