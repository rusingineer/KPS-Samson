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
from PyQt4.QtCore import Qt, pyqtSignature, QString, QVariant

from library.exception            import CException
from library.Counter              import CCounterController
from library.DialogBase           import CDialogBase
from library.PrintTemplates       import applyTemplate, customizePrintButton, getPrintButton
from library.PrintInfo            import CInfoContext, CInfoList
from library.Utils                import forceInt, forceString

from Events.ActionInfo            import CActionInfo, CPropertyInfo
from Events.Utils                 import checkTissueJournalStatusByActions

from Registry.ClientEditDialog    import CClientEditDialog
from Registry.Utils               import getClientInfo, getClientBanner

from TissueJournal.TissueJournalModels import CActionEditorModel, CPropertiesEditorModel
from TissueJournal.TissueStatus   import CTissueStatus

from Users.Rights                 import urAdmin, urRegTabReadRegistry, urRegTabWriteRegistry

from Ui_ActionTableEditor         import Ui_ActionTableEditorDialog


class CActionTableEditor(CDialogBase, Ui_ActionTableEditorDialog):
    def __init__(self, parent, tissueJournalModel=None, onlyProperties=False):
        CDialogBase.__init__(self, parent)
        self.addObject('btnPrint', getPrintButton(self, ''))
        customizePrintButton(self.btnPrint, 'actionTableEditor')
        self.addObject('actEditClient', QtGui.QAction(u'Открыть регистрационную карточку', self))
        if onlyProperties:
            model = CPropertiesEditorModel
        else:
            model = CActionEditorModel
        self.addModels('ActionEditor', model(self))

        self.setupUi(self)

        self._tissueJournalModel = tissueJournalModel
        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)
        self.setModels(self.tblActions, self.modelActionEditor, self.selectionModelActionEditor)
        self.setWindowTitleEx(u'Табличный редактор')
        self.setupDirtyCather()
        self._actionIdList = []
        self._mapIdToInfo  = {}
        self._tissueRecordInfoById = {}
        self.currentClientId = None
#        self.connect(self.btnPrint, SIGNAL('printByTemplate(int)'), self.on_btnPrint_printByTemplate)
#        self.connect(self.selectionModelActionEditor,
#                     SIGNAL('currentChanged(QModelIndex, QModelIndex)'),
#                     self.on_selectionModelActionEditor_currentChanged)
        self.txtClientInfoBrowser.actions.append(self.actEditClient)
        self.actEditClient.setEnabled(False)


    def setTissueJournalIdList(self, tissueJournalIdList, actionIdList=None):
        self.setVerticalHeaderViewModeByTissueJournalIdCount(len(tissueJournalIdList))
        if actionIdList is None:
            db = QtGui.qApp.db
            table = db.table('Action')
            actionIdList = db.getIdList(table, 'id',
                                        table['takenTissueJournal_id'].inlist(tissueJournalIdList),
                                        table['takenTissueJournal_id'].name())
        self.setActionIdList(actionIdList, False)


    def setTissueRecordInfo(self, info):
        actionTypeTextInfo = self.modelActionEditor.getActionTypeTextInfo(self.tblActions.currentIndex())
        if actionTypeTextInfo:
            info = info + u'\nТип действия: %s'%actionTypeTextInfo
        self.lblTissueJournalRecordInfo.setText(info)


    def setCurrentClient(self, clientId):
        if self.currentClientId != clientId:
            self.currentClientId = clientId
            clientInfo = self._mapIdToInfo.get(clientId, None)
            if not clientInfo:
                self._mapIdToInfo[clientId] = clientInfo = getClientInfo(clientId)
            clientBanner = getClientBanner(self.currentClientId)
            self.txtClientInfoBrowser.setHtml(clientBanner)
            self.actEditClient.setEnabled(self.currentClientId and QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]))


    def updateClientInfo(self):
        self._mapIdToInfo[self.currentClientId] = clientInfo = getClientInfo(self.currentClientId)
        clientBanner = getClientBanner(self.currentClientId)
        self.txtClientInfoBrowser.setHtml(clientBanner)


    def setActionIdList(self, actionIdList, checkTakenTissueCount=True):
        if checkTakenTissueCount:
            db = QtGui.qApp.db
            table = db.table('Action')
            cond = [table['id'].inlist(actionIdList)]
            record = db.getRecordEx(table, 'COUNT(DISTINCT takenTissueJournal_id) AS tissueJournalIdCount', cond)
            tissueJournalIdCount = forceInt(record.value('tissueJournalIdCount')) if record else 0
            self.setVerticalHeaderViewModeByTissueJournalIdCount(tissueJournalIdCount)
        self._actionIdList = actionIdList
        self.modelActionEditor.setActionIdList(actionIdList)
        self.tblActions.setFocus(Qt.OtherFocusReason)
        self.tblActions.setCurrentIndex(self.modelActionEditor.firstAvailableIndex())


    def setVerticalHeaderViewModeByTissueJournalIdCount(self, tissueJournalIdCount):
        if tissueJournalIdCount > 1:
            self.modelActionEditor.setVerticalHeaderViewIdentifiersMode()
        else:
            self.modelActionEditor.setVerticalHeaderViewActionTypeMode()


    def setClientId(self, clientId):
        self.modelActionEditor.setClientId(clientId)


    def formatTissueRecordInfo(self, id):
        rows = self._tissueRecordInfoById.setdefault(id, [])
        if not rows:
            if self._tissueJournalModel:
                model = self._tissueJournalModel
                modelIdList = model.idList()
                if id in modelIdList:
                    row = modelIdList.index(id)
                else:
                    return ''
                tissueType = forceString(model.data(model.index(row, 2)))
                identifier = forceString(model.data(model.index(row, 3)))
                status     = forceString(model.data(model.index(row, 4)))
                date       = forceString(model.data(model.index(row, 5)))
            else:
                db = QtGui.qApp.db
                record     = db.getRecord('TakenTissueJournal',
                                          'tissueType_id, externalId, status, datetimeTaken',
                                          id)
                tissueType = forceString(db.translate('rbTissueType', 'id', record.value('tissueType_id'), 'name'))
                identifier = forceString(record.value('externalId'))
                status     = CTissueStatus.text(forceInt(record.value('status')))
                date       = forceString(record.value('datetimeTaken'))
            rows.append(u'Тип биоматериала: %s'%tissueType)
            rows.append(u'Идентификатор: %s'%identifier)
            rows.append(u'Статус: %s'%status)
            rows.append(u'Дата забора: %s'%date)
        return u', '.join(rows)


    def exec_(self):
        self.loadDialogPreferences()
        self.setWindowState(Qt.WindowMaximized)

        QtGui.qApp.setCounterController(CCounterController(self))
        QtGui.qApp.setJTR(self)
        try:
            result = QtGui.QDialog.exec_(self)
        finally:
            QtGui.qApp.unsetJTR(self)

        if result:
            QtGui.qApp.delAllCounterValueIdReservation()
        else:
            QtGui.qApp.resetAllCounterValueIdReservation()
        QtGui.qApp.setCounterController(None)
        return result


    def saveData(self):
        QtGui.qApp.callWithWaitCursor(self, self.save)
        return True


    def save(self):
        listForTissueJournalStatusChecking = self.modelActionEditor.saveItems()
        for actionItem, propertiesDictItem in self.modelActionEditor.itemsForDeleting():
            actionRecord = actionItem.getRecord()
            actionRecord.setValue('deleted', QVariant(1))
            QtGui.qApp.db.updateRecord('Action', actionRecord)
        checkTissueJournalStatusByActions(listForTissueJournalStatusChecking)


    def getClientIdByTakenTissueJournalId(self, takenTissueJournalId):
        return self.modelActionEditor.getClientIdByTakenTissueJournalId(takenTissueJournalId)


    @pyqtSignature('')
    def on_actEditClient_triggered(self):
        if QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]):
            dialog = CClientEditDialog(self)
            try:
                dialog.load(self.currentClientId)
                if dialog.exec_():
                    self.updateClientInfo()
            finally:
                dialog.deleteLater()


    @pyqtSignature('int')
    def on_btnPrint_printByTemplate(self, templateId):
        context = CInfoContext()
        actionsInfo = context.getInstance(CActionTableEditorInfoList, tuple(self._actionIdList))
        data = { 'actions' : actionsInfo}
        applyTemplate(self, templateId, data)


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelActionEditor_currentChanged(self, current, previous):
        row = current.row()
        previousRow = previous.row()
        if previousRow != row:
            takenTissueJournalId = self.modelActionEditor.getTakenTissueJournalId(row)
            self.setTissueRecordInfo(self.formatTissueRecordInfo(takenTissueJournalId))
            self.setCurrentClient(self.getClientIdByTakenTissueJournalId(takenTissueJournalId))



# ###################################################################
class CActionTableEditorInfo(CActionInfo):

    def isVisible(self, propertyType):
        return propertyType.visibleInTableEditor == 1 # видно в табличном редакторе и редактрируемо


    def __getitem__(self, key):
        if isinstance(key, (basestring, QString)):
            try:
                property = self._action.getProperty(unicode(key))
                propertyType = property.type()
                if self.isVisible(propertyType):
                    return self.getInstance(CPropertyInfo, property)
                else:
                    actionType = self._action.getType()
                    raise CException(u'У действия типа "%s" свойство "%s" не выводится в табличном редакторе' % (
                                                        actionType.name, unicode(key))
                                    )
            except KeyError:
                actionType = self._action.getType()
                raise CException(u'Действие типа "%s" не имеет свойства "%s"' % (actionType.name, unicode(key)))
        if isinstance(key, (int, long)):
            try:
                return self.getInstance(CPropertyInfo, self._action.getPropertyByIndex(key))
            except IndexError:
                actionType = self._action.getType()
                raise CException(u'Действие типа "%s" не имеет свойства c индексом "%s"' % (actionType.name, unicode(key)))
        else:
            raise TypeError, u'Action property subscription must be string or integer'


    def __iter__(self):
        for property in self._action.getProperties():
            if self.isVisible(property.type()):
                yield self.getInstance(CPropertyInfo, property)



class CActionTableEditorInfoList(CInfoList):
    def __init__(self, context, idList):
        CInfoList.__init__(self, context)
        self._idList = idList

    def _load(self):
        self._items = [ self.getInstance(CActionTableEditorInfo, id) for id in self._idList ]
        return True


