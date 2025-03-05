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
from PyQt4.QtCore import Qt, SIGNAL, pyqtSignature, QAbstractTableModel, QDate, QDateTime, QVariant


from library.DialogBase    import CDialogBase
from library.InDocTable    import CDateTimeForEventInDocTableCol
from library.TableModel    import CDateTimeCol, CRefBookCol, CTextCol
from library.Utils         import forceDate, forceDateTime, forceInt, forceRef, forceString, getDataOSHB, getMKB, toDateTimeWithoutSeconds, toVariant

from Events.Action         import CActionTypeCache, CAction, CActionType
from Events.ActionStatus   import CActionStatus
from Events.Utils          import getActionTypeIdListByFlatCode

from Registry.AmbCardMixin import CAmbCardMixin
from Registry.Utils        import getClientBanner, getClientString

from Reports.ReportBase    import CReportBase, createTable
from Reports.ReportView    import CReportViewDialog
from Reports.Utils         import getDataOrgStructureName

from Users.Rights          import urEditCheckPeriodActions

from Ui_CheckPeriodActions import Ui_CheckPeriodActions


class CCheckPeriodActions(CDialogBase, CAmbCardMixin, Ui_CheckPeriodActions):
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

    def __init__(self, parent, tabList, eventId, prevEventId = None, checkStationary = False):
        CDialogBase.__init__(self, parent)
        self.addModels('ActionList', CActionListModel(self))
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setModels(self.tblActionList,  self.modelActionList, self.selectionModelActionList)
        self.currentEventId = eventId
        self.clientId = self.getClientIdForEvent()
        self.checkStationary = checkStationary
        self.tblActionList.model().loadData(tabList, self.currentEventId, prevEventId, self.checkStationary)


    def getClientIdForEvent(self):
        self.clientId = None
        if self.currentEventId:
            db = QtGui.qApp.db
            tableEvent = db.table('Event')
            record = db.getRecordEx(tableEvent, [tableEvent['client_id']], [tableEvent['id'].eq(self.currentEventId), tableEvent['deleted'].eq(0)])
            self.clientId = forceRef(record.value('client_id')) if record else None
        if self.clientId:
            self.txtClientInfoBrowser.setHtml(getClientBanner(self.clientId))
            return self.clientId
        self.txtClientInfoBrowser.setText('')
        return self.clientId


    @pyqtSignature('')
    def on_btnClose_clicked(self):
        self.close()


    @pyqtSignature('')
    def on_btnSave_clicked(self):
        items = self.modelActionList.items()
        if items is not None:
            db = QtGui.qApp.db
            table = db.table('Action')
            for row, item in enumerate(items):
                actionId = item[len(item)-1]
                checkEventId = item[len(item)-2]
                if actionId and checkEventId:
                    record = db.getRecordEx(table, '*', [table['id'].eq(actionId), table['deleted'].eq(0)])
                    if record:
                        masterId = forceRef(record.value('id'))
                        eventId = forceRef(record.value('event_id'))
                        if masterId == actionId and eventId == checkEventId:
                            status = forceInt(item[2])
                            begDateTime = forceDateTime(item[4])
                            endDateTime = forceDateTime(item[5])
                            if not self.checkActionDate(eventId, begDateTime, endDateTime, row):
                                return
                            if not self.checkActionsDataEntered(eventId, masterId, begDateTime, endDateTime, row):
                                return
                            record.setValue('status', toVariant(status))
                            record.setValue('begDate', toVariant(begDateTime))
                            record.setValue('endDate', toVariant(endDateTime))
                            outRecord = record
                            id = db.updateRecord(table, outRecord)
                            record.setValue('id', toVariant(id))
        self.on_btnClose_clicked()


    def checkActionDate(self, eventId, begDate, endDate, row):
        result = True
        db = QtGui.qApp.db
        table = db.table('Event')
        record = db.getRecordEx(table, '*', [table['id'].eq(eventId), table['deleted'].eq(0)])
        if record:
            begDateAction = toDateTimeWithoutSeconds(begDate)
            endDateAction = toDateTimeWithoutSeconds(endDate)
            setDateTime = toDateTimeWithoutSeconds(forceDateTime(record.value('setDate')))
            execDateTime = toDateTimeWithoutSeconds(forceDateTime(record.value('execDate')))
            if begDateAction:
                if setDateTime:
                    result = result and (begDateAction >= setDateTime or self.checkValueMessage(u'Дата начала действия %s раньше даты начала события %s'%(forceString(begDateAction), forceString(setDateTime)), False, self.tblActionList, row, 4))
                if execDateTime:
                    result = result and (begDateAction <= execDateTime or self.checkValueMessage(u'Дата начала действия %s позже даты окончания события %s'%(forceString(begDateAction), forceString(execDateTime)), False, self.tblActionList, row, 4))
            if endDateAction:
                if setDateTime:
                    result = result and (endDateAction >= setDateTime or self.checkValueMessage(u'Дата окончания действия %s раньше даты начала события %s'%(forceString(endDateAction), forceString(setDateTime)), False, self.tblActionList, row, 5))
                if execDateTime:
                    result = result and (endDateAction <= execDateTime or self.checkValueMessage(u'Дата окончания действия %s позже даты окончания события %s'%(forceString(endDateAction), forceString(execDateTime)), False, self.tblActionList, row, 5))
        else:
            QtGui.QMessageBox.warning( self,
                         u'Внимание!',
                         u'Нет события соответствующего действию!',
                         QtGui.QMessageBox.Ok,
                         QtGui.QMessageBox.Ok)
            return False
        return result


    def checkActionsDataEntered(self, eventId, masterId, begDateAction, endDateAction, currentRow):
        result = True
        db = QtGui.qApp.db
        table = db.table('Event')
        record = db.getRecordEx(table, '*', [table['id'].eq(eventId), table['deleted'].eq(0)])
        if record:
#            setDateTime = toDateTimeWithoutSeconds(forceDateTime(record.value('setDate')))
#            execDateTime = toDateTimeWithoutSeconds(forceDateTime(record.value('execDate')))
            model = self.modelActionList
            for row, item in enumerate(model.items()):
                actionId = forceRef(item[10])
                if actionId != masterId:
                    begDate = forceDateTime(item[4])
                    endDate = forceDateTime(item[5])
                    if begDateAction:
                        if begDate and endDate:
                            result = result and ((begDateAction < begDate or begDateAction >= endDate)
                                                 or self.checkValueMessage(u'Дата начала действия %s не должна попадать в диапазон дат другого действия в событии %s - %s'%(forceString(begDateAction), forceString(begDate), forceString(endDate)), False, self.tblActionList, currentRow, 4))

                        elif begDate and not endDate:
                            result = result and ((begDateAction < begDate)
                                                 or self.checkValueMessage(u'Дата начала действия %s не должна попадать в диапазон дат другого действия в событии %s - %s'%(forceString(begDateAction), forceString(begDate), forceString(endDate)), False, self.tblActionList, currentRow, 4))

                        elif not begDate and endDate:
                            result = result and ((begDateAction >= endDate)
                                                 or self.checkValueMessage(u'Дата начала действия %s не должна попадать в диапазон дат другого действия в событии %s - %s'%(forceString(begDateAction), forceString(begDate), forceString(endDate)), False, self.tblActionList, currentRow, 4))

                        elif not begDate and not endDate:
                            result = result and ((False)
                                                 or self.checkValueMessage(u'Дата начала действия %s не должна попадать в диапазон дат другого действия в событии %s - %s'%(forceString(begDateAction), forceString(begDate), forceString(endDate)), False, self.tblActionList, currentRow, 4))

                    if endDateAction:
                        if begDate and endDate:
                            result = result and ((endDateAction <= begDate or endDateAction > endDate)
                                                 or self.checkValueMessage(u'Дата окончания действия %s не должна попадать в диапазон дат другого действия в событии %s - %s'%(forceString(endDateAction), forceString(begDate), forceString(endDate)), False, self.tblActionList, currentRow, 5))

                        elif begDate and not endDate:
                            result = result and ((endDateAction <= begDate)
                                                 or self.checkValueMessage(u'Дата окончания действия %s не должна попадать в диапазон дат другого действия в событии %s - %s'%(forceString(endDateAction), forceString(begDate), forceString(endDate)), False, self.tblActionList, currentRow, 5))

                        elif not begDate and endDate:
                            result = result and ((endDateAction > endDate)
                                                 or self.checkValueMessage(u'Дата окончания действия %s не должна попадать в диапазон дат другого действия в событии %s - %s'%(forceString(endDateAction), forceString(begDate), forceString(endDate)), False, self.tblActionList, currentRow, 5))

                        elif not begDate and not endDate:
                            result = result and ((False)
                                                 or self.checkValueMessage(u'Дата окончания действия %s не должна попадать в диапазон дат другого действия в событии %s - %s'%(forceString(endDateAction), forceString(begDate), forceString(endDate)), False, self.tblActionList, currentRow, 5))
                    if not self.checkPlannedEndDate(currentRow, record, CAction(record=record), self.tblAPActions):
                        return False
        return result


    def checkPlannedEndDate(self, row, record, action, tblAPActions):
        if action:
            actionType = action.getType()
            if actionType and actionType.isPlannedEndDateRequired in [CActionType.dpedControlMild, CActionType.dpedControlHard]:
                if not forceDate(record.value('plannedEndDate')):
                    skippable = True if actionType.isPlannedEndDateRequired == CActionType.dpedControlMild else False
                    message = u'Необходимо указать Плановую дату выполнения у действия %s'%(actionType.name)
                    return self.checkValueMessage(message, skippable, tblAPActions, row, 0)
        return True


    @pyqtSignature('')
    def on_btnPrint_clicked(self):
        model = self.modelActionList
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Движение пациента\n')
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertText(u'Пациент: %s' % (getClientString(self.clientId) if self.clientId else u'не известен'))
        cursor.insertText(u'\nОтчёт составлен: ' + forceString(QDateTime.currentDateTime()))
        cursor.insertBlock()
        colWidths  = [ self.tblActionList.columnWidth(i) for i in xrange(model.columnCount()-1) ]
        colWidths.insert(0,10)
        totalWidth = sum(colWidths)
        tableColumns = []
        iColNumber = False
        for iCol, colWidth in enumerate(colWidths):
            widthInPercents = str(max(1, colWidth*90/totalWidth))+'%'
            if iColNumber == False:
                tableColumns.append((widthInPercents, [u'№'], CReportBase.AlignRight))
                iColNumber = True
            tableColumns.append((widthInPercents, [forceString(model.column[iCol])], CReportBase.AlignLeft))
        table = createTable(cursor, tableColumns)
        for iModelRow in xrange(model.rowCount()):
            iTableRow = table.addRow()
            table.setText(iTableRow, 0, iModelRow+1)
            for iModelCol in xrange(model.columnCount()):
                index = model.createIndex(iModelRow, iModelCol)
                text = forceString(model.data(index))
                table.setText(iTableRow, iModelCol+1, text)
        html = doc.toHtml('utf-8')
        view = CReportViewDialog(self)
        view.setText(html)
        view.exec_()


    @pyqtSignature('QModelIndex')
    def on_tblActionList_doubleClicked(self, index):
        if index.isValid():
            row = index.row()
            column = index.column()
            model = self.tblActionList.model()
            eventId = model._items[row][9]
            if eventId and column not in [4, 5] and (self.currentEventId != eventId or self.checkStationary):
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


class CActionListModel(QAbstractTableModel):
    column = [u'Тип действия', u'Отделение пребывания', u'Статус', u'Длительность',
    u'Начало "Движения"', u'Конец "Движения"', u'Профиль койки', u'Койка', u'Исполнитель']

    def __init__(self, parent):
        QAbstractTableModel.__init__(self, parent)
        self._items = []
        self._cols = []
        self.cols()


    def flags(self, index=None):
        column = index.column()
        result = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if (column == 4 or column == 5) and QtGui.qApp.userHasRight(urEditCheckPeriodActions):
            result |= Qt.ItemIsEditable
        return result


    def cols(self):
        self._cols = [CTextCol(u'Тип действия',      ['actionType'], 20, 'l'),
                      CTextCol(u'Отделение пребывания', ['nameOS'],     20, 'l'),
                      CTextCol(u'Статус',               ['status'],     20, 'l'),
                      CTextCol(u'Длительность',         ['days'],       20, 'l'),
                      CDateTimeForEventInDocTableCol(u'Начало "Движения"', 'begDate', 20, canBeEmpty=True),
                      CDateTimeForEventInDocTableCol(u'Конец "Движения"', 'endDate', 20, canBeEmpty=True),
                      CDateTimeCol(u'Начало "Движения"',['begDate'],    20, 'l'),
                      CDateTimeCol(u'Конец "Движения"', ['endDate'],    20, 'l'),
                      CRefBookCol(u'Профиль койки',     ['bedName'],    20, 'l'),
                      CTextCol(u'Койка',                ['bedName'],    20, 'l'),
                      CTextCol(u'Исполнитель',          ['namePerson'], 30, 'l')
                      ]
        return self._cols


    def columnCount(self, index = None):
        return 9


    def rowCount(self, index = None):
        return len(self._items)


    def items(self):
        return self._items


    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return QVariant(self.column[section])
        return QVariant()


    def getReceivedAction(self, idList):
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        tableMES = db.table('mes.MES')
        tablePWS = db.table('vrbPersonWithSpeciality')
#        tableAPT = db.table('ActionPropertyType')
#        tableAP = db.table('ActionProperty')
        tableActionType = db.table('ActionType')
        tableAction = db.table('Action')
#        tableOSHB = db.table('OrgStructure_HospitalBed')
#        tableOS = db.table('OrgStructure')
#        tableAPOS = db.table('ActionProperty_OrgStructure')
        cols = [tableEvent['id'].alias('eventId'),
                tableEvent['setDate'],
                tableEvent['execDate'],
                tableEvent['execPerson_id'],
                tableEventType['name'].alias('eventTypeName'),
                tableMES['code'].alias('codeMes'),
                tableMES['name'].alias('nameMes'),
                tablePWS['name'].alias('namePerson'),
                tableAction['id'].alias('actionId'),
                tableAction['idx'],
                tableAction['begDate'],
                tableAction['endDate'],
                tableAction['status'],
                tableAction['person_id'],
                tableActionType['name'].alias('actionTypeName'),
                tableActionType['name'].alias('actionTypeName')
                ]
        cols.append(getDataOrgStructureName(u'Направлен в отделение'))
        cols.append(getMKB())
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
                tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode(u'received%')),
                tableAction['deleted'].eq(0)
                ]
        cond.append(u'''(EventType.medicalAidType_id IN (SELECT rbMedicalAidType.id from rbMedicalAidType where rbMedicalAidType.code IN (\'1\', \'2\', \'3\', \'7\')))''')
        table = tableEvent.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
        table = table.leftJoin(tableMES, tableEvent['MES_id'].eq(tableMES['id']))
        table = table.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
        table = table.leftJoin(tablePWS, tablePWS['id'].eq(tableAction['person_id']))
        table = table.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        return db.getRecordList(table, cols, cond, 'Event.setDate, Action.begDate')


    def getMovingAction(self, idList):
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        tableMES = db.table('mes.MES')
        tablePWS = db.table('vrbPersonWithSpeciality')
#        tableAPT = db.table('ActionPropertyType')
#        tableAP = db.table('ActionProperty')
        tableActionType = db.table('ActionType')
        tableAction = db.table('Action')
#        tableOSHB = db.table('OrgStructure_HospitalBed')
#        tableOS = db.table('OrgStructure')
#        tableAPOS = db.table('ActionProperty_OrgStructure')
        cols = [tableEvent['id'].alias('eventId'),
                tableEvent['setDate'],
                tableEvent['execDate'],
                tableEvent['execPerson_id'],
                tableEventType['name'].alias('eventTypeName'),
                tableMES['code'].alias('codeMes'),
                tableMES['name'].alias('nameMes'),
                tablePWS['name'].alias('namePerson'),
                tableAction['id'].alias('actionId'),
                tableAction['idx'],
                tableAction['begDate'],
                tableAction['endDate'],
                tableAction['status'],
                tableAction['person_id'],
                tableActionType['name'].alias('actionTypeName'),
                tableActionType['name'].alias('actionTypeName')
                ]
        cols.append(getDataOrgStructureName(u'Отделение пребывания'))
        cols.append(getMKB())
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
                tableAction['deleted'].eq(0)
                ]
        cond.append(u'''(EventType.medicalAidType_id IN (SELECT rbMedicalAidType.id from rbMedicalAidType where rbMedicalAidType.code IN (\'1\', \'2\', \'3\', \'7\')))''')
        table = tableEvent.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
        table = table.leftJoin(tableMES, tableEvent['MES_id'].eq(tableMES['id']))
        table = table.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
        table = table.leftJoin(tablePWS, tablePWS['id'].eq(tableAction['person_id']))
        table = table.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        return db.getRecordList(table, cols, cond, 'Event.setDate, Action.begDate')


    def getLeavedAction(self, idList):
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableEventType = db.table('EventType')
        tableMES = db.table('mes.MES')
        tablePWS = db.table('vrbPersonWithSpeciality')
#        tableAPT = db.table('ActionPropertyType')
#        tableAP = db.table('ActionProperty')
        tableActionType = db.table('ActionType')
        tableAction = db.table('Action')
#        tableOSHB = db.table('OrgStructure_HospitalBed')
#        tableOS = db.table('OrgStructure')
#        tableAPOS = db.table('ActionProperty_OrgStructure')
        cols = [tableEvent['id'].alias('eventId'),
                tableEvent['setDate'],
                tableEvent['execDate'],
                tableEvent['execPerson_id'],
                tableEventType['name'].alias('eventTypeName'),
                tableMES['code'].alias('codeMes'),
                tableMES['name'].alias('nameMes'),
                tablePWS['name'].alias('namePerson'),
                tableAction['id'].alias('actionId'),
                tableAction['idx'],
                tableAction['begDate'],
                tableAction['endDate'],
                tableAction['status'],
                tableAction['person_id'],
                tableActionType['name'].alias('actionTypeName')
                ]
        cols.append(getDataOrgStructureName(u'Отделение'))
        cols.append(getMKB())
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
                tableAction['actionType_id'].inlist(getActionTypeIdListByFlatCode(u'leaved%')),
                tableAction['deleted'].eq(0)
                ]
        cond.append(u'''(EventType.medicalAidType_id IN (SELECT rbMedicalAidType.id from rbMedicalAidType where rbMedicalAidType.code IN (\'1\', \'2\', \'3\', \'7\')))''')
        table = tableEvent.innerJoin(tableEventType, tableEvent['eventType_id'].eq(tableEventType['id']))
        table = table.leftJoin(tableMES, tableEvent['MES_id'].eq(tableMES['id']))
        table = table.innerJoin(tableAction, tableAction['event_id'].eq(tableEvent['id']))
        table = table.leftJoin(tablePWS, tablePWS['id'].eq(tableAction['person_id']))
        table = table.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        return db.getRecordList(table, cols, cond, 'Event.setDate, Action.begDate')


    def loadData(self, tabList, eventId, prevEventId, checkStationary = False):
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableRBHospitalBedProfile = db.table('rbHospitalBedProfile')
        tablePWS = db.table('vrbPersonWithSpeciality')
        tableOSHB = db.table('OrgStructure_HospitalBed')
        tableOS = db.table('OrgStructure')
        self._items = []
        idList = set([])
        idListParents = []
        idListDescendant = []
        def fillTableAction(records):
            for record in records:
                bedCodeName = forceString(record.value('bedCodeName')).split("  ")
                bedCode = forceString(bedCodeName[0]) if len(bedCodeName)>=1 else ''
                bedName = forceString(bedCodeName[1]) if len(bedCodeName)>=2 else ''
                bedSex = forceString(bedCodeName[2]) if len(bedCodeName)>=3 else ''
                profileId = forceRef(record.value('profileId'))
                checkEventId = forceRef(record.value('eventId'))
                checkActionId = forceRef(record.value('actionId'))
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
                item = [forceString(record.value('actionTypeName')),
                        forceString(record.value('nameOrgStructure')),
                        forceInt(record.value('status')),
                        days,
                        begDateTime ,
                        endDateTime,
                        forceString(db.translate(tableRBHospitalBedProfile, 'id', profileId, 'name')) if profileId else u'',
                        bedCode + (u'-' + bedName if bedName else u'') + ((u'(' + bedSex + u')') if bool(bedSex) else u''),
                        forceString(record.value('namePerson')),
                        checkEventId,
                        checkActionId
                        ]
                self._items.append(item)
        if eventId or prevEventId:
            idListParents = set(db.getTheseAndParents(tableEvent, 'prevEvent_id', [eventId if eventId else prevEventId]))
            idList |= idListParents
            idListDescendant = set(db.getDescendants(tableEvent, 'prevEvent_id', eventId if eventId else prevEventId))
            if len(idListDescendant) > 1 or (len(idListDescendant) == 1 and idListDescendant != set([eventId if eventId else prevEventId])):
                idList |= idListDescendant
            if idList:
                idList |= idListDescendant
                for actionTab in tabList:
                    model = actionTab.tblAPActions.model()
                    for row, (record, action) in enumerate(model.items()):
                        if action and action._actionType.id:
                            actionTypeId = action._actionType.id
                            actionType = CActionTypeCache.getById(actionTypeId) if actionTypeId else None
                            actionTypeItem = action.getType()
                            if actionTypeItem and (u'received' in actionTypeItem.flatCode.lower()
                                                   or u'moving' in actionTypeItem.flatCode.lower()
                                                   or u'leaved' in actionTypeItem.flatCode.lower()):
                                begDateTime = forceDateTime(record.value('begDate'))
                                endDateTime = forceDateTime(record.value('endDate'))
                                actionId = forceRef(record.value('actionId'))
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
                                nameActionType = action._actionType.name
                                status = forceInt(record.value('status'))
                                personId = forceString(record.value('person_id'))
                                personName = forceString(db.translate(tablePWS, 'id', personId, 'name')) if personId else u''
                                bedCodeName = u''
                                nameOS = u''
                                profileName = u''
                                if u'received' in actionTypeItem.flatCode.lower():
                                    if u'Направлен в отделение' in actionType._propertiesByName:
                                        orgStructureId = action[u'Направлен в отделение']
                                        nameOS = forceString(db.translate(tableOS, 'id', orgStructureId, 'name')) if orgStructureId else u''
                                    if u'Профиль' in actionType._propertiesByName:
                                        profileId = action[u'Профиль']
                                        profileName = forceString(db.translate(tableRBHospitalBedProfile, 'id', profileId, 'name')) if profileId else u''
                                elif u'moving' in actionTypeItem.flatCode.lower():
                                    if u'Отделение пребывания' in actionType._propertiesByName:
                                        orgStructureId = action[u'Отделение пребывания']
                                        nameOS = forceString(db.translate(tableOS, 'id', orgStructureId, 'name')) if orgStructureId else u''
                                    if u'койка' in actionType._propertiesByName:
                                        bedId = action[u'койка']
                                        bedRecord = db.getRecordEx(tableOSHB, ['code, name, profile_id'], [tableOSHB['id'].eq(bedId)])
                                        codeBed = forceString(bedRecord.value('code')) if bedRecord else u''
                                        nameBed = forceString(bedRecord.value('name')) if bedRecord else u''
                                        bedCodeName = codeBed + u'-'+ nameBed
                                        profileId = forceRef(bedRecord.value('profile_id')) if bedRecord else u''
                                        profileName = forceString(db.translate(tableRBHospitalBedProfile, 'id', profileId, 'name')) if profileId else u''
                                elif u'leaved' in actionTypeItem.flatCode.lower():
                                    if u'Отделение' in actionType._propertiesByName:
                                        orgStructureId = action[u'Отделение']
                                        nameOS = forceString(db.translate(tableOS, 'id', orgStructureId, 'name')) if orgStructureId else u''
                                    if u'Профиль' in actionType._propertiesByName:
                                        profileId = action[u'Профиль']
                                        profileName = forceString(db.translate(tableRBHospitalBedProfile, 'id', profileId, 'name')) if profileId else u''
                                item = [nameActionType,
                                        nameOS,
                                        status,
                                        days,
                                        begDateTime ,
                                        endDateTime,
                                        profileName,
                                        bedCodeName,
                                        personName,
                                        eventId,
                                        actionId
                                        ]
                                self._items.append(item)

            if not checkStationary and len(idList) == 1 and (eventId in list(idList)) and (eventId != prevEventId):
                idList = []
            if idList:
                fillTableAction(self.getReceivedAction(idList))
                fillTableAction(self.getMovingAction(idList))
                fillTableAction(self.getLeavedAction(idList))
        self.reset()


    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if role == Qt.DisplayRole:
            item = self._items[row]
            if column == 2:
                status = forceInt(item[column])
                return toVariant(CActionStatus.text(status))
            return toVariant(item[column])
        elif role == Qt.EditRole:
            item = self._items[row]
            newDate = item[column]
            if column == 5 and newDate:
               self._items[row][2] = 2
            elif not newDate:
                self._items[row][2] = 0
            return toVariant(newDate)
        return QVariant()


    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            column = index.column()
            row = index.row()
            self._items[row][column] = value
            self.emitCellChanged(row, column)
            return True
        return False


    def emitCellChanged(self, row, column):
        index = self.index(row, column)
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)


    def emitRowChanged(self, row):
        self.emitRowsChanged(row, row)


    def emitRowsChanged(self, begRow, endRow):
        index1 = self.index(begRow, 0)
        index2 = self.index(endRow, self.columnCount())
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index1, index2)


    def emitColumnChanged(self, column):
        index1 = self.index(0, column)
        index2 = self.index(self.rowCount(), column)
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index1, index2)


    def emitAllChanged(self):
        index1 = self.index(0, 0)
        index2 = self.index(self.rowCount(), self.columnCount())
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index1, index2)


    def createEditor(self, index, parent):
        column = index.column()
        return self._cols[column].createEditor(parent)


    def setEditorData(self, column, editor, value, record):
        return self._cols[column].setEditorData(editor, value, record)


    def getEditorData(self, column, editor):
        return self._cols[column].getEditorData(editor)


    def afterUpdateEditorGeometry(self, editor, index):
        pass


class CCheckPeriodActionsForEvent(CCheckPeriodActions):
    def __init__(self, parent, tabList, eventId, prevEventId = None, checkStationary = False):
        CDialogBase.__init__(self, parent)
        self.addModels('ActionList', CActionListForEventModel(self))
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setModels(self.tblActionList,  self.modelActionList, self.selectionModelActionList)
        self.currentEventId = eventId
        self.clientId = self.getClientIdForEvent()
        self.checkStationary = checkStationary
        self.btnSave.setVisible(False)
        self.tblActionList.model().loadData(tabList, self.currentEventId, prevEventId, self.checkStationary)


class CActionListForEventModel(CActionListModel):
    def flags(self, index=None):
#        column = index.column()
        result = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return result


