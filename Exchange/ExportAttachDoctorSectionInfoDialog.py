# -*- coding: utf-8 -*-

from itertools import groupby

from PyQt4 import QtGui
from PyQt4.QtCore import *

from library.DialogBase import CConstructHelperMixin
from library.TableModel import CTableModel, CCol, CTextCol
from library.Utils import *
from RefBooks.Person.List import CPersonEditor
from Users.Rights import urAdmin, urAccessRefPerson, urAccessRefPersonPersonal
from Orgs.Utils import getOrgStructureDescendants
import Exchange.AttachService as AttachService

from Ui_ExportAttachDoctorSectionInfoDialog import Ui_ExportAttachDoctorSectionInfoDialog

class CExportAttachDoctorSectionInfoDialog(QtGui.QDialog, CConstructHelperMixin, Ui_ExportAttachDoctorSectionInfoDialog):
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        self.addModels('PersonOrder', CPersonOrderModel(self))
        self.addObject('actEditPerson', QtGui.QAction(u'Редактировать данные сотрудника', self))
        self.setupUi(self)
        self.actEditPerson.setEnabled(QtGui.qApp.userHasAnyRight([urAdmin, urAccessRefPerson, urAccessRefPersonPersonal]))
        self.tblPersonOrder.createPopupMenu([self.actEditPerson])
        self.lblExportStatus.setVisible(False)
        self.edExportResults.setVisible(False)
        self.pbExportProgress.setVisible(False)
        self.setModels(self.tblPersonOrder, self.modelPersonOrder, self.selectionModelPersonOrder)
        self.modelPersonOrder.setShowErrorsOnly(self.rbShowErrors.isChecked())
        header = self.tblPersonOrder.horizontalHeader()
        header.setSortIndicatorShown(True)
        header.setSortIndicator(0, Qt.AscendingOrder)
        QObject.connect(header, SIGNAL('sectionClicked(int)'), self.setSort)

    def showEvent(self, event):
        QTimer.singleShot(0, self.updateList)
    
    def disableControls(self, disabled = True):
        self.rbShowAll.setDisabled(disabled)
        self.rbShowErrors.setDisabled(disabled)
        self.tblPersonOrder.setDisabled(disabled)
        self.btnExport.setDisabled(disabled)
        self.btnClose.setDisabled(disabled)

    def enableControls(self):
        self.disableControls(False)
        
    def updateList(self, personOrderId = None):
        self.disableControls()
        labelText = u'Обновление списка...'
        try:
            self.lblPersonOrderCount.setText(labelText)
            QtGui.qApp.processEvents()
            self.modelPersonOrder.update()
            if personOrderId:
                self.tblPersonOrder.setCurrentItemId(personOrderId)
            allCount = len(self.modelPersonOrder._idList)
            errorInList = [id for id in self.modelPersonOrder._idList if id in self.modelPersonOrder.errorsById]
            errorInListCount = len(errorInList)
            labelText = u'Всего записей: %d, из них %d с ошибками' % (allCount, errorInListCount)
            self.btnExport.setEnabled(allCount > 0)
        except Exception as e:
            labelText = unicode(e)
        finally:
            self.enableControls()
            self.lblPersonOrderCount.setText(labelText)
    
    def getRequests(self):
        requests = {}
        for record in self.modelPersonOrder.recordsById.itervalues():
            if self.modelPersonOrder.showOrgStruct and forceInt(record.value('orgStructure_id')) not in self.modelPersonOrder.showOrgStructIds:
                continue
            moCode = forceString(record.value('moCode'))
            if moCode not in requests:
                requests[moCode] = {}
            status = forceInt(record.value("status"))
            doctors = requests[moCode]
            spec = forceString(record.value("spec"))
            personKey = forceString(record.value("personKey"))
            createDate = QDateTime.currentDateTime()
            if personKey not in doctors:
                doctors[personKey] = {
                    "lastName": forceString(record.value("lastName")),
                    "firstName": forceString(record.value("firstName")),
                    "patrName": forceString(record.value("patrName")),
                    "birthDate": forceString(forceDate(record.value("birthDate")).toString('yyyy-MM-dd')),
                    "snils": forceString(record.value('snils')),
                    "status": status,
                    "spec": spec,
                    "createDate": forceString(createDate.toString('yyyy-MM-ddThh:mm:ss')),
                    "sectInfos": []
                }
            elif doctors[personKey]["status"] < status:
                doctors[personKey]["status"] = status
                doctors[personKey]["spec"] = spec
            sectInfos = doctors[personKey]["sectInfos"]
            sectInfos.append({
                "beginDate": forceString(forceDate(record.value("beginDate")).toString('yyyy-MM-dd')),
                "sect": forceString(record.value('sect')),
            })
        for moCode, doctors in requests.items():
            requests[moCode] = doctors.values()
        return requests
    
    def export(self):
        requests = self.getRequests()
        if not requests:
            QtGui.QMessageBox.information(self, u'Сведения не отправлены', u'Нет данных для отправки',
                                          QtGui.QMessageBox.Close)
            return
        results = []
        self.disableControls()
        successCount = 0
        errorCount = 0
        try:
            self.clearLog()
            self.showLog()

            self.lblExportStatus.setText(u"Отправка пакетов...")
            self.pbExportProgress.setMaximum(len(requests))
            self.pbExportProgress.setValue(0)
            self.edExportResults.clear()
            self.lblExportStatus.setVisible(True)
            self.pbExportProgress.setVisible(True)
            self.edExportResults.setVisible(True)
            for moCode, doctors in requests.iteritems():
                QtGui.qApp.processEvents()
                try:
                    response = AttachService.sendAttachDoctorSectionInformation(moCode, doctors)
                    result = response[u'result']
                    self.appendLog(u"Экспорт участка %s - запрос" % moCode, True)
                    self.appendLog(response['req'], True)
                    self.appendLog(u"Экспорт участка %s - ответ" % moCode, False)
                    self.appendLog(
                        response['result']['responcepack']['p10_packrespinf']['r11_rsinf']['responceMessage'], False
                    )
                    self.appendLog(u"%s: успешно" % moCode, False)
                    successCount += 1
                except Exception as e:
                    self.appendLog(u"%s: ошибка (%s)" % (moCode, exceptionToUnicode(e)))
                    errorCount += 1
                finally:
                    self.showLog()
                self.pbExportProgress.setValue(self.pbExportProgress.value() + 1)
            totalCount = successCount + errorCount
            message = u"Сведения отправлены: учреждений %d, из них %d успешно, %d с ошибками" % (totalCount, successCount, errorCount)
            self.lblExportStatus.setText(message)
        except Exception as e:
            self.lblExportStatus.setText(u"Ошибка: %s" % exceptionToUnicode(e))
        finally:
            self.enableControls()
            self.pbExportProgress.setVisible(False)

    def setSort(self, newColumn):
        newOrderField = self.modelPersonOrder.orderByColumn[newColumn]
        if newOrderField is None:
            return
        column, asc = self.modelPersonOrder.order
        if column == newColumn:
            newAsc = not asc
        else:
            newAsc = True
        self.modelPersonOrder.order = (newColumn, newAsc)
        self.updateList()
    
    def currentRecord(self):
        id = self.tblPersonOrder.currentItemId()
        if id is None:
            return None
        else:
            return self.modelPersonOrder.recordsById[id]

    def clearLog(self):
        self.shortLog = u''
        self.fullLog = u''

    def appendLog(self, text, fullLogOnly):
        self.fullLog += text
        self.fullLog += u'\r\n'
        if not fullLogOnly:
            self.shortLog += text
            self.shortLog += u'\r\n'

    def showLog(self):
        if self.chbFullLog.isChecked():
            self.edExportResults.setPlainText(self.fullLog)
        else:
            self.edExportResults.setPlainText(self.shortLog)
        self.edExportResults.verticalScrollBar().setValue(self.edExportResults.verticalScrollBar().maximum())
        QtGui.qApp.processEvents()

    @pyqtSignature('')
    def on_btnClose_clicked(self):
        self.reject()

    @pyqtSignature('')
    def on_btnExport_clicked(self):
        self.export()

    @pyqtSignature('')
    def on_btnRefresh_clicked(self):
        self.updateList()

    @pyqtSignature('')
    def on_rbShowAll_clicked(self):
        self.modelPersonOrder.setShowErrorsOnly(False)

    @pyqtSignature('')
    def on_rbShowErrors_clicked(self):
        self.modelPersonOrder.setShowErrorsOnly(True)

    @pyqtSignature('int')
    def on_cmbOrgStructure_currentIndexChanged(self, index):
        orgStructureId = self.cmbOrgStructure.value()
        self.modelPersonOrder.setShowOrgStructOnly(orgStructureId)
        self.updateList()

    @pyqtSignature('')
    def on_actEditPerson_triggered(self):
        record = self.currentRecord()
        personId = forceRef(record.value('person_id'))
        personOrderId = forceRef(record.value('id'))
        if personId is not None and QtGui.qApp.userHasAnyRight([urAdmin, urAccessRefPerson, urAccessRefPersonPersonal]):
            dialog = None
            try:
                QtGui.qApp.setWaitCursor()
                try:
                    dialog = CPersonEditor(self)
                    dialog.load(personId)
                finally:
                    QtGui.qApp.restoreOverrideCursor()
                if dialog.exec_():
                    self.updateList(personOrderId)
            finally:
                if dialog:
                    dialog.deleteLater()

class CPersonOrderModel(CTableModel):
    ErrorTypes = {
        1: u"Не указана дата начала",
        2: u"Для медработника один и тот же участок выбран несколько раз",
        3: u"Одинаковый СНИЛС у разных врачей",
        4: u"Настройка номера или типа участка некорректна",
        5: u"Несколько врачей закреплены за одним участком"
    }

    class CInfoCol(CTextCol):
        def __init__(self, title, infoField, recordsDict, defaultWidth, alignment='l'):
            CTextCol.__init__(self, title, ['id'], defaultWidth, 'l')
            self.recordsDict = recordsDict
            self.infoField = infoField

        def format(self, values):
            id = forceRef(values[0])
            record = self.recordsDict.get(id)
            if record:
                return QVariant(forceString(record.value(self.infoField)))
            else:
                return CCol.invalid

    class CErrorsCol(CTextCol):
        def __init__(self, title, errorsDict, defaultWidth, alignment='l'):
            CTextCol.__init__(self, title, ['id'], defaultWidth, 'l')
            self.errorsDict = errorsDict

        def format(self, values):
            id = forceRef(values[0])
            errors = self.errorsDict.get(id)
            if errors:
                return QVariant(u'; '.join([CPersonOrderModel.ErrorTypes[error] for error in errors]))
            else:
                return CCol.invalid

    def __init__(self, parent):
        self.orderByColumn = [
            'p.lastName',
            'p.firstName',
            'p.patrName',
            'p.birthDate',
            'p.SNILS',
            'po.validFromDate',
            'case when post.high = 1 then 1 else 2 end',
            'IF(length(o1.bookkeeperCode) = 5, o1.bookkeeperCode, IF(length(o2.bookkeeperCode) = 5, o2.bookkeeperCode, IF(length(o3.bookkeeperCode) = 5, o3.bookkeeperCode, IF(length(o4.bookkeeperCode) = 5, o4.bookkeeperCode, o5.bookkeeperCode))))',
            'o1.infisInternalCode',
            's.regionalCode',
        ]
        self.showErrorsOnly = False
        self.showOrgStruct = None
        self.showOrgStructIds = list()
        self.recordsById = {}
        self.errorsById = {}
        self.order = (0, True)
        CTableModel.__init__(self, parent)
        self.addColumn(self.CInfoCol(u'Фамилия', 'lastName', self.recordsById, 20))
        self.addColumn(self.CInfoCol(u'Имя', 'firstName', self.recordsById, 20))
        self.addColumn(self.CInfoCol(u'Отчество', 'patrName', self.recordsById, 20))
        self.addColumn(self.CInfoCol(u'Дата рожд.', 'birthDate', self.recordsById, 20))
        self.addColumn(self.CInfoCol(u'СНИЛС', 'SNILS', self.recordsById, 20))
        self.addColumn(self.CInfoCol(u'Действителен с', 'beginDate', self.recordsById, 20))
        self.addColumn(self.CInfoCol(u'Категория медработника', 'statusName', self.recordsById, 20))
        self.addColumn(self.CInfoCol(u'Код МО', 'moCode', self.recordsById, 20))
        self.addColumn(self.CInfoCol(u'Участок', 'sect', self.recordsById, 20))
        self.addColumn(self.CInfoCol(u'Специальность', 'specName', self.recordsById, 20))
        self.addColumn(self.CErrorsCol(u'Ошибки', self.errorsById, 20))
        self.loadField('id')
        self.setTable('Person_Order')
    
    def setError(self, id, error):
        if id in self.errorsById:
            self.errorsById[id].add(error)
        else:
            self.errorsById[id] = set([error])

    def update(self):
        db = QtGui.qApp.db

        sql = u"""
            select 
                po.id as id,
                p.id as person_id,
                p.lastName as lastName,
                p.firstName as firstName,
                p.patrName as patrName,
                p.birthDate as birthDate,
                p.SNILS as snils,
                po.validFromDate as beginDate,
                case when post.high = 1 then 1 else 2 end as status,
                case when post.high = 1 then '1 - врач' else '2 - средний мед. персонал' end as statusName,
                IF(length(o1.bookkeeperCode) = 5, o1.bookkeeperCode, IF(length(o2.bookkeeperCode) = 5, o2.bookkeeperCode, IF(length(o3.bookkeeperCode) = 5, o3.bookkeeperCode, IF(length(o4.bookkeeperCode) = 5, o4.bookkeeperCode, o5.bookkeeperCode)))) as moCode,
                o1.infisInternalCode as sect,
                concat_ws('', p.lastName, ';', p.firstName, ';', p.patrName, ';', p.birthDate, ';', p.SNILS) as personKey,
                s.regionalCode AS spec,
                s.name AS specName,
                o1.areaType,
                po.orgStructure_id
            from Person_Order po
                left join Person p ON p.id = po.master_id
                left join rbSpeciality s ON s.id = p.speciality_id
                left join rbPost post on post.id = po.post_id
                inner join OrgStructure o1 on o1.id = po.orgStructure_id
                left join OrgStructure o2 on o2.id = o1.parent_id
                left join OrgStructure o3 on o3.id = o2.parent_id
                left join OrgStructure o4 on o4.id = o3.parent_id
                left join OrgStructure o5 on o5.id = o4.parent_id
            where po.type = 6
                and po.documentType_id IS NOT NULL
                and po.deleted = 0
                and LENGTH(p.SNILS) > 0
                and (po.validToDate IS NULL or LENGTH(po.validToDate) = 0 or po.validToDate >= current_date)
                and (po.validFromDate IS NULL or LENGTH(po.validFromDate) = 0 or po.validFromDate <= current_date)
            """

        orderColumnIndex, isAscending = self.order
        orderBy = self.orderByColumn[orderColumnIndex]
        orderBy += (' asc' if isAscending else ' desc')
        sql += (' order by ' + orderBy)

        self.fullIdList = []
        self.recordsById.clear()
        self.errorsById.clear()
        db = QtGui.qApp.db
        query = db.query(sql)

        peopleBySnils = {}
        personOrderIdsByPersonSect = {}
        doctorsBySect = {}
        while query.next():
            record = query.record()
            personOrderId = forceRef(record.value('id'))
            self.fullIdList.append(personOrderId)
            self.recordsById[personOrderId] = record
            moCode = forceString(record.value('moCode'))
            snils = forceString(record.value('snils'))
            personKey = forceString(record.value('personKey'))
            status = forceInt(record.value('status'))
            snilsKey = (moCode, snils)
            if snilsKey not in peopleBySnils:
                peopleBySnils[snilsKey] = (set([personKey]), set([personOrderId]))
            else:
                peopleBySnils[snilsKey][0].add(personKey)
                peopleBySnils[snilsKey][1].add(personOrderId)
            sect = forceString(record.value('sect'))
            areaType = forceInt(record.value('areaType'))
            if sect == '' or areaType == 0:
                self.setError(personOrderId, 4) # Настройка номера или типа участка некорректна
            if sect != '':
                personSectKey = (moCode, personKey, sect)
                if personSectKey not in personOrderIdsByPersonSect:
                    personOrderIdsByPersonSect[personSectKey] = set([personOrderId])
                else:
                    personOrderIdsByPersonSect[personSectKey].add(personOrderId)
                if status == 1:
                    sectKey = sect
                    if sectKey not in doctorsBySect:
                        doctorsBySect[sectKey] = (set([personKey]), set([personOrderId]))
                    else:
                        doctorsBySect[sectKey][0].add(personKey)
                        doctorsBySect[sectKey][1].add(personOrderId)
            if record.isNull('beginDate'):
                self.setError(personOrderId, 1) # Не указана дата начала
        for personKeys, personOrderIds in peopleBySnils.itervalues():
            if len(personKeys) > 1:
                for personOrderId in personOrderIds:
                    self.setError(personOrderId, 3) # Одинаковый СНИЛС у разных врачей
        for personOrderIds in personOrderIdsByPersonSect.itervalues():
            if len(personOrderIds) > 1:
                for personOrderId in personOrderIds:
                    self.setError(personOrderId, 2) # Один и тот же код участка указан несколько раз
        for personKeys, personOrderIds in doctorsBySect.itervalues():
            if len(personKeys) > 1:
                for personOrderId in personOrderIds:
                    self.setError(personOrderId, 5) # Несколько врачей прикреплено к одному участку
        self.updateIdList()
    
    def updateIdList(self):
        idList = []
        for id in self.fullIdList:
            record = self.recordsById[id]
            if self.showOrgStruct and record.value('orgStructure_id') not in self.showOrgStructIds:
                continue
            if self.showErrorsOnly and id not in self.errorsById:
                continue
            idList.append(id)
        self.setIdList(idList)

    def setShowErrorsOnly(self, showErrorsOnly):
        self.showErrorsOnly = showErrorsOnly
        if len(self.recordsById) > 0:
            self.updateIdList()

    def setShowOrgStructOnly(self, showOrgStruct):
        self.showOrgStruct = showOrgStruct
        self.showOrgStructIds = list()
        if showOrgStruct:
            self.showOrgStructIds = getOrgStructureDescendants(showOrgStruct)
        if len(self.recordsById) > 0:
            self.updateIdList()
