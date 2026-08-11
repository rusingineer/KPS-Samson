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

import codecs

from PyQt4         import QtGui
from PyQt4.QtCore  import Qt, pyqtSignature

from Orgs.PersonInfo        import CPersonInfo
from Orgs.Utils             import COrgInfo
from Registry.Utils         import getClientBanner, getClientInfo2
from Timeline.Schedule      import CSchedule
from Timeline.TimeTable     import formatTimeRange
from library.DialogBase     import CDialogBase
from library.PrintTemplates import applyTemplate, getPrintTemplates, applyTemplateInt
from library.PrintInfo      import CDateInfo
from library.TableModel     import CTableModel, CDateTimeFixedCol, CEnumCol, CRefBookCol, CTextCol
from library.Utils          import forceBool, forceDate, forceInt, forceRef, forceString, forceTime, forceDateTime
from RefBooks.AppointmentPurpose.Info import CAppointmentPurposeInfo

from Registry.Ui_BeforeRecordClient import Ui_Dialog


class CQueue(CDialogBase, Ui_Dialog):
    def __init__(self, parent, clientId, scheduleIdList, visibleOkButton = False):
        CDialogBase.__init__(self, parent)
        cols = [
#            CEnumTableCol(u'Тип приёма', ['appointmentType'], 5,  CSchedule.atNames),
            CEnumCol(u'Тип приёма', ['appointmentType'], CSchedule.atNames, 4),
            CDateTimeFixedCol(u'Дата и время приема', ['time'], 20),
            CRefBookCol(u'Врач',                      ['person_id'], 'vrbPersonWithSpeciality', 20),
            CRefBookCol(u'Назначил',    ['recordPerson_id'], 'vrbPersonWithSpeciality', 20),
            CTextCol(u'Каб',            ['office'],    6),
            CTextCol(u'Жалобы',         ['complaint'], 6),
            CTextCol(u'Примечания',     ['note'],      6),
            CRefBookCol(u'Записал',     ['recordPerson_id'], 'vrbPersonWithSpeciality', 20),
            CDateTimeFixedCol(u'Дата записи', ['recordDatetime'], 20),
        ]
        self.addModels('ScheduleItems', CTableModel(self, cols, 'vScheduleItem'))
        self.addObject('btnPrint', QtGui.QPushButton(u'Печать', self))
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        if visibleOkButton:
            self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok|QtGui.QDialogButtonBox.Cancel)
        else:
            self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close)
        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)
        self.tblScheduleItems.setModel(self.modelScheduleItems)
        self.tblScheduleItems.addPopupPrintRow(self)
        self.clientId = clientId
        self.txtClientInfoBrowser.setHtml(getClientBanner(self.clientId) if self.clientId else '')
        self.modelScheduleItems.setIdList(scheduleIdList)
        self.buttonBox.setEnabled(bool(scheduleIdList))


    def showQueuePosition(self, scheduleItemId):
        if QtGui.qApp.mainWindow.dockResources:
            QtGui.qApp.mainWindow.dockResources.showQueueItem2(scheduleItemId)


    @pyqtSignature('QModelIndex')
    def on_tblScheduleItems_doubleClicked(self, index):
        scheduleItemId = self.tblScheduleItems.currentItemId()
        self.showQueuePosition(scheduleItemId)


    def destroy(self):
        pass


    @pyqtSignature('')
    def on_btnPrint_clicked(self):
        if self.modelScheduleItems.rowCount():
            self.tblScheduleItems.setReportHeader(u'Протокол предварительной записи пациента')
            self.tblScheduleItems.setReportDescription(self.txtClientInfoBrowser.toHtml())
            self.tblScheduleItems.printContent()


    def printOrderQueueItem(self):
        scheduleItemId = self.tblScheduleItems.currentItemId()
        printOrderByScheduleItem(self, scheduleItemId, self.clientId)


def printOrderByScheduleItem(widget, scheduleItemId, clientId=None, templateId=None):
    # clientId: для проверки того, что scheduleItem не изменился.
    # ещё нужно контролировать deleted
    db = QtGui.qApp.db
    record = db.getRecord('vScheduleItem', '*', scheduleItemId)
    scheduleClientId = forceRef(record.value('client_id'))
    printOrder(widget,                                  # widget
               scheduleClientId,                        # clientId
               forceInt(record.value('appointmentType')) == CSchedule.atHome, #toHome
               forceDate(record.value('date')),         #date
               forceString(record.value('office')),     #office
               forceRef(record.value('person_id')),     #personId
               forceInt(record.value('idx'))+1,         #num
               forceTime(record.value('time')),         #time
               forceBool(record.value('overtime')),     #overtime
               unicode(formatTimeRange((forceTime(record.value('begTime')),
                                        forceTime(record.value('endTime'))
                                       )
                                      )
                       ),                               #timeRange
               forceString(record.value('complaint')),
               forceRef(record.value('createPerson_id')), #createPersonId
               forceRef(record.value('recordPerson_id')), #recordPersonId
               forceDateTime(record.value('recordDatetime')), #recordDatetime
               forceRef(record.value('srcOrg_id')),       #srcOrgId
               forceString(record.value('srcPerson')),    #srcPerson
               forceDate(record.value('srcDate')),        #srcDate
               forceString(record.value('srcNumber')),    #srcNumber
               forceRef(record.value('appointmentPurpose_id')), #appointmentPurposeId
               templateId=templateId
              )


def printOrder(widget,
               clientId,
               toHome,
               date,
               office,
               personId,
               num,
               time,
               overtime,
               timeRange,
               complaints,
               createPersonId,
               recordPersonId,
               recordDatetime,
               srcOrgId,
               srcPerson,
               srcDate,
               srcNumber,
               appointmentPurposeId,
               templateId=None
               ):
    if toHome:
        context = 'orderHome'
        typeText = u'Вызов на дом'
    else:
        context = 'orderAmb'
        typeText = u'Направление на приём к врачу'
    visitInfo  = {'clientId'  : clientId,
                  'type'      : typeText,
                  'date'      : forceString(date),
                  'office'    : office,
                  'personId'  : personId, # WFT?
                  'num'       : num,
                  'time'      : time.toString('H:mm') if time and not overtime else '--:--',
                  'overtime'  : overtime,
                  'timeRange' : timeRange,
                  'complaints': complaints,
                  'createPersonId'  : createPersonId, # WTF?
                  'recordPersonId'  : recordPersonId,
                  'recordDatetime' : recordDatetime.toString('dd.MM.yyyy HH:mm') if recordDatetime else '',
                  'purpose'   : CAppointmentPurposeInfo(widget, appointmentPurposeId)
                 }
    clientInfo = getClientInfo2(clientId)
    personInfo = clientInfo.getInstance(CPersonInfo, personId)
    createPersonInfo = clientInfo.getInstance(CPersonInfo, createPersonId)
    recordPersonInfo = clientInfo.getInstance(CPersonInfo, recordPersonId)
    referralInfo =  { 'org'    : clientInfo.getInstance(COrgInfo, srcOrgId),
                      'person' : srcPerson,
                      'date'   : CDateInfo(srcDate),
                      'number' : srcNumber
                    }
    data = {'client'       : clientInfo,
            'person'       : personInfo,
            'visit'        : visitInfo,
            'createPerson' : createPersonInfo,
            'recordPerson' : recordPersonInfo,
            'referral'     : referralInfo
           }
    if not templateId:
        templates = getPrintTemplates(context)
        if templates:
            templateId = templates[0].id
    if not templateId:
        orderTemplate = getOrderTemplate()
        QtGui.qApp.call(widget, applyTemplateInt, (widget, visitInfo['type'], orderTemplate, data))
    else:
        QtGui.qApp.call(widget, applyTemplate, (widget, templateId, data))
    


def getOrderTemplate():
    import os.path
    templateFileName   = ''
    fullPath = os.path.join(QtGui.qApp.getTemplateDir(), templateFileName)
    for enc in ('utf-8', 'cp1251'):
        try:
            file = codecs.open(fullPath, encoding=enc, mode='r')
            return file.read()
        except:
            pass
    return \
        u'<HTML><BODY><table width="100%" style="font-size:12pt;"><tr><td>' \
        u'код: {client.id}&nbsp;<FONT FACE="Code 9 de 11" SIZE=+3>*{client.id}*</FONT><BR/>' \
        u'ФИО: <B>{client.fullName}</B><BR/>' \
        u'ДР:  <B>{client.birthDate}</B>(<B>{client.age}</B>),&nbsp;Пол: <B>{client.sex}</B>,&nbsp;СНИЛС:<B>{client.SNILS}</B><BR/>' \
        u'Док: <B>{client.document}</B><BR/>' \
        u'Полис:<B>{client.policy}</B><BR/>' \
        u'<HR>' \
        u'<CENTER>{visit.type}</CENTER>' \
        u'<HR>' \
        u'Врач: <B>{person.fullName}</B>(<B>{person.speciality}</B>)<BR>' \
        u'Явиться: <B>{visit.date} в каб.{visit.office}</B> Приём<B>{visit.timeRange}</B><BR>' \
        u'Время: <B>{visit.time}, #{visit.num}</B>' \
        u'</td></tr></BODY></HTML>'
