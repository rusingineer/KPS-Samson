# -*- coding: utf-8 -*-
from PyQt4 import QtGui
from PyQt4.QtCore import *

from Ui_addServiceProfileDialog import *
from library.ItemsListDialog import CItemsListDialog, CItemEditorBaseDialog
from library.Utils import *
from library.interchange import *
from Utils import warninWindow, ConnectionInfo
import re

def is_valid_guid(guid):
    return re.match(r'^[{(]?[0-9a-fA-F]{8}-([0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}[)}]?$', guid) is not None

class CMedServiceProfileDialog(CItemEditorBaseDialog, Ui_MedServiceProfileDialog):
    def __init__(self, parent):
        CItemEditorBaseDialog.__init__(self, parent, 'MedServiceProfiles')
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setWindowTitleEx(u'Профили')
        self.cmbProfileMedService.setTable(QtGui.qApp.db.db.databaseName()+'.`v1.2.643.2.69.1.1.1.56`', True)
        self.setupDirtyCather()
        # если 1 то изменить, если то 0- то добавить новое
        self.typeEv = parent.typeEv
        if self.typeEv == 1:
            self.cmbProfileMedService.setEnabled(False)
            self.cmbLpuId.setEnabled(False)
            self.dteStartDate.setEnabled(False)

    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        setLineEditValue(self.edtAddress, record, 'address')
        setLineEditValue(self.edtContactValue, record, 'contactValue')
        setLineEditValue(self.edtSite, record, 'site')
        setRBComboBoxValue(self.cmbProfileMedService, record, 'master_id')
        setRBComboBoxValue(self.cmbLpuId, record, 'targetMo')
        setDateEditValue(self.dteStartDate, record, 'startDate')
        setDateEditValue(self.dteEndDate, record, 'endDate')
        setTextEditValue(self.editComment, record, 'comment')
        self.setIsDirty(False)

    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        getLineEditValue(self.edtAddress, record, 'address')
        getLineEditValue(self.edtContactValue, record, 'contactValue')
        getLineEditValue(self.edtSite, record, 'site')
        getRBComboBoxValue(self.cmbProfileMedService, record, 'master_id')
        getRBComboBoxValue(self.cmbLpuId, record, 'targetMo')
        getDateEditValue(self.dteStartDate, record, 'startDate')
        getDateEditValue(self.dteEndDate, record, 'endDate')
        getTextEditValue(self.editComment, record, 'comment')
        record.setValue('master_id', toVariant(self.cmbProfileMedService.value()))
        self.cmbProfileMedService.value()
        if self.typeEv == 1:
            record.setValue('modifyDatetime', toVariant(QDateTime.currentDateTime()))
            record.setValue('modifyPerson_id', toVariant(QtGui.qApp.userId))
            record.setValue('acceptModify', toVariant(0))
        else:
            record.setValue('createDatetime', toVariant(QDateTime.currentDateTime()))
            record.setValue('createPerson_id', toVariant(QtGui.qApp.userId))
            record.setValue('acceptModify', toVariant(0))
        record.setValue('idLpu', toVariant(self.targetMo))
        return record

    def checkDataEntered(self):
        if self.cmbLpuId.value() is not None:
            orgstructureId = self.cmbLpuId.value()
            value = ConnectionInfo(orgstructureId)
            if value != '':
                if is_valid_guid:
                    self.targetMo = value
                else:
                    warninWindow(u'Не верный формат значение идентификации по справочнику 1.2.643.2.69.1.1.1.64')
            else:
                warninWindow(u'Для подразделения не заполнена идентификации по справочнику 1.2.643.2.69.1.1.1.64')
                return
        else:
            warninWindow(u'Выберите подразделение')
            return False
        result = True
        cmbProfile = forceRef(self.cmbProfileMedService.currentIndex())
        if self.cmbProfileMedService.currentIndex() == -1:
            warninWindow(u'Требуется указать профиль мед. помощи')
            return
        dteStartDate = forceDate(self.dteStartDate.date())
        result = result and (cmbProfile or self.checkInputMessage(u'Профиль', False, self.cmbProfileMedService))
        result = result and (dteStartDate or self.checkInputMessage(u'Дату начала', False, self.dteStartDate))
        return result
