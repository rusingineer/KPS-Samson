# -*- coding: utf-8 -*-

from PyQt4 import QtGui
from PyQt4.QtGui import QDialog
from PyQt4 import QtCore
from library.Utils import forceString, forceDate, forceInt, formatSex, forceDateTime, getPrefDate, getPref
from Reports.Utils import dateRangeAsStr
from Reports.Report import CReport
from Reports.ReportBase import CReportBase, createTable
from Ui_ActDeattachCheckSetupDialog import Ui_ActDeattachCheckSetupDialog

def getQuery(begDate, endDate, actType, orgStructureIdList):
    orgStructureIdListString = None
    if len(orgStructureIdList) > 0:
        orgStructureIdListString = u','.join([ forceString(el) for el in orgStructureIdList])

    if actType == 1:
        stmt = u"""
            select
                ce.master_id as clientid,
                concat_ws(' ', Client.lastName, Client.firstName, Client.patrName) as fio,
                Client.sex as sex,
                Client.birthDate as birthDate,
                coalesce(
                    (select concat_ws(' ',Organisation.infisCode, Organisation.shortName) from Organisation where Organisation.infisCode = ce.note order by id desc limit 1),
                    ce.note) as org,
                ce.dateTime as date,
                coalesce((select code from OrgStructure where  OrgStructure.id = ca.orgStructure_id), null) as uchastok
            from Client_Export ce
            left join Client on Client.id = ce.master_id
            left join ClientAttach ca on ca.client_id = Client.id and ca.deleted = 0  and ca.endDate is NULL
            where date(ce.dateTime) between '%s' and '%s' and ce.system_id = 10 and ce.success = 1
            and ce.note not in (select bookkeeperCode from OrgStructure where deleted = 0)
        """
        if orgStructureIdListString:
            stmt += u"  and ca.orgStructure_id in (" + orgStructureIdListString + u") "
        stmt += u" order by ce.dateTime desc "
    else:
        stmt = u"""
            select
                concat_ws(' ', sa.lastName, sa.firstName, sa.patrName) as fio,
                case
                    when sa.sex like 'Ж' then 2
                    when sa.sex like 'М' then 1
                    else null end as sex,
                date(sa.birthDate) as birthDate,
                coalesce(
                    (select concat_ws(' ',Organisation.infisCode, Organisation.shortName) from Organisation where Organisation.infisCode = sa.attach_mo order by id desc limit 1),
                     sa.attach_mo) as org,
                sa.createDate as date,
                sa.attach_area as uchastok,
              sa.client_id as clientid
             from soc_attachments sa

            where date(sa.createDate) between '%s' and '%s' and  sa.serviceMethod = 3
        
            """
        if orgStructureIdListString:
            stmt += u"""  and exists(select 1 from OrgStructure os where os.id in (""" + orgStructureIdListString + u""") and sa.attach_area = os.code and os.areaType > 0 and os.deleted = 0) """
        stmt +=  u" order by sa.lastName asc, sa.firstName asc, sa.patrName asc "
    stmt = stmt % (
        forceString(begDate.toString("yyyy-MM-dd")),
        forceString(endDate.toString("yyyy-MM-dd"))
    )
    return QtGui.qApp.db.query(stmt)


class CActDeattachCheckSetupDialog(QDialog, Ui_ActDeattachCheckSetupDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)

    def params(self):
        result = {}
        result['begDate'] = self.edtBegDate.date()
        result['endDate'] = self.edtEndDate.date()
        result['actType'] = 1 if self.rbActType1.isChecked() else 2
        result['orgStructure_id'] = self.cmbOrgStructure.value()
        return result


    def setParams(self, params):
        today = QtCore.QDate.currentDate()
        self.edtBegDate.setDate(params.get('begDate', today))
        self.edtEndDate.setDate(params.get('endDate', today))
        self.cmbOrgStructure.setValue(params.get('orgStructure_id', None))
        if params.get('actType', 1) == 1:
            self.rbActType1.setChecked(True)
        else:
            self.rbActType2.setChecked(True)

    def setTitle(self, title):
        self.setWindowTitle(title)


class CActDeattachCheckReport(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Журнал обмена уведомлениями с другими медицинским организациями о прикреплении граждан')

    def getDefaultParams(self):
        result = {}
        today = QtCore.QDate.currentDate()
        prefs = getPref(QtGui.qApp.preferences.reportPrefs, self.title(), {})
        result['begDate'] = getPrefDate(prefs, 'begDate', today)
        result['endDate'] = getPrefDate(prefs, 'endDate', today)
        result['actType'] = 1
        result['orgStructure_id'] = getPref(prefs, 'orgStructure_id', None)
        return result

    def getSetupDialog(self, parent):
        result = CActDeattachCheckSetupDialog(parent)
        result.setTitle(self.title())
        return result

    def getDescription(self, params):
        begDate = params.get('begDate', QtCore.QDate())
        endDate = params.get('endDate', QtCore.QDate())
        actType = params.get('actType', 1)
        rows = []
        rows.append(dateRangeAsStr(u'за период', begDate, endDate))
        if actType == 1:
            rows.append(u'по отправленным уведомлениями')
        else:
            rows.append(u'по полученным уведомлениями')
        rows.append(u'отчёт составлен: ' + forceString(QtCore.QDateTime.currentDateTime()))
        return rows

    def dumpParams(self, cursor, params):
        description = self.getDescription(params)
        columns = [ ('100%', [], CReportBase.AlignLeft) ]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertHtml('<br/><br/>')

    def build(self, params):
        actType = params.get("actType", 1)
        orgStructureId = params.get("orgStructure_id", None)

        resultListOrgStructure = []
        if orgStructureId:
            listOfOrgStructuresUchRecord = QtGui.qApp.db.getRecordList(u"OrgStructure", u'id',
                                                                       u' OrgStructure.areaType > 0 and OrgStructure.deleted = 0')
            listOfOrgStructuresUch = []
            for recordUch in listOfOrgStructuresUchRecord:
                listOfOrgStructuresUch.append(forceInt(recordUch.value('id')))
            tempRecOrgStructure = QtGui.qApp.db.getDescendants('OrgStructure', 'parent_id', orgStructureId, u'OrgStructure.areaType > 0 and OrgStructure.deleted = 0 ')
            for tempRec in tempRecOrgStructure:
                if forceInt(tempRec) in listOfOrgStructuresUch:
                    resultListOrgStructure.append(forceInt(tempRec))
        query = getQuery(
            params.get("begDate",QtCore.QDate.currentDate()),
            params.get("endDate",QtCore.QDate.currentDate()),
            actType,
            resultListOrgStructure
        )
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Журнал обмена уведомлениями с другими медицинским организациями о прикреплении граждан')
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertHtml('<br/><br/>')
        self.dumpParams(cursor, params)
        if actType == 1:
            tableColumns = [
                ('10%',  [u'№ п/п'], CReportBase.AlignLeft),
                ('10%', [u'Код'], CReportBase.AlignLeft),
                ('20%', [u'ФИО пациента'], CReportBase.AlignLeft),
                ('5%',  [u'Пол'], CReportBase.AlignLeft),
                ('10%', [u'Дата рождения'], CReportBase.AlignLeft),
                ('30%', [u'Сведения отправлены в'], CReportBase.AlignLeft),
                ('15%', [u'Запрос отправлен'], CReportBase.AlignLeft),
            ]
        else:
            tableColumns = [
                ('10%',  [u'№ п/п'], CReportBase.AlignLeft),
                ('30%', [u'ФИО пациента'], CReportBase.AlignLeft),
                ('10%', [u'Дата рождения'], CReportBase.AlignLeft),
                ('35%', [u'МО-отправитель уведомления'], CReportBase.AlignLeft),
                ('15%', [u'Запрос получен'], CReportBase.AlignLeft),
            ]

        table = createTable(cursor, tableColumns)

        rowNumber = 0
        dictOfRecords = {}
        while query.next():
            record = query.record()
            orgStructure = forceString(record.value('uchastok'))
            if orgStructure not in dictOfRecords.keys():
                dictOfRecords[orgStructure] = []
            dictOfRecords[orgStructure].append(record)

        dictKeys = dictOfRecords.keys()
        dictKeys = sorted(dictKeys, key=lambda x: (not x, x))
        for key in dictKeys:
            orgStructureName = u"Без участка"
            if key and key not in (u'', u'0'):
                orgStructureSql = u"Select name from OrgStructure where code in ('%s') and deleted = 0 " % (key)
                orgStructureQuery = QtGui.qApp.db.query(orgStructureSql)
                if orgStructureQuery.next():
                    orgStructureName = forceString(orgStructureQuery.record().value('name'))

            rowHeader = table.addRow()
            table.mergeCells(rowHeader, 0, 1, len(tableColumns))
            table.setText(rowHeader, 0, orgStructureName)
            for elem in dictOfRecords[key]:
                rowNumber += 1
                row = table.addRow()

                colFio = forceString(elem.value('fio'))
                columns = [rowNumber,
                           colFio,
                       '' if elem.isNull('birthDate') else forceDate(elem.value('birthDate')).toString(
                           'dd.MM.yyyy'),
                       forceString(elem.value('org')),
                       '' if elem.isNull('date') else forceDateTime(elem.value('date')).toString(
                           'dd.MM.yyyy hh:mm:ss')]
                if actType == 1:
                    colClientId = forceString(elem.value('clientid'))
                    if forceString(elem.value('clientid')) and forceString(elem.value('clientid')) != u"":
                        colClientId = u'''<a style="color:#000000;" href="karta_''' + forceString(
                            elem.value('clientid')) + u'">' + forceString(elem.value('clientid')) + u"</a>"
                    columns.insert(1, colClientId)  # поле код для первого акта
                    columns.insert(3, formatSex(forceInt(elem.value('sex'))))  # поле пол для первого акта

                colChangeMethod = 1
                for idx, val in enumerate(columns):
                    if idx == colChangeMethod and actType == 1:
                        table.setHtml(row, idx, val)
                    else:
                        table.setText(row, idx, val)

        return doc
