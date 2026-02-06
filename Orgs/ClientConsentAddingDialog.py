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
from PyQt4.QtCore import QDate, QVariant

from library.DialogBase import CDialogBase
from library.InDocTable import CInDocTableModel, CDateInDocTableCol, CEnumInDocTableCol, CInDocTableCol, CRBInDocTableCol
from library.Utils import forceDate, forceInt, forceRef, toVariant, forceString

from Ui_ClientConsentAddingDialog import Ui_ClientConsentAddingDialog


class CClientConsentAddingDialog(CDialogBase, Ui_ClientConsentAddingDialog):
    def __init__(self, parent=None, clientId=None, clientConsentTypeList=None):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.addModels('ClientConsents', CClientConsentModel(self))
        self.setModels(self.tblClientConsents, self.modelClientConsents, self.selectionModelClientConsents)
        if clientId and clientConsentTypeList:
            self._loadData(clientId, clientConsentTypeList)
        self.setWindowTitle(u'Согласия пациента')


    def setClientId(self, clientId):
        self._clientId = clientId


    def setClientConsentTypeList(self, clientConsentTypeList):
        self._clientConsentTypeList = clientConsentTypeList


    def loadData(self):
        self._loadData(self._clientId, self._clientConsentTypeList)


    def _loadData(self, clientId, clientConsentTypeList):
        self._clientId = clientId
        self._clientConsentTypeList = clientConsentTypeList
        self.cmbRepresenterClient.setClientId(clientId)
        self.modelClientConsents.setClientId(clientId)
        self.modelClientConsents.loadNewItems(self._clientConsentTypeList)


    def saveData(self):
        representerClientId = self.cmbRepresenterClient.value()
        date = self.edtDate.date() if self.edtDate.date() else QDate.currentDate()
        self.modelClientConsents.setRepresenterClientAndDateValues(representerClientId, date)
        self.modelClientConsents.saveItems(self._clientId)
        QtGui.qApp.emitCurrentClientInfoChanged()
        return True


    def getSelectedConsent(self):
        self.selectedClientConsent_id = self.cmbRepresenterClient.value() if self.cmbRepresenterClient.value() else None
        self.dateSignatory = forceDate(self.edtDate.date()) if self.edtDate.date() else None
        self.listSelectedConsent = []   # На всякий случай
        temp_db = QtGui.qApp.db
        stmt_consentType = u"""select cct.name from rbClientConsentType cct where cct.id = <cctid> """
        if self.tblClientConsents.getSelectedRows():  # Смотрим выделенные строки, в противном случае, будет выбран первый в списке
            for row in self.tblClientConsents.getSelectedRows():
                dictSelectedConsent = {'clientConsentType_id': None, 'value': None, 'endDate': None,
                                            'note': None, 'id': None, 'client_id': None, 'representerClient_id': None,
                                            'date': None, 'clientConsentType_name': None}
                dictSelectedConsent['clientConsentType_id'] = forceInt(self.tblClientConsents.model().value(row, 'clientConsentType_id')) if not self.tblClientConsents.model().value(row, 'clientConsentType_id').isNull() else None
                query_consentType = temp_db.query(stmt_consentType.replace(u'<cctid>', forceString(self.tblClientConsents.model().value(row, 'clientConsentType_id').toString())))
                query_consentType.next()
                record_consentType = query_consentType.record()
                dictSelectedConsent['clientConsentType_name'] = forceString(record_consentType.value('name'))
                dictSelectedConsent['value'] = forceInt(self.tblClientConsents.model().value(row, 'value')) if not self.tblClientConsents.model().value(row, 'value').isNull() else None
                dictSelectedConsent['endDate'] = forceDate(self.tblClientConsents.model().value(row, 'endDate')) if not self.tblClientConsents.model().value(row, 'endDate').isNull() else None
                dictSelectedConsent['note'] = forceString(self.tblClientConsents.model().value(row, 'note')) if not self.tblClientConsents.model().value(row, 'note').isNull() else None
                dictSelectedConsent['id'] = forceInt(self.tblClientConsents.model().value(row, 'id')) if not self.tblClientConsents.model().value(row, 'id').isNull() else None
                dictSelectedConsent['client_id'] = forceInt(self.tblClientConsents.model().value(row, 'client_id')) if not self.tblClientConsents.model().value(row, 'client_id').isNull() else None
                dictSelectedConsent['representerClient_id'] = forceInt(self.tblClientConsents.model().value(row, 'representerClient_id')) if not self.tblClientConsents.model().value(row, 'representerClient_id').isNull() else None
                dictSelectedConsent['date'] = forceDate(self.tblClientConsents.model().value(row, 'date')) if not self.tblClientConsents.model().value(row, 'date').isNull() else None
                self.listSelectedConsent.append(dictSelectedConsent)
        else:
            if self.tblClientConsents.model().items():  # Есть ли вообще согласия, вдруг их нет ¯\_(о_0)_/¯
                dictSelectedConsent = {'clientConsentType_id': None, 'value': None, 'endDate': None,
                                       'note': None, 'id': None, 'client_id': None, 'representerClient_id': None,
                                       'date': None, 'clientConsentType_name': None}
                dictSelectedConsent['clientConsentType_id'] = forceInt(self.tblClientConsents.model().value(0, 'clientConsentType_id')) if not self.tblClientConsents.model().value(0, 'clientConsentType_id').isNull() else None
                query_consentType = temp_db.query(stmt_consentType.replace(u'<cctid>', forceString(self.tblClientConsents.model().value(0, 'clientConsentType_id'))))
                query_consentType.next()
                record_consentType = query_consentType.record()
                dictSelectedConsent['clientConsentType_name'] = forceString(record_consentType.value('name'))
                dictSelectedConsent['value'] = forceInt(self.tblClientConsents.model().value(0, 'value')) if not self.tblClientConsents.model().value(0, 'value').isNull() else None
                dictSelectedConsent['endDate'] = forceDate(self.tblClientConsents.model().value(0, 'endDate')) if not self.tblClientConsents.model().value(0, 'endDate').isNull() else None
                dictSelectedConsent['note'] = forceString(self.tblClientConsents.model().value(0, 'note')) if not self.tblClientConsents.model().value(0, 'note').isNull() else None
                dictSelectedConsent['id'] = forceInt(self.tblClientConsents.model().value(0, 'id')) if not self.tblClientConsents.model().value(0, 'id').isNull() else None
                dictSelectedConsent['client_id'] = forceInt(self.tblClientConsents.model().value(0, 'client_id')) if not self.tblClientConsents.model().value(0, 'client_id').isNull() else None
                dictSelectedConsent['representerClient_id'] = forceInt(self.tblClientConsents.model().value(0, 'representerClient_id')) if not self.tblClientConsents.model().value(0, 'representerClient_id').isNull() else None
                dictSelectedConsent['date'] = forceDate(self.tblClientConsents.model().value(0, 'date')) if not self.tblClientConsents.model().value(0, 'date').isNull() else None
                self.listSelectedConsent.append(dictSelectedConsent)
            else:
                dictSelectedConsent = {'clientConsentType_id': None, 'value': None, 'endDate': None,
                                       'note': None, 'id': None, 'client_id': None, 'representerClient_id': None,
                                       'date': None, 'clientConsentType_name': None}
                self.listSelectedConsent.append(dictSelectedConsent)


class CClientConsentModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'ClientConsent', 'id', 'client_id', parent)
        self.addCol(CRBInDocTableCol(u'Тип согласия', 'clientConsentType_id', 15, 'rbClientConsentType'))
        self.addCol(CEnumInDocTableCol( u'Значение', 'value', 10, [u'Нет', u'Да']))
        self.addCol(CDateInDocTableCol(u'Дата окончания согласия', 'endDate', 15))
        self.addCol(CInDocTableCol(u'Примечания', 'note', 15))
        self.addHiddenCol('representerClient_id')
        self.addHiddenCol('date')
        self._clientId = None
        self._parent = parent
        self._date = None
        self._representerClientId = None
        self.setEnableAppendLine(False)


    def setClientId(self, clientId):
        self._clientId = clientId


    def saveItems(self, masterId):
        if self._items is not None:
            db = QtGui.qApp.db
            idList = []
            for record in self._items:
                record.setValue('client_id', QVariant(masterId))
                actualRecord = self.checkRecordByExists(record)
                actualRecord.setValue('representerClient_id', QVariant(self._representerClientId))
                actualRecord.setValue('date', QVariant(self._date))
                id = db.insertOrUpdate(self._table, actualRecord)
                actualRecord.setValue('id', toVariant(id))
                idList.append(id)


    def checkRecordByExists(self, record):
        db = QtGui.qApp.db
        consentTypeId = forceRef(record.value('clientConsentType_id'))
        consentTypePeriodFlag = forceInt(db.translate('rbClientConsentType', 'id', consentTypeId, 'periodFlag'))
        existsClientConsentRecordList = db.getRecordList('ClientConsent', '*', 'clientConsentType_id=%d AND client_id=%d AND deleted=0'%(consentTypeId, self._clientId))
        if consentTypePeriodFlag:
            for existsClientConsentRecord in existsClientConsentRecordList:
                if not forceDate(existsClientConsentRecord.value('endDate')):
                    existsClientConsentRecord.setValue('endDate', QVariant(self._date.addDays(-1)))
                    db.updateRecord('ClientConsent', existsClientConsentRecord)
            return record
        else:
            for existsClientConsentRecord in existsClientConsentRecordList:
                if not forceDate(existsClientConsentRecord.value('endDate')):
                    existsClientConsentRecord.setValue('value', record.value('value'))
                    return existsClientConsentRecord
            return record


    def loadNewItems(self, clientConsentTypeList):
        for newConsentItem in clientConsentTypeList:

            consentTypeId = newConsentItem.clientConsentTypeId
            consentValue  = newConsentItem.clientConsentValue

            newItem = self.getEmptyRecord()

            consentTypeRecord = QtGui.qApp.db.getRecord('rbClientConsentType', 'periodFlag, defaultPeriod', consentTypeId)
            if consentTypeRecord and forceInt(consentTypeRecord.value('periodFlag')):
                defaultPeriod = forceInt(consentTypeRecord.value('defaultPeriod'))
                date = self._parent.edtDate.date()
                if date:
                    newItem.setValue('endDate', QVariant(date.addMonths(defaultPeriod)))
            newItem.setValue('clientConsentType_id', QVariant(consentTypeId))
            newItem.setValue('value', QVariant(consentValue))

            self._items.append(newItem)
        self.reset()
        return True


    def setRepresenterClientAndDateValues(self, representerClientId, date):
        self._date = date
        self._representerClientId = representerClientId
