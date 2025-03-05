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
from PyQt4.QtCore import Qt, pyqtSignature, QAbstractTableModel, QVariant, QDateTime

from library.DialogBase    import CDialogBase
from library.Utils         import forceDate, forceInt, forceRef, forceString, toVariant

from Events.EditDispatcher import getEventFormClass

from Ui_HospitalBedsEvent  import  Ui_dialogHospitalBedsEvent


class CHospitalBedsEventDialog(CDialogBase, Ui_dialogHospitalBedsEvent):
    def __init__(self, parent, hospitalBedId = None):
        CDialogBase.__init__(self, parent)
        self.addModels('HospitalBedEvent', CHospitalBedsEventModel(self, hospitalBedId))
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setModels(self.tblHospitalBedEvent,  self.modelHospitalBedEvent, self.selectionModelHospitalBedEvent)
        self.hospitalBedId = hospitalBedId
        self.modelHospitalBedEvent.loadData()

    def selectItem(self):
        return self.exec_()

    @pyqtSignature('QModelIndex')
    def on_tblHospitalBedEvent_doubleClicked(self, index):
        row = index.row()
        if row >= 0:
            event_id = self.modelHospitalBedEvent.items[row][8]
            if event_id:
                self.editEvent(event_id)

    @pyqtSignature('')
    def on_btnClose_clicked(self):
        self.close()

    def editEvent(self, eventId):
        formClass = getEventFormClass(eventId)
        dialog = formClass(self)
        try:
            dialog.load(eventId)
            return dialog.exec_()
        finally:
            dialog.deleteLater()


class CHospitalBedsEventModel(QAbstractTableModel):
    column = [u'Номер', u'ФИО', u'Пол', u'Дата рождения', u'Назначен', u'Выполнен', u'Тип', u'Врач']
    sex = [u'', u'М', u'Ж']

    def __init__(self, parent, hospitalBedId = None):
        QAbstractTableModel.__init__(self, parent)
        self.hospitalBedId = hospitalBedId
        self.items = []


    def columnCount(self, index = None):
        return 8


    def rowCount(self, index = None):
        return len(self.items)


    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return QVariant(self.column[section])
        return QVariant()


    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if role == Qt.DisplayRole:
            item = self.items[row]
            return toVariant(item[column])
        return QVariant()


    def loadData(self):
        self.items = []
        db = QtGui.qApp.db
        tableAPHB = db.table('ActionProperty_HospitalBed')
        tableAP = db.table('ActionProperty')
        tableAction = db.table('Action')
        tableEvent = db.table('Event')
        tableClient = db.table('Client')
        tableEventType = db.table('EventType')
        tablePersonWithSpeciality = db.table('vrbPersonWithSpeciality')
        queryTable = tableAPHB.leftJoin(tableAP, tableAPHB['id'].eq(tableAP['id']))
        queryTable = queryTable.leftJoin(tableAction, tableAction['id'].eq(tableAP['action_id']))
        queryTable = queryTable.leftJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
        queryTable = queryTable.leftJoin(tableClient, tableEvent['client_id'].eq(tableClient['id']))
        queryTable = queryTable.leftJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
        queryTable = queryTable.leftJoin(tablePersonWithSpeciality, tableEvent['execPerson_id'].eq(tablePersonWithSpeciality['id']))
        cols = [tableEvent['id'].alias('eventId'),
                tableEvent['client_id'],
                tableClient['lastName'],
                tableClient['firstName'],
                tableClient['patrName'],
                tableClient['sex'],
                tableClient['birthDate'],
                tableEvent['setDate'],
                tableEvent['execDate'],
                tablePersonWithSpeciality['name'],
                tableEventType['name'].alias('eventType')
               ]
        currentDate = QDateTime.currentDateTime()
        cond = [ tableAPHB['value'].eq(self.hospitalBedId),
                 tableAction['deleted'].eq(0),
                 tableAction['status'].eq(0),
                 tableEvent['deleted'].eq(0),
                 db.joinOr([tableAction['begDate'].le(currentDate)]),
                 db.joinOr([tableAction['endDate'].gt(currentDate), tableAction['endDate'].isNull()])
               ]
        records = db.getRecordList(queryTable, cols, cond)
        for record in records:
            clientId = forceRef(record.value('client_id'))
            sexClient = self.sex[forceInt(record.value('sex'))]
            item = [clientId,
                    forceString(record.value('lastName')) + u' ' + forceString(record.value('firstName')) + u' ' + forceString(record.value('patrName')),
                    sexClient,
                    forceDate(record.value('birthDate')),
                    forceDate(record.value('setDate')),
                    forceDate(record.value('execDate')),
                    forceString(record.value('eventType')),
                    forceString(record.value('name')),
                    forceRef(record.value('eventId'))
                   ]
            self.items.append(item)
        self.reset()
