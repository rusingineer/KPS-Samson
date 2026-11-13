# -*- coding: utf-8 -*-
from PyQt4 import QtGui


def searchActionIn(actionId):
    stmt = u'''  SELECT
    ActionPropertyType.dataInheritance,
    ActionPropertyType.name,
    ActionPropertyType.typeName,
    CASE ActionPropertyType.typeName
        WHEN 'ArterialPressure' THEN ActionProperty_ArterialPressure.value -- varchar
        WHEN 'Constructor'      THEN ActionProperty_String.value -- varchar
        WHEN 'Double'           THEN CAST(ActionProperty_Double.value AS CHAR)
        WHEN 'Html'             THEN ActionProperty_String.value
        WHEN 'Integer'          THEN CAST(ActionProperty_Integer.value AS CHAR)
        WHEN 'Pulse'            THEN ActionProperty_Pulse.value
        WHEN 'String'           THEN ActionProperty_String.value
        WHEN 'Text'             THEN ActionProperty_String.value
        WHEN 'Temperature'      THEN ActionProperty_Temperature.value
        WHEN 'Time'             THEN CAST(ActionProperty_Time.value AS CHAR)
        WHEN 'URL'              THEN ActionProperty_String.value
        WHEN 'Жалобы'           THEN ActionProperty_String.value
        WHEN 'Date'             THEN ActionProperty_Date.value
        WHEN 'Boolean'           THEN IF(ActionProperty_Boolean.value IS NULL, 'false', 'true')
    ELSE NULL
    END              AS value
FROM Action
INNER JOIN ActionType ON ActionType.id = Action.actionType_id
INNER JOIN ActionPropertyType ON ActionPropertyType.actionType_id = ActionType.id
left JOIN ActionProperty ON ActionProperty.action_id = Action.id AND ActionProperty.type_id = ActionPropertyType.id

LEFT  JOIN ActionProperty_ArterialPressure ON ActionProperty_ArterialPressure.id = ActionProperty.id
LEFT  JOIN ActionProperty_Date             ON ActionProperty_Date.id = ActionProperty.id
LEFT  JOIN ActionProperty_Double           ON ActionProperty_Double.id = ActionProperty.id
LEFT  JOIN ActionProperty_Integer          ON ActionProperty_Integer.id = ActionProperty.id
LEFT  JOIN ActionProperty_PhaseMenstrual   ON ActionProperty_PhaseMenstrual.id = ActionProperty.id
LEFT  JOIN ActionProperty_Pulse            ON ActionProperty_Pulse.id = ActionProperty.id
LEFT  JOIN ActionProperty_String           ON ActionProperty_String.id = ActionProperty.id
LEFT  JOIN ActionProperty_Temperature      ON ActionProperty_Temperature.id = ActionProperty.id
LEFT  JOIN ActionProperty_Time             ON ActionProperty_Time.id = ActionProperty.id
LEFT  JOIN ActionProperty_Boolean          ON ActionProperty_Boolean.id = ActionProperty.id
LEFT JOIN Event e ON e.id = Action.event_id
WHERE Action.id = %(actionId)s
  AND ActionPropertyType.deleted = 0
    AND dataInheritance LIKE '%%in_%%'
    ORDER BY shortName
        ''' % dict(actionId=actionId)
    db = QtGui.qApp.db
    return db.query(stmt)

def searchActionOut(shortNames, eventId):
    if isinstance(shortNames, list):
        shortName = '('
        for params in shortNames:
            if shortName == '(':
                shortName += " dataInheritance like ('%" + params.replace("in_", "out_") + "%')"
            else:
                shortName += " or dataInheritance like ('%" + params.replace("in_", "out_") + "%')"
        shortName += ')'
    else:
        shortName = " dataInheritance like ('%" + shortNames.replace("in_", "out_") + "%')"
    stmt = u'''  SELECT
    Action.id as action_id,
    Action.idx as action_idx,
    ActionPropertyType.dataInheritance,
    ActionPropertyType.name,
    ActionType.name as actionName,
    ActionPropertyType.typeName,
    ActionType.title,
    Action.endDate,
    CASE ActionPropertyType.typeName
        WHEN 'ArterialPressure' THEN ActionProperty_ArterialPressure.value -- varchar
        WHEN 'Constructor'      THEN ActionProperty_String.value -- varchar
        WHEN 'Double'           THEN CAST(ActionProperty_Double.value AS CHAR)
        WHEN 'Html'             THEN ActionProperty_String.value
        WHEN 'Integer'          THEN CAST(ActionProperty_Integer.value AS CHAR)
        WHEN 'Pulse'            THEN ActionProperty_Pulse.value
        WHEN 'String'           THEN ActionProperty_String.value
        WHEN 'Text'             THEN ActionProperty_String.value
        WHEN 'Temperature'      THEN ActionProperty_Temperature.value
        WHEN 'Time'             THEN CAST(ActionProperty_Time.value AS CHAR)
        WHEN 'URL'              THEN ActionProperty_String.value
        WHEN 'Жалобы'           THEN ActionProperty_String.value
        WHEN 'Date'             THEN ActionProperty_Date.value
        WHEN 'Boolean'           THEN IF(ActionProperty_Boolean.value IS NULL, 'false', 'true')
    ELSE NULL
    END              AS value
FROM Action
INNER JOIN ActionType ON ActionType.id = Action.actionType_id
INNER JOIN ActionPropertyType ON ActionPropertyType.actionType_id = ActionType.id
left JOIN ActionProperty ON ActionProperty.action_id = Action.id AND ActionProperty.type_id = ActionPropertyType.id

LEFT  JOIN ActionProperty_ArterialPressure ON ActionProperty_ArterialPressure.id = ActionProperty.id
LEFT  JOIN ActionProperty_Date             ON ActionProperty_Date.id = ActionProperty.id
LEFT  JOIN ActionProperty_Double           ON ActionProperty_Double.id = ActionProperty.id
LEFT  JOIN ActionProperty_Integer          ON ActionProperty_Integer.id = ActionProperty.id
LEFT  JOIN ActionProperty_PhaseMenstrual   ON ActionProperty_PhaseMenstrual.id = ActionProperty.id
LEFT  JOIN ActionProperty_Pulse            ON ActionProperty_Pulse.id = ActionProperty.id
LEFT  JOIN ActionProperty_String           ON ActionProperty_String.id = ActionProperty.id
LEFT  JOIN ActionProperty_Temperature      ON ActionProperty_Temperature.id = ActionProperty.id
LEFT  JOIN ActionProperty_Time             ON ActionProperty_Time.id = ActionProperty.id
LEFT  JOIN ActionProperty_Boolean          ON ActionProperty_Boolean.id = ActionProperty.id
LEFT JOIN Event e ON e.id = Action.event_id
WHERE Action.deleted = 0 and Action.event_id = %(eventId)s
  AND ActionPropertyType.deleted = 0 
  AND Action.endDate IS NOT NULL AND Action.endDate!=''
    AND %(shortName)s
    having value is not null and value != ''
    ORDER BY Action.endDate, Action.id, ActionPropertyType.idx
        ''' % dict(shortName=shortName, eventId=eventId)
    db = QtGui.qApp.db
    return db.query(stmt)

def dialog_copi(list):
    dialog = QtGui.QDialog()
    layout = QtGui.QGridLayout(dialog)
    edtBegDate = QtGui.QListWidget()
    edtBegDate.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
    edtBegDate.addItems(list)
    buttonBox = QtGui.QDialogButtonBox()
    buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
    buttonBox.accepted.connect(dialog.accept)
    buttonBox.rejected.connect(dialog.reject)
    layout.addWidget(QtGui.QLabel(u'Дата начала периода'), 0, 0)
    layout.addWidget(edtBegDate, 0, 1)
    layout.addWidget(buttonBox, 4, 0, 1, 2)
    dialog.setWindowTitle(u'Параметры отчета')
    dialog.exec_()