# -*- coding: utf-8 -*-

from PyQt4 import QtGui
from PyQt4.QtCore import QTimer, pyqtSignature, QVariant

from Exchange import SanAviacService
from library.DialogBase import CConstructHelperMixin
from library.TableModel import CTableModel, CCol, CTextCol

from Ui_ExportSanAviacInfoDialog import Ui_ExportSanAviacInfoDialog
from library.Utils import forceInt, forceString, forceDate, forceDateTime, exceptionToUnicode, forceRef


class CExportSanAviacInfoDialog(QtGui.QDialog, CConstructHelperMixin, Ui_ExportSanAviacInfoDialog):
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        self.addModels('SanAviac', CSanAviacModel(self))
        self.setupUi(self)
        self.lblExportStatus.setVisible(False)
        self.edExportResults.setVisible(False)
        self.pbExportProgress.setVisible(False)
        self.setModels(self.tblSanAviac, self.modelSanAviac, self.selectionModelSanAviac)

    def disableControls(self, disabled=True):
        self.tblSanAviac.setDisabled(disabled)
        self.btnExport.setDisabled(disabled)
        self.btnClose.setDisabled(disabled)

    def enableControls(self):
        self.disableControls(False)

    def showEvent(self, event):
        QTimer.singleShot(0, self.updateList)

    def updateList(self):
        self.disableControls()
        labelText = u'Обновление списка...'
        try:
            self.lblSavAviacRecordCount.setText(labelText)
            QtGui.qApp.processEvents()
            self.modelSanAviac.update()
            allCount = len(self.modelSanAviac.recordsById)
            errorCount = len(self.modelSanAviac.errorsById)
            labelText = u'Всего записей: %d, из них %d с ошибками' % (allCount, errorCount)
            self.btnExport.setEnabled(allCount > 0)
        except Exception as e:
            labelText = unicode(e)
        finally:
            self.enableControls()
            self.lblSavAviacRecordCount.setText(labelText)

    def getRequests(self):
        requests = []
        for record in self.modelSanAviac.recordsById.itervalues():

            if forceInt(record.value("iserrorrecord")) == 0:
                diagnostics = []

                for diagnostic in forceString(record.value("diagnostics")).split(','):
                    diagnostics.append({"diagnostics_code": diagnostic})

                requests.append({
                    "fam": forceString(record.value("fam")),
                    "ima": forceString(record.value("ima")),
                    "otch": forceString(record.value("otch")),
                    "birthDate": forceString(forceDate(record.value("birthDate")).toString('yyyy-MM-dd')),
                    "addr": forceString(record.value("addr")),
                    "MKBX_code": forceString(record.value("MKBX_code")),
                    "MedSection_code": forceString(record.value("MedSection_code")),
                    "dateIn": forceString(forceDateTime(record.value("dateIn")).toString('yyyy-MM-dd hh:mm:ss')),
                    "dateTrans": forceString(forceDateTime(record.value("dateTrans")).toString('yyyy-MM-dd hh:mm:ss')),
                    "diagnostics": diagnostics,
                    "constist_code": forceString(record.value("constist_code")),
                    "IDr": forceString(record.value("IDr"))
                })

        return requests

    def export(self):
        self.edExportResults.clear()
        requests = self.getRequests()

        if len(requests) < 1:
            self.edExportResults.setVisible(True)
            self.edExportResults.insertPlainText(u"данных для выгрузки нет")
            return None

        self.disableControls()
        self.edExportResults.setVisible(True)
        try:
            urlService = forceString(QtGui.qApp.db.translate('GlobalPreferences', 'code', 'PHP_ServicesUrl', 'value'))
            if not urlService:
                urlService = QtGui.qApp.preferences.dbServerName
            result = SanAviacService.sendSanAviacInformation(requests, "http://%s/san_avia/handler.php" % urlService)

            for resultItem in result['result']:
                self.edExportResults.insertPlainText(u"ActionID %s: %s\n" % (resultItem["IDr"],  (resultItem["Error"] if resultItem["Error"] != "" else u"успешно") ))

        except Exception as e:
            self.lblExportStatus.setText(u"Ошибка: %s" % exceptionToUnicode(e))
        finally:
            self.updateList()
            self.enableControls()
            self.pbExportProgress.setVisible(False)

# buttons
    @pyqtSignature('')
    def on_btnExport_clicked(self):
        self.export()

    @pyqtSignature('')
    def on_btnClose_clicked(self):
        self.reject()

    @pyqtSignature('')
    def on_btnRefresh_clicked(self):
        self.updateList()


class CSanAviacModel(CTableModel):
    ErrorTypes = {
        1: u"Не заполнен диагноз",
        2: u"Не заполнено отделение",
        3: u"Не заполнено состояние"
    }

    class CInfoCol(CTextCol):
        def __init__(self, title, infoField, recordsDict, defaultWidth, alignment='l'):
            CTextCol.__init__(self, title, ['id'], defaultWidth, alignment)
            self.recordsDict = recordsDict
            self.infoField = infoField

        def format(self, values):
            _id = forceRef(values[0])
            record = self.recordsDict.get(_id)
            if record:
                return QVariant(forceString(record.value(self.infoField)))
            else:
                return CCol.invalid

    class CErrorsCol(CTextCol):
        def __init__(self, title, errorsDict, defaultWidth, alignment='l'):
            CTextCol.__init__(self, title, ['id'], defaultWidth, alignment)
            self.errorsDict = errorsDict

        def format(self, values):
            _id = forceRef(values[0])
            errors = self.errorsDict.get(_id)
            if errors:
                return QVariant(u'; '.join([CSanAviacModel.ErrorTypes[error] for error in errors]))
            else:
                return CCol.invalid

    def __init__(self, parent):
        self.recordsById = {}
        self.errorsById = {}

        CTableModel.__init__(self, parent)

        self.addColumn(self.CInfoCol(u'Код карточки', 'evID', self.recordsById, 15))
        self.addColumn(self.CInfoCol(u'ФИО', 'fio', self.recordsById, 15))
        self.addColumn(self.CInfoCol(u'Дата рожд.', 'birthDate', self.recordsById, 15))
        self.addColumn(self.CInfoCol(u'Код отделения', 'MedSection_code', self.recordsById, 15))
        self.addColumn(self.CInfoCol(u'Поступил в МО', 'dateIn', self.recordsById, 15))
        self.addColumn(self.CInfoCol(u'Поступил в ОРиА', 'dateTrans', self.recordsById, 15))
        self.addColumn(self.CInfoCol(u'Проведенные исследования', 'diagnst_name', self.recordsById, 15))
        self.addColumn(self.CInfoCol(u'Состояние пациента', 'consist_name', self.recordsById, 15))
        self.addColumn(self.CErrorsCol(u'Ошибки', self.errorsById, 20))
        self.addColumn(self.CInfoCol(u'Ошибки экспорта', 'exporterror', self.recordsById, 20))
        self.loadField('id')
        self.setTable('Action')

    def setError(self, _id, error):
        if _id in self.errorsById:
            self.errorsById[_id].add(error)
        else:
            self.errorsById[_id] = set([error])

    def update(self):
        sql = u"""
        select 
            a.id id,
            e.id evID,
            c.lastName fam, 
            c.firstName ima, 
            c.patrName otch,
            CONCAT_WS(' ', c.lastName, c.firstName, c.patrName) fio, 
            c.birthDate birthDate,
            (case when LENGTH(formatClientAddress(ca.id))=0 then formatClientAddress(ca1.id) else formatClientAddress(ca.id) end) addr,
            a.MKB MKBX_code,
            a.MKB otd,
            sectinfo.value MedSection_code,
            IFNULL(dateInGet.dateIn, IFNULL(HospitalReceivedAction.begDate, a.begDate)) dateIn,
            a.begDate dateTrans,
            diagnst.diagnst_code diagnostics,
            diagnst.diagnst_name diagnst_name,
            cntc.consist_code constist_code,
            cntc.consist_name as consist_name,
            a.id IDr,
            (case when a.MKB is null or sectinfo.value is null or cntc.consist_code is null then 1 else 0 end) iserrorrecord,
            aee.note exporterror
        from Client c
            inner join Event e on e.client_id = c.id and e.deleted = 0 and e.execDate is null
            inner join `Action` a on a.event_id = e.id and a.deleted = 0 and a.status = 0 and a.endDate is null
            inner join ActionType actp on actp.id = a.actionType_id and actp.serviceType = 9 and actp.deleted = 0
            left join(
                select a.event_id, a.begDate dateIn
                from `Action` a
                inner join ActionType actp on actp.id = a.actionType_id and actp.flatCode = 'received' and actp.deleted = 0
            ) dateInGet on dateInGet.event_id = e.id
            inner join EventType et on et.id = e.eventType_id and et.deleted=0 and et.code not in('hospDir','egpuDisp','plng') and et.context not in('relatedAction','inspection')
            left join(
                select a.action_id, s.value consist_name, (case when s.value = 'удовлетворительное' then 1 when s.value = 'средней тяжести' then 2 when s.value = 'тяжелое' then 3 when s.value = 'крайне тяжелое' then 4 end) consist_code
                from ActionProperty as a
                inner join ActionPropertyType t on t.id = a.type_id and a.deleted = 0 and t.deleted = 0 and t.shortName='consist_code'
                inner join ActionProperty_String s on s.id = a.id
            ) cntc on cntc.action_id = a.id
            left join(
                select a.action_id, group_concat(case when t.shortName = 'diagnostics_operac' then 1 when t.shortName = 'diagnostics_KT' then 2 when t.shortName = 'diagnostics_MRT' 
                then 3 when t.shortName = 'diagnostics_Rg' then 4 when t.shortName = 'diagnostics_UZI' then 5 when t.shortName = 'diagnostics_EKG' then 6 end) diagnst_code,
                group_concat(case when t.shortName = 'diagnostics_operac' then 'операция' when t.shortName = 'diagnostics_KT' then 'кт' when t.shortName = 'diagnostics_MRT' 
                then 'мрт' when t.shortName = 'diagnostics_Rg' then 'рентген' when t.shortName = 'diagnostics_UZI' then 'узи' when t.shortName = 'diagnostics_EKG' then 'экг' end SEPARATOR ', ') diagnst_name
                from ActionProperty as a
                inner join ActionPropertyType t on t.id = a.type_id and a.deleted = 0 and t.deleted = 0 and t.shortName in ('diagnostics_operac', 'diagnostics_KT', 
                'diagnostics_MRT', 'diagnostics_Rg', 'diagnostics_UZI', 'diagnostics_EKG')
                inner join ActionProperty_String s on s.id = a.id
                where s.value = 'да'
                group by a.action_id
            ) diagnst on diagnst.action_id = a.id
            left join(
                SELECT osi.value, a.id
                FROM Action a
                INNER JOIN ActionType at ON a.actionType_id = at.id
                INNER JOIN ActionPropertyType apt ON at.id = apt.actionType_id AND apt.shortName='MedSection_code' AND apt.typeName='OrgStructure' 
                INNER JOIN ActionProperty ap ON a.id = ap.action_id AND ap.type_id=apt.id and ap.deleted = 0
                INNER JOIN ActionProperty_OrgStructure apos ON ap.id = apos.id
                INNER JOIN OrgStructure os ON apos.value = os.id
                INNER JOIN OrgStructure_Identification osi ON os.id = osi.master_id and osi.deleted=0
                INNER JOIN rbAccountingSystem asi ON osi.system_id = asi.id
                WHERE asi.code='sanAviaMedSection'
            )sectinfo on sectinfo.id = a.id
            left join ClientAddress ca on ca.client_id = c.id and ca.id = (select max(cal.id) from ClientAddress cal where cal.deleted=0 and cal.client_id = c.id and cal.deleted=0 and cal.`type`=0)
            left join ClientAddress ca1 on ca1.client_id = c.id and ca1.id = (select max(cal.id) from ClientAddress cal where cal.deleted=0 and cal.client_id = c.id and cal.deleted=0 and cal.`type`=1)
            LEFT JOIN Action AS HospitalReceivedAction ON HospitalReceivedAction.id = getPrevActionId(a.event_id, a.id, (select max(id) from ActionType where flatCode = 'received' and deleted = 0), a.begDate)
            left join Action_Export aee on aee.master_id = a.id and aee.id = (select max(Action_Export.id) from Action_Export where Action_Export.master_id = a.id)
        where
            IFNULL(aee.success,0)=0
        """
        self.fullIdList = []
        self.recordsById.clear()
        self.errorsById.clear()
        db = QtGui.qApp.db
        query = db.query(sql)

        while query.next():
            record = query.record()
            sanAviacId = forceRef(record.value('id'))
            self.fullIdList.append(sanAviacId)
            self.recordsById[sanAviacId] = record

            if forceString(record.value('MKBX_code')) == '':
                self.setError(sanAviacId, 1)
            if forceString(record.value('MedSection_code')) == '':
                self.setError(sanAviacId, 2)
            if forceString(record.value('constist_code')) == '':
                self.setError(sanAviacId, 3)

        self.updateIdList()

    def updateIdList(self):
        self.setIdList(self.fullIdList)
