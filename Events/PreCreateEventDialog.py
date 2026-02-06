# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2024 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

# диалог предваряющий создание события

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDate, QDateTime, QObject, QTime, QString, pyqtSignature, SIGNAL

from Orgs.Utils import getPersonListByEventtypeId, getOrgstructureListByEventtypeId, \
    checkPersonByDefaultSettingsFromEventtype
from library.Calendar import wpFiveDays, wpSixDays, wpSevenDays
from library.Counter import CCounterController
from library.database import CTableRecordCache
from library.DialogBase import CDialogBase
from library.Utils import forceRef, forceString, forceStringEx, getPref, setPref, forceBool

from Events.Utils import (
    isEventResolutionOfDirection,
    checkUniqueEventExternalId,
    checkUniqueEventVoucherNumber,
    getEventCode,
    getEventCounterId,
    getEventDateInput,
    getEventvoucherCounterId,
    getEventDuration,
    getEventIsExternal,
    getEventIsTakenTissue,
    getEventShowTime,
    getEventType,
    getEventTypeForm,
    getEventWeekProfileCode,
    getOrgStructureEventTypeFilter,
    getWorkEventTypeFilter,
    hasEventAssistant,
    hasEventCurator,
    isEventLong,
    getEventTypeRelCounter,
    getEventTypeRelOrg,
    getEventMesCodeMask,
    getEventMesNameMask,
    getEventMesRequired
)

from Orgs.Orgs import selectOrganisation


from Events.Ui_PreCreateEventDialog import Ui_PreCreateEventDialog


class CPreCreateEventDialog(CDialogBase, Ui_PreCreateEventDialog):
    _orgId          = None
    _relegateOrgId  = None
    _srcNumber      = None
    _relegatePersonId = None
#    _eventTypeFilter= {}
    _eventTypeId    = None
    _personId       = None
    _assistantId    = None
    _curatorId      = None
    _eventSetDate   = None
    _eventDate      = None
    _addVisits      = False
    _tissueTypeId   = None
    _selectPreviousActions = False
    _connected      = False
    _useCurrentDate = True
    _eventId = None
    _orgStructureId = None
    _planningActionId = None

    def __init__(self, params):
        self._setupDateTimeEnded = False
        CDialogBase.__init__(self, params['widget'])
        self.setupUi(self)
        self.edtSrcDate.setDate(None)
        self.clientId                  = params['clientId']
        valueProperties                = params.get('valueProperties', [])
        orgStructureId                 = valueProperties[0] if len(valueProperties) == 1 else None
        eventTypeFilterHospitalization = params.get('eventTypeFilterHospitalization', 0)
        personId                       = params.get('personId', None)
        eventType_Form                       = params.get('eventType_Form', None)
        externalId                     = params.get('externalId', '')
#        relegateOrgId                  = params.get('relegateOrgId', None)
#        relegatePersonId               = params.get('relegatePersonId', None)
        self.dateTime                  = params.get('dateTime', None)
        self.params = params
        self.edtSrcDate.setDate(QDate())

        if eventTypeFilterHospitalization == 3:
            filter1 = "(EventType.purpose_id IN (SELECT rbEventTypePurpose.id from rbEventTypePurpose where rbEventTypePurpose.code = '5'))"
        elif eventTypeFilterHospitalization == 4:
            filter1 = "(EventType.purpose_id IN (SELECT rbEventTypePurpose.id from rbEventTypePurpose where rbEventTypePurpose.code = '999'))"
        else:
            filter1 = getWorkEventTypeFilter(isApplyActive=True)
        filter2 = getOrgStructureEventTypeFilter(orgStructureId if orgStructureId else QtGui.qApp.currentOrgStructureId())
        if eventTypeFilterHospitalization and eventTypeFilterHospitalization < 3:
            filter3 = ' AND (EventType.medicalAidType_id IN (SELECT rbMedicalAidType.id from rbMedicalAidType where rbMedicalAidType.code IN (\'1\', \'2\', \'3\', \'7\')))'
        elif eventTypeFilterHospitalization == 5:
            filter3 = ' AND (EventType.medicalAidType_id IN (SELECT rbMedicalAidType.id from rbMedicalAidType where rbMedicalAidType.code IN (\'8\')))'
        else:
            filter3 = ''
        filter4 = ' AND EventType.deleted = 0'
        if eventTypeFilterHospitalization in [3, 4] and forceBool(QtGui.qApp.preferences.appPrefs.get('isPreferencesEventTypeActive', False)):
            filter4 += u' AND EventType.isActive = 1'
        filter5 = ''' AND (EventType.context != 'flag' AND EventType.code != 'flag') '''
        if eventType_Form:
            filter6 = ' and EventType.form = "%s"' % eventType_Form
        else:
            filter6 = ''

        filter = 'EventType.deleted = 0 AND EventType.isActive = 1 AND ' + filter1 + ' AND ' + filter2 + filter3 + filter4 + filter5 + filter6
        self.cmbEventType.setTable('EventType',
                                   False,
                                   filter
                                  )
        self.cmbTissueType.setTable('rbTissueType')

        self.cmbRelegateOrg.setFilter('isMedical != 0 and deleted = 0 and isActive = 1')
        if not CPreCreateEventDialog._orgId:
            self.loadDefaults()
        self.isSrcRegion = False
        self.setRelegateVisible(CPreCreateEventDialog._eventTypeId, self.params)
        db = QtGui.qApp.db
        self.organisationCache = CTableRecordCache(db, db.forceTable('Organisation'), u'*', capacity=None)
        self.cmbSrcCity.setAreaSelectable(True)
        # self.cmbSrcCity.setCode(QtGui.qApp.defaultKLADR())
        self.lblMes.setVisible(False)
        self.cmbMes.setVisible(False)
        self.cmbSrcRegion.setEnabled(True)
        self.cmbOrg.setValue(CPreCreateEventDialog._orgId)
        self.cmbEventType.setValue(CPreCreateEventDialog._eventTypeId)
        self.cmbDirectedProfileId.setTable('rbHospitalBedProfile', addNone=True, order='code')
        self.cmbClientRelationId.setClientId(self.clientId)
        self.cmbAssistantId.setValue(CPreCreateEventDialog._assistantId)
        self.cmbCuratorId.setValue(CPreCreateEventDialog._curatorId)
        self.chkAddVisits.setChecked(CPreCreateEventDialog._addVisits)
        self.cmbWeekProfile.setCurrentIndex(getEventWeekProfileCode(self.cmbEventType.value()))
        self.cmbTissueType.setValue(CPreCreateEventDialog._tissueTypeId)
        self.chkSelectPreviousActions.setChecked(CPreCreateEventDialog._selectPreviousActions)
        self.chkUseCurrentDate.setChecked(False if params.get('actionListToNewEvent', None) else CPreCreateEventDialog._useCurrentDate)
        self.cmbPerson.setOrgStructureId(orgStructureId if orgStructureId else QtGui.qApp.currentOrgStructureId())
        self.cmbPerson.setBegDate(self.edtEventSetDate.date())
        self.cmbPerson.setValue(personId if personId else CPreCreateEventDialog._personId)
        
        self.cmbEventType.setFocus(Qt.OtherFocusReason)
        #if self.edtExternalId.isEnabled():
        self.edtExternalId.setText(externalId)
        self.setupDatesAndTimes()
        self.setupAssistant()
        self.setupCurator()
        self.setupExternal()
        self.setupTissue()
        self.setupSelectPreviousActions()
        self.setVoucherVisible()

        if not CPreCreateEventDialog._connected:
            QtGui.qApp.connect(QtGui.qApp, SIGNAL('dbConnectionChanged(bool)'), CPreCreateEventDialog.onConnectionChanged)
            CPreCreateEventDialog._connected = True


    def setRelegateVisible(self, eventTypeId, params):
        isResolutionOfDirection = bool(eventTypeId and isEventResolutionOfDirection(eventTypeId))
        self.cmbRelegateOrg.setVisible(isResolutionOfDirection)
        self.cmbRelegatePerson.setVisible(isResolutionOfDirection)
        self.edtRelegatePerson.setVisible(isResolutionOfDirection)
        self.edtSrcNumber.setVisible(isResolutionOfDirection)
        self.edtSrcDate.setVisible(isResolutionOfDirection)
        self.lblRelegateOrg.setVisible(isResolutionOfDirection)
        self.lblRelegate.setVisible(isResolutionOfDirection)
        self.lblN.setVisible(isResolutionOfDirection)
        self.lblRelegatePerson.setVisible(isResolutionOfDirection)
        self.lblSL.setVisible(isResolutionOfDirection)
        self.btnSelectRelegateOrg.setVisible(isResolutionOfDirection)
        self.btnCopyRelegateOrgId.setVisible(isResolutionOfDirection)
        eventTypeId = self.cmbEventType.value()
        showSrcToVoucher = (getEventTypeForm(eventTypeId) == '072') and isResolutionOfDirection
        self.lblSrcMKB.setVisible(showSrcToVoucher)
        self.edtSrcMKB.setVisible(showSrcToVoucher)
        self.lblSrcRegion.setVisible(showSrcToVoucher)
        self.cmbSrcRegion.setVisible(showSrcToVoucher)
        self.lblSrcCity.setVisible(showSrcToVoucher)
        self.cmbSrcCity.setVisible(showSrcToVoucher)
        if isResolutionOfDirection:
            if not QtGui.qApp.counterController():
                QtGui.qApp.setCounterController(CCounterController(self))
            srcOrgId         = params.get('srcOrgId', None)
            srcPerson        = params.get('srcPerson', '')
            srcNumber        = params.get('srcNumber', '')
            srcDate          = params.get('srcDate', QDate())
            relegateOrgId    = params.get('relegateOrgId', None)
            relegatePersonId = params.get('relegatePersonId', None)
            srcMKB           = params.get('srcMKB', '')
            CPreCreateEventDialog._relegateOrgId = getEventTypeRelOrg(eventTypeId)
            if not relegateOrgId:
                relegateOrgId = CPreCreateEventDialog._relegateOrgId if CPreCreateEventDialog._relegateOrgId else srcOrgId
            self.cmbRelegateOrg.setValue(relegateOrgId)
            self.cmbRelegatePerson.setOrganisationId(relegateOrgId if relegateOrgId else CPreCreateEventDialog._relegateOrgId)
            self.cmbRelegatePerson.setValue(relegatePersonId)
            if not relegatePersonId and srcPerson:
                self.edtRelegatePerson.setText(srcPerson)
            self.edtSrcMKB.setText(srcMKB)
            self.edtSrcDate.setDate(srcDate)
            self.edtSrcNumber.setText(srcNumber)
        else:
            self.cmbRelegateOrg.setValue(None)
            self.edtSrcNumber.setText('')


    def setVoucherVisible(self):
        eventTypeId = self.cmbEventType.value()
        showSrcToVoucher = (getEventTypeForm(eventTypeId) == '072')
        self.chkAddVisits.setVisible(not showSrcToVoucher)
        self.cmbWeekProfile.setVisible(not showSrcToVoucher)
        self.edtDays.setVisible(not showSrcToVoucher)
        self.addVisitsWidget.setVisible(not showSrcToVoucher)
        self.lblDays.setVisible(not showSrcToVoucher)
        self.edtDays.setVisible(not showSrcToVoucher)
        self.lblAssistantId.setVisible(not showSrcToVoucher)
        self.cmbAssistantId.setVisible(not showSrcToVoucher)
        self.lblCuratorId.setVisible(not showSrcToVoucher)
        self.cmbCuratorId.setVisible(not showSrcToVoucher)
        self.lblVoucher.setVisible(showSrcToVoucher)
        self.lblVoucherSerial.setVisible(showSrcToVoucher)
        self.edtVoucherSerial.setVisible(showSrcToVoucher)
        self.lblVoucherNumber.setVisible(showSrcToVoucher)
        self.edtVoucherNumber.setVisible(showSrcToVoucher)
        self.lblVoucherBegDate.setVisible(showSrcToVoucher)
        self.edtVoucherBegDate.setVisible(showSrcToVoucher)
        self.lblVoucherEndDate.setVisible(showSrcToVoucher)
        self.edtVoucherEndDate.setVisible(showSrcToVoucher)
        if showSrcToVoucher:
            self.edtVoucherEndDate.setDate(self.edtVoucherBegDate.date().addDays(QtGui.qApp.voucherDuration()))
            result = forceBool(getEventvoucherCounterId(eventTypeId))
            if result:
                result = result and not forceBool(QtGui.qApp.db.translate('rbCounter', 'id', getEventCounterId(eventTypeId), 'sequenceFlag'))
                self.edtVoucherNumber.setEnabled(result)
        self.lblDirectedToOSId.setVisible(showSrcToVoucher)
        self.cmbDirectedToOSId.setVisible(showSrcToVoucher)
        self.lblDirectedProfileId.setVisible(showSrcToVoucher)
        self.cmbDirectedProfileId.setVisible(showSrcToVoucher)
        self.lblClientRelationId.setVisible(showSrcToVoucher)
        self.cmbClientRelationId.setVisible(showSrcToVoucher)
        db = QtGui.qApp.db
        table = db.table('OrgStructure')
        cond = [table['hasHospitalBeds'].eq(1),
                      table['deleted'].eq(0),
                      table['organisation_id'].eq(QtGui.qApp.currentOrgId())
                     ]
        idList = db.getIdList(table, 'OrgStructure.id', cond)
        theseAndParentIdList = []
        if idList:
            theseAndParentIdList = db.getTheseAndParents('OrgStructure', 'parent_id', idList)
        filterCond = [table['id'].inlist(theseAndParentIdList if theseAndParentIdList else []),
                      table['deleted'].eq(0),
                      table['organisation_id'].eq(QtGui.qApp.currentOrgId())
                      ]
        self.cmbDirectedToOSId.setFilter(db.joinAnd(filterCond))


    def exec_(self):
        if not QtGui.qApp.counterController():
            QtGui.qApp.setCounterController(CCounterController(self))
        result = CDialogBase.exec_(self)
        if not result:
            QtGui.qApp.resetAllCounterValueIdReservation()
            QtGui.qApp.setCounterController(None)
        return result


    def loadDefaults(self):
        db = QtGui.qApp.db
        prefs = getPref(QtGui.qApp.preferences.appPrefs, 'PreCreateEvent', {})
        infisCode      = getPref(prefs, 'infisCode', '')
        eventTypeCode  = getPref(prefs, 'eventTypeCode', '01')
        personCode     = getPref(prefs, 'personCode', '')
        assistantCode  = getPref(prefs, 'assistantCode', '')
        curatorCode    = getPref(prefs, 'curatorCode', '')
        addVisits      = bool(getPref(prefs, 'addVisits', False))
        tissueTypeCode = getPref(prefs, 'tissueTypeCode', '1')
        CPreCreateEventDialog._relegateOrgId = getPref(prefs, 'relegateOrgId', None)
        CPreCreateEventDialog._relegatePersonId = getPref(prefs, 'relegatePersonId', None)
        selectPreviousActions = bool(getPref(prefs, 'selectPreviousActions', False))
        CPreCreateEventDialog._srcNumber = getPref(prefs, 'srcNumber', '')
        if infisCode:
            CPreCreateEventDialog._orgId = forceRef(db.translate('Organisation', 'infisCode', infisCode, 'id'))
        if not CPreCreateEventDialog._orgId:
            CPreCreateEventDialog._orgId = QtGui.qApp.currentOrgId()
        if not eventTypeCode:
            eventTypeCode = '01'
        CPreCreateEventDialog._eventTypeId = getEventType(eventTypeCode).eventTypeId
        if QtGui.qApp.userSpecialityId:
            CPreCreateEventDialog._personId = QtGui.qApp.userId
        elif personCode:
            CPreCreateEventDialog._personId = forceRef(db.translate('Person', 'code', personCode, 'id')) if personCode else None
        CPreCreateEventDialog._assistantId = forceRef(db.translate('Person', 'code', assistantCode, 'id')) if assistantCode else None
        CPreCreateEventDialog._curatorId   = forceRef(db.translate('Person', 'code', curatorCode, 'id')) if curatorCode else None
        CPreCreateEventDialog._tissueTypeId = forceRef(db.translate('rbTissueType', 'code', tissueTypeCode, 'id')) if tissueTypeCode else None
        CPreCreateEventDialog._selectPreviousActions = selectPreviousActions
        CPreCreateEventDialog._addVisits = addVisits


    def saveDefaults(self):
        db = QtGui.qApp.db

        orgId = self.cmbOrg.value()
        relegateOrgId = self.cmbRelegateOrg.value()
        relegatePersonId = self.cmbRelegatePerson.value()
        eventTypeId = self.cmbEventType.value()
        personId = self.cmbPerson.value()
        assistantId = self.cmbAssistantId.value()
        curatorId = self.cmbCuratorId.value()
        addVisits = self.chkAddVisits.isChecked()
        useCurrentDate = self.chkUseCurrentDate.isChecked()

        tissueTypeId = self.cmbTissueType.value()
        selectPreviousActions = self.chkSelectPreviousActions.isChecked()
        SrcNumber = self.edtSrcNumber.text()
        prefs = getPref(QtGui.qApp.preferences.appPrefs, 'PreCreateEvent', {})
        if CPreCreateEventDialog._orgId != orgId:
            CPreCreateEventDialog._orgId = orgId
            infisCode = forceString(db.translate('Organisation', 'id', orgId, 'infisCode'))
            setPref(prefs, 'infisCode', infisCode)
        if CPreCreateEventDialog._eventTypeId != eventTypeId:
            CPreCreateEventDialog._eventTypeId = eventTypeId
            eventTypeCode = getEventCode(eventTypeId)
            setPref(prefs, 'eventTypeCode', eventTypeCode)
        if CPreCreateEventDialog._personId != personId:
            CPreCreateEventDialog._personId = personId
            personCode = forceString(db.translate('Person', 'id', personId, 'code')) if personId else ''
            setPref(prefs, 'personCode', personCode)
        if CPreCreateEventDialog._assistantId != assistantId:
            CPreCreateEventDialog._assistantId = assistantId
            assistantCode = forceString(db.translate('Person', 'id', assistantId, 'code')) if assistantId else ''
            setPref(prefs, 'assistantId', assistantCode)
        if CPreCreateEventDialog._curatorId != curatorId:
            CPreCreateEventDialog._curatorId = curatorId
            curatorCode = forceString(db.translate('Person', 'id', curatorId, 'code')) if curatorId else ''
            setPref(prefs, 'curatorId', curatorCode)
        if CPreCreateEventDialog._addVisits != addVisits:
            CPreCreateEventDialog._addVisits = addVisits
            setPref(prefs, 'addVisits', addVisits)
        if CPreCreateEventDialog._tissueTypeId != tissueTypeId:
            CPreCreateEventDialog._tissueTypeId = tissueTypeId
            tissueTypeCode = forceString(db.translate('rbTissueType', 'id', tissueTypeId, 'code')) if tissueTypeId else ''
            setPref(prefs, 'tissueTypeCode', tissueTypeCode)
        if CPreCreateEventDialog._selectPreviousActions != selectPreviousActions:
            CPreCreateEventDialog._selectPreviousActions = selectPreviousActions
            setPref(prefs, 'selectPreviousActions', selectPreviousActions)
        if CPreCreateEventDialog._relegateOrgId != relegateOrgId:
            CPreCreateEventDialog._relegateOrgId = relegateOrgId
            setPref(prefs, 'relegateOrgId', relegateOrgId)
        if CPreCreateEventDialog._srcNumber != SrcNumber:
            CPreCreateEventDialog._srcNumber = SrcNumber
            srcNumberCode = forceString(db.translate('rbCounter_Value', 'value', SrcNumber, 'master_id')) if SrcNumber else ''
            setPref(prefs, 'srcNumber', srcNumberCode)
        if relegatePersonId and CPreCreateEventDialog._relegatePersonId != relegatePersonId:
            CPreCreateEventDialog._relegatePersonId = relegatePersonId
            setPref(prefs, 'relegatePersonId', relegatePersonId)
        if CPreCreateEventDialog._useCurrentDate != useCurrentDate:
            CPreCreateEventDialog._useCurrentDate = useCurrentDate

        setPref(QtGui.qApp.preferences.appPrefs, 'PreCreateEvent', prefs)


    def checkSpecialityId(self):
        personId = self.cmbPerson.value()
        if personId:
            eventTypeId = self.cmbEventType.value()
            if not eventTypeId:
                return False
            if getEventTypeForm(eventTypeId) == '090':
                specialityId = forceRef(QtGui.qApp.db.translate('Person', 'id', personId, 'speciality_id'))
                if not specialityId:
                    QtGui.QMessageBox.warning(self,
                                              u'Внимание!',
                                              u'У ответственного за событие не указана специальность. Выберите врача со специальностью!',
                                              QtGui.QMessageBox.Ok,
                                              QtGui.QMessageBox.Ok)
                    self.cmbPerson.setFocus(Qt.OtherFocusReason)
                    return False
        return True

    def checkCorrectlyEnteredCmbPerson(self, preference_flag, cmbPerson):
        message = u'Врач не соответствует умолчаниям типа события'
        result = True
        if not checkPersonByDefaultSettingsFromEventtype(cmbPerson.value(), self.eventTypeId()):
            result = result and self.checkValueMessage(message, preference_flag, cmbPerson)
        return result

    def saveData(self):
        result = True
        if QtGui.qApp.defaultNeedPreCreateEventPerson():
            result = bool(self.cmbPerson.value()) or self.checkInputMessage(u'ответственного врача', False, self.cmbPerson)
        if not QtGui.qApp.checkGlobalPreference('23:checkChosenPerson', u'не выполнять'):
            result = self.checkCorrectlyEnteredCmbPerson(QtGui.qApp.checkGlobalPreference('23:checkChosenPerson', u'мягкий'), self.cmbPerson)
        result = result and (self.cmbEventType.value() or self.checkInputMessage(u'цель обращения', False, self.cmbEventType))
        if result and self.checkOrGenerateUniqueEventExternalId() and self.checkOrGenerateUniqueEventVoucherNumber() and self.checkSpecialityId():
            self.saveDefaults()
            CPreCreateEventDialog._eventSetDate = self.edtEventSetDate.date()
            CPreCreateEventDialog._eventDate    = self.edtEventDate.date()
            return True
        return False


#    def getEventTypeFilter(self):
#        orgStructureId = QtGui.qApp.currentOrgStructureId()
#        filter = CPreCreateEventDialog._eventTypeFilter.get(orgStructureId, None)
#        if not filter:
#            filter = getWorkEventTypeFilter() + ' AND ' + getOrgStructureEventTypeFilter(orgStructureId)
#            CPreCreateEventDialog._eventTypeFilter[orgStructureId] = filter
#        return filter


    def setupDatesAndTimes(self, isDatesAndTimesUpdate = True):
        eventTypeId = self.cmbEventType.value()
        dateInput = getEventDateInput(eventTypeId)
        showTime  = getEventShowTime(eventTypeId)

        if dateInput == 0:
            self.edtEventSetDate.setEnabled(True)
            self.edtEventSetTime.setEnabled(True)
            self.edtEventDate.setEnabled(False)
            self.edtEventTime.setEnabled(False)
            self.edtEventDate.canBeEmpty(True)
            clearEndDate = False
        elif dateInput == 1:
            self.edtEventSetDate.setEnabled(False)
            self.edtEventSetTime.setEnabled(False)
            self.edtEventDate.setEnabled(True)
            self.edtEventTime.setEnabled(True)
            self.edtEventDate.canBeEmpty(False)
            clearEndDate = False
        else:
            self.edtEventSetDate.setEnabled(True)
            self.edtEventSetTime.setEnabled(True)
            self.edtEventDate.setEnabled(True)
            self.edtEventTime.setEnabled(True)
            self.edtEventDate.canBeEmpty(True)
            clearEndDate = True

        self.edtEventSetTime.setVisible(showTime)
        self.edtEventTime.setVisible(showTime)

        zeroTime = QTime(0, 0)
        now = QDateTime.currentDateTime()
        if self.chkUseCurrentDate.isChecked():
            setDate, setTime = now.date(), now.time()
            date, time = (QDate(), zeroTime) if clearEndDate else (setDate, setTime)
        else:
            if isDatesAndTimesUpdate or not self.edtEventSetDate.date():
                if self.dateTime:
                    setDate, setTime = self.dateTime.date(), self.dateTime.time()
                    date, time = (QDate(), zeroTime) if clearEndDate else (setDate, setTime)
                else:
                    setDate = CPreCreateEventDialog._eventSetDate if CPreCreateEventDialog._eventSetDate else now.date()
                    setTime = now.time() if now.date() == setDate else zeroTime
                    if clearEndDate:
                        date, time = QDate(), zeroTime
                    else:
                        date = CPreCreateEventDialog._eventDate if CPreCreateEventDialog._eventDate else now.date()
                        time = now.time() if now.date() == date and QtGui.qApp.userSpecialityId else zeroTime
        if self.chkUseCurrentDate.isChecked() or isDatesAndTimesUpdate or not self.edtEventSetDate.date():
            self.edtEventSetDate.setDate(setDate)
            self.edtEventSetTime.setTime(setTime)
            self.edtEventDate.setDate(date)
            self.edtEventTime.setTime(time)
            self._setupDateTimeEnded = True


    def setupAssistant(self):
        self.cmbAssistantId.setEnabled(hasEventAssistant(self.cmbEventType.value()))


    def setupCurator(self):
        self.cmbCuratorId.setEnabled(hasEventCurator(self.cmbEventType.value()))


    def setupExternal(self):
        eventTypeId = self.cmbEventType.value()
        isExternal = getEventIsExternal(eventTypeId)
        self.edtExternalId.setEnabled(isExternal and not getEventCounterId(eventTypeId))


    def setupTissue(self):
        eventTypeId = self.cmbEventType.value()
        isTakenTissue = getEventIsTakenTissue(eventTypeId)
        self.cmbTissueType.setEnabled(isTakenTissue)
        self.lblTissueType.setVisible(isTakenTissue)
        self.cmbTissueType.setVisible(isTakenTissue)


    def setupSelectPreviousActions(self):
        eventTypeId = self.cmbEventType.value()
        showChkSelectPreviousActions = getEventTypeForm(eventTypeId) == '001'
        self.chkSelectPreviousActions.setEnabled(showChkSelectPreviousActions)
        self.chkSelectPreviousActions.setVisible(showChkSelectPreviousActions)


    def orgId(self):
        return self.cmbOrg.value()


    def relegateOrgId(self):
        return self.cmbRelegateOrg.value()


    def relegatePersonId(self):
        return self.cmbRelegatePerson.value()


    def getSrcPerson(self):
        return self.edtRelegatePerson.text()


    def getSrcNumber(self):
        return self.edtSrcNumber.text()


    def getSrcDate(self):
        return self.edtSrcDate.date()


    def getSrcMKB(self):
        return self.edtSrcMKB.text()


    def getSrcRegion(self):
        return self.cmbSrcRegion.value()


    def getSrcCity(self):
        return self.cmbSrcCity.code()


    def getVoucherSerial(self):
        return self.edtVoucherSerial.text()


    def getVoucherNumber(self):
        return self.edtVoucherNumber.text()


    def getVoucherBegDate(self):
        return self.edtVoucherBegDate.date()


    def getVoucherEndDate(self):
        return self.edtVoucherEndDate.date()


    def eventTypeId(self):
        return self.cmbEventType.value()


    def personId(self):
        return self.cmbPerson.value()


    def getDirectedToOSId(self):
        return self.cmbDirectedToOSId.value()


    def getDirectedProfileId(self):
        return self.cmbDirectedProfileId.value()


    def getClientRelationId(self):
        return self.cmbClientRelationId.value()


    def assistantId(self):
        return self.cmbAssistantId.value() if self.cmbAssistantId.isEnabled() else None


    def curatorId(self):
        return self.cmbCuratorId.value() if self.cmbCuratorId.isEnabled() else None

    def eventId(self):
        return self._eventId

    def planningActionId(self):
        return self._planningActionId


    def orgStructureId(self):
        return self._orgStructureId


    def eventSetDate(self):
        eventTypeId = self.cmbEventType.value()
        dateInput = getEventDateInput(eventTypeId)
        showTime  = getEventShowTime(eventTypeId)
        if dateInput == 0:
            date = self.edtEventSetDate.date()
            time = self.edtEventSetTime.time()
        elif dateInput == 1:
            date = self.edtEventDate.date()
            time = self.edtEventTime.time()
        else:
            date = self.edtEventSetDate.date()
            time = self.edtEventSetTime.time()
        if showTime:
            return QDateTime(date, time)
        else:
            return QDateTime(date)


    def setCurTime(self, watched):
        eventTypeId = self.cmbEventType.value()
        showTime  = getEventShowTime(eventTypeId)
        if showTime:
            if str(watched.objectName()) == 'edtEventDate':
                self.edtEventTime.setTime(QTime.currentTime())
            elif str(watched.objectName()) == 'edtEventSetDate':
                self.edtEventSetTime.setTime(QTime.currentTime())


    def eventDate(self):
        eventTypeId = self.cmbEventType.value()
        dateInput = getEventDateInput(eventTypeId)
        showTime  = getEventShowTime(eventTypeId)
        if dateInput == 0:
            return QDateTime()
        elif dateInput == 1:
            date = self.edtEventDate.date()
            time = self.edtEventTime.time()
        else:
            date = self.edtEventDate.date()
            time = self.edtEventTime.time()
        if showTime:
            return QDateTime(date, time)
        else:
            return QDateTime(date)


    def externalId(self):
        eventTypeId = self.cmbEventType.value()
        return forceStringEx(self.edtExternalId.text()) if getEventIsExternal(eventTypeId) else ''


    def addVisits(self):
        return self.chkAddVisits.isChecked() if self.chkAddVisits.isEnabled() else False


    def weekProfile(self):
        weekProfileCode = self.cmbWeekProfile.currentIndex()
        return (wpFiveDays, wpSixDays, wpSevenDays)[weekProfileCode]


    def days(self):
        return self.edtDays.value() if self.edtDays.isEnabled() else 0


    def tissueTypeId(self):
        return self.cmbTissueType.value() if self.cmbTissueType.isEnabled() else None


    def mesId(self):
        return self.cmbMes.value()


    def selectPreviousActions(self):
        return self.chkSelectPreviousActions.isChecked() and self.chkSelectPreviousActions.isEnabled()


    def setDays(self):
        eventTypeId = self.cmbEventType.value()
        isLong = isEventLong(eventTypeId)
        dateInput = getEventDateInput(eventTypeId)
        setDate = self.edtEventSetDate.date()
        eventDate = self.edtEventDate.date()
        enableChkAddVisits = bool(isLong and dateInput == 2 and setDate and eventDate)
        self.chkAddVisits.setEnabled(enableChkAddVisits)
        addVisits = bool(enableChkAddVisits and self.chkAddVisits.isChecked())
        self.cmbWeekProfile.setEnabled(addVisits)
        self.edtDays.setEnabled(addVisits)
        if addVisits:
            totalDays = setDate.daysTo(eventDate)+1
            numDays = getEventDuration(setDate, eventDate, self.weekProfile(), self.cmbEventType.value())
            self.edtDays.setMaximum(totalDays)
            self.edtDays.setValue(numDays)


    def generateVoucherNumber(self):
        eventTypeId = self.cmbEventType.value()
        counterId = getEventvoucherCounterId(eventTypeId)
        if counterId:
            try:
                voucherNumberId = QtGui.qApp.getDocumentNumber(self.clientId, counterId)
                self.edtVoucherNumber.setText(voucherNumberId)
            except Exception, e:
                QtGui.QMessageBox.critical(QtGui.qApp.mainWindow,
                                           u'Внимание!',
                                           u'Произошла ошибка при получении значения счетчика\n%s' % e,
                                           QtGui.QMessageBox.Ok)
                return False
        return True


    def checkUniqueEventVoucherNumber(self):
        if self.edtVoucherNumber.isEnabled():
            voucherNumber = forceStringEx(self.edtVoucherNumber.text())
            if bool(voucherNumber):
                eventTypeId = self.cmbEventType.value()
                counterId = getEventvoucherCounterId(eventTypeId)
                isControlVoucherNumber = QtGui.qApp.isControlVoucherNumber()
                if isControlVoucherNumber or counterId:
                    sameVoucherNumberIdListInfo = checkUniqueEventVoucherNumber(voucherNumber, eventTypeId, self.edtEventSetDate.date(), None, forceStringEx(self.edtVoucherSerial.text()), counterId)
                    if bool(sameVoucherNumberIdListInfo):
                        sameVoucherNumberIdListText = '\n'.join(sameVoucherNumberIdListInfo)
                        message = u'Подобный номер путевки уже существует в других событиях:\n%s\n\n%s'%(sameVoucherNumberIdListText, u'Исправить?')
                        return self.checkValueMessage(message, False if isControlVoucherNumber == 2 else True, self.edtVoucherSerial)
        return True


    def checkOrGenerateUniqueEventVoucherNumber(self):
        if self.edtVoucherNumber.text():
            return self.checkUniqueEventVoucherNumber()
        else:
            return self.checkUniqueEventVoucherNumber() and self.generateVoucherNumber()


    def generateExternalId(self):
        eventTypeId = self.cmbEventType.value()
        counterId = getEventCounterId(eventTypeId)
        if counterId:
            try:
                externalId = QtGui.qApp.getDocumentNumber(self.clientId, counterId)
                self.edtExternalId.setText(externalId)
            except Exception, e:
                QtGui.QMessageBox.critical(QtGui.qApp.mainWindow,
                                           u'Внимание!',
                                           u'Произошла ошибка при получении значения счетчика\n%s' % e,
                                           QtGui.QMessageBox.Ok)
                return False
        return True


    def checkUniqueEventExternalId(self):
        if self.edtExternalId.isEnabled():
            externalId = self.externalId()
            if bool(externalId):
                eventTypeId = self.cmbEventType.value()
                sameExternalIdListInfo = checkUniqueEventExternalId(externalId, eventTypeId, self.edtEventSetDate.date(), None)
                if bool(sameExternalIdListInfo):
                    sameExternalIdListText = '\n'.join(sameExternalIdListInfo)
                    message = u'Подобный внешний идентификатор уже существует в других событиях:\n%s\n\n%s'%(
                                                                                    sameExternalIdListText, u'Исправить?')
                    return self.checkValueMessage(message, True, self.edtExternalId)
        return True


    def checkOrGenerateUniqueEventExternalId(self):
        if self.edtExternalId.text():
            return self.checkUniqueEventExternalId()
        else:
            return self.checkUniqueEventExternalId() and self.generateExternalId()


    @pyqtSignature('')
    def on_btnCopyRelegateOrgId_clicked(self):
        pass


    @pyqtSignature('')
    def on_btnSelectRelegateOrg_clicked(self):
        orgId = selectOrganisation(self, self.cmbRelegateOrg.value(), False, filter='isMedical != 0 and deleted = 0 and isActive = 1')
        self.cmbRelegateOrg.updateModel()
        if orgId:
            self.setIsDirty()
            self.cmbRelegateOrg.setValue(orgId)
            self.cmbRelegatePerson.setOrganisationId(orgId)


    @pyqtSignature('int')
    def on_cmbRelegateOrg_currentIndexChanged(self):
        if not self.isSrcRegion:
            orgId = self.cmbRelegateOrg.value()
            self.cmbRelegatePerson.setOrganisationId(orgId)
            if getEventTypeForm(self.cmbEventType.value()) == '072':
                okato = None
                record = self.organisationCache.get(orgId)
                if record:
                    okato = forceStringEx(record.value('OKATO'))
                    okato = QString(okato).left(5) if len(okato) > 5 else okato
                if self.cmbSrcRegion.value() != okato:
                    self.cmbSrcRegion.setValue(okato)
        self.isSrcRegion = False


    @pyqtSignature('int')
    def on_cmbSrcCity_currentIndexChanged(self, index):
        code = self.cmbSrcCity.code()
        self.cmbSrcRegion.setKladrCode(code)


    @pyqtSignature('int')
    def on_cmbSrcRegion_currentIndexChanged(self, index):
        if getEventTypeForm(self.cmbEventType.value()) == '072':
            orgId = self.cmbRelegateOrg.value()
            okato = self.cmbSrcRegion.value()
            filter = u'''Organisation.isMedical != 0'''
            if okato:
                filter += u''' AND Organisation.OKATO LIKE '%s%%' '''%(okato)
            if self.cmbRelegateOrg.filter != filter:
                self.isSrcRegion = True
                self.cmbRelegateOrg.setFilter(filter)
                self.isSrcRegion = True
                self.cmbRelegateOrg.setValue(orgId)


    @pyqtSignature('int')
    def on_cmbOrg_currentIndexChanged(self, index):
        orgId = self.cmbOrg.value()
        self.cmbPerson.setOrgId(orgId)


    @pyqtSignature('int')
    def on_cmbEventType_currentIndexChanged(self, idx):
        eventTypeId = self.cmbEventType.value()
        CPreCreateEventDialog._srcNumber = getEventTypeRelCounter(eventTypeId)
        CPreCreateEventDialog._relegateOrgId = getEventTypeRelOrg(eventTypeId)
        self.setRelegateVisible(eventTypeId, self.params)
        self.setVoucherVisible()
        if eventTypeId:
            self.cmbPerson.setOrgStructureList(getOrgstructureListByEventtypeId(eventTypeId))
            self.cmbPerson.setPersonIdList(getPersonListByEventtypeId(eventTypeId))
            db = QtGui.qApp.db
            tableEventType = db.table('EventType')
            record = db.getRecordEx(tableEventType, [tableEventType['form']], [tableEventType['deleted'].eq(0), tableEventType['id'].eq(eventTypeId)])
            form = forceString(record.value('form')) if record else ''
            if CPreCreateEventDialog._srcNumber:
                SrcNumberId = forceString(QtGui.qApp.getDocumentNumber(self.clientId, CPreCreateEventDialog._srcNumber))
                self.edtSrcNumber.setText(SrcNumberId)
            if form == '027':
                tableEvent = db.table('Event')
                record = db.getRecordEx(tableEvent, [tableEvent['curator_id'], tableEvent['assistant_id']], [tableEvent['eventType_id'].eq(eventTypeId), tableEvent['deleted'].eq(0)], 'Event.id DESC')
                if record:
                    CPreCreateEventDialog._assistantId = forceRef(record.value('assistant_id'))
                    CPreCreateEventDialog._curatorId   = forceRef(record.value('curator_id'))
                    self.cmbAssistantId.setValue(CPreCreateEventDialog._assistantId)
                    self.cmbCuratorId.setValue(CPreCreateEventDialog._curatorId)
            if form == '131' and getEventMesRequired(eventTypeId):
                self.lblMes.setVisible(True)
                self.cmbMes.setVisible(True)
                self.cmbMes.setMESCodeTemplate(getEventMesCodeMask(eventTypeId))
                self.cmbMes.setMESNameTemplate(getEventMesNameMask(eventTypeId))
                self.cmbMes.updateFilter()
                self.cmbMes.setCurrentIndex(1)
                self.cmbMes.setValue(self.cmbMes._model.getId(self.cmbMes.currentIndex()))
            else:
                self.lblMes.setVisible(False)
                self.cmbMes.setVisible(False)
                self.cmbMes.setValue(None)
        else:
            self.lblMes.setVisible(False)
            self.cmbMes.setVisible(False)
        self.setupDatesAndTimes()
        self.setupAssistant()
        self.setupCurator()
        self.setupExternal()
        self.setupTissue()
        self.setupSelectPreviousActions()


    @pyqtSignature('int')
    def on_cmbDirectedToOSId_currentIndexChanged(self, index):
        setFilter = u''
        orgStructureId = self.cmbDirectedToOSId.value()
        if orgStructureId:
            db = QtGui.qApp.db
            orgStructureIdList = db.getDescendants('OrgStructure', 'parent_id', orgStructureId)
            if orgStructureIdList:
                table = db.table('vHospitalBed')
                profileIdList = db.getDistinctIdList(table, [table['profile_id']], [table['master_id'].inlist(orgStructureIdList)])
                if profileIdList:
                    setFilter = u'id IN (%s)'%(u', '.join(str(profileId) for profileId in profileIdList if profileId))
        self.cmbDirectedProfileId.setTable('rbHospitalBedProfile', addNone=True, filter=setFilter, order='code')


    @pyqtSignature('QDate')
    def on_edtEventSetDate_dateChanged(self, date):
        self.cmbPerson.setBegDate(date)
        isLong = isEventLong(self.cmbEventType.value())
        if isLong:
            if self.edtEventSetDate.date() == QDate.currentDate():
                self.edtEventTime.setTime(QTime())
                self.edtEventDate.setDate(QDate())
        if self._setupDateTimeEnded:
            if date:
                if date == QDate.currentDate():
                    self.edtEventSetTime.setTime(QTime.currentTime())
                else:
                    self.edtEventSetTime.setTime(QTime(0, 0))
            else:
                self.edtEventSetTime.setTime(QTime())
        self.setDays()


    @pyqtSignature('QDate')
    def on_edtEventDate_dateChanged(self, date):
        self.cmbPerson.setEndDate(date)
        if self._setupDateTimeEnded:
            if date:
                if date == QDate.currentDate():
                    self.edtEventTime.setTime(QTime.currentTime())
                else:
                    self.edtEventTime.setTime(QTime(0, 0))
            else:
                self.edtEventTime.setTime(QTime())
        self.setDays()


    @pyqtSignature('bool')
    def on_chkAddVisits_toggled(self, checked):
        self.setDays()


    @pyqtSignature('bool')
    def on_chkUseCurrentDate_toggled(self, checked):
        self.setupDatesAndTimes(isDatesAndTimesUpdate = False)


    @pyqtSignature('int')
    def on_cmbWeekProfile_currentIndexChanged(self, index):
        self.setDays()


    @staticmethod
    def onConnectionChanged(value):
        if value:
            CPreCreateEventDialog._orgId          = None
            CPreCreateEventDialog._relegateOrgId  = None
            CPreCreateEventDialog._relegatePersonId = None
#            CPreCreateEventDialog._eventTypeFilter= {}
            CPreCreateEventDialog._eventTypeId    = None
            CPreCreateEventDialog._personId       = None
            CPreCreateEventDialog._assistantId    = None
            CPreCreateEventDialog._curatorId      = None
            CPreCreateEventDialog._eventSetDate   = None
            CPreCreateEventDialog._eventDate      = None
            CPreCreateEventDialog._addVisits      = False
            CPreCreateEventDialog._tissueTypeId   = None
            CPreCreateEventDialog._selectPreviousActions = False
            CPreCreateEventDialog._connected = False
            CPreCreateEventDialog._useCurrentDate = True
            QObject.disconnect(QtGui.qApp, SIGNAL('dbConnectionChanged(bool)'), CPreCreateEventDialog.onConnectionChanged)


    @staticmethod
    def onCurrentUserIdChanged():
        CPreCreateEventDialog._orgId = None
        CPreCreateEventDialog._relegateOrgId = None
        CPreCreateEventDialog._relegatePersonId = None
        CPreCreateEventDialog._eventTypeId = None
        CPreCreateEventDialog._personId = None
        CPreCreateEventDialog._assistantId = None
        CPreCreateEventDialog._curatorId = None
        CPreCreateEventDialog._eventSetDate = None
        CPreCreateEventDialog._eventDate = None
        CPreCreateEventDialog._addVisits = False
        CPreCreateEventDialog._tissueTypeId = None
        CPreCreateEventDialog._selectPreviousActions = False
        CPreCreateEventDialog._connected = False
        CPreCreateEventDialog._useCurrentDate = True

