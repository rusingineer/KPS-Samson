# -*- coding: utf-8 -*-

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDate, QObject, SIGNAL, QTimer, pyqtSignature, QVariant
from PyQt4.QtGui import QAction

from library.Calendar import monthName
from library.DialogBase import CDialogBase
from library.TableModel import CTableModel, CCol, CTextCol, CIntCol, CDesignationCol
from library.Utils import exceptionToUnicode, forceRef, forceString, forceInt, forceBool, forceDate, toVariant

import Exchange.AttachService as AttachService

from Registry.ClientEditDialog import CClientEditDialog

from Users.Rights import urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry

from Ui_ExportDispPlanDiagnosisDialog import Ui_ExportDispPlanDiagnosisDialog


class CExportDispPlanDiagnosisDialog(CDialogBase, Ui_ExportDispPlanDiagnosisDialog):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.initialized = False
        self.addModels('DispPlan', CDispPlanModel(self))
        self.addModels('DispPlanErrors', CDispPlanErrorsModel(self))
        self.addObject('actEditClient', QAction(u'Открыть регистрационную карточку', self))
        self.addObject('actDeletePlanExport', QAction(u'Удалить признак экспорта', self))
        self.setupUi(self)
        self.modelDispPlan.setHideSuccess(parent.chkHideSuccess.isChecked())
        self.setWindowFlags(Qt.Window)
        self.actEditClient.setEnabled(QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]))
        self.tblDispPlan.createPopupMenu([self.actEditClient, self.actDeletePlanExport])
        self.pbExportProgress.setVisible(False)
        self.lblExportStatus.setVisible(False)
        currentDate = QDate.currentDate()
        self.sbYear.setValue(currentDate.year())
        self.cmbMonthFrom.setCurrentIndex(currentDate.month() - 1)
        self.setModels(self.tblDispPlan, self.modelDispPlan, self.selectionModelDispPlan)
        self.setModels(self.tblDispPlanErrors, self.modelDispPlanErrors, self.selectionModelDispPlanErrors)
        self.tblDispPlanErrors.setEnabled(False)
        header = self.tblDispPlan.horizontalHeader()
        header.setSortIndicatorShown(True)
        header.setSortIndicator(0, Qt.AscendingOrder)
        QObject.connect(header, SIGNAL('sectionClicked(int)'), self.setSort)
        self.exportableIdList = []
        self.initialized = True

    def showEvent(self, event):
        QTimer.singleShot(0, self.updateList)
        
    def disableControls(self, disabled=True):
        self.sbYear.setDisabled(disabled)
        self.cmbMonthFrom.setDisabled(disabled)
        self.cmbMonthTo.setDisabled(disabled)
        self.tblDispPlan.setDisabled(disabled)
        self.btnExport.setDisabled(disabled)
        self.btnClose.setDisabled(disabled)

    def enableControls(self):
        self.disableControls(False)
        
    def updateList(self):
        self.disableControls()
        labelText = u'Обновление списка...'
        try:
            self.lblPlanCount.setText(labelText)
            year = self.sbYear.value()
            monthFrom = self.cmbMonthFrom.currentIndex() + 1
            monthTo = self.cmbMonthTo.currentIndex() + 1
            QtGui.qApp.processEvents()
            self.modelDispPlan.update(year, monthFrom, monthTo)
            itemCount = self.modelDispPlan.rowCount()
            monthFromText = unicode(self.cmbMonthFrom.currentText())
            monthToText = unicode(self.cmbMonthTo.currentText())
            if monthFrom == monthTo:
                monthText = u'на %s' % monthToText
            else:
                monthText = u'с %s по %s' % (monthFromText, monthToText)
            self.exportableIdList = self.modelDispPlan.notExportedIdList + self.modelDispPlan.errorsIdList
            exportableCount = len(self.exportableIdList)
            errorCount = len(self.modelDispPlan.errorsIdList)
            labelText = u'Запланировано %s %d г.: %d, подлежат экспорту: %d, из них %d с ошибками' % (monthText, year, itemCount, exportableCount, errorCount)
            self.btnExport.setEnabled(len(self.exportableIdList) > 0)
        except Exception as e:
            labelText = unicode(e)
        finally:
            self.enableControls()
            self.lblPlanCount.setText(labelText)
    
    def export(self):
        successCount = 0
        errorCount = 0
        notAcceptedCount = 0
        totalCount = len(self.exportableIdList)
        self.pbExportProgress.setVisible(True)
        self.pbExportProgress.setValue(0)
        self.pbExportProgress.setMaximum(totalCount)
        self.lblExportStatus.setVisible(True)
        self.lblExportStatus.setText(u'Отправка пакетов...')
        packageSize = 1000
        self.disableControls()
        try:
            while self.exportableIdList:
                ids = self.exportableIdList[0:packageSize]
                self.exportableIdList = self.exportableIdList[packageSize:]
                QtGui.qApp.processEvents()
                result = AttachService.putEvPlanList('DiagnosisDispansPlaned', ids,
                                                     useSocAttachments=int(self.chkUseSocAttachments.isChecked()))
                successCount = successCount + result['successCount']
                errorCount = errorCount + result['errorCount']
                acceptedCount = successCount + errorCount
                notAcceptedCount = totalCount - acceptedCount
                self.pbExportProgress.setValue(self.pbExportProgress.value() + len(ids))
            labelText = (u'Экспорт завершен: отправлено %d записей' % totalCount)
            if totalCount > 0:
                labelParts = []
                if successCount > 0:
                    labelParts.append(u'%d успешно' % successCount)
                if errorCount > 0:
                    labelParts.append(u'%d с ошибками' % errorCount)
                if notAcceptedCount > 0:
                    labelParts.append(u'%d не принято' % notAcceptedCount)
                labelText += (u', из них ' + u', '.join(labelParts))
            self.lblExportStatus.setText(labelText)                
        except Exception as e:
            self.lblExportStatus.setText(u'Ошибка: ' + exceptionToUnicode(e))
        finally:
            self.updateList()
            self.pbExportProgress.setVisible(False)

    def setSort(self, newColumn):
        newOrderField = self.modelDispPlan.orderByColumn[newColumn]
        if newOrderField is None:
            return
        column, asc = self.modelDispPlan.order
        if column == newColumn:
            newAsc = not asc
        else:
            newAsc = True
        self.modelDispPlan.order = (newColumn, newAsc)
        self.updateList()
    
    def currentInfoRecord(self):
        ddpId = self.tblDispPlan.currentItemId()
        if ddpId is None:
            return None
        else:
            return self.modelDispPlan.infoDict[ddpId]

    @pyqtSignature('')
    def on_btnClose_clicked(self):
        self.reject()

    @pyqtSignature('int')
    def on_sbYear_valueChanged(self, index):
        if self.initialized:
            self.updateList()

    @pyqtSignature('int')
    def on_cmbMonthFrom_currentIndexChanged(self, index):
        if index > self.cmbMonthTo.currentIndex():
            self.cmbMonthTo.setCurrentIndex(index)
        elif self.initialized:
            self.updateList()

    @pyqtSignature('int')
    def on_cmbMonthTo_currentIndexChanged(self, index):
        if index < self.cmbMonthFrom.currentIndex():
            self.cmbMonthFrom.setCurrentIndex(index)
        elif self.initialized:
            self.updateList()

    @pyqtSignature('')
    def on_btnExport_clicked(self):
        self.export()

    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelDispPlan_currentRowChanged(self, current, previous):
        record = self.currentInfoRecord()
        planExportId = forceRef(record.value('planExport_id'))
        if planExportId is None:
            self.tblDispPlanErrors.setEnabled(False)
            self.actDeletePlanExport.setEnabled(False)
            self.modelDispPlanErrors.setIdList([])
        else:
            self.tblDispPlanErrors.setEnabled(True)
            self.actDeletePlanExport.setEnabled(True)
            self.modelDispPlanErrors.update(planExportId)

    @pyqtSignature('')
    def on_actEditClient_triggered(self):
        record = self.currentInfoRecord()
        clientId = forceRef(record.value('client_id'))
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
                    self.updateList()
            finally:
                if dialog:
                    dialog.deleteLater()

    @pyqtSignature('')
    def on_actDeletePlanExport_triggered(self):
        record = self.currentInfoRecord()
        planExportId = forceRef(record.value('planExport_id'))
        if planExportId is None:
            return
        deleted = False
        db = QtGui.qApp.db
        db.transaction()
        try:
            db.deleteRecord('disp_PlanExportErrors', 'planExport_id = %d' % planExportId)
            db.deleteRecord('disp_PlanExport', 'id = %d' % planExportId)
            db.commit()
            deleted = True
        except Exception as e:
            db.rollback()
            QtGui.QMessageBox.critical(self, u'Произошла ошибка', exceptionToUnicode(e), QtGui.QMessageBox.Close)
        if deleted:
            self.updateList()


class CDispPlanModel(CTableModel):
    class CInfoCol(CTextCol):
        def __init__(self, title, infoField, infoDict, defaultWidth, alignment='l'):
            CTextCol.__init__(self, title, ['id'], defaultWidth, 'l')
            self.infoDict = infoDict
            self.infoField = infoField

        def format(self, values):
            id = forceRef(values[0])
            record = self.infoDict.get(id)
            if record:
                return QVariant(forceString(record.value(self.infoField)))
            else:
                return CCol.invalid

    class CYearMonthCol(CCol):
        def __init__(self, title, fields, defaultWidth):
            CCol.__init__(self, title, fields, defaultWidth, 'l')

        def format(self, values):
            year = forceInt(values[0])
            month = forceInt(values[1])
            return QVariant(u"%s %d" % (monthName[month], year))

    class CExportStatusCol(CCol):
        def __init__(self, title, infoDict, defaultWidth):
            CCol.__init__(self, title, ['id'], defaultWidth, 'l')
            db = QtGui.qApp.db
            self.dict = infoDict

        def format(self, values):
            ddpId = forceRef(values[0])
            record = self.dict.get(ddpId)
            planExportId = forceRef(record.value('planExport_id'))
            if planExportId:
                success = forceBool(record.value('exportSuccess'))
                exportDate = forceDate(record.value('exportDate')).toString('dd.MM.yyyy')
                if success:
                    return QVariant(u'отправлен %s успешно' % exportDate)
                else:
                    return QVariant(u'отправлен %s с ошибками' % exportDate)
            else:
                return QVariant(u'не отправлен')

    def __init__(self, parent):
        self.infoDict = {}
        self.hideSuccess = False
        self.orderByColumn = [
            'Client.lastName',
            'Client.birthDate',
            'DDP.month',
            'PlanExport.exportSuccess',
            'AttachOrgStructure.name',
            'Diagnosis.MKB',
            'Person.code',
        ]
        self.order = (0, True)
        CTableModel.__init__(self, parent)
        self.addColumn(self.CInfoCol(u'Ф.И.О.', 'clientName', self.infoDict, 20))
        self.addColumn(self.CInfoCol(u'Дата рожд.', 'birthDate', self.infoDict, 20))
        self.addColumn(self.CYearMonthCol(u'Запланирован на месяц', ['year', 'month'], 20))
        self.addColumn(self.CExportStatusCol(u'Статус', self.infoDict, 20))
        self.addColumn(self.CInfoCol(u'Участок', 'attachName', self.infoDict, 15))
        self.addColumn(self.CInfoCol(u'Код МКБ', 'MKB', self.infoDict, 15))
        self.addColumn(self.CInfoCol(u'Врач', 'personName', self.infoDict, 15))
        self.setTable('DiagnosisDispansPlaned')

        self._boldFont = QtGui.QFont()
        self._boldFont.setWeight(QtGui.QFont.Bold)

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.FontRole:
                planId = self._idList[index.row()]
                if forceInt(self.infoDict.get(planId).value('bold')):
                    return toVariant(self._boldFont)
        return CTableModel.data(self, index, role)


    def setHideSuccess(self, state):
        self.hideSuccess = state

    def update(self, year, monthFrom, monthTo):
        db = QtGui.qApp.db

        exportSuccess = u"ifnull(PlanExport.exportSuccess, 0) != 1" if self.hideSuccess else u"1"

        sql = u"""
        select DDP.id,
            Client.id as client_id,
            concat_ws(' ', Client.lastName, Client.firstName, Client.patrName) as clientName,
            Client.birthDate,
            PlanExport.exportDate,
            PlanExport.exportSuccess,
            PlanExport.id as planExport_id,
            AttachOrgStructure.name as attachName,
            ifnull(SocAttachOrgStructure.id, 0) != ifnull(AttachOrgStructure.id, 0) as bold,
            Diagnosis.MKB,
            concat(Person.code, ' | ', formatPersonName(Person.id), ', ', rbSpeciality.name) as personName
        from DiagnosisDispansPlaned as DDP
            left join Client on Client.id = DDP.client_id
            left join ClientAttach as Attach on Attach.id = (
                select max(Attach.id)
                from ClientAttach as Attach
                    left join rbAttachType as AttachType on AttachType.id = Attach.attachType_id
                    left join OrgStructure o on o.id = Attach.orgStructure_id
                where Attach.client_id = Client.id
                    and Attach.deleted = 0
                    and AttachType.code in ('1', '2')
                    and Attach.endDate is null
                    and o.areaType > 0
            )
            LEFT JOIN (
                SELECT soc_attachments.client_id,  OrgStructure.id orgStructure_id 
                FROM soc_attachments
                INNER JOIN OrgStructure ON OrgStructure.id = 
                        (SELECT id FROM OrgStructure org WHERE org.deleted=0 
                        AND getOMSCode(org.id)=soc_attachments.attach_mo 
                        AND org.infisInternalCode=soc_attachments.attach_area AND org.areaType > 0 limit 1)
                WHERE soc_attachments.serviceMethod = 0
            ) SocAttach ON Client.id = SocAttach.client_id 
            left join Diagnosis on Diagnosis.id = DDP.diagnosis_id
            left join Person on Person.id = DDP.person_id
            left join rbSpeciality on rbSpeciality.id = Person.speciality_id
            left join disp_PlanExport as PlanExport on PlanExport.exportKind = 'DiagnosisDispansPlaned' and PlanExport.row_id = DDP.id
            left join OrgStructure as AttachOrgStructure on AttachOrgStructure.id = Attach.orgStructure_id
            left join OrgStructure as SocAttachOrgStructure on SocAttachOrgStructure.id = SocAttach.orgStructure_id
        where DDP.deleted = 0
            and Client.deleted = 0
            and DDP.year = %(year)d
            and DDP.month between %(monthFrom)d and %(monthTo)d
            and DDP.isExport = 1
            and %(exportSuccess)s
        """ % {
            "year": year,
            "monthFrom": monthFrom,
            "monthTo": monthTo,
            "exportSuccess": exportSuccess
        }
        orderColumnIndex, isAscending = self.order
        orderBy = self.orderByColumn[orderColumnIndex]
        orderBy += (' asc' if isAscending else ' desc')
        sql += (' order by ' + orderBy)
        
        idList = []
        self.infoDict.clear()
        notExportedIdList = []
        errorsIdList = []
        query = db.query(sql)
        while query.next():
            record = query.record()
            ddpId = record.value('id').toInt()[0]
            idList.append(ddpId)
            self.infoDict[ddpId] = record
            exportSuccess = record.value('exportSuccess')
            if exportSuccess.isNull():
                notExportedIdList.append(ddpId)
            elif forceInt(exportSuccess) == 0:
                errorsIdList.append(ddpId)
        self.setIdList(idList)
        self.year = year
        self.monthFrom = monthFrom
        self.monthTo = monthTo
        self.notExportedIdList = notExportedIdList
        self.errorsIdList = errorsIdList
    
    def getOrderField(self):
        return 'Client.lastName asc'


class CDispPlanErrorsModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent, [
            CIntCol(u'Код ошибки', ['errorType_id'], 20),
            CDesignationCol(u'Текст ошибки', ['errorType_id'], ('disp_ErrorTypes', 'name'), 20)
            ], 'disp_PlanExportErrors')

    def update(self, planExport_id):
        if planExport_id is None:
            idList = []
        else:
            db = QtGui.qApp.db
            table = db.table('disp_PlanExportErrors')
            where = [table['planExport_id'].eq(planExport_id)]
            idList = db.getIdList(table, where=where)
        self.setIdList(idList)
