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
from PyQt4.QtCore import QVariant, QDateTime, Qt

from library.InDocTable       import CMKBListInDocTableModel, CBoolInDocTableCol, CInDocTableCol, CRBInDocTableCol, CDateInDocTableCol, CDateTimeInDocTableCol, CEnumInDocTableCol
from library.ItemsListDialog  import CItemEditorBaseDialog
from library.ICDInDocTableCol import CICDExInDocTableCol
from library.crbcombobox      import CRBComboBox
from library.Utils            import forceRef, forceString, forceStringEx, toVariant, forceDate, formatSex, formatName, forceBool, forceTime

from Ui_ProphylaxisPlanningEditor import Ui_ProphylaxisPlanningEditor


class CProphylaxisPlanningEditor(CItemEditorBaseDialog, Ui_ProphylaxisPlanningEditor):
    def __init__(self,  parent):
        CItemEditorBaseDialog.__init__(self, parent, 'ProphylaxisPlanning')
        self.addModels('Prophylaxis', CProphylaxisModel(self))
        self.setupUi(self)
        self.setWindowTitleEx(u'Редактор Журнала планирования профилактического наблюдения')
        self.setModels(self.tblProphylaxis, self.modelProphylaxis, self.selectionModelProphylaxis)
        self.setupDirtyCather()
        self.isLUDSelected = True
        self.clientId = None


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        code = forceString(QtGui.qApp.db.translate('rbProphylaxisPlanningType', 'id', toVariant(record.value('prophylaxisPlanningType_id')), 'code'))
        if code == u'ДН':
            self.tblProphylaxis.setColumnHidden(self.modelProphylaxis.Col_BegDate, True)
            columnEndDate = self.modelProphylaxis.cols()[self.modelProphylaxis.getColIndex('endDate')]
            columnEndDate.setTitle(u'Дата запланированной явки')
        self.modelProphylaxis.loadItems(self.itemId())
        self.clientId = forceRef(record.value('client_id'))


    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        return record


    def saveInternals(self, id):
        self.modelProphylaxis.saveItems(id)


    def checkDataEntered(self):
        result = True
        return result


class CLocClientCacheColumn(CInDocTableCol):
    def __init__(self, title, fieldName, width, **params):
        CInDocTableCol.__init__(self, title, fieldName, width, **params)
        self.clientCache = {}

    def getClientString(self, clientId):
        return QVariant()

    def toString(self, val, record):
        clientId  = forceRef(val)
        if clientId:
            if clientId in self.clientCache:
                return self.getClientString(clientId)
            else:
                db = QtGui.qApp.db
                table = db.table('Client')
                cols = [table['id'],
                        table['lastName'],
                        table['firstName'],
                        table['patrName'],
                        table['birthDate'],
                        table['sex']
                        ]
                record = db.getRecordEx(table, cols, [table['id'].eq(clientId)])
                if record:
                    self.clientCache[clientId] = record
                    return self.getClientString(clientId)
        return QVariant()


class CProphylaxisModel(CMKBListInDocTableModel):
    class CLocClientColumn(CLocClientCacheColumn):
        def __init__(self, title, fieldName, width, **params):
            CLocClientCacheColumn.__init__(self, title, fieldName, width, **params)

        def getClientString(self, clientId):
            clientRecord = self.clientCache.get(clientId, None)
            if clientRecord:
                name  = formatName(clientRecord.value('lastName'),
                                   clientRecord.value('firstName'),
                                   clientRecord.value('patrName'))
                return toVariant(name)
            return QVariant()

    class CLocClientBirthDateColumn(CLocClientCacheColumn):
        def __init__(self, title, fieldName, width, **params):
            CLocClientCacheColumn.__init__(self, title, fieldName, width, **params)

        def getClientString(self, clientId):
            clientRecord = self.clientCache.get(clientId, None)
            if clientRecord:
                return toVariant(forceString(clientRecord.value('birthDate')))
            return QVariant()

    class CLocClientSexColumn(CLocClientCacheColumn):
        def __init__(self, title, fieldName, width,  **params):
            CLocClientCacheColumn.__init__(self, title, fieldName, width, **params)

        def getClientString(self, clientId):
            clientRecord = self.clientCache.get(clientId, None)
            if clientRecord:
                return toVariant(formatSex(clientRecord.value('sex')))
            return QVariant()

    class CScheduleInDocTableCol(CInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.recordCache = {}

        def getScheduleRecord(self, clientId):
            db = QtGui.qApp.db
            tableScheduleItem = db.table('Schedule_Item')
            tableSchedule = db.table('Schedule')
            tablePerson = db.table('vrbPersonWithSpeciality')
            tableOrgStructure = db.table('OrgStructure')
            cols = ['Schedule_Item.id',
                    'Schedule_Item.client_id',
                    'Schedule_Item.time',
                    'Schedule.date',
                    'OrgStructure.name AS osName',
                    'vrbPersonWithSpeciality.name AS personName',
                    '(Schedule_Item.deleted OR Schedule.deleted) AS deleted'
                   ]
            cond = [tableSchedule['id'].eq(tableScheduleItem['master_id']),
                    tableScheduleItem['deleted'].eq(0),
                    tableScheduleItem['client_id'].eq(clientId),
                    tableSchedule['deleted'].eq(0)
                    ]
            table = tableScheduleItem.innerJoin(tableSchedule, db.joinAnd(cond))
            table = table.innerJoin(tablePerson, tablePerson['id'].eq(tableSchedule['person_id']))
            table = table.innerJoin(tableOrgStructure, tableOrgStructure['id'].eq(tablePerson['orgStructure_id']))
            records = db.getRecordList(table, cols)
            for record in records:
                appointmentId = forceRef(record.value('id'))
                if appointmentId:
                    self.recordCache[appointmentId] = record

        def getAppointmentString(self, clientId, appointmentId):
            record = self.recordCache.get(appointmentId, None)
            if record and not forceBool(record.value('deleted')) and clientId == forceRef(record.value('client_id')):
                date = forceDate(record.value('date'))
                time = forceTime(record.value('time'))
                personName = forceString(record.value('personName'))
                return toVariant(forceString(QDateTime(date, time))+' '+personName)
            return QVariant()

        def toString(self, val, record):
            clientId = forceRef(record.value('client_id'))
            appointmentId = forceRef(record.value('appointment_id'))
            if clientId and appointmentId:
                if appointmentId in self.recordCache.key():
                    return self.getAppointmentString(clientId, appointmentId)
                else:
                    self.getScheduleRecord(clientId)
                    if appointmentId in self.recordCache.key():
                        return self.getAppointmentString(clientId, appointmentId)
            return QVariant()


    class CVisitInDocTableCol(CInDocTableCol):
        def __init__(self, title, fieldName, width, **params):
            CInDocTableCol.__init__(self, title, fieldName, width, **params)
            self.caches = {}
            self.MKBCaches = {}

        def toString(self, val, record):
            visitId = forceRef(val)
            date = u''
            db = QtGui.qApp.db
            if visitId:
                visitRecord = self.caches.get(visitId, None)
                if not visitRecord:
                    table = db.table('Visit')
                    visitRecord = db.getRecordEx(table, '*', [table['id'].eq(visitId)])
                if visitRecord:
                    date = forceStringEx(forceDate(visitRecord.value('date')))
                self.caches[visitId] = visitRecord
                MKBRecord = self.MKBCaches.get(visitId, None)
                if not MKBRecord:
                    MKB = forceStringEx(record.value('MKB'))
                    if MKB:
                        table = db.table('Visit')
                        tableEvent = db.table('Event')
                        tableDiagnosis = db.table('Diagnosis')
                        tableDiagnostic = db.table('Diagnostic')
                        tableDispanser = db.table('rbDispanser')
                        queryTable = tableEvent.innerJoin(table, table['event_id'].eq(tableEvent['id']))
                        queryTable = queryTable.innerJoin(tableDiagnostic, tableDiagnostic['event_id'].eq(tableEvent['id']))
                        queryTable = queryTable.innerJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
                        queryTable = queryTable.innerJoin(tableDispanser, tableDispanser['id'].eq(tableDiagnostic['dispanser_id']))
                        cond = [table['id'].eq(visitId),
                                db.joinOr([tableDiagnosis['MKB'].eq(MKB), tableDiagnosis['MKB'].like(MKB[:3]+'%')]),
                                tableDiagnostic['dispanser_id'].isNotNull(),
                                table['deleted'].eq(0),
                                tableDiagnosis['deleted'].eq(0),
                                tableDiagnostic['deleted'].eq(0),
                                tableEvent['deleted'].eq(0)
                                ]
                        MKBRecord = db.getRecordEx(queryTable, 'Diagnosis.MKB', cond)
                        if MKBRecord:
                            self.MKBCaches[visitId] = MKBRecord
            return toVariant(date)

        def setEditorData(self, editor, value, record):
            editor.setValue(forceRef(value))

        def getEditorData(self, editor):
            return toVariant(editor.value())

    Col_BegDate = 4
    Col_EndDate = 5
    Col_PlanningType = 9
    
    def __init__(self, parent):
        CMKBListInDocTableModel.__init__(self, 'ProphylaxisPlanning', 'id', 'id', parent)
        self.addCol(CProphylaxisModel.CLocClientColumn( u'Ф.И.О.', 'client_id', 60)).setReadOnly(True)
        self.addCol(CProphylaxisModel.CLocClientBirthDateColumn(u'Дата рожд.', 'client_id', 20)).setReadOnly(True)
        self.addCol(CProphylaxisModel.CLocClientSexColumn(u'Пол', 'client_id', 5)).setReadOnly(True)
        self.addCol(CInDocTableCol(    u'Телефон','contact', 10))
        self.addCol(CDateInDocTableCol(u'С',      'begDate', 10))
        self.addCol(CDateInDocTableCol(u'По',     'endDate', 10))
        self.addCol(CRBInDocTableCol(u'Подразделение', 'orgStructure_id', 50, 'OrgStructure', showFields = CRBComboBox.showCode))
        self.addCol(CRBInDocTableCol(u'Специальность', 'speciality_id', 30,    'rbSpeciality'))
        self.addCol(CRBInDocTableCol(u'Врач',          'person_id', 30,        'vrbPerson'))
        self.addCol(CRBInDocTableCol(u'Тип планирования профилактики', 'prophylaxisPlanningType_id', 15, 'rbProphylaxisPlanningType', filter=u"code != 'ДН'"))
        self.addCol(CRBInDocTableCol(u'Место',      'scene_id', 15, 'rbScene'))
        self.addCol(CICDExInDocTableCol(u'Диагноз', 'MKB', 10))
        self.addCol(CBoolInDocTableCol(u'Отработан','processed', 7)).setReadOnly(True)
        self.addCol(CProphylaxisModel.CScheduleInDocTableCol(u'Талон на приём к врачу', 'appointment_id', 50)).setReadOnly(True)
        self.addCol(CProphylaxisModel.CVisitInDocTableCol(u'Явился', 'visit_id', 20)).setReadOnly(True)
        self.addCol(CEnumInDocTableCol(u'Оповещён', 'notified', 10, [u'', u'телефон', u'СМС', u'эл.почта'])).setReadOnly(True)
        self.addCol(CInDocTableCol(u'Примечание',   'note', 10))
        self.addCol(CInDocTableCol(u'Роль',         'externalUserRole', 10)).setReadOnly(True)
        self.addCol(CInDocTableCol(u'Внешний пользователь', 'externalUserName', 10)).setReadOnly(True)
        self.addCol(CInDocTableCol(u'Причина',      'reason', 10))
        self.addCol(CDateTimeInDocTableCol(u'Создано','createDatetime', 20).setReadOnly(True))
        self.addCol(CRBInDocTableCol(u'Создал',     'createPerson_id', 30, 'vrbPersonWithSpeciality')).setReadOnly(True)
        self.addCol(CDateTimeInDocTableCol(u'Изменено','modifyDatetime', 20).setReadOnly(True))
        self.addCol(CRBInDocTableCol(u'Изменил',    'modifyPerson_id', 30, 'vrbPersonWithSpeciality')).setReadOnly(True)
        self.setEnableAppendLine(False)
        self.eventEditor = parent
        
    
    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            db = QtGui.qApp.db
            column = index.column()
            if column == self.Col_PlanningType and self.eventEditor.tblProphylaxis.isColumnHidden(self.Col_BegDate):
                code = forceString(db.translate('rbProphylaxisPlanningType', 'id', toVariant(value), 'code'))
                if code != u'ДН':
                    self.eventEditor.tblProphylaxis.setColumnHidden(self.Col_BegDate, False)
                    columnEndDate = self.cols()[self.getColIndex('endDate')]
                    columnEndDate.setTitle(u'По')
            if column == self.Col_EndDate:
               CMKBListInDocTableModel.setData(self, self.index(index.row(), self.Col_BegDate), value, role=role) 
        return CMKBListInDocTableModel.setData(self, index, value, role=role)


