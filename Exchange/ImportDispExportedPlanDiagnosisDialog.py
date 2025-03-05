# -*- coding: utf-8 -*-

from PyQt4 import QtCore, QtGui, QtSql
from PyQt4.QtCore import *

import Exchange.AttachService as AttachService
from Reports.ReportView import CReportViewDialog

from library.DialogBase import CDialogBase
from library.TableModel import CTableModel, CTextCol, CDateCol, CEnumCol, CBoolCol, CIntCol, CDesignationCol
from library.Utils import *

from Registry.ClientEditDialog import CClientEditDialog

from Users.Rights import urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry

from Ui_ImportDispExportedPlanDiagnosisDialog import Ui_ImportDispExportedPlanDiagnosisDialog

class CImportDispExportedPlanDiagnosisDialog(CDialogBase, Ui_ImportDispExportedPlanDiagnosisDialog):
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
        self.update()

    def getReportHeader(self):
        return self.objectName()

    def getFilterAsText(self):
        return u''

    def contentToHTML(self):
        #reportHeader = self.getReportHeader()
        self.tblExportedPlan.setReportHeader(u"Список граждан из ТФОМС, запланированных на диспансерные осмотры")
        reportDescription = self.getFilterAsText()
        self.tblExportedPlan.setReportDescription(reportDescription)
        return self.tblExportedPlan.contentToHTML()

    @pyqtSignature('')
    def on_btnPrint_clicked(self):
        html = self.contentToHTML()
        view = CReportViewDialog(self)
        view.setText(html)
        view.exec_()

    def disableControls(self, disabled = True):
        self.sbYear.setDisabled(disabled)
        self.cmbMonth.setDisabled(disabled)
        self.btnRefresh.setDisabled(disabled)
        self.btnClose.setDisabled(disabled)
        self.btnSelectNotFound.setDisabled(disabled)
        self.btnSelectAll.setDisabled(disabled)
        self.btnDeleteSelected.setDisabled(disabled or len(self.modelExportedPlan.deleteIdSet) == 0)
        QtGui.qApp.processEvents()

    def enableControls(self):
        self.disableControls(False)
    
    def update(self):
        year = self.sbYear.value()
        month = self.cmbMonth.currentIndex() + 1
        self.disableControls()
        try:
            self.modelExportedPlan.update(year, month)
            self.updateCountLabel()
        finally:
            self.enableControls()
    
    def updateCountLabel(self):
        totalCount = self.modelExportedPlan.rowCount()
        self.lblExpPlanCount.setText(u"На сервисе %d записей" % totalCount)

    def refresh(self):
        year = self.sbYear.value()
        month = self.cmbMonth.currentIndex() + 1
        self.disableControls()
        try:
            response = AttachService.updateExportedPlan(year, month)
            self.modelExportedPlan.update(year, month)
            self.updateCountLabel()
        except Exception as e:
            QtGui.QMessageBox.critical(self, u'Произошла ошибка', exceptionToUnicode(e), QtGui.QMessageBox.Close)
        finally:
            self.enableControls()
    
    def deleteSelectionChanged(self, count):
        self.btnDeleteSelected.setText(u'Удалить выбранные (%d)' % count)
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
            return self.modelExportedPlan.expPlanInfoById[expPlanId]['clientId']
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

    @pyqtSignature('')
    def on_btnSelectNotFound_clicked(self):
        self.modelExportedPlan.selectNotFound()

    @pyqtSignature('')
    def on_btnDeleteSelected_clicked(self):
        self.deleteSelected()
    
    @pyqtSignature('')
    def on_btnSelectAll_clicked(self):
        self.modelExportedPlan.selectAll()

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

    class CPersonCol(CTextCol):
        def __init__(self, title, fields, defaultWidth, expPlanInfoById):
            CTextCol.__init__(self, title, fields, defaultWidth)
            self.expPlanInfoById = expPlanInfoById

        def format(self, values):
            expPlanId = forceRef(values[0])
            if expPlanId not in self.expPlanInfoById:
                return QVariant()
            info = self.expPlanInfoById[expPlanId]
            personName = info['personName']
            return QVariant(personName)

    class CFoundCol(CTextCol):
        def __init__(self, title, fields, defaultWidth, expPlanInfoById):
            CTextCol.__init__(self, title, fields, defaultWidth)
            self.expPlanInfoById = expPlanInfoById

        def format(self, values):
            expPlanId = forceRef(values[0])
            if expPlanId not in self.expPlanInfoById:
                return QVariant()
            info = self.expPlanInfoById[expPlanId]
            id = info['ddpId']
            clientId = info['clientId']
            if id:
                return QVariant(u'Найден')
            elif clientId:
                return QVariant(u'Нет соответствия')
            else:
                return QVariant(u'Не найден')

    def __init__(self, parent):
        self.deleteIdSet = set()
        self.expPlanInfoById = {}
        self.notFoundIdSet = set()
        self.orderByColumn = [
            'ExpPlan.a15_pfio',
            'ExpPlan.a16_pnm',
            'ExpPlan.a17_pln',
            'ExpPlan.a19_pbd',
            'ExpPlan.mkbx',
            '(case when Person.id is null then ExpPlan.doc_ss else concat_ws(' ', Person.lastName, Person.firstName, Person.patrName) end)',
            None,
        ]
        self.order = (0, True)
        CTableModel.__init__(self, parent, [
            CTextCol(u'Фамилия', ['a15_pfio'], 20),
            CTextCol(u'Имя', ['a16_pnm'], 20),
            CTextCol(u'Отчество', ['a17_pln'], 20),
            CDateCol(u'Дата рождения', ['a19_pbd'], 20),
            CTextCol(u'Код МКБ', ['mkbx'], 20),
            self.CPersonCol(u'Врач', ['id'], 20, self.expPlanInfoById),
            CExportedPlanModel.CFoundCol(u'Статус в ЛПУ', ['id'], 20, self.expPlanInfoById),
            self.CDeleteCol(u'Удалить', ['id'], 20, self.deleteIdSet),
            ], 'disp_ExportedPlan')

    def update(self, year, month):
        db = QtGui.qApp.db
        stmt = u"""
            select ExpPlan.id,
                Client.id as client_id,
                (case when Person.id is null
                    then coalesce(formatSNILS(ExpPlan.doc_ss), ExpPlan.doc_ss)
                    else concat_ws(' ', Person.lastName, Person.firstName, Person.patrName)
                end) as personName,
                ddp.id as ddp_id
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
                left join disp_PlanExport pe on pe.client_id = Client.id and ExpPlan.rid = pe.row_id AND pe.exportKind = 'DiagnosisDispansPlaned'
                left JOIN DiagnosisDispansPlaned ddp on ddp.id = pe.row_id and ddp.deleted = 0
                left join Person on Person.id = (
                    select max(P.id)
                    from Person as P
                    where P.SNILS = replace(replace(ExpPlan.doc_ss, '-', ''), ' ', '')
                        and P.deleted = 0
                )
            where ExpPlan.year = %d and ExpPlan.mnth = %d and ExpPlan.kind = 3
            """ % (year, month)
        orderColumnIndex, isAscending = self.order
        orderBy = self.orderByColumn[orderColumnIndex]
        orderBy += (' asc' if isAscending else ' desc')
        stmt += (' order by ' + orderBy)
        query = db.query(stmt)
        idList = []
        self.deleteIdSet.clear()
        self.expPlanInfoById.clear()
        self.notFoundIdSet.clear()
        while query.next():
            record = query.record()
            id = forceRef(record.value('id'))
            idList.append(id)
            clientId = forceRef(record.value('client_id'))
            personName = forceString(record.value('personName'))
            ddpId = forceRef(record.value('ddp_id'))
            self.expPlanInfoById[id] = {'clientId': clientId, 'personName': personName, 'ddpId': ddpId}
            if ddpId is None:
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
        if index and index.column() == 7:
            result |= Qt.ItemIsUserCheckable
        return result


    def data(self, index, role):
        if role == Qt.ToolTipRole and index.isValid():
            if index.column() == 6:
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
