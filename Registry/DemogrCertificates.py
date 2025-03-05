# -*- coding: utf-8 -*-

from PyQt4.QtCore import *

from library.DialogBase   import CConstructHelperMixin
from library.TableModel import CTableModel, CDateTimeFixedCol, CEnumCol, CNameCol, CTextCol, CBoolCol, CDateFixedCol
from library.Utils        import *

from Registry.ClientEditDialog import CClientEditDialog
from Registry.ClientSearchDialog import CExternalClientSearchDialog

from Reports.ReportBase import CReportBase, createTable
from Reports.ReportView     import CReportViewDialog, CPageFormat

from Users.Rights import urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry

from Ui_DemogrCertificates   import Ui_DemogrCertificatesDialog

class CDemogrCertificatesDialog(QtGui.QDialog, Ui_DemogrCertificatesDialog, CConstructHelperMixin):
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        self.addModels('Certificates', CCertificatesModel(self))
        self.addObject('actEditClient', QtGui.QAction(u'Открыть регистрационную карточку', self))
        self.setupUi(self)
        self.actEditClient.allowed = QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry])
        self.tblCertificates.createPopupMenu([self.actEditClient])
        self.tblCertificates.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.setModels(self.tblCertificates, self.modelCertificates, self.selectionModelCertificates)
        self.orderFieldByColumn = [
            'Certificate.surname',
            'Certificate.name',
            'Certificate.patronymic',
            'Certificate.gender',
            'Certificate.birthDate',
            'Certificate.deathDate',
            'Certificate.certDate',
            'Certificate.client_id',
            'Certificate.numberSector'
        ]
        self.order = (0, True)
        self.setDefaultFilterDates()
        self.updateCertificatesList()
        self.updateCertificateInfo()
        self.btnSyncSelected.setEnabled(False)
        if not self.actEditClient.allowed:
            self.actEditClient.setEnabled(False)
        else:
            self.updateEditClientAction()
        header = self.tblCertificates.horizontalHeader()
        header.setSortIndicatorShown(True)
        header.setSortIndicator(0, Qt.AscendingOrder)
        QObject.connect(header, SIGNAL('sectionClicked(int)'), self.setCertificateSort)
    
    def setDefaultFilterDates(self):
        dateFrom = QDate.currentDate()
        dateTo = QDate.currentDate()
        db = QtGui.qApp.db
        lastDeathDate = db.getMax(table='demogr_Certificate', maxCol='deathDate')
        if lastDeathDate is not None:
            lastDeathDate = forceDate(lastDeathDate)
            if lastDeathDate.isValid():
                dateFrom = lastDeathDate
                dateTo = lastDeathDate
        self.edtDeathDateFrom.setDate(dateFrom)
        self.edtDeathDateTo.setDate(dateTo)

    def updateCertificatesList(self):
        db = QtGui.qApp.db
        deathDateFrom = self.edtDeathDateFrom.date()
        deathDateTo = self.edtDeathDateTo.date().addDays(1)

        sql = u"""select Certificate.*
            from demogr_Certificate as Certificate
        """
        where = [
            "Certificate.deathDate >= '%s'" % deathDateFrom.toString('yyyy-MM-dd'),
            "Certificate.deathDate < '%s'" % deathDateTo.toString('yyyy-MM-dd'),
        ]
        if self.chkFilterSurname.isChecked():
            surname = forceStringEx(self.edtFilterSurname.text())
            if surname:
                where.append("Certificate.surname like '%s%%'" % surname)
        if self.chkFilterName.isChecked():
            name = forceStringEx(self.edtFilterName.text())
            if name:
                where.append("Certificate.name like '%s%%'" % name)
        if self.chkFilterPatronymic.isChecked():
            patronymic = forceStringEx(self.edtFilterPatronymic.text())
            if patronymic:
                where.append("Certificate.patronymic like '%s%%'" % patronymic)
        sql += (' where ' + ' and '.join(where))

        order = self.getOrderField()
        sql += (' order by ' + order)

        idList = []
        infoDict = self.modelCertificates.certificateInfoDict
        infoDict.clear()
        query = db.query(sql)
        while query.next():
            record = query.record()
            certificateId = forceRef(record.value('id'))
            idList.append(certificateId)
            infoDict[certificateId] = record
        self.modelCertificates.setIdList(idList)
        count = len(idList)
        self.lblCertificatesCount.setText(formatRecordsCount(count))
        
    def updateCertificateInfo(self):
        def joinNonEmpty(separator, strings):
            return separator.join([string for string in strings if string])
        def formatLine(lineName, lineText):
            if lineText:
                return '<b>%s</b>: %s' % (lineName, lineText)
            else:
                return None
        def formatFieldValue(name, value):
            if value:
                return '%s %s' % (name, value)
            else:
                return None
        def formatFieldValues(fields):
            formattedFieldValues = [formatFieldValue(name, value) for name, value in fields]
            return joinNonEmpty(', ', formattedFieldValues)
        selectedRecords = self.getSelectedRecords()
        self.txtCertificateInfo.clear()
        infoHtmls = []
        for record in selectedRecords:
            fullName = joinNonEmpty(' ', [
                forceString(record.value('surname')),
                forceString(record.value('name')),
                forceString(record.value('patronymic')),
            ])
            lines = [
                '<b>%s</b>' % fullName,
                formatLine(u'Полис', formatFieldValues([
                    (u'серия', forceString(record.value('seriesDoccofirm'))),
                    (u'номер', forceString(record.value('numberDoccofirm'))),
                ])),
                formatLine(u'Адрес', forceString(record.value('address'))),
                formatLine(u'Сертификат', formatFieldValues([
                    (u'серия', forceString(record.value('certSerial'))),
                    (u'номер', forceString(record.value('certNumber'))),
                    (u'дата выдачи', forceString(record.value('certDate'))),
                ])),
                formatLine(u'Участок', forceString(record.value('numberSector')))
            ]
            infoHtml = joinNonEmpty('<br>', lines)
            infoHtmls.append(infoHtml)
        joinedHtml = '<br><br>'.join(infoHtmls)
        self.txtCertificateInfo.setHtml(joinedHtml)

    def updateEditClientAction(self):
        if not self.actEditClient.allowed:
            return
        record = self.tblCertificates.currentItem()
        clientId = forceRef(record.value('client_id')) if record else None
        self.actEditClient.setEnabled(clientId is not None)

    def getOrderField(self):
        column, asc = self.order
        direction = ' asc' if asc else ' desc'
        field = self.orderFieldByColumn[column] + direction
        return field

    def setCertificateSort(self, newColumn):
        newOrderField = self.orderFieldByColumn[newColumn]
        if newOrderField is None:
            return
        column, asc = self.order
        if column == newColumn:
            newAsc = not asc
        else:
            newAsc = True
        self.order = (newColumn, newAsc)
        self.updateCertificatesList()
    
    def getSelectedRecords(self):
        itemIdList = self.modelCertificates.idList()
        infoDict = self.modelCertificates.certificateInfoDict
        selectedIds = [itemIdList[index.row()] for index in self.selectionModelCertificates.selectedRows()]
        return [infoDict[id] for id in selectedIds]
    
    def syncSelected(self):
        selectedRecords = self.getSelectedRecords()
        validRecords = [record for record in selectedRecords if not record.value('client_id').isNull()]
        db = QtGui.qApp.db
        for record in validRecords:
            clientId = forceRef(record.value('client_id'))
            deathDate = forceDateTime(record.value('deathDate'))
            if deathDate.isValid():
                db.query("update Client set deathDate = '%s' where id = %d" % (deathDate.toString('yyyy-MM-dd hh:mm:ss'), clientId))
                db.query("update ClientAttach set deAttachType_id = 2, endDate = '%s' where client_id = %d and endDate is null" % (deathDate.toString('yyyy-MM-dd'), clientId))
        count = len(validRecords)
        messageFormat = agreeNumberAndWord(count, (u'Синхронизирована %d запись', u'Синхронизировано %d записи', u'Синхронизировано %d записей'))
        message = messageFormat % count
        QtGui.QMessageBox.information(self, u'Снихронизация списка умерших', message, QtGui.QMessageBox.Close)
    
    def findClient(self):
        serviceRecord = self.tblCertificates.currentItem()
        if not serviceRecord:
            return
        dialog = CDemogrClientSearchDialog(self, serviceRecord)
        result = dialog.exec_()
        if result != QtGui.QDialog.Accepted:
            return
        clientId = dialog.clientId
        if clientId is None:
            return
        serviceRecord.setValue('client_id', clientId)
        db = QtGui.qApp.db
        db.updateRecord('demogr_Certificate', serviceRecord)
        self.updateCertificatesList()

    def showReport(self):
        def showReportInt():
            report = CDemogrCertificatesReport(self, self.modelCertificates)
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
        deathDateFrom = self.edtDeathDateFrom.date()
        deathDateTo = self.edtDeathDateTo.date()
        lines = []
        lines.append(u'Дата смерти: с %s по %s' % (deathDateFrom.toString('dd.MM.yyyy'), deathDateTo.toString('dd.MM.yyyy')))
        if self.chkFilterSurname.isChecked():
            surname = forceStringEx(self.edtFilterSurname.text())
            lines.append(u'Фамилия: %s' % surname)
        if self.chkFilterName.isChecked():
            name = forceStringEx(self.edtFilterName.text())
            lines.append(u'Имя: %s' % name)
        if self.chkFilterPatronymic.isChecked():
            patronymic = forceStringEx(self.edtFilterPatronymic.text())
            lines.append(u'Отчество: %s' % patronymic)
        return '\n'.join(lines)

    def applyFilter(self):
        self.updateCertificatesList()

    def resetFilter(self):
        self.chkFilterSurname.setChecked(False)
        self.chkFilterName.setChecked(False)
        self.chkFilterPatronymic.setChecked(False)
        self.updateCertificatesList()

    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelCertificates_currentRowChanged(self, current, previous):
        self.updateEditClientAction()

    @pyqtSignature('QItemSelection, QItemSelection')
    def on_selectionModelCertificates_selectionChanged(self, selected, deselected):
        selectedRecords = self.getSelectedRecords()
        validRecords = [record for record in selectedRecords if not record.value('client_id').isNull()]
        self.btnSyncSelected.setEnabled(len(validRecords) > 0)
        self.updateCertificateInfo()

    @pyqtSignature('QAbstractButton*')
    def on_filterButtonBox_clicked(self, button):
        buttonCode = self.filterButtonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.applyFilter()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.resetFilter()

    @pyqtSignature('int')
    def on_chkFilterSurname_stateChanged(self, state):
        self.edtFilterSurname.setEnabled(state == Qt.Checked)

    @pyqtSignature('int')
    def on_chkFilterName_stateChanged(self, state):
        self.edtFilterName.setEnabled(state == Qt.Checked)

    @pyqtSignature('int')
    def on_chkFilterPatronymic_stateChanged(self, state):
        self.edtFilterPatronymic.setEnabled(state == Qt.Checked)
    
    @pyqtSignature('')
    def on_actEditClient_triggered(self):
        record = self.tblCertificates.currentItem()
        clientId = forceRef(record.value('client_id')) if record else None
        if clientId is not None:
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
    def on_btnSyncSelected_clicked(self):
        self.syncSelected()

    @pyqtSignature('')
    def on_btnFindClient_clicked(self):
        self.findClient()

    @pyqtSignature('')
    def on_btnShowReport_clicked(self):
        self.showReport()
    
    @pyqtSignature('')
    def on_btnSelectAll_clicked(self):
        self.tblCertificates.selectAll()
    
    @pyqtSignature('')
    def on_btnClearSelection_clicked(self):
        self.tblCertificates.clearSelection()


class CCertificatesModel(CTableModel):
    class CFoundCol(CBoolCol):
        def checked(self, values):
            clientId = forceRef(values[0])
            if clientId is not None:
                return CBoolCol.valChecked
            else:
                return CBoolCol.valUnchecked

    def __init__(self, parent):
        self.certificateInfoDict = {}
        CTableModel.__init__(self, parent)
        self.addColumn(CNameCol(u'Фамилия',    ['surname'], 15))
        self.addColumn(CNameCol(u'Имя',        ['name'], 15))
        self.addColumn(CNameCol(u'Отчество',   ['patronymic'], 15))
        self.addColumn(CEnumCol(u'Пол',        ['gender'], [u'М', u'Ж'], 4, 'c'))
        self.addColumn(CDateFixedCol(u'Дата рожд.', ['birthDate'], 12, highlightRedDate=False))
        self.addColumn(CDateTimeFixedCol(u'Дата смерти', ['deathDate'], 12, highlightRedDate=False))
        self.addColumn(CDateFixedCol(u'Сертификат', ['certDate'], 12, highlightRedDate=False))
        self.addColumn(CCertificatesModel.CFoundCol(u'Найден в МИС', ['client_id'], 15))
        self.addColumn(CTextCol(u'Участок', ['numberSector'], 15))
        self.addColumn(CTextCol(u'Полис', ['numberDoccofirm'], 15))
        self.setTable('demogr_Certificate')

class CDemogrCertificatesReport(CReportBase):
    def __init__(self, parent, model):
        CReportBase.__init__(self, parent)
        self.model = model
        self.setTitle(u'Сервис Демография (умершие)')
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
            ('15%', [u'Фамилия'      ], CReportBase.AlignLeft),
            ('15%', [u'Имя'          ], CReportBase.AlignLeft),
            ('15%', [u'Отчество'     ], CReportBase.AlignLeft),
            ('5%',  [u'Пол'          ], CReportBase.AlignLeft),
            ('10%', [u'Дата рождения'], CReportBase.AlignLeft),
            ('10%', [u'Дата смерти'  ], CReportBase.AlignLeft),
            ('10%', [u'Сертификат'   ], CReportBase.AlignLeft),
            ('5%',  [u'Найден в МИС' ], CReportBase.AlignLeft),
            ('5%',  [u'Участок'      ], CReportBase.AlignLeft),
            ('10%', [u'Полис'],         CReportBase.AlignLeft),
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

class CDemogrClientSearchDialog(CExternalClientSearchDialog):
    def __init__(self, parent, serviceRecord):
        defaultFilter = {
            'lastName': forceString(serviceRecord.value('surname')),
            'firstName': forceString(serviceRecord.value('name')),
            'patrName': forceString(serviceRecord.value('patronymic')),
            'birthDate': forceDate(serviceRecord.value('birthDate'))
        }
        CExternalClientSearchDialog.__init__(self, parent, defaultFilter=defaultFilter, addInfo=u'Данные web-сервиса')
        self.externalInfo['lastName'] = self.infoStringValue(serviceRecord.value('surname'))
        self.externalInfo['firstName'] = self.infoStringValue(serviceRecord.value('name'))
        self.externalInfo['patrName'] = self.infoStringValue(serviceRecord.value('patronymic'))
        gender = serviceRecord.value('gender')
        gender = None if gender.isNull() else forceInt(gender)
        self.externalInfo['sex'] = {0: u"М", 1: u"Ж"}.get(gender)
        self.externalInfo['birthDate'] = self.infoDateValue(serviceRecord.value('birthDate'))
        self.updateInfoText()