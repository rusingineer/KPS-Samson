# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2012-2024 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtCore, QtGui
from Events.Action import CAction
from Events.ActionStatus import CActionStatus
from Orgs.Utils import getOrgStructureDescendants
from Stock.Service import CStockService
from library.DialogBase import CDialogBase
from library.Utils import forceDate, forceInt, forceRef, forceString, forceBool, firstMonthDay, formatName

__all__ = ('CHospitalBedInvoicesByEventsDialog',)


class CHospitalBedInvoicesByEventsDialog(CDialogBase):
    def __init__(self, parent):
        super(CHospitalBedInvoicesByEventsDialog, self).__init__(parent)
        self.setObjectName('CHospitalBedInvoicesByEventsDialog')
        self._eventIdList = []
        self._setupUi()

    def _setupUi(self):
        # размер по умолчанию, должен быть изменен после загрузки настроек из ini
        self.resize(800, 600)
        self.setWindowTitle(u'Списание ЛС по случаю обслуживания')
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowMinMaxButtonsHint)
        self.log = QtGui.QTextEdit()
        self.log.setReadOnly(True)
        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close)
        self.buttonBox.clicked.connect(self.accept)
        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(self.log)
        layout.addWidget(self.buttonBox)

    def setEventIdList(self, eventIdList):
        self._eventIdList = eventIdList

    def showEvent(self, event):
        QtCore.QTimer.singleShot(200, self._doInvoices)
        return super(CHospitalBedInvoicesByEventsDialog, self).showEvent(event)

    def _writeLog(self, msg):
        self.log.append(msg)

    def _writeEventLogInfo(self, eventId):
        db = QtGui.qApp.db
        event = db.getRecord('Event', 'client_id, externalId', eventId)
        client = db.getRecord('Client',
                              'lastName, firstName, patrName',
                              event.value('client_id'))
        externalId = forceString(event.value('externalId'))
        name = formatName(client.value('lastName'),
                          client.value('firstName'),
                          client.value('patrName'))

        message = u''
        if self.log.textCursor().position() > 0:
            # Нужно добавлять разделитель только если в логе уже что-то есть.
            message += u'<hr>'
        message += u'<b>Поиск медикаментозных назначений пациента ' + name
        if externalId:
            message += u' (Карта № %s)' % externalId
        message += '</b>'
        self._writeLog(message)

    def _doInvoices(self):
        processedActionIdList = [] # type: list[int]
        logs = {} # type: dict[datetime.date, list[str]]
        orgStructureId = QtGui.qApp.currentOrgStructureId()
        db = QtGui.qApp.db
        db.transaction()
        try:
            for eventId in self._eventIdList:
                logs.clear()
                self._writeEventLogInfo(eventId)
                recordList, groupingItems = _findActionsForInvoice(eventId, orgStructureId, processedActionIdList)
                if len(recordList) == 0:
                    self._writeLog(u'Отсутствуют назначения, подлежащие выполнению.')
                while len(recordList) > 0:
                    for record in recordList:
                        actionId = forceRef(record.value('actionId'))
                        clientId = forceRef(record.value('client_id'))
                        begDate = forceDate(record.value('begDate'))
                        isNomenclatureExpense = forceBool(record.value('isNomenclatureExpense'))
                        action = CAction.getActionById(actionId)
                        groupingRecords = groupingItems[forceInt(record.value('group_id'))] if forceInt(record.value('group_id')) in groupingItems.keys() else [(record, action)]

                        message = ''
                        for subrecord, subaction in groupingRecords:
                            groupActionId = forceRef(subrecord.value('actionId'))
                            nomenclatureName = _getNomenclatureName(groupActionId)
                            if nomenclatureName:
                                message += u'<i>%s</i>, ' % nomenclatureName
                        message += u':'
                        if not isNomenclatureExpense:
                            # таким действиям не предполагается выполнение списания,
                            # поэтому завершаем текущее действие и создаем следующее
                            if action.getDuration() < 1:
                                action.setDuration(1)
                            nextAction = action.finishAction(clientId, begDate)
                            action.save(idx=-1)
                            if nextAction is not None:
                                idx = nextAction.countIdx(eventId)
                                nextAction.save(eventId=eventId, idx=idx)
                            message += u'успешно.'
                        else:
                            ok, errorMsg = CStockService.doClientInvoice(action, record, orgStructureId, begDate, clientId, groupingRecords=groupingRecords, dialog=self)
                            if ok:
                                message += u'успешно, создан документ списания.'
                            else:
                                errorMsg = errorMsg.replace('<br>', '')
                                # первый символ в нижний регистр, чтобы сочеталось с предыдущим текстом
                                errorMsg = errorMsg[:1].lower() + errorMsg[1:]
                                message += u'<span style="color: red;">%s</span>' % errorMsg
                        logs.setdefault(begDate.toPyDate(), []).append(message)
                        processedActionIdList.append(actionId)
                    recordList, groupingItems = _findActionsForInvoice(eventId, orgStructureId, processedActionIdList)
                for date in sorted(logs.keys()):
                    self._writeLog(
                        u'Выполняется списание по назначениям на дату <b>%s</b>:'
                        % date.strftime('%d.%m.%Y'))
                    for message in logs[date]:
                        self._writeLog(message)
        except:
            db.rollback()
            QtGui.qApp.logCurrentException()
            self._writeLog(u'<h1 style="color: red;">Непредвиденная ошибка!</h1>')
        else:
            db.commit()

def _getNomenclatureName(actionId):
    query = QtGui.qApp.db.query('''
        SELECT rbNomenclature.name
        FROM ActionProperty AP
        JOIN ActionProperty_rbNomenclature APN ON AP.id = APN.id
        JOIN rbNomenclature ON APN.value = rbNomenclature.id
        WHERE AP.deleted = 0 AND AP.action_id = %d
        LIMIT 1
    ''' % actionId)
    if query.next():
        return forceString(query.value(0))
    return ''

# Нужно выполнить списание для всех Элементов плана, но действие для списания
# есть только у одного текущего Элемента плана, и при его выполнении создается
# новое действие следующему элементу. Поэтому нужно каждый раз находить вновь
# созданные действия под списание.
def _findActionsForInvoice(eventId, orgStructureId, excludeActionIdList=[]):
    # type: (int, int, list[int]) -> list[QSqlRecord]
    db = QtGui.qApp.db
    tableAction = db.table('Action')
    tableActionType = db.table('ActionType')
    tableEvent = db.table('Event')
    tableActionEPI = db.table('ActionExecutionPlan_Item')
    queryTable = tableAction \
        .join(tableActionType, tableAction['actionType_id'].eq(tableActionType['id'])) \
        .join(tableEvent, tableAction['event_id'].eq(tableEvent['id'])) \
        .leftJoin(tableActionEPI, tableAction['id'].eq(tableActionEPI['action_id']))

    leavedEndDateStmt = '(SELECT MIN(A.endDate) FROM vActionLeaved A WHERE A.event_id = Action.event_id and deleted=0)'
    cond = [
        tableAction['deleted'].eq(0),
        tableAction['status'].inlist([CActionStatus.started, CActionStatus.appointed]),
        tableAction['event_id'].eq(eventId),
        tableActionType['isDoesNotInvolveExecutionCourse'].eq(0),
        'Action.begDate <= COALESCE(Event.execDate, %s, NOW())' % leavedEndDateStmt,
        ('EXISTS('
            ' SELECT NULL'
            ' FROM ActionProperty AP'
            ' JOIN ActionPropertyType APT ON AP.type_id = APT.id'
            ' JOIN ActionProperty_Double APD ON AP.id = APD.id'
            ' WHERE APT.inActionsSelectionTable = 2'
            ' AND APT.actionType_id = Action.actionType_id'
            ' AND AP.action_id = Action.id'
            ' AND APT.deleted = 0'
            ' AND AP.deleted = 0'
            ' AND APD.value > 0.0'
            ')'
        ),
        ('EXISTS('
            ' SELECT NULL'
            ' FROM ActionProperty AP'
            ' JOIN ActionProperty_rbNomenclature APN ON AP.id = APN.id'
            ' WHERE AP.action_id = Action.id'
            ' AND AP.deleted = 0'
            ' AND APN.value IS NOT NULL'
            ')'
        ),
    ]
    if orgStructureId:
        cond.append(tableAction['orgStructure_id'].inlist(getOrgStructureDescendants(orgStructureId)))
    if len(excludeActionIdList) > 0:
        cond.append(tableAction['id'].notInlist(excludeActionIdList))

    cols = [
        tableAction['id'].alias('actionId'),
        tableAction['begDate'],
        tableEvent['client_id'],
        tableActionType['isNomenclatureExpense'],
        tableActionEPI['id'].alias('EPIID'),
        tableActionEPI['group_id']
    ]

    recordList = db.getRecordList(queryTable, cols, cond, order='begDate')
    nomenclatureExpensePostDates = QtGui.qApp.admissibilityNomenclatureExpensePostDates()
    if not QtGui.qApp.userHasRight('nomenclatureExpenseLaterDate'):
        # без этого права нельзя выполнять списания позже текущей даты
        recordList = filter(
            lambda record: forceDate(record.value('begDate')) <= QtCore.QDate.currentDate(),
            recordList,
        )
    if not QtGui.qApp.userHasRight('noRestrictRetrospectiveNEClient') and nomenclatureExpensePostDates > 0:
        # в этом случае нельзя выполнять списание раньше даты, заданной глобальной настройкой
        minDate = QtCore.QDate()
        if nomenclatureExpensePostDates == 1: # прошедший день
            minDate = QtCore.QDate.currentDate().addDays(-1)
        elif nomenclatureExpensePostDates == 2: # текущий месяц
            minDate = firstMonthDay(QtCore.QDate.currentDate())
        if minDate:
            recordList = filter(
                lambda record: forceDate(record.value('begDate')) >= minDate,
                recordList,
            )
            
    groupingItems = {}
    sortedItems = []
    
    for item in recordList:
        groupId = forceInt(item.value('group_id'))
        subactionId = forceRef(item.value('actionId'))
        subaction = CAction.getActionById(subactionId)
        if not groupId:
            sortedItems.append(item)
        elif groupId == forceInt(item.value('EPIID')):
            if not groupId in groupingItems.keys():
                groupingItems[groupId] = [(item, subaction)]
            else:
                groupingItems[groupId].append((item,subaction))
            sortedItems.append(item)
        else:
            if not groupId in groupingItems.keys():
                groupingItems[groupId] = [(item,subaction)]
            else:
                groupingItems[groupId].append((item,subaction))
    return sortedItems, groupingItems
