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
u"""Работа с правилами оповещений"""

from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignature

from library.interchange import setComboBoxValue, getComboBoxValue
from library.ItemsListDialog import CItemsListDialog, CItemEditorBaseDialog
from library.TableModel import CIntCol, CEnumCol, CTextCol, CRefBookCol
from library.InDocTable import CInDocTableModel, CRBInDocTableCol
from library.Utils import (toVariant, forceBool, forceInt, forceStringEx,
    forceString, forceRef)

from RefBooks.Tables import rbNotificationKind
from Timeline.Schedule import CSchedule

from Notifications.Ui_NotificationRuleEditorDialog import (
    Ui_NotificationRuleEditorDialog)

tblNotificationRule = 'Notification_Rule'
tblNotificationKind = 'Notification_Kind'


class CNotificationRule(object):
    u"""Класс для работы с правилами оповещений"""
    ncInternal = 0 # Ручной класс(внутренний)
    ncExternal = 1 # Автоматический класс (внешний)
    ntSchedule = 0
    ntRegistry = 1
    ntAction = 2
    nrIsRestricted = 1
    ncdConfirmation = 0
    ncdNotification = 1
    ncdCancel = 2
    ncdQuiz = 3
    #ncdAutoResearch = 4
    #ncdManualResearch = 5
    ncdResearch = 4


    def __init__(self, record):
        self.id = forceRef(record.value('id'))
        self.template = forceString(record.value('template'))
        self.name = forceString(record.value('name'))
        self.actionType_id = forceInt(record.value('actionType_id'))
        self.type = forceInt(record.value('type'))
        self.condition = forceInt(record.value('condition'))
        self.notificationKindList = list(self.__getNotificationKind(self.id))
        self.multiplicity = forceInt(record.value('multiplicity'))
        self.term = forceInt(record.value('term'))
        self.expiration = forceInt(record.value('expiration'))
        self.modifyPersonId = forceRef(record.value('modifyPerson_id'))
        self.createPersonId = forceRef(record.value('createPerson_id'))
        self.ignoreToday = forceBool(record.value('ignoreToday'))
        self.appointmentType = forceInt(record.value('appointmentType'))
        self.allowConfirmiation = forceBool(record.value('allowConfirmation'))
        self.isTransmittable = forceBool(record.value('isTransmittable'))
        self.ruleClass = forceBool(record.value('class'))
        self.obsDescr = forceString(record.value('obsDescr'))


    def __getNotificationKind(self, _id):
        u"""Получает виды оповещения по идентификатору правила,
        возвращает генератор кортежей (код оповещения типа,
        идентификатор типа оповещения, идентификатор типа контакта)"""

        stmt = """SELECT rbNotificationKind.code,
            rbNotificationKind.contactType_id,
            rbNotificationKind.id
        FROM Notification_Kind
        LEFT JOIN rbNotificationKind ON
            Notification_Kind.kind_id = rbNotificationKind.id
        WHERE Notification_Kind.rule_id = {0}""".format(_id)

        query = QtGui.qApp.db.query(stmt)

        while query.next():
            record = query.record()

            if record:
                code = forceString(record.value(0))
                contactTypeId = forceRef(record.value(1))
                kindId = forceRef(record.value(2))
                yield code, kindId, contactTypeId


class CNotificationRuleList(CItemsListDialog):
    u"""Список правил оповещений"""
    def __init__(self, parent):
        CItemsListDialog.__init__(self, parent, [
                CIntCol(u'Идентификатор', ['id'], 20),
                CTextCol(u'Наименование', ['name'], 40),
                CEnumCol(u'Класс', ['class'], (u'Ручной', u'Автоматический'), 20),
                CEnumCol(u'Тип', ['type'], (u'Расписание', u'Картотека', u'Действие'), 20),
                CEnumCol(u'Условие', ['condition'], (u'Подтверждение записи',
                    u'Напоминание', u'Отмена записи', u'Опрос', u'Отправка результата'), 20),
                #CTextCol(u'Тип действия', ['actionType_id'], 15),
                CRefBookCol(u'Тип действия', ['actionType_id'], 'ActionType', 30),
                CEnumCol(u'Тип приёма', ['appointmentType'],
                         CSchedule.atNames, 15),
            ], tblNotificationRule, ['id', 'class', 'type'])
        self.setWindowTitleEx(u'Правила оповещений')


    def getItemEditor(self):
        u"""Возвращает диалог редактировния вида оповещения"""
        return CNotificationRuleEditor(self)


class CNotificationRuleEditor(CItemEditorBaseDialog,
        Ui_NotificationRuleEditorDialog):
    u"""Диалог редактирования правил оповещения"""
    def __init__(self, parent):
        CItemEditorBaseDialog.__init__(self, parent, tblNotificationRule)
        self.addModels('NotificationKind', CNotificationKindModel(self))

        self.setupUi(self)
        self.setModels(self.tblNotificationKind, self.modelNotificationKind,
            self.selectionModelNotificationKind)
        self.tblNotificationKind.addPopupDelRow()
        self.cmbActionType.setTable('ActionType', True, u'serviceType=11')
        self.cmbActionType.setEnabled(False)
        self.cmbReceivingActionType.setEnabled(False)
        self.edtObsDescr.setEnabled(False)
        self.edtExpiration.setEnabled(False)
        self.cmbAttachedFile.setEnabled(False)
        self.cmbAppointmentType.clear()
        self.cmbAppointmentType.addItems(CSchedule.atNames)


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        _id = self.itemId()

        self.cmbClass.setCurrentIndex(forceInt(record.value('class')))
        self.cmbType.setCurrentIndex(forceInt(record.value('type')))
        self.cmbCondition.setCurrentIndex(forceInt(record.value('condition')))
        self.chkIsRestricted.setChecked(forceBool(record.value('restricted')))
        self.edtTemplate.setPlainText(forceStringEx(record.value('template')))
        self.edtName.setText(forceStringEx(record.value('name')))
        self.edtMultiplicity.setValue(forceInt(record.value('multiplicity')))
        self.edtTerm.setValue(forceInt(record.value('term')))
        self.edtExpiration.setValue(forceInt(record.value('expiration')))
        self.chkIgnoreToday.setChecked(forceBool(record.value('ignoreToday')))
        self.chkAllowConfirm.setChecked(forceBool(record.value('allowConfirmation')))
        self.cmbActionType.setValue(forceRef(record.value('actionType_id')))
        self.cmbReceivingActionType.setValue(forceRef(record.value('receivingActionType_id')))
        self.edtObsDescr.setText(forceStringEx(record.value('obsDescr')))
        self.chkTransferred.setChecked(forceBool(record.value('isTransmittable')))
        setComboBoxValue(self.cmbAppointmentType, record, 'appointmentType')
        setComboBoxValue(self.cmbAttachedFile, record, 'attachedFileAttr')
        self.modelNotificationKind.loadItems(_id)


    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        record.setValue('class', toVariant(
            forceInt(self.cmbClass.currentIndex())))
        record.setValue('type', toVariant(
            forceInt(self.cmbType.currentIndex())))
        record.setValue('condition', toVariant(
            forceInt(self.cmbCondition.currentIndex())))
        record.setValue('restricted', toVariant(
            forceBool(self.chkIsRestricted.isChecked())))
        record.setValue('template', toVariant(
            forceStringEx(self.edtTemplate.toPlainText())))
        record.setValue('expiration', toVariant(
            forceInt(self.edtExpiration.value())))
        record.setValue('name', toVariant(
            forceStringEx(self.edtName.text())))
        record.setValue('multiplicity', toVariant(
            forceInt(self.edtMultiplicity.value())))
        record.setValue('term', toVariant(
            forceInt(self.edtTerm.value())))
        record.setValue('ignoreToday', toVariant(
            forceBool(self.chkIgnoreToday.isChecked())))
        record.setValue('allowConfirmation', toVariant(
            forceBool(self.chkAllowConfirm.isChecked())))
        record.setValue('actionType_id', toVariant(
            forceRef(self.cmbActionType.value())))
        record.setValue('receivingActionType_id', toVariant(
            forceRef(self.cmbReceivingActionType.value())))
        record.setValue('attachedFileAttr', toVariant(
            forceInt(self.cmbAttachedFile.currentIndex())))
        record.setValue('obsDescr', toVariant(
            forceStringEx(self.edtObsDescr.text())))
        record.setValue('isTransmittable', toVariant(
            forceBool(self.chkTransferred.isChecked())))
        getComboBoxValue(self.cmbAppointmentType, record, 'appointmentType')
        return record


    def saveInternals(self, _id):
        self.modelNotificationKind.saveItems(_id)


    def checkDataEntered(self):
        result = True
        return result


    def destroy(self):
        pass


    @pyqtSignature('bool')
    def on_chkTransferred_toggled(self, checked):
        if checked:
            self.cmbReceivingActionType.setEnabled(True)
            self.edtObsDescr.setEnabled(True)
        else:
            self.cmbReceivingActionType.setEnabled(False)
            self.edtObsDescr.setEnabled(False)
            self.cmbReceivingActionType.setCurrentModelIndex(0)
            self.edtObsDescr.setText('')


    @pyqtSignature('int')
    def on_cmbCondition_currentIndexChanged(self, index):
        flag = index == CNotificationRule.ncdNotification
        self.edtMultiplicity.setEnabled(flag)
        self.edtTerm.setEnabled(flag)
        if index == CNotificationRule.ncdQuiz:
            self.edtExpiration.setEnabled(True)
            self.cmbActionType.setEnabled(True)
            self.cmbActionType.setTable('ActionType', True, u'serviceType=11')
            return
        else:
            self.edtExpiration.setValue(0)
            self.edtExpiration.setEnabled(False)
        if (index == CNotificationRule.ncdResearch):
            self.cmbAppointmentType.setCurrentIndex(0)
            self.cmbAppointmentType.setEnabled(False)
        else:
            self.cmbAppointmentType.setCurrentIndex(0)
            self.cmbAppointmentType.setEnabled(True)
        if (     index == CNotificationRule.ncdResearch
             #and unicode(self.cmbClass.currentText()) == u'автоматический'
           ):
            self.cmbActionType.setEnabled(True)
            self.cmbActionType.setTable('ActionType', True, u'serviceType=5 OR serviceType=10')
            self.edtMultiplicity.setValue(0)
            self.edtMultiplicity.setEnabled(False)
            self.edtTerm.setValue(0)
            self.edtTerm.setEnabled(False)
            self.edtExpiration.setValue(0)
            self.edtExpiration.setEnabled(False)
        else:
            self.cmbActionType.setValue(None)
            self.cmbActionType.setEnabled(False)


    @pyqtSignature('int')
    def on_cmbType_currentIndexChanged(self, index):
        if unicode(self.cmbType.currentText()) == u'действие':
            self.cmbActionType.setEnabled(True)
            self.cmbAttachedFile.setEnabled(True)
        else:
            self.cmbAttachedFile.setEnabled(False)
            self.cmbAttachedFile.setCurrentIndex(0)
        if (    self.cmbCondition.currentIndex() == CNotificationRule.ncdResearch
            and unicode(self.cmbType.currentText()) == u'действие'
           #and unicode(self.cmbClass.currentText()) == u'автоматический'
           ):
            self.cmbActionType.setEnabled(True)
            self.cmbActionType.setTable('ActionType', True, u'serviceType=5 OR serviceType=10')
            return
        if (    unicode(self.cmbClass.currentText()) == u'ручной'
            and unicode(self.cmbType.currentText()) == u'действие'
            and self.cmbCondition.currentIndex() == CNotificationRule.ncdQuiz
           ):
            self.cmbActionType.setEnabled(True)
            self.cmbActionType.setTable('ActionType', True, u'serviceType=11')
            return
        self.cmbActionType.setValue(None)
        self.cmbActionType.setEnabled(False)


    @pyqtSignature('int')
    def on_cmbClass_currentIndexChanged(self, index):
        if (     self.cmbCondition.currentIndex() == CNotificationRule.ncdResearch
             #and unicode(self.cmbClass.currentText()) == u'автоматический'
           ):
            self.cmbActionType.setEnabled(True)
            self.cmbActionType.setTable('ActionType', True, u'serviceType=5 OR serviceType=10')
            return
        if (    unicode(self.cmbClass.currentText()) == u'ручной'
            and unicode(self.cmbType.currentText()) == u'действие'
            and self.cmbCondition.currentIndex() == CNotificationRule.ncdQuiz
           ):
            self.cmbActionType.setEnabled(True)
            self.cmbActionType.setTable('ActionType', True, u'serviceType=11')
            return
        self.cmbActionType.setValue(None)
        self.cmbActionType.setEnabled(False)


class CNotificationKindModel(CInDocTableModel):
    u"""Модель видов оповещений"""
    def __init__(self, parent):
        CInDocTableModel.__init__(self,
            tblNotificationKind, 'id', 'rule_id', parent)
        self.addCol(CRBInDocTableCol(
            u'Тип', 'kind_id', 15, rbNotificationKind))

