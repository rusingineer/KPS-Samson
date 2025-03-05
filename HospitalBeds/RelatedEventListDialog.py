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
from PyQt4.QtCore import Qt, pyqtSignature, QAbstractTableModel, QDate, QDateTime, QVariant

from library.DialogBase import CDialogBase
from library.TableModel import CCol
from library.Utils import forceDateTime, forceRef, forceString, getDataOSHB, getMKB, toVariant

from Events.Utils import getActionTypeIdListByFlatCode
from Registry.AmbCardMixin import CAmbCardMixin


from Ui_RelatedEventListDialog import Ui_RelatedEventListDialog


class CRelatedEventListDialog(CDialogBase, CAmbCardMixin, Ui_RelatedEventListDialog):
    @pyqtSignature('')
    def on_tblAmbCardStatusActions_popupMenuAboutToShow(self): CAmbCardMixin.on_tblAmbCardStatusActions_popupMenuAboutToShow(self)
    @pyqtSignature('')
    def on_tblAmbCardDiagnosticActions_popupMenuAboutToShow(self): CAmbCardMixin.on_tblAmbCardDiagnosticActions_popupMenuAboutToShow(self)
    @pyqtSignature('')
    def on_tblAmbCardCureActions_popupMenuAboutToShow(self): CAmbCardMixin.on_tblAmbCardCureActions_popupMenuAboutToShow(self)
    @pyqtSignature('')
    def on_tblAmbCardMiscActions_popupMenuAboutToShow(self): CAmbCardMixin.on_tblAmbCardMiscActions_popupMenuAboutToShow(self)
    @pyqtSignature('')
    def on_actAmbCardActionTypeGroupId_triggered(self): CAmbCardMixin.on_actAmbCardActionTypeGroupId_triggered(self)
    @pyqtSignature('')
    def on_actAmbCardOpenActionELMK_triggered(self): CAmbCardMixin.on_actAmbCardOpenActionELMK_triggered(self)
    @pyqtSignature('QModelIndex')
    def on_tblAmbCardStatusActions_doubleClicked(self, *args): CAmbCardMixin.on_tblAmbCardStatusActions_doubleClicked(self, *args)
    @pyqtSignature('QModelIndex')
    def on_tblAmbCardDiagnosticActions_doubleClicked(self, *args): CAmbCardMixin.on_tblAmbCardDiagnosticActions_doubleClicked(self, *args)
    @pyqtSignature('QModelIndex')
    def on_tblAmbCardCureActions_doubleClicked(self, *args): CAmbCardMixin.on_tblAmbCardCureActions_doubleClicked(self, *args)
    @pyqtSignature('QModelIndex')
    def on_tblAmbCardMiscActions_doubleClicked(self, *args): CAmbCardMixin.on_tblAmbCardMiscActions_doubleClicked(self, *args)
    @pyqtSignature('int')
    def on_cmbAmbCardDiagnosticsSpeciality_currentIndexChanged(self, *args): CAmbCardMixin.on_cmbAmbCardDiagnosticsSpeciality_currentIndexChanged(self, *args)
    @pyqtSignature('QAbstractButton*')
    def on_cmdAmbCardDiagnosticsButtonBox_clicked(self, *args): CAmbCardMixin.on_cmdAmbCardDiagnosticsButtonBox_clicked(self, *args)
    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardDiagnostics_currentRowChanged(self, *args): CAmbCardMixin.on_selectionModelAmbCardDiagnostics_currentRowChanged(self, *args)
    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardVisits_currentRowChanged(self, *args): CAmbCardMixin.on_selectionModelAmbCardVisits_currentRowChanged(self, *args)
    @pyqtSignature('int')
    def on_tabAmbCardDiagnosticDetails_currentChanged(self, *args): CAmbCardMixin.on_tabAmbCardDiagnosticDetails_currentChanged(self, *args)
    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardDiagnosticsActions_currentRowChanged(self, *args): CAmbCardMixin.on_selectionModelAmbCardDiagnosticsActions_currentRowChanged(self, *args)
    @pyqtSignature('')
    def on_actDiagnosticsShowPropertyHistory_triggered(self): CAmbCardMixin.on_actDiagnosticsShowPropertyHistory_triggered(self)
    @pyqtSignature('')
    def on_actDiagnosticsShowPropertiesHistory_triggered(self): CAmbCardMixin.on_actDiagnosticsShowPropertiesHistory_triggered(self)
    @pyqtSignature('int')
    def on_tabAmbCardContent_currentChanged(self, *args): CAmbCardMixin.on_tabAmbCardContent_currentChanged(self, *args)
    @pyqtSignature('')
    def on_actAmbCardPrintEvents_triggered(self): CAmbCardMixin.on_actAmbCardPrintEvents_triggered(self)
    @pyqtSignature('int')
    def on_actAmbCardPrintCaseHistory_printByTemplate(self, *args): CAmbCardMixin.on_actAmbCardPrintCaseHistory_printByTemplate(self, *args)
    @pyqtSignature('')
    def on_mnuAmbCardPrintActions_aboutToShow(self): CAmbCardMixin.on_mnuAmbCardPrintActions_aboutToShow(self)
    @pyqtSignature('int')
    def on_actAmbCardPrintAction_printByTemplate(self, *args): CAmbCardMixin.on_actAmbCardPrintAction_printByTemplate(self, *args)
    @pyqtSignature('')
    def on_actAmbCardPrintActions_triggered(self): CAmbCardMixin.on_actAmbCardPrintActions_triggered(self)
    @pyqtSignature('')
    def on_actAmbCardCopyAction_triggered(self): CAmbCardMixin.on_actAmbCardCopyAction_triggered(self)
    @pyqtSignature('int')
    def on_actAmbCardPrintActionsHistory_printByTemplate(self, *args): CAmbCardMixin.on_actAmbCardPrintActionsHistory_printByTemplate(self, *args)
    @pyqtSignature('QAbstractButton*')
    def on_cmdAmbCardStatusButtonBox_clicked(self, *args): CAmbCardMixin.on_cmdAmbCardStatusButtonBox_clicked(self, *args)
    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardStatusActions_currentRowChanged(self, *args): CAmbCardMixin.on_selectionModelAmbCardStatusActions_currentRowChanged(self, *args)
    @pyqtSignature('')
    def on_actStatusShowPropertyHistory_triggered(self): CAmbCardMixin.on_actStatusShowPropertyHistory_triggered(self)
    @pyqtSignature('')
    def on_actStatusShowPropertiesHistory_triggered(self): CAmbCardMixin.on_actStatusShowPropertiesHistory_triggered(self)
    @pyqtSignature('QAbstractButton*')
    def on_cmdAmbCardDiagnosticButtonBox_clicked(self, *args): CAmbCardMixin.on_cmdAmbCardDiagnosticButtonBox_clicked(self, *args)
    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardDiagnosticActions_currentRowChanged(self, *args): CAmbCardMixin.on_selectionModelAmbCardDiagnosticActions_currentRowChanged(self, *args)
    @pyqtSignature('')
    def on_actDiagnosticShowPropertyHistory_triggered(self): CAmbCardMixin.on_actDiagnosticShowPropertyHistory_triggered(self)
    @pyqtSignature('')
    def on_actDiagnosticShowPropertiesHistory_triggered(self): CAmbCardMixin.on_actDiagnosticShowPropertiesHistory_triggered(self)
    @pyqtSignature('QAbstractButton*')
    def on_cmdAmbCardCureButtonBox_clicked(self, *args): CAmbCardMixin.on_cmdAmbCardCureButtonBox_clicked(self, *args)
    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardCureActions_currentRowChanged(self, *args): CAmbCardMixin.on_selectionModelAmbCardCureActions_currentRowChanged(self, *args)
    @pyqtSignature('')
    def on_actCureShowPropertyHistory_triggered(self): CAmbCardMixin.on_actCureShowPropertyHistory_triggered(self)
    @pyqtSignature('')
    def on_actCureShowPropertiesHistory_triggered(self): CAmbCardMixin.on_actCureShowPropertiesHistory_triggered(self)
    @pyqtSignature('QAbstractButton*')
    def on_cmdAmbCardVisitButtonBox_clicked(self, *args): CAmbCardMixin.on_cmdAmbCardVisitButtonBox_clicked(self, *args)
    @pyqtSignature('')
    def on_actAmbCardPrintVisits_triggered(self): CAmbCardMixin.on_actAmbCardPrintVisits_triggered(self)
    @pyqtSignature('QAbstractButton*')
    def on_cmdAmbCardMiscButtonBox_clicked(self, *args): CAmbCardMixin.on_cmdAmbCardMiscButtonBox_clicked(self, *args)
    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardMiscActions_currentRowChanged(self, *args): CAmbCardMixin.on_selectionModelAmbCardMiscActions_currentRowChanged(self, *args)
    @pyqtSignature('')
    def on_actMiscShowPropertyHistory_triggered(self): CAmbCardMixin.on_actMiscShowPropertyHistory_triggered(self)
    @pyqtSignature('')
    def on_actMiscShowPropertiesHistory_triggered(self): CAmbCardMixin.on_actMiscShowPropertiesHistory_triggered(self)
    @pyqtSignature('')
    def on_tblAmbCardSurveyActions_popupMenuAboutToShow(self): CAmbCardMixin.on_tblAmbCardSurveyActions_popupMenuAboutToShow(self)
    @pyqtSignature('QModelIndex')
    def on_tblAmbCardSurveyActions_doubleClicked(self, *args): CAmbCardMixin.on_tblAmbCardSurveyActions_doubleClicked(self, *args)
    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAmbCardSurveyActions_currentRowChanged(self, *args): CAmbCardMixin.on_selectionModelAmbCardSurveyActions_currentRowChanged(self, *args)
    @pyqtSignature('QAbstractButton*')
    def on_cmdAmbCardSurveyButtonBox_clicked(self, *args): CAmbCardMixin.on_cmdAmbCardSurveyButtonBox_clicked(self, *args)
    @pyqtSignature('')
    def on_actSurveyShowPropertyHistory_triggered(self): CAmbCardMixin.on_actSurveyShowPropertyHistory_triggered(self)
    @pyqtSignature('')
    def on_actSurveyShowPropertiesHistory_triggered(self): CAmbCardMixin.on_actSurveyShowPropertiesHistory_triggered(self)


    def __init__(self, parent, eventId, prevEventId = None):
        CDialogBase.__init__(self, parent)
        self.addModels('RelatedEventList', CRelatedEventListModel(self))
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setModels(self.tblRelatedEventList,  self.modelRelatedEventList, self.selectionModelRelatedEventList)
        self.tblRelatedEventList.model().loadData(eventId, prevEventId)


    @pyqtSignature('')
    def on_btnClose_clicked(self):
        self.close()


    @pyqtSignature('')
    def on_btnPrint_clicked(self):
        self.tblRelatedEventList.setReportHeader(u'Связанные события')
        titlePresenceDay = u'\n' + u'отчёт составлен: ' + forceString(QDateTime.currentDateTime())
        self.tblRelatedEventList.setReportDescription(titlePresenceDay)
        self.tblRelatedEventList.printContent()


    @pyqtSignature('QModelIndex')
    def on_tblRelatedEventList_doubleClicked(self, index):
        if index.isValid():
            row = index.row()
            model = self.tblRelatedEventList.model()
            eventId = model.items[row][14]
            if eventId:
                self.editEvent(eventId)


    def editEvent(self, eventId):
        from Events.EditDispatcher import getEventFormClass
        formClass = getEventFormClass(eventId)
        dialog = formClass(self)
        try:
            dialog.load(eventId)
            return dialog.exec_()
        finally:
            dialog.deleteLater()


class CRelatedEventListModel(QAbstractTableModel):
    column = [u'Начало "Движения"', u'Конец "Движения"', u'Отделение пребывания', u'Название койки', u'Профиль койки', u'Диагноз отделения', u'Количество койко-дней', u'Начало события', u'Конец события', u'Тип', u'MKB', u'Код стандарта', u'Наименование стандарта', u'Ответственный']
    def __init__(self, parent):
        QAbstractTableModel.__init__(self, parent)
        self.items = []
        self._cols = []


    def cols(self):
        self._cols = [CCol(u'Начало "Движения"', ['setDate'], 20, 'l'),
                      CCol(u'Конец "Движения"',  ['setDate'], 20, 'l'),
                      CCol(u'Отделение пребывания', ['nameOS'], 20, 'l'),
                      CCol(u'Название койки',    ['bedName'], 20, 'l'),
                      CCol(u'Профиль койки',     ['bedName'], 20, 'l'),
                      CCol(u'Диагноз отделения', ['diagnosis'], 20, 'l'),
                      CCol(u'Количество койко-дней', ['days'], 20, 'l'),
                      CCol(u'Начало события', ['setDate'], 20, 'l'),
                      CCol(u'Конец события',  ['execDate'], 20, 'l'),
                      CCol(u'Тип события',    ['eventTypeId'], 30, 'l'),
                      CCol(u'MKB',            ['MKB'], 20, 'l'),
                      CCol(u'Код стандарта', ['codeMes'], 20, 'l'),
                      CCol(u'Наименование стандарта', ['nameMes'], 30, 'l'),
                      CCol(u'Ответственный', ['namePerson'], 30, 'l')
                      ]
        return self._cols


    def columnCount(self, index = None):
        return 14


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


    def loadData(self, eventId, prevEventId):
        self.items = []
        idList = set([])
        idListParents = []
        idListDescendant = []
        if eventId or prevEventId:
#            if not eventId:
#                eventId = prevEventId
            db = QtGui.qApp.db
            tableEvent = db.table('Event')
            tableEventType = db.table('EventType')
            tableMES = db.table('mes.MES')
            tablePWS = db.table('vrbPersonWithSpeciality')
#            tableAPHB = db.table('ActionProperty_HospitalBed')
            tableAPT = db.table('ActionPropertyType')
            tableAP = db.table('ActionProperty')
            tableActionType = db.table('ActionType')
            tableAction = db.table('Action')
            tableOS = db.table('OrgStructure')
            tableAPOS = db.table('ActionProperty_OrgStructure')
            tableRBHospitalBedProfile = db.table('rbHospitalBedProfile')
#            tableContract = db.table('Contract')
#            tableRBFinance = db.table('rbFinance')
#            tableRBFinanceBC = db.table('rbFinance').alias('rbFinanceByContract')

            idListParents = set(db.getTheseAndParents(tableEvent, 'prevEvent_id', [eventId if eventId else prevEventId]))
            idList |= idListParents
            idListDescendant = set(db.getDescendants(tableEvent, 'prevEvent_id', eventId if eventId else prevEventId))
            idList |= idListDescendant
            if len(idList) == 1 and (eventId in list(idList)) and (eventId != prevEventId):
                idList = []
            if idList:
                idList |= idListDescendant
                cols = [tableEvent['id'].alias('eventId'),
                        tableEvent['setDate'],
                        tableEvent['execDate'],
                        tableEvent['execPerson_id'],
                        tableEventType['name'].alias('eventTypeName'),
                        tableMES['code'].alias('codeMes'),
                        tableMES['name'].alias('nameMes'),
                        tablePWS['name'].alias('namePerson'),
                        tableAction['id'],
                        tableAction['begDate'],
                        tableAction['endDate']
                        ]
                cols.append(getMKB())
                cols.append(u'IF(OrgStructure.id IS NOT NULL AND OrgStructure.deleted=0, OrgStructure.name, NULL) AS nameOS')
                cols.append(getDataOSHB())
                cols.append(u'''(SELECT APS.value
    FROM ActionPropertyType AS APT
    INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id
    INNER JOIN ActionProperty_String AS APS ON APS.id=AP.id
    WHERE  Action.id IS NOT NULL AND APT.actionType_id=Action.actionType_id AND AP.action_id=Action.id AND APT.deleted=0 AND APT.name = '%s') AS diagnosis'''%(u'Диагноз'))
                cols.append('''(SELECT OSHB.profile_id
FROM ActionPropertyType AS APT
INNER JOIN ActionProperty AS AP ON AP.type_id=APT.id
INNER JOIN ActionProperty_HospitalBed AS APHB ON APHB.id=AP.id
INNER JOIN OrgStructure_HospitalBed AS OSHB ON OSHB.id=APHB.value
WHERE APT.actionType_id=Action.actionType_id AND AP.action_id=Action.id AND AP.deleted=0 AND APT.deleted=0 AND APT.typeName = 'HospitalBed') AS profileId''')
                cond = [tableEvent['deleted'].eq(0),
                        tableEvent['id'].inlist(idList),
                        tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode(u'moving%')),
                        tableAction['deleted'].eq(0),
                        tableAction['event_id'].eq(tableEvent['id']),
                        tableAP['deleted'].eq(0),
                        tableAPT['deleted'].eq(0),
                        tableAP['action_id'].eq(tableAction['id'])
                        ]
                cond.append(u'''(EventType.medicalAidType_id IN (SELECT rbMedicalAidType.id from rbMedicalAidType where rbMedicalAidType.code IN (\'1\', \'2\', \'3\', \'7\')))''')
                cond.append(tableAPT['name'].like(u'Отделение пребывания'))
                table = tableEvent.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
                table = table.leftJoin(tablePWS, tablePWS['id'].eq(tableEvent['execPerson_id']))
                table = table.leftJoin(tableMES, tableEvent['MES_id'].eq(tableMES['id']))
                table = table.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
                table = table.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
                table = table.innerJoin(tableAPT, tableAPT['actionType_id'].eq(tableActionType['id']))
                table = table.innerJoin(tableAP, tableAP['type_id'].eq(tableAPT['id']))
                table = table.leftJoin(tableAPOS, tableAPOS['id'].eq(tableAP['id']))
                table = table.leftJoin(tableOS, tableOS['id'].eq(tableAPOS['value']))
                records = db.getRecordList(table, cols, cond, 'Event.setDate, Action.begDate')
                for record in records:
                    newEventId = forceRef(record.value('eventId'))
                    if newEventId != eventId:
                        bedCodeName = forceString(record.value('bedCodeName')).split("  ")
                        bedCode = forceString(bedCodeName[0]) if len(bedCodeName)>=1 else ''
                        bedName = forceString(bedCodeName[1]) if len(bedCodeName)>=2 else ''
                        bedSex = forceString(bedCodeName[2]) if len(bedCodeName)>=3 else ''
                        profileId = forceRef(record.value('profileId'))
                        begDateTime = forceDateTime(record.value('begDate'))
                        endDateTime = forceDateTime(record.value('endDate'))
                        begDate = begDateTime.date()
                        endDate = endDateTime.date()
                        days = u'-'
                        if begDate or endDate:
                            if not endDate:
                                endDate = QDate.currentDate()
                            if begDate == endDate:
                                days = u'1'
                            elif not begDate:
                                days = u'-'
                            else:
                                days = str(begDate.daysTo(endDate))
                        item = [begDateTime,
                                endDateTime,
                                forceString(record.value('nameOS')),
                                bedCode + (u'-' + bedName if bedName else u'') + ((u'(' + bedSex + u')') if bool(bedSex) else u''),
                                forceString(db.translate(tableRBHospitalBedProfile, 'id', profileId, 'name')) if profileId else u'',
                                forceString(record.value('diagnosis')),
                                days,
                                forceDateTime(record.value('setDate')),
                                forceDateTime(record.value('execDate')),
                                forceString(record.value('eventTypeName')),
                                forceString(record.value('MKB')),
                                forceString(record.value('codeMes')),
                                forceString(record.value('nameMes')),
                                forceString(record.value('namePerson')),
                                newEventId
                                ]
                        self.items.append(item)
        self.reset()
