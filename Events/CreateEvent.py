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

from PyQt4 import QtGui
from PyQt4.QtCore import QDate, QDateTime

from Events.Action import CActionTypeCache, CAction
from Events.ActionStatus import CActionStatus
from Events.ActionTypeDialog import CActionTypeDialogTableModel
from F088.F088CreateDialog import CF088CreateDialog
from F088.F088EditDialog import CF088EditDialog
from F088.F0882022EditDialog                import CF0882022EditDialog
from F088.F0882022CreateDialog              import CF0882022CreateDialog
from F090.F090CreateDialog import createF090
from F090.F090EditDialog import CF090EditDialog
from library.AgeSelector          import checkAgeSelector
from library.Utils import calcAgeTuple, exceptionToUnicode, forceBool, forceDate, forceDateTime, forceRef, forceString, formatDateTime, toVariant, forceInt
from library.PrintTemplates import applyTemplate

from Events.EditDispatcher        import getEventFormClass, getEventFormClassByType, getF090ActionIdToEventId
from Events.PreCreateEventDialog import CPreCreateEventDialog
from Events.Utils import CEventTypeDescription, CFinanceType, getActionTypeIdListByFlatCode, getEventShowTime, checkEventPosibility, getDeathDate, getEventAgeSelector, \
    getEventFinanceCode, getEventTypeForm, getEventProfileId, isEventDeath, getEventOrder, getEventContextData, \
    getEventAidTypeRegionalCode
from Registry.CheckEnteredOpenEventsDialog import CCheckEnteredOpenEvents
from Registry.Utils import getClientCompulsoryPolicy, getClientInfo, getClientVoluntaryPolicy, getClientWork, getClientIdentifications
from Users.Rights import urAdmin, urRegTabWriteEvents, urNewEventCliSnils, urNewEventCliPolis, urNewEventCliUDL, urHospitalOverWaitDirection


def requestNewEvent(params):
    widget = params['widget']
    clientId = params['clientId']
    if QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteEvents]) and clientId and checkClientCanHaveEvent(widget, clientId):
        flagHospitalization = params.get('flagHospitalization', False)
        actionTypeId        = params.get('actionTypeId', None)
        valueProperties     = params.get('valueProperties', [])
        planningEventId     = params.get('planningEventId', None)
        planningActionId    = params.get('planningActionId', None)
        diagnos             = params.get('diagnos', '')
        financeId           = params.get('financeId', None)
        protocolQuoteId     = params.get('protocolQuoteId', None)
        actionByNewEvent    = params.get('actionByNewEvent', [])
        transferDataList    = params.get('transferDataList', [])
        relegateOrgId       = params.get('relegateOrgId', None)
        relegatePersonId    = params.get('relegatePersonId', None)
        prevEventId         = params.get('prevEventId', None)
        order               = params.get('order', None)
        isMoving            = params.get('moving', False)
        emergencyInfo       = params.get('emergencyInfo', None)
        actionListToNewEvent = params.get('actionListToNewEvent', [])
        eventDatetime        = params.get('endDateTime', None)
        typeQueue            = params.get('typeQueue', -1)
        result               = params.get('result', None)
        docNum               = params.get('docNum', None)
        plannedEndDate       = params.get('plannedEndDate', None)
        mapJournalInfoTransfer = params.get('mapJournalInfoTransfer', None)
        #planningActionId = None
        actionBegDate = None
        actionEndDate = None

        while True:
            destroyCounterController()
            dlg = CPreCreateEventDialog(params)
            if transferDataList:
                externalId        = params.get('externalId', '')
            else:
                if not dlg.exec_():
                    return
                externalId        = dlg.externalId()

            if dlg.eventId():
                planningEventId = dlg.eventId()
                prevEventId = dlg.eventId()
                valueProperties = [dlg.orgStructureId(), None]
                flagHospitalization = True
                planningActionId = dlg.planningActionId()

            orgId                 = dlg.orgId()
            relegateOrgId         = dlg.relegateOrgId()
            relegatePersonId      = dlg.relegatePersonId()
            srcPerson             = dlg.getSrcPerson()
            srcNumber             = dlg.getSrcNumber()
            srcDate               = dlg.getSrcDate()
            srcMKB                = dlg.getSrcMKB()
            relegateInfo          = [srcPerson, srcNumber, srcDate, relegateOrgId, relegatePersonId, srcMKB]

            eventTypeId           = dlg.eventTypeId()
            tissueTypeId          = dlg.tissueTypeId()
            personId              = dlg.personId()
            eventSetDatetime      = dlg.eventSetDate()
            if not eventDatetime:
                eventDatetime     = dlg.eventDate()
            weekProfile           = dlg.weekProfile()
            selectPreviousActions = dlg.selectPreviousActions()
            days                  = dlg.days()
            assistantId           = dlg.assistantId()
            curatorId             = dlg.curatorId()
            mesId                 = dlg.mesId()
            eventSetDate = eventSetDatetime.date() if eventSetDatetime else None
            eventDate    = eventDatetime.date() if eventDatetime else None
            form         = getEventTypeForm(eventTypeId)
            eventProfileId = getEventProfileId(eventTypeId)
            eventProfileRegionalCode = forceString(QtGui.qApp.db.translate('rbEventProfile', 'id', eventProfileId, 'regionalCode'))
            voucherParams = {}
            financeCode = getEventFinanceCode(eventTypeId)

            # проверять только при создании событий по омс
            if financeCode == CFinanceType.CMI and not checkFirstEvent(clientId, personId, eventSetDate, eventDate, eventTypeId):
                if QtGui.QMessageBox.question(widget,
                                    u'Внимание!',
                                    u'У этого пациента в этом месяце уже была услуга от врача данной специальности.\nПродолжить?',
                                    QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel,
                                    QtGui.QMessageBox.Yes) == QtGui.QMessageBox.Cancel:
                    break

            if form == '088':
                db = QtGui.qApp.db
                tableActionType = db.table('ActionType')
                cond = [tableActionType['deleted'].eq(0), tableActionType['flatCode'].like(u'inspection_mse%'), tableActionType['showInForm'].eq(1)]
                actionTypeIdList = db.getIdList(tableActionType, 'id', cond)
                if actionTypeIdList:
                    actionTypeId = None
                    if len(actionTypeIdList) > 1:
                        dialog = None
                        try:
                            dialog = CActionTypeDialogTableModel(QtGui.qApp.mainWindow.registry, actionTypeIdList)
                            dialog.setWindowTitle(u'Выберите тип направления на МСЭ')
                            if dialog.exec_():
                                actionTypeId = dialog.currentItemId()
                        except Exception:
                            QtGui.qApp.logCurrentException()
                        finally:
                            if dialog:
                                dialog.deleteLater()
                    else:
                        actionTypeId = actionTypeIdList[0]
                    if actionTypeId:
                        eventId = None
                        if False and QDate().currentDate() < QDate(2021, 1, 1):
                            dialog = CF088CreateDialog(QtGui.qApp.mainWindow.registry, eventTypeId)
                        else:
                            dialog = CF0882022CreateDialog(QtGui.qApp.mainWindow.registry, eventTypeId)
                        try:
                            tableAction = QtGui.qApp.db.table('Action')
                            actionType = CActionTypeCache.getById(actionTypeId)
                            defaultStatus = actionType.defaultStatus
                            defaultOrgId = actionType.defaultOrgId
                            # defaultExecPersonId = actionType.defaultExecPersonId
                            newRecord = tableAction.newRecord()
                            newRecord.setValue('createDatetime', toVariant(QDateTime().currentDateTime()))
                            newRecord.setValue('createPerson_id', toVariant(QtGui.qApp.userId))
                            newRecord.setValue('modifyDatetime', toVariant(QDateTime().currentDateTime()))
                            newRecord.setValue('modifyPerson_id', toVariant(QtGui.qApp.userId))
                            newRecord.setValue('actionType_id', toVariant(actionTypeId))
                            newRecord.setValue('status', toVariant(defaultStatus))
                            newRecord.setValue('begDate', toVariant(eventSetDate))
                            newRecord.setValue('directionDate', toVariant(eventSetDate))
                            newRecord.setValue('org_id', toVariant(defaultOrgId if defaultOrgId else QtGui.qApp.currentOrgId()))
                            newRecord.setValue('setPerson_id', toVariant(QtGui.qApp.userId))
                            newRecord.setValue('person_id', toVariant(personId))
                            newRecord.setValue('id', toVariant(None))
                            # newRecord = preFillingActionRecordMSI(newRecord, actionTypeId)
                            newAction = CAction(record=newRecord)
                            if not newAction:
                                return
                            if u'Номер' in newAction.getType()._propertiesByName:
                                newAction[u'Номер'] = None
                            eventId = None
                            dialog.load(newAction.getRecord(), newAction, clientId, recordFirstEvent=None)
                            dialog.exec_()
                        finally:
                            dialog.deleteLater()
                            destroyCounterController()
                            return eventId
            # --------------
            if form == '090':
                if not personId:
                    QtGui.QMessageBox.warning(widget,
                                              u'Внимание!',
                                              u'Укажите врача ответственного за событие. Выберите врача со специальностью!',
                                              QtGui.QMessageBox.Ok,
                                              QtGui.QMessageBox.Ok)
                    break
            if form == '072':
                voucherParams['directionOrgId'] = relegateOrgId
                voucherParams['directionPersonId'] = relegatePersonId
                voucherParams['directionInfo'] = relegateInfo
                voucherParams['directionMKB'] = dlg.getSrcMKB()
                voucherParams['directionCity'] = dlg.getSrcCity()
                voucherParams['directionRegion'] = dlg.getSrcRegion()
                voucherParams['voucherSerial'] = dlg.getVoucherSerial()
                voucherParams['voucherNumber'] = dlg.getVoucherNumber()
                voucherParams['voucherBegDate'] = dlg.getVoucherBegDate()
                voucherParams['voucherEndDate'] = dlg.getVoucherEndDate()
                voucherParams['directedToOSId'] = dlg.getDirectedToOSId()
                voucherParams['directedProfileId'] = dlg.getDirectedProfileId()
                voucherParams['clientRelationId'] = dlg.getClientRelationId()
            deathDate = forceDateTime(QtGui.qApp.db.translate('Client', 'id', clientId, 'deathDate'))
            SNILS = forceString(QtGui.qApp.db.translate('Client', 'id', clientId, 'SNILS'))
            pol=getClientInfo(clientId)
            policyRecord = pol.get('compulsoryPolicyRecord')
            doc=getClientInfo(clientId)
            # Проверка на превышение сроков госпитализации
            if QtGui.qApp.provinceKLADR()[:2] == u'23' \
            and getEventAidTypeRegionalCode(eventTypeId) in ['11', '12', '301', '302', '401', '402', '41', '42', '43', '51', '52', '71', '72', '90', '411', '422', '511', '522'] \
            and srcDate and eventSetDate.addDays(-14) > srcDate:
                msg = u'Дата госпитализации превышает 14 дней от даты направления.\nПродолжить госпитализацию?'
                if QtGui.qApp.userHasRight(urAdmin) or QtGui.qApp.userHasRight(urHospitalOverWaitDirection):
                    boxResult = QtGui.QMessageBox.question(widget,
                        u'Внимание!',
                        msg,
                        QtGui.QMessageBox.Close|QtGui.QMessageBox.Retry|QtGui.QMessageBox.Ignore,
                        QtGui.QMessageBox.Ignore
                        )
                else:
                    boxResult = QtGui.QMessageBox.question(widget,
                        u'Внимание!',
                        msg,
                        QtGui.QMessageBox.Close|QtGui.QMessageBox.Retry
                        )
                if boxResult == QtGui.QMessageBox.Retry:
                    continue
                elif boxResult == QtGui.QMessageBox.Close:
                    break
            documentRecord = doc.get('documentRecord')
            if order is None:
                order = getEventOrder(eventTypeId)
            if not eventSetDate and not eventDate:
                msg = u'Новый осмотр не может быть добавлен.\nНе введены даты начала и выполнения данного события.'
                boxResult = QtGui.QMessageBox.question(widget,
                    u'Внимание!',
                    msg,
                    QtGui.QMessageBox.Close|QtGui.QMessageBox.Retry,
                    QtGui.QMessageBox.Close
                    )
                if boxResult == QtGui.QMessageBox.Retry:
                    continue
                else:
                    break

            #  контроль 2 эпата ДД без первого для КК
            if eventProfileRegionalCode in ['8009', '8015'] and QtGui.qApp.defaultKLADR()[:2] == u'23':
                stmt = """select e.id
                from Event e
                left join EventType et on et.id = e.eventType_id
                left join rbEventProfile ep on ep.id = et.eventProfile_id
                left join rbMedicalAidType mt on mt.id = et.medicalAidType_id
                where e.client_id = %d
                    and (ep.regionalCode in ('8008', '8014') or mt.regionalCode = '261')
                    and e.deleted = 0
                    and e.execDate >= year(%s)
                """ % (clientId, QtGui.qApp.db.formatDate(eventSetDate))
                if QtGui.qApp.db.query(stmt).size() == 0:
                    msg = u"Для данного пациента отсутствует обращение по диспансеризации взрослого населения I этапа"
                    boxResult = QtGui.QMessageBox.critical(widget,
                                                    u'Внимание!',
                                                    msg,
                                                    QtGui.QMessageBox.Cancel|QtGui.QMessageBox.Ignore,
                                                    QtGui.QMessageBox.Ignore)
                    if boxResult == QtGui.QMessageBox.Cancel:
                        break
                    
            eventId = None if QtGui.qApp.isDisabledEventForPersonOrSpeciality() else findCreateEventToDate(eventTypeId, personId, clientId, eventSetDate, eventDate)
            if eventId and form != '090':
                msg = u'Новый осмотр указанного типа не может быть добавлен.\nОткрыть существующий?'
                boxResult = QtGui.QMessageBox.question(widget,
                    u'Внимание!',
                    msg,
                    QtGui.QMessageBox.Yes|QtGui.QMessageBox.No|QtGui.QMessageBox.Retry,
                    QtGui.QMessageBox.Yes
                    )
                if boxResult == QtGui.QMessageBox.Retry:
                    continue
                elif boxResult == QtGui.QMessageBox.Yes and eventId:
                    destroyCounterController()
                    editEvent(widget, eventId, eventTypeId)
                    return eventId
                else:
                    break
            if deathDate and deathDate <= eventSetDatetime and not isEventDeath(eventTypeId):
                QtGui.QMessageBox.critical(widget,
                                                u'Внимание!',
                                                u'Пациент умер %s'%formatDateTime(deathDate),
                                                QtGui.QMessageBox.Ok,
                                                QtGui.QMessageBox.Ok)
                break
            if not policyRecord and not QtGui.qApp.userHasRight(urNewEventCliPolis):
                QtGui.QMessageBox.critical(widget,
                                                u'Внимание!',
                                                u'Обслуживание пациента запрещено, в регистрационной карте пациента не заполнен полис ОМС',
                                                QtGui.QMessageBox.Ok,
                                                QtGui.QMessageBox.Ok)
                break
            if not SNILS and not QtGui.qApp.userHasRight(urNewEventCliSnils):
                QtGui.QMessageBox.critical(widget,
                                                u'Внимание!',
                                                u'Обслуживание пациента запрещено, в регистрационной карте пациента не заполнен СНИЛС',
                                                QtGui.QMessageBox.Ok,
                                                QtGui.QMessageBox.Ok)
                break
            if not documentRecord and not QtGui.qApp.userHasRight(urNewEventCliUDL):
                QtGui.QMessageBox.critical(widget,
                                                u'Внимание!',
                                                u'Обслуживание пациента запрещено, в регистрационной карте пациента не заполнен документ УДЛ',
                                                QtGui.QMessageBox.Ok,
                                                QtGui.QMessageBox.Ok)
                break
            resCheckSocStatus, isCheckSocStatus, socStatusNames = checkSocStatus(widget, clientId, eventSetDate)
            if not resCheckSocStatus and isCheckSocStatus:
                msg = u'''У пациента отсутствует обязательный социальный статус: '%s'!'''%(socStatusNames)
                if isCheckSocStatus == 1:
                    buttonBox = QtGui.QMessageBox.Ignore|QtGui.QMessageBox.Close
                else:
                    buttonBox = QtGui.QMessageBox.Close
                boxResult = QtGui.QMessageBox.question(widget,
                    u'Внимание!',
                    msg,
                    buttonBox,
                    QtGui.QMessageBox.Close
                    )
                if boxResult == QtGui.QMessageBox.Close:
                    break
            if not checkEventTypeAge(widget, clientId, eventTypeId, eventSetDate):
                msg = u'Новый осмотр указанного типа не может быть добавлен.\nВозраст пациента не попадает в диапазон возрастов данного события.'
                boxResult = QtGui.QMessageBox.question(widget,
                    u'Внимание!',
                    msg,
                    QtGui.QMessageBox.Close,
                    QtGui.QMessageBox.Close
                    )
                break
            if eventDate and eventSetDate > eventDate:
                if not confirmTrouble(widget, u'Дата окончания %s не может быть раньше даты начала %s' % (forceString(eventDate), forceString(eventSetDate))):
                    continue
            if not checkDatesRegardToClientLife(widget, clientId, eventSetDate, eventDate, eventTypeId):
                continue
            if form != '090' and not checkWorkHurts(widget, clientId, eventTypeId):
                continue
            if form != '001' and not isMoving:
                eventId = None if QtGui.qApp.isDisabledEventForPersonOrSpeciality() else findSameEvent(eventTypeId, personId, clientId, eventSetDate, eventDate)
                if eventId:
                    msg = u'Новый осмотр указанного типа пересекается по времени с существующим.\nОткрыть существующий?'
                    boxResultExisting = QtGui.QMessageBox.question(widget,
                        u'Внимание!',
                        msg,
                        QtGui.QMessageBox.Yes|QtGui.QMessageBox.Cancel|QtGui.QMessageBox.Ignore,
                        QtGui.QMessageBox.Yes
                        )
                    if boxResultExisting == QtGui.QMessageBox.Cancel:
                        break
                    elif boxResultExisting == QtGui.QMessageBox.Yes and eventId:
                        destroyCounterController()
                        editEvent(widget, eventId, eventTypeId)
                        return eventId
            
            if not flagHospitalization and isStationaryEventType(eventTypeId):
                btnAction, eventId, planningActionId = checkPlanningOpenEvents(widget, clientId)
                if btnAction == 1 and eventId:
                    from HospitalBeds.HospitalizationFromQueue import CHospitalizationFromQueue
                    hospEvent = CHospitalizationFromQueue(widget)
                    data = hospEvent.getDataQueueEvent(eventId)
                    orgStructureId = data[1]
                    bedId = data[2]
                    # обновить данные
                    flagHospitalization = True
                    valueProperties = [orgStructureId, bedId]
                    relegatePersonId = data[8]
                    plannedEndDate = data[6]
                    relegateOrgId = data[10]
                    srcNumber = data[11] or forceString(QtGui.qApp.db.translate('Event', 'id', eventId, 'srcNumber'))
                    srcDate = data[12]
                    planningEventId = eventId
                    prevEventId = eventId
                    diagnos = hospEvent.getDiagnosString(eventId)
                    financeId = hospEvent.getPlanningFinanceId(eventId)
                    protocolQuoteId = hospEvent.getProtocolQuote(eventId) if form == '027' else None
                    params['valueProperties'] = valueProperties
                    params['plannedEndDate'] = plannedEndDate
                    params['relegateOrgId'] = relegateOrgId
                    if QtGui.qApp.currentOrgId() == relegateOrgId:
                        params['relegatePersonId'] = relegatePersonId
                        params['srcPerson'] = None
                    else:
                        params['relegatePersonId'] = None
                        params['srcPerson'] = forceString(QtGui.qApp.db.translate('vrbPersonWithSpeciality', 'id', relegatePersonId, 'name')) if relegatePersonId else ''
                    params['srcNumber'] = srcNumber
                    params['srcDate'] = srcDate
                    params['planningEventId'] = planningEventId
                    params['prevEventId'] = prevEventId
                    params['diagnos'] = diagnos
                    params['financeId'] = financeId
                    params['protocolQuoteId'] = protocolQuoteId
                    continue  # заново открыть диалог
            
            if not isMoving:
                btnOpenEvent, eventId = checkClientHasOpenEvents(widget, eventTypeId, clientId, eventSetDate, eventDate, personId, form)
                if eventId and btnOpenEvent == 2:
                    destroyCounterController()
                    editEvent(widget, eventId, eventTypeId)
                    return eventId
                elif btnOpenEvent == 0:
                    break
                elif btnOpenEvent == 1:
                    continue
            if form == '001' or form == '090' or isMoving:
                if QtGui.qApp.preferences.dbDatabaseName == 's11_00000':
                    canEnterEvent, priorEventId = checkEventPosibility(clientId, eventTypeId, personId, eventDate if eventDate else eventSetDate)
                else:
                    canEnterEvent = True
            else:
                canEnterEvent, priorEventId = checkEventPosibility(clientId, eventTypeId, personId, eventDate if eventDate else eventSetDate)
            if canEnterEvent:
                if (    widget.checkClientAttach(personId, clientId, eventDatetime if eventDatetime else eventSetDatetime, False)
                    and (    widget.checkClientAttendance(personId, clientId)
                          or widget.confirmClientAttendance(widget, personId, clientId)
                        )
                    and (    checkClientPolicyAttendance(eventTypeId, clientId, eventDate or eventSetDate)
                          or confirmClientPolicyAttendance(widget, eventTypeId, clientId)
                        )
                    and confirmClientPolicyConstraint(widget, eventTypeId, clientId, eventSetDate, eventDate)
                   ):
                        if transferDataList:
                            return saveTransferEvent(widget, transferDataList, clientId, eventTypeId, orgId, personId, eventDatetime, eventSetDatetime, weekProfile, days, externalId, assistantId, curatorId, flagHospitalization, actionTypeId, valueProperties, tissueTypeId, selectPreviousActions, relegateOrgId, relegatePersonId, planningEventId, diagnos, financeId, protocolQuoteId, actionByNewEvent, order)
                        else:
                            eventId = createEvent(widget, form, clientId, eventTypeId, orgId, personId, eventDatetime, eventSetDatetime, weekProfile, days, externalId, assistantId, curatorId,
                                               flagHospitalization, actionTypeId, valueProperties, tissueTypeId, selectPreviousActions, relegateOrgId, relegatePersonId, planningEventId, diagnos, financeId,
                                               protocolQuoteId, actionByNewEvent, order, actionListToNewEvent, result, prevEventId, typeQueue, docNum, relegateInfo, plannedEndDate, mapJournalInfoTransfer, voucherParams=voucherParams,
                                               planningActionId=planningActionId, emergencyInfo=emergencyInfo, mesId=mesId)
                            if flagHospitalization and eventId:
                                closePlanningAction(planningActionId, eventId)
                        return eventId
                else:
                    continue
            elif form != '090':
                msg = u'Новый осмотр указанного типа не может быть добавлен.'
                if priorEventId:
                    msg += u'\nОткрыть существующий?'
                boxResult = QtGui.QMessageBox.question(widget,
                    u'Внимание!',
                    msg,
                    QtGui.QMessageBox.Yes|QtGui.QMessageBox.No|QtGui.QMessageBox.Retry,
                    QtGui.QMessageBox.Yes
                    )
                if boxResult == QtGui.QMessageBox.Retry:
                    continue
                elif boxResult == QtGui.QMessageBox.Yes and priorEventId:
                    destroyCounterController()
                    editEvent(widget, priorEventId, eventTypeId)
                    return priorEventId
                else:
                    break
    destroyCounterController()
    return None


def destroyCounterController():
    QtGui.qApp.resetAllCounterValueIdReservation()
    QtGui.qApp.setCounterController(None)


def saveTransferEvent(widget, transferDataList, clientId, eventTypeId, orgId, personId, eventDatetime, eventSetDatetime, weekProfile, days, externalId, assistantId, curatorId, flagHospitalization, actionTypeId, valueProperties, tissueTypeId, selectPreviousActions, relegateOrgId, relegatePersonId, planningEventId, diagnos, financeId, protocolQuoteId, actionByNewEvent, order):
    recordEvent, recordDiagnosis, newAction, oldEventId = transferDataList
    eventSetDateTime = eventSetDatetime if isinstance(eventSetDatetime, QDateTime) else QDateTime(eventSetDatetime)
    eventExecDateTime = eventDatetime if isinstance(eventDatetime, QDateTime) else QDateTime(eventDatetime)
    db = QtGui.qApp.db
    tableEvent = db.table('Event')
    newEventRecord = tableEvent.newRecord()
    for i in range(0, newEventRecord.count()):
        newEventRecord.setValue(newEventRecord.fieldName(i), toVariant(recordEvent.value(recordEvent.fieldName(i))))
    newEventRecord.setValue('id', toVariant(None))
    newEventRecord.setValue('isClosed', toVariant(0))
    newEventRecord.setValue('MES_id', toVariant(None))
    newEventRecord.setValue('mesSpecification_id', toVariant(None))
    newEventRecord.setValue('client_id', toVariant(clientId))
    newEventRecord.setValue('org_id', toVariant(orgId))
    newEventRecord.setValue('execPerson_id', toVariant(personId))
    newEventRecord.setValue('prevEventDate', toVariant(newEventRecord.value('setDate')))
    newEventRecord.setValue('setDate', toVariant(eventSetDateTime))
    newEventRecord.setValue('execDate', toVariant(eventExecDateTime))
    newEventRecord.setValue('externalId', toVariant(externalId))
    newEventRecord.setValue('assistant_id', toVariant(assistantId))
    newEventRecord.setValue('curator_id', toVariant(curatorId))
    newEventRecord.setValue('order', toVariant(order))
    newEventRecord.setValue('relegateOrg_id', toVariant(relegateOrgId))
    newEventRecord.setValue('relegatePerson_id', toVariant(relegatePersonId))
    newEventRecord.setValue('result_id', toVariant(None))
    newEventRecord.setValue('prevEvent_id', toVariant(oldEventId))

    eventId = saveTransferData(widget,'Event', newEventRecord)
    if eventId:
        newActionRecord = newAction._record
        newActionRecord.setValue('event_id', toVariant(eventId))
        newActionRecord.setValue('idx', toVariant(9999))
        newAction.save(eventId, -1)
    return eventId


def saveTransferData(widget, tableName, record):
    try:
        db = QtGui.qApp.db
        db.transaction()
        try:
            id = db.insertOrUpdate(db.table(tableName), record)
            db.commit()
        except:
            db.rollback()
            raise
        return id
    except Exception, e:
        QtGui.qApp.logCurrentException()
        QtGui.QMessageBox.critical( widget,
                                    u'',
                                    exceptionToUnicode(e),
                                    QtGui.QMessageBox.Close)
        return None


def confirmTrouble(widget, message):
    boxResult = QtGui.QMessageBox.question(widget,
                                    u'Внимание!',
                                    message,
                                    QtGui.QMessageBox.Ok,
                                    QtGui.QMessageBox.Ok)
    if boxResult == QtGui.QMessageBox.Ok:
        return False


def checkEventTypeAge(widget, clientId, eventTypeId, eventSetDate):
    if clientId:
        db = QtGui.qApp.db
        birthDate = forceDate(db.translate('Client', 'id', clientId, 'birthDate'))
        if birthDate:
            ageSelector = getEventAgeSelector(eventTypeId)
            if not eventSetDate:
                eventSetDate = QDate.currentDate()
            return checkAgeSelector(ageSelector, calcAgeTuple(birthDate, eventSetDate))
    return False


def checkSocStatus(widget, clientId, eventSetDate):
    isCheckSocStatus, socStatusRes = QtGui.qApp.getStrictCheckSocStatus()
    socStatusNames = u''
    if isCheckSocStatus:
        db = QtGui.qApp.db
        if socStatusRes:
            tableSSC = db.table('rbSocStatusClass')
            records = db.getRecordList(tableSSC, tableSSC['name'], [tableSSC['id'].inlist(socStatusRes)])
            for record in records:
                if socStatusNames:
                    socStatusNames += u', '
                socStatusNames += forceString(record.value('name'))
        if clientId:
#            socStatusClassIdList = []
            table = db.table('ClientSocStatus')
            cond = [table['deleted'].eq(0),
                    table['client_id'].eq(clientId),
                    ]
            if eventSetDate:
                cond.append(db.joinOr([table['endDate'].isNull(), table['endDate'].dateGe(eventSetDate)]))
                cond.append(db.joinOr([table['begDate'].isNull(), table['begDate'].dateLe(eventSetDate)]))
            records = db.getRecordList(table, table['socStatusClass_id'], cond)
            for record in records:
                socStatusClassId = forceRef(record.value('socStatusClass_id'))
                if socStatusClassId in socStatusRes:
                    return True, isCheckSocStatus, socStatusNames
    return False, isCheckSocStatus, socStatusNames


def checkWorkHurts(widget, clientId, eventTypeId):
    db = QtGui.qApp.db
    tableEventTypeDiagnostic = db.table('EventType_Diagnostic')
    cond = [tableEventTypeDiagnostic['eventType_id'].eq(eventTypeId),
            db.joinOr([tableEventTypeDiagnostic['hurtType'].ne(''), tableEventTypeDiagnostic['hurtFactorType'].ne('')])]
    if not db.getRecordEx(tableEventTypeDiagnostic, tableEventTypeDiagnostic['id'].name(), cond):
        return True

    clientWorkRecord = getClientWork(clientId)
    if clientWorkRecord:
        tableClientWorkHurt = db.table('ClientWork_Hurt')
        cond = [tableClientWorkHurt['master_id'].eq(forceRef(clientWorkRecord.value('id')))]
        if db.getRecordEx(tableClientWorkHurt, tableClientWorkHurt['id'].name(), cond):
            return True

    QtGui.QMessageBox.information(widget,
                            u'Внимание!',
                            u'У пациента отсутствуют записи о вредности работы.',
                            QtGui.QMessageBox.Ok,
                            QtGui.QMessageBox.Ok)

    return False

def checkClientCanHaveEvent(widget, clientId):
    eventControl = QtGui.qApp.getGlobalPreference('20')  # WTF!!!!
    if eventControl in (u'мягкий', u'строгий'):
        identifiers = getClientIdentifications(clientId)
        if u'Согласие на обследование' in identifiers and identifiers[u'Согласие на обследование'][0] == u'Да':
            lastDate = identifiers[u'Согласие на обследование'][1].addYears(1)
            if lastDate.daysTo(QDate.currentDate()) >= 0:
                if eventControl == u'строгий':
                    QtGui.QMessageBox.critical(widget,
                                        u'Ошибка',
                                        u'Согласие на обследование пациента просрочено',
                                        QtGui.QMessageBox.Ok,
                                        QtGui.QMessageBox.Ok)
                    return False
                else:
                    append = QtGui.QMessageBox.question(widget,
                        u'Внимание!',
                        u'Согласие на обследование пациента просрочено. Все равно добавить событие?',
                        QtGui.QMessageBox.Yes|QtGui.QMessageBox.No,
                        QtGui.QMessageBox.No)
                    return (append == QtGui.QMessageBox.Yes)
            else:
                return True
        else:
            if eventControl == u'строгий':
                QtGui.QMessageBox.critical(widget,
                                        u'Ошибка',
                                        u'У пациента нет согласия на обследование',
                                        QtGui.QMessageBox.Ok,
                                        QtGui.QMessageBox.Ok)
                return False
            else:
                append = QtGui.QMessageBox.question(widget,
                        u'Внимание!',
                        u'У пациента нет согласия на обследование. Все равно добавить событие?',
                        QtGui.QMessageBox.Yes|QtGui.QMessageBox.No,
                        QtGui.QMessageBox.No)
                return append == QtGui.QMessageBox.Yes
    else:
        return True


def checkDatesRegardToClientLife(widget, clientId, eventSetDate, eventDate, eventTypeId):
    result = True
    if clientId:
        db = QtGui.qApp.db
        birthDate   = forceDate(db.translate('Client', 'id', clientId, 'birthDate'))
        deathDate   = getDeathDate(clientId)
        possibleDeathDate = birthDate.addYears(QtGui.qApp.maxLifeDuration)
        if birthDate:
            postmortem = isEventDeath(eventTypeId)
            if eventSetDate:
                result = result and (eventSetDate >= birthDate or confirmTrouble(widget, u'Дата назначения %s не должна быть раньше даты рождения пациента %s' % (forceString(eventSetDate), forceString(birthDate))))
                if deathDate:
                    result = result and (eventSetDate <= deathDate or postmortem or confirmTrouble(widget, u'Дата назначения %s не должна быть позже имеющейся даты смерти пациента %s' % (forceString(eventSetDate), forceString(deathDate))))
                else:
                    result = result and (eventSetDate <= possibleDeathDate or postmortem or confirmTrouble(widget, u'Дата назначения %s не должна быть позже возможной даты смерти пациента %s' % (forceString(eventSetDate), forceString(possibleDeathDate))))

            if eventDate:
                result = result and (eventDate >= birthDate or confirmTrouble(widget, u'Дата выполнения (окончания) %s не должна быть раньше даты рождения пациента %s' % (forceString(eventDate), forceString(birthDate))))
                if deathDate:
                    result = result and (eventDate <= deathDate or postmortem or confirmTrouble(widget, u'Дата выполнения (окончания) %s не должна быть позже имеющейся даты смерти пациента %s' % (forceString(eventDate), forceString(deathDate))))
                else:
                    result = result and (eventDate <= possibleDeathDate or postmortem or confirmTrouble(widget, u'Дата выполнения (окончания) %s не должна быть позже возможной даты смерти пациента %s' % (forceString(eventDate), forceString(possibleDeathDate))))
    return result


def findCreateEventToDate(eventTypeId, personId, clientId, eventSetDate, eventDate):
    if clientId and eventTypeId and personId and (eventSetDate or eventDate):
        db = QtGui.qApp.db
        tableEvent  = db.table('Event')
        tableEventType = db.table('EventType')
        queryTable = tableEvent.leftJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
        cols = [tableEvent['id']]
        cond = [tableEvent['client_id'].eq(clientId),
                tableEvent['eventType_id'].eq(eventTypeId),
                tableEvent['deleted'].eq(0),
                tableEventType['form'].ne('001'),
                "NOT exists(SELECT NULL FROM EventType_Identification eti left JOIN rbAccountingSystem `as` ON `as`.id = eti.system_id WHERE eti.master_id = EventType.id AND `as`.code = 'AccTFOMS')"
                ]
        if QtGui.qApp.isCheckedEventForPersonOrSpeciality():
            cond.append(tableEvent['execPerson_id'].eq(personId))
        else:
            if personId:
                db = QtGui.qApp.db
                tablePerson = db.table('Person')
                record = db.getRecordEx(tablePerson, [tablePerson['speciality_id']], [tablePerson['deleted'].eq(0), tablePerson['id'].eq(personId)])
                specialityId = forceRef(record.value('speciality_id')) if record else None
                if specialityId:
                    queryTable = queryTable.innerJoin(tablePerson, tableEvent['execPerson_id'].eq(tablePerson['id']))
                    cond.append(tablePerson['speciality_id'].eq(specialityId))
                    cond.append(tablePerson['deleted'].eq(0))
        eventShowTime = getEventShowTime(eventTypeId)
        if eventSetDate:
            eventSetDateTime = db.formatDate(eventSetDate)
        else:
            eventSetDateTime = None
        if eventDate:
            eventDateTime = db.formatDate(eventDate)
        else:
            eventDateTime = None
        if eventSetDateTime:
            if eventShowTime:
                cond.append(u'''Event.setDate = %s''' % (eventSetDateTime))
            else:
                cond.append(u'''DATE(Event.setDate) = %s''' % (eventSetDateTime))
        elif eventDateTime:
            if eventShowTime:
                cond.append(u'''Event.execDate = %s''' % (eventDateTime))
            else:
                cond.append(u'''DATE(Event.execDate) = %s''' % (eventDateTime))
        recordList = db.getRecordList(queryTable, cols, cond, 'Event.setDate')
        if recordList:
            record = recordList[0]
            eventId = forceRef(record.value('id'))
            return eventId
    return None


def findSameEvent(eventTypeId, personId, clientId, eventSetDate, eventDate):
    if clientId and eventTypeId and personId and (eventSetDate or eventDate):
        db = QtGui.qApp.db
        tableEvent  = db.table('Event')
        cols = [tableEvent['id']]
        cond = [tableEvent['client_id'].eq(clientId),
                tableEvent['eventType_id'].eq(eventTypeId),
                tableEvent['deleted'].eq(0)
                ]
        queryTable = tableEvent
        if QtGui.qApp.isCheckedEventForPersonOrSpeciality():
            cond.append(tableEvent['execPerson_id'].eq(personId))
        else:
            if personId:
                db = QtGui.qApp.db
                tablePerson = db.table('Person')
                record = db.getRecordEx(tablePerson, [tablePerson['speciality_id']], [tablePerson['deleted'].eq(0), tablePerson['id'].eq(personId)])
                specialityId = forceRef(record.value('speciality_id')) if record else None
                if specialityId:
                    queryTable = queryTable.innerJoin(tablePerson, tableEvent['execPerson_id'].eq(tablePerson['id']))
                    cond.append(tablePerson['speciality_id'].eq(specialityId))
                    cond.append(tablePerson['deleted'].eq(0))
        if eventSetDate:
            eventSetDateTime = db.formatDate(eventSetDate)
        else:
            eventSetDateTime = None
        if eventDate:
            eventDateTime = db.formatDate(eventDate)
        else:
            eventDateTime = None
        if eventSetDateTime and eventDateTime:
            cond.append(u''' (DATE(Event.execDate) IS NOT NULL
            AND ((DATE(Event.setDate) <= %s AND DATE(Event.execDate) >= %s) OR (DATE(Event.setDate) >= %s
            AND DATE(Event.execDate) <= %s) OR (DATE(Event.setDate) >= %s AND (DATE(Event.setDate) <= %s)
            OR (DATE(Event.setDate) <= %s AND (DATE(Event.execDate) <= %s AND DATE(Event.execDate) >= %s))))
            OR (DATE(Event.execDate) IS NULL AND (DATE(Event.setDate) = %s OR DATE(Event.setDate) = %s
            OR (%s <= DATE(Event.setDate) AND DATE(Event.setDate) <= %s))))
            ''' % (eventSetDateTime, eventDateTime, eventSetDateTime, eventDateTime,
                   eventSetDateTime, eventDateTime, eventSetDateTime, eventDateTime,
                   eventSetDateTime, eventSetDateTime, eventDateTime, eventSetDateTime, eventDateTime))
        elif eventSetDateTime:
            cond.append(u''' ((DATE(Event.execDate) IS NULL AND DATE(Event.setDate) = %s)
            OR (DATE(Event.execDate) IS NOT NULL AND (DATE(Event.setDate) <= %s AND DATE(Event.execDate) >= %s)))
            ''' % (eventSetDateTime, eventSetDateTime, eventSetDateTime))
        elif eventDateTime:
            cond.append(u''' ((DATE(Event.execDate) IS NULL AND DATE(Event.setDate) = %s)
            OR (DATE(Event.execDate) IS NOT NULL AND (DATE(Event.setDate) <= %s AND DATE(Event.execDate) >= %s)))
            ''' % (eventDateTime, eventDateTime, eventDateTime))
        recordList = db.getRecordList(queryTable, cols, cond, 'Event.setDate')
        if recordList:
            record = recordList[0]
            eventId = forceRef(record.value('id'))
            return eventId
    return None


def checkClientHasOpenEvents(widget, eventTypeId, clientId, eventSetDate, eventDate, personId, form):
    result = (3, None)
    if clientId and eventTypeId and (eventSetDate or eventDate):
        db = QtGui.qApp.db
        tableEvent  = db.table('Event')
        tableEventType = db.table('EventType')
        table = tableEvent.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
        cols = [tableEvent['id']]
        cond = [tableEvent['client_id'].eq(clientId),
                tableEvent['deleted'].eq(0),
                tableEventType['deleted'].eq(0),
                tableEventType['purpose_id'].gt(1),
                tableEvent['execDate'].isNull(),
                tableEventType['context'].notlike(u'relatedAction%'),
                tableEventType['context'].notlike(u'inspection%')
                ]
#        if eventSetDate and eventDate:
#            cond.append(tableEvent['setDate'].le(max(eventSetDate, eventDate)))
#        elif eventSetDate:
#            cond.append(tableEvent['setDate'].le(eventSetDate))
#        elif eventDate:
#            cond.append(tableEvent['setDate'].le(eventDate))
        recordList = db.getIdList(table, cols, cond, 'Event.setDate')
        if recordList:
            dialog = CCheckEnteredOpenEvents(widget, recordList, clientId, eventDate or eventSetDate)
            try:
                dialog.exec_()
                result = (dialog.btnResult, dialog.resultEventId)
            finally:
                dialog.deleteLater()
    return result


def checkClientPolicyAttendance(eventTypeId, clientId, date):
    if QtGui.qApp.isStrictPolicyCheckOnEventCreation() != 2:
        financeCode = getEventFinanceCode(eventTypeId)
        if financeCode == CFinanceType.CMI:
            return bool(getClientCompulsoryPolicy(clientId, date))
        elif financeCode == CFinanceType.VMI:
            return bool(getClientVoluntaryPolicy(clientId, date))
    return True


def confirmClientPolicyAttendance(widget, eventTypeId, clientId):
    if QtGui.qApp.isStrictPolicyCheckOnEventCreation() != 2:
        if QtGui.qApp.isStrictPolicyCheckOnEventCreation(): # строгий контроль
            message = u'Пациент не имеет полиса, требуемого для данного типа обращения.\nРегистрация обращения запрещена.'
            QtGui.QMessageBox.critical(widget, u'Внимание!', message, QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
            return False
        else:
            message = u'Пациент не имеет полиса, требуемого для данного типа обращения.\nЭто может привести к затруднениям оплаты обращения.\nВсё равно продолжить?'
            return QtGui.QMessageBox.critical(widget,
                                        u'Внимание!',
                                        message,
                                        QtGui.QMessageBox.Yes|QtGui.QMessageBox.No,
                                        QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes
    return True


def confirmClientPolicyConstraint(widget, eventTypeId, clientId, eventSetDate, eventDate):
    if QtGui.qApp.isStrictPolicyCheckOnEventCreation() != 2:
        today = QDate.currentDate()
        fixedEventDate = eventDate or today
        fixedEventSetDate = eventSetDate or fixedEventDate
        policyDate = fixedEventSetDate
        serviceName = ''
        serviceStopFieldName = ''
        financeCode = getEventFinanceCode(eventTypeId)
        recordPolicy = None
        if financeCode == 2:
            recordPolicy = getClientCompulsoryPolicy(clientId, policyDate)
            serviceName = u'ОМС'
            serviceStopFieldName = 'compulsoryServiceStop' # wtf
        elif financeCode == 3:
            recordPolicy = getClientVoluntaryPolicy(clientId, policyDate)
            serviceName = u'ДМС'
            serviceStopFieldName = 'voluntaryServiceStop' # wtf
        serviceStopped = False
        if recordPolicy:
            policyBegDate = forceDate(recordPolicy.value('begDate'))
            policyEndDate = forceDate(recordPolicy.value('endDate'))
            validPolicy = not policyBegDate or policyBegDate <= fixedEventSetDate
            validPolicy = validPolicy and (not policyEndDate or policyEndDate >= fixedEventDate)
            if not validPolicy:
                if not confirmPolicyAvailable(widget, u'Полис пациента не действителен по дате!'):
                    return False
            serviceStopped = forceBool(recordPolicy.value(serviceStopFieldName)) # wtf
        if serviceStopped:
            if QtGui.qApp.checkGlobalPreference('4', u'да'): # строгий контроль
                message = u'По данной СМО приостановлено обслуживание %s полисов.\nРегистрация обращения запрещена.' % serviceName
                QtGui.QMessageBox.critical(widget, u'Внимание!', message, QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
                return False
            else:
                message = u'По данной СМО приостановлено обслуживание %s полисов.\nЭто может привести к затруднениям оплаты обращения.\nВсё равно продолжить?' % serviceName
                return QtGui.QMessageBox.critical(widget,
                                        u'Внимание!',
                                        message,
                                        QtGui.QMessageBox.Yes|QtGui.QMessageBox.No,
                                        QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes
    return True


def confirmPolicyAvailable(widget, message):
    if QtGui.qApp.checkGlobalPreference('4', u'да'): # строгий контроль
        default = buttons = QtGui.QMessageBox.Ok
        messageBox = QtGui.QMessageBox.critical
    else:
        buttons = QtGui.QMessageBox.Yes | QtGui.QMessageBox.No
        default = QtGui.QMessageBox.Yes
        message = '\n'.join([message, u'Все равно продолжить?'])
        messageBox = QtGui.QMessageBox.question
    result = messageBox(widget,
                        u'Внимание!',
                        message,
                        buttons,
                        default) == QtGui.QMessageBox.Yes
    return result


def printCostSprDialog(widget):
    if QtGui.qApp.defaultKLADR()[:2] != u'23':
        return
    buttons = QtGui.QMessageBox.Yes | QtGui.QMessageBox.No
    default = QtGui.QMessageBox.Yes
    message = u'Распечатать справку о стоимости?'
    messageBox = QtGui.QMessageBox.question
    result = messageBox(widget,
                        u'Внимание!',
                        message,
                        buttons,
                        default) == QtGui.QMessageBox.Yes
    if not result:
        return
    templateId = forceRef(QtGui.qApp.db.translate('rbPrintTemplate', 'code', '100','id'))
    context = forceString(QtGui.qApp.db.translate('rbPrintTemplate', 'id', templateId, 'context'))
    data = None
    if context == u'tempInvalid':
        return
    else:
        data = getEventContextData(widget)
        #{'client': <Registry.Utils.CClientInfo object at 0x0AF01DB0>, 'tempInvalid': <Events.TempInvalidInfo.CTempInvalidInfo object at 0x0AF019F0>, 'event': <Events.EventInfo.CEmergencyEventInfo object at 0x0ACDEDD0>}
    QtGui.qApp.call(widget, applyTemplate, (widget, templateId, data))

def createEvent(widget, form, clientId, eventTypeId, orgId, personId, eventDate, eventSetDate, weekProfile, numDays, externalId, assistantId, curatorId, flagHospitalization=False, actionTypeId=None,
                valueProperties=None, tissueTypeId=None, selectPreviousActions=False, relegateOrgId=None, relegatePersonId=None, planningEventId=None, diagnos=None, financeId=None, protocolQuoteId=None,
                actionByNewEvent=[], order=1, actionListToNewEvent=[], result=None, prevEventId=None, typeQueue=-1, docNum=None, relegateInfo=[], plannedEndDate=None, mapJournalInfoTransfer=[], voucherParams={},
                planningActionId=None, emergencyInfo=None, mesId=None):
    formClass = getEventFormClassByType(eventTypeId)
    dialog = formClass(widget)
    QtGui.qApp.setJTR(dialog) # fucked shit!
    try:
#        QtGui.qApp.setCounterController(CCounterController(dialog))
        if emergencyInfo:
            dialog.emergencyInfo = emergencyInfo
        if dialog.prepare(clientId, eventTypeId, orgId, personId, eventSetDate, eventDate, weekProfile, numDays, externalId, assistantId,
                          curatorId, flagHospitalization, actionTypeId, valueProperties, tissueTypeId, selectPreviousActions,
                          relegateOrgId, relegatePersonId, diagnos, financeId, protocolQuoteId, actionByNewEvent, order, actionListToNewEvent, typeQueue, docNum,
                          relegateInfo, plannedEndDate, mapJournalInfoTransfer, voucherParams=voucherParams):
            dialog.initPrevEventId(prevEventId)
            if not dialog.initPrevEventTypeId(eventTypeId, clientId):
                return None
            dialog.addActions(actionListToNewEvent)
            if result:
                dialog.setCmbResult(result)
            if hasattr(dialog, 'getEventDataPlanning'):
                dialog.getEventDataPlanning(planningEventId)
            if planningActionId:
                dialog.planningActionId = planningActionId
            if mesId:
                if hasattr(dialog, 'tabMes') and hasattr(dialog.tabMes, 'cmbMes'):
                    dialog.tabMes.cmbMes.setValue(mesId)
                    dialog.autoInsertingActionByMES()
            if form == u'090':
                resultF090, eventF090Id, actionF090Id = createF090(dialog, dialog.getRecord())
                if resultF090:
                    updateEventListAfterEdit(eventF090Id)
                    return eventF090Id
            elif dialog.exec_():
                updateEventListAfterEdit(dialog.itemId())
                # вставка обращений
                if QtGui.qApp.checkGlobalPreference(u'23:obr', u'да'):
                    QtGui.qApp.db.query('CALL InsertObr(%d);' % dialog.itemId())
                if dialog.tabNotes.isEventClosed() and QtGui.qApp.checkGlobalPreference(u'23:printCostSpr', u'да'):
                    printCostSprDialog(dialog)
                # изменение типа приема терапевта для диспансеризации
                if hasattr(dialog, 'changeExaminServiceCode'):
                    (id026, id047) = dialog.changeExaminServiceCode
                    sql = '''
                        update Action
                    left join ActionType on ActionType.id = Action.actionType_id
                    left join rbService on rbService.id = ActionType.nomenclativeService_id 
                    set Action.actionType_id = (case when rbService.infis regexp 'B04.026.001.0(01|02|05|06|09|10|17|18|21|22|25|26|37|38|39|40|41|42|53|55|56|59|62|63|65|66|67|68|69|70|71|72|73|74|75|76|77|78|79|80|71|72|83|86|87|88)' 
                                                     or rbService.infis regexp 'B04.026.002.0(13|14|15|16|17|18|19|20|21|22)' then %d
                                                     when rbService.infis regexp 'B04.047.001.0(01|02|05|06|09|10|17|18|21|22|25|26|37|38|39|40|41|42|54|56|57|60|63|64|66|67|68|69|70|71|72|73|74|75|76|77|78|79|80|71|72|83|84|85|86|87)'
                                                     or rbService.infis regexp 'B04.047.002.0(13|14|15|16|17|18|19|20|21|22)' then %d
                                                     else Action.actionType_id end)
                    where Action.event_id = %d           '''
                    QtGui.qApp.db.query(sql % (forceInt(id026), forceInt(id047),  dialog.itemId()))             

                return dialog.itemId()
        return dialog.itemId() if dialog.itemId() else None
    finally:
        QtGui.qApp.unsetJTR(dialog) # fuck it again!
        QtGui.qApp.resetAllCounterValueIdReservation()
        dialog.deleteLater()


def editEvent(widget, eventId, eventTypeId=None, readOnly=False):
    if not eventTypeId:
        eventTypeId = forceRef(QtGui.qApp.db.translate('Event', 'id', eventId, 'eventType_id'))
    form = getEventTypeForm(eventTypeId) if eventTypeId else u''
    if form == u'090':
        actionId = getF090ActionIdToEventId(eventId)
        if not actionId:
            return None
        dialog = CF090EditDialog(widget)
        try:
            dialog.load(actionId)
            dialog.protectWidgetFromEdit(False)
            dialog.exec_()
            if dialog.isBtnSave:
                actionId = dialog.itemId()
                updateEventListAfterEdit(eventId)
                return actionId
            return None
        finally:
            dialog.destroy()
            dialog.setParent(None)
    else:
        formClass = getEventFormClass(eventId)
        if formClass == CF088EditDialog:
            db = QtGui.qApp.db
            tableAction = db.table('Action')
            recordAction = db.getRecordEx(tableAction, [tableAction['createDatetime'], tableAction['id']],
                                          [tableAction['event_id'].eq(eventId), tableAction['deleted'].eq(0)])
            createDate = forceDate(recordAction.value('createDatetime')) if recordAction else None
            actionId = forceRef(recordAction.value('id')) if recordAction else None
            if createDate and createDate >= QDate(2022, 1, 1):
                dialog = CF0882022EditDialog(widget)
            else:
                dialog = CF088EditDialog(widget)
            dialog.load(actionId)
        else:
            dialog = formClass(widget)
            dialog.load(eventId)

        if readOnly:
            dialog.setReadOnly(readOnly)
        res = None
        try:
            if dialog.exec_():
                res = dialog.itemId()
                updateEventListAfterEdit(eventId)
                # вставка обращений
                if QtGui.qApp.checkGlobalPreference(u'23:obr', u'да'):
                    QtGui.qApp.db.query('CALL InsertObr(%d);' % dialog.itemId())
                if dialog.tabNotes.isEventClosed() and QtGui.qApp.checkGlobalPreference(u'23:printCostSpr', u'да'):
                    printCostSprDialog(widget)
                # изменение типа приема терапевта для диспансеризации
                if hasattr(dialog, 'changeExaminServiceCode'):
                    (id026, id047) = dialog.changeExaminServiceCode
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
                    QtGui.qApp.db.query(sql % (forceInt(id026), forceInt(id047),  dialog.itemId()))
        finally:
            dialog.destroy()
            dialog.setParent(None)
        return res


def updateEventListAfterEdit(eventId):
    if QtGui.qApp.mainWindow.registry:
        QtGui.qApp.mainWindow.registry.updateEventListAfterEdit(eventId)


def isStationaryEventType(eventTypeId):
    description = CEventTypeDescription.get(eventTypeId)
    return description.isStationary or description.isDayStationary


def checkPlanningOpenEvents(parent, clientId):
    from HospitalBeds.HospitalizationEventDialog import CCheckPlanningOpenEvents
    result = (2, None, None)
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
                tableActionType['deleted'].eq(0),
                tableEvent['deleted'].eq(0),
                tableActionType['id'].inlist(actionTypeIdList)
                ]
        
        cond.append(tableAction['status'].notInlist([CActionStatus.finished, CActionStatus.canceled, CActionStatus.refused]))
            
        actionIdList = db.getIdList(table, cols, cond, 'Action.begDate')
        if actionIdList:
            dialog = CCheckPlanningOpenEvents(parent, actionIdList, clientId, isVisible=False)
            dialog.setWindowTitleEx(u'Список открытых планирований на пациента')
            try:
                dialog.exec_()
                actionId = dialog.resultActionId
                eventId = None
                if actionId:
                    eventId = forceRef(db.translate('Action', 'id', actionId, 'event_id'))
                result = (dialog.btnResult, eventId, actionId)
            finally:
                dialog.deleteLater()
    return result

def closePlanningAction(actionId, eventId):
    if not actionId:
        return
    db = QtGui.qApp.db
    tableAction = db.table('Action')
    setDate = forceDateTime(db.translate('Event', 'id', eventId, 'setDate'))
    updateCond = [
        tableAction['id'].eq(actionId),
        tableAction['deleted'].eq(0),
    ]
    updateCols = [
        tableAction['endDate'].eq(setDate),
        tableAction['status'].eq(2),
    ]
    db.updateRecords(tableAction, updateCols, updateCond)


# проверка при создании нового события: была ли у данного пациента услуга
# от врача такой специальности в данном месяце
def checkFirstEvent(clientID, personId, setDate, endDate, eventTypeId):
    db = QtGui.qApp.db
    smt1 = u''' select EventType.code as codeEvent
                from EventType
                where EventType.id = %s ''' % eventTypeId
    query = db.query(smt1)
    eventTypeCode = 0
    while query.next():
        record = query.record()
        if record:
            eventTypeCode = forceInt(record.value('codeEvent'))

    if eventTypeCode not in (11, 12, 301, 302, 401, 402, 41, 42, 51, 52,
                             71, 72, 60, 111, 112, 241, 242, 262, 211, 261):
        dateMonthEnd = 0
        dateMonthSet = 0
        dateYearEnd = 0
        dateYearSet = 0
        dateMonth = 0
        dateYear = 0
        if endDate is not None:
            dateMonthEnd = endDate.month()
            dateYearEnd = endDate.year()
        if setDate is not None:
            dateMonthSet = setDate.month()
            dateYearSet = setDate.year()
        if dateMonthEnd >= dateMonthSet and dateYearEnd >= dateYearSet:
            dateMonth = dateMonthEnd
            dateYear = dateYearEnd
        if dateMonthEnd < dateMonthSet and dateYearEnd < dateYearSet:
            dateMonth = dateMonthSet
            dateYear = dateYearSet


        smt1 = u''' SELECT Person.speciality_id AS specid
                    FROM Person
                    WHERE Person.id = %s ''' % personId
        query = db.query(smt1)
        spec_id = 0
        while query.next():
            record = query.record()
            if record:
                spec_id = forceInt(record.value('specid'))

        smt = u''' SELECT COUNT(*) as id
                    FROM Event
                    LEFT JOIN Person ON Person.id = Event.execPerson_id
                    WHERE	
                            case
                            when Event.execDate is not NULL then
                                MONTH(Event.execDate) = %s and
                                YEAR(Event.execDate) = %s 
                            when Event.setDate is not NULL then
                                month(Event.setDate) = %s and
                                Year(Event.setDate) = %s 
                            end 
                            and Event.client_id = %s AND Person.speciality_id = %s and Event.deleted=0''' % (dateMonth, dateYear, dateMonth, dateYear, clientID, spec_id)
        query = db.query(smt)
        checkFlag = 0
        while query.next():
            record = query.record()
            if record:
                checkFlag = forceInt(record.value('id'))
        if checkFlag != 0:
            return False
    return True
