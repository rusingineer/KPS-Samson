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

from Orgs.Utils            import getPersonInfo
from Registry.Utils        import getClientInfoEx

from Reports.ReportBase    import CReportBase
from Reports.ReportView    import CReportViewDialog
from library.Utils         import forceBool, forceInt, forceRef, forceString, formatDate


def showScheduleItemInfo(scheduleItemId, widget):
    db = QtGui.qApp.db
    scheduleItemRecord = db.getRecord('Schedule_Item', '*', scheduleItemId)
    scheduleRecord = db.getRecord('Schedule', '*', scheduleItemRecord.value('master_id'))

    appointmentType = forceInt(scheduleRecord.value('appointmentType'))
    appointmentPurposeId = forceRef(scheduleRecord.value('appointmentPurpose_id'))
    datetime       = forceString(scheduleItemRecord.value('time'))
    office         = forceString(scheduleRecord.value('office'))
    createDatetime = forceString(scheduleItemRecord.value('createDatetime'))
    createPersonId = forceRef(scheduleItemRecord.value('createPerson_id'))
    modifyDatetime = forceString(scheduleItemRecord.value('modifyDatetime'))
    modifyPersonId = forceRef(scheduleItemRecord.value('modifyPerson_id'))
    recordDatetime = forceString(scheduleItemRecord.value('recordDatetime'))
    recordPersonId = forceRef(scheduleItemRecord.value('recordPerson_id'))

    personId = forceRef(scheduleRecord.value('person_id'))
    clientId = forceRef(scheduleItemRecord.value('client_id'))
    complaint= forceString(scheduleItemRecord.value('complaint'))
    note     = forceString(scheduleItemRecord.value('note'))
    overtime = forceBool(scheduleItemRecord.value('overtime'))
    isUrgent = forceBool(scheduleItemRecord.value('isUrgent'))

    appointmentPurpose = forceString(db.translate('rbAppointmentPurpose', 'id', appointmentPurposeId, 'name'))
    createPerson = forceString(db.translate('vrbPersonWithSpeciality', 'id', createPersonId, 'name'))
    modifyPerson = forceString(db.translate('vrbPersonWithSpeciality', 'id', modifyPersonId, 'name'))
    recordPerson = forceString(db.translate('vrbPersonWithSpeciality', 'id', recordPersonId, 'name'))
    personInfo = getPersonInfo(personId)
    clientInfo = getClientInfoEx(clientId)

    doc = QtGui.QTextDocument()
    cursor = QtGui.QTextCursor(doc)

    cursor.setCharFormat(CReportBase.ReportTitle)
    cursor.insertText(u'Свойства записи')
    cursor.insertBlock()
    cursor.setCharFormat(CReportBase.ReportBody)

    if appointmentType == 1:
        cursor.insertText(u'Запись на амбулаторный приём')
    elif appointmentType == 2:
        cursor.insertText(u'Зызов на дом')
    elif appointmentType == 3:
        cursor.insertText(u'КЭР')
    else:
        cursor.insertText(u'Неизвестный тип приёма (%d)' % appointmentType)

    cursor.insertText(' ')
    cursor.insertText(datetime)
    if office and appointmentType != 2:
        cursor.insertText(u', кабинет %s' % office)
    cursor.insertText('\n')
    if isUrgent:
        cursor.insertText(u'Запись произведена неотложно\n')
    elif overtime:
        cursor.insertText(u'Запись произведена сверх плана\n')
    if appointmentPurpose:
        cursor.insertText(u'Назначение приёма: %s\n' % appointmentPurpose)
    cursor.insertText('\n')
    cursor.insertText(u'Создатель записи: %s\n' % createPerson)
    cursor.insertText(u'Дата создания записи: %s\n' % createDatetime)
    cursor.insertText(u'Редактор записи: %s\n' % modifyPerson)
    cursor.insertText(u'Дата редактирования записи: %s\n\n' % modifyDatetime)

    cursor.insertText(u'Записал: %s\n' % recordPerson)
    cursor.insertText(u'Дата записи: %s\n' % recordDatetime)
    if personInfo:
        cursor.insertText(u'врач: %s, %s\n' % (personInfo['fullName'], personInfo['specialityName']))
        cursor.insertText(u'подразделение: %s, %s\n' % (personInfo['orgStructureName'], personInfo['postName']))
        if personInfo['tariffCategoryName']:
            cursor.insertText(u'тарифная категория: %s\n' % (personInfo['tariffCategoryName']))
    if clientInfo:
        cursor.insertText(u'пациент: %s\n' % clientInfo['fullName'])
        cursor.insertText(u'д/р: %s\n' % formatDate(clientInfo['birthDate']))
        cursor.insertText(u'возраст: %s\n' % clientInfo['age'])
        cursor.insertText(u'пол: %s\n' % clientInfo['sex'])
        cursor.insertText(u'адрес регистрации: %s\n' % (clientInfo['regAddress'] or ''))
        cursor.insertText(u'адрес проживания: %s\n' % (clientInfo['locAddress'] or ''))
        cursor.insertText(u'полис: %s\n' % (clientInfo['policy'] or ''))
        cursor.insertText(u'паспорт: %s\n' % (clientInfo['document'] or ''))
        cursor.insertText(u'СНИЛС: %s\n' % clientInfo['SNILS'])
        cursor.insertText(u'контактная информация: %s\n' % clientInfo['phones'])
    cursor.insertText(u'жалобы: %s\n' % complaint)
    cursor.insertText(u'примечания: %s\n' % note)

    cursor.insertBlock()
    reportView = CReportViewDialog(widget)
    reportView.setWindowTitle(u'Свойства записи')
    reportView.setText(doc)
    reportView.exec_()
