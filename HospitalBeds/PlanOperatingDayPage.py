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
from PyQt4.QtCore import Qt, QDate, QDateTime, QModelIndex, pyqtSignature, SIGNAL, QVariant

from library.DialogBase    import CDialogBase
from library.Utils         import exceptionToUnicode, forceRef, forceString, toVariant, forceDate, forceInt, formatShortNameInt, trim, forceStringEx, calcAge
from library.InDocTable    import CInDocTableModel, CInDocTableCol, CEnumInDocTableCol, CTextInDocTableCol, forcePyType
from library.ItemsListDialog  import CItemEditorBaseDialog
from library.interchange   import setCheckBoxValue, setDatetimeEditValue, setDoubleBoxValue, setLabelText, setLineEditValue, setRBComboBoxValue
from library.PrintInfo     import CInfoContext
from library.PrintTemplates import customizePrintButton, applyTemplate, CPrintAction, getPrintTemplates
from library.database      import CTableRecordCache
from library.ICDCodeEdit   import CICDCodeEditEx
from Orgs.PersonComboBoxEx import CPersonFindInDocTableCol, CPersonComboBoxEx
from Orgs.Utils            import getOrgStructureFullName
from Reports.ReportBase    import CReportBase, createTable
from Reports.ReportView    import CReportViewDialog
from Reports.Report        import normalizeMKB
from Reports.Utils         import updateLIKE
from Resources.JobTicketChooser import getJobTicketAsText
from SurgeryJournal.SurgeryJournalDialog import CSurgeryJournalDialog
from Events.Action         import CAction, CActionType
from Events.ActionInfo     import CPlanOperatingDayInfoList
from Events.ActionStatus   import CActionStatus
from Events.ActionEditDialog import CActionEditDialog
from Events.ActionServiceType import CActionServiceType
from Events.ActionTypeComboBoxEx import CActionTypeFindInDocTableCol
from Events.Utils          import setActionPropertiesColumnVisible, inPlanOperatingDay, inMedicalDiagnosis, getActionTypeIdListByFlatCode, medicalDiagnosisType
from HospitalBeds.OperatingAssistentsDialog import COperatingAssistentsDialog
from HospitalBeds.OperatingMedicalDiagnosisDialog import COperatingMedicalDiagnosisDialog
from Users.Rights import urCanUseNomenclatureButton, urCopyPrevAction, urLoadActionTemplate, urSaveActionTemplate, \
    urEditOtherpeopleAction, urEditOtherPeopleActionSpecialityOnly

from Ui_PlanOperatingDayPage import Ui_PlanOperatingDayPage
from Ui_UpdateDateSurgeryDialog import Ui_UpdateDateSurgeryDialog


numberPropertyColumnName         = u'номер по порядку'
medicalDiagnosisColumnName       = u'предоперационный диагноз'
assistantTeamColumnName          = u'ассистент'
anestesiaTeamColumnName          = u'анестезиолог'
assistantAnestesiaTeamColumnName = u'ассистент анестезиолога'
noteColumnName                   = u'особые отметки'
planedTimeColumnName             = u'длительность операции'
jobTicketPropertyColumnName      = u'работа'


class CPlanOperatingDayModel(CInDocTableModel):
    class CLocClientColumn(CInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.clientCaches = params.get('clientCaches', [])
            self.eventCaches = params.get('eventCaches', [])

        def setClientCache(self, clientCache):
            self.clientCaches = clientCache

        def setEventCache(self, eventCache):
            self.eventCaches = eventCache

        def toString(self, val, record):
            eventId  = forceRef(val)
            if eventId and self.clientCaches and self.eventCaches:
                eventRecord = self.eventCaches.get(eventId)
                if eventRecord:
                    clientId = forceRef(eventRecord.value('client_id'))
                    setDate  = forceDate(eventRecord.value('setDate'))
                    clientRecord = self.clientCaches.get(clientId) if clientId else None
                    if clientRecord:
                        birthDate = forceDate(clientRecord.value('birthDate'))
                        clientAge = calcAge(birthDate, setDate)
                        name = formatShortNameInt(forceString(clientRecord.value('lastName')),
                               forceString(clientRecord.value('firstName')),
                               forceString(clientRecord.value('patrName'))) + u', ' + clientAge
                        return toVariant(name)
            return QVariant()

        def alignment(self):
            return QVariant(Qt.AlignLeft + Qt.AlignTop)

    class CLocExternalIdColumn(CInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.eventCaches = params.get('eventCaches', [])

        def setEventCache(self, eventCache):
            self.eventCaches = eventCache

        def toString(self, val, record):
            eventId  = forceRef(val)
            if eventId and self.eventCaches:
                eventRecord = self.eventCaches.get(eventId)
                if eventRecord:
                    return toVariant(forceString(eventRecord.value('externalId')))
            return QVariant()

        def alignment(self):
            return QVariant(Qt.AlignLeft + Qt.AlignTop)

    class CLocPlacementColumn(CInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.eventCaches = params.get('eventCaches', [])

        def setEventCache(self, eventCache):
            self.eventCaches = eventCache

        def toString(self, val, record):
            eventId  = forceRef(val)
            if eventId and self.eventCaches:
                eventRecord = self.eventCaches.get(eventId)
                if eventRecord:
                    return toVariant(forceString(eventRecord.value('placement')))
            return QVariant()

        def alignment(self):
            return QVariant(Qt.AlignLeft + Qt.AlignTop)

    class CToolButtonPropertyColumn(CInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.name = params.get('name', '')
            self.caches = params.get('caches', [])

        def toString(self, val, record, action):
            properties = []
            if action and self.name:
                actionType = action.getType()
                for name, propertyType in actionType._propertiesByName.items():
                    if propertyType.inPlanOperatingDay and self.name.lower() == inPlanOperatingDay[propertyType.inPlanOperatingDay].lower():
                        properties.append((propertyType, action[name]))
                properties.sort(key=lambda prop:prop[0].idx)
                return toVariant(u'\n'.join((forceString(self.caches.get(properti[1]).value('name')) if self.caches.get(properti[1]) else u'') for properti in properties))
            return QVariant()

        def toSortString(self, val, record, action):
            return forcePyType(self.toString(val, record, action))

        def toStatusTip(self, val, record, action):
            return self.toString(val, record, action)

        def createEditor(self, parent):
            editor = QtGui.QToolButton(parent)
            editor.setText(u'...')
            return editor

        def setEditorData(self, editor, value, record):
            editor.setText(forceString(value))

        def getEditorData(self, editor):
            return toVariant(editor.text())

        def alignment(self):
            return QVariant(Qt.AlignLeft + Qt.AlignTop)

    class CLocActionPropertyColumn(CTextInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CTextInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.name = params.get('name', '')

        def toString(self, val, record, action):
            if action and self.name:
                actionType = action.getType()
                for name, propertyType in actionType._propertiesByName.items():
                    if propertyType.inPlanOperatingDay and self.name.lower() == inPlanOperatingDay[propertyType.inPlanOperatingDay].lower():
                        return toVariant(action[name])
            return QVariant()

        def toSortString(self, val, record, action):
            return forcePyType(self.toString(val, record, action))

        def toStatusTip(self, val, record, action):
            return self.toString(val, record, action)

    class CLocNumberActionPropertyColumn(CInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.name = params.get('name', '')

        def toString(self, val, record, action, row):
            if action and self.name:
                actionType = action.getType()
                for name, propertyType in actionType._propertiesByName.items():
                    if propertyType.inPlanOperatingDay and self.name.lower() == inPlanOperatingDay[propertyType.inPlanOperatingDay].lower():
                        number = action[name]
                        if number == (row + 1):
                            return toVariant(number)
                        else:
                            action[name] = row + 1
                            return toVariant(action[name])
            return toVariant(row + 1)

        def toSortString(self, val, record, action, row):
            return forcePyType(self.toString(val, record, action, row))

        def toStatusTip(self, val, record, action, row):
            return self.toString(val, record, action, row)

        def createEditor(self, parent):
            editor = QtGui.QLineEdit(parent)
            if self._maxLength:
                editor.setMaxLength(self._maxLength)
            if self._inputMask:
                editor.setInputMask(self._inputMask)
            return editor

        def setEditorData(self, editor, value, record):
            editor.setText(forceStringEx(value))

        def getEditorData(self, editor):
            text = trim(editor.text())
            if text:
                return toVariant(text)
            else:
                return QVariant()

        def alignment(self):
            return QVariant(Qt.AlignLeft + Qt.AlignTop)

    class CLocJobTicketPropertyColumn(CInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.name = params.get('name', '')
            self.eventCache = params.get('eventCache', [])

        def setEventCache(self, eventCache):
            self.eventCaches = eventCache

        def toString(self, val, record, action):
            if action and self.name:
                actionType = action.getType()
                for name, propertyType in actionType._propertiesByName.items():
                    if propertyType.inPlanOperatingDay and self.name.lower() == inPlanOperatingDay[propertyType.inPlanOperatingDay].lower():
                        return toVariant(getJobTicketAsText(action[name]))
            return QVariant()

        def toSortString(self, val, record, action):
            return forcePyType(self.toString(val, record, action))

        def toStatusTip(self, val, record, action):
            return self.toString(val, record, action)

        def alignment(self):
            return QVariant(Qt.AlignLeft + Qt.AlignTop)

    class CLocEnumInDocTableCol(CEnumInDocTableCol):
        def __init__(self, title, fieldName, width, values, **params):
            CEnumInDocTableCol.__init__(self, title, fieldName, width, values, **params)
            self.values = values

        def alignment(self):
            return QVariant(Qt.AlignLeft + Qt.AlignTop)

    class CLocPersonFindInDocTableCol(CPersonFindInDocTableCol):
        def __init__(self, title, fieldName, width, tableName, **params):
            CPersonFindInDocTableCol.__init__(self, title, fieldName, width, tableName, **params)

        def createEditor(self, parent):
            editor = CPersonComboBoxEx(parent)
            editor.setOrgStructureId(self.orgStructureId)
            editor.setDate(self.date)
            editor.setOnlyDoctors(True)
            return editor

        def alignment(self):
            return QVariant(Qt.AlignLeft + Qt.AlignTop)

    class CLocAssistantFindInDocTableCol(CPersonFindInDocTableCol):
        def __init__(self, title, fieldName, width, tableName, **params):
            CPersonFindInDocTableCol.__init__(self, title, fieldName, width, tableName, **params)

        def alignment(self):
            return QVariant(Qt.AlignLeft + Qt.AlignTop)

    class CLocActionTypeFindInDocTableCol(CActionTypeFindInDocTableCol):
        def __init__(self, title, fieldName, width, tableName, actionTypeClass, serviceType = None, **params):
            CActionTypeFindInDocTableCol.__init__(self, title, fieldName, width, tableName, actionTypeClass, serviceType, **params)

        def alignment(self):
            return QVariant(Qt.AlignLeft + Qt.AlignTop)

    class CLocICDInDocTableCol(CInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)

        def createEditor(self, parent):
            editor = CICDCodeEditEx(parent)
            return editor

        def setEditorData(self, editor, value, record):
            findFilter = u''
            eventId = forceRef(record[0].value('event_id'))
            if eventId:
                diagnosisLine = []
                db = QtGui.qApp.db
                tableDiagnosis = db.table('Diagnosis')
                tableDiagnostic = db.table('Diagnostic')
                queryTable = tableDiagnosis.innerJoin(tableDiagnostic, tableDiagnostic['diagnosis_id'].eq(tableDiagnosis['id']))
                cols = [tableDiagnosis['MKB'],
                        tableDiagnostic['event_id'],
                        ]
                cond = [tableDiagnostic['event_id'].eq(eventId),
                        tableDiagnosis['deleted'].eq(0),
                        tableDiagnostic['deleted'].eq(0),
                        ]
                records = db.getRecordListGroupBy(queryTable, cols, cond, group=u'Diagnosis.MKB, Diagnostic.event_id', order=u'Diagnosis.MKB, Diagnostic.event_id')
                for recordMKB in records:
                    MKB = normalizeMKB(forceString(recordMKB.value('MKB')))
                    if MKB:
                        diagnosisLine.append(MKB)
                tableAction = db.table('Action')
                cols = [tableAction['MKB']]
                cond = [tableAction['event_id'].eq(eventId),
                        tableAction['deleted'].eq(0)
                        ]
                records = db.getRecordListGroupBy(tableAction, cols, cond, group=u'Action.MKB, Action.event_id', order=u'Action.MKB, Action.event_id')
                for recordMKB in records:
                    MKB = normalizeMKB(forceString(recordMKB.value('MKB')))
                    if MKB:
                        diagnosisLine.append(MKB)
                if diagnosisLine:
                    findFilter = (u'LEFT(DiagId, 3) IN (%s)'%(u','.join(u'LEFT(\'%s\', 3)'%(mkb) for mkb in diagnosisLine if mkb)), u'DiagId IN (%s)'%(u','.join(u'\'%s\''%(mkb) for mkb in diagnosisLine if mkb)))
            editor.setFindFilter(findFilter)
            editor.setText(forceStringEx(value))

        def alignment(self):
            return QVariant(Qt.AlignLeft + Qt.AlignTop)


    Col_Number                 = 0
    Col_Fio                    = 1
    Col_Placement              = 2
    Col_ExternalId             = 3
    Col_MKB                    = 4
    Col_MedicalDiagnosis       = 5
    Col_Status                 = 6
    Col_ActionTypeId           = 7
    Col_PersonId               = 8
    Col_AssistantId            = 9
    Col_AssistantTeam          = 10
    Col_AnestesiaTeam          = 11
    Col_AssistantAnestesiaTeam = 12
    Col_Note                   = 13
    Col_PlanedTime             = 14
    Col_JobTicked              = 15


    def __init__(self, parent, type, personsCache, clientCache=[], eventCache=[], orgStructureId=None):
        CInDocTableModel.__init__(self, 'Action', 'id', 'event_id', parent)
        self.addCol(CPlanOperatingDayModel.CLocNumberActionPropertyColumn(   u'№',                           'id',            10, name = numberPropertyColumnName                                )).setReadOnly(True)
        self.addCol(CPlanOperatingDayModel.CLocClientColumn(                 u'ФИО, возраст',                'event_id',      60, clientCache = clientCache, eventCache = eventCache        )).setReadOnly(True)
        self.addCol(CPlanOperatingDayModel.CLocPlacementColumn(              u'Палата',                      'event_id',      10, eventCache = eventCache                                   )).setReadOnly(True)
        self.addCol(CPlanOperatingDayModel.CLocExternalIdColumn(             u'№ истории болезни',           'event_id',      10, eventCache = eventCache                                   )).setReadOnly(True)
        self.addCol(CPlanOperatingDayModel.CLocICDInDocTableCol(             u'МКБ',                         'MKB',           20                                                            )).setReadOnly(type)
        self.addCol(CPlanOperatingDayModel.CLocActionPropertyColumn(         u'Диагноз',                     'event_id',      20, name = medicalDiagnosisColumnName                        )).setReadOnly(type)
        self.addCol(CPlanOperatingDayModel.CLocEnumInDocTableCol(            u'Статус',                      'status',        10, CActionStatus.names                                       )).setReadOnly(True)
        self.addCol(CPlanOperatingDayModel.CLocActionTypeFindInDocTableCol(  u'Операция',                    'actionType_id', 20, 'ActionType', 2, CActionServiceType.operation, isPlanOperatingDay=True, orgStructureId=orgStructureId, isPreferableOrgStructure=True)).setReadOnly(type)
        self.addCol(CPlanOperatingDayModel.CLocPersonFindInDocTableCol(      u'Оператор',                    'person_id',     20, 'vrbPersonWithSpecialityAndOrgStr', parent=parent         )).setReadOnly(type)
        self.addCol(CPlanOperatingDayModel.CLocAssistantFindInDocTableCol(   u'Ассистент',                   'assistant_id',  20, 'vrbPersonWithSpecialityAndOrgStr', parent=parent         )).setReadOnly(type)
        self.addCol(CPlanOperatingDayModel.CToolButtonPropertyColumn(        u'Ассистент',                   'id',            20, name = assistantTeamColumnName,    caches = personsCache  )).setReadOnly(type)
        self.addCol(CPlanOperatingDayModel.CToolButtonPropertyColumn(        u'Анестезиологическая бригада', 'id',            20, name = anestesiaTeamColumnName,    caches = personsCache  )).setReadOnly(type)
        self.addCol(CPlanOperatingDayModel.CToolButtonPropertyColumn(        u'Ассистент анестезиолога',     'id',            20, name = assistantAnestesiaTeamColumnName, caches = personsCache  )).setReadOnly(type)
        self.addCol(CPlanOperatingDayModel.CLocActionPropertyColumn(         u'Особые отметки',              'id',            20, name = noteColumnName                                  )).setReadOnly(type)
        self.addCol(CPlanOperatingDayModel.CLocActionPropertyColumn(         u'Планируемое время',           'id',            20, name = planedTimeColumnName                           )).setReadOnly(type)
        self.addCol(CPlanOperatingDayModel.CLocJobTicketPropertyColumn(      u'Работа',                      'id',            20, name = jobTicketPropertyColumnName,                  eventCache = eventCache)).setReadOnly(type)
        self.personsCache = personsCache
        self.clientCache = clientCache
        self.eventCache = eventCache
        self.type = type
        self.actionList = {}
        self.removeActions = []
        self.setEnableAppendLine(False)
        self.reservedJobTickets = {}
        self.operatingPlanDate = None


    def addReservedJobTickets(self, jobTicketData):
        self.reservedJobTickets = jobTicketData


    def addReservedJobTicketId(self, clientId, jobTicketId):
        reservedJobTicketsLine = set(self.reservedJobTickets.get(clientId, []))
        reservedJobTicketsLine = reservedJobTicketsLine | set([jobTicketId])
        self.reservedJobTickets[clientId] = list(reservedJobTicketsLine)


    def removeReservedJobTickets(self):
        self.reservedJobTickets = {}


    def removeReservedJobTicketId(self, clientId, jobTicketId):
        reservedJobTicketsLine = set(self.reservedJobTickets.get(clientId, []))
        reservedJobTicketsLine = reservedJobTicketsLine - set([jobTicketId])
        self.reservedJobTickets[clientId] = list(reservedJobTicketsLine)


    def getEditorInitValues(self, index):
        if index and index.isValid():
            row = index.row()
            items = self.items()
            if row >= 0 and row < len(items):
                item = items[row]
                return self.getEditorInitValuesByItem(item)
        return None, None, None, None, {}


    def getMedicalDiagnosisValues(self, index):
        if index and index.isValid():
            row = index.row()
            items = self.items()
            if row >= 0 and row < len(items):
                item = items[row]
                if item:
                    record, action = item
                    if record and action:
                        eventId = forceRef(record.value('event_id'))
                        return eventId, self.operatingPlanDate
        return None, None


    def getEditorInitValuesByItem(self, item):
        if item:
            record, action = item
            if record and action:
                eventId = forceRef(record.value('event_id'))
                if eventId and self.eventCache:
                    eventRecord = self.eventCache.get(eventId)
                    if eventRecord:
                        clientId = forceRef(eventRecord.value('client_id'))
                        eventTypeId = forceRef(eventRecord.value('eventType_id'))
                        domain = self.getDomain(action)
                        return action, domain, clientId, eventTypeId, self.reservedJobTickets
        return None, None, None, None, {}


    def getDomain(self, action):
        col = self._cols[CPlanOperatingDayModel.Col_JobTicked]
        if action and col.name:
            actionType = action.getType()
            for name, propertyType in actionType._propertiesByName.items():
                if propertyType.inPlanOperatingDay and col.name.lower() == inPlanOperatingDay[propertyType.inPlanOperatingDay].lower():
                    return propertyType.valueDomain
        return None


    def getJobTickedId(self, action):
        col = self._cols[CPlanOperatingDayModel.Col_JobTicked]
        if action and col.name:
            actionType = action.getType()
            for name, propertyType in actionType._propertiesByName.items():
                if propertyType.inPlanOperatingDay and col.name.lower() == inPlanOperatingDay[propertyType.inPlanOperatingDay].lower():
                    return action[name]
        return None


    def setClientCache(self, clientCache):
        self.clientCache = clientCache
        self._cols[CPlanOperatingDayModel.Col_Fio].setClientCache(self.clientCache)


    def setEventCache(self, eventCache):
        self.eventCache = eventCache
        self._cols[CPlanOperatingDayModel.Col_Fio].setEventCache(self.eventCache)
        self._cols[CPlanOperatingDayModel.Col_Placement].setEventCache(self.eventCache)
        self._cols[CPlanOperatingDayModel.Col_ExternalId].setEventCache(self.eventCache)
        self._cols[CPlanOperatingDayModel.Col_JobTicked].setEventCache(self.eventCache)


    def getEmptyRecord(self):
        return QtGui.qApp.db.table('Action').newRecord()


    def setItems(self, items):
        recordNew, actionNew = items
        record, action = self._items
        if id(record) != id(recordNew):
            self._items = items
            self.reset()


    def insertRecord(self, row, record, action):
        self.beginInsertRows(QModelIndex(), row, row)
        self._items.insert(row, (record, action))
        self.endInsertRows()


    def addRecord(self, record, action):
        self.insertRecord(len(self._items), (record, action))


    def cellReadOnly(self, index):
        column = index.column()
        row = index.row()
        if 0 <= row < len(self._items) and column == CPlanOperatingDayModel.Col_JobTicked:
            record, action = self._items[row]
            if action:
                actionType = action.getType()
                for name, propertyType in actionType._propertiesByName.items():
                    if propertyType.inPlanOperatingDay and jobTicketPropertyColumnName == inPlanOperatingDay[propertyType.inPlanOperatingDay].lower():
                        return False
            return True
        return False


    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if 0 <= row < len(self._items):
            if role == Qt.EditRole:
                col = self._cols[column]
                record, action = self._items[row]
                if column in [CPlanOperatingDayModel.Col_AssistantTeam, CPlanOperatingDayModel.Col_AnestesiaTeam, CPlanOperatingDayModel.Col_AssistantAnestesiaTeam]:
                    if action:
                        actionType = action.getType()
                        properties = []
                        for name, propertyType in actionType._propertiesByName.items():
                            if propertyType.inPlanOperatingDay and col.name == inPlanOperatingDay[propertyType.inPlanOperatingDay].lower():
                                properties.append((propertyType, action[name]))
                        properties.sort(key=lambda prop:prop[0].idx)
                        return toVariant(u'\n'.join((forceString(self.personsCache.get(properti[1]).value('name')) if self.personsCache.get(properti[1]) else u'') for properti in properties))
                    return QVariant()
                elif column in [CPlanOperatingDayModel.Col_Number, CPlanOperatingDayModel.Col_MedicalDiagnosis, CPlanOperatingDayModel.Col_Note, CPlanOperatingDayModel.Col_PlanedTime, CPlanOperatingDayModel.Col_JobTicked]:
                    if action:
                        actionType = action.getType()
                        for name, propertyType in actionType._propertiesByName.items():
                            if propertyType.inPlanOperatingDay and col.name.lower() == inPlanOperatingDay[propertyType.inPlanOperatingDay].lower():
                                return toVariant(action[name])
                    return QVariant()
                else:
                    return record.value(col.fieldName())

            if role == Qt.DisplayRole:
                col = self._cols[column]
                record, action = self._items[row]
                if column == CPlanOperatingDayModel.Col_Number:
                    return col.toString(record.value(col.fieldName()), record, action, row)
                elif column in [CPlanOperatingDayModel.Col_AssistantTeam, CPlanOperatingDayModel.Col_AnestesiaTeam, CPlanOperatingDayModel.Col_AssistantAnestesiaTeam, CPlanOperatingDayModel.Col_Note, CPlanOperatingDayModel.Col_MedicalDiagnosis, CPlanOperatingDayModel.Col_PlanedTime, CPlanOperatingDayModel.Col_JobTicked]:
                    return col.toString(record.value(col.fieldName()), record, action)
                else:
                    return col.toString(record.value(col.fieldName()), record)

            if role == Qt.StatusTipRole:
                col = self._cols[column]
                record, action = self._items[row]
                if column == CPlanOperatingDayModel.Col_Number:
                    return col.toStatusTip(record.value(col.fieldName()), record, action, row)
                elif column in [CPlanOperatingDayModel.Col_AssistantTeam, CPlanOperatingDayModel.Col_AnestesiaTeam, CPlanOperatingDayModel.Col_AssistantAnestesiaTeam, CPlanOperatingDayModel.Col_MedicalDiagnosis, CPlanOperatingDayModel.Col_Note, CPlanOperatingDayModel.Col_PlanedTime, CPlanOperatingDayModel.Col_JobTicked]:
                    return col.toStatusTip(record.value(col.fieldName()), record, action)
                else:
                    return col.toStatusTip(record.value(col.fieldName()), record)

            if role == Qt.TextAlignmentRole:
                col = self._cols[column]
                return col.alignment()

            if role == Qt.CheckStateRole:
                col = self._cols[column]
                record, action = self._items[row]
                return col.toCheckState(record.value(col.fieldName()), record)

            if role == Qt.ForegroundRole:
                col = self._cols[column]
                record, action = self._items[row]
                return col.getForegroundColor(record.value(col.fieldName()), record)

        return QVariant()


    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            column = index.column()
            row = index.row()
            if row == len(self._items):
                if value.isNull():
                    return False
                record = self.getEmptyRecord()
                self._items.append(record, CAction(record=record))
                count = len(self._items)
                rootIndex = QModelIndex()
                self.beginInsertRows(rootIndex, count, count)
                self.insertRows(count, 1, rootIndex)
                self.endInsertRows()
            record, action = self._items[row]
            col = self._cols[column]
            if column in [CPlanOperatingDayModel.Col_AssistantTeam, CPlanOperatingDayModel.Col_AnestesiaTeam, CPlanOperatingDayModel.Col_AssistantAnestesiaTeam]:
                pass
            elif column in [CPlanOperatingDayModel.Col_Number, CPlanOperatingDayModel.Col_MedicalDiagnosis, CPlanOperatingDayModel.Col_Note, CPlanOperatingDayModel.Col_PlanedTime, CPlanOperatingDayModel.Col_JobTicked]:
                if action:
                    actionType = action.getType()
                    for name, propertyType in actionType._propertiesByName.items():
                        if propertyType.inPlanOperatingDay and col.name.lower() == inPlanOperatingDay[propertyType.inPlanOperatingDay].lower():
                            if column == CPlanOperatingDayModel.Col_JobTicked:
                                jobTicketIdOld = forceRef(action[name])
                                eventId = forceRef(record.value('event_id'))
                                if eventId and self.eventCache:
                                    eventRecord = self.eventCache.get(eventId)
                                    if eventRecord:
                                        clientId = forceRef(eventRecord.value('client_id'))
                                        jobTicketId = forceRef(value)
                                        if clientId:
                                            if jobTicketIdOld and jobTicketIdOld != jobTicketId:
                                                self.removeReservedJobTicketId(clientId, jobTicketIdOld)
                                            if jobTicketId:
                                                self.addReservedJobTicketId(clientId, jobTicketId)
                            action[name] = forceString(value)
            else:
                record.setValue(col.fieldName(), value)
            self.emitCellChanged(row, column)
            return True
        if role == Qt.CheckStateRole:
            column = index.column()
            row = index.row()
            state = value.toInt()[0]
            if row == len(self._items):
                if state == Qt.Unchecked:
                    return False
                record = self.getEmptyRecord()
                self._items.append(record, CAction(record=record))
                count = len(self._items)
                rootIndex = QModelIndex()
                self.beginInsertRows(rootIndex, count, count)
                self.insertRows(count, 1, rootIndex)
                self.endInsertRows()
            record, action = self._items[row]
            col = self._cols[column]
            record.setValue(col.fieldName(), QVariant(0 if state == Qt.Unchecked else 1))
            self.emitCellChanged(row, column)
            return True
        return False


    def setValue(self, row, fieldName, value):
        if 0<=row<len(self._items):
            record, action = self._items[row]
            valueAsVariant = toVariant(value)
            if record.value(fieldName) != valueAsVariant:
                record.setValue(fieldName, valueAsVariant)
                self.emitValueChanged(row, fieldName)


    def value(self, row, fieldName):
        if 0<=row<len(self._items):
            record, action = self._items[row]
            return record.value(fieldName)
        return None


    def sortData(self, column, ascending):
        pass


    def loadItems(self, operatingPlanDate, orgStructureIdList, isStrictDate=True, status=CActionStatus.appointed):
        self.operatingPlanDate = operatingPlanDate
        self._items = []
        self.removeActions = []
        self.actionList = {}
        self.removeReservedJobTickets()
        actionTypeIdList = getActionTypeIdListByFlatCode(u'moving%')
        db = QtGui.qApp.db
        table = self._table
        tableAT = db.table('ActionType')
        tableEvent = db.table('Event')
        tableClient = db.table('Client')
        queryTable = table.innerJoin(tableAT, tableAT['id'].eq(table['actionType_id']))
        queryTable = queryTable.innerJoin(tableEvent, tableEvent['id'].eq(table['event_id']))
        queryTable = queryTable.innerJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
        filter = [tableAT['deleted'].eq(0),
                  tableEvent['deleted'].eq(0),
                  tableClient['deleted'].eq(0),
                  tableAT['class'].eq(2),
                  tableAT['serviceType'].eq(CActionServiceType.operation),
                  #table['status'].inlist([CActionStatus.appointed, CActionStatus.started, CActionStatus.wait]) # Задача №0009410
                  ]
        if self.type:
            filter.append(table['plannedEndDate'].isNull())
            if isStrictDate:
                filter.append(table['directionDate'].dateEq(operatingPlanDate))
            else:
               filter.append(db.joinOr([table['directionDate'].isNull(), table['directionDate'].dateLe(operatingPlanDate)]))
            if status is not None:
                filter.append(table['status'].eq(status))
        else:
            filter.append(table['plannedEndDate'].isNotNull())
            filter.append(table['plannedEndDate'].eq(operatingPlanDate))
        if actionTypeIdList:
            filter.append(u'''EXISTS(SELECT A.id
            FROM Action AS A
            INNER JOIN Event AS E ON E.id = A.event_id
            WHERE E.client_id = Client.id AND A.deleted = 0 AND E.deleted = 0
            AND A.status = %s
            AND A.actionType_id IN (%s)
            AND A.begDate IS NOT NULL
            AND A.endDate IS NULL
            AND (Action.plannedEndDate IS NULL OR DATE(A.begDate) <= DATE(Action.plannedEndDate))
            %s
            )'''%(CActionStatus.started, ','.join(forceString(actionTypeId) for actionTypeId in actionTypeIdList if actionTypeId),
                 (u''' AND EXISTS(SELECT APOS2.value
    FROM ActionPropertyType AS APT2
    INNER JOIN ActionProperty AS AP2 ON AP2.type_id = APT2.id
    INNER JOIN ActionProperty_OrgStructure AS APOS2 ON APOS2.id = AP2.id
    INNER JOIN OrgStructure AS OS2 ON OS2.id = APOS2.value
    WHERE APT2.actionType_id = A.actionType_id AND AP2.action_id = A.id
    AND APT2.deleted=0 AND APT2.name %s AND OS2.deleted=0
    AND APOS2.value %s)'''%(updateLIKE(u'Отделение пребывания'), u' IN ('+(','.join(forceString(orgStructureId) for orgStructureId in orgStructureIdList))+')')) if orgStructureIdList else u''))
        if self._filter:
            filter.append(self._filter)
        if table.hasField('deleted'):
            filter.append(table['deleted'].eq(0))
        if self._idxFieldName:
            order = [self._idxFieldName, self._idFieldName]
        else:
            order = [self._idFieldName]
        records = db.getRecordList(queryTable, u'Action.*', filter, order)
        for record in records:
            actionId = forceRef(record.value('id'))
            action = CAction(record=record)
            actionType = action.getType()
            numberLine = -1
            for name, propertyType in actionType._propertiesByName.items():
                if propertyType.inPlanOperatingDay and numberPropertyColumnName == inPlanOperatingDay[propertyType.inPlanOperatingDay].lower():
                    numberLine = action[name]
            self.actionList[numberLine, actionId] = (record, action)
        keysLine = self.actionList.keys()
        keysLine.sort(key=lambda x: x[0])
        for keyLine in keysLine:
            self._items.append(self.actionList[keyLine])
        self.reset()
        self.setClientCache(CTableRecordCache(db, db.forceTable(tableClient), u'*', capacity=None))
        actionTypeIdStr = (','.join(str(actionTypeId) for actionTypeId in actionTypeIdList if actionTypeId))
        if actionTypeIdStr:
            stmt = u''', (SELECT OSP.name
                FROM Action AS A
                INNER JOIN ActionPropertyType AS APT ON APT.actionType_id = A.actionType_id
                INNER JOIN ActionProperty AS AP ON AP.type_id = APT.id
                INNER JOIN ActionProperty_OrgStructure_Placement AS APOS ON APOS.id = AP.id
                INNER JOIN OrgStructure_Placement as OSP on OSP.id = APOS.value
                WHERE A.event_id = Event.id
                AND A.deleted = 0
                AND A.endDate IS NULL
                AND A.actionType_id IN (%s)
                AND AP.action_id = A.id
                AND AP.deleted = 0
                AND APT.actionType_id = A.actionType_id
                AND APT.deleted = 0
                AND APT.name = 'Помещение'
                ORDER BY A.begDate DESC
                LIMIT 1) AS placement'''%(actionTypeIdStr)
        else:
            stmt = u''
        self.setEventCache(CTableRecordCache(db, db.forceTable(tableEvent), u'* %s'%(stmt), capacity=None))
        jobTicketData = {}
        for (record, action) in self._items:
            if record and action:
                eventId = forceRef(record.value('event_id'))
                if eventId and self.eventCache:
                    eventRecord = self.eventCache.get(eventId)
                    if eventRecord:
                        clientId = forceRef(eventRecord.value('client_id'))
                        jobTicketId = self.getJobTickedId(action)
                        if clientId and jobTicketId:
                            jobTicketLine = jobTicketData.get(clientId, [])
                            jobTicketLine.append(jobTicketId)
                            jobTicketData[clientId] = jobTicketLine
        self.addReservedJobTickets(jobTicketData)


    def saveItems(self, operatingPlanDate):
        actionIdList = []
        removeActions = set(self.removeActions)
        db = QtGui.qApp.db
        for idx, (record, action) in enumerate(self._items):
            eventId = forceRef(record.value('event_id'))
            if not action:
                action = CAction(record = record)
            actionType = action.getType()
            for name, propertyType in actionType._propertiesByName.items():
                if propertyType.inPlanOperatingDay and numberPropertyColumnName == inPlanOperatingDay[propertyType.inPlanOperatingDay].lower():
                    action[name] = idx + 1
            id = action.save(eventId)
            if id and id not in actionIdList:
                actionIdList.append(id)
            removeActions = removeActions - set([id])
        self.removeActions = list(removeActions)
        if self.removeActions:
            tableActionProperty = db.table('ActionProperty')
            filter = [tableActionProperty['action_id'].inlist(self.removeActions), tableActionProperty['deleted'].eq(0)]
            if actionIdList:
                filter.append(tableActionProperty['action_id'].notInlist(actionIdList))
            db.deleteRecord(tableActionProperty, filter)

            tableActionExecutionPlan = db.table('Action_ExecutionPlan')
            filter = [tableActionExecutionPlan['master_id'].inlist(self.removeActions), tableActionExecutionPlan['deleted'].eq(0)]
            if actionIdList:
                filter.append(tableActionExecutionPlan['master_id'].notInlist(actionIdList))
            db.deleteRecord(tableActionExecutionPlan, filter)

            tableAction = db.table('Action')
            tableStockMotion = db.table('StockMotion')
            tableActionNR = db.table('Action_NomenclatureReservation')
            filter = [tableActionNR['action_id'].inlist(self.removeActions)]
            if actionIdList:
                filter.append(tableActionNR['action_id'].notInlist(actionIdList))
            reservationIdList = db.getDistinctIdList(tableActionNR, [tableActionNR['reservation_id']], filter)
            if reservationIdList:
                filter = [tableStockMotion['id'].inlist(reservationIdList), tableStockMotion['deleted'].eq(0)]
                db.deleteRecord(tableStockMotion, filter)

            filter = [tableAction['id'].inlist(self.removeActions), tableAction['deleted'].eq(0)]
            if actionIdList:
                filter.append(tableAction['id'].notInlist(actionIdList))
            stockMotionIdList = db.getDistinctIdList(tableAction, [tableAction['stockMotion_id']], filter)
            if stockMotionIdList:
                tableStockMotionItem = db.table('StockMotion_Item')
                filter = [tableStockMotionItem['master_id'].inlist(stockMotionIdList), tableStockMotionItem['deleted'].eq(0)]
                db.deleteRecord(tableStockMotionItem, filter)
                filter = [tableStockMotion['id'].inlist(stockMotionIdList), tableStockMotion['deleted'].eq(0)]
                db.deleteRecord(tableStockMotion, filter)

            filter = [tableAction['id'].inlist(self.removeActions), tableAction['deleted'].eq(0)]
            if actionIdList:
                filter.append('NOT ('+tableAction['id'].inlist(actionIdList)+')')
            db.deleteRecord(tableAction, filter)

        self.removeActions = []
        self.removeReservedJobTickets()


class CPlanOperatingDayPage(CDialogBase, Ui_PlanOperatingDayPage):
    def __init__(self, parent=None, orgStructureId=None):
        CDialogBase.__init__(self, parent)
        self.setupOutsideOperatingDayMenu()
        self.setupUi(self)
        self.personsCache = CTableRecordCache(QtGui.qApp.db, 'vrbPersonWithSpeciality', '*')
        self.orgStructureId = orgStructureId
        self.lblOrgStructureName.setWordWrap(True)

        templates = getPrintTemplates(getPlanOperatingDayContext())
        if not templates:
            self.btnOperatingDayPrint.setId(-1)
        else:
            for template in templates:
                action = CPrintAction(template.name, template.id, self.btnOperatingDayPrint, self.btnOperatingDayPrint)
                self.btnOperatingDayPrint.addAction(action)
            self.btnOperatingDayPrint.menu().addSeparator()
            self.btnOperatingDayPrint.addAction(CPrintAction(u'Список План Операционного дня', -1, self.btnOperatingDayPrint, self.btnOperatingDayPrint))

        self.addModels('PlanOperatingDay', CPlanOperatingDayModel(self, 0, self.personsCache, clientCache=[], eventCache=[], orgStructureId=self.orgStructureId))
        self.addModels('OutsideOperatingDay', CPlanOperatingDayModel(self, 1, self.personsCache, clientCache=[], eventCache=[], orgStructureId=self.orgStructureId))
        self.tblPlanOperatingDay.setModel(self.modelPlanOperatingDay)
        self.tblOutsideOperatingDay.setModel(self.modelOutsideOperatingDay)

        self.tblPlanOperatingDay.addPopupDuplicateSelectRows()
        self.tblPlanOperatingDay.addPopupSeparator()
        self.tblPlanOperatingDay.addMoveRow()
        self.tblPlanOperatingDay.addPopupSeparator()
        self.tblPlanOperatingDay.addPopupSelectAllRow()
        self.tblPlanOperatingDay.addPopupClearSelectionRow()
        self.tblPlanOperatingDay.addPopupSeparator()
        self.tblPlanOperatingDay.addPopupDelRow()

        self.addPopupUpdateDateSurgery()
        self.tblOutsideOperatingDay.setPopupMenu(self.mnuOutsideOperatingDay)
        self.isDirty = False
        self.operatingPlanDate = QDate()
        self.eventIdList = None
        self.orgStructureIdList = []
        self.firstEntry = True
        self.edtOperatingPlanDate.setDate(QDate.currentDate().addDays(1))
        self.tblPlanOperatingDay.enableColsMove()
        self.cmbActionStatus.insertSpecialValue(u'не задано', None)
        self.setFilterOODVisible(self.tabWidget.currentIndex())
        self.on_btnReset_clicked()
        self.connect(self.modelPlanOperatingDay, SIGNAL('dataChanged(QModelIndex, QModelIndex)'), self.on_modelPlanOperatingDay_dataChanged)
        self.connect(self.tblPlanOperatingDay._popupMenu, SIGNAL('aboutToShow()'), self.on_mnuPlanOperatingDay_aboutToShow)
        self.firstEntry = False


    def addPopupUpdateDateSurgery(self):
        if self.tblPlanOperatingDay._popupMenu is None:
            self.tblPlanOperatingDay.createPopupMenu()
        self.actUpdateDateSurgery = QtGui.QAction(u'Изменить дату операции', self)
        self.actUpdateDateSurgery.setObjectName('actUpdateDateSurgery')
        self.tblPlanOperatingDay._popupMenu.addAction(self.actUpdateDateSurgery)
        self.connect(self.actUpdateDateSurgery, SIGNAL('triggered()'), self.updateDateSurgery)

        self.actOpenAction = QtGui.QAction(u'Открыть действие', self)
        self.actOpenAction.setObjectName('actOpenAction')
        self.tblPlanOperatingDay._popupMenu.addAction(self.actOpenAction)
        self.connect(self.actOpenAction, SIGNAL('triggered()'), self.openAction)

        self.actSurgeryStatusCanceled = QtGui.QAction(u'Статус Операции "Отменено"', self)
        self.actSurgeryStatusCanceled.setObjectName('actSurgeryStatusCanceled')
        self.tblPlanOperatingDay._popupMenu.addAction(self.actSurgeryStatusCanceled)
        self.connect(self.actSurgeryStatusCanceled, SIGNAL('triggered()'), self.surgeryStatusCanceled)

#        self.actUpdateAssistentList = QtGui.QAction(u'Изменить список Бригады', self)
#        self.actUpdateAssistentList.setObjectName('actUpdateAssistentList')
#        self.tblPlanOperatingDay._popupMenu.addAction(self.actUpdateAssistentList)
#        self.connect(self.actUpdateAssistentList, SIGNAL('triggered()'), self.updateAssistentList)


    def surgeryStatusCanceled(self):
        rows = self.tblPlanOperatingDay.getSelectedRows()
        for row in rows:
            self.isDirty = True
            record, action = self.modelPlanOperatingDay._items[row] if 0 <= row < len(self.modelPlanOperatingDay._items) else (None, None)
            if forceInt(record.value('status')) in [CActionStatus.appointed, CActionStatus.started, CActionStatus.wait]:
                record.setValue('status', toVariant(CActionStatus.canceled))
        self.modelPlanOperatingDay.reset()


    def openAction(self):
        row = self.tblPlanOperatingDay.currentIndex().row()
        record, action = self.modelPlanOperatingDay._items[row] if 0 <= row < len(self.modelPlanOperatingDay._items) else (None, None)
        actionTypeId = forceRef(record.value('actionType_id')) if record else None
        if actionTypeId:
            dialog = COperatingDayActionEditDialog(self)
            try:
                dialog.load(record, action)
                if dialog.exec_():
                    id = dialog.itemId()
                    if id:
                        db = QtGui.qApp.db
                        table = db.table('Action')
                        tableAT = db.table('ActionType')
                        queryTable = table.innerJoin(tableAT, tableAT['id'].eq(table['actionType_id']))
                        filter = [table['id'].eq(id),
                                  tableAT['deleted'].eq(0),
                                  tableAT['class'].eq(2),
                                  tableAT['serviceType'].eq(CActionServiceType.operation),
                                  #table['status'].inlist([CActionStatus.appointed, CActionStatus.started, CActionStatus.wait])
                                  ]
                        filter.append(table['plannedEndDate'].isNotNull())
                        filter.append(table['plannedEndDate'].eq(self.edtOperatingPlanDate.date()))
                        if self.modelPlanOperatingDay._filter:
                            filter.append(self.modelPlanOperatingDay._filter)
                        if table.hasField('deleted'):
                            filter.append(table['deleted'].eq(0))
                        if self.modelPlanOperatingDay._idxFieldName:
                            order = [self.modelPlanOperatingDay._idxFieldName, self.modelPlanOperatingDay._idFieldName]
                        else:
                            order = [self.modelPlanOperatingDay._idFieldName]
                        record = db.getRecordEx(queryTable, u'Action.*', filter, order)
                        self.modelPlanOperatingDay._items[row] = (record, CAction(record=record))
                        self.modelPlanOperatingDay.reset()
            finally:
                dialog.deleteLater()


    def getAssistentList(self, propertyName, fieldName):
        rows = self.tblPlanOperatingDay.getSelectedRows()
        if rows:
            self.getAssistentListRows(propertyName, rows, fieldName)
            self.modelPlanOperatingDay.reset()


    def getAssistentListRows(self, nameProperty, rows, fieldName):
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableClient = db.table('Client')
        table = tableEvent.innerJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
        row = rows[0]
        record, action = self.modelPlanOperatingDay._items[row]
        if forceRef(record.value('actionType_id')):
            eventId  = forceRef(record.value('event_id'))
            clientId = None
            clientSex = None
            clientAge = None
            if eventId:
                recordClient = db.getRecordEx(table,
                                              [tableClient['id'], tableClient['sex'], u'age(Client.birthDate, Event.setDate) AS clientAge'],
                                              [tableEvent['id'].eq(eventId), tableEvent['deleted'].eq(0)])
                if recordClient:
                    clientId = forceRef(recordClient.value('id'))
                    clientSex = forceInt(recordClient.value('sex'))
                    clientAge = forceInt(recordClient.value('clientAge'))
            dialog = COperatingAssistentsDialog(self, fieldName)
            try:
                dialog.tblAPProps.model().setAction(action, clientId, clientSex, clientAge, nameProperty)
                dialog.tblAPProps.model().reset()
                dialog.tblAPProps.resizeRowsToContents()
                if dialog.exec_():
                    action = dialog.getAction()
                    if action:
                        self.modelPlanOperatingDay._items[row] = (action.getRecord(), action)
                        self.isDirty = True
                        if len(rows) > 1:
                            rows = list(set(rows) - set([row]))
                            for row in rows:
                                recordEdit, actionEdit = self.modelPlanOperatingDay._items[row]
                                if actionEdit and forceRef(recordEdit.value('actionType_id')):
                                    for id in action._propertiesById:
                                        property = actionEdit.getPropertyById(id)
                                        if property.type().inPlanOperatingDay and nameProperty == inPlanOperatingDay[property.type().inPlanOperatingDay].lower():
                                            if property.type().valueType.isCopyable:
                                                property.copy(action._propertiesById[id])
                                    self.modelPlanOperatingDay._items[row] = (actionEdit.getRecord(), actionEdit)
            finally:
                dialog.deleteLater()


    @pyqtSignature('')
    def on_mnuPlanOperatingDay_aboutToShow(self):
        self.tblPlanOperatingDay.on_popupMenu_aboutToShow()
        rowCount = self.modelPlanOperatingDay.rowCount()
        row = self.tblPlanOperatingDay.currentIndex().row()
        self.actUpdateDateSurgery.setEnabled(0 <= row < rowCount)
        record, action = self.modelPlanOperatingDay._items[row] if 0 <= row < len(self.modelPlanOperatingDay._items) else (None, None)
        actionTypeId = forceRef(record.value('actionType_id')) if record else None
        self.actOpenAction.setEnabled(bool(0 <= row < rowCount and actionTypeId))
        #self.actUpdateAssistentList.setEnabled(bool(0 <= row < rowCount and actionTypeId))


    def updateDateSurgery(self):
        date = None
        rows = self.tblPlanOperatingDay.getSelectedRows()
        if rows:
            dialog = CUpdateDateSurgeryDialog(self)
            try:
                if dialog.exec_():
                    date = dialog.getCurrentDate()
                    if self.edtOperatingPlanDate.date() != date:
                        actionIdList = {}
                        for row in rows:
                            record, action = self.modelPlanOperatingDay._items[row]
                            if forceRef(record.value('actionType_id')):
                                record.setValue('plannedEndDate', toVariant(date))
                                eventId = forceRef(record.value('event_id'))
                                id = action.save(eventId)
                                actionIdList[row] = id
                        rows.reverse()
                        for row in rows:
                            if actionIdList[row]:
                                self.modelPlanOperatingDay.removeRow(row)
            finally:
                dialog.deleteLater()
        self.modelPlanOperatingDay.reset()


#    def updateAssistentList(self):
#        col = self.modelPlanOperatingDay._cols[self.tblPlanOperatingDay.currentIndex().column()]
#        self.getAssistentList(col.name, forceString(col._title))


    def setupOutsideOperatingDayMenu(self):
        self.addObject('mnuOutsideOperatingDay', QtGui.QMenu(self))
        self.addObject('actMovingToPlanDayRows', QtGui.QAction(u'Добавить в план', self))
        self.mnuOutsideOperatingDay.addAction(self.actMovingToPlanDayRows)


    @pyqtSignature('')
    def on_mnuOutsideOperatingDay_aboutToShow(self):
        rowCount = self.modelOutsideOperatingDay.rowCount()
        row = self.tblOutsideOperatingDay.currentIndex().row()
        self.actMovingToPlanDayRows.setEnabled(0<=row<rowCount)


    @pyqtSignature('')
    def on_actMovingToPlanDayRows_triggered(self):
        self.isDirty = True
        rows = self.tblOutsideOperatingDay.getSelectedRows()
        rows.sort(reverse=True)
        for row in rows:
            currentRecord, currentAction = self.modelOutsideOperatingDay._items[row]
            currentRecord.setValue('plannedEndDate', toVariant(self.edtOperatingPlanDate.date()))
            if currentAction:
                actionType = currentAction.getType()
                for name, propertyType in actionType._propertiesByName.items():
                    if propertyType.inPlanOperatingDay and numberPropertyColumnName == inPlanOperatingDay[propertyType.inPlanOperatingDay].lower():
                        currentAction[name] = len(self.modelPlanOperatingDay._items)
            self.modelPlanOperatingDay._items.append((currentRecord, currentAction))
            self.modelOutsideOperatingDay.removeRow(row)
        self.modelPlanOperatingDay.reset()
        self.modelOutsideOperatingDay.reset()


    @pyqtSignature('')
    def on_btnClose_clicked(self):
        self.close()


    @pyqtSignature('')
    def on_btnSave_clicked(self):
        if self.checkDataEntered():
            self.save()
            self.close()


    @pyqtSignature('')
    def on_btnSurgeryJournal_clicked(self):
        QtGui.qApp.setWaitCursor()
        try:
            surgeryJournalDialog = CSurgeryJournalDialog(self)
        finally:
            QtGui.qApp.restoreOverrideCursor()
        try:
            surgeryJournalDialog.exec_()
        finally:
            surgeryJournalDialog.deleteLater()


    @pyqtSignature('QDate')
    def on_edtOperatingPlanDate_dateChanged(self, date):
        if self.operatingPlanDate != date and not self.firstEntry:
            if self.canClose():
                self.isDirty = False
                self.modelPlanOperatingDay.saveItems(self.operatingPlanDate)
            self.modelPlanOperatingDay.loadItems(date, self.orgStructureIdList)
            isStrictDate, status = self.getFilterOODVisible()
            self.modelOutsideOperatingDay.loadItems(date, self.orgStructureIdList, isStrictDate, status)
            self.tblPlanOperatingDay.setRowHeightLoc()
            self.tblOutsideOperatingDay.setRowHeightLoc()
            self.operatingPlanDate = date
            index = self.tabWidget.currentIndex()
            table = self.tblPlanOperatingDay
            if index:
                table = self.tblOutsideOperatingDay
            if len(table.model().items()) > 0:
                table.setCurrentRow(0)
                self.setModifyInfo(index)
            else:
                self.lblCreatePerson.setText(u'Автор: ')
                self.lblModifyPerson.setText(u' Изменил: ')
                self.lblCreateDate.setText('')
                self.lblModifyDate.setText('')
            self.tblPlanOperatingDay.resizeRowsToContents()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelPlanOperatingDay_dataChanged(self, topLeft, bottomRight):
        self.isDirty = True
        row = self.tblPlanOperatingDay.currentIndex().row()
        column = self.tblPlanOperatingDay.currentIndex().column()
        col = self.modelPlanOperatingDay._cols[column]
        if col.fieldName() == 'actionType_id':
            record, action = self.modelPlanOperatingDay._items[row]
            actionTypeId = forceRef(record.value('actionType_id'))
            if not action and actionTypeId:
                action = CAction(record=record)
                if action:
                    actionType = action.getType()
                    for name, propertyType in actionType._propertiesByName.items():
                        if propertyType.inPlanOperatingDay and numberPropertyColumnName == inPlanOperatingDay[propertyType.inPlanOperatingDay].lower():
                            action[name] = row + 1
                        if propertyType.inPlanOperatingDay and medicalDiagnosisColumnName == inPlanOperatingDay[propertyType.inPlanOperatingDay].lower():
                            action[name] = self.getMedicalDiagnosisProperties(record)
                    self.modelPlanOperatingDay._items[row] = (record, action)
            elif action and actionTypeId:
                newAction = CAction(record=record)
                newAction.updateByAction(action)
                self.modelPlanOperatingDay._items[row] = (newAction.getRecord(), newAction)
                self.modelPlanOperatingDay.reset()
        elif column in [CPlanOperatingDayModel.Col_AssistantTeam, CPlanOperatingDayModel.Col_AnestesiaTeam, CPlanOperatingDayModel.Col_AssistantAnestesiaTeam]:
            record, action = self.modelPlanOperatingDay._items[row]
            actionTypeId = forceRef(record.value('actionType_id'))
            if actionTypeId:
                self.getAssistentList(col.name, forceString(col._title))
        self.tblPlanOperatingDay.setRowHeightLoc()
        self.tblPlanOperatingDay.resizeRowsToContents()


    def getMedicalDiagnosisProperties(self, record, customFilter = None):
        eventId = forceRef(record.value('event_id')) if record else None
        date = self.edtOperatingPlanDate.date()
        if eventId:
            db = QtGui.qApp.db
            actionTypeIdList = getActionTypeIdListByFlatCode(u'medicalDiagnosis%')
            if actionTypeIdList:
                table = db.table('Action')
                tableAT = db.table('ActionType')
                queryTable = table.innerJoin(tableAT, tableAT['id'].eq(table['actionType_id']))
                filter = [table['event_id'].eq(eventId),
                          tableAT['deleted'].eq(0),
                          table['deleted'].eq(0),
                          table['actionType_id'].inlist(actionTypeIdList)
                          ]
                if date:
                    filter.append(table['endDate'].le(date))
                if customFilter:
                    filter.append(customFilter)
                order = ['Action.endDate DESC']
                recordAction = db.getRecordEx(queryTable, u'Action.*', filter, order)
                if recordAction:
                    action = CAction(record=recordAction)
                    if action:
                        actionType = action.getType()
                        properties = []
                        for name, propertyType in actionType._propertiesByName.items():
                            if propertyType.inMedicalDiagnosis and inMedicalDiagnosis[propertyType.inMedicalDiagnosis].lower() in medicalDiagnosisType:
                                properties.append((propertyType, action[name]))
                        properties.sort(key=lambda prop:prop[0].idx)
                        return '\n'.join(((forceString(properti[0].name) + u'. ' + forceString(properti[1])) if properti[1] else u'') for properti in properties)
            stmt = u'''SELECT APS.value
                       FROM Action
                            INNER JOIN ActionPropertyType AS APT ON APT.actionType_id = Action.actionType_id
                            INNER JOIN ActionProperty AS AP ON AP.type_id = APT.id
                            INNER JOIN ActionProperty_String AS APS ON APS.id = AP.id
                       WHERE Action.event_id = %s
                            AND Action.deleted = 0
                            %s
                            AND APT.inMedicalDiagnosis > 0
                            AND AP.action_id = Action.id
                            AND APT.deleted = 0
                            %s
                       ORDER BY Action.endDate DESC '''%(eventId, (u' AND DATE(Action.endDate) <= %s'%db.formatDate(date)) if date else u'', (u' AND %s'%customFilter) if customFilter else u'')
            query = db.query(stmt)
            if query.first():
                recordAction = query.record()
                return forceString(recordAction.value('value'))
        return u''


    @pyqtSignature('QModelIndex')
    def on_tblPlanOperatingDay_clicked(self, index):
        row = index.row()
        record, action = self.modelPlanOperatingDay._items[row]
        self.updateModifyInfo(record)


    @pyqtSignature('QModelIndex')
    def on_tblPlanOperatingDay_doubleClicked(self, index):
        if index.isValid():
            row = index.row()
            column = index.column()
            record, action = self.modelPlanOperatingDay._items[row]
            if column in [CPlanOperatingDayModel.Col_MedicalDiagnosis, ]:
                actionTypeId = forceRef(record.value('actionType_id'))
                if actionTypeId and action:
                    eventId  = forceRef(record.value('event_id'))
                    self.getOperatingMedicalDiagnosis(eventId, self.edtOperatingPlanDate.date(), record, action, self.modelPlanOperatingDay._cols[column], row)
                    self.tblPlanOperatingDay.resizeRowsToContents()
            self.updateModifyInfo(record)


    def getOperatingMedicalDiagnosis(self, eventId, date, record, action, col, row):
        def setMedicalDiagnosisText(text):
            if text is not None and action:
                actionType = action.getType()
                for name, propertyType in actionType._propertiesByName.items():
                    if propertyType.inPlanOperatingDay and col.name.lower() == inPlanOperatingDay[propertyType.inPlanOperatingDay].lower():
                        action[name] = forceString(text)
                        break
                self.modelPlanOperatingDay._items[row] = (action.getRecord(), action)
                self.isDirty = True
                self.modelPlanOperatingDay.reset()
                self.tblPlanOperatingDay.setRowHeightLoc()
        if eventId:
            dialog = COperatingMedicalDiagnosisDialog(self, eventId, date)
            try:
                self.connect(dialog, SIGNAL('medicalDiagnosisSelected(QString)'), setMedicalDiagnosisText)
                dialog.exec_()
            finally:
                dialog.deleteLater()


    @pyqtSignature('QModelIndex')
    def on_tblOutsideOperatingDay_clicked(self, index):
        row = index.row()
        record, action = self.modelOutsideOperatingDay._items[row]
        self.updateModifyInfo(record)


    def updateModifyInfo(self, record):
        if record:
            createDatetime = forceString(record.value('createDatetime'))
            createPersonId = forceRef(record.value('createPerson_id'))
            createPerson = self.personsCache.get(createPersonId) if createPersonId else u''
            modifyDatetime = forceString(record.value('modifyDatetime'))
            modifyPersonId = forceRef(record.value('modifyPerson_id'))
            modifyPerson = self.personsCache.get(modifyPersonId) if modifyPersonId else u''
            self.lblCreatePerson.setText(u'Автор: ' + (forceString(createPerson.value('name')) if createPerson else u''))
            self.lblModifyPerson.setText(u' Изменил: ' + (forceString(modifyPerson.value('name')) if modifyPerson else u''))
            self.lblCreateDate.setText(createDatetime)
            self.lblModifyDate.setText(modifyDatetime)
        else:
            self.lblCreatePerson.setText(u'Автор: ')
            self.lblModifyPerson.setText(u' Изменил: ')
            self.lblCreateDate.setText('')
            self.lblModifyDate.setText('')


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelOutsideOperatingDay_dataChanged(self, topLeft, bottomRight):
        self.tblOutsideOperatingDay.setRowHeightLoc()


    def closeEvent(self, event):
        if self.canClose():
            self.isDirty = False
            self.modelPlanOperatingDay.saveItems(self.edtOperatingPlanDate.date())
        QtGui.QDialog.closeEvent(self, event)


    def canClose(self):
        if self.isDirty:
            res = QtGui.QMessageBox.warning( self,
                                      u'Внимание!',
                                      u'Данные были изменены.\nСохранить изменения в текущей таблице?',
                                      QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                      QtGui.QMessageBox.Yes)
            if res == QtGui.QMessageBox.Yes:
                self.isDirty = False
                return True
        return False


    def destroy(self):
        pass


    def load(self, eventIdList, orgStructureId):
        self.eventIdList = eventIdList
        self.orgStructureId = orgStructureId
        self.orgStructureIdList = QtGui.qApp.db.getDescendants('OrgStructure', 'parent_id', orgStructureId) if orgStructureId else []
        self.modelPlanOperatingDay.loadItems(self.edtOperatingPlanDate.date(), self.orgStructureIdList)
        isStrictDate, status = self.getFilterOODVisible()
        self.modelOutsideOperatingDay.loadItems(self.edtOperatingPlanDate.date(), self.orgStructureIdList, isStrictDate, status)
        self.lblOrgStructureName.setText(u'Текущее подразделение: ' + (getOrgStructureFullName(orgStructureId) if orgStructureId else u'ЛПУ'))
        self.tblPlanOperatingDay.setRowHeightLoc()
        self.tblOutsideOperatingDay.setRowHeightLoc()
        index = self.tabWidget.currentIndex()
        table = self.tblPlanOperatingDay
        if index:
            table = self.tblOutsideOperatingDay
        if len(table.model().items()) > 0:
            table.setCurrentRow(0)
            self.setModifyInfo(index)


    def checkDataEntered(self):
        result = True
        for row, (record, action) in enumerate(self.modelPlanOperatingDay.items()):
            if not forceRef(record.value('actionType_id')):
                return CDialogBase(self).checkValueMessage(u'Не заполнен Тип действия', False, self.tblPlanOperatingDay, row, self.modelPlanOperatingDay.getColIndex('actionType_id', 0))
            if not action:
                return CDialogBase(self).checkValueMessage(u'Некорректно заведено действие', False, self.tblPlanOperatingDay, row, self.modelPlanOperatingDay.getColIndex('actionType_id', 0))
            if action:
                actionType = action.getType()
                for name, propertyType in actionType._propertiesByName.items():
                    if propertyType.inPlanOperatingDay and medicalDiagnosisColumnName == inPlanOperatingDay[propertyType.inPlanOperatingDay].lower():
                        if not action[name]:
                            if not CDialogBase(self).checkValueMessage(u'Не заполнен Предоперационный диагноз', True, self.tblPlanOperatingDay, row, self.modelPlanOperatingDay.Col_MedicalDiagnosis):
                                return False
                            else:
                                result = True
            if not forceRef(record.value('person_id')):
                if not CDialogBase(self).checkValueMessage(u'Не заполнен Оператор', True, self.tblPlanOperatingDay, row, self.modelPlanOperatingDay.getColIndex('person_id', 0)):
                    return False
                else:
                    result = True
#            if not forceRef(record.value('assistant_id')):
#                if not CDialogBase(self).checkValueMessage(u'Не заполнен Ассистент', True, self.tblPlanOperatingDay, row, self.modelPlanOperatingDay.getColIndex('assistant_id', 0)):
#                    return False
#                else:
#                    result = True
        return result


    def save(self):
        self.isDirty = False
        self.modelPlanOperatingDay.saveItems(self.edtOperatingPlanDate.date())


    @pyqtSignature('')
    def on_btnAddRecords_clicked(self):
        self.operatingPlanDate = self.edtOperatingPlanDate.date()
        items = self.modelPlanOperatingDay.items()
        db = QtGui.qApp.db
        table = db.table('Action')
        for masterId in self.eventIdList:
            record = table.newRecord()
            record.setValue('id', toVariant(None))
            record.setValue('createPerson_id', toVariant(QtGui.qApp.userId))
            record.setValue('createDatetime', toVariant(QDateTime.currentDateTime()))
            record.setValue('modifyPerson_id', toVariant(QtGui.qApp.userId))
            record.setValue('modifyDatetime', toVariant(QDateTime.currentDateTime()))
            record.setValue('event_id', toVariant(masterId))
            record.setValue('setPerson_id', toVariant(QtGui.qApp.userId))
            record.setValue('directionDate', toVariant(QDateTime.currentDateTime()))
            record.setValue('plannedEndDate', toVariant(self.operatingPlanDate))
            record.setValue('actionType_id', toVariant(None))
            record.setValue('begDate', toVariant(self.operatingPlanDate))
            record.setValue('status', toVariant(CActionStatus.appointed))
            record.setValue('org_id',  toVariant(QtGui.qApp.currentOrgId()))
            record.setValue('amount',  toVariant(1))
            items.append((record, None))
        self.modelPlanOperatingDay.reset()
        self.isDirty = True
        index = self.tabWidget.currentIndex()
        table = self.tblPlanOperatingDay
        if index:
            table = self.tblOutsideOperatingDay
        if len(table.model().items()) > 0:
            currentIndex = table.currentIndex()
            table.setCurrentRow(currentIndex.row() if currentIndex.isValid() else 0)
            self.setModifyInfo(index)
        self.tblPlanOperatingDay.resizeRowsToContents()


    @pyqtSignature('int')
    def on_tabWidget_currentChanged(self, index):
        self.setFilterOODVisible(index)
        self.setModifyInfo(index)


    @pyqtSignature('')
    def on_btnReset_clicked(self):
        self.chkStrictDate.setChecked(True)
        self.cmbActionStatus.setValue(CActionStatus.appointed)


    @pyqtSignature('')
    def on_btnApply_clicked(self):
        isStrictDate, status = self.getFilterOODVisible()
        QtGui.qApp.callWithWaitCursor(self, self.modelOutsideOperatingDay.loadItems, self.edtOperatingPlanDate.date(), self.orgStructureIdList, isStrictDate, status)
        self.tblOutsideOperatingDay.setRowHeightLoc()
        if len(self.tblOutsideOperatingDay.model().items()) > 0:
            self.tblOutsideOperatingDay.setCurrentRow(0)
            self.setModifyInfo(self.tabWidget.currentIndex())


    def setFilterOODVisible(self, index):
        self.chkStrictDate.setVisible(bool(index))
        self.lblActionStatus.setVisible(bool(index))
        self.cmbActionStatus.setVisible(bool(index))
        self.btnReset.setVisible(bool(index))
        self.btnApply.setVisible(bool(index))
        self.lblLine.setVisible(bool(index))
        self.lblFilter1.setVisible(bool(index))
        self.lblFilter2.setVisible(bool(index))


    def getFilterOODVisible(self):
        isStrictDate = self.chkStrictDate.isChecked() if self.chkStrictDate.isVisible() else True
        status = self.cmbActionStatus.value() if self.cmbActionStatus.isVisible() else CActionStatus.appointed
        return isStrictDate, status


    def setModifyInfo(self, index):
        table = self.tblPlanOperatingDay
        if index:
            table = self.tblOutsideOperatingDay
        currentIndex = table.currentIndex()
        if currentIndex.isValid():
            row = currentIndex.row()
            record, action = table.model()._items[row]
            self.updateModifyInfo(record)


    @pyqtSignature('int')
    def on_btnOperatingDayPrint_printByTemplate(self, templateId):
        widgetIndex = self.tabWidget.currentIndex()
        if widgetIndex == 0:
            model = self.modelPlanOperatingDay
        else:
            model = self.modelOutsideOperatingDay
        if templateId == -1:
            doc = QtGui.QTextDocument()
            cursor = QtGui.QTextCursor(doc)
            cursor.setCharFormat(CReportBase.ReportTitle)
            cursor.insertText(u'План операционного дня %s'%(self.edtOperatingPlanDate.date().toString('dd.MM.yyyy')))
            cursor.setCharFormat(CReportBase.ReportBody)
            cursor.insertBlock()
            cursor.insertText(u'Отчёт составлен: ' + forceString(QDateTime.currentDateTime()))
            cursor.insertBlock()
            colWidths  = [ self.tblPlanOperatingDay.columnWidth(i) for i in xrange(model.columnCount()) ]
            totalWidth = sum(colWidths)
            tableColumns = []
            for iCol, colWidth in enumerate(colWidths):
                widthInPercents = str(max(1, colWidth*90/totalWidth))+'%'
                tableColumns.append((widthInPercents, [forceString(model._cols[iCol].title())], CReportBase.AlignLeft))
            table = createTable(cursor, tableColumns)
            for iModelRow in xrange(model.rowCount()):
                iTableRow = table.addRow()
                for iModelCol in xrange(model.columnCount()):
                    index = model.createIndex(iModelRow, iModelCol)
                    text = forceString(model.data(index))
                    table.setText(iTableRow, iModelCol, text)
            html = doc.toHtml('utf-8')
            view = CReportViewDialog(self)
            view.setOrientation('LANDSCAPE')
            view.setText(html)
            view.exec_()
        else:
            context = CInfoContext()
            data = { 'actions': CPlanOperatingDayInfoList(context, [model], None) }
            QtGui.qApp.call(self, applyTemplate, (self, templateId, data))


class CUpdateDateSurgeryDialog(QtGui.QDialog, Ui_UpdateDateSurgeryDialog):
    def __init__(self,  parent):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.currentDate = None


    def getCurrentDate(self):
        return self.currentDate


    def setCurrentDate(self, date):
        self.currentDate = date


    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Ok:
            self.setCurrentDate(self.edtSurgeryDate.date())
        elif buttonCode == QtGui.QDialogButtonBox.Cancel:
            self.close()


class COperatingDayActionEditDialog(CActionEditDialog):
    def __init__(self, parent):
        CActionEditDialog.__init__(self, parent)


    def load(self, record, action):
        self.action = action
        self.setRecord(record)
        self.setIsDirty(False)


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        self.eventId = forceRef(record.value('event_id'))
        self.eventTypeId = forceRef(QtGui.qApp.db.translate('Event', 'id', self.eventId, 'eventType_id'))
        self.eventSetDate = forceDate(QtGui.qApp.db.translate('Event', 'id', self.eventId, 'setDate'))
        self.idx = forceInt(record.value('idx'))
        self.clientId = self.getClientId(self.eventId)
        actionType = self.action.getType()
        setActionPropertiesColumnVisible(actionType, self.tblProps)
        showTime = actionType.showTime
        self.edtDirectionTime.setVisible(showTime)
        self.edtPlannedEndTime.setVisible(showTime)
        self.edtCoordTime.setVisible(showTime)
        self.edtBegTime.setVisible(showTime)
        self.edtEndTime.setVisible(showTime)
        self.lblAssistant.setVisible(actionType.hasAssistant)
        self.cmbAssistant.setVisible(actionType.hasAssistant)
        self.setWindowTitle(actionType.code + '|' + actionType.name)
        setCheckBoxValue(self.chkIsUrgent, record, 'isUrgent')
        setDatetimeEditValue(self.edtDirectionDate,    self.edtDirectionTime,    record, 'directionDate')
        setDatetimeEditValue(self.edtPlannedEndDate,   self.edtPlannedEndTime,   record, 'plannedEndDate')
        setDatetimeEditValue(self.edtCoordDate, self.edtCoordTime, record, 'coordDate')
        setLabelText( self.lblCoordText, record, 'coordText')
        setDatetimeEditValue(self.edtBegDate,          self.edtBegTime,          record, 'begDate')
        setDatetimeEditValue(self.edtEndDate,          self.edtEndTime,          record, 'endDate')
        setRBComboBoxValue(self.cmbStatus,      record, 'status')
        setDoubleBoxValue(self.edtAmount,       record, 'amount')
        setDoubleBoxValue(self.edtUet,          record, 'uet')
        setRBComboBoxValue(self.cmbPerson,      record, 'person_id')
        setRBComboBoxValue(self.cmbSetPerson,   record, 'setPerson_id')
        setLineEditValue(self.edtOffice,        record, 'office')
        setRBComboBoxValue(self.cmbAssistant,   record, 'assistant_id')
        setLineEditValue(self.edtNote,          record, 'note')
        self.edtDuration.setValue(forceInt(record.value('duration')))
        self.edtPeriodicity.setValue(forceInt(record.value('periodicity')))
        self.edtAliquoticity.setValue(forceInt(record.value('aliquoticity')))

        mkbVisible = bool(actionType.defaultMKB)
        mkbEnabled = actionType.defaultMKB in (CActionType.dmkbByFinalDiag,
                                               CActionType.dmkbBySetPersonDiag,
                                               CActionType.dmkbUserInput
                                              )
        self.cmbMKB.setVisible(mkbVisible)
        self.lblMKB.setVisible(mkbVisible)
        self.cmbMKB.setEnabled(mkbEnabled)
        self.cmbMKB.setText(forceString(record.value('MKB')))

        morphologyMKBVisible = mkbVisible and QtGui.qApp.defaultMorphologyMKBIsVisible()
        self.cmbMorphologyMKB.setVisible(morphologyMKBVisible)
        self.lblMorphologyMKB.setVisible(morphologyMKBVisible)
        self.cmbMorphologyMKB.setEnabled(mkbEnabled)
        self.cmbMorphologyMKB.setText(forceString(record.value('morphologyMKB')))

        self.cmbOrg.setValue(forceRef(record.value('org_id')))
        if (self.cmbPerson.value() is None
                and actionType.defaultPersonInEditor in (CActionType.dpUndefined, CActionType.dpCurrentUser, CActionType.dpCurrentMedUser)
                and QtGui.qApp.userSpecialityId):
            self.cmbPerson.setValue(QtGui.qApp.userId)

        self.setPersonId(self.cmbPerson.value())
        self.updateClientInfo()

        self.modelActionProperties.setAction(self.action, self.clientId, self.clientSex, self.clientAge, self.eventTypeId)
        self.modelActionProperties.reset()
        self.tblProps.resizeRowsToContents()

        context = actionType.context if actionType else ''
        customizePrintButton(self.btnPrint, context)
        self.btnAttachedFiles.setAttachedFileItemList(self.action.getAttachedFileItemList())
        self.btnAttachedFiles.setAction(self.action)

        if QtGui.qApp.userHasRight(urLoadActionTemplate) and (self.cmbStatus.value() != CActionStatus.finished
                                                              or not self.cmbPerson.value()
                                                              or QtGui.qApp.userId == self.cmbPerson.value()
                                                              or (QtGui.qApp.userHasRight(urEditOtherPeopleActionSpecialityOnly) and QtGui.qApp.userSpecialityId == self.getSpecialityId(self.cmbPerson.value()))
                                                              or QtGui.qApp.userHasRight(urEditOtherpeopleAction)):
            actionTemplateTreeModel = self.actionTemplateCache.getModel(actionType.id)
            self.btnLoadTemplate.setModel(actionTemplateTreeModel)
        else:
            self.btnLoadTemplate.setEnabled(False)
        self.btnSaveAsTemplate.setEnabled(QtGui.qApp.userHasRight(urSaveActionTemplate))
        self.edtDuration.setEnabled(QtGui.qApp.userHasRight(urCopyPrevAction)
                                    and QtGui.qApp.userId == self.cmbSetPerson.value()
                                    and not self.action.getExecutionPlan()
                                    and self.cmbStatus.value() in (CActionStatus.started, CActionStatus.appointed)
                                    and not self.edtEndDate.date())
        self.edtPeriodicity.setEnabled(QtGui.qApp.userHasRight(urCopyPrevAction)
                                       and QtGui.qApp.userId == self.cmbSetPerson.value()
                                       and not self.action.getExecutionPlan()
                                       and self.cmbStatus.value() in (CActionStatus.started, CActionStatus.appointed)
                                       and not self.edtEndDate.date())
        self.edtAliquoticity.setEnabled(QtGui.qApp.userHasRight(urCopyPrevAction)
                                        and QtGui.qApp.userId == self.cmbSetPerson.value()
                                        and not self.action.getExecutionPlan()
                                        and self.cmbStatus.value() in (CActionStatus.started, CActionStatus.appointed)
                                        and not self.edtEndDate.date())

        canEdit = not self.action.isLocked() if self.action else True
        for widget in (self.edtPlannedEndDate, self.edtPlannedEndTime,
                       self.cmbStatus, self.edtBegDate, self.edtBegTime,
                       self.edtEndDate, self.edtEndTime,
                       self.cmbPerson, self.edtOffice,
                       self.cmbAssistant,
                       self.edtUet,
                       self.edtNote, self.cmbOrg,
                       self.buttonBox.button(QtGui.QDialogButtonBox.Ok)
                      ):
                widget.setEnabled(canEdit)
        self.edtAmount.setEnabled(actionType.amountEvaluation == 0 and canEdit)
        if not QtGui.qApp.userHasRight(urLoadActionTemplate) and not (self.cmbStatus.value() != CActionStatus.finished
                                                                      or not self.cmbPerson.value()
                                                                      or QtGui.qApp.userId == self.cmbPerson.value()
                                                                      or (QtGui.qApp.userHasRight(urEditOtherPeopleActionSpecialityOnly) and QtGui.qApp.userSpecialityId == self.getSpecialityId(self.cmbPerson.value()))
                                                                      or QtGui.qApp.userHasRight(urEditOtherpeopleAction)) and not canEdit:
            self.btnLoadTemplate.setEnabled(False)

        canEditPlannedEndDate = canEdit and actionType.defaultPlannedEndDate not in (CActionType.dpedBegDatePlusAmount,
                                                                                     CActionType.dpedBegDatePlusDuration)
        self.edtPlannedEndDate.setEnabled(canEditPlannedEndDate)
        self.edtPlannedEndTime.setEnabled(canEditPlannedEndDate and bool(self.edtPlannedEndDate.date()))

        btnNextActionEnabled = (self.edtDuration.value() > 1 or self.edtAliquoticity.value() > 1) and not self.edtEndDate.date()

        self.btnNextAction.setEnabled(btnNextActionEnabled)

        if self.edtDuration.value() > 0:
            self.btnPlanNextAction.setEnabled(True)
        else:
            self.btnPlanNextAction.setEnabled(False)
        self.on_edtDuration_valueChanged(forceInt(record.value('duration')))
        self.edtBegTime.setEnabled(bool(self.edtBegDate.date()) and canEdit)
        self.edtEndTime.setEnabled(bool(self.edtEndDate.date()) and canEdit)
        self.edtPlannedEndTime.setEnabled(bool(self.edtPlannedEndDate.date()) and canEdit)
        if not self.action.nomenclatureExpense:
            self.btnAPNomenclatureExpense.setVisible(False)
        elif not QtGui.qApp.userHasAnyRight([urCanUseNomenclatureButton]):
            self.btnAPNomenclatureExpense.setEnabled(False)
        self.setActionCoordinationEnable(actionType.isRequiredCoordination)


    def getSpecialityId(self, personId):
        specialityId = None
        if personId:
            db = QtGui.qApp.db
            tablePerson = db.table('Person')
            record = db.getRecordEx(tablePerson, [tablePerson['speciality_id']], [tablePerson['deleted'].eq(0), tablePerson['id'].eq(personId)])
            specialityId = forceRef(record.value('speciality_id')) if record else None
        return specialityId


    def save(self):
        try:
            prevId = self.itemId()
            db = QtGui.qApp.db
            db.transaction()
            try:
                self.action._record = self.getRecord()
                id = self.saveInternals(None)
                db.commit()
            except:
                db.rollback()
                self.setItemId(prevId)
                raise
            self.setItemId(id)
            self.afterSave()
            return id
        except Exception, e:
            QtGui.qApp.logCurrentException()
            QtGui.QMessageBox.critical( self,
                                        u'',
                                        exceptionToUnicode(e),
                                        QtGui.QMessageBox.Close)
            return None


def getPlanOperatingDayContext():
    return ['planOperatingDay']

