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

from Events.Utils import getEventTypeForm, isEventDeath, isEventPeriodic, isEventUrgent
from library.Utils       import forceRef
from F000.F000Dialog import CF000Dialog
from F001.F001Dialog import CF001Dialog
from F003.F003Dialog import CF003Dialog
from F025.F025Dialog import CF025Dialog
from F025.F025TrDialog import CF025TrDialog
from F027.F027Dialog import CF027Dialog
from F030.F030Dialog import CF030Dialog
from F043.F043Dialog import CF043Dialog
from F072.F072Dialog import CF072Dialog
from F088.F088EditDialog import CF088EditDialog
from F106.F106Dialog import CF106Dialog
from F131.F131Dialog import CF131Dialog
from F110.F110Dialog import CF110Dialog


_eventForms = [
   ('000',   u'ф. 000/у (платное обслуживание)',      CF000Dialog),
   ('001',   u'ф. 001/у (ввод услуг)',                CF001Dialog),
   ('003',   u'ф. 003/у (стационарное лечение)',      CF003Dialog),
   ('025',   u'ф. 025/у (стат.талон)',                CF025Dialog),
   ('027',   u'ф. 027/у (протокол)',                  CF027Dialog),
   ('030',   u'ф. 030/у (диспансерное наблюдение)',   CF030Dialog),
   ('043',   u'ф. 043/у (стоматология)',              CF043Dialog),
   ('072',   u'ф. 072/у (восстановительное лечение)', CF072Dialog),
   ('088',   u'ф. 088/у (направление на МСЭ)',        CF088EditDialog),
   ('090',   u'ф. 090/у (ЭЛМК)',                      CF001Dialog),
   ('106',   u'ф. 106/у (констатация смерти)',        CF106Dialog),
   ('131',   u'ф. 131/у (доп.диспансеризация)',       CF131Dialog),
   ('110',   u'ф. 110/у (скорая медицинская помощь)', CF110Dialog),
 ]

_mapEventFormCodeToFormClass = dict([(descr[0], descr[2]) for descr in _eventForms if descr[2]])


def getEventFormClassByType(eventTypeId):
    form = getEventTypeForm(eventTypeId)
    result = _mapEventFormCodeToFormClass.get(form, None)
    if result:
        return result
    if isEventDeath(eventTypeId):
        return CF106Dialog
    if isEventPeriodic(eventTypeId):
        return CF131Dialog
    if isEventUrgent(eventTypeId):
        return CF025TrDialog
    return CF025Dialog


def getEventFormClass(eventId):
    eventTypeId = QtGui.qApp.db.translate('Event', 'id', eventId, 'eventType_id')
    return getEventFormClassByType(eventTypeId)


def getEventFormList():
    return [_descr[:2] for _descr in _eventForms if _descr[2]]


def getF090ActionIdToEventId(eventId):
    if eventId:
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        queryTable = tableAction.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        cond = [tableAction['event_id'].eq(eventId),
                tableAction['deleted'].eq(0),
                tableActionType['deleted'].eq(0),
                tableActionType['flatCode'].like(u'%medical_examination'),
                ]
        record = db.getRecordEx(queryTable, [tableAction['id'].alias('actionId')], cond)
        return forceRef(record.value('actionId')) if record else None
    return None
