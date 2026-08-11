# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2023 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignature, Qt, QAbstractTableModel, QVariant

from library.DialogBase import CDialogBase
from library.TableModel import CCol
from library.Utils import toVariant, forceRef, forceDate, forceString, forceInt

from Events.ActionEditDialog import CActionEditDialog
from Events.ActionStatus import CActionStatus
from Registry.Utils import getClientBanner
from Reports.Utils import getDataOrgStructureName


from Events.Ui_SelectPlanningOpenEventsDialog import Ui_SelectPlanningOpenEventsDialog


class CSelectPlanningOpenEvents(CDialogBase, Ui_SelectPlanningOpenEventsDialog):
    def __init__(self, parent, actionIdList=[], clientId=None, date=None):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setWindowTitleEx(u'Список открытых планирований на пациента')
        self.btnResult = None
        self.resultActionId = None
        self.actionIdList = actionIdList
        self.clientId = clientId
        self.date = date
        self.model = CPlanningOpenEventsModel(self)
        self.model.loadData(self.actionIdList)
        self.tblOpenActions.setModel(self.model)
        if self.actionIdList:
            self.tblOpenActions.selectRow(0)
        if self.clientId:
            self.txtClientInfoEventsBrowser.setHtml(getClientBanner(self.clientId, self.date))
        else:
            self.txtClientInfoEventsBrowser.setText('')
        self.btnClose.setFocus(Qt.TabFocusReason)


    def currentItemId(self):
        currentItemId = None
        index = self.tblOpenActions.currentIndex()
        row = index.row() if index.isValid() else -1
        if row >= 0:
            currentItemId = self.model.getActionId(row)
        return currentItemId


    @pyqtSignature('')
    def on_btnClose_clicked(self):
        self.resultActionId = None
        self.btnResult = 0
        self.close()


    @pyqtSignature('')
    def on_btnOpen_clicked(self):
        dialog = CActionEditDialog(self)
        try:
            dialog.setReadOnly(True)
            dialog.load(self.currentItemId())
            if dialog.exec_():
                pass
        finally:
            dialog.deleteLater()


    @pyqtSignature('')
    def on_btnSelect_clicked(self):
        self.resultActionId = self.currentItemId()
        self.btnResult = 1
        self.close()


    def destroy(self):
        pass


class CPlanningOpenEventsModel(QAbstractTableModel):
    column = [u'Тип', u'Дата начала', u'Дата планирования', u'Статус', u'Врач назначивший', u'Куда направляется']

    def __init__(self, parent):
        QAbstractTableModel.__init__(self, parent)
        self.items = []
        self.itemByName = {}
        self._cols = []

    def cols(self):
        self._cols = [CCol(u'Тип', ['name'], 20, 'l'),
                      CCol(u'Дата начала', ['begDate'], 20, 'l'),
                      CCol(u'Дата планирования', ['plannedEndDate'], 20, 'l'),
                      CCol(u'Статус', ['status'], 20, 'l'),
                      CCol(u'Врач назначивший', ['namePerson'], 20, 'l'),
                      CCol(u'Куда направляется', ['nameOrgStructure'], 15, 'l'),
                      ]
        return self._cols


    def columnCount(self, index=None, *args, **kwargs):
        return 6


    def rowCount(self, index=None, *args, **kwargs):
        return len(self.items)


    def getActionId(self, row):
        return self.items[row][-1]


    def headerData(self, section, orientation, role=Qt.DisplayRole):
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


    def loadData(self, actionIdList):
        self.items = []
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        tablePWS = db.table('vrbPersonWithSpeciality')
        tableOrgStruct = db.table('OrgStructure').alias('PersonOrgStructure')
        tableOrgStruct1 = db.table('OrgStructure').alias('Parent1')
        tableOrgStruct2 = db.table('OrgStructure').alias('Parent2')
        tableOrgStruct3 = db.table('OrgStructure').alias('Parent3')
        tableOrgStruct4 = db.table('OrgStructure').alias('Parent4')
        tableOrgStruct5 = db.table('OrgStructure').alias('Parent5')
        tableOrg = db.table('Organisation')
        tableRelegateOrg = db.table('Organisation').alias('RelegateOrg')

        nameProperty = u'подразделение'
        cols = [tableAction['id'].alias('actionId'),
                tableAction['event_id'],
                tableActionType['name'],
                tableAction['begDate'],
                tableAction['directionDate'],
                tableAction['plannedEndDate'],
                tableAction['status'],
                tableAction['setPerson_id'],
                tablePWS['name'].alias('namePerson'),
                tableRelegateOrg['id'].alias('relegateOrg_id'),
                getDataOrgStructureName(nameProperty),
                u'''(SELECT ActionProperty_OrgStructure.value FROM ActionProperty_OrgStructure
                    LEFT JOIN ActionProperty ON ActionProperty.id = ActionProperty_OrgStructure.id
                    LEFT JOIN Action AS ACT ON ACT.id = ActionProperty.action_id
                    LEFT JOIN ActionPropertyType ON ActionPropertyType.id = ActionProperty.type_id
                    WHERE ACT.id = Action.id AND ActionPropertyType.name = 'Подразделение') as orgStructureId''',
                u'''(SELECT ActionProperty_String.value FROM ActionProperty_String
                    LEFT JOIN ActionProperty ON ActionProperty.id = ActionProperty_String.id
                    LEFT JOIN Action AS ACT ON ACT.id = ActionProperty.action_id
                    LEFT JOIN ActionPropertyType ON ActionPropertyType.id = ActionProperty.type_id
                    WHERE ACT.id = Action.id AND ActionPropertyType.name = 'Номер направления') as srcNumber''']
        queryTable = tableAction.leftJoin(tablePWS, tablePWS['id'].eq(tableAction['setPerson_id']))
        queryTable = queryTable.leftJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        queryTable = queryTable.leftJoin(tableOrgStruct, tablePWS['orgStructure_id'].eq(tableOrgStruct['id']))
        queryTable = queryTable.leftJoin(tableOrgStruct1, tableOrgStruct['parent_id'].eq(tableOrgStruct1['id']))
        queryTable = queryTable.leftJoin(tableOrgStruct2, tableOrgStruct1['parent_id'].eq(tableOrgStruct2['id']))
        queryTable = queryTable.leftJoin(tableOrgStruct3, tableOrgStruct2['parent_id'].eq(tableOrgStruct3['id']))
        queryTable = queryTable.leftJoin(tableOrgStruct4, tableOrgStruct3['parent_id'].eq(tableOrgStruct4['id']))
        queryTable = queryTable.leftJoin(tableOrgStruct5, tableOrgStruct4['parent_id'].eq(tableOrgStruct5['id']))
        if QtGui.qApp.defaultKLADR().startswith('01'):
            queryTable = queryTable.leftJoin(tableOrg, u"""Organisation.infisCode = IF(length(PersonOrgStructure.bookkeeperCode)>=5, PersonOrgStructure.bookkeeperCode,
                                                                          IF(length(Parent1.bookkeeperCode)>=5, Parent1.bookkeeperCode,
                                                                            IF(length(Parent2.bookkeeperCode)>=5, Parent2.bookkeeperCode,
                                                                              IF(length(Parent3.bookkeeperCode)>=5, Parent3.bookkeeperCode,
                                                                                IF(length(Parent4.bookkeeperCode)>=5, Parent4.bookkeeperCode, Parent5.bookkeeperCode))))) and Organisation.deleted = 0 and Organisation.isActive = 1""")

        else:
            queryTable = queryTable.leftJoin(tableOrg, u"""Organisation.infisCode = IF(length(PersonOrgStructure.bookkeeperCode)=5, PersonOrgStructure.bookkeeperCode,
                                                              IF(length(Parent1.bookkeeperCode)=5, Parent1.bookkeeperCode,
                                                                IF(length(Parent2.bookkeeperCode)=5, Parent2.bookkeeperCode,
                                                                  IF(length(Parent3.bookkeeperCode)=5, Parent3.bookkeeperCode,
                                                                    IF(length(Parent4.bookkeeperCode)=5, Parent4.bookkeeperCode, Parent5.bookkeeperCode))))) and Organisation.deleted = 0 and Organisation.isActive = 1""")
        queryTable = queryTable.leftJoin(tableRelegateOrg, 'RelegateOrg.id = ifnull(Action.org_id, Organisation.id)')
        cond = [tableAction['id'].inlist(actionIdList)]
        records = db.getRecordList(queryTable, cols, cond, 'Action.begDate desc')
        for record in records:
            item = [forceString(record.value('name')),
                    forceDate(record.value('begDate')),
                    forceDate(record.value('plannedEndDate')),
                    CActionStatus.names[forceInt(record.value('status'))],
                    forceString(record.value('namePerson')),
                    forceString(record.value('nameOrgStructure')),
                    forceRef(record.value('actionId'))]
            self.items.append(item)
            _dict = {
                'eventId': forceRef(record.value('event_id')),
                'relegateOrgId': forceRef(record.value('relegateOrg_id')),
                'relegatePersonId': forceRef(record.value('setPerson_id')),
                'orgStructureId': forceRef(record.value('orgStructureId')),
                'srcDate': forceDate(record.value('directionDate')),
                'srcNumber': forceString(record.value('srcNumber')),
                'srcPerson': forceString(record.value('namePerson'))
            }
            self.itemByName[forceRef(record.value('actionId'))] = _dict
        self.reset()
