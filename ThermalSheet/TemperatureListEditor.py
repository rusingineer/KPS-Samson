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
from PyQt4.QtCore import pyqtSignature, QDateTime, QTime, QDate

from library.DialogBase   import CConstructHelperMixin
from library.Utils        import forceDate, forceDateTime, forceInt, forceRef, toVariant
from library.PrintTemplates import getPrintButton, applyTemplate
from library.PrintInfo      import CInfoContext, CInfoList
from Events.ActionInfo import CActionInfo
from Events.EventInfo import CEventInfo

from Events.Action        import CAction
from Events.ActionPropertiesTable import CActionPropertiesTableModel
from Events.ActionStatus  import CActionStatus
from Events.Utils         import setActionPropertiesColumnVisible
from Orgs.Utils           import getPersonOrgStructureChiefs
from Users.Rights         import urEditOtherpeopleAction, urEditThermalSheetPastDate, urEditSubservientPeopleAction

from Ui_TemperatureListEditor import Ui_TemperatureListEditor


class CTemperatureActionInfoList(CInfoList):
    def __init__(self, context, eventId):
        CInfoList.__init__(self, context)
        self.eventId = eventId
        self._idList = []

    def _load(self):
        db = QtGui.qApp.db
        tableAction = db.table('Action')
        tableAT = db.table('ActionType')
        table = tableAction.leftJoin(tableAT, tableAT['id'].eq(tableAction['actionType_id']))
        cond = [
            tableAT['flatCode'].like(u'temperatureSheet%'),
            tableAction['event_id'].eq(self.eventId),
            tableAction['deleted'].eq(0)
        ]
        self._idList = db.getIdList(table, tableAction['id'], cond, 'id')
        self._items = [ self.getInstance(CActionInfo, id) for id in self._idList ]
        return True

class CTemperatureListEditorDialog(QtGui.QDialog, CConstructHelperMixin, Ui_TemperatureListEditor):
    def __init__(self, parent, clientId, eventId, actionTypeIdList, clientSex, clientAge, setDate):
        QtGui.QDialog.__init__(self, parent)
        self.addModels('APActionProperties',   CActionPropertiesTableModel(self))
        self.setupUi(self)
        self.setModels(self.tblAPProps, self.modelAPActionProperties, self.selectionModelAPActionProperties)
        self.addObject('btnPrint', getPrintButton(self, 'temperatureList'))
        self.btnPrint.printByTemplate.connect(self.on_btnPrint_printByTemplate)
        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)
        self.clientId = clientId
        self.clientSex = clientSex
        self.clientAge = clientAge
        self.setDate = setDate.date() if setDate else None
        self.eventId = eventId
        self.actionTypeIdList = actionTypeIdList
        self.action = None
        self.timeList = {}
        self.isDirty = False
        currentDateTime = QDateTime.currentDateTime()
        self.edtDate.setDate(currentDateTime.date())
        self.edtTime.setTime(currentDateTime.time())
        self.cmbTimeEdit.setCurrentIndex(0)
        self.signHandler = parent.tabNotes.btnAttachedFiles.getSignAndAttachHandler() if parent and hasattr(parent, 'tabNotes') else None
        self.getTimeList()


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelAPActionProperties_dataChanged(self, topLeft, bottomRight):
        self.isDirty = True


    def canClose(self):
        if self.isDirty:
            res = QtGui.QMessageBox.warning( self,
                                      u'Внимание!',
                                      u'Данные были изменены.\nСохранить изменения?',
                                      QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                      QtGui.QMessageBox.Yes)
            if res == QtGui.QMessageBox.Yes:
                self.isDirty = False
                return True
        return False


    def closeEvent(self, event):
        if self.canClose():
            self.isDirty = False
            self.action.save()
        QtGui.QDialog.closeEvent(self, event)


    def updatePropTable(self, action):
        self.tblAPProps.model().setAction(action, self.clientId, self.clientSex, self.clientAge)
        self.tblAPProps.resizeRowsToContents()


    def createAction(self):
        self.action = None
        if self.clientId:
            db = QtGui.qApp.db
            tableAction = db.table('Action')
            date = self.edtDate.date()
            time = self.edtTime.time()
            execPersonId = self.cmbExecPerson.value()
            if not execPersonId:
                execPersonId = QtGui.qApp.userId
                self.cmbExecPerson.setValue(execPersonId)
            dialogDateTime = QDateTime(date, time)
            cond = [tableAction['deleted'].eq(0),
                    tableAction['event_id'].eq(self.eventId),
                    tableAction['actionType_id'].inlist(self.actionTypeIdList)
                    ]
            cond.append(tableAction['endDate'].eq(dialogDateTime))
            record = db.getRecordEx(tableAction, '*', cond)
            if record:
                execPersonId = forceRef(record.value('person_id'))
                if execPersonId:
                    self.cmbExecPerson.setValue(execPersonId)
                else:
                    self.cmbExecPerson.setValue(QtGui.qApp.userId)
                record.setValue('person_id', toVariant(execPersonId))
                self.action = CAction(record=record)
            else:
                actionTypeId = self.actionTypeIdList[0]
                if actionTypeId:
                    record = tableAction.newRecord()
                    record.setValue('event_id', toVariant(self.eventId))
                    record.setValue('actionType_id', toVariant(actionTypeId))
                    record.setValue('directionDate', toVariant(dialogDateTime))
                    record.setValue('begDate', toVariant(dialogDateTime))
                    record.setValue('endDate', toVariant(dialogDateTime))
                    record.setValue('status',  toVariant(2))
                    record.setValue('person_id', toVariant(execPersonId))
                    record.setValue('org_id',  toVariant(QtGui.qApp.currentOrgId()))
                    record.setValue('amount',  toVariant(1))
                    self.action = CAction(record=record)
            if self.action:
                tableEvent = db.table('Event')
                cols = [tableEvent['setDate']]
                cond = [tableEvent['deleted'].eq(0)]
                cond.append('Event.id = IF(getFirstEventId(%s) IS NOT NULL, getFirstEventId(%s), %s)'%(self.eventId, self.eventId, self.eventId))
                recordEvent = db.getRecordEx(tableEvent, cols, cond)
                setDate = (forceDate(recordEvent.value('setDate'))  if recordEvent else None)
                begDate = forceDate(record.value('begDate'))
                if setDate and begDate:
                    self.action[u'День болезни'] = setDate.daysTo(begDate) + 1
                setActionPropertiesColumnVisible(self.action._actionType, self.tblAPProps)
                self.updatePropTable(self.action)
                self.tblAPProps.setEnabled(self.getIsLocked(self.action._record))
        self.isDirty = False
        return self.action


    def getIsLocked(self, record):
        if record:
            status = forceInt(record.value('status'))
            personId = forceRef(record.value('person_id'))
            if status == CActionStatus.finished and personId:
                return ( QtGui.qApp.userId == personId
                                 or QtGui.qApp.userHasRight(urEditOtherpeopleAction)
                                 or (QtGui.qApp.userHasRight(urEditSubservientPeopleAction) and QtGui.qApp.userId in getPersonOrgStructureChiefs(personId))
                               )
        return False


    @pyqtSignature('QTime')
    def on_edtTime_timeChanged(self, time):
        if self.canClose():
            self.isDirty = False
            self.action.save()
        self.createAction()


    @pyqtSignature('QDate')
    def on_edtDate_dateChanged(self, date):
        if self.canClose():
            self.isDirty = False
            self.action.save()
        if QDate.currentDate() == date:
            isProtected = False
        else:
            isProtected = not QtGui.qApp.userHasRight(urEditThermalSheetPastDate)
        self.modelAPActionProperties.setReadOnly(isProtected)
        self.getTimeList()
        self.cmbTimeEdit.setCurrentIndex(0)
        self.createAction()


    @pyqtSignature('int')
    def on_cmbTimeEdit_currentIndexChanged(self, index):
        if index > 0:
            time = self.timeList.get(index, QTime())
            self.edtTime.setTime(time)
        else:
            currentDateTime = QDateTime.currentDateTime()
            self.edtTime.setTime(currentDateTime.time())
            self.cmbExecPerson.setValue(QtGui.qApp.userId)


    def getTimeList(self):
        self.timeList = {}
        countItems = self.cmbTimeEdit.count()
        countItem = countItems - 1
        while countItem > 0:
            self.cmbTimeEdit.removeItem(countItem)
            countItem -= 1
        if self.eventId and self.actionTypeIdList:
            db = QtGui.qApp.db
            tableAction = db.table('Action')
            date = forceDate(self.edtDate.date())
            cond = [tableAction['deleted'].eq(0),
                    tableAction['event_id'].eq(self.eventId),
                    tableAction['actionType_id'].inlist(self.actionTypeIdList)
                    ]
            cond.append(tableAction['endDate'].dateEq(date))
            records = db.getRecordList(tableAction, [tableAction['id'], tableAction['endDate']], cond, 'Action.endDate')
            idx = 1
            for record in records:
#                actionId = forceRef(record.value('id'))
                endDate = forceDateTime(record.value('endDate'))
                endTime = endDate.time()
                self.timeList[idx] = endTime
                self.cmbTimeEdit.insertItem(idx, endTime.toString('hh:mm'))
                idx += 1
        if len(self.timeList) > 0:
            endTime = self.timeList.get(idx-1, None)
            if endTime:
                self.lblLastTime.setText(endTime.toString('hh:mm'))
            else:
                self.lblLastTime.setText(u'')
        else:
            self.lblLastTime.setText(u'нет')

    def on_btnPrint_printByTemplate(self, templateId):
        context = CInfoContext()
        tempActionInfoList = CTemperatureActionInfoList(context, self.eventId)
        data = {'event': context.getInstance(CEventInfo, self.eventId),
                'tempActions': tempActionInfoList
                }
        applyTemplate(self, templateId, data, signAndAttachHandler=self.signHandler)


def log(name, text):
    print("%s: %s"%(name, text))

def logCurrentException():
    pass

if __name__ == '__main__':
    import sys
    import os
    import logging
    from library.Preferences import CPreferences
    from library.database import connectDataBase
    from Events.Utils import getActionTypeIdListByFlatCode
    from library.Utils import calcAge
    from library.Calendar import CCalendarInfo
    from library.PrintDebug.Utils import DebugPrintData
    app = QtGui.QApplication(sys.argv)
    app.userHasRight = lambda x: True
    app.documentEditor = lambda: ""
    app.enablePreview = lambda: True
    app.enableFastPrint = lambda: False
    app.highlightRedDate = lambda: False
    app.showPageSetup = lambda: True
    app.currentOrgId = lambda: 3178
    app.currentOrgStructureId = lambda: None
    app.getPrintTemplatesGroupsPlacing = lambda: 2
    app.defaultKLADR = lambda: None
    app.provinceKLADR = lambda: None
    app.getTemplateDir = lambda: ""
    app.isPrintDebugEnabled = False
    app.log = log
    app.logCurrentException = logCurrentException
    app.userId = 1
    QtGui.qApp = app
    app.calendarInfo = CCalendarInfo(app)

    preferences = CPreferences("100")
    iniFileName = preferences.getSettings().fileName()
    if not os.path.exists(iniFileName):
        print("ini file (%s) not exists") % iniFileName
        app.quit()
    preferences.load()
    settings = preferences.getSettings()
    app.preferences = preferences

    app.getPathToDictionary = lambda: None
    app.showingSpellCheckHighlight = lambda: False

    app.isPrintDebugEnabled = True
    app.debugPrintData = DebugPrintData()

    debug = False
    #clientId = 292604
    #eventId = 4639520
    clientId = 92304
    eventId = 4702550

    db = connectDataBase(preferences.dbDriverName,
                                 preferences.dbServerName,
                                 preferences.dbServerPort,
                                 preferences.dbDatabaseName,
                                 preferences.dbUserName,
                                 preferences.dbPassword,
                                 compressData = preferences.dbCompressData,
                                 logger = logging.getLogger('DB') if debug else None)
    app.db = db

    actionTypeIdList = getActionTypeIdListByFlatCode(u'temperatureSheet%')
    tableClient = db.table('Client')
    clientRecord = db.getRecordEx(tableClient, [tableClient['sex'], tableClient['birthDate']],
                                  [tableClient['id'].eq(clientId), tableClient['deleted'].eq(0)])
    clientSex = forceInt(clientRecord.value('sex'))
    clientAge = calcAge(forceDate(clientRecord.value('birthDate')), QDate.currentDate())
    dialog = CTemperatureListEditorDialog(None, clientId, eventId, actionTypeIdList, clientSex, clientAge, QDateTime(2022, 10, 13, 0, 0))
    app.mainWindow = dialog
    dialog.exec_()
    print('qq')
