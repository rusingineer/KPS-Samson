# -*- coding: utf-8 -*-

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDate, QVariant, QObject, SIGNAL, QTimer, pyqtSignature
from PyQt4.QtGui import QAction

from library.DialogBase import CDialogBase
from library.TableModel import CTableModel, CCol, CTextCol, CIntCol, CDateCol, CDesignationCol
from library.Utils import exceptionToUnicode, forceRef, formatName, toVariant, forceBool, forceDate, forceInt

import Exchange.AttachService as AttachService

from Registry.ClientEditDialog import CClientEditDialog

from Users.Rights import urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry

from Ui_ExportDispPlanDialog import Ui_ExportDispPlanDialog


class CExportDispPlanDialog(CDialogBase, Ui_ExportDispPlanDialog):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.initialized = False
        self.addModels('DispPlan', CDispPlanModel(self))
        self.addModels('DispPlanErrors', CDispPlanErrorsModel(self))
        self.addObject('actEditClient', QAction(u'Открыть регистрационную карточку', self))
        self.addObject('actDeletePlanExport', QtGui.QAction(u'Удалить признак экспорта', self))
        self.setupUi(self)
        self.setWindowFlags(Qt.Window)
        self.actEditClient.setEnabled(QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]))
        self.tblDispPlan.createPopupMenu([self.actEditClient, self.actDeletePlanExport])
        self.pbExportProgress.setVisible(False)
        self.lblExportStatus.setVisible(False)
        currentDate = QDate.currentDate()
        self.sbYear.setValue(currentDate.year())
        self.cmbMonthFrom.setCurrentIndex(currentDate.month() - 1)
        self.cmbKind.addItem(u"все", QVariant())
        self.cmbKind.addItem(u"Дисп. раз в 3 г", QVariant('disp'))
        self.cmbKind.addItem(u"Дисп. раз в 2 г", QVariant('disp_2'))
        self.cmbKind.addItem(u"Дисп. ежегодная", QVariant('disp_1'))
        self.cmbKind.addItem(u"Проф. осмотр", QVariant('prof'))
        self.cmbKind.addItem(u"Дисп. углубленная (гр. 1)", QVariant('disp_cov1'))
        self.cmbKind.addItem(u"Дисп. углубленная (гр. 2)", QVariant('disp_cov2'))
        self.cmbKind.setCurrentIndex(0)
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
            kind = self.cmbKind.itemData(self.cmbKind.currentIndex())
            kind = unicode(kind.toString()) if kind.isValid() else None
            QtGui.qApp.processEvents()
            self.modelDispPlan.update(year, monthFrom, monthTo, kind)
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
                result = AttachService.putEvPlanList('ClientSocStatus', ids)
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
        cssId = self.tblDispPlan.currentItemId()
        if cssId is None:
            return None
        else:
            return self.modelDispPlan.cssInfoDict[cssId]

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

    @pyqtSignature('int')
    def on_cmbKind_currentIndexChanged(self, index):
        if self.initialized:
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
    class CClientCol(CCol):
        def __init__(self, title, fields, defaultWidth, infoDict):
            CCol.__init__(self, title, fields, defaultWidth, 'l')
            db = QtGui.qApp.db
            self.dict = infoDict

        def format(self, values):
            cssId = forceRef(values[0])
            record = self.dict.get(cssId)
            if record:
                name = formatName(
                    record.value('lastName'),
                    record.value('firstName'),
                    record.value('patrName')
                    )
                return toVariant(name)
            else:
                return CCol.invalid

    class CClientAgeCol(CCol):
        def __init__(self, title, fields, defaultWidth, model, infoDict):
            CCol.__init__(self, title, fields, defaultWidth, 'c')
            self.model = model
            self.dict = infoDict

        def format(self, values):
            cssId = forceRef(values[0])
            record = self.dict.get(cssId)
            if record:
                birthDate = record.value('birthDate')
                if birthDate.type() in (QVariant.Date, QVariant.DateTime):
                    birthYear = birthDate.toDate().year()
                    selectedYear = self.model.year
                return QVariant(selectedYear - birthYear)
            else:
                return CCol.invalid

    class CYearMonthCol(CCol):
        def __init__(self, title, fields, defaultWidth):
            CCol.__init__(self, title, fields, defaultWidth, 'l')

        def format(self, values):
            val = values[0]
            if val.type() in (QVariant.Date, QVariant.DateTime):
                val = val.toDate()
                return QVariant(val.toString('MMMM yyyy'))
            return CCol.invalid

    class CExportStatusCol(CCol):
        def __init__(self, title, fields, defaultWidth, infoDict):
            CCol.__init__(self, title, fields, defaultWidth, 'l')
            db = QtGui.qApp.db
            self.dict = infoDict

        def format(self, values):
            cssId = forceRef(values[0])
            record = self.dict.get(cssId)
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

    class CSocStatusTypeNameCol(CTextCol):
        def __init__(self, title, fields, defaultWidth):
            CTextCol.__init__(self, title, fields, defaultWidth, 'l')
            db = QtGui.qApp.db
            disp3Id = forceRef(db.translate('rbSocStatusType', 'code', 'disp', 'id'))
            disp2Id = forceRef(db.translate('rbSocStatusType', 'code', 'disp_2', 'id'))
            disp1Id = forceRef(db.translate('rbSocStatusType', 'code', 'disp_1', 'id'))
            profId = forceRef(db.translate('rbSocStatusType', 'code', 'prof', 'id'))
            dispCov1Id = forceRef(db.translate('rbSocStatusType', 'code', 'disp_cov1', 'id'))
            dispCov2Id = forceRef(db.translate('rbSocStatusType', 'code', 'disp_cov2', 'id'))
            self.typeNameById = {
                disp3Id: u'Дисп. раз в 3 г',
                disp2Id: u'Дисп. раз в 2 г',
                disp1Id: u'Дисп. ежегодная',
                profId: u'Проф. осмотр',
                dispCov1Id: u'Дисп. углубленная (группа 1)',
                dispCov2Id: u'Дисп. углубленная (группа 2)'
            }


        def format(self, values):
            typeId = forceRef(values[0])
            if typeId in self.typeNameById:
                name = self.typeNameById[typeId]
                return toVariant(name)
            else:
                return CCol.invalid
    
    class CAttachCol(CTextCol):
        def __init__(self, title, fields, defaultWidth, infoDict):
            CTextCol.__init__(self, title, fields, defaultWidth, 'l')
            self.dict = infoDict

        def format(self, values):
            clientId = forceRef(values[0])
            record = self.dict.get(clientId)
            if record:
                return record.value('attachName')
            else:
                return CCol.invalid

    def __init__(self, parent):
        self.cssInfoDict = {}
        self.orderByColumn = [
            'Client.lastName',
            '(year(CSS.begDate) - year(Client.birthDate))',
            'CSS.begDate',
            'PlanExport.exportSuccess',
            'CSS.socStatusType_id',
            'CSS.begDate',
            'CSS.endDate',
            'AttachOrgStructure.name',
        ]
        self.order = (0, True)
        CTableModel.__init__(self, parent)
        self.addColumn(CDispPlanModel.CClientCol(u'Ф.И.О.', ['id'], 20, self.cssInfoDict))
        self.addColumn(CDispPlanModel.CClientAgeCol(u'Возраст', ['id'], 20, self, self.cssInfoDict))
        self.addColumn(CDispPlanModel.CYearMonthCol(u'Запланирован на месяц', ['begDate'], 20))
        self.addColumn(CDispPlanModel.CExportStatusCol(u'Статус', ['id'], 20, self.cssInfoDict))
        self.addColumn(CDispPlanModel.CSocStatusTypeNameCol(u'Мероприятие', ['socStatusType_id'], 15))
        self.addColumn(CDateCol(u'Дата начала', ['begDate'], 15))
        self.addColumn(CDateCol(u'Дата окончания', ['endDate'], 15))
        self.addColumn(CDispPlanModel.CAttachCol(u'Участок', ['id'], 15, self.cssInfoDict))
        self.setTable('ClientSocStatus')

    def update(self, year, monthFrom, monthTo, kind):
        db = QtGui.qApp.db
        dateFrom = QDate(year, monthFrom, 1)
        dateTo = QDate(year, monthTo, 1).addMonths(1).addDays(-1)
        if kind is None:
            cssTypeCond = u"SST.code in ('disp', 'disp_2', 'disp_1', 'prof', 'disp_cov1', 'disp_cov2')"
        else:
            cssTypeCond = u"SST.code = '%s'" % kind

        sql = u"""
        select CSS.*,
            Client.firstName,
            Client.lastName,
            Client.patrName,
            Client.birthDate,
            PlanExport.exportDate,
            PlanExport.exportSuccess,
            PlanExport.id as planExport_id,
            AttachOrgStructure.name as attachName
        from ClientSocStatus as CSS
            left join rbSocStatusClass as SSC on SSC.id = CSS.socStatusClass_id
            left join rbSocStatusType as SST on SST.id = CSS.socStatusType_id
            left join Client on Client.id = CSS.client_id
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
            left join disp_PlanExport as PlanExport on PlanExport.exportKind = 'ClientSocStatus' and PlanExport.row_id = CSS.id
            left join OrgStructure as AttachOrgStructure on AttachOrgStructure.id = Attach.orgStructure_id
        where CSS.deleted = 0
            and Client.deleted = 0
            and SSC.code = 'profilac'
            and %(cssTypeCond)s
            and CSS.begDate >= '%(dateFrom)s'
            and CSS.begDate <= '%(dateTo)s'
        """ % {
            "cssTypeCond": cssTypeCond,
            "dateFrom": dateFrom.toString('yyyy-MM-dd'),
            "dateTo": dateTo.toString('yyyy-MM-dd'),
        }
        orderColumnIndex, isAscending = self.order
        orderBy = self.orderByColumn[orderColumnIndex]
        orderBy += (' asc' if isAscending else ' desc')
        sql += (' order by ' + orderBy)
        
        idList = []
        self.cssInfoDict.clear()
        notExportedIdList = []
        errorsIdList = []
        query = db.query(sql)
        while query.next():
            record = query.record()
            cssId = record.value('id').toInt()[0]
            idList.append(cssId)
            self.cssInfoDict[cssId] = record
            exportSuccess = record.value('exportSuccess')
            if exportSuccess.isNull():
                notExportedIdList.append(cssId)
            elif forceInt(exportSuccess) == 0:
                errorsIdList.append(cssId)
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
