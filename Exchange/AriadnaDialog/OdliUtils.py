# -*- coding:utf-8 -*-

from library.Utils import *


# получение информации о направлении из бд
def OrderMis(actionId):
    db = QtGui.qApp.db
    sql = u'''select Action.event_id as eventId, aps.value as number
                from Action
                LEFT JOIN ActionType ON  ActionType.id = Action.actionType_id   
				LEFT JOIN ActionPropertyType AS apt ON  ActionType.id = apt.actionType_id and apt.deleted=0 and apt.name = 'Номер направления'  
				LEFT JOIN ActionProperty AS ap ON  Action.id = ap.action_id and ap.deleted=0 and ap.type_id = apt.id  
				LEFT JOIN ActionProperty_String AS aps ON aps.id = ap.id 
                where Action.id = {0} '''.format(actionId)
    result = {}
    query = db.query(sql)
    while query.next():
        record = query.record()
        result['eventId'] = forceString(record.value('eventId'))
        result['number'] = forceString(record.value('number'))
    return result


def warninWindow(massege):
    buttons = QtGui.QMessageBox.Ok
    QtGui.QMessageBox.warning(QtGui.qApp.mainWindow,
                              u'Информация',
                              massege,
                              buttons)
