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
from PyQt4.QtCore import Qt, pyqtSignature, QDate
from Orgs.OrgComboBox import CContractComboBox

from library.Utils import forceString, forceRef, calcAgeTuple
from Registry.Utils import getClientInfo, getClientWork

from Registry.Ui_UpdateEventTypeByEvent import Ui_UpdateEventTypeByEvent


class CUpdateEventTypeByEvent(QtGui.QDialog, Ui_UpdateEventTypeByEvent):
    def __init__(self,  parent, eventTypeIdList, eventTypeId, date=QDate(), orgId=None, clientId=None, setDate=QDate(), eventId=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.eventTypeIdList = eventTypeIdList
        filterNew = ('''id IN (%s) '''%((u','.join(forceString(tmpEventTypeId) for tmpEventTypeId in self.eventTypeIdList)))) if self.eventTypeIdList else ''
        self.cmbEventType.setTable('EventType', True, filter=filterNew)
        self.setNewEventTypeId(eventTypeId)
        self.cmbOrder.setCurrentIndex(-1)
        self.cmbContract = CContractComboBox(self)
        self.cmbContract.setVisible(False)
        clientInfo = getClientInfo(clientId, date=date, consents={'begDate': setDate if setDate else QDate(), 'endDate': date if date else QDate()}, eventId=eventId)
        workRecord = getClientWork(clientId)
        self.contractInit(date, orgId, eventTypeId, clientId, clientInfo, setDate, workRecord)
    
    
    def contractInit(self, date, orgId, eventTypeId, clientId, clientInfo, setDate, workRecord):
        self.cmbContract.setDate(date if date else (setDate if setDate else QDate.currentDate()))
        self.cmbContract.setOrgId(orgId if orgId else QtGui.qApp.currentOrgId())
        self.cmbContract.setEventTypeId(eventTypeId)
        if clientInfo.id:
            clientSex = clientInfo.sexCode
            clientBirthDate = clientInfo.birthDate
            dateAge = setDate if setDate else QDate.currentDate()
            clientAge = calcAgeTuple(clientBirthDate, dateAge)
        else:
            clientSex = None
            clientAge = None
        clientWorkOrgId = forceRef(workRecord.value('org_id')) if workRecord else None
        clientPolicyInfoList = []
        policyRecord = clientInfo.get('compulsoryPolicyRecord')
        if policyRecord:
            clientPolicyInfoList.append(self.getPolicyInfo(policyRecord))
        policyRecord = clientInfo.get('voluntaryPolicyRecord')
        if policyRecord:
            clientPolicyInfoList.append(self.getPolicyInfo(policyRecord))
        self.cmbContract.setClientInfo(clientId, clientSex, clientAge, clientWorkOrgId, clientPolicyInfoList)
        self.cmbContract.setCurrentIndex(0)

    
    def getPolicyInfo(self, policyRecord):
            if policyRecord:
                insurerId = forceRef(policyRecord.value('insurer_id'))
                policyTypeId = forceRef(policyRecord.value('policyType_id'))
            else:
                insurerId = None
                policyTypeId = None
            return insurerId, policyTypeId
        

    def setNewEventTypeId(self, eventTypeId):
        self.cmbEventType.setValue(eventTypeId)


    def getNewEventTypeId(self):
        return self.cmbEventType.value()
    
    
    def getOrder(self):
        return self.cmbOrder.currentIndex()
    
    
    def getContractId(self):
        return self.cmbContract.value()
    
    
    @pyqtSignature('int')
    def on_cmbEventType_currentIndexChanged(self, index):
        eventTypeId = self.getNewEventTypeId()
        self.cmbContract.setEventTypeId(eventTypeId)
        self.cmbContract.setCurrentIndex(0)
        if eventTypeId:
            self.cmbOrder.setCurrentIndex(-1)
            self.cmbOrder.setEnabled(True)
            availableOrders = QtGui.qApp.db.translate('EventType', 'id',  forceString(eventTypeId), 'availableOrders')
            for index in range(self.cmbOrder.count()):
                if forceString(index+1) not in forceString(availableOrders):
                    self.cmbOrder.model().item(index).setEnabled(False)
                else:
                    self.cmbOrder.model().item(index).setEnabled(True) 
        else:
            self.cmbOrder.setEnabled(False)


    @pyqtSignature('int')
    def on_cmbOrder_currentIndexChanged(self, index):
        btnOk = self.buttonBox.button(QtGui.QDialogButtonBox.Ok)
        btnOk.setEnabled(bool(index+1))


    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Ok:
            self.getNewEventTypeId()
        elif buttonCode == QtGui.QDialogButtonBox.Cancel:
            self.close()
