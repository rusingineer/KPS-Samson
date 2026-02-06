# -*- coding: utf-8 -*-

from PyQt4 import QtGui
from PyQt4.QtCore import QDate, QObject, SIGNAL, Qt, pyqtSignature, QVariant
from PyQt4.QtGui import QAbstractItemView, QWidget, QAction

from library.Calendar import monthName
from library.DialogBase import CConstructHelperMixin
from library.TableModel import CTableModel, CCol, CDesignationCol, CIntCol, CTextCol, CEnumCol
from library.Utils import forceInt, forceStringEx, forceString, forceRef, formatRecordsCount, toVariant

from Exchange.ExportDispPlanDiagnosisDialog import CExportDispPlanDiagnosisDialog
from Exchange.ImportDispExportedPlanDiagnosisDialog import CImportDispExportedPlanDiagnosisDialog

from Orgs.Utils import getOrgStructureDescendants

from Registry.ClientEditDialog import CClientEditDialog

from Reports.ReportBase import CReportBase, createTable
from Reports.ReportView import CReportViewDialog, CPageFormat

from Users.Rights import urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry

from Ui_DispExchangeDiagnosisPage import Ui_DispExchangeDiagnosisPage


class CDispExchangeDiagnosisPage(QWidget, Ui_DispExchangeDiagnosisPage, CConstructHelperMixin):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.addModels('DiagnosisDispansPlaned', CDiagnosisDispansPlanedModel(self))
        self.addModels('PlanExportErrors', CPlanExportErrorsModel(self))
        self.addObject('actEditClient', QAction(u'Открыть регистрационную карточку', self))
        self.addObject('actEditExport', QAction(u'Изменить признак экспорта', self))
        self.addObject('actEditPlan', QAction(u'Перепланировать', self))
        self.setupUi(self)
        self.actEditClient.setEnabled(QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]))
        self.setModels(self.tblDiagnosisDispansPlaned, self.modelDiagnosisDispansPlaned, self.selectionModelDiagnosisDispansPlaned)
        self.setModels(self.tblPlanExportErrors, self.modelPlanExportErrors, self.selectionModelPlanExportErrors)
        currentDate = QDate.currentDate()
        self.orderFieldByColumn = [
            'Client.lastName',
            'Client.firstName',
            'Client.patrName',
            'Client.birthDate',
            'Client.sex',
            'AttachOrgStructure.name',
            'Diagnosis.MKB',
            'DDP.year',
            'DDP.month',
            'Person.code',
            'DDP.isExport'
        ]
        self.order = (0, True)
        self.sbYear.setValue(currentDate.year())
        self.updateDDPList()
        self.updateDDPDetails()
        header = self.tblDiagnosisDispansPlaned.horizontalHeader()
        header.setSortIndicatorShown(True)
        header.setSortIndicator(0, Qt.AscendingOrder)
        QObject.connect(header, SIGNAL('sectionClicked(int)'), self.setDDPSort)
        self.tblDiagnosisDispansPlaned.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.cmbSocStatusesType.setTable('rbSocStatusType', True)
        self.on_chkSocStatuses_toggled(self.chkSocStatuses.isChecked())
        self.cmbExportedWithErrors.setVisible(False)
        self.cmbExportedWithErrors.setTable(u'disp_ErrorTypes', ['id', 'name'])

    def contextMenuEvent(self, event):
        self.menu = QtGui.QMenu(self)
        selectedRows = self.getSelectedRows(self.tblDiagnosisDispansPlaned)
        if len(selectedRows) == 1:
            self.menu.addAction(self.actEditClient)
            self.menu.addAction(self.actEditExport)
        self.menu.addAction(self.actEditPlan)
        self.menu.popup(QtGui.QCursor.pos())

    def getSelectedRows(self, tbl):
        return [index.row() for index in tbl.selectionModel().selectedRows()]

    def updateDDPList(self):
        try:
            db = QtGui.qApp.db
            QtGui.QApplication.setOverrideCursor(QtGui.QCursor(Qt.WaitCursor))
            tableClient = db.table('Client')
            year = self.sbYear.value()
            month = self.cmbMonth.currentIndex()

            attachTypeIds = db.getIdList('rbAttachType', where="code in ('1', '2')")

            sql = u"""
            select DDP.id,
                Client.id as client_id,
                Client.lastName,
                Client.firstName,
                Client.patrName,
                Client.birthDate,
                (case Client.sex when 1 then 'М' when 2 then 'Ж' end) as sex,
                AttachOrgStructure.name as attachName,
                ifnull(SocAttachOrgStructure.id, 0) != ifnull(AttachOrgStructure.id, 0) as bold,
                Diagnosis.MKB,
                concat(Person.code, ' | ', formatPersonName(Person.id), ', ', rbSpeciality.name) as personName,
                PlanExport.id as planExport_id
            from DiagnosisDispansPlaned as DDP
                left join Client on Client.id = DDP.client_id
                left join ClientAttach as Attach on Attach.id = (
                    select max(Attach.id)
                    from ClientAttach as Attach
                    left join OrgStructure o on o.id = Attach.orgStructure_id
                    where Attach.client_id = Client.id
                        and Attach.deleted = 0
                        and Attach.endDate is null
                        and o.areaType > 0
                        and Attach.attachType_id in (%(attachTypeIds)s)
                )
                LEFT JOIN (
                    SELECT soc_attachments.client_id,  OrgStructure.id orgStructure_id 
                    FROM soc_attachments
                    INNER JOIN OrgStructure ON OrgStructure.id = 
                            (SELECT id FROM OrgStructure org WHERE org.deleted=0 
                            AND getOMSCode(org.id)=soc_attachments.attach_mo 
                            AND org.infisInternalCode=soc_attachments.attach_area  AND org.areaType > 0 limit 1)
                    WHERE soc_attachments.serviceMethod = 0
                ) SocAttach ON Client.id = SocAttach.client_id
                LEFT JOIN ClientWork ON ClientWork.client_id = Client.id AND ClientWork.id = (
                    SELECT
                    MAX(CW.id)
                    FROM ClientWork AS CW
                    WHERE CW.client_id = Client.id
                    AND CW.deleted = 0)
                left join Diagnosis on Diagnosis.id = DDP.diagnosis_id
                left join Person on Person.id = DDP.person_id
                left join rbSpeciality on rbSpeciality.id = Person.speciality_id
                left join disp_PlanExport as PlanExport on PlanExport.exportKind = 'DiagnosisDispansPlaned' and PlanExport.row_id = DDP.id
                left join disp_PlanExportErrors as PlanExportErrors on PlanExportErrors.planExport_id = PlanExport.id
                left join OrgStructure as AttachOrgStructure on AttachOrgStructure.id = Attach.orgStructure_id
                left join OrgStructure as SocAttachOrgStructure on SocAttachOrgStructure.id = SocAttach.orgStructure_id
            """ % {
                "attachTypeIds": ', '.join([str(id) for id in attachTypeIds]),
            }
            where = [
                "DDP.year = %d" % year,
                'DDP.deleted = 0',
                'Client.deleted = 0'
            ]
            if month > 0:
                where.append("DDP.month = %d" % month)
            if self.chkFilterLastName.isChecked():
                lastName = forceStringEx(self.edtFilterLastName.text())
                if lastName:
                    where.append("Client.lastName like '%s%%'" % lastName)
            if self.chkFilterFirstName.isChecked():
                firstName = forceStringEx(self.edtFilterFirstName.text())
                if firstName:
                    where.append("Client.firstName like '%s%%'" % firstName)
            if self.chkFilterPatrName.isChecked():
                patrName = forceStringEx(self.edtFilterPatrName.text())
                if patrName:
                    where.append("Client.patrName like '%s%%'" % patrName)
            if self.chkFilterBirthDay.isChecked():
                birthDate = self.edtFilterBirthDay.date()
                if not birthDate:
                    birthDate = None
                if self.chkFilterEndBirthDay.isChecked():
                    endBirthDate = self.edtFilterEndBirthDay.date()
                    if not endBirthDate:
                        endBirthDate = None
                    where.append(tableClient['birthDate'].dateGe(birthDate))
                    where.append(tableClient['birthDate'].dateLe(endBirthDate))
                else:
                    where.append(tableClient['birthDate'].eq(birthDate))
            if self.chkFilterAddressOrgStructure.isChecked():
                orgStructureId = self.cmbFilterAddressOrgStructure.value()
                if orgStructureId:
                    orgStructureIdList = getOrgStructureDescendants(orgStructureId)
                    tableClientAttach = db.table('ClientAttach').alias('Attach')
                    where.append(tableClientAttach['orgStructure_id'].inlist(orgStructureIdList))
            if self.chkFilterSex.isChecked():
                sex = self.cmbFilterSex.currentIndex()
                if sex:
                    where.append(tableClient['sex'].eq(sex))
            if self.cmbBusyness.currentIndex() == 1:
                where.append(u"IF((ClientWork.org_id is not null or IFNULL(ClientWork.freeInput, '') <> '') and IFNULL(ClientWork.post, '') <> '', 1, 0) = 1")
            elif self.cmbBusyness.currentIndex() == 2:
                where.append(u"IF((ClientWork.org_id is not null or IFNULL(ClientWork.freeInput, '') <> '') and IFNULL(ClientWork.post, '') <> '', 1, 0) = 0")

            if self.chkSocStatuses.isChecked():
                socStatusesNotExist = self.chkSocStatusesCondition.isChecked()
                socStatusesBegDate = self.edtFilterSocStatusesBegDate.date()
                socStatusesEndDate = self.edtFilterSocStatusesEndDate.date()
                socStatusesClass = self.cmbSocStatusesClass.value()
                socStatusesType = self.cmbSocStatusesType.value()
                socStatusWhere = [
                    "CSS.client_id = Client.id",
                    "CSS.deleted = 0",
                ]
                if socStatusesClass:
                    socStatusClassIdList = db.getDescendants('rbSocStatusClass', 'group_id', socStatusesClass)
                    if socStatusClassIdList:
                        stmtStatusTypeId = u'''SELECT DISTINCT rbSocStatusClassTypeAssoc.type_id
                            FROM  rbSocStatusClassTypeAssoc
                            WHERE rbSocStatusClassTypeAssoc.class_id IN (%s)
                        ''' % (
                            u','.join(str(socStatusClassId) for socStatusClassId in socStatusClassIdList)
                        )
                        queryStatusTypeId = db.query(stmtStatusTypeId)
                        resultStatusTypeIdList = []
                        while queryStatusTypeId.next():
                            resultStatusTypeIdList.append(forceRef(queryStatusTypeId.value(0)))
                    if resultStatusTypeIdList:
                        socStatusWhere.append(u"CSS.socStatusType_id IN (%s)" % u','.join(str(id) for id in resultStatusTypeIdList))
                    else:
                        parentSocStatusClassIdList = db.getTheseAndParents('rbSocStatusClass', 'group_id', [socStatusesClass])
                        socStatusWhere.append(u"CSS.socStatusClass_id IN (%s)" % u','.join(str(id) for id in parentSocStatusClassIdList))
                        socStatusWhere.append(u"CSS.socStatusType_id is null")
                if socStatusesType:
                    socStatusWhere.append(u"CSS.socStatusType_id = %s" % socStatusesType)
                if socStatusesBegDate:
                    socStatusWhere.append(u"(CSS.endDate is null or DATE(CSS.endDate) >= DATE(%s))" % db.formatDate(socStatusesBegDate))
                if socStatusesEndDate:
                    socStatusWhere.append(u"(CSS.begDate is null or DATE(CSS.begDate) <= DATE(%s))" % db.formatDate(socStatusesEndDate))
                socStatusStmt = u"select id from ClientSocStatus as CSS where " + " and ".join(socStatusWhere)
                if socStatusesNotExist:
                    where.append(u"not exists (%s)" % socStatusStmt)
                else:
                    where.append(u"exists (%s)" % socStatusStmt)
            if self.chkFilterPerson.isChecked():
                personId = self.cmbFilterPerson.value()
                if personId:
                    where.append('DDP.person_id = %d' % personId)
            if self.chkFilterMKB.isChecked():
                mkbFrom = forceString(self.edtFilterMKBFrom.text())
                mkbTo = forceString(self.edtFilterMKBTo.text())
                if mkbFrom:
                    where.append("Diagnosis.MKB >= '%s'" % mkbFrom)
                if mkbTo:
                    where.append("Diagnosis.MKB <= '%s'" % mkbTo)
            if self.chkFilterIsExport.isChecked():
                where.append('DDP.isExport = 0')
            statusFilter = []
            if self.chkNotExported.isChecked():
                statusFilter.append('PlanExport.id is null')
            if self.chkExportedSuccessfully.isChecked():
                statusFilter.append('PlanExport.exportSuccess = 1')
            if self.chkHideSuccess.isChecked():
                statusFilter.append('ifnull(PlanExport.exportSuccess, 0) != 1')
            if self.chkExportedWithErrors.isChecked():
                statusFilter.append('PlanExport.exportSuccess = 0')
                errorTypes = self.cmbExportedWithErrors.value()
                if errorTypes:
                    where.append('PlanExportErrors.errorType_id in ({})'.format(errorTypes))
            if len(statusFilter) > 0 and len(statusFilter) < 3:
                where.append('(' + ' or '.join(statusFilter) + ')')
            sql += (' where ' + ' and '.join(where))

            order = self.getOrderField()
            sql += (' order by ' + order)

            idList = []
            infoDict = self.modelDiagnosisDispansPlaned.infoDict
            infoDict.clear()
            query = db.query(sql)
            ddpIdList = []
            clientsList = []
            while query.next():
                record = query.record()
                clientId = forceRef(record.value('id'))
                idList.append(clientId)
                infoDict[clientId] = record
                ddpIdList.append(forceRef(record.value('id')))
                clientsList.append(forceRef(record.value('client_id')))
            self.modelDiagnosisDispansPlaned.setIdList(idList)
            
            tablePlanExport = db.table('disp_PlanExport')
            planExportFilter = [
                tablePlanExport['exportKind'].eq('DiagnosisDispansPlaned'),
                tablePlanExport['row_id'].inlist(idList),
            ]
            exportedIdSet = set(db.getDistinctIdList(tablePlanExport, idCol='row_id', where=planExportFilter))
            self.modelDiagnosisDispansPlaned.setExportedIdSet(exportedIdSet)
            
            count = len(idList)
            people = u", {0} человек".format(len(list(set(clientsList)))) if idList else u""
            self.lblRowCount.setText(formatRecordsCount(count) + people)
        finally:
            QtGui.QApplication.restoreOverrideCursor()

    def updateDDPDetails(self):
        ddp_id = self.tblDiagnosisDispansPlaned.currentItemId()
        ddpInfo = self.modelDiagnosisDispansPlaned.infoDict.get(ddp_id)
        planExport_id = forceRef(ddpInfo.value('planExport_id')) if ddpInfo else None
        self.modelPlanExportErrors.update(planExport_id)
        self.tabWidget.setTabText(0, u'Ошибки (%d)' % self.modelPlanExportErrors.rowCount())

    def getOrderField(self):
        column, asc = self.order
        direction = ' asc' if asc else ' desc'
        field = self.orderFieldByColumn[column] + direction
        return field
    
    def setDDPSort(self, newColumn):
        newOrderField = self.orderFieldByColumn[newColumn]
        if newOrderField is None:
            return
        column, asc = self.order
        if column == newColumn:
            newAsc = not asc
        else:
            newAsc = True
        self.order = (newColumn, newAsc)
        self.updateDDPList()

    def showReport(self):
        def showReportInt():
            report = CDispExchangeReport(self, self.modelDiagnosisDispansPlaned)
            description = self.reportDescription()
            reportTxt = report.build(description)
            view = CReportViewDialog(self)
            view.setWindowTitle(report.title())
            view.setText(reportTxt)
            if report.pageFormat:
                view.setPageFormat(report.pageFormat)
            return view
        view = QtGui.qApp.callWithWaitCursor(self, showReportInt)
        view.exec_()
    
    def reportDescription(self):
        year = self.sbYear.value()
        month = self.cmbMonth.currentIndex()
        lines = []
        lines.append(u'Год: %d' % year)
        if month > 0:
            monthText = self.cmbMonth.currentText()
            lines.append(u'Месяц: %s' % monthText)
        if self.chkFilterLastName.isChecked():
            lastName = forceStringEx(self.edtFilterLastName.text())
            lines.append(u'Фамилия: %s' % lastName)
        if self.chkFilterFirstName.isChecked():
            firstName = forceStringEx(self.edtFilterFirstName.text())
            lines.append(u'Имя: %s' % firstName)
        if self.chkFilterPatrName.isChecked():
            patrName = forceStringEx(self.edtFilterPatrName.text())
            lines.append(u'Отчество: %s' % patrName)
        statusLines = []
        if self.chkNotExported.isChecked():
            statusLines.append(u'- запланированные, не отправленные')
        if self.chkFilterIsExport.isChecked():
            statusLines.append(u'- не подлежащие экспорту')
        if self.chkExportedSuccessfully.isChecked():
            statusLines.append(u'- отправленные успешно')
        if self.chkExportedWithErrors.isChecked():
            statusLines.append(u'- отправленные с ошибками')
        if len(statusLines) > 0 and len(statusLines) < 3:
            lines.append(u'Статус:')
            lines += statusLines
        return '\n'.join(lines)

    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelDiagnosisDispansPlaned_currentRowChanged(self, current, previous):
        self.updateDDPDetails()

    @pyqtSignature('')
    def on_btnApplyFilter_clicked(self):
        self.updateDDPList()

    @pyqtSignature('')
    def on_btnResetFilter_clicked(self):
        self.cmbMonth.setCurrentIndex(0)
        self.chkFilterLastName.setChecked(False)
        self.chkFilterFirstName.setChecked(False)
        self.chkFilterPatrName.setChecked(False)
        self.chkFilterBirthDay.setChecked(False)
        self.chkFilterEndBirthDay.setChecked(False)
        self.chkFilterAddressOrgStructure.setChecked(False)
        self.chkFilterSex.setChecked(False)
        self.chkFilterPerson.setChecked(False)
        self.chkFilterMKB.setChecked(False)
        self.cmbBusyness.setCurrentIndex(0)
        self.chkNotExported.setChecked(True)
        self.chkFilterIsExport.setChecked(False)
        self.chkExportedSuccessfully.setChecked(False)
        self.chkExportedWithErrors.setChecked(False)
        self.updateDDPList()

    @pyqtSignature('int')
    def on_cmbSocStatusesClass_currentIndexChanged(self, index):
        socStatusClassId = self.cmbSocStatusesClass.value()
        if socStatusClassId:
            filter = (u'''rbSocStatusType.id IN (SELECT DISTINCT rbSocStatusClassTypeAssoc.type_id
            FROM  rbSocStatusClassTypeAssoc
            WHERE rbSocStatusClassTypeAssoc.class_id = %s)'''%(socStatusClassId))
        else:
            filter = u''
        self.cmbSocStatusesType.setFilter(filter)

    @pyqtSignature('int')
    def on_chkFilterLastName_stateChanged(self, state):
        self.edtFilterLastName.setEnabled(state == Qt.Checked)
        if self.chkFilterLastName.isChecked():
            self.edtFilterLastName.setFocus()

    @pyqtSignature('int')
    def on_chkFilterFirstName_stateChanged(self, state):
        self.edtFilterFirstName.setEnabled(state == Qt.Checked)
        if self.chkFilterFirstName.isChecked():
            self.edtFilterFirstName.setFocus()

    @pyqtSignature('int')
    def on_chkFilterPatrName_stateChanged(self, state):
        self.edtFilterPatrName.setEnabled(state == Qt.Checked)
        if self.chkFilterPatrName.isChecked():
            self.edtFilterPatrName.setFocus()

    @pyqtSignature('bool')
    def on_chkFilterBirthDay_toggled(self, checked):
        if checked:
            self.edtFilterBirthDay.setEnabled(checked)
            self.chkFilterEndBirthDay.setEnabled(checked)
            self.edtFilterEndBirthDay.setEnabled(self.chkFilterEndBirthDay.isChecked())
            self.edtFilterBirthDay.setFocus()
        else:
            self.edtFilterBirthDay.setEnabled(False)
            self.chkFilterEndBirthDay.setEnabled(False)
            self.edtFilterEndBirthDay.setEnabled(False)

    @pyqtSignature('bool')
    def on_chkFilterAddressOrgStructure_toggled(self, checked):
        self.cmbFilterAddressOrgStructure.setEnabled(checked)

    @pyqtSignature('bool')
    def on_chkFilterEndBirthDay_toggled(self, checked):
        self.edtFilterEndBirthDay.setEnabled(checked)
        if self.chkFilterEndBirthDay.isChecked():
            self.edtFilterEndBirthDay.setFocus()

    @pyqtSignature('bool')
    def on_chkFilterSex_toggled(self, checked):
        self.cmbFilterSex.setEnabled(checked)

    @pyqtSignature('bool')
    def on_chkFilterPerson_toggled(self, checked):
        self.cmbFilterPerson.setEnabled(checked)

    @pyqtSignature('bool')
    def on_chkFilterMKB_toggled(self, checked):
        self.edtFilterMKBFrom.setEnabled(checked)
        self.edtFilterMKBTo.setEnabled(checked)

    @pyqtSignature('bool')
    def on_chkSocStatuses_toggled(self, checked):
        self.chkSocStatusesCondition.setEnabled(checked)

        self.lblFilterSocStatusesBegDate.setEnabled(checked)
        self.edtFilterSocStatusesBegDate.setEnabled(checked)
        self.lblFilterSocStatusesEndDate.setEnabled(checked)
        self.edtFilterSocStatusesEndDate.setEnabled(checked)

        self.cmbSocStatusesClass.setEnabled(checked)
        self.cmbSocStatusesType.setEnabled(checked)

    @pyqtSignature('')
    def on_btnPutEvPlanList_clicked(self):
        CExportDispPlanDiagnosisDialog(self).exec_()

    @pyqtSignature('')
    def on_btnExportedPlan_clicked(self):
        CImportDispExportedPlanDiagnosisDialog(self).exec_()

    @pyqtSignature('')
    def on_actEditClient_triggered(self):
        ddpId = self.tblDiagnosisDispansPlaned.currentItemId()
        infoRecord = self.modelDiagnosisDispansPlaned.infoDict.get(ddpId)
        clientId = forceRef(infoRecord.value('client_id')) if infoRecord else None
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
    
    
    @pyqtSignature('')
    def on_actEditExport_triggered(self):
        item = self.tblDiagnosisDispansPlaned.currentItem()
        dialog = QtGui.QDialog()
        dialog.setWindowTitle(u"Изменение признака экспорта")
        layout = QtGui.QVBoxLayout(dialog)

        dialog.rdIsNotExport = QtGui.QRadioButton(u"Не подлежит")
        dialog.rdNotExported = QtGui.QRadioButton(u"Не отправлен")
        layout.addWidget(dialog.rdIsNotExport)
        layout.addWidget(dialog.rdNotExported)
        dialog.buttonGroup = QtGui.QButtonGroup(dialog)
        dialog.buttonGroup.addButton(dialog.rdIsNotExport)
        dialog.buttonGroup.addButton(dialog.rdNotExported)

        dialog.buttonBox = QtGui.QDialogButtonBox(dialog)
        dialog.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        dialog.connect(dialog.buttonBox, SIGNAL('accepted()'), dialog.accept)
        dialog.connect(dialog.buttonBox, SIGNAL('rejected()'), dialog.reject)
        layout.addWidget(dialog.buttonBox)
        dialog.rdIsNotExport.setChecked(True)
        if dialog.exec_():
            db = QtGui.qApp.db
            result = int(dialog.rdNotExported.isChecked())
            if result:
                db.deleteRecord(u'disp_PlanExport', [u'disp_PlanExport.exportKind = "DiagnosisDispansPlaned"',
                                                     u'disp_PlanExport.exportSuccess = 0',
                                                     u'disp_PlanExport.row_id = {}'.format(forceString(item.value('id')))])
            item.setValue('isExport', result)
            item.setValue('modifyDatetime', toVariant(QDate.currentDate()))
            item.setValue('modifyPerson_id', QtGui.qApp.userId)
            db.updateRecord(u'DiagnosisDispansPlaned', item)
            db.commit()
            self.updateDDPList()   
    
    
    @pyqtSignature('')
    def on_actEditPlan_triggered(self):
        records = []
        itemIdList = self.tblDiagnosisDispansPlaned.selectedItemIdList()
        for id in itemIdList:
            records.append(self.tblDiagnosisDispansPlaned.model().recordCache().get(id))
        dialog = QtGui.QDialog()
        dialog.setWindowTitle(u"Перепланировать")
        layout = QtGui.QVBoxLayout(dialog)
        
        ylayout = QtGui.QHBoxLayout()
        lblYear = QtGui.QLabel(u"Год ", dialog)
        dialog.cmbYear = QtGui.QSpinBox(dialog)
        dialog.cmbYear.setMinimum(2017)
        dialog.cmbYear.setMaximum(9999)
        ylayout.addWidget(lblYear)
        ylayout.addWidget(dialog.cmbYear)
        layout.addLayout(ylayout)
        
        monthNames = (
        u'январь', u'февраль', u'март', u'апрель', u'май', u'июнь', u'июль', u'август', u'сентябрь', u'октябрь',
        u'ноябрь', u'декабрь')
        lblMonth = QtGui.QLabel(u"Месяц ", dialog)
        dialog.cmbMonth = QtGui.QComboBox(dialog)
        dialog.cmbMonth.addItems(monthNames)
        mlayout = QtGui.QHBoxLayout()
        mlayout.addWidget(lblMonth)
        mlayout.addWidget(dialog.cmbMonth)
        layout.addLayout(mlayout)

        dialog.buttonBox = QtGui.QDialogButtonBox(dialog)
        dialog.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        dialog.connect(dialog.buttonBox, SIGNAL('accepted()'), dialog.accept)
        dialog.connect(dialog.buttonBox, SIGNAL('rejected()'), dialog.reject)
        layout.addWidget(dialog.buttonBox)
        dialog.cmbYear.setValue(QDate.currentDate().year())
        dialog.cmbMonth.setCurrentIndex(QDate.currentDate().month() - 1)
        
        if dialog.exec_():
            db = QtGui.qApp.db
            year = dialog.cmbYear.value()
            month = dialog.cmbMonth.currentIndex()+1
            tablePlanExport = db.table('disp_PlanExport')
            planExportFilter = [
                tablePlanExport['exportKind'].eq('DiagnosisDispansPlaned'),
                tablePlanExport['row_id'].inlist(itemIdList),
                tablePlanExport['exportSuccess'].eq(1),
            ]
            exportedIdSet = set(db.getDistinctIdList(tablePlanExport, idCol='row_id', where=planExportFilter))
            for item in records:
                if forceInt(item.value('id')) not in exportedIdSet:
                    item.setValue('year', year)
                    item.setValue('month', month)
                    item.setValue('modifyDatetime', toVariant(QDate.currentDate()))
                    item.setValue('modifyPerson_id', QtGui.qApp.userId)
                    db.updateRecord(u'DiagnosisDispansPlaned', item)
            db.commit()
            self.updateDDPList() 
            

    @pyqtSignature('')
    def on_btnShowReport_clicked(self):
        self.showReport()


class CDiagnosisDispansPlanedModel(CTableModel):
    class CEnableEditCol(CTextCol):
        def __init__(self, title, fields, width, exportedIdSet):
            CTextCol.__init__(self, title, fields, width, 'l')
            self.exportedIdSet = exportedIdSet

        def setExportedIdSet(self, idList):
            self.exportedIdSet = idList
        
        def format(self, values):
            val = forceRef(values[0])
            record = values[1]
            if not val:
                return QVariant(u'Не подлежит')
            elif forceRef(record.value('id')) not in self.exportedIdSet:
                return QVariant(u'Не отправлен')
            else:
                return QVariant(u'Отправлен')
            
    class CInfoCol(CTextCol):
        def __init__(self, title, infoField, infoDict, defaultWidth, alignment='l'):
            CTextCol.__init__(self, title, ['id'], defaultWidth, alignment)
            self.infoDict = infoDict
            self.infoField = infoField

        def format(self, values):
            id = forceRef(values[0])
            record = self.infoDict.get(id)
            if record:
                return QVariant(forceString(record.value(self.infoField)))
            else:
                return CCol.invalid

    def __init__(self, parent):
        self.infoDict = {}
        CTableModel.__init__(self, parent)
        self.parent = parent
        self.addColumn(self.CInfoCol(u'Фамилия', 'lastName', self.infoDict, 15))
        self.addColumn(self.CInfoCol(u'Имя', 'firstName', self.infoDict, 15))
        self.addColumn(self.CInfoCol(u'Отчество', 'patrName', self.infoDict, 15))
        self.addColumn(self.CInfoCol(u'Дата рожд.', 'birthDate', self.infoDict, 15))
        self.addColumn(self.CInfoCol(u'Пол', 'sex', self.infoDict, 15, alignment='c'))
        self.addColumn(self.CInfoCol(u'Участок', 'attachName', self.infoDict, 15))
        self.addColumn(self.CInfoCol(u'Код МКБ', 'MKB', self.infoDict, 15))
        self.addColumn(CIntCol(u'Год', ['year'], 15))
        self.addColumn(CEnumCol(u'Месяц', ['month'], monthName, 15))
        self.addColumn(self.CInfoCol(u'Врач', 'personName', self.infoDict, 15))
        self.exportedIdSet = []
        self.enableEditCol = self.CEnableEditCol(u'Экспорт в ТФОМС', ['isExport'], 10, self.exportedIdSet)
        self.addColumn(self.enableEditCol)
        self.setTable('DiagnosisDispansPlaned')

        self._boldFont = QtGui.QFont()
        self._boldFont.setWeight(QtGui.QFont.Bold)

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid():
            if role == Qt.FontRole:
                clientId = self._idList[index.row()]
                if forceInt(self.infoDict.get(clientId).value('bold')):
                    return toVariant(self._boldFont)
        return CTableModel.data(self, index, role)
    
    def setExportedIdSet(self, idList):
        self.exportedIdSet = idList
        self.enableEditCol.setExportedIdSet(idList)
    
    def getExportedIdSet(self):
        return self.exportedIdSet


class CPlanExportErrorsModel(CTableModel):
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
            where = [
                table['planExport_id'].eq(planExport_id)
                ]
            idList = db.getIdList(table, idCol=table['id'], where=where)
        self.setIdList(idList)


class CDispExchangeReport(CReportBase):
    def __init__(self, parent, model):
        CReportBase.__init__(self, parent)
        self.model = model
        self.setTitle(u'Диспансерные осмотры')
        self.pageFormat = CPageFormat(pageSize=CPageFormat.A4, orientation=CPageFormat.Landscape, leftMargin=1, topMargin=1, rightMargin=1,  bottomMargin=1)
        
    def build(self, description):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertText(description)
        cursor.insertBlock()

        tableColumns = [
            ('15%', [u'Фамилия'       ], CReportBase.AlignLeft),
            ('15%', [u'Имя'           ], CReportBase.AlignLeft),
            ('15%', [u'Отчество'      ], CReportBase.AlignLeft),
            ('10%', [u'Дата рождения' ], CReportBase.AlignLeft),
            ('5%',  [u'Пол'           ], CReportBase.AlignLeft),
            ('10%', [u'Участок'       ], CReportBase.AlignLeft),
            ('10%', [u'Код МКБ'       ], CReportBase.AlignLeft),
            ('5%',  [u'Год'           ], CReportBase.AlignLeft),
            ('5%',  [u'Месяц'         ], CReportBase.AlignLeft),
            ('10%', [u'Врач'          ], CReportBase.AlignLeft),
            ('5%',  [u'Экспорт в ТФОМС'], CReportBase.AlignLeft)
        ]
        table = createTable(cursor, tableColumns)
        n = 0
        rowCount = self.model.rowCount()
        columnCount = self.model.columnCount()
        for row in xrange(0, rowCount):
            tableRow = table.addRow()
            for column in xrange(0, columnCount):
                (modelColumn, values) = self.model.getRecordValues(column, row)
                text = forceString(modelColumn.format(values))
                table.setText(tableRow, column, text)
        return doc
