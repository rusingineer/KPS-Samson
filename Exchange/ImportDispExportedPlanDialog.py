# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui, QtSql
from PyQt4.QtCore import *

import Exchange.AttachService as AttachService

from library.DialogBase import CDialogBase
from library.TableModel import CTableModel, CTextCol, CDateCol, CEnumCol, CBoolCol, CIntCol, CDesignationCol, CCol
from library.Utils import *

from Registry.ClientEditDialog import CClientEditDialog

from Users.Rights import urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry

from Ui_ImportDispExportedPlanDialog import Ui_ImportDispExportedPlanDialog
from Ui_ImportDispExportedPlanSyncDialog import Ui_ImportDispExportedPlanSyncDialog

class CImportDispExportedPlanDialog(CDialogBase, Ui_ImportDispExportedPlanDialog):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.addModels('ExportedPlan', CExportedPlanModel(self))
        self.addModels('ExportedPlanErrors', CExportedPlanErrorsModel(self))
        self.addObject('actEditClient', QtGui.QAction(u'Открыть регистрационную карточку', self))
        self.setupUi(self)
        self.setWindowFlags(Qt.Window)
        self.actEditClient.setEnabled(QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]))
        self.tblExportedPlan.createPopupMenu([self.actEditClient])
        self.pbDeleteProgress.setVisible(False)
        self.lblDeleteStatus.setVisible(False)
        self.connect(self.modelExportedPlan, SIGNAL('deleteSelectionChanged(int)'), self.deleteSelectionChanged)
        currentDate = QDate.currentDate()
        self.sbYear.setValue(currentDate.year())
        self.cmbMonth.setCurrentIndex(currentDate.month() - 1)
        self.setModels(self.tblExportedPlan, self.modelExportedPlan, self.selectionModelExportedPlan)
        self.setModels(self.tblExportedPlanErrors, self.modelExportedPlanErrors, self.selectionModelExportedPlanErrors)
        header = self.tblExportedPlan.horizontalHeader()
        header.setSortIndicatorShown(True)
        header.setSortIndicator(0, Qt.AscendingOrder)
        QObject.connect(header, SIGNAL('sectionClicked(int)'), self.setSort)
        self.edit_fio.setText("")
        self.update()

    def disableControls(self, disabled = True):
        self.sbYear.setDisabled(disabled)
        self.cmbMonth.setDisabled(disabled)
        self.cmbKind.setDisabled(disabled)
        self.btnRefresh.setDisabled(disabled or self.cmbKind.currentIndex() != 0)
        self.btnClose.setDisabled(disabled)
        self.btnSelectNotFound.setDisabled(disabled)
        self.btnSelectAll.setDisabled(disabled)
        self.btnDeleteSelected.setDisabled(disabled or len(self.modelExportedPlan.deleteIdSet) == 0)
        self.btnSyncMIS.setDisabled(disabled or self.modelExportedPlan.rowCount() == 0)
        QtGui.qApp.processEvents()

    def enableControls(self):
        self.disableControls(False)
    
    def update(self):
        year = self.sbYear.value()
        month = self.cmbMonth.currentIndex() + 1
        kind = self.cmbKind.currentIndex()
        name = forceString(self.edit_fio.text())
        self.disableControls()
        try:
            self.modelExportedPlan.update(year, month, kind, name)
            self.btnSyncMIS.setEnabled(self.modelExportedPlan.rowCount() > 0)
            self.updateCountLabel()
        finally:
            self.enableControls()
    
    def updateCountLabel(self):
        totalCount = self.modelExportedPlan.rowCount()
        foundCount = self.modelExportedPlan.foundCount
        invalidCssCount = self.modelExportedPlan.invalidCssCount
        clientNotFoundCount = self.modelExportedPlan.clientNotFoundCount
        self.lblExpPlanCount.setText(u"На сервисе %d записей, соответствие с БД ЛПУ: %d найдено, %d нет соответствия, %d не найдено" % (totalCount, foundCount, invalidCssCount, clientNotFoundCount))

    def refresh(self):
        year = self.sbYear.value()
        month = self.cmbMonth.currentIndex() + 1
        kind = self.cmbKind.currentIndex()
        name = forceString(self.edit_fio.text())
        self.disableControls()
        try:
            response = AttachService.updateExportedPlan(year, month)
            self.modelExportedPlan.update(year, month, kind, name)
            self.updateCountLabel()
        except Exception as e:
            QtGui.QMessageBox.critical(self, u'Произошла ошибка', exceptionToUnicode(e), QtGui.QMessageBox.Close)
        finally:
            self.enableControls()
    
    def deleteSelectionChanged(self, count):
        self.btnDeleteSelected.setText(u'Удалить выбранные (%d)' % (count,))
        self.btnDeleteSelected.setEnabled(count > 0)
    
    def deleteSelected(self):
        successCount = 0
        errorCount = 0
        deleteIdList = list(self.modelExportedPlan.deleteIdSet)
        totalCount = len(deleteIdList)
        self.pbDeleteProgress.setVisible(True)
        self.pbDeleteProgress.setValue(0)
        self.pbDeleteProgress.setMaximum(totalCount)
        self.lblDeleteStatus.setVisible(True)
        self.lblDeleteStatus.setText(u'Отправка пакетов...')
        packageSize = 1000
        self.disableControls()
        QtGui.qApp.setWaitCursor()
        try:
            while deleteIdList:
                ids = deleteIdList[0:packageSize]
                deleteIdList = deleteIdList[packageSize:]
                QtGui.qApp.processEvents()
                result = AttachService.deleteExportedPlan(ids)
                successCount = successCount + result['successCount']
                errorCount = errorCount + result['errorCount']
                acceptedCount = successCount + errorCount
                notAcceptedCount = totalCount - acceptedCount
                self.pbDeleteProgress.setValue(self.pbDeleteProgress.value() + len(ids))
            labelText = (u'Удаление завершено: отправлено %d записей' % totalCount)
            if totalCount > 0:
                labelParts = []
                if successCount > 0:
                    labelParts.append(u'%d удалено' % successCount)
                if errorCount > 0:
                    labelParts.append(u'%d с ошибками' % errorCount)
                if notAcceptedCount > 0:
                    labelParts.append(u'%d не принято' % notAcceptedCount)
                labelText += (u', из них ' + u', '.join(labelParts))
            self.lblDeleteStatus.setText(labelText)                
        except Exception as e:
            self.lblDeleteStatus.setText(u'Ошибка: ' + exceptionToUnicode(e))
        finally:
            QtGui.qApp.restoreOverrideCursor()
            self.update()
            self.pbDeleteProgress.setVisible(False)
    
    def syncMIS(self):
        year = self.sbYear.value()
        month = self.cmbMonth.currentIndex() + 1
        kind = self.cmbKind.currentIndex()
        monthName = self.cmbMonth.currentText()
        self.disableControls()
        db = QtGui.qApp.db
        db.transaction()
        try:
            # все записи с сервиса
            kindFilter1 = ""
            kindFilter2 = ""
            if kind == 1:
                kindFilter1 = "and ExpPlan.kind = 1 and ExpPlan.category not in (101, 102, 111, 112, 113, 114, 121, 122)"
                kindFilter2 = "and SST.code = 'disp'"
            elif kind == 2:
                kindFilter1 = "and ExpPlan.kind = 1 and ExpPlan.category = 102"
                kindFilter2 = "and SST.code = 'disp_2'"
            elif kind == 3:
                kindFilter1 = "and ExpPlan.kind = 2"
                kindFilter2 = "and SST.code = 'prof'"
            elif kind == 4:
                kindFilter1 = "and ExpPlan.kind = 1 and ExpPlan.category in (101, 111, 112, 113, 114)"
                kindFilter2 = "and SST.code = 'disp_1'"
            elif kind == 5:
                kindFilter1 = "and ExpPlan.kind = 1 and ExpPlan.category = 121"
                kindFilter2 = "and SST.code = 'disp_cov1'"
            elif kind == 6:
                kindFilter1 = "and ExpPlan.kind = 1 and ExpPlan.category = 122"
                kindFilter2 = "and SST.code = 'disp_cov2'"

            stmt = u"""
                select ExpPlan.id,
                    (case when ExpPlan.kind = 1 and ExpPlan.category in (101, 111, 112, 113, 114) then 4
                          when ExpPlan.kind = 1 and ExpPlan.category = 102 then 3
                          when ExpPlan.kind = 1 and ExpPlan.category = 121 then 5
                          when ExpPlan.kind = 1 and ExpPlan.category = 122 then 6
                          else ExpPlan.kind
                          end) as expKind,
                    Client.id as client_id,
                    CSS.id as clientSocStatus_id,
                    month(CSS.begDate) as cssMonth,
                    (case SST.code
                        when 'disp' then 1
                        when 'prof' then 2
                        when 'disp_2' then 3
                        when 'disp_1' then 4
                        when 'disp_cov1' then 5
                        when 'disp_cov2' then 6
                    end) as cssKind,
                    PlanExport.id as planExport_id,
                    PlanExport.exportSuccess
                from disp_ExportedPlan as ExpPlan
                    left join Client on Client.id = (
                        select max(C.id)
                        from Client as C
                        where C.lastName = ExpPlan.a15_pfio
                            and C.firstName = ExpPlan.a16_pnm
                            and coalesce(C.patrName, '') = coalesce(ExpPlan.a17_pln, '')
                            and C.birthDate = ExpPlan.a19_pbd
                            and C.deleted = 0
                    )
                    left join ClientSocStatus as CSS on CSS.client_id = Client.id
                        and CSS.deleted = 0
                        and CSS.socStatusClass_id in (select id from rbSocStatusClass where code = 'profilac')
                        and (
                            CSS.socStatusType_id in (select id from rbSocStatusType where code in ('disp', 'disp_2', 'disp_1', 'prof')) and ExpPlan.category not in (121, 122)
                            or CSS.socStatusType_id in (select id from rbSocStatusType where code in ('disp_cov1', 'disp_cov2')) and ExpPlan.category in (121, 122)
                        )
                        and year(CSS.begDate) = ExpPlan.year
                    left join rbSocStatusType as SST on SST.id = CSS.socStatusType_id
                    left join disp_PlanExport as PlanExport on PlanExport.exportKind = 'ClientSocStatus' and PlanExport.row_id = CSS.id
                where ExpPlan.year = %d and ExpPlan.mnth = %d and ExpPlan.kind in (1, 2)
                    %s
                """ % (year, month, kindFilter1)
            query = db.query(stmt)
            notFoundClientIdList = []
            cssToInsert = []
            cssToDelete = set()
            planExportToInsert = []
            planExportToUpdate = []
            planExportToDelete = set()
            notFoundCSSToDelete = set()
            notFoundCSSPlanExportToDelete = set()
            cssInfoByGroup = {}
            while query.next():
                record = query.record()
                expPlanId = forceRef(record.value('id'))
                clientId = forceRef(record.value('client_id'))
                if clientId is None:
                    # клиент не найден, ничего не делать
                    notFoundClientIdList.append(clientId)
                    continue
                cssId = forceRef(record.value('clientSocStatus_id'))
                expKind = forceInt(record.value('expKind'))
                if expKind in (5, 6):
                    expKindGroup = 2
                else:
                    expKindGroup = 1
                cssGroupKey = (clientId, expKindGroup)
                if cssGroupKey in cssInfoByGroup:
                    currentCssInfo = cssInfoByGroup[cssGroupKey]
                else:
                    currentCssInfo = {'validCssId': None, 'kind': expKind, 'month': month}
                    cssInfoByGroup[cssGroupKey] = currentCssInfo

                if cssId is None:
                    # соц. статусов за этот год нет вообще
                    continue
                cssKind = forceInt(record.value('cssKind'))
                cssMonth = forceInt(record.value('cssMonth'))
                planExportId = forceRef(record.value('planExport_id'))
                if cssMonth != month or cssKind != expKind:
                    # месяц или тип не совпадают, удаляем соц. статус
                    cssToDelete.add(cssId)
                    if planExportId is not None:
                        planExportToDelete.add(planExportId)
                    continue
                validCssId = currentCssInfo['validCssId']
                if validCssId and validCssId != cssId:
                    # уже есть другой подходящий соц. статус, все равно удаляем
                    cssToDelete.add(cssId)
                    if planExportId is not None:
                        planExportToDelete.add(planExportId)
                    continue
                # это подходящий соцстатус, ничего с ним не делаем
                currentCssInfo['validCssId'] = cssId
                exportSuccess = forceInt(record.value('exportSuccess'))
                if planExportId is None:
                    # признака выгрузки нет вообще, нужно добавить
                    planExportToInsert.append({'cssId': cssId, 'clientId': clientId, 'month': month})
                elif exportSuccess != 1:
                    # признак выгрузки неправильный, нужно поменять
                    planExportToUpdate.append({'planExportId': planExportId})
            for cssGroupKey, cssInfo in cssInfoByGroup.items():
                clientId, expKindGroup = cssGroupKey
                if cssInfo['validCssId'] is None:
                    cssToInsert.append({'clientId': clientId, 'kind': cssInfo['kind'], 'month': cssInfo['month']})

            # соцстатусы, не найденные на сервисе
            stmt = u"""
                select CSS.id as clientSocStatus_id,
                    PlanExport.id as planExport_id,
                    PlanExport.exportSuccess
                from ClientSocStatus as CSS
                    left join disp_PlanExport as PlanExport on PlanExport.exportKind = 'ClientSocStatus' and PlanExport.row_id = CSS.id
                    left join Client on Client.id = CSS.client_id
                    left join rbSocStatusClass as SSC on SSC.id = CSS.socStatusClass_id
                    left join rbSocStatusType as SST on SST.id = CSS.socStatusType_id
                    left join disp_ExportedPlan as ExpPlan on ExpPlan.id = (
                        select max(ExpPlan.id)
                        from disp_ExportedPlan as ExpPlan
                        where ExpPlan.a15_pfio = Client.lastName
                            and ExpPlan.a16_pnm = Client.firstName
                            and coalesce(ExpPlan.a17_pln, '') = coalesce(Client.patrName, '')
                            and ExpPlan.a19_pbd = Client.birthDate
                            and ExpPlan.year = year(CSS.begDate)
                            and ExpPlan.mnth = month(CSS.begDate)
                            and ExpPlan.kind in (1, 2)
                            and (
                                ExpPlan.kind = 1 and SST.code = 'disp'
                                or ExpPlan.kind = 2 and SST.code = 'prof'
                                or ExpPlan.kind = 1 and ExpPlan.category = 102 and SST.code = 'disp_2'
                                or ExpPlan.kind = 1 and ExpPlan.category in (101, 111, 112, 113, 114) and SST.code = 'disp_1'
                                or ExpPlan.kind = 1 and ExpPlan.category = 121 and SST.code = 'disp_cov1'
                                or ExpPlan.kind = 1 and ExpPlan.category = 122 and SST.code = 'disp_cov2'
                            )
                    )
                where CSS.deleted = 0
                    and Client.deleted = 0
                    and SSC.code = 'profilac'
                    and SST.code in ('disp', 'disp_2', 'disp_1', 'prof', 'disp_cov1', 'disp_cov2')
                    and ExpPlan.id is null
                    and year(CSS.begDate) = %d
                    and month(CSS.begDate) = %d
                    %s
                """ % (year, month, kindFilter2)
            query = db.query(stmt)
            while query.next():
                record = query.record()
                cssId = forceRef(record.value('clientSocStatus_id'))
                planExportId = forceRef(record.value('planExport_id'))
                # удалить соц. статус, если будет отмечен чекбокс
                notFoundCSSToDelete.add(cssId)
                if planExportId is not None:
                    exportSuccess = forceInt(record.value('exportSuccess'))
                    if exportSuccess == 0:
                        # если соц. статус не был выгружен успешно, то удалить признак экспорта только если удаляем соц. статус
                        notFoundCSSPlanExportToDelete.add(planExportId)
                    else:
                        # если соц. статус был выгружен успешно, то удалить признак экспорта в любом случае
                        planExportToDelete.add(planExportId)

            questionDialog = CImportDispExportedPlanSyncDialog(self)
            questionDialog.monthName = monthName
            questionDialog.year = year
            questionDialog.totalCount = self.modelExportedPlan.rowCount()
            questionDialog.deleteCSSCount = len(cssToDelete)
            questionDialog.insertCSSCount = len(cssToInsert)
            questionDialog.updatePlanExportCount = len(planExportToInsert) + len(planExportToUpdate)
            questionDialog.deletePlanExportCount = len(planExportToDelete)
            questionDialog.deleteNotFoundCSSCount = len(notFoundCSSToDelete)
            dialogResult = questionDialog.show()

            if dialogResult == QtGui.QDialog.Rejected:
                db.rollback()
                return
            if questionDialog.deleteNotFoundCSS:
                planExportToDelete.update(notFoundCSSPlanExportToDelete)
                cssToDelete.update(notFoundCSSToDelete)

            self.pbDeleteProgress.setVisible(True)
            self.pbDeleteProgress.setValue(0)
            # при вставке ClientSocStatus добавляется и disp_PlanExport, поэтому *2
            totalCount = len(cssToDelete) + len(cssToInsert) * 2 + len(planExportToInsert) + len(planExportToUpdate) + len(planExportToDelete)
            self.pbDeleteProgress.setMaximum(totalCount)
            QtGui.qApp.processEvents()
            now = QtCore.QDateTime.currentDateTime()
            profilacClassId = forceRef(db.translate('rbSocStatusClass', 'code', 'profilac', 'id'))
            kindToTypeId = {}
            kindToTypeId[1] = forceRef(db.translate('rbSocStatusType', 'code', 'disp', 'id'))
            kindToTypeId[2] = forceRef(db.translate('rbSocStatusType', 'code', 'prof', 'id'))
            kindToTypeId[3] = forceRef(db.translate('rbSocStatusType', 'code', 'disp_2', 'id'))
            kindToTypeId[4] = forceRef(db.translate('rbSocStatusType', 'code', 'disp_1', 'id'))
            kindToTypeId[5] = forceRef(db.translate('rbSocStatusType', 'code', 'disp_cov1', 'id'))
            kindToTypeId[6] = forceRef(db.translate('rbSocStatusType', 'code', 'disp_cov2', 'id'))
            tableCSS = db.table('ClientSocStatus')
            tablePlanExport = db.table('disp_PlanExport')
            tablePlanExportErrors = db.table('disp_PlanExportErrors')
            for planExportId in planExportToDelete:
                db.deleteRecord(tablePlanExportErrors, tablePlanExportErrors['planExport_id'].eq(planExportId))
                db.deleteRecord(tablePlanExport, tablePlanExport['id'].eq(planExportId))
                self.pbDeleteProgress.setValue(self.pbDeleteProgress.value() + 1)
                QtGui.qApp.processEvents()
            for cssId in cssToDelete:
                db.markRecordsDeleted(tableCSS, tableCSS['id'].eq(cssId))
                self.pbDeleteProgress.setValue(self.pbDeleteProgress.value() + 1)
                QtGui.qApp.processEvents()
            for cssInfo in cssToInsert:
                clientId = cssInfo['clientId']
                kind = cssInfo['kind']
                month = cssInfo['month']
                begDate = QDate(year, month, 1)
                endDate = QDate(year, month, begDate.daysInMonth())
                cssRecord = tableCSS.newRecord()
                cssRecord.setValue('client_id', toVariant(clientId))
                cssRecord.setValue('socStatusClass_id', toVariant(profilacClassId))
                cssRecord.setValue('socStatusType_id', toVariant(kindToTypeId[kind]))
                cssRecord.setValue('begDate', toVariant(begDate))
                cssRecord.setValue('endDate', toVariant(endDate))
                cssId = db.insertRecord(tableCSS, cssRecord)
                self.pbDeleteProgress.setValue(self.pbDeleteProgress.value() + 1)
                QtGui.qApp.processEvents()
                planExportToInsert.append({'cssId': cssId, 'clientId': clientId, 'month': month})
            for planExportInfo in planExportToInsert:
                cssId = planExportInfo['cssId']
                clientId = planExportInfo['clientId']
                db.deleteRecord(tablePlanExport, [
                    tablePlanExport['row_id'].eq(cssId),
                ])
                planExportRecord = tablePlanExport.newRecord()
                planExportRecord.setValue('exportKind', toVariant('ClientSocStatus'))
                planExportRecord.setValue('row_id', toVariant(cssId))
                planExportRecord.setValue('client_id', toVariant(clientId))
                planExportRecord.setValue('year', toVariant(year))
                planExportRecord.setValue('month', toVariant(month))
                planExportRecord.setValue('exportDate', toVariant(now))
                planExportRecord.setValue('exportSuccess', toVariant(1))
                db.insertRecord(tablePlanExport, planExportRecord)
                self.pbDeleteProgress.setValue(self.pbDeleteProgress.value() + 1)
                QtGui.qApp.processEvents()
            for planExportInfo in planExportToUpdate:
                planExportId = planExportInfo['planExportId']
                planExportRecord = db.getRecord(tablePlanExport, '*', planExportId)
                planExportRecord.setValue('exportSuccess', toVariant(1))
                db.updateRecord(tablePlanExport, planExportRecord)
                self.pbDeleteProgress.setValue(self.pbDeleteProgress.value() + 1)
                QtGui.qApp.processEvents()
            db.commit()
            self.update()
        except Exception as e:
            db.rollback()
            QtGui.QMessageBox.critical(self, u'Произошла ошибка', exceptionToUnicode(e), QtGui.QMessageBox.Close)
        finally:
            self.pbDeleteProgress.setVisible(False)
            self.enableControls()

    def setSort(self, newColumn):
        column, asc = self.modelExportedPlan.order
        newOrderField = self.modelExportedPlan.orderByColumn[newColumn]
        if newOrderField is None:
            self.tblExportedPlan.horizontalHeader().setSortIndicator(column, Qt.AscendingOrder if asc else Qt.DescendingOrder)
            return
        if column == newColumn:
            newAsc = not asc
        else:
            newAsc = True
        self.modelExportedPlan.order = (newColumn, newAsc)
        self.update()

    def currentClientId(self):
        expPlanId = self.tblExportedPlan.currentItemId()
        if expPlanId:
            infoRecord = self.modelExportedPlan.expPlanInfoById[expPlanId]
            return infoRecord.value('client_id')
        else:
            return None
        
    @pyqtSignature('')
    def on_btnRefresh_clicked(self):
        self.refresh()
        
    @pyqtSignature('')
    def on_btnClose_clicked(self):
        self.reject()
        
    @pyqtSignature('int')
    def on_sbYear_valueChanged(self, value):
        self.update()
        
    @pyqtSignature('int')
    def on_cmbMonth_currentIndexChanged(self, index):
        self.update()
        
    @pyqtSignature('int')
    def on_cmbKind_currentIndexChanged(self, index):
        self.update()

    @pyqtSignature('QString')
    def on_edit_fio_textChanged(self, text):  # При вводе в текстовое поле сразу же формирует список по фамильно
        year = self.sbYear.value()
        month = self.cmbMonth.currentIndex() + 1
        kind = self.cmbKind.currentIndex()
        self.modelExportedPlan.update(year, month, kind, forceString(text))

    @pyqtSignature('')
    def on_btnSelectNotFound_clicked(self):
        self.modelExportedPlan.selectNotFound()

    @pyqtSignature('')
    def on_btnSelectAll_clicked(self):
        self.modelExportedPlan.selectAll()

    @pyqtSignature('')
    def on_btnDeleteSelected_clicked(self):
        self.deleteSelected()

    @pyqtSignature('')
    def on_btnSyncMIS_clicked(self):
        self.syncMIS()

    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelExportedPlan_currentRowChanged(self, current, previous):
        expPlanId = self.tblExportedPlan.currentItemId()
        clientId = self.currentClientId()
        self.modelExportedPlanErrors.update(expPlanId)
        self.actEditClient.setEnabled(clientId is not None)

    @pyqtSignature('')
    def on_actEditClient_triggered(self):
        clientId = self.currentClientId()
        if clientId is not None and QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]):
            dialog = None
            QtGui.qApp.setWaitCursor()
            try:
                try:
                    dialog = CClientEditDialog(self)
                    dialog.load(clientId)
                finally:
                    QtGui.qApp.restoreOverrideCursor()
                if dialog.exec_():
                    self.update()
            finally:
                if dialog:
                    dialog.deleteLater()

class CExportedPlanModel(CTableModel):
    __pyqtSignals__ = ('deleteSelectionChanged(int)')

    class CDeleteCol(CBoolCol):
        def __init__(self, title, fields, defaultWidth, deleteIdSet):
            CBoolCol.__init__(self, title, fields, defaultWidth)
            self.deleteIdSet = deleteIdSet

        def checked(self, values):
            value = forceRef(values[0])
            if value in self.deleteIdSet:
                return CBoolCol.valChecked
            else:
                return CBoolCol.valUnchecked

    class CFoundCol(CTextCol):
        def __init__(self, title, fields, defaultWidth, expPlanInfoById):
            CTextCol.__init__(self, title, fields, defaultWidth)
            self.expPlanInfoById = expPlanInfoById

        def format(self, values):
            expPlanId = forceRef(values[0])
            if expPlanId not in self.expPlanInfoById:
                return QVariant()
            record = self.expPlanInfoById[expPlanId]
            cssId = forceRef(record.value('clientSocStatus_id'))
            clientId = forceRef(record.value('clientId'))
            if cssId:
                return QVariant(u'Найден')
            elif clientId:
                return QVariant(u'Нет соответствия')
            else:
                return QVariant(u'Не найден')
            

    class CKindCol(CTextCol):
        def format(self, values):
            kind = forceInt(values[0])
            category = forceInt(values[1])
            if kind == 1 and category == 102:
                return QVariant(u'Дисп. раз в 2 г')
            elif kind == 1 and category in [101, 111, 112, 113, 114]:
                return QVariant(u'Дисп. ежегодная')
            elif kind == 1 and category == 121:
                return QVariant(u'Дисп. углубленная (1 гр)')
            elif kind == 1 and category == 122:
                return QVariant(u'Дисп. углубленная (2 гр)')
            elif kind == 1:
                return QVariant(u'Дисп. раз в 3 г')
            elif kind == 2:
                return QVariant(u'Проф. осмотр')
            else:
                return QVariant(u'Неизвестно (%d, %d)' % (kind, category))
    
    class CInfoDictCol(CTextCol):
        def __init__(self, title, defaultWidth, infoDict, dictKey):
            CTextCol.__init__(self, title, ['id'], defaultWidth, 'l')
            self.infoDict = infoDict
            self.dictKey = dictKey

        def format(self, values):
            clientId = forceRef(values[0])
            record = self.infoDict.get(clientId)
            if record:
                return toVariant(forceString(record.value(self.dictKey)))
            else:
                return CCol.invalid

    def __init__(self, parent):
        self.deleteIdSet = set()
        self.expPlanInfoById = {}
        self.notFoundIdSet = set()
        self.foundCount = 0
        self.invalidCssCount = 0
        self.clientNotFoundCount = 0
        self.orderByColumn = [
            'ExpPlan.a15_pfio',
            'ExpPlan.a16_pnm',
            'ExpPlan.a17_pln',
            'ExpPlan.a19_pbd',
            '''(case when ExpPlan.kind = 1 and ExpPlan.category in (101, 111, 112, 113, 114) then 4
                when ExpPlan.kind = 1 and ExpPlan.category = 102 then 3
                when ExpPlan.kind = 1 and ExpPlan.category = 121 then 5
                when ExpPlan.kind = 1 and ExpPlan.category = 122 then 6
            else ExpPlan.kind end)''',
            '(case when Client.id is null then 0 when CSS.id is null then 1 else 2 end)',
            'EventStage1.execDate',
            'EventStage2.execDate',
            'EventProf.execDate',
            None,
        ]
        self.order = (0, True)
        CTableModel.__init__(self, parent, [
            CTextCol(u'Фамилия', ['a15_pfio'], 20),
            CTextCol(u'Имя', ['a16_pnm'], 20),
            CTextCol(u'Отчество', ['a17_pln'], 20),
            CDateCol(u'Дата рождения', ['a19_pbd'], 20),
            CExportedPlanModel.CKindCol(u'Вид мероприятия', ['kind', 'category'], 20),
            CExportedPlanModel.CFoundCol(u'Статус в ЛПУ', ['id'], 20, self.expPlanInfoById),
            CExportedPlanModel.CInfoDictCol(u'Дата 1 этапа', 15, self.expPlanInfoById, 'lastStage1'),
            CExportedPlanModel.CInfoDictCol(u'Дата 2 этапа', 15, self.expPlanInfoById, 'lastStage2'),
            CExportedPlanModel.CInfoDictCol(u'Дата профосмотра', 15, self.expPlanInfoById, 'lastProf'),
            CExportedPlanModel.CDeleteCol(u'Удалить', ['id'], 20, self.deleteIdSet),
            ], 'disp_ExportedPlan')

    def update(self, year, month, kind, name):
        db = QtGui.qApp.db
        startOfThisYear = QDate(year, 1, 1)
        startOfNextYear = QDate(year + 1, 1, 1)
        stage1EventProfileIds = db.getIdList('rbEventProfile', where="regionalCode in ('8008', '8014', '8017', '8018')")
        stage2EventProfileIds = db.getIdList('rbEventProfile', where="regionalCode in ('8009', '8015', '8019')")
        profEventProfileIds = db.getIdList('rbEventProfile', where="regionalCode = '8011'")
        stage1EventTypeIds = db.getIdList('EventType', where="eventProfile_id in (%s)" % ', '.join([str(id) for id in stage1EventProfileIds]))
        stage2EventTypeIds = db.getIdList('EventType', where="eventProfile_id in (%s)" % ', '.join([str(id) for id in stage2EventProfileIds]))
        profEventTypeIds = db.getIdList('EventType', where="eventProfile_id in (%s)" % ', '.join([str(id) for id in profEventProfileIds]))
        kindFilter = ""
        nameFilter = ""
        if kind == 1:
            kindFilter = "and ExpPlan.kind = 1 and ExpPlan.category not in (101, 102, 111, 112, 113, 114, 121, 122)"
        elif kind == 2:
            kindFilter = "and ExpPlan.kind = 1 and ExpPlan.category = 102"
        elif kind == 3:
            kindFilter = "and ExpPlan.kind = 2"
        elif kind == 4:
            kindFilter = "and ExpPlan.kind = 1 and ExpPlan.category in (101, 111, 112, 113, 114)"
        elif kind == 5:
            kindFilter = "and ExpPlan.kind = 1 and ExpPlan.category = 121"
        elif kind == 6:
            kindFilter = "and ExpPlan.kind = 1 and ExpPlan.category = 122"
        if len(name) > 0:
            clientNames = name.split(u' ', 2)
            if len(clientNames) == 3:
                nameFilter = u''' AND Client.lastName like '{0}%' AND Client.firstName like '{1}%' AND Client.patrName like '{2}%' '''.format(
                    clientNames[0],
                    clientNames[1],
                    clientNames[2].strip())
            elif len(clientNames) == 2:
                nameFilter = u''' AND Client.lastName like '{0}%' AND Client.firstName like '{1}%' '''.format(clientNames[0], clientNames[1])
            else:
                nameFilter = u''' AND Client.lastName like '{0}%' '''.format(clientNames[0])
        stmt = u"""
            select ExpPlan.id,
                Client.id as client_id,
                cast(EventStage1.execDate as date) as lastStage1,
                cast(EventStage2.execDate as date) as lastStage2,
                cast(EventProf.execDate as date) as lastProf,
                CSS.id as clientSocStatus_id
            from disp_ExportedPlan as ExpPlan
                left join Client on Client.id = (
                    select max(C.id)
                    from Client as C
                    where C.lastName = ExpPlan.a15_pfio
                        and C.firstName = ExpPlan.a16_pnm
                        and coalesce(C.patrName, '') = coalesce(ExpPlan.a17_pln, '')
                        and C.birthDate = ExpPlan.a19_pbd
                        and C.deleted = 0
                )
                left join disp_PlanExport as PlanExport on PlanExport.id = (
                    select max(PlanExport.id)
                    from disp_PlanExport as PlanExport
                        left join ClientSocStatus as CSS on CSS.id = PlanExport.row_id
                        left join rbSocStatusType as SST on SST.id = CSS.socStatusType_id
                    where PlanExport.exportKind = 'ClientSocStatus'
                        and PlanExport.client_id = Client.id
                        and PlanExport.year = ExpPlan.year
                        and PlanExport.month = ExpPlan.mnth
                        and PlanExport.exportSuccess = 1
                        and SST.code = (
                            case when ExpPlan.kind = 1 and ExpPlan.category in (101, 111, 112, 113, 114) then 'disp_1'
                                 when ExpPlan.kind = 1 and ExpPlan.category = 102 then 'disp_2'
                                 when ExpPlan.kind = 1 and ExpPlan.category = 121 then 'disp_cov1'
                                 when ExpPlan.kind = 1 and ExpPlan.category = 122 then 'disp_cov2'
                                 when ExpPlan.kind = 1 then 'disp'
                                 when ExpPlan.kind = 2 then 'prof'
                                 end)
                        and CSS.deleted = 0
                )
                left join Event as EventStage1 on EventStage1.id = (
                    select e.id
                    from Event as e
                    where e.client_id = Client.id
                        and e.deleted = 0
                        and e.execDate >= '%(startOfThisYear)s'
                        and e.execDate < '%(startOfNextYear)s'
                        and e.eventType_id in (%(stage1EventTypeIds)s)
                    order by e.execDate desc
                    limit 1
                )
                left join Event as EventStage2 on EventStage2.id = (
                    select e.id
                    from Event as e
                    where e.client_id = Client.id
                        and e.deleted = 0
                        and e.execDate >= '%(startOfThisYear)s'
                        and e.execDate < '%(startOfNextYear)s'
                        and e.eventType_id in (%(stage2EventTypeIds)s)
                    order by e.execDate desc
                    limit 1
                )
                left join Event as EventProf on EventProf.id = (
                    select e.id
                    from Event as e
                    where e.client_id = Client.id
                        and e.deleted = 0
                        and e.execDate >= '%(startOfThisYear)s'
                        and e.execDate < '%(startOfNextYear)s'
                        and e.eventType_id in (%(profEventTypeIds)s)
                    order by e.execDate desc
                    limit 1
                )
                left join ClientSocStatus as CSS on CSS.id = PlanExport.row_id
            where ExpPlan.year = %(year)d
                and ExpPlan.mnth = %(month)d
                and ExpPlan.kind in (1, 2)
                %(kindFilter)s
                %(nameFilter)s
        """ % {
            "startOfThisYear": startOfThisYear.toString('yyyy-MM-dd'),
            "startOfNextYear": startOfNextYear.toString('yyyy-MM-dd'),
            "year": year,
            "month": month,
            "stage1EventTypeIds": ', '.join([str(id) for id in stage1EventTypeIds]) or 'null',
            "stage2EventTypeIds": ', '.join([str(id) for id in stage2EventTypeIds]) or 'null',
            "profEventTypeIds": ', '.join([str(id) for id in profEventTypeIds]) or 'null',
            "kindFilter": kindFilter,
            "nameFilter": nameFilter,
        }
        orderColumnIndex, isAscending = self.order
        orderBy = self.orderByColumn[orderColumnIndex]
        orderBy += (' asc' if isAscending else ' desc')
        stmt += (' order by ' + orderBy)
        query = db.query(stmt)
        idList = []
        self.deleteIdSet.clear()
        self.expPlanInfoById.clear()
        self.notFoundIdSet.clear()
        self.foundCount = 0
        self.invalidCssCount = 0
        self.clientNotFoundCount = 0
        while query.next():
            record = query.record()
            id = forceRef(record.value('id'))
            clientId = forceRef(record.value('client_id'))
            cssId = forceRef(record.value('clientSocStatus_id'))
            if cssId:
                self.foundCount += 1
            elif clientId:
                self.invalidCssCount += 1
            else:
                self.clientNotFoundCount += 1
            idList.append(id)
            self.expPlanInfoById[id] = record
            if cssId is None:
                self.notFoundIdSet.add(id)
        self.emit(SIGNAL('deleteSelectionChanged(int)'), 0)
        self.setIdList(idList)

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.CheckStateRole:
            row = index.row()
            id = self._idList[row]
            if id in self.deleteIdSet:
                self.deleteIdSet.remove(id)
            else:
                self.deleteIdSet.add(id)
            self.emit(SIGNAL('deleteSelectionChanged(int)'), len(self.deleteIdSet))
            self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
            return True
        return False
    
    def selectNotFound(self):
        self.deleteIdSet.clear()
        self.deleteIdSet.update(self.notFoundIdSet)
        self.emitDataChanged()
        self.emit(SIGNAL('deleteSelectionChanged(int)'), len(self.deleteIdSet))
    
    def selectAll(self):
        self.deleteIdSet.clear()
        self.deleteIdSet.update(self.idList())
        self.emitDataChanged()
        self.emit(SIGNAL('deleteSelectionChanged(int)'), len(self.deleteIdSet))

    def flags(self, index=None):
        result = CTableModel.flags(self, index)
        if index and index.column() == 9:
            result |= Qt.ItemIsUserCheckable
        return result
    
    def data(self, index, role):
        if role == Qt.ToolTipRole and index.isValid():
            if index.column() == 5:
                row = index.row()
                record = self.getRecordByRow(row)
                id = forceRef(record.value('id'))
                if id in self.notFoundIdSet:
                    return QVariant(u'По набору данных: Фамилия, Имя, Отчество, Пол, Дата рождения, Год, месяц и Тип профилактического мероприятия не выявлено совпадений в МИС')
        return CTableModel.data(self, index, role)


class CExportedPlanErrorsModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent, [
            CIntCol(u'Код ошибки', ['errorType_id'], 20),
            CDesignationCol(u'Текст ошибки', ['errorType_id'], ('disp_ErrorTypes', 'name'), 20)
            ], 'disp_ExportedPlanErrors')

    def update(self, expPlanId):
        if expPlanId is None:
            idList = []
        else:
            db = QtGui.qApp.db
            table = db.table('disp_ExportedPlanErrors')
            where = [table['expPlan_id'].eq(expPlanId)]
            idList = db.getIdList(table, where=where)
        self.setIdList(idList)

class CImportDispExportedPlanSyncDialog(QtGui.QDialog, Ui_ImportDispExportedPlanSyncDialog):
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)

    def show(self):
        self.lblMonthYearTotalCount.setText(u'Импортировано из ТФОМС за %s %d г.: %d' % (self.monthName, self.year, self.totalCount))
        self.lblDeleteCSS.setText(u'Удалить планирование: %d' % self.deleteCSSCount)
        self.lblInsertCSS.setText(u'Добавить планирование: %d' % self.insertCSSCount)
        self.lblUpdatePlanExport.setText(u'Обновить признак экспорта: %d' % self.updatePlanExportCount)
        self.lblDeletePlanExport.setText(u'Удалить признак экспорта: %d' % self.deletePlanExportCount)
        self.chkDeleteNotFoundCSS.setText(u'Удалить соц. статусы из карт, не найденных на сервисе: %d' % self.deleteNotFoundCSSCount)
        self.chkDeleteNotFoundCSS.setEnabled(self.deleteNotFoundCSSCount > 0)
        return self.exec_()
    
    @pyqtSignature('')
    def on_buttonBox_accepted(self):
        self.deleteNotFoundCSS = (self.chkDeleteNotFoundCSS.checkState() == Qt.Checked)
        self.accept()
    
    @pyqtSignature('')
    def on_buttonBox_rejected(self):
        self.reject()