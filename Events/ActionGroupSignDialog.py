# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2025 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4                      import QtGui
from PyQt4.QtSql                import QSqlRecord, QSqlField
from PyQt4.QtCore               import pyqtSignature, QDate, Qt, QVariant, SIGNAL, QByteArray

from library.Identification import getIdentificationByCode
from library.RecordLock import CRecordLockMixin
from library.Utils import (forceInt,
                           forceString,
                           forceDate,
                           toVariant,
                           getPrefInt,
                           getPref,
                           setPref)
from Events.Utils               import getEventContextData
from Events.Action              import CActionTypeCache
from Events.ActionInfo          import CActionInfo
from library.PreferencesMixin   import CDialogPreferencesMixin
from library.DialogBase         import CConstructHelperMixin
from library.InDocTable         import (CRecordListModel,
                                        CBoolInDocTableCol,
                                        CTextInDocTableCol,
                                        CDateInDocTableCol,
                                        CEnumInDocTableCol,
                                        CRBInDocTableCol)
from library.PrintTemplates     import (getPrintTemplates,
                                        getTemplate,
                                        compileAndExecTemplate,
                                        htmlTemplate,
                                        svgTemplate,
                                        CTemplateExecutionResult)
from library.PrintInfo          import CInfoContext
from Ui_ActionGroupSignPage1    import Ui_ActionGroupSignPage1
from Reports.ReportView         import CReportViewDialog
from library.Attach.AttachButton import CAttachButton


class CActionGroupSignDialog(QtGui.QWizard, CDialogPreferencesMixin, CRecordLockMixin):
    # currentAttachButton - CAttachButton для алгоритма подписи (signAndAttachHandler)
    # currentAction - CAction для обновления списка прикрепленных файлов
    def __init__(self, parent=None, currentAttachButton=None, currentAction=None, innerAppLock=False, noFilters=False):
        QtGui.QWizard.__init__(self, parent)
        CRecordLockMixin.__init__(self)
        self.setObjectName(u'CActionGroupSignDialog')
        self.setWizardStyle(QtGui.QWizard.ModernStyle)
        self.setWindowFlags(Qt.Window)
        self.setWindowTitle(u'Групповое подписание и прикрепление')
        self.setOptions(QtGui.QWizard.NoBackButtonOnLastPage | \
                        QtGui.QWizard.NoBackButtonOnStartPage | \
                        QtGui.QWizard.NoCancelButton)
        self.records = []
        self.actionInfoMap = {}  # {actionId: CActionInfo}
        self.attachButton = CAttachButton(None)
        self.attachButton.setTable('Action_FileAttach')
        self.signAndAttachHandler = self.attachButton.getSignAndAttachHandler()
        self.currentAttachButton = currentAttachButton
        self.currentAction = currentAction

        self.innerAppLock = innerAppLock if not self.currentAction else False
        self.actionIdLockIdmap = {}
        self.actionRecordMap = {}
        self.allActionInfoLoaded = False
        
        if u'cactiongroupsigndialog' in QtGui.qApp.preferences.windowPrefs:
            self.loadDialogPreferences()
        else:  # первый запуск
            self.setWindowState(self.windowState() | Qt.WindowMaximized)
        self.addPage(CActionGroupSignPage1(self, noFilters))
        self.addPage(CActionGroupSignPage2(self))


    def setEventEditor(self, eventEditor):
        contextData = getEventContextData(eventEditor)
        n = 1
        for actionInfo in contextData['event'].actions:
            actionId = actionInfo.id
            if not actionId:
                # для маппинга еще не сохраненных действий используем
                # отрицательные значения, чтобы не было коллизий с уже сохраненными id
                actionId = -1 * (n * 10 + actionInfo.classId)  # вместо hash(actionInfo)
                n += 1
                # это хак! временно устанавливаем id записям, которые еще не сохранены
                actionInfo._record.setValue('id', toVariant(actionId))
            self.actionInfoMap[actionId] = actionInfo

            self.actionRecordMap[actionId] = actionInfo._record

        self.allActionInfoLoaded = True


    def setActionIdList(self, actionIdList):
        for actionId in actionIdList:
            record = QtGui.qApp.db.getRecord('Action', '*', actionId)
            if not record:
                continue
            if not self.innerAppLock:
                context = CInfoContext()
                status = forceInt(record.value('status'))
                personId = forceInt(record.value('person_id'))
                self.actionInfoMap[actionId] = CActionInfo(context, actionId)
                self.allActionInfoLoaded = True

            self.actionRecordMap[actionId] = record


    def exec_(self):
        result = QtGui.QWizard.exec_(self)
        self.saveDialogPreferences()
        index = self.page(0).cmbActionStatus.currentIndex()
        headerState = self.page(0).tblActions.savePreferences()
        setPref(QtGui.qApp.preferences.appPrefs, u'CActionGroupSignDialog_actionStatus', toVariant(index))
        setPref(QtGui.qApp.preferences.windowPrefs, u'CActionGroupSignDialog_headerState', headerState)

        # это хак! убираем временно установленный id для несохраненных действий
        for actionId, actionInfo in self.actionInfoMap.iteritems():
            if actionId < 0:
                actionInfo._record.setValue('id', QVariant())

        if self.currentAttachButton and self.currentAction:
            # текущее действие указано, значит файлы сохраняются, когда сохраняется это действие
            self.currentAttachButton.setAttachedFileItemList(self.currentAction.getAttachedFileItemList())
        else:
            # действия нет, прикрепленные файлы сохраняем сразу же
            if not self.innerAppLock:
                eventIdList = set()
                for actionInfo in self.actionInfoMap.itervalues():
                    action = actionInfo._action
                    action.save()
                    eventIdList.add(forceInt(actionInfo._record.value('event_id')))
                db = QtGui.qApp.db
                tableEvent = db.table('Event')
                db.query('UPDATE Event SET modifyDatetime = NOW() WHERE ' + tableEvent['id'].inlist(list(eventIdList)))

        # в идеале снимать блокировки по каждому экшену, тогда экшен.сйэв и ивент.модифай надо переносить...
        self.releaseActionLock()
            
        return result

    def releaseActionLock(self):
        if self.innerAppLock:
            for lockId in self._appLockIdList:
                try:
                    self.releaseLock(lockId)
                except:
                    QtGui.qApp.logCurrentException()


class CActionGroupSignPage1(QtGui.QWizardPage, Ui_ActionGroupSignPage1, CConstructHelperMixin):
    def __init__(self, parent, noFilters=False):
        QtGui.QWizardPage.__init__(self, parent)
        self.addModels('Actions', CActionsModel(self))
        self.setupUi(self)
        self.setBegDateDefault = QDate()
        self.setEndDateDefault = QDate()
        self.execBegDateDefault = QDate()
        self.execEndDateDefault = QDate()
        self.setButtonText(QtGui.QWizard.NextButton, u'Подписать и прикрепить')
        self.setModels(self.tblActions, self.modelActions, self.selectionModelActions)
        self.tblActions.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.tblActions.setSortingEnabled(True)
        self.tblActions.horizontalHeader().sectionClicked.disconnect()
        self.tblActions.horizontalHeader().sectionClicked.connect(self.on_sortByColumn)
        self.tblActions.horizontalHeader().setSortIndicator(0, Qt.AscendingOrder)
        self.loadPreferences()
        self.noFilters = noFilters


    def initializePage(self):
        begDates = []
        endDates = []
        if self.wizard().allActionInfoLoaded:
            for actionInfo in self.wizard().actionInfoMap.itervalues():
                if actionInfo.begDate.date:
                    begDates.append(actionInfo.begDate.date)
                if actionInfo.endDate.date:
                    endDates.append(actionInfo.endDate.date)
        else:
            for record in self.wizard().actionRecordMap.itervalues():
                if forceDate(record.value('begDate')):
                    begDates.append(forceDate(record.value('begDate')))
                if forceDate(record.value('endDate')):
                    endDates.append(forceDate(record.value('endDate')))
        if len(begDates) > 0:
            self.setBegDateDefault = min(begDates)
            self.setEndDateDefault = max(begDates)
        if len(endDates) > 0:
            self.execBegDateDefault = min(endDates)
            self.execEndDateDefault = max(endDates)
        if self.noFilters:
            self.disableAllFilters()
        else:
            self.on_btnResetFilters_clicked()


    def loadPreferences(self):
        status = getPrefInt(QtGui.qApp.preferences.appPrefs, u'CActionGroupSignDialog_actionStatus', 0)
        headerState = getPref(QtGui.qApp.preferences.windowPrefs, u'CActionGroupSignDialog_headerState', {})
        self.cmbActionStatus.setCurrentIndex(status)
        self.tblActions.loadPreferences(headerState)


    def isComplete(self):
        return bool(self.wizard()) and bool(self.wizard().signAndAttachHandler) and self.modelActions.hasChecked()


    def on_sortByColumn(self, col):
        order = self.tblActions.horizontalHeader().sortIndicatorOrder()
        self.modelActions.sortData(col, order == Qt.AscendingOrder)


    def getFilters(self):
        result = {}
        result['status'] = self.cmbActionStatus.currentIndex()
        result['withoutDocuments'] = self.chkWithoutDocuments.isChecked()
        result['exportSuitable'] = self.chkExportSuitable.isChecked()
        if self.chkSetDate.isChecked():
            result['setBegDate'] = self.edtSetBegDate.date()
            result['setEndDate'] = self.edtSetEndDate.date()
        if self.chkExecDate.isChecked():
            result['execBegDate'] = self.edtExecBegDate.date()
            result['execEndDate'] = self.edtExecEndDate.date()
        if self.chkPerson.isChecked():
            result['personId'] = self.cmbPerson.value()
        if self.chkSetPerson.isChecked():
            result['setPerson_id'] = self.cmbSetPerson.value()
        return result


    @pyqtSignature('')
    def on_btnResetFilters_clicked(self):
        try:
            # функция обновляла вью кратно количеству виджетов
            self.blockSignalsCustom(True)
            self.cmbActionStatus.setCurrentIndex(0)
            self.chkSetDate.setChecked(True)
            self.chkExecDate.setChecked(True)
            self.chkPerson.setChecked(False)
            self.cmbPerson.setValue(QtGui.qApp.userId)
            self.chkSetPerson.setChecked(False)
            self.cmbSetPerson.setValue(QtGui.qApp.userId)
            self.chkWithoutDocuments.setChecked(True)
            self.chkExportSuitable.setChecked(True)
            self.edtSetBegDate.setDate(self.setBegDateDefault)
            self.edtSetEndDate.setDate(self.setEndDateDefault)
            self.edtExecBegDate.setDate(self.execBegDateDefault)
            self.edtExecEndDate.setDate(self.execEndDateDefault)
        finally:
            self.blockSignalsCustom(False)
        self.updateActionsList()
        
    
    def disableAllFilters(self):
        try:
            # функция обновляла вью кратно количеству виджетов
            self.blockSignalsCustom(True)
            self.chkActionStatus.setVisible(False)
            self.cmbActionStatus.setCurrentIndex(0)
            self.cmbActionStatus.setVisible(False)
            self.chkSetDate.setChecked(False)
            self.chkSetDate.setVisible(False)
            self.edtSetBegDate.setDate(QDate())
            self.edtSetBegDate.setVisible(False)
            self.edtSetEndDate.setDate(QDate())
            self.edtSetEndDate.setVisible(False)
            self.chkExecDate.setChecked(False)
            self.chkExecDate.setVisible(False)
            self.edtExecBegDate.setDate(QDate())
            self.edtExecBegDate.setVisible(False)
            self.edtExecEndDate.setDate(QDate())
            self.edtExecEndDate.setVisible(False)
            self.chkPerson.setChecked(False)
            self.chkPerson.setVisible(False)
            self.cmbPerson.setValue(QtGui.qApp.userId)
            self.cmbPerson.setVisible(False)
            self.chkSetPerson.setChecked(False)
            self.chkSetPerson.setVisible(False)
            self.cmbSetPerson.setValue(QtGui.qApp.userId)
            self.cmbSetPerson.setVisible(False)
            self.chkWithoutDocuments.setChecked(False)
            self.chkExportSuitable.setChecked(False)
            self.chkWithoutDocuments.setVisible(False)
            self.chkExportSuitable.setVisible(False)
            self.btnResetFilters.setVisible(False)
        finally:
            self.blockSignalsCustom(False)
        self.updateActionsList()

    def blockSignalsCustom(self, state):
        for wgt in (
                self.cmbActionStatus,
                self.chkSetDate,
                self.chkExecDate,
                self.cmbPerson,
                self.cmbSetPerson,
                self.chkWithoutDocuments,
                self.chkExportSuitable,
                self.edtSetBegDate,
                self.edtSetEndDate,
                self.edtExecBegDate,
                self.edtExecEndDate
        ):
            wgt.blockSignals(state)


    def updateActionsList(self):
        self.modelActions.load(self.wizard(), self.getFilters())
        self.lblCountRecords.setText(u'Всего записей: ' + forceString(len(self.modelActions.items())))
        self.emit(SIGNAL('completeChanged()'))


    @pyqtSignature('int')
    def on_cmbActionStatus_currentIndexChanged(self, _):
        self.updateActionsList()


    @pyqtSignature('int')
    def on_cmbPerson_currentIndexChanged(self, _):
        self.updateActionsList()
    
    
    @pyqtSignature('int')
    def on_cmbSetPerson_currentIndexChanged(self, _):
        self.updateActionsList()


    @pyqtSignature('QDate')
    def on_edtSetBegDate_dateChanged(self, _):
        self.updateActionsList()


    @pyqtSignature('QDate')
    def on_edtSetEndDate_dateChanged(self, _):
        self.updateActionsList()


    @pyqtSignature('QDate')
    def on_edtExecBegDate_dateChanged(self, _):
        self.updateActionsList()


    @pyqtSignature('QDate')
    def on_edtExecEndDate_dateChanged(self, _):
        self.updateActionsList()


    @pyqtSignature('bool')
    def on_chkWithoutDocuments_toggled(self, _):
        self.updateActionsList()

    @pyqtSignature('bool')
    def on_chkExportSuitable_toggled(self, _):
        self.updateActionsList()


    @pyqtSignature('bool')
    def on_chkSetDate_toggled(self, _):
        self.updateActionsList()


    @pyqtSignature('bool')
    def on_chkExecDate_toggled(self, _):
        self.updateActionsList()


    @pyqtSignature('bool')
    def on_chkPerson_toggled(self, _):
        self.updateActionsList()
    
    
    @pyqtSignature('bool')
    def on_chkSetPerson_toggled(self, _):
        self.updateActionsList()


    @pyqtSignature('')
    def on_btnSelectAll_clicked(self):
        self.modelActions.selectAll()
        self.emit(SIGNAL('completeChanged()'))


    @pyqtSignature('')
    def on_btnClearAll_clicked(self):
        self.modelActions.deselectAll()
        self.emit(SIGNAL('completeChanged()'))


    @pyqtSignature('QModelIndex,QModelIndex')
    def on_selectionModelActions_currentChanged(self, currentIndex, _):
        currentIndex = self.tblActions.currentIndex()
        if not currentIndex.isValid():
            return
        record = self.modelActions.getRecordByRow(currentIndex.row())
        actionId = forceInt(record.value('id'))

        messageNotLocked = self.setActionLock(actionId)

        templateId = forceInt(record.value('templateId'))
        result, isError, type = getTempalteResult(self.wizard(), templateId, actionId)
        if type == svgTemplate:
            svgContent = "data:image/svg+xml;base64," + QByteArray(result.content.encode('utf-8')).toBase64().data()
            htmlContent = '<html><body><img src="{}" /></body></html>'.format(svgContent)
            self.txtReport.setHtml(htmlContent)
        else:
            self.txtReport.setHtml(result.content)

        if self.wizard().innerAppLock and messageNotLocked:
            QtGui.QMessageBox().warning(self.wizard(), u'Внимание!', messageNotLocked)
    
    def setActionLock(self, actionId):
        messageNotLocked = u''
        if self.wizard().innerAppLock and not self.wizard().actionIdLockIdmap.get(actionId, None):
            try:
                appLockId, messageNotLocked = self.wizard().tryLock('Action', actionId, shorted=1)
                if appLockId:
                    self.wizard().actionIdLockIdmap[actionId] = appLockId
            except:
                appLockId = None
                QtGui.qApp.logCurrentException()
            if appLockId is None:
                messageNotLocked += u' При подписании данные могут отличаться от отображаемых!'
            if not actionId < 0:
                self.wizard().actionInfoMap[actionId] = CActionInfo(CInfoContext(), actionId)
        return messageNotLocked
    
    
    @pyqtSignature('QModelIndex,QModelIndex')
    def on_modelActions_dataChanged(self, topLeft, bottomRight):
        row = topLeft.row()
        column = topLeft.column()
        if column == 5:
            record = self.modelActions.getRecordByRow(row)
            templateId = record.value('templateId')
            context = forceString(record.value('context'))
            if QtGui.QMessageBox().question(self, 
                                         u'Внимание!', 
                                         u'Изменить шаблон для всех документов данного типа?', 
                                         QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                        QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
                for item in self.modelActions.items():
                    if forceString(item.value('context')) == context:
                        item.setValue('templateId', templateId)

class CActionGroupSignPage2(QtGui.QWizardPage):
    def __init__(self, parent):
        QtGui.QWizardPage.__init__(self, parent)
        self.setCommitPage(True)
        self.setFinalPage(True)
        self.done = False
        self.progressBar = QtGui.QProgressBar()
        self.logBrowser = QtGui.QTextEdit()
        self.logBrowser.setReadOnly(True)
        self.btnAbort = QtGui.QPushButton(u'Прервать')
        self.lblStatus = QtGui.QLabel(u'пропущено: 0, подписано и прикреплено: 0')

        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(self.progressBar)
        layout.addWidget(self.logBrowser)
        layout.addWidget(self.lblStatus)
        layout.addWidget(self.btnAbort)

        self.isAborted = False
        self.signedCount = 0
        self.skippedCount = 0
        self.records = []
        self.reportView = CReportViewDialog(self)
        self.reportView.setSignAndAttachHandler(parent.signAndAttachHandler)
        self.btnAbort.clicked.connect(self.on_btnAbort_clicked)
        self.connect(self, SIGNAL('doProcess()'), self.process, Qt.QueuedConnection)


    def isComplete(self):
        return self.done


    def initializePage(self):
        self.records = self.wizard().page(0).modelActions.items()
        self.emit(SIGNAL('doProcess()'))


    def on_btnAbort_clicked(self):
        self.isAborted = True


    def process(self):
        checkedRecords = sum(forceInt(record.value('isChecked')) for record in self.records)
        self.progressBar.setMaximum(checkedRecords)
        self.progressBar.setValue(0)
        self.signedCount = 0
        self.skippedCount = 0
        self.signedExtCount = {}
        for record in self.records:
            if self.isAborted:
                break
            if forceInt(record.value('isChecked')):
                self.processRecord(record)
                self.progressBar.setValue(self.progressBar.value() + 1)
                self.lblStatus.setText(
                    u'пропущено: %d, подписано и прикреплено: %d,%s' % (
                    self.skippedCount, self.signedCount,
                    u', '.join(u' подписано {}: {}'.format(key, value) for key, value in self.signedExtCount.items())))
            QtGui.qApp.processEvents()
        self.done = True
        self.btnAbort.setEnabled(False)
        self.emit(SIGNAL('completeChanged()'))


    def processRecord(self, record):
        name = forceString(record.value('actionName'))
        code = forceString(record.value('actionCode'))
        templateId = forceInt(record.value('templateId'))
        actionId = forceInt(record.value('id'))

        if actionId > 0:
            actionInfoStr = '%s|%s (%d)' % (code, name, actionId)
        else:
            actionInfoStr = '%s|%s' % (code, name)

        if not self.setActionLock(actionId):
            self.logBrowser.append(u'%s - не удалось установить блокировку' % (actionInfoStr))
            self.skippedCount += 1
            return

        if not QtGui.qApp.getAllowUnsignedAttachments() and not QtGui.qApp.isCspDefined():
            self.logBrowser.append(u'%s - запрещено прикреплять документ без подписи' % (actionInfoStr))
            self.skippedCount += 1
            self.releaseActionLock(None, actionId)
            return

        try:
            result, isError, type = getTempalteResult(self.wizard(), templateId, actionId)
        except:
            result, isError = None, True
            QtGui.qApp.logCurrentException()
        if isError or result is None:
            self.logBrowser.append(u'%s - документ не сформирован' % (actionInfoStr))
            self.skippedCount += 1
            self.releaseActionLock(None, actionId)
            return

        self.reportView.fileName = result.documentName
        mainFileName = result.documentName + '.pdf'
        self.reportView.setText(result.content)
        self.reportView.setSupplements(dict(result.supplements))
        self.reportView.templateContent = result.content

        attachButton = self.wizard().attachButton
        actionInfo = self.wizard().actionInfoMap.setdefault(actionId, CActionInfo(CInfoContext(), actionId))
        action = actionInfo._action

        db = QtGui.qApp.db
        requireSignerPerson = forceInt(db.translate('rbPrintTemplate', 'id', templateId, 'requireSignerPerson'))
        if requireSignerPerson == 1:
            snils = actionInfo.setPerson.SNILS
            snils = snils.replace('-', '').replace(' ', '')
        else:
            snils = actionInfo.person.SNILS
            snils = snils.replace('-', '').replace(' ', '')

        try:
            ok, trail = self.reportView.signAndAttach(
                templateId=templateId,
                snils=snils,
                requireSignerPerson=requireSignerPerson,
                silent=True
                #action._actionType.isNeedAllMembersSign,
                #canSign=True,
                #signerIdList=[],
                #execPersonId=None,
            )
        except:
            ok, trail = False, [None]
            QtGui.qApp.logCurrentException()
        if ok:
            # это хак: перемещаем запись с подписанным файлом из кнопки в действие
            attachedFileRecordList = attachButton.modelFiles.items
            action._attachedFileItemList.extend(attachedFileRecordList)
            attachButton.setAttachedFileItemList([])
            self.signedCount += 1
            if trail[0]:
                self.logBrowser.append(u'%s - документ «%s» успешно сформирован,'\
                                       u' подписан и прикреплён' % (actionInfoStr, mainFileName))
                for filename in result.supplements.keys():
                    self.logBrowser.append(u'%s - документ «%s» успешно сформирован,'\
                                           u' подписан и прикреплён' % (actionInfoStr, result.documentName + '.' + filename))
                    self.signedExtCount[filename] = self.signedExtCount.setdefault(filename, 0) + 1
            else:
                self.logBrowser.append(u'%s - документ «%s» успешно сформирован,'\
                                       u' прикреплён без подписи' % (actionInfoStr, mainFileName))
                for filename in result.supplements.keys():
                    self.signedExtCount.setdefault(filename, 0)
                    self.logBrowser.append(u'%s - документ «%s» успешно сформирован,'\
                                           u' прикреплён без подписи' % (actionInfoStr, result.documentName + '.' + filename))
            self.isChanged = True
            actionInfo.isChanged = True
            if self.wizard().currentAttachButton and self.wizard().currentAction:
                self.wizard().currentAttachButton.modelFiles_changed()
        else:
            self.logBrowser.append(u'%s - документ не сформирован' % (actionInfoStr))
            self.skippedCount += 1

        self.releaseActionLock(actionInfo, actionId)

    def releaseActionLock(self, actionInfo, actionId):
        if self.wizard().innerAppLock:
            lockId = self.wizard().actionIdLockIdmap.get(actionId, None)
            if not lockId:
                return
            try:
                if actionInfo:
                    action = actionInfo._action
                    action.save()
                    tableEvent = QtGui.qApp.db.table('Event')
                    QtGui.qApp.db.query('UPDATE Event SET modifyDatetime = NOW() WHERE ' + tableEvent['id'].eq(
                        forceInt(actionInfo._record.value('event_id'))))
            except:
                QtGui.qApp.logCurrentException()
            try:
                self.wizard().releaseLock(lockId)
            except:
                QtGui.qApp.logCurrentException()

    def setActionLock(self, actionId):
        if self.wizard().innerAppLock and not self.wizard().actionIdLockIdmap.get(actionId, None):
            try:
                appLockId, _ = self.wizard().tryLock('Action', actionId, shorted=1)
                if appLockId:
                    self.wizard().actionIdLockIdmap[actionId] = appLockId
            except:
                appLockId = None
                QtGui.qApp.logCurrentException()
            if appLockId is None:
                return False
            if not actionId < 0:
                self.wizard().actionInfoMap[actionId] = CActionInfo(CInfoContext(), actionId)
        return True


class CLocRBInDocTableCol(CRBInDocTableCol):
    def setEditorData(self, editor, value, record):
        editor.setFilter('id IN (%s)' % forceString(record.value('templateIds')))
        editor.setValue(forceInt(value))


class CActionsModel(CRecordListModel):
    def __init__(self, parent):
        CRecordListModel.__init__(self, parent)
        self._parent = parent
        actionStatuses = (u'Начато', u'Ожидание', u'Закончено', u'Отменено', u'Без результата', u'Назначено', u'Отказ')
        self.addCol(CBoolInDocTableCol(u'Выбрать', 'isChecked', 20))
        self.addCol(CEnumInDocTableCol(u'Состояние', 'status', 40, actionStatuses, readOnly=True))
        self.addCol(CTextInDocTableCol(u'Действие', 'actionName', 40, readOnly=True))
        self.addCol(CDateInDocTableCol(u'Дата начала', 'begDate', 20, readOnly=True))
        self.addCol(CDateInDocTableCol(u'Дата окончания', 'endDate', 20, readOnly=True))
        self.addCol(CLocRBInDocTableCol(u'Шаблон', 'templateId', 40, 'rbPrintTemplate', addNone=False))

        self.actionTypeByUrnCodeMap = {}
        self.actionDocumentCountMap = {}


    def getEmptyRecord(self):
        record = QSqlRecord()
        record.append(QSqlField('id', QVariant.Int))
        record.append(QSqlField('idx', QVariant.Int))
        record.append(QSqlField('isChecked', QVariant.Bool))
        record.append(QSqlField('status', QVariant.Int))
        record.append(QSqlField('actionName', QVariant.String))
        record.append(QSqlField('actionCode', QVariant.String))
        record.append(QSqlField('begDate', QVariant.Date))
        record.append(QSqlField('endDate', QVariant.Date))
        record.append(QSqlField('templateId', QVariant.Int))  # id выбранного шаблона
        record.append(QSqlField('templateIds', QVariant.String))  # список id возможных шаблонов
        record.append(QSqlField('context', QVariant.String))
        return record


    def _isActionRecordSuitableByFilters(self, record, actionInfo, filters):
        status = filters.get('status', 0)
        personId = filters.get('personId', 0)
        setPersonId = filters.get('setPerson_id', 0)
        setBegDate = filters.get('setBegDate', None)
        setEndDate = filters.get('setEndDate', None)
        execBegDate = filters.get('execBegDate', None)
        execEndDate = filters.get('execEndDate', None)
        isWithoutDocuments = filters.get('withoutDocuments', False)
        isExportSuitable = filters.get('exportSuitable', False)

        if status > 0 and (status - 1) != forceInt(record.value('status')):
            return False
        if personId and personId != forceInt(record.value('person_id')):
            return False
        if setPersonId and setPersonId != forceInt(record.value('setPerson_id')):
            return False
        if setBegDate and forceDate(record.value('begDate')) < setBegDate:
            return False
        if setEndDate and forceDate(record.value('begDate')) > setEndDate:
            return False
        if execBegDate and forceDate(record.value('endDate')) < execBegDate:
            return False
        if execEndDate and forceDate(record.value('endDate')) > execEndDate:
            return False
        if isWithoutDocuments:
            if not self._isActionRecordSuitableByWithoutDocumentsFilter(record, actionInfo):
                return False
        if isExportSuitable:
            pdf, cda, observation = self._getActionRecordSuitableByExportVals(record, actionInfo)
            if not pdf and not cda and not observation:
                return False

        return True

    def _isActionRecordSuitableByWithoutDocumentsFilter(self, record, actionInfo):
        if actionInfo is not None:
            if len(actionInfo._action.getAttachedFileItemList()) > 0:
                return False
        else:
            if self.checkActionWithoutDocuments(forceInt(record.value('id'))) > 0:
                return False
        return True

    def _getActionRecordSuitableByExportVals(self, record, actionInfo):
        if actionInfo is not None:
            pdf = actionInfo.identifyInfoByCode('n3.medDocumentType.Pdf').value
            cda = actionInfo.identifyInfoByCode('n3.medDocumentType.Cda').value
            observation = actionInfo.identifyInfoByCode('n3.medDocumentType.Observation').value
        else:
            actionTypeId = forceInt(record.value('actionType_id'))
            pdf = self.identifyActionTypeByUrnCode(actionTypeId, 'n3.medDocumentType.Pdf')
            cda = self.identifyActionTypeByUrnCode(actionTypeId, 'n3.medDocumentType.Cda')
            observation = self.identifyActionTypeByUrnCode(actionTypeId, 'n3.medDocumentType.Observation')
        return pdf, cda, observation

    def identifyActionTypeByUrnCode(self, actionTypeId, code):
        if (actionTypeId, code) in self.actionTypeByUrnCodeMap:
            return self.actionTypeByUrnCodeMap[(actionTypeId, code)]
        # value = self.actionTypeByUrnCodeMap.get((actionTypeId, code), None)
        # if not value:
        value = self.actionTypeByUrnCodeMap[(actionTypeId, code)] = \
            getIdentificationByCode('ActionType', actionTypeId, code, raiseIfNonFound=False)
        return value

    def checkActionWithoutDocuments(self, actionId):
        if actionId in self.actionDocumentCountMap:
            return self.actionDocumentCountMap[actionId]
        # value = self.actionDocumentCountMap.get(actionId, None)
        # if not value:
        tableAFA = QtGui.qApp.db.table('Action_FileAttach')
        value = self.actionDocumentCountMap[actionId] = QtGui.qApp.db.getCount(tableAFA,
                                       where=[tableAFA['master_id'].eq(actionId), tableAFA['deleted'].eq(0)])
        return value



    def load(self, wizard, filters):
        itemsList = []
        for idx, actionInfo in enumerate(self.getActionMap(wizard)):
            isRecord = isinstance(actionInfo, QSqlRecord)
            record = actionInfo._record if not isRecord else actionInfo
            if not self._isActionRecordSuitableByFilters(record, actionInfo if not isRecord else None, filters):
                continue
            actionTypeId = forceInt(record.value('actionType_id'))
            actionType = CActionTypeCache.getById(actionTypeId) if actionTypeId else None
            context = actionType.context if actionType else ''
            if context:
                templates = getPrintTemplates(context)
                if templates:
                    templateIds = []
                    for t in templates[::-1]:
                        templateIds.append(t.id)
                        templateId = t.id
                    newRecord = self.getEmptyRecord()
                    newRecord.setValue('id', record.value('id'))
                    newRecord.setValue('idx', toVariant(idx))
                    newRecord.setValue('isChecked', toVariant(True))
                    newRecord.setValue('status', record.value('status'))
                    newRecord.setValue('actionName', toVariant(actionType.name))
                    newRecord.setValue('actionCode', toVariant(actionType.code))
                    newRecord.setValue('begDate', record.value('begDate'))
                    newRecord.setValue('endDate', record.value('endDate'))
                    newRecord.setValue('templateId', toVariant(templateId))
                    newRecord.setValue('templateIds', toVariant(','.join(map(str, templateIds))))
                    newRecord.setValue('context', context)
                    itemsList.append(newRecord)
        self.setItems(itemsList)

    def getActionMap(self, wizard):
        #условие or self.currentAction - если все переедет на рекорд
        return wizard.actionInfoMap.itervalues() if wizard.allActionInfoLoaded \
            else wizard.actionRecordMap.itervalues()


    def selectAll(self):
        for record in self._items:
            record.setValue('isChecked', toVariant(True))
        self.reset()


    def deselectAll(self):
        for record in self._items:
            record.setValue('isChecked', toVariant(False))
        self.reset()


    def hasChecked(self):
        for record in self._items:
            if forceInt(record.value('isChecked')) != 0:
                return True
        return False


    def setData(self, index, value, role=Qt.EditRole):
        result = CRecordListModel.setData(self, index, value, role)
        if index.column() == 5:  # переключить шаблон после изменения
            self._parent.on_selectionModelActions_currentChanged(index, None)
        elif index.column() == 0:
            self._parent.emit(SIGNAL('completeChanged()'))
        return result

class DisabledAttribute(object):
    def __call__(self, *args, **kwargs):
        raise UserWarning

    def __or__(self, other):
        return self

    def __ror__(self, other):
        return self

    def __getattr__(self, name):
        return self

    def __int__(self):
        return 0

class DisabledDialogMeta(type):
    def __getattr__(cls, name):
        return DisabledAttribute()

class DisabledMessageDialog(object):
    __metaclass__ = DisabledDialogMeta

    def __init__(self, *args, **kwargs):
        pass 

    def __getattr__(self, name):
        return DisabledAttribute()

class DisabledDialog(QtGui.QDialog):
    def exec_():
        raise UserWarning


def getTempalteResult(wizard, templateId, actionId):
    from Events.TeethEventInfo import CTeethEventInfo

    name, template, type_, printBlank, code = getTemplate(templateId, True)
    result = u''
    isError = False
    if type_ not in (htmlTemplate, svgTemplate):
        result = CTemplateExecutionResult(u'Ошибка',
            u'<HTML><BODY>Поддержка шаблонов печати в формате' \
            u' отличном от html или svg не реализована</BODY></HTML>',
            {},
            {})
        isError = True
        return result, isError, type_

    # actionInfo = wizard.actionInfoMap[actionId]
    actionInfo = wizard.actionInfoMap.setdefault(actionId, CActionInfo(CInfoContext(), actionId))
    eventInfo = actionInfo.getEventInfo(infoClass=CTeethEventInfo)
    data = {
        'event': eventInfo,
        'action': actionInfo,
        'actions': eventInfo.actions,
        'client': eventInfo.client,
        # запрещаем использовать диалоги, создавая ошибку
        'dialogs': DisabledDialog,
    }
    # TODO: найти другой способ создавать ошибку при вызове диалогов
    oldMessageBox = QtGui.QMessageBox
    oldDialog = QtGui.QDialog
    QtGui.QMessageBox = DisabledMessageDialog
    QtGui.QDialog = DisabledDialog

    # в CAction._properties оказываются только заполненные свойства
    # форсируем создание других свойств через обращение к ним
    for propName in actionInfo._action._actionType.getPropertiesByName():
        actionInfo._action.getProperty(propName)

    try:
        result = compileAndExecTemplate(name, template, data, templateId=templateId)
        if result.content is None:
            raise Exception
    except:
        result = CTemplateExecutionResult(
            u'Ошибка', u'<HTML><BODY>ОШИБКА ЗАПОЛНЕНИЯ ШАБЛОНА</BODY></HTML>', {}, {})
        isError = True
    finally:
        QtGui.QMessageBox = oldMessageBox
        QtGui.QDialog = oldDialog

    return result, isError, type_
