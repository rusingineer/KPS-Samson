# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2022 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################


from PyQt4 import QtGui
from PyQt4.QtCore import Qt, pyqtSignature, SIGNAL, QChar, QDate, QRegExp, QObject, QString, QDateTime

from Events.Action import CActionTypeCache, CAction
from Events.ActionCreateDialog import CActionCreateDialog
from Events.ActionsSelector import selectActionTypes
from Exchange.ExchangeScanPromobot import scanning
from library.Counter import CCounterController
from library.DialogBase         import CDialogBase
from library.TableModel         import CDateCol, CEnumCol, CTableModel, CTextCol, CRefBookCol, CDateTimeCol
from library.database           import CTableRecordCache
from library.Utils import forceDate, forceRef, forceString, forceStringEx, getPref, setPref, forceInt, calcAgeTuple, \
    toVariant, forceBool

from Registry.ClientEditDialog  import CClientEditDialog
from Registry.SimplifiedClientSearch import CSimplifiedClientSearch
from Registry.Utils             import CCheckNetMixin, getClientBanner
from Orgs.Utils                 import advisePolicyType
from Events.CreateEvent         import requestNewEvent
from Events.Utils               import getActionTypeIdListByFlatCode
from Events.ActionStatus        import CActionStatus
from Users.Rights               import urAdmin, urRegTabReadRegistry, urRegTabWriteRegistry, urRegTabNewWriteRegistry
from HospitalBeds.HospitalizationFromQueue import CHospitalizationFromQueue

from Ui_HospitalizationEventDialog import Ui_HospitalizationEventDialog


class CHospitalizationEventDialog(CDialogBase, Ui_HospitalizationEventDialog, CCheckNetMixin):
    __pyqtSignals__ = ('HospitalizationEventCodeSelected(int)',
                      )

    def __init__(self, parent, clientIdList = [], isHealthResort = False):
        CDialogBase.__init__(self, parent)
        CCheckNetMixin.__init__(self)
        self.tableModel = CHospitalizationEventDialogTableModel(self)
        self.tableSelectionModel = QtGui.QItemSelectionModel(self.tableModel, self)
        self.tableSelectionModel.setObjectName('tableSelectionModel')
        self.setupGetClientIdMenu()
        self.setupHospitalizationEventMenu()
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.tblHospitalizationEvent.setModel(self.tableModel)
        self.tblHospitalizationEvent.setSelectionModel(self.tableSelectionModel)
        self.parent = parent #wtf? скрывать Qt-шный parent - это плохая затея
        self.isHealthResort = isHealthResort
        self.isHBDeath = False
        self.hospitalBedsHasRight = True
        self.date = None
        self.code = None
        self.newEventId = None
        self.dialogInfo = {}
        self.clientIdList = clientIdList
        preferences = getPref(QtGui.qApp.preferences.windowPrefs, 'CHospitalizationEventDialog', {})
        self.tblHospitalizationEvent.loadPreferences(preferences)
        self.tblHospitalizationEvent.setPopupMenu(self.mnuHospitalizationEvent)
        self.tblHospitalizationEvent.addAction(self.actEditClientInfo)
        self.tblHospitalizationEvent.addAction(self.actCreateEvent)
        self.edtLastName.setFocus(Qt.OtherFocusReason)
        self.idValidator = CIdValidator(self)
        self.edtFilterId.setValidator(self.idValidator)
        self.edtBirthDate.setDate(QDate())
        self.cmbDocType.setTable('rbDocumentType', True, 'group_id IN (SELECT id FROM rbDocumentTypeGroup WHERE code=\'1\')')
        self.cmbCompulsoryPolisType.setTable('rbPolicyType', True)
        self.cmbFilterPolicyKind.setTable('rbPolicyKind', True)
        self.cmbFilterAccountingSystem.setTable('rbAccountingSystem',  True)
        self.cmbFilterAccountingSystem.setValue(forceRef(QtGui.qApp.preferences.appPrefs.get('FilterAccountingSystem', 0)))
        self.connect(QtGui.qApp, SIGNAL('identCardReceived(PyQt_PyObject)'), self.onIdentCardReceived)
        self.btnRegistry.setEnabled(QtGui.qApp.userHasRight(urRegTabNewWriteRegistry))
        self.btnScan.setEnabled(forceBool(QtGui.qApp.preferences.appPrefs.get('ScanPromobotEnable')))


    def simplifiedClientSearch(self):
        ok, nameParts, date = CSimplifiedClientSearch(self).parseKey(unicode(self.edtKey.text()))
        if ok:
            widgets = (self.edtLastName,
                       self.edtFirstName,
                       self.edtPatrName,
                      )
            for part, edt in zip(nameParts, widgets):
                edt.setText(part)
            if date:
                self.edtBirthDate.setDate(date)


    @pyqtSignature('bool')
    def on_chkKey_toggled(self, checked):
        if checked:
                self.on_buttonBox_reset()

    def onPolicySmartCardReceived(self, data):
        def normalizeDict(d):
            result = {}
            for key, val in d.iteritems():
                if isinstance(key, QString):
                    key = unicode(key)
                if isinstance(val, QString):
                    val = unicode(val)
                elif isinstance(val, dict):
                    val = normalizeDict(val)
                result[key] = val
            return result

        def decodeDate(d):
            if d and isinstance(d, (tuple, list)) and len(d)==3:
                return QDate(*d)
            return None

        def findInsurer(OGRN, OKATO):
            db = QtGui.qApp.db
            table = db.table('Organisation')
            record = db.getRecordEx(table,
                                    'id',
                                    [ table['deleted'].eq(0),
                                      table['isInsurer'].eq(1),
                                      table['OGRN'].eq(OGRN),
                                      table['OKATO'].eq(OKATO),
                                    ]
                                   )
            if record:
                return forceRef(record.value(0))
            return None

        clientInfo = normalizeDict(data.toPyObject())
        lastName  = clientInfo.get('lastName')
        firstName = clientInfo.get('firstName')
        patrName  = clientInfo.get('patrName')
        sex       = clientInfo.get('sex')
        birthDate = decodeDate(clientInfo.get('birthDate'))
        policyNumber = clientInfo.get('policyNumber')
        insurerId = None
        smo = clientInfo.get('smo')
        if isinstance(smo, dict):
            OGRN  = smo.get('OGRN')
            OKATO = smo.get('OKATO')
            begDate = decodeDate(smo.get('begDate'))
            endDate = decodeDate(smo.get('endDate'))
            if OGRN and OKATO:
                insurerId = findInsurer(OGRN, OKATO)

        self.on_buttonBox_reset()
        if lastName:
            self.edtLastName.setText(lastName)
        if firstName:
            self.edtFirstName.setText(firstName)
        if patrName:
            self.edtPatrName.setText(patrName)
        if birthDate:
            self.edtBirthDate.setDate(birthDate)
        if sex:
            self.cmbFilterSex.setCurrentIndex(sex)
            
        if policyNumber:
            self.edtCompulsoryPolisSerial.setText('')
            self.edtCompulsoryPolisNumber.setText(policyNumber)
            self.cmbCompulsoryPolisCompany.setValue(insurerId)
            self.cmbCompulsoryPolisType.setCode(u'ОМС')
            self.cmbFilterPolicyKind.setCode('4')
            if begDate:
                self.edtPolicyBegDate.setDate(begDate)
            if endDate:
                self.edtPolicyEndDate.setDate(endDate)
            else:
                self.edtPolicyEndDate.setDate(None)
        self.on_buttonBox_apply()


    @pyqtSignature('const QString &')
    def on_edtKey_textChanged(self, text):
        ok, nameParts, date = CSimplifiedClientSearch(self).parseKey(unicode(text))
        self.btnApply.setEnabled(ok)


    def setupGetClientIdMenu(self):
        pass


    @pyqtSignature('')
    def on_actGetClientId_triggered(self):
        pass


    @pyqtSignature('bool')
    def on_chkFilterId_toggled(self, checked):
        self.cmbFilterAccountingSystem.setEnabled(checked)
        self.edtFilterId.setEnabled(checked)
        self.edtLastName.setEnabled(not checked)
        self.edtFirstName.setEnabled(not checked)
        self.edtPatrName.setEnabled(not checked)
        self.edtBirthDate.setEnabled(not checked)
        self.cmbDocType.setEnabled(not checked)
        self.edtLeftSerial.setEnabled(not checked)
        self.edtRightSerial.setEnabled(not checked)
        self.edtNumber.setEnabled(not checked)
        self.edtContact.setEnabled(not checked)
        self.edtCompulsoryPolisSerial.setEnabled(not checked)
        self.edtCompulsoryPolisNumber.setEnabled(not checked)
        self.cmbCompulsoryPolisCompany.setEnabled(not checked)
        self.cmbCompulsoryPolisType.setEnabled(not checked)
        self.chkFilterDocument.setEnabled(not checked)
        self.chkFilterPolicy.setEnabled(not checked)
        self.edtPolicyBegDate.setEnabled(not checked)
        self.edtPolicyEndDate.setEnabled(not checked)
        self.cmbFilterPolicyKind.setEnabled(not checked)
        self.chkKey.setEnabled(not checked)
        self.edtKey.setEnabled(not checked)


    @pyqtSignature('bool')
    def on_chkFilterPolicy_toggled(self, checked):
        self.edtCompulsoryPolisSerial.setEnabled(checked)
        self.edtCompulsoryPolisNumber.setEnabled(checked)
        self.cmbCompulsoryPolisCompany.setEnabled(checked)
        self.cmbCompulsoryPolisType.setEnabled(checked)
        self.edtPolicyBegDate.setEnabled(checked)
        self.edtPolicyEndDate.setEnabled(checked)
        self.cmbFilterPolicyKind.setEnabled(checked)


    @pyqtSignature('bool')
    def on_chkFilterDocument_toggled(self, checked):
        self.cmbDocType.setEnabled(checked)
        self.edtLeftSerial.setEnabled(checked)
        self.edtRightSerial.setEnabled(checked)
        self.edtNumber.setEnabled(checked)


    def setupHospitalizationEventMenu(self):
        self.addObject('mnuHospitalizationEvent', QtGui.QMenu(self))
        self.addObject('actEditClientInfo', QtGui.QAction(u'Открыть регистрационную карточку', self))
        self.actEditClientInfo.setShortcuts([Qt.Key_Enter,
                                             Qt.Key_Return,
                                             Qt.Key_Select,
                                            ]
                                           )
        self.addObject('actCreateEvent', QtGui.QAction(u'Новое обращение', self))
        self.addObject('actCreateRelatedAction', QtGui.QAction(u'Создать связанное действие', self))
        self.actCreateEvent.setShortcutContext(Qt.WidgetShortcut)
        self.actCreateEvent.setShortcut(Qt.Key_Space)
        self.mnuHospitalizationEvent.addAction(self.actEditClientInfo)
        self.mnuHospitalizationEvent.addAction(self.actCreateEvent)
        self.mnuHospitalizationEvent.addAction(self.actCreateRelatedAction)


    @pyqtSignature('')
    def on_actCreateRelatedAction_triggered(self):
        db = QtGui.qApp.db
        table = db.table('Client')
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        eventId = None

        self.clientId = self.getCurrentClientId()

        recordEventType = db.getRecordEx(tableEventType, [tableEventType['id']],
                                         [tableEventType['context'].like(u'relatedAction%'),
                                          tableEventType['deleted'].eq(0)], u'EventType.id')
        eventTypeId = forceRef(recordEventType.value('id')) if recordEventType else None
        if not eventTypeId:
            QtGui.QMessageBox().warning(self, u'Внимание!', u'Отсутствует тип события с контекстом "relatedAction"',
                                        QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
            return

        record = db.getRecord(table, '*', self.clientId)
        self.clientSex = forceInt(record.value('sex'))
        self.clientBirthDate = forceDate(record.value('birthDate'))
        self.clientAge = calcAgeTuple(self.clientBirthDate, QDate().currentDate())
        actionTypeIdList = selectActionTypes(self, self, [0, 1, 2, 3], orgStructureId=None, eventTypeId=None,
                                             contractId=None, mesId=None, eventDate=QDate().currentDate(),
                                             visibleTblSelected=False, preActionTypeIdList=[])
        if actionTypeIdList:
            prevEventId = eventId
            recordEvent = tableEvent.newRecord()
            recordEvent.setValue('createDatetime', toVariant(QDateTime().currentDateTime()))
            recordEvent.setValue('createPerson_id', toVariant(QtGui.qApp.userId))
            recordEvent.setValue('modifyDatetime', toVariant(QDateTime().currentDateTime()))
            recordEvent.setValue('modifyPerson_id', toVariant(QtGui.qApp.userId))
            recordEvent.setValue('setDate', toVariant(QDateTime().currentDateTime()))
            recordEvent.setValue('eventType_id', toVariant(eventTypeId))
            recordEvent.setValue('client_id', toVariant(self.clientId))
            recordEvent.setValue('prevEvent_id', toVariant(prevEventId))
            eventId = db.insertRecord(tableEvent, recordEvent)

            if eventId:
                recordEvent.setValue('id', toVariant(eventId))

        for actionTypeId in actionTypeIdList:
            if actionTypeId:
                dialog = CActionCreateDialog(self)
                QtGui.qApp.setCounterController(CCounterController(self))
                QtGui.qApp.setJTR(self)
                try:
                    actionType = CActionTypeCache.getById(actionTypeId)
                    defaultStatus = actionType.defaultStatus
                    newRecord = tableAction.newRecord()

                    newRecord.setValue('createDatetime', toVariant(QDateTime().currentDateTime()))
                    newRecord.setValue('createPerson_id', toVariant(QtGui.qApp.userId))
                    newRecord.setValue('modifyDatetime', toVariant(QDateTime().currentDateTime()))
                    newRecord.setValue('modifyPerson_id', toVariant(QtGui.qApp.userId))
                    newRecord.setValue('actionType_id', toVariant(actionTypeId))
                    newRecord.setValue('status', toVariant(defaultStatus))
                    newRecord.setValue('begDate', toVariant(QDateTime().currentDateTime()))
                    newRecord.setValue('directionDate', toVariant(QDateTime().currentDateTime()))
                    newRecord.setValue('setPerson_id', toVariant(QtGui.qApp.userId))
                    newRecord.setValue('id', toVariant(None))
                    newRecord.setValue('event_id', toVariant(eventId))

                    newAction = CAction(record=newRecord)
                    newAction.updatePresetValuesConditions({'clientId': self.clientId, 'eventTypeId': eventTypeId})
                    newAction.initPresetValues()

                    if not newAction:
                        return
                    dialog.load(newAction.getRecord(), newAction, self.clientId)
                    dialog.chkIsUrgent.setEnabled(True)
                    dialog.setReduced(True)
                    if dialog.exec_() and dialog.checkDataEntered(secondTry=True):
                        action = dialog.getAction()
                        if action:
                            action.save(idx=0, checkModifyDate=False)
                finally:
                    QtGui.qApp.unsetJTR(self)
                    QtGui.qApp.delAllCounterValueIdReservation()
                    QtGui.qApp.setCounterController(None)
                    dialog.deleteLater()

        if hasattr(self, 'clientSex'):
            delattr(self, 'clientSex')
        if hasattr(self, 'clientBirthDate'):
            delattr(self, 'clientBirthDate')
        if hasattr(self, 'clientAge'):
            delattr(self, 'clientAge')


    @pyqtSignature('int')
    def on_cmbFilterAccountingSystem_currentIndexChanged(self, index):
        self.edtFilterId.setValidator(None)
        if self.cmbFilterAccountingSystem.value():
            self.edtFilterId.setValidator(None)
        else:
            self.edtFilterId.setValidator(self.idValidator)


    @pyqtSignature('')
    def on_actEditClientInfo_triggered(self):
        clientId = self.getCurrentClientId()
        if clientId and QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]):
            self.selectHospitalizationEventCode(clientId)
            self.editClient(clientId)
            self.focusClients()


    @pyqtSignature('')
    def on_actCreateEvent_triggered(self):
        self.requestNewEvent()


    @pyqtSignature('')
    def on_mnuHospitalizationEvent_aboutToShow(self):
        currentIndex = self.tblHospitalizationEvent.currentIndex()
        isEnabled = currentIndex.row() >= 0
        self.actEditClientInfo.setEnabled(isEnabled)
        self.actCreateEvent.setEnabled(isEnabled)


    @pyqtSignature('int')
    def on_cmbCompulsoryPolisCompany_currentIndexChanged(self, index):
        self.updateCompulsoryPolicyType()
        self.getParamsDialogHospital()


    def updateCompulsoryPolicyType(self):
        serial = forceStringEx(self.edtCompulsoryPolisSerial.text())
        insurerId = self.cmbCompulsoryPolisCompany.value()
        if serial and insurerId:
            policyTypeId = advisePolicyType(insurerId, serial)
            self.cmbCompulsoryPolisType.setValue(policyTypeId)


    def mousePressEvent(self, event):
        parent = self.parentWidget()
        if parent!=None:
            opt=QtGui.QStyleOptionComboBox()
            opt.init(parent)
            arrowRect = parent.style().subControlRect(
                QtGui.QStyle.CC_ComboBox, opt, QtGui.QStyle.SC_ComboBoxArrow, parent)
            arrowRect.moveTo(parent.mapToGlobal(arrowRect.topLeft()))
            if (arrowRect.contains(event.globalPos()) or self.rect().contains(event.pos())):
                self.setAttribute(Qt.WA_NoMouseReplay)
        QtGui.QDialog.mousePressEvent(self, event)


    def closeEvent(self, event):
        preferences = self.tblHospitalizationEvent.savePreferences()
        setPref(QtGui.qApp.preferences.windowPrefs, 'CHospitalizationEventDialog', preferences)
        QtGui.QDialog.closeEvent(self, event)


    @pyqtSignature('')
    def on_btnReset_clicked(self):
        self.on_buttonBox_reset()


    @pyqtSignature('')
    def on_btnApply_clicked(self):
        self.on_buttonBox_apply()


    @pyqtSignature('')
    def on_btnRegistry_clicked(self):
        self.editNewClient()
        self.focusClients()


    @pyqtSignature('')
    def on_btnScan_clicked(self):
        scaningData = QtGui.qApp.callWithWaitCursor(self, scanning)
        if scaningData:
            self.on_buttonBox_reset()
            self.edtLastName.setText(scaningData['lastName'])
            self.edtFirstName.setText(scaningData['firstName'])
            self.edtPatrName.setText(scaningData['patrName'])
            self.edtBirthDate.setDate(scaningData['birthDate'])
            self.on_buttonBox_apply()


    def editNewClient(self):
        if QtGui.qApp.userHasAnyRight([urRegTabNewWriteRegistry]):
            dialog = CClientEditDialog(self)
            self.getParamsDialogHospital()
            if self.dialogInfo:
                dialog.setClientDialogInfo(self.dialogInfo)
            try:
                if dialog.exec_():
                    clientId = dialog.itemId()
                    self.tblHospitalizationEvent.model().setTable('Client')
                    self.setHospitalizationEventIdList([clientId], clientId)
            finally:
                dialog.deleteLater()


    @pyqtSignature('')
    def on_btnClose_clicked(self):
        self.close()


    def on_buttonBox_reset(self):
        self.dialogInfo = {}
        self.cmbFilterAccountingSystem.setValue(None)
        self.edtFilterId.setText('')
        self.edtLastName.setText('')
        self.edtFirstName.setText('')
        self.edtPatrName.setText('')
        self.edtBirthDate.setDate(QDate())
        self.cmbDocType.setValue(None)
        self.edtLeftSerial.setText('')
        self.edtRightSerial.setText('')
        self.edtNumber.setText('')
        self.newEventId = None
        self.edtContact.setText('')
        self.edtCompulsoryPolisSerial.setText('')
        self.edtCompulsoryPolisNumber.setText('')
        self.cmbCompulsoryPolisCompany.setValue(None)
        self.cmbCompulsoryPolisType.setValue(None)
        self.edtPolicyBegDate.setDate(None)
        self.edtPolicyEndDate.setDate(None)
        self.cmbFilterPolicyKind.setValue(None)
        self.cmbFilterSex.setCurrentIndex(0)
        self.chkFilterDocument.setChecked(False)
        self.chkFilterPolicy.setChecked(False)


    def on_buttonBox_apply(self):
        self.newEventId = None
        crIdList = self.getHospitalizationEventIdList()
        self.setHospitalizationEventIdList(crIdList, None)


    def setHospitalizationEventIdList(self, idList, posToId):
        if idList:
            self.tblHospitalizationEvent.setIdList(idList, posToId)
            self.tabWidget.setCurrentIndex(0)
            self.tabWidget.setTabEnabled(0, True)
            self.tblHospitalizationEvent.setFocus(Qt.OtherFocusReason)
        else:
            self.tabWidget.setCurrentIndex(1)
            self.tabWidget.setTabEnabled(0, False)
            self.edtLastName.setFocus(Qt.OtherFocusReason)
            res = QtGui.QMessageBox.warning(self,
                                            u'Внимание',
                                            u'Пациент не обнаружен.\nХотите зарегистрировать пациента?',
                                            QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel,
                                            QtGui.QMessageBox.Ok)
            if res == QtGui.QMessageBox.Ok:
                self.editNewClient()
                self.focusClients()


    def getParamsDialogHospital(self):
        self.dialogInfo = {}
        self.dialogInfo['lastName'] = forceString(self.edtLastName.text())
        self.dialogInfo['firstName'] = forceString(self.edtFirstName.text())
        self.dialogInfo['patrName'] = forceString(self.edtPatrName.text())
        self.dialogInfo['birthDate'] = forceDate(self.edtBirthDate.date())
        self.dialogInfo['docType'] = self.cmbDocType.value()
        self.dialogInfo['serialLeft'] = forceString(self.edtLeftSerial.text())
        self.dialogInfo['serialRight'] = forceString(self.edtRightSerial.text())
        self.dialogInfo['docNumber'] = forceString(self.edtNumber.text())
        self.dialogInfo['contact'] = forceString(self.edtContact.text())
        self.dialogInfo['polisSerial'] = forceString(self.edtCompulsoryPolisSerial.text())
        self.dialogInfo['polisNumber'] = forceString(self.edtCompulsoryPolisNumber.text())
        self.dialogInfo['polisCompany'] = self.cmbCompulsoryPolisCompany.value()
        self.dialogInfo['polisType'] = self.cmbCompulsoryPolisType.value()
        self.dialogInfo['polisTypeName'] = self.cmbCompulsoryPolisType.model().getName(self.cmbCompulsoryPolisType.currentIndex())
        self.dialogInfo['polisKind'] = self.cmbFilterPolicyKind.value()
        self.dialogInfo['sex'] = self.cmbFilterSex.currentIndex()
        self.dialogInfo['polisBegDate'] = forceDate(self.edtPolicyBegDate.date())
        self.dialogInfo['polisEndDate'] = forceDate(self.edtPolicyEndDate.date())
        self.dialogInfo['extendedPolicyInformation'] = { 'number'    : forceString(self.edtCompulsoryPolisNumber.text()),
                                               'insurerId' : self.cmbCompulsoryPolisCompany.value(),
                                               'begDate'   : forceDate(self.edtPolicyBegDate.date()),
                                               'endDate'   : forceDate(self.edtPolicyEndDate.date()),
                                               'polisKind' : self.cmbFilterPolicyKind.value()
                                               }


    def getHospitalizationEventIdList(self):
        self.dialogInfo = {}
        db = QtGui.qApp.db
        tableClient = db.table('Client')
        tableDocument = db.table('ClientDocument')
        tableAddress = db.table('ClientAddress')
        tableDocumentType = db.table('rbDocumentType')
        tableClientPolicy = db.table('ClientPolicy')
        tablePolicyType = db.table('rbPolicyType')
        tableOrganisation = db.table('Organisation')
        tableClientContact = db.table('ClientContact')
        cond = [tableClient['deleted'].eq(0)]
        queryTable = tableClient
        if self.chkFilterId.isChecked():
            accountingSystemId = self.cmbFilterAccountingSystem.value()
            clientId = forceStringEx(self.edtFilterId.text())
            if not accountingSystemId and clientId:
                clientId = parseClientId(clientId)
            if clientId:
                if accountingSystemId:
                    tableIdentification = db.table('ClientIdentification')
                    queryTable = queryTable.leftJoin(tableIdentification, tableIdentification['client_id'].eq(tableClient['id']))
                    cond.append(tableIdentification['accountingSystem_id'].eq(accountingSystemId))
                    cond.append(tableIdentification['identifier'].eq(clientId))
                    cond.append(tableIdentification['deleted'].eq(0))
                else:
                    cond.append(tableClient['id'].eq(clientId))
        else:
            if self.chkKey.isChecked():
                self.simplifiedClientSearch()
            lastName = forceString(self.edtLastName.text())
            firstName = forceString(self.edtFirstName.text())
            patrName = forceString(self.edtPatrName.text())
            birthDate = forceDate(self.edtBirthDate.date())
            sex = self.cmbFilterSex.currentIndex()
            docTypeId = self.cmbDocType.value()
            leftSerial = forceString(self.edtLeftSerial.text())
            rightSerial = forceString(self.edtRightSerial.text())
            number = forceString(self.edtNumber.text())
            contactText = self.edtContact.text()
            sex = self.cmbFilterSex.currentIndex()
            contact = forceString((contactText.remove(QChar('-'), Qt.CaseInsensitive)).remove(QChar(' '), Qt.CaseInsensitive))
            compulsoryPolisSerial = forceString(self.edtCompulsoryPolisSerial.text())
            compulsoryPolisNumber = forceString(self.edtCompulsoryPolisNumber.text())
            compulsoryPolisCompany = self.cmbCompulsoryPolisCompany.value()
            compulsoryPolisType = self.cmbCompulsoryPolisType.value()
            policyKind = self.cmbFilterPolicyKind.value()
            policyBegDate = forceDate(self.edtPolicyBegDate.date())
            policyEndDate = forceDate(self.edtPolicyEndDate.date())
            self.dialogInfo['lastName'] = lastName
            self.dialogInfo['firstName'] = firstName
            self.dialogInfo['patrName'] = patrName
            self.dialogInfo['birthDate'] = birthDate
            self.dialogInfo['docType'] = docTypeId
            self.dialogInfo['serialLeft'] = leftSerial
            self.dialogInfo['serialRight'] = rightSerial
            self.dialogInfo['docNumber'] = number
            self.dialogInfo['contact'] = forceString(self.edtContact.text())
            self.dialogInfo['polisSerial'] = compulsoryPolisSerial
            self.dialogInfo['polisNumber'] = compulsoryPolisNumber
            self.dialogInfo['polisCompany'] = compulsoryPolisCompany
            self.dialogInfo['polisType'] = compulsoryPolisType
            self.dialogInfo['polisTypeName'] = self.cmbCompulsoryPolisType.model().getName(self.cmbCompulsoryPolisType.currentIndex())
            self.dialogInfo['polisKind'] = policyKind
            self.dialogInfo['sex'] = sex
            self.dialogInfo['polisBegDate'] = policyBegDate
            self.dialogInfo['polisEndDate'] = policyEndDate
            self.dialogInfo['extendedPolicyInformation'] = { 'number'    : compulsoryPolisNumber,
                                               'insurerId' : compulsoryPolisCompany,
                                               'begDate'   : policyBegDate,
                                               'endDate'   : policyEndDate,
                                               'polisKind' : self.cmbFilterPolicyKind.value()
                                               }
            serial = u''
            if leftSerial:
                serial = leftSerial
            if rightSerial:
                if serial != u'':
                    serial += u' ' + rightSerial
                else:
                    serial += rightSerial
            queryTable = tableClient.leftJoin(tableAddress, db.joinAnd([tableClient['id'].eq(tableAddress['client_id']), tableAddress['deleted'].eq(0)]))
            if self.clientIdList:
                cond.append(tableClient['id'].inlist(self.clientIdList))
            if lastName:
                cond.append(tableClient['lastName'].like('%s%%'%lastName))
            if firstName:
                cond.append(tableClient['firstName'].like('%s%%'%firstName))
            if patrName:
                cond.append(tableClient['patrName'].like('%s%%'%patrName))
            if birthDate:
                cond.append(tableClient['birthDate'].eq(birthDate))
            if sex:
                cond.append(tableClient['sex'].eq(sex))
            if self.chkFilterDocument.isChecked():
                if docTypeId:
                    cond.append(tableDocument['documentType_id'].eq(docTypeId))
                if serial:
                    cond.append(tableDocument['serial'].eq(serial))
                if number:
                    cond.append(tableDocument['number'].eq(number))
                if docTypeId or serial or number:
                    queryTable = queryTable.innerJoin(tableDocument, tableClient['id'].eq(tableDocument['client_id']))
                    queryTable = queryTable.innerJoin(tableDocumentType, tableDocument['documentType_id'].eq(tableDocumentType['id']))
                    cond.append(tableDocument['deleted'].eq(0))
            if contact:
                queryTable = queryTable.innerJoin(tableClientContact, tableClient['id'].eq(tableClientContact['client_id']))
                strContact = u'%'
                for element in contact:
                    strContact += element + u'%'
                if len(strContact) > 1:
                    cond.append(tableClientContact['contact'].like(strContact))
            if self.chkFilterPolicy.isChecked():
                if compulsoryPolisSerial or compulsoryPolisNumber or compulsoryPolisCompany or compulsoryPolisType:
                    queryTable = queryTable.innerJoin(tableClientPolicy, tableClient['id'].eq(tableClientPolicy['client_id']))
                    if compulsoryPolisType:
                       queryTable = queryTable.innerJoin(tablePolicyType, tableClientPolicy['policyType_id'].eq(tablePolicyType['id']))
                    if compulsoryPolisCompany:
                        queryTable = queryTable.innerJoin(tableOrganisation, tableClientPolicy['insurer_id'].eq(tableOrganisation['id']))
                    if compulsoryPolisSerial:
                        cond.append(tableClientPolicy['serial'].eq(compulsoryPolisSerial))
                    if compulsoryPolisNumber:
                        cond.append(tableClientPolicy['number'].eq(compulsoryPolisNumber))
                    if compulsoryPolisCompany:
                        cond.append(tableClientPolicy['insurer_id'].eq(compulsoryPolisCompany))
                    if compulsoryPolisType:
                        cond.append(tableClientPolicy['policyType_id'].eq(compulsoryPolisType))
                    if policyKind:
                        cond.append(tableClientPolicy['policyKind_id'].eq(policyKind))
                    if policyBegDate:
                        cond.append(tableClientPolicy['begDate'].dateLe(policyBegDate))
                    if policyEndDate:
                        cond.append(
                                    db.joinOr(
                                              [
                                               tableClientPolicy['endDate'].dateGe(policyEndDate),
                                               tableClientPolicy['endDate'].isNull()
                                              ]
                                             )
                                   )

        orderList = ['Client.lastName', 'Client.firstName', 'Client.patrName']
        orderStr = ', '.join([fieldName for fieldName in orderList])
        idList = db.getDistinctIdList(queryTable, tableClient['id'].name(),
                              where=cond,
                              order=orderStr,
                              limit=1000)
        return idList


    def setDate(self, date):
        self.tableModel.date = date


    def selectHospitalizationEventCode(self, code):
        self.code = code
        self.emit(SIGNAL('HospitalizationEventCodeSelected(int)'), code)


    def getCurrentClientId(self):
        db = QtGui.qApp.db
        tableClient = db.table('Client')
        id = self.tblHospitalizationEvent.currentItemId()
        code = None
        if id:
            record = db.getRecordEx(tableClient, [tableClient['id']], [tableClient['deleted'].eq(0), tableClient['id'].eq(id)])
            if record:
                code = forceRef(record.value(0))
            return code
        return None


    @pyqtSignature('QModelIndex')
    def on_tblHospitalizationEvent_doubleClicked(self, index):
        if index.isValid():
            if (Qt.ItemIsEnabled & self.tableModel.flags(index)):
                clientId = self.getCurrentClientId()
                if clientId and QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]):
                    self.selectHospitalizationEventCode(clientId)
                    self.editClient(clientId)
                    self.focusClients()


    def editClient(self, clientId):
        if QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]):
            dialog = CClientEditDialog(self)
            try:
                if clientId:
                    dialog.load(clientId)
                if dialog.exec_():
                    clientId = dialog.itemId()
            finally:
                dialog.deleteLater()


    def focusClients(self):
        self.tblHospitalizationEvent.setFocus(Qt.TabFocusReason)


    def setHospitalBedsHasRight(self, hospitalBedsHasRight):
        self.hospitalBedsHasRight = hospitalBedsHasRight


    def requestNewEvent(self):
        if self.hospitalBedsHasRight:
            self.newEventId = None
            clientId = self.getCurrentClientId()
            self.close()
            if clientId:
                btnAction, actionId = self.checkPlanningOpenEvents(clientId, False)
                if btnAction == 1 and actionId:
                    db = QtGui.qApp.db
                    tableAction  = db.table('Action')
                    tableActionType = db.table('ActionType')
                    tableEvent  = db.table('Event')
                    table = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
                    table = table.innerJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
                    cols = [tableAction['id'],
                            tableEvent['client_id'],
                            tableAction['event_id'],
                            tableAction['setPerson_id'],
                            tableEvent['externalId'],
                            tableEvent['relegateOrg_id'],
                            tableEvent['relegatePerson_id'],
                            tableEvent['srcDate'],
                            tableEvent['srcNumber'],
                            tableAction['directionDate'],
                            tableAction['MKB'],
                            ]
                    cond = [tableEvent['client_id'].eq(clientId),
                            tableAction['deleted'].eq(0),
                            tableAction['status'].notInlist([CActionStatus.finished, CActionStatus.canceled, CActionStatus.refused]),
                            tableActionType['deleted'].eq(0),
                            tableEvent['deleted'].eq(0),
                            tableAction['id'].eq(actionId)
                            ]
                    record = db.getRecordEx(table, cols, cond, 'Action.begDate')
                    if record:
                        clientId = forceRef(record.value('client_id'))
                        eventId  = forceRef(record.value('event_id'))
                        directionInfo = [
                                            forceString(record.value('externalId')),
                                            forceRef(record.value('relegateOrg_id')),
                                            forceRef(record.value('relegatePerson_id')),
                                            forceString(record.value('srcDate')),
                                            forceString(record.value('srcNumber')),
                                            forceDate(record.value('directionDate')),
                                            forceRef(record.value('setPerson_id')),
                                            forceString(record.value('MKB')),
                                         ]
                    HospitalizationEvent = CHospitalizationFromQueue(self, clientId, eventId, directionInfo)
                    return HospitalizationEvent.requestNewEvent()
                else:
                    self.selectHospitalizationEventCode(clientId)
                    params = {}
                    params['widget'] = self
                    params['clientId'] = clientId
                    params['flagHospitalization'] = True
                    params['actionTypeId'] = None
                    params['valueProperties'] = [None, None]
                    params['eventTypeFilterHospitalization'] = (3 if self.isHBDeath else 2) if not self.isHealthResort else 5
                    if hasattr(self, 'emergencyInfo'):
                        params['emergencyInfo'] = self.emergencyInfo
                    self.newEventId = requestNewEvent(params)
                    return self.newEventId
        return None


    def onIdentCardReceived(self, identCard):
        self.on_buttonBox_reset()
        self.edtLastName.setText(identCard.lastName or '')
        self.edtFirstName.setText(identCard.firstName or '')
        self.edtPatrName.setText(identCard.patrName or '')
        self.cmbFilterSex.setCurrentIndex(identCard.sex or 0)
        self.edtBirthDate.setDate(identCard.birthDate or QDate())

        if identCard.policy:
            self.edtCompulsoryPolisSerial.setText(identCard.policy.serial)
            self.edtCompulsoryPolisNumber.setText(identCard.policy.number)
            self.cmbCompulsoryPolisType.setCode(u'ОМС')
            self.cmbCompulsoryPolisCompany.setValue(identCard.policy.insurerId)
            self.cmbFilterPolicyKind.setCode('4')
            self.edtPolicyBegDate.setDate(identCard.policy.begDate or QDate())
            self.edtPolicyEndDate.setDate(identCard.policy.endDate or QDate())
        self.on_buttonBox_apply()


    def checkPlanningOpenEvents(self, clientId, isVisible = True):
        result = (2, None)
        actionTypeIdList = getActionTypeIdListByFlatCode(u'planning%')
        if clientId and actionTypeIdList:
            db = QtGui.qApp.db
            tableAction  = db.table('Action')
            tableActionType = db.table('ActionType')
            tableEvent  = db.table('Event')
            table = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
            table = table.innerJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
            cols = [tableAction['id']]
            cond = [tableEvent['client_id'].eq(clientId),
                    tableAction['deleted'].eq(0),
                    tableAction['status'].notInlist([CActionStatus.finished, CActionStatus.canceled, CActionStatus.refused]),
                    tableActionType['deleted'].eq(0),
                    tableEvent['deleted'].eq(0),
                    tableActionType['id'].inlist(actionTypeIdList)
                    ]
            actionIdList = db.getIdList(table, cols, cond, 'Action.begDate')
            if actionIdList:
                dialog = CCheckPlanningOpenEvents(self, actionIdList, clientId, isVisible = isVisible)
                try:
                    dialog.exec_()
                    result = (dialog.btnResult, dialog.resultActionId)
                finally:
                    dialog.deleteLater()
        return result

from Ui_CheckPlanningOpenEventsDialog import Ui_CheckPlanningOpenEventsDialog

class CCheckPlanningOpenEvents(CDialogBase, Ui_CheckPlanningOpenEventsDialog):
    def __init__(self, parent, actionIdList = [], clientId = None, date= None, isVisible = True):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setWindowTitleEx(u'У выбранного пациента Планирование зарегистрировано ранее, продолжить создание нового Планирования, или открыть существующее?')
        cols = [
                CRefBookCol( u'Тип',              ['actionType_id'], 'ActionType',              40),
                CDateTimeCol(u'Дата начала',      ['begDate'],                                  10),
                CDateTimeCol(u'Дата окончания',   ['endDate'],                                  10),
                CDateCol(    u'Дата планирования',['plannedEndDate'],                           10),
                CEnumCol(    u'Статус',           ['status'],        CActionStatus.names,       5),
                CRefBookCol( u'Врач назначивший', ['setPerson_id'],  'vrbPersonWithSpeciality', 15),
                CRefBookCol( u'Врач выполнивший', ['person_id'],     'vrbPersonWithSpeciality', 15),
                CTextCol(    u'Примечания',       ['note'],                                     6)
               ]
        self.props = {}
        self.order = ['begDate']
        self.btnResult = None
        self.resultActionId = None
        self.actionIdList = actionIdList
        self.clientId = clientId
        self.date = date
        if not isVisible:
            self.btnCreate.setVisible(isVisible)
            self.btnOpen.setText(u'ОК')
            self.btnClose.setText(u'Отмена')
        self.model = CTableModel(self, cols, 'Action')
        self.model.setIdList(self.actionIdList)
        self.tblOpenActions.setModel(self.model)
        if self.actionIdList:
            self.tblOpenActions.selectRow(0)
        if self.clientId:
            self.txtClientInfoEventsBrowser.setHtml(getClientBanner(self.clientId, self.date))
        else:
            self.txtClientInfoEventsBrowser.setText('')
        self.btnClose.setFocus(Qt.TabFocusReason)
        QObject.connect(self.tblOpenActions.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.setSort)


    def currentItemId(self):
        return self.tblOpenActions.currentItemId()


    def select(self):
        table = self.model.table()
        return QtGui.qApp.db.getIdList(table.name(), 'id', table['id'].inlist(self.actionIdList), self.order)


    def renewList(self):
        idList = self.select()
        self.tblOpenActions.setIdList(idList)


    @pyqtSignature('')
    def on_btnClose_clicked(self):
        self.resultActionId = None
        self.btnResult = 0
        self.close()


    @pyqtSignature('')
    def on_btnOpen_clicked(self):
        self.resultActionId = self.currentItemId()
        self.btnResult = 1
        self.close()


    @pyqtSignature('')
    def on_btnCreate_clicked(self):
        self.resultActionId = None
        self.btnResult = 2
        self.close()


    def setSort(self, col):
        name = self.model.cols()[col].fields()[0]
        self.order = name
        header=self.tblOpenActions.horizontalHeader()
        header.setSortIndicatorShown(True)
        header.setSortIndicator(col, Qt.AscendingOrder)
        self.renewList()


    def destroy(self):
        pass


class CHospitalizationEventDialogTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.addColumn(CTextCol(u'Фамилия', ['lastName'], 30))
        self.addColumn(CTextCol(u'Имя', ['firstName'], 30))
        self.addColumn(CTextCol(u'Отчество', ['patrName'], 30))
        self.addColumn(CTextCol(u'Номер клиента', ['id'], 20))
        self.addColumn(CEnumCol(u'Пол', ['sex'], ['', u'М', u'Ж'], 10))
        self.addColumn(CDateCol(u'Дата рождения', ['birthDate'], 20))
        self.addColumn(CTextCol(u'Адрес регистрации', ['regAddress'], 20))
        self.addColumn(CTextCol(u'Адрес проживания', ['logAddress'], 20))
        self.addColumn(CTextCol(u'Контакт', ['contact'], 20))
        self.addColumn(CTextCol(u'Тип документа', ['name'], 20))
        self.addColumn(CTextCol(u'Серия документа', ['serial'], 20))
        self.addColumn(CTextCol(u'Номер документа', ['number'], 20))
        self.addColumn(CTextCol(u'Документ выдан', ['origin'], 20))
        self.addColumn(CDateCol(u'Дата выдачи документа', ['date'], 20))
        self.addColumn(CTextCol(u'страховая организация', ['nameOrgPolicy'], 20))
        self.addColumn(CTextCol(u'страховая Id', ['id'], 20))
        self.addColumn(CTextCol(u'Тип полиса', ['typePolicy'], 20))
        self.addColumn(CTextCol(u'Серия полиса', ['serialPolicy'], 20))
        self.addColumn(CTextCol(u'Номер полиса', ['numberPolicy'], 20))

        self.setTable('Client')
        self.date = QDate.currentDate()


    def flags(self, index):
        return Qt.ItemIsEnabled|Qt.ItemIsSelectable
#        row = index.row()
#        record = self.getRecordByRow(row)
#        enabled = True
#        if enabled:
#            return Qt.ItemIsEnabled|Qt.ItemIsSelectable
#        else:
#            return Qt.ItemIsSelectable


    def setTable(self, tableName):
        db = QtGui.qApp.db
        tableClient = db.table('Client')
        tableDocument = db.table('ClientDocument')
        tableAddress = db.table('ClientAddress')
        tableDocumentType = db.table('rbDocumentType')
        tableClientPolicy = db.table('ClientPolicy')
        tablePolicyType = db.table('rbPolicyType')
        tableOrganisation = db.table('Organisation')
        tableClientContact = db.table('ClientContact')
        loadFields = []
        loadFields.append(u'''DISTINCT Client.id, Client.lastName, Client.firstName, Client.patrName, Client.birthDate, Client.sex, ClientDocument.serial, ClientDocument.number, ClientDocument.date, ClientDocument.origin, rbDocumentType.name, IF(ClientAddress.type = 0,  ClientAddress.freeInput, _utf8'') AS regAddress, IF(ClientAddress.type = 1, ClientAddress.freeInput, _utf8'') AS logAddress, ClientPolicy.serial AS serialPolicy, ClientPolicy.number AS numberPolicy, rbPolicyType.name AS typePolicy, Organisation.shortName AS nameOrgPolicy, Organisation.id, ClientContact.contact''')
        queryTable = tableClient.leftJoin(tableAddress, tableClient['id'].eq(tableAddress['client_id']))
        queryTable = queryTable.leftJoin(tableDocument, tableClient['id'].eq(tableDocument['client_id']))
        queryTable = queryTable.leftJoin(tableDocumentType, tableDocument['documentType_id'].eq(tableDocumentType['id']))
        queryTable = queryTable.leftJoin(tableClientPolicy, tableClient['id'].eq(tableClientPolicy['client_id']))
        queryTable = queryTable.leftJoin(tablePolicyType, tableClientPolicy['policyType_id'].eq(tablePolicyType['id']))
        queryTable = queryTable.leftJoin(tableOrganisation, tableClientPolicy['insurer_id'].eq(tableOrganisation['id']))
        queryTable = queryTable.leftJoin(tableClientContact, tableClient['id'].eq(tableClientContact['client_id']))
        self._table = queryTable
        self._recordsCache = CTableRecordCache(db, self._table, loadFields)


class CFindClientInfoDialog(CHospitalizationEventDialog):
    def __init__(self, parent, clientIdList = []):
        CHospitalizationEventDialog.__init__(self, parent, clientIdList)
        self.filterClientId = None
        self.tblHospitalizationEvent.setPopupMenu(self.mnuGetClientId)
        self.isHBDeath = False


    def setIsHBDeath(self, isHBDeath = False):
        self.isHBDeath = isHBDeath


    def setupGetClientIdMenu(self):
        self.addObject('mnuGetClientId', QtGui.QMenu(self))
        self.addObject('actGetClientId', QtGui.QAction(u'''Добавить в фильтр "Стационарного монитора"''', self))
        self.addObject('actCreateRelatedAction', QtGui.QAction(u'Создать связанное действие', self))
        self.mnuGetClientId.addAction(self.actGetClientId)
        self.mnuGetClientId.addAction(self.actCreateRelatedAction)



    def setupGetClientIdMenuNew(self):
        self.addObject('mnuGetClientId2', QtGui.QMenu(self))
        self.addObject('actGetClientId2', QtGui.QAction(u'''Вставить код пациента''', self))
        self.mnuGetClientId2.addAction(self.actGetClientId2)
        self.actGetClientId2.triggered.connect(self.on_actGetClientId2_triggered)
        self.tblHospitalizationEvent.setPopupMenu(self.mnuGetClientId2)


    @pyqtSignature('')
    def on_actGetClientId_triggered(self):
        self.filterClientId = self.getCurrentClientId()
        self.close()


    @pyqtSignature('')
    def on_actGetClientId2_triggered(self):
        self.filterClientId = self.getCurrentClientId()
        self.close()


    @pyqtSignature('')
    def on_actCreateRelatedAction_triggered(self):
        db = QtGui.qApp.db
        table = db.table('Client')
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        eventId = None

        self.clientId = self.getCurrentClientId()

        recordEventType = db.getRecordEx(tableEventType, [tableEventType['id']],
                                         [tableEventType['context'].like(u'relatedAction%'),
                                          tableEventType['deleted'].eq(0)], u'EventType.id')
        eventTypeId = forceRef(recordEventType.value('id')) if recordEventType else None
        if not eventTypeId:
            QtGui.QMessageBox().warning(self, u'Внимание!', u'Отсутствует тип события с контекстом "relatedAction"',
                                        QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
            return

        record = db.getRecord(table, '*', self.clientId)
        self.clientSex = forceInt(record.value('sex'))
        self.clientBirthDate = forceDate(record.value('birthDate'))
        self.clientAge = calcAgeTuple(self.clientBirthDate, QDate().currentDate())
        actionTypeIdList = selectActionTypes(self, self, [0, 1, 2, 3], orgStructureId=None, eventTypeId=None,
                                             contractId=None, mesId=None, eventDate=QDate().currentDate(),
                                             visibleTblSelected=False, preActionTypeIdList=[])
        if actionTypeIdList:
            prevEventId = eventId
            recordEvent = tableEvent.newRecord()
            recordEvent.setValue('createDatetime', toVariant(QDateTime().currentDateTime()))
            recordEvent.setValue('createPerson_id', toVariant(QtGui.qApp.userId))
            recordEvent.setValue('modifyDatetime', toVariant(QDateTime().currentDateTime()))
            recordEvent.setValue('modifyPerson_id', toVariant(QtGui.qApp.userId))
            recordEvent.setValue('setDate', toVariant(QDateTime().currentDateTime()))
            recordEvent.setValue('eventType_id', toVariant(eventTypeId))
            recordEvent.setValue('client_id', toVariant(self.clientId))
            recordEvent.setValue('prevEvent_id', toVariant(prevEventId))
            eventId = db.insertRecord(tableEvent, recordEvent)

            if eventId:
                recordEvent.setValue('id', toVariant(eventId))

        for actionTypeId in actionTypeIdList:
            if actionTypeId:
                dialog = CActionCreateDialog(self)
                QtGui.qApp.setCounterController(CCounterController(self))
                QtGui.qApp.setJTR(self)
                try:
                    actionType = CActionTypeCache.getById(actionTypeId)
                    defaultStatus = actionType.defaultStatus
                    newRecord = tableAction.newRecord()

                    newRecord.setValue('createDatetime', toVariant(QDateTime().currentDateTime()))
                    newRecord.setValue('createPerson_id', toVariant(QtGui.qApp.userId))
                    newRecord.setValue('modifyDatetime', toVariant(QDateTime().currentDateTime()))
                    newRecord.setValue('modifyPerson_id', toVariant(QtGui.qApp.userId))
                    newRecord.setValue('actionType_id', toVariant(actionTypeId))
                    newRecord.setValue('status', toVariant(defaultStatus))
                    newRecord.setValue('begDate', toVariant(QDateTime().currentDateTime()))
                    newRecord.setValue('directionDate', toVariant(QDateTime().currentDateTime()))
                    newRecord.setValue('setPerson_id', toVariant(QtGui.qApp.userId))
                    newRecord.setValue('id', toVariant(None))
                    newRecord.setValue('event_id', toVariant(eventId))

                    newAction = CAction(record=newRecord)
                    newAction.updatePresetValuesConditions({'clientId': self.clientId, 'eventTypeId': eventTypeId})
                    newAction.initPresetValues()

                    if not newAction:
                        return
                    dialog.load(newAction.getRecord(), newAction, self.clientId)
                    dialog.chkIsUrgent.setEnabled(True)
                    dialog.setReduced(True)
                    if dialog.exec_() and dialog.checkDataEntered(secondTry=True):
                        action = dialog.getAction()
                        if action:
                            action.save(idx=0, checkModifyDate=False)
                finally:
                    QtGui.qApp.unsetJTR(self)
                    QtGui.qApp.delAllCounterValueIdReservation()
                    QtGui.qApp.setCounterController(None)
                    dialog.deleteLater()

        if hasattr(self, 'clientSex'):
            delattr(self, 'clientSex')
        if hasattr(self, 'clientBirthDate'):
            delattr(self, 'clientBirthDate')
        if hasattr(self, 'clientAge'):
            delattr(self, 'clientAge')


class CIdValidator(QtGui.QRegExpValidator):
    def __init__(self, parent):
        QtGui.QRegExpValidator.__init__(self, QRegExp(r'(\d*)(\.\d*)?'), parent)


def parseClientId(clientIdEx):
    if '.' in clientIdEx:
        miacCode, clientId = clientIdEx.split('.')
    else:
        miacCode, clientId = '', clientIdEx
    if miacCode:
        if forceString(QtGui.qApp.db.translate('Organisation', 'id', QtGui.qApp.currentOrgId(), 'miacCode')) != miacCode.strip():
            return -1
    return int(clientId)

