# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2026 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import Qt

from library.InDocTable import CInDocTableView
from library.Utils import forceDate, forceRef, forceStringEx, toVariant
from Registry.VisitComboBox   import CVisitComboBox


class CVisitItemDelegate(QtGui.QItemDelegate):
    def __init__(self, parent=None):
        QtGui.QItemDelegate.__init__(self, parent)


    def createEditor(self, parent, option, index):
        visitIdList = []
        prophylaxisPlanningIdList = []
        removeDate = None
        model = index.model()
        row = index.row()
        items = model.items()
        for item in items:
            visitId = forceRef(item.value('visit_id'))
            if visitId and visitId not in visitIdList:
                visitIdList.append(visitId)
            prophylaxisPlanningId = forceRef(item.value('id'))
            if prophylaxisPlanningId and prophylaxisPlanningId not in prophylaxisPlanningIdList:
                prophylaxisPlanningIdList.append(prophylaxisPlanningId)
            if not removeDate:
                removeDate = forceDate(item.value('removeDate'))
        record = items[row]
        takenDate = forceDate(record.value('takenDate'))
        MKB = forceStringEx(record.value('MKB'))
        MKB = MKB[:3]
        clientId = forceRef(record.value('client_id'))
        if MKB and clientId:
            db = QtGui.qApp.db
            table = db.table('Visit')
            tableEvent = db.table('Event')
            tableEventType = db.table('EventType')
            tableRBEventTypePurpose = db.table('rbEventTypePurpose')
            tableDiagnosis = db.table('Diagnosis')
            tableDiagnostic = db.table('Diagnostic')
            tableDispanser = db.table('rbDispanser')
            queryTable = tableEvent.innerJoin(table, table['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.innerJoin(tableDiagnostic, tableDiagnostic['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.innerJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
            queryTable = queryTable.innerJoin(tableDispanser, tableDispanser['id'].eq(tableDiagnostic['dispanser_id']))
            queryTable = queryTable.innerJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
            queryTable = queryTable.innerJoin(tableRBEventTypePurpose, tableRBEventTypePurpose['id'].eq(tableEventType['purpose_id']))
            cond = [#table['date'].dateGe(takenDate),
                    tableDiagnosis['client_id'].eq(clientId),
                    tableEvent['client_id'].eq(clientId),
                    tableDiagnosis['MKB'].like(MKB[:3]+'%'),
                    tableDiagnostic['dispanser_id'].isNotNull(),
                    table['deleted'].eq(0),
                    tableDiagnosis['deleted'].eq(0),
                    tableDiagnostic['deleted'].eq(0),
                    tableEvent['deleted'].eq(0),
                    tableRBEventTypePurpose['purpose'].eq(6)
                    ]
            if visitIdList:
                cond.append(table['id'].notInlist(visitIdList))
            if removeDate:
                cond.append(table['date'].dateLe(removeDate))
            cond.append(u'''NOT EXISTS(SELECT ProphylaxisPlanning.id
            FROM ProphylaxisPlanning
            WHERE ProphylaxisPlanning.visit_id = Visit.id
            AND ProphylaxisPlanning.MKB LIKE '%s'
            AND ProphylaxisPlanning.deleted = 0 %s)'''%(MKB[:3]+'%', (u'AND ProphylaxisPlanning.id NOT IN (%s)'%(u','.join(str(ppId) for ppId in prophylaxisPlanningIdList if ppId))) if prophylaxisPlanningIdList else u''))
            editor = CVisitComboBox(parent)
            editor.setFilter(cond, queryTable)
        else:
            editor = None
        return editor


    def setEditorData(self, editor, index):
        model  = index.model()
        data = model.data(index, Qt.EditRole)
        editor.setValue(forceRef(data))


    def setModelData(self, editor, model, index):
        model.setData(index, toVariant(editor.value()))


class CVisitInDocTableView(CInDocTableView):
    def __init__(self, parent):
        CInDocTableView.__init__(self, parent)
        self.setItemDelegateForColumn(3, CVisitItemDelegate(self))

