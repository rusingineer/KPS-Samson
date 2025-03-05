# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2014 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
##
## Форма 025Тр: нечто для травмы.
##
#############################################################################

import codecs
from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDate, QDateTime, pyqtSignature

from library.Attach.AttachAction import getAttachAction
from library.ICDUtils           import getMKBName
from library.interchange        import getComboBoxValue, getDatetimeEditValue, getLineEditValue, getRBComboBoxValue, setComboBoxValue, setDatetimeEditValue, setLineEditValue, setRBComboBoxValue
from library.PrintInfo          import CInfoContext
from library.PrintTemplates     import applyTemplateInt
from library.Utils              import forceDate, forceInt, forceRef, forceString, forceStringEx, toVariant

from Events.EventEditDialog     import CEventEditDialog
from Events.Utils               import checkDiagnosis, getDiagnosisId2, getEventShowTime, orderTexts
from Orgs.Utils                 import getPersonInfo
from Registry.Utils             import CClientInfo
from Users.Rights               import urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry, urCanReadClientVaccination, urCanEditClientVaccination

from F025.Ui_F025Tr             import Ui_Dialog


class CF025TrDialog(CEventEditDialog, Ui_Dialog):
    defaultMKB = 'Z04.1'
    defaultOrder = 2

    def __init__(self, parent):
# ctor
        CEventEditDialog.__init__(self, parent)
        self.diagnosticRecord = None
        self.availableDiagnostics = []
        self.mapSpecialityIdToDiagFilter = {}

# ui
        self.addObject('actEditClient', QtGui.QAction(u'Открыть регистрационную карточку', self))
        self.addObject('actPortal_Doctor', QtGui.QAction(u'Перейти на портал врача', self))
        self.addObject('actShowAttachedToClientFiles', getAttachAction('Client_FileAttach',  self))
        self.addObject('actOpenClientVaccinationCard', QtGui.QAction(u'Открыть прививочную карту', self))
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setWindowTitleEx(u'"Карточка травматика" Ф.025')

# tables to rb and combo-boxes
        self.cmbTraumaType.setTable('rbTraumaType', False)

# popup menus
        self.txtClientInfoBrowser.actions.append(self.actEditClient)
        self.txtClientInfoBrowser.actions.append(self.actPortal_Doctor)
        self.txtClientInfoBrowser.actions.append(self.actShowAttachedToClientFiles)
        self.txtClientInfoBrowser.actions.append(self.actOpenClientVaccinationCard)
        self.actOpenClientVaccinationCard.setEnabled(QtGui.qApp.userHasAnyRight([urCanReadClientVaccination, urCanEditClientVaccination]))
        self.actEditClient.setEnabled(QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]))

        self.setupDirtyCather()
        self.setIsDirty(False)
        self.setupVisitsIsExposedPopupMenu()
# done


    def exec_(self):
        result = CEventEditDialog.exec_(self)
        if result:
                self.print_()
        return result


    def prepare(self, clientId, eventTypeId, orgId, personId, eventSetDatetime, eventDatetime, weekProfile,
                numDays, externalId, assistantId, curatorId, flagHospitalization = False,
                actionTypeIdValue = None, valueProperties = [], tissueTypeId=None,
                selectPreviousActions=False, relegateOrgId = None, relegatePersonId=None, diagnos = None,
                financeId = None, protocolQuoteId = None, actionByNewEvent = [], order = 1,
                actionListToNewEvent = [], typeQueue = -1, docNum=None, relegateInfo=[], plannedEndDate = None,
                mapJournalInfoTransfer = [], voucherParams = {}):
        self.eventSetDate = eventSetDatetime.date() if isinstance(eventSetDatetime, QDateTime) else eventSetDatetime
        self.eventDate = eventDatetime.date() if isinstance(eventDatetime, QDateTime) else eventDatetime
        self.setOrgId(orgId if orgId else QtGui.qApp.currentOrgId())
        self.setEventTypeId(eventTypeId)
        self.edtCardNo.setText(self.getNextCardNo(eventTypeId))
        self.edtBegDate.setDate(self.eventSetDate)
        self.edtEndDate.setDate(self.eventDate)
        self.setClientId(clientId)
        self.setPersonId(personId)
        self.cmbPerson.setValue(personId)
        self.cmbOrder.setCurrentIndex(self.defaultOrder)
        self.edtMKB.setText(self.defaultMKB)
        self.diagnosticRecord = None
        self.initFocus()
        self.setIsDirty(False)
        return True and self.checkDeposit()


    def setLeavedAction(self, actionTypeIdValue):
        pass


    def initFocus(self):
        pass
#        if self.cmbContract.count() != 1:
#            self.cmbContract.setFocus(Qt.OtherFocusReason)
#        else:
#            self.tblInspections.setFocus(Qt.OtherFocusReason)


    def getNextCardNo(self, eventTypeId):
        db = QtGui.qApp.db
        table = db.table('Event')
        lastEvent = db.getRecordEx(table, 'externalId', table['eventType_id'].eq(eventTypeId), 'id DESC')
        if lastEvent:
            return str(forceInt(lastEvent.value(0))+1)
        else:
            return '1'


    def setRecord(self, record):
        CEventEditDialog.setRecord(self, record)
        setLineEditValue(self.edtCardNo,        record, 'externalId')
        setDatetimeEditValue(self.edtBegDate, self.edtBegTime, record, 'setDate')
        setDatetimeEditValue(self.edtEndDate, self.edtEndTime, record, 'execDate')
        setRBComboBoxValue(self.cmbPerson,      record, 'execPerson_id')
        setRBComboBoxValue(self.cmbResult,      record, 'result_id')
        setComboBoxValue(self.cmbOrder,         record, 'order')
        self.setPersonId(self.cmbPerson.value())
        self.loadDiagnostics()
        self.initFocus()
        self.setIsDirty(False)


    def loadDiagnostics(self):
        db = QtGui.qApp.db
        table = db.table('Diagnostic')
#        tablePerson = db.table('Person')
        record = db.getRecordEx(table, '*', [table['deleted'].eq(0), table['event_id'].eq(self.itemId())], 'id')
        if record:
            traumaTypeId = forceRef(record.value('traumaType_id'))
            diagnosisId = record.value('diagnosis_id')
            MKB   = forceString(db.translate('Diagnosis', 'id', forceRef(diagnosisId), 'MKB'))
            MKBEx = forceString(db.translate('Diagnosis', 'id', forceRef(diagnosisId), 'MKBEx'))
            self.diagnosticRecord = record
        else:
            traumaTypeId = None
            MKB = self.defaultMKB
            MKBEx = ''
            self.diagnosticRecord = None
        self.cmbTraumaType.setValue(traumaTypeId)
        self.edtMKB.setText(MKB)
        self.edtMKBEx.setText(MKBEx)


    def getRecord(self):
        record = CEventEditDialog.getRecord(self)
        showTime = getEventShowTime(self.eventTypeId)

        getLineEditValue(self.edtCardNo,        record, 'externalId')
        getDatetimeEditValue(self.edtBegDate, self.edtBegTime, record, 'setDate', showTime)

#        getRBComboBoxValue(self.cmbPerson,      record, 'setPerson_id')
        getDatetimeEditValue(self.edtEndDate, self.edtEndTime, record, 'execDate', showTime)
        getRBComboBoxValue(self.cmbPerson,      record, 'execPerson_id')
        getRBComboBoxValue(self.cmbResult,      record, 'result_id')
        getComboBoxValue(self.cmbOrder,         record, 'order')
        # Это хак: удаляем payStatus из записи
        result = type(record)(record) # copy record
        result.remove(result.indexOf('payStatus'))
        return result


    def saveInternals(self, eventId):
        self.saveDiagnostic(eventId)


    def saveDiagnostic(self, eventId):
        db = QtGui.qApp.db
        table = db.table('Diagnostic')

        if not self.diagnosticRecord:
            self.diagnosticRecord = table.newRecord()
            self.diagnosticRecord.setValue('event_id', toVariant(eventId))

        record = self.diagnosticRecord
        diagnosisTypeId = self.getDiagnosisTypeId()
        characterId     = self.getCharacterId()
        dispanserId     = None
        traumaTypeId    = self.cmbTraumaType.value()
        resultId        = self.cmbResult.value()

        MKB    = unicode(self.edtMKB.text())
        MKBEx  = unicode(self.edtMKBEx.text())

        diagnosisId, characterId = getDiagnosisId2(
            self.eventDate,
            self.personId,
            self.clientId,
            diagnosisTypeId,
            MKB,
            MKBEx,
            characterId,
            dispanserId,
            traumaTypeId,
            forceRef(record.value('diagnosis_id')),
            forceRef(record.value('id')),
            dispanserBegDate=forceDate(record.value('endDate')))

        record.setValue('diagnosisType_id', toVariant(diagnosisTypeId))
        record.setValue('speciality_id', toVariant(self.personSpecialityId))
        record.setValue('person_id', toVariant(self.personId) )
        record.setValue('setDate', toVariant(self.eventDate) )
        record.setValue('endDate', toVariant(self.eventDate) )
        record.setValue('diagnosis_id',  toVariant(diagnosisId))
        record.setValue('character_id',  toVariant(characterId))
        record.setValue('traumaType_id', toVariant(traumaTypeId))
        record.setValue('result_id',    toVariant(resultId))
        db.insertOrUpdate(table, record)
        self.modifyDiagnosises([(MKB, diagnosisId)])


    def setOrgId(self, orgId):
        self.orgId = orgId
        self.cmbPerson.setOrgId(orgId)


    def setEventTypeId(self, eventTypeId):
        CEventEditDialog.setEventTypeId(self, eventTypeId, u'Ф.025Тр')
        showTime = getEventShowTime(eventTypeId)
        self.edtBegTime.setVisible(showTime)
        self.edtEndTime.setVisible(showTime)
        self.cmbResult.setTable('rbResult', False, 'eventPurpose_id=\'%d\'' % self.eventPurposeId)


    def getTemplate(self):
        import os.path
        templateFileName   = 'F25Tr.html'
        fullPath = os.path.join(QtGui.qApp.getTemplateDir(), templateFileName)
        for enc in ('utf-8', 'cp1251'):
            try:
                file = codecs.open(fullPath, encoding=enc, mode='r')
                return file.read()
            except:
                pass
        return \
            u'<HTML><BODY>' \
            u'<HR>' \
            u'<CENTER>КАРТОЧКА ТРАВМAТИКА № {cardNo}</CENTER>' \
            u'<HR>' \
            u'код: {client.id}&nbsp;<FONT FACE="Code 3 de 9" SIZE=+3>*{client.id}*</FONT><BR/>' \
            u'ФИО: <B>{client.fullName}</B><BR/>' \
            u'ДР:  <B>{client.birthDate}</B>(<B>{client.age}</B>),&nbsp;Пол: <B>{client.sex}</B>,&nbsp;СНИЛС:<B>{client.SNILS}</B><BR/>' \
            u'Док: <B>{client.document}</B><BR/>' \
            u'Полис:<B>{client.policy}</B><BR/>' \
            u'<HR>' \
            u'Врач: <B>{person.fullName}</B>(<B>{person.specialityName}</B>)<BR>' \
            u'Порядок поступления: <B>{order}</B><BR>' \
            u'Тип травмы: <B>{traumaType}</B><BR>' \
            u'обстоятельства: <B>{MKBEx}</B>(<B>{MKBExName}</B>)<BR>' \
            u'</BODY></HTML>'


    def getEventInfo(self):
      #TODO: сделать CEventInfo
        context = CInfoContext()
        result = {}
        result['person'] = getPersonInfo(self.personId)
        result['cardNo'] = unicode(self.edtCardNo.text())
        result['order']  = orderTexts[self.cmbOrder.currentIndex()]
        result['traumaType']  = unicode(self.cmbTraumaType.currentText())
        result['MKB']       = unicode(self.edtMKB.text())
        result['MKBName']   = getMKBName(result['MKB'])
        result['MKBEx']     = unicode(self.edtMKBEx.text())
        result['MKBExName'] = getMKBName(result['MKBEx'])
        result['date']  = forceString(self.eventDate)
        result['client'] = context.getInstance(CClientInfo, self.clientId, self.eventDate)#getClientInfoEx(self.clientId, self.eventDate)
        return result


    def print_(self):
        eventInfo = self.getEventInfo()
        template = self.getTemplate()
        applyTemplateInt(self, u'карточка травматика', template, eventInfo, signAndAttachHandler=None)
#        text = substFields(template, eventInfo)
#        reportView = CReportViewDialog(self)
#        reportView.setWindowTitle()
#        reportView.setText(text)
#        reportView.exec_()


    def checkDataEntered(self):
        result = CEventEditDialog.checkDataEntered(self)
        begDate = self.edtBegDate.date()
        endDate = self.edtEndDate.date()
        result = result and (forceStringEx(self.edtCardNo) or self.checkInputMessage(u'номер карты', False, self.edtCardNo))
        result = result and (begDate or self.checkInputMessage(u'дату происшествия', False, self.edtBegDate))
        result = result and (endDate or self.checkInputMessage(u'дату обращения',    False, self.edtEndDate))
        result = result and (self.cmbPerson.value()   or self.checkInputMessage(u'врач',        False, self.cmbPerson))
        result = result and (self.cmbOrder.currentIndex() or self.checkInputMessage(u'порядок поступления', False, self.cmbOrder))
        result = result and (self.cmbTraumaType.value()   or self.checkInputMessage(u'тип травмы',          False, self.cmbTraumaType))
        result = result and self.checkDiagnosticDataEntered()
        result = result and (self.cmbResult.value()   or self.checkInputMessage(u'результат',   False, self.cmbResult))
        if self.edtEndDate.date():
            result = result and self.checkAndUpdateExpertise(self.edtEndDate.date(), self.cmbPerson.value())
        return result


    def checkDiagnosticDataEntered(self):
        result = True
        MKB    = unicode(self.edtMKB.text())
        MKBEx  = unicode(self.edtMKBEx.text())
        result = result and (MKB or self.checkInputMessage(u'диагноз', False, self.edtMKB))
        result = result and self.checkActualMKB(None, self.edtBegDate.date(), MKB, None, None)
        if result:
            result = self.checkDiagnosis(MKB)
            if not result:
                self.edtMKB.setFocus(Qt.OtherFocusReason)
                self.edtMKB.update()
        result = result and (MKBEx or self.checkInputMessage(u'обстоятельства',   False, self.edtMKBEx))
        if result:
            result = self.checkDiagnosis(MKBEx)
            if not result:
                self.edtMKBEx.setFocus(Qt.OtherFocusReason)
                self.edtMKBEx.update()
        return result


    def getDiagFilter(self):
        specialityId = self.personSpecialityId
        result = self.mapSpecialityIdToDiagFilter.get(specialityId, None)
        if result is None:
            result = QtGui.qApp.db.translate('rbSpeciality', 'id', specialityId, 'mkbFilter')
            if result is None:
                result = ''
            else:
                result = forceString(result)
            self.mapSpecialityIdToDiagFilter[specialityId] = forceString(result)
        return result


    def checkDiagnosis(self, MKB):
        diagFilter = self.getDiagFilter()
        return checkDiagnosis(self, MKB, diagFilter, self.clientId, self.clientSex, self.clientAge, self.edtBegDate.date())


    def getDiagnosisTypeId(self):
        return forceRef(QtGui.qApp.db.translate('rbDiagnosisType', 'code', '90', 'id'))

    def getCharacterId(self):
        return forceRef(QtGui.qApp.db.translate('rbDiseaseCharacter', 'code', '1', 'id'))


    @pyqtSignature('QDate')
    def on_edtBegDate_dateChanged(self, date):
        self.eventSetDate = QDate(date)
        self.setFilterResult(date)
        self.cmbPerson.setBegDate(date)


    @pyqtSignature('QDate')
    def on_edtEndDate_dateChanged(self, date):
        self.eventDate = QDate(date)
        self.cmbPerson.setEndDate(self.eventDate)
        self.setEnabledChkCloseEvent(self.eventDate)


    @pyqtSignature('int')
    def on_cmbPerson_currentIndexChanged(self):
        self.setPersonId(self.cmbPerson.value())
