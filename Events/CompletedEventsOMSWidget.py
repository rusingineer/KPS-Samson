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
from PyQt4.QtCore import Qt, QDateTime
from library.DialogBase import CConstructHelperMixin
from library.InDocTable import CRecordListModel, CInDocTableCol, CDateInDocTableCol
from library.RecordLock import CRecordLockMixin
from library.Utils import forceInt, forceString, toVariant, forceDate
from Users.Rights import urEditEndDateEvent, urAdmin, urEditClosedEvent
    
from Events.Ui_CompletedEventsOMSWidget import Ui_CompletedEventsOMSWidget

class CCompletedEventsOMSWidget(QtGui.QDialog, CConstructHelperMixin, CRecordLockMixin, Ui_CompletedEventsOMSWidget):
    u"""
    Виджет контроля законченных случаев по ОМС, отображающий сведения о событии,
    связанные действия, соответствующие критериям, и осуществляющий перенос информации из сохраняемого события.
    """
    def __init__(self, eventRecord, prevEventId, parent = None):
        QtGui.QDialog.__init__(self, parent)
        CRecordLockMixin.__init__(self)
        self.setupUi(self)
        self.eventRecord = eventRecord
        self.eventId = forceInt(self.eventRecord.value('id'))
        self.prevEventId = prevEventId
        self.lockId = None
        self.addModels('Actions', CActionsModel(self))
        self.setModels(self.tblActions, self.modelActions, self.selectionModelActions)
        self.tblActions.horizontalHeader().setStretchLastSection(True)
        self.tblActions.verticalHeader().hide()
        self.modelActions.loadData(self.eventId)
        self.tblActions.resizeColumnsToContents()
        self.lblInfo.setWordWrap(True)
        self.lblCancel.setVisible(False)
        flags = self.windowFlags()
        flags &= ~Qt.WindowContextHelpButtonHint
        self.setWindowFlags(flags)
        self.formatInfo()
        self.initButtonBox()
        
    
    def formatInfo(self):
        u"""
        Форматирование информации о событии.
        """
        execDate = forceString(self.eventRecord.value('execDate'))
        MKB = forceString(self.eventRecord.value('MKB'))
        specialityName = forceString(self.eventRecord.value('specialityName'))
        lastName = forceString(self.eventRecord.value('lastName'))
        firstName = forceString(self.eventRecord.value('firstName'))
        patrName = forceString(self.eventRecord.value('patrName'))
        orgStructName = forceString(self.eventRecord.value('orgStructureName'))
        self.lblInfo.setText(u"""На пациента найдено аналогичное обращение, код карточки: {}
Дата выполнения: {}
{} {} {}{}{}, {}
Перенести в него данные?
""".format(self.eventId, 
           execDate,
           MKB + u',' if MKB else u'',
           specialityName + u',' if specialityName else u'',
           lastName + u' ' if lastName else u'',
           firstName + u' ' if firstName else u'',
           patrName if patrName else u'',
           orgStructName if orgStructName else u'',
           ))
    
    
    def initButtonBox(self):
        u"""
        Инициализирует buttonBox в соответствии с контролем checkCompletedEventsOMS и возможностью обновления события
        """
        btnOK = self.buttonBox.button(QtGui.QDialogButtonBox.Ok)
        btnCancel = self.buttonBox.button(QtGui.QDialogButtonBox.Cancel)
        control = forceInt(self.eventRecord.value('checkCompletedEventsOMS'))
        if control == 1:
            btnCancel.setVisible(True)
            btnCancel.setText(u'Нет')
        else:
            btnCancel.setVisible(False)
        self.lockId = self.lock('Event', self.eventId, shorted = 1)
        if self.lockId and (QtGui.qApp.userHasRight(urAdmin) or (QtGui.qApp.userHasRight(urEditEndDateEvent) and QtGui.qApp.userHasRight(urEditClosedEvent))):
            btnOK.setText(u'Да')
        else:
            if self.lockId:
                self.releaseLock(self.lockId)
                self.lockId = None
            btnOK.setVisible(False)
            btnCancel.setVisible(True)
            btnCancel.setText(u'Закрыть')
            self.lblCancel.setVisible(True)
    
    
    def closeEvent(self, event):
        u"""
        Переопределяет метод closeEvent(), для соответствия доступным buttonBox.
        """
        btnOK = self.buttonBox.button(QtGui.QDialogButtonBox.Ok)
        btnCancel = self.buttonBox.button(QtGui.QDialogButtonBox.Cancel)
        if not btnCancel.isVisible() and btnOK.text() == u'Да':
            try:
                self.updateEvent()
                event.accept()
            except:
                event.ignore()
        else:
            self.reject()
    
    
    def accept(self):
        u"""
        Обрабатывает сигнал accepted().
        Вызывает updateEvent(), а затем вызывает родительский accept().
        """
        self.updateEvent()
        QtGui.QDialog.accept(self)
    
    
    def updateEvent(self):
        u"""
        Обновляет принадлежность записей из Action, Visit, Event_FileAttach, TempInvalid событию.
        Для сохраняемого события и соответствующего ему Diagnostic удаляются записи (deleted=1), обновляются modifyPerson_id, modifyDatetime, note.
        Для обновляемого собыьтя обновляются execDate и setDate, если у сохраняемого события, даты начала подходящих действий меньше или дата конца больше.
        Если во время транзакции возникает какая-либо ошибка, изменения откатываются, блокировка события снимается.
        """
        db = QtGui.qApp.db
        db.transaction()
        try:
            tableEvent = db.table('Event')
            tableAction = db.table('Action')
            tableVisit = db.table('Visit')
            tableEventFileAttach = db.table('Event_FileAttach')
            tableTempInvalid = db.table('TempInvalid')
            tableDiagnostic = db.table('Diagnostic')
            newItems = db.getRecordList(tableAction, cols=[tableAction['begDate'], tableAction['endDate']], where = [tableAction['deleted'].eq(0), tableAction['event_id'].eq(self.prevEventId)])
            db.updateRecords(tableAction, tableAction['event_id'].eq(toVariant(self.eventId)), tableAction['event_id'].eq(self.prevEventId))
            db.updateRecords(tableVisit, tableVisit['event_id'].eq(toVariant(self.eventId)), tableVisit['event_id'].eq(self.prevEventId))
            db.updateRecords(tableEventFileAttach, tableEventFileAttach['master_id'].eq(toVariant(self.eventId)), tableEventFileAttach['master_id'].eq(self.prevEventId))
            db.updateRecords(tableTempInvalid, tableTempInvalid['event_id'].eq(toVariant(self.eventId)), tableTempInvalid['event_id'].eq(self.prevEventId))
            db.updateRecords(tableDiagnostic, [tableDiagnostic['deleted'].eq(toVariant(1)), tableDiagnostic['modifyPerson_id'].eq(toVariant(QtGui.qApp.userId)), tableDiagnostic['modifyDatetime'].eq(toVariant(QDateTime.currentDateTime()))], tableDiagnostic['event_id'].eq(self.prevEventId))
            
            prevRecord = db.getRecord(tableEvent, '*', self.prevEventId)
            prevRecord.setValue('deleted', toVariant(1))
            prevRecord.setValue('modifyPerson_id', toVariant(QtGui.qApp.userId))
            prevRecord.setValue('modifyDatetime', toVariant(QDateTime.currentDateTime()))
            note = forceString(prevRecord.value('note'))
            note += u"; Данные перемещены контролем законченного случая по ОМС в код карточки ".format(forceString(self.eventId))
            prevRecord.setValue('note', toVariant(note))
            db.updateRecord(tableEvent, prevRecord)
            
            
            minBegDate = None
            maxEndDate = None
            for item in self.modelActions.items():
                begDate = forceDate(item.value('begDate'))
                endDate = forceDate(item.value('endDate'))
                if begDate < minBegDate or not minBegDate:
                    minBegDate = begDate
                if endDate > maxEndDate or not maxEndDate:
                    maxEndDate = endDate
            for item in newItems:
                begDate = forceDate(item.value('begDate'))
                endDate = forceDate(item.value('endDate'))
                if begDate < minBegDate or not minBegDate:
                    minBegDate = begDate
                if endDate > maxEndDate or not maxEndDate:
                    maxEndDate = endDate
                    
            record = db.getRecord(tableEvent, '*', self.eventId)
            record.setValue('setDate', toVariant(minBegDate))
            record.setValue('execDate', toVariant(maxEndDate))
            db.updateRecord(tableEvent, record)
            db.commit()
            self.afterUpdate()
            self.releaseLock(self.lockId)
        except:
            db.rollback()
            self.releaseLock(self.lockId)
            QtGui.qApp.logCurrentException()
            raise
    
    
    def afterUpdate(self):
        if QtGui.qApp.checkGlobalPreference(u'23:obr', u'да'):
            QtGui.qApp.db.query('CALL InsertObr(%d);' % self.eventId)
        if hasattr(self.parent(), 'changeExaminServiceCode'):
            (id026, id047) = self.parent().changeExaminServiceCode
            sql = '''
                update Action
                left join ActionType on ActionType.id = Action.actionType_id
                left join rbService on rbService.id = ActionType.nomenclativeService_id 
                set Action.actionType_id = (case when rbService.infis regexp 'B04.026.001.0(01|02|05|06|09|10|17|18|21|22|25|26|37|38|39|40|41|42|53|55|56|59|62|63|65|66|67|68|69|70|71|72|73|74|75|76|77|78|79|80|71|72|83|86|87|88)' 
                                                    or rbService.infis regexp 'B04.026.002.0(13|14|15|16|17|18|19|20|21|22)' then %d
                                                    when rbService.infis regexp 'B04.047.001.0(01|02|05|06|09|10|17|18|21|22|25|26|37|38|39|40|41|42|54|56|57|60|63|64|66|67|68|69|70|71|72|73|74|75|76|77|78|79|80|71|72|83|84|85|86|87)'
                                                    or rbService.infis regexp 'B04.047.002.0(13|14|15|16|17|18|19|20|21|22)' then %d
                                                    else Action.actionType_id end)
                where Action.event_id = %d
            '''
            QtGui.qApp.db.query(sql % (forceInt(id026), forceInt(id047), self.eventId))
                    

class CActionsModel(CRecordListModel):
    def __init__(self, parent):
        CRecordListModel.__init__(self, parent)
        self.addCol(CInDocTableCol(u'Код и наименование', 'codeName', 100)).setReadOnly()
        self.addCol(CDateInDocTableCol(u'Дата выполнения', 'endDate', 2)).setReadOnly()
        self.addHiddenCol('begDate')


    def loadData(self, eventId):
        if eventId:
            stmt = u"""SELECT
                        Action.begDate,
                        Action.endDate, 
                        CONCAT(rbService.infis,\'|\', ActionType.name) AS codeName
                    FROM Action 
                        LEFT JOIN ActionType on ActionType.id = Action.actionType_id
                        LEFT JOIN ActionType_Service on ActionType_Service.master_id = ActionType.id
                        LEFT JOIN rbFinance on rbFinance.id = ActionType_Service.finance_id
                        LEFT JOIN rbService on rbService.id = ActionType_Service.service_id
                        WHERE
                        Action.event_id = {}
                        AND Action.status = 2
                        AND Action.endDate is not NULL
                        AND Action.org_id is NULL
                        AND Action.deleted = 0
                        AND (rbFinance.code is NULL or rbFinance.code = 2)
                        AND rbService.name NOT LIKE '%беремен%'
                        AND rbService.name NOT LIKE '%обращение по поводу%'
                        AND rbService.name NOT LIKE '%патронаж%'
                        AND rbService.name NOT LIKE '%инокраев%'
                        AND (
                            (rbService.infis LIKE 'B01%' AND SUBSTRING(rbService.infis, 5, 3) IN 
                            ('001','002','004','005','007','008','010','014','015','018','023','025',
                            '026','027','028','029','031','037','038','040','047','048','049','050',
                            '053','057','058','063','064','065','067'))
                            OR
                            (rbService.infis LIKE 'B02%' AND SUBSTRING(rbService.infis, 5, 3) IN ('001','031','047'))
                            )""".format(eventId)
            
            db = QtGui.qApp.db
            query = db.query(stmt)
            items = []
            while query.next():
                items.append(query.record())
            self.setItems(items)
        else:
            self.clearItems()