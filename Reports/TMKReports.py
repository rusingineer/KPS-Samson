# -*- coding: utf-8 -*-

import re
import json
import base64

import requests
from datetime import datetime

from PyQt4 import QtGui
from library.Utils import forceDate, forceDateTime
from Reports.Report import CReport, CVoidSetupDialog
from Reports.ReportBase import CReportBase, createTable
from library.DialogBase import CDialogBase
from PyQt4.QtCore import Qt, pyqtSignature, QVariant, QAbstractTableModel
from library.Utils import forceString

from Ui_TMKInfo import Ui_tmkInfo
from Ui_TMKReports import Ui_tmkReports


def columnValidator(colName, values):
    val = None

    if colName in values:
        val = values[colName] if values[colName] else None
    elif 'nsi_code_{0}'.format(colName) in values:
        val = values['nsi_code_{0}'.format(colName)] if values['nsi_code_{0}'.format(colName)] else None

    if val:
        val = val.replace("\n", "")

    if colName == u'col_hdlogrw6ik6jd1iy2ngmja':
        if values[u'status_name'] in (u'Заявка отменена/отклонена', u'Заключение готово'):
            val = values[u'update_time']
        else:
            pass

    if val == u"True":
        val = u"Да"
    elif val == u"False":
        val = u"Нет"

    if val:
        val = forceString(val)

    if val and colName in [u'col_hdlogrw6ik6jd1iy2ngmja', u'update_time', u'create_time', u'col_kz1npipauuoxfhwdzi43za']:
        val = val.split(u"+")[0]

    if val and colName == u'col_hdlogrw6ik6jd1iy2ngmja':
        try:
            date_obj = datetime.strptime(val, '%Y-%m-%dT%H:%M:%S')
            val = date_obj.strftime('%d.%m.%Y %H:%M')
        except:
            pass
    elif val and colName == u'update_time':
        date_obj = datetime.strptime(val, '%Y-%m-%dT%H:%M:%S')
        val = date_obj.strftime('%d.%m.%Y %H:%M')
    elif val and colName == u'create_time':
        date_obj = datetime.strptime(val, '%Y-%m-%dT%H:%M:%S')
        val = date_obj.strftime('%d.%m.%Y %H:%M')
    elif val and colName == u'col_kz1npipauuoxfhwdzi43za':
        date_obj = datetime.strptime(val, '%Y-%m-%d %H:%M:%S')
        val = date_obj.strftime('%d.%m.%Y')

    return val


class CTMKReports(CDialogBase, Ui_tmkReports):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.parent = parent
        self.setFilter = True
        self.setWindowTitle(u"ТМК-Отчет")
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)

        url = forceString(QtGui.qApp.db.translate('GlobalPreferences', 'code', 'TMKServiceUrl', 'value'))
        ip_address = re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', url)
        self.url = u"http://{0}/tm-shared/api".format(ip_address.group(0))
        self.header = {'Accept': 'application/fhir+json'}

        self.token = '770bb750-0ad8-44f6-81a0-80fa4b6abf34'
        self.userId = forceString(QtGui.qApp.db.translate('GlobalPreferences', 'code', 'TMKServiceUserId', 'value'))
        if not self.token or not self.userId or not self.url:
            QtGui.QMessageBox.information(
                self,
        u'Ошибка',
        u'Для работы сервиса, в настройках - предпочтениях - глобальные настройки, нужно указать userID для сервиса ТМК',
                QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)
        if self.token and self.userId and self.url:
            self.sessionId = self.getSessionId(self.token, self.userId)

        self.tableName = []
        self.tableTitle = []
        self.tableData = []
        self.listDescription = []

        self.chkGetData.setChecked(True)

        self.chkBoxPreferences = QtGui.qApp.preferences.appPrefs

        self.listId = [
            '4e61e410-6de1-426f-ad3a-a0b1c6d10673'
        ]

        if self.sessionId is None:
            self.btnFilterApply.setEnabled(False)
            self.btnPrint.setEnabled(False)
            QtGui.QMessageBox.information(
                self,
                u'Ошибка',
                u'Пользователь c TMKServiceUserId = {0} не найден, уточните актуальность идентификатора пользователя для сервиса отчетов ТМК в миац'.format(self.userId),
                QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)
        else:
            self.setCmbTemplates()

        self.lblTemplatesId.setVisible(False)
        self.cmbTemplatesId.setVisible(False)

        self.addModels('Report', CTMKReportModel(self))
        self.setModels(self.tblReport, self.modelReport, self.selectionModelReport)
        self.tblReport.setSortingEnabled(True)

        self.tblReport.enableColsHide()
        self.tblReport.enableColsMove()

        self.cmbStatusName._popupView.lblFilterCode.setText(u'Наименование')
        self.cmbStatusName._popupView.lblFilterName.setVisible(False)
        self.cmbStatusName._popupView.edtFilterName.setVisible(False)

        self.cmbOrganisation._popupView.lblFilterCode.setText(u'Наименование')
        self.cmbOrganisation._popupView.lblFilterName.setVisible(False)
        self.cmbOrganisation._popupView.edtFilterName.setVisible(False)

        self.btnFilterApply.setFocus()

    def setCmbTemplates(self):
        """Устанавливаем названия доступных отчетов в комбобокс"""
        listName = []

        for i in self.listId:
            r = requests.get(self.url + '/Reports/templates/' + i)

            jsonRequests = r.json()

            if 'data' in jsonRequests:
                data = jsonRequests['data']
                data = base64.b64decode(data)
                data = (data.decode('utf-8'))
                data = json.loads(data)

                listName.append(data['name'])
                if data['accessDescription']:
                    self.listDescription.append(data['accessDescription'])
                else:
                    self.listDescription.append(u'Отчет без описания.')

        self.setDescription(self.listDescription[0])

        self.cmbTemplatesId.addItems(listName)

    def getSessionId(self, token, userId):
        """Авторизовываемся"""
        sessionId = None
        authHeaders = {
            'Content-type': 'application/fhir+json',
            'Accept': 'application/fhir+json',
            'Authorization': token
        }

        authData = {
            'resourceType': 'Parameters',
            'parameter': [{
                'name': 'userId',
                'valueString': userId
            }]
        }

        r = requests.post(
            url=self.url + '/Authorization/sign-in',
            headers=authHeaders,
            data=json.dumps(authData)
        )

        jsonRequests = r.json()
        status = jsonRequests.get('parameter', None)
        if status:
            sessionId = jsonRequests['parameter'][0]['valueString']
        else:
            sessionId = None

        return sessionId

    def getReportData(self, sessionId, fileId):
        """ Запрашиваем ТМК отчет по выбранному из self.listId """
        self.tableName = []
        self.tableTitle = []
        self.tableData = []
        self.listDescription = []

        getReportDataHeaders = {
        'Content-type': 'application/fhir+json',
        'Accept': 'application/fhir+json',
        'Authorization': sessionId
        }

        def getCount():
            getReportDataData = {
                "resourceType": "Parameters",
                "parameter": [
                    {
                        "name": "take",
                        "valuePositiveInt": 0
                    }
                ]}

            r = requests.post(
                url=self.url + '/Reports/getReportData/' + fileId,
                headers=getReportDataHeaders,
                data=json.dumps(getReportDataData)
            )

            jsonRequests = r.json()

            data = jsonRequests['data']
            data = base64.b64decode(data)
            data = json.loads(data)

            return int(data['count'])

        # Указываем количество записей
        getReportDataData = {
            "resourceType": "Parameters",
            "parameter": [
                {
                    "name": "take",
                    "valuePositiveInt": getCount()  # 10
                }
            ]}

        r = requests.post(
            url=self.url + '/Reports/getReportData/' + fileId,
            headers=getReportDataHeaders,
            data=json.dumps(getReportDataData)
        )

        jsonRequests = r.json()

        if 'data' in jsonRequests:
            data = jsonRequests['data']
            data = base64.b64decode(data)
            data = (data.decode('utf-8'))

            data = json.loads(data)
            self.tableName = []
            self.tableTitle = []

            json_list = data['template']['reportColumns']
            sortedJsonList = sorted(json_list, key=lambda x: (unicode(x['name'])))

            renameClmn = {
                u'status_name': u'Статус заявки'
            }

            for i in sortedJsonList:
                if i['title'] in renameClmn:
                    self.tableName.append(renameClmn[i['title']])
                else:
                    self.tableName.append(u"{0}".format(i['name']))

                self.tableTitle.append(i['title'])

            self.tableData = []
            for val in data['table']:
                row = []
                for idx, colName in enumerate(self.tableTitle):
                    row.append(columnValidator(colName, val))
                self.tableData.append(row)

            self.setValuesCmb(self.tableData)
            self.setLenRecord(len(self.tableData))
            if self.setFilter:
                self.setFilterParametrs()
                self.setFilter = False
            self.modelReport.setHeader(self.tableName)
            self.modelReport.setHeaderEn(self.tableTitle)
            self.modelReport.setItems(self.tableData)
            self.tblReport.resizeColumnsToContents()
            self.tblReport.horizontalHeader().setStretchLastSection(True)

        else:
            QtGui.QMessageBox.warning(self,
                                      u'Внимание!',
                                      u'Данные о отчета по шаблону {0} не найденны'.format(fileId),
                                      QtGui.QMessageBox.Ok)

    def setLenRecord(self, num):
        self.lblNumRec.setText(u'Всего записей: {0}'.format(num))

    def setDescription(self, description):
        self.cmbTemplatesId.setToolTip(u"Описание: {0}".format(description))

    def setValuesCmb(self, values):
        # Читаем наименования статусов и загоням в мульти комбо бокс или обычный.
        cmbStatus = []
        cmbOrganisation = []

        for val in values:
            if val[self.tableTitle.index('col_pkm3viuqkam8fvren9ska')] not in cmbOrganisation:
                cmbOrganisation.append(val[self.tableTitle.index('col_pkm3viuqkam8fvren9ska')])

            if val[self.tableTitle.index('status_name')] not in cmbStatus:
                cmbStatus.append(val[self.tableTitle.index('status_name')])

        for val in cmbStatus:
            self.cmbStatusName.addItem(val)

        for val in cmbOrganisation:
            self.cmbOrganisation.addItem(val)

    def setFilterParametrs(self):
        maxDate = None
        minDate = None

        idxDate = self.tableTitle.index(u'create_time')

        for values in self.tableData:
            parmDate = forceDate(datetime.strptime(values[idxDate], '%d.%m.%Y %H:%M'))

            if maxDate is None:
                maxDate = parmDate

            if parmDate > maxDate:
                maxDate = parmDate

            if minDate != None:
                if parmDate < minDate:
                    minDate = parmDate
            else:
                minDate = parmDate

        self.edtBegDate.setMaximumDate(maxDate)
        self.edtBegDate.setMinimumDate(minDate)

        self.edtEndDate.setMaximumDate(maxDate)
        self.edtEndDate.setMinimumDate(minDate)

        self.edtBegDate.setDate(minDate)
        self.edtEndDate.setDate(maxDate)

    @pyqtSignature('')
    def on_btnFilterApply_clicked(self):
        if not self.token or not self.userId:
            QtGui.QMessageBox.information(
                self,
        u'Ошибка',
        u'Для работы сервиса, в настройках - предпочтениях - глобальные настройки, нужно указать userID для сервиса ТМК',
                QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)

        else:
            fileId = self.cmbTemplatesId.currentIndex()
            if self.chkGetData.isChecked():
                self.getReportData(self.sessionId, self.listId[fileId])
                self.chkGetData.setChecked(False)

            reportFilter = {}
            if self.chkBegDate.isChecked():
                begDate = self.edtBegDate.date()
                reportFilter['begDate'] = ['create_time', begDate]
            if self.chkEndDate.isChecked():
                endDate = self.edtEndDate.date()
                reportFilter['endDate'] = ['create_time', endDate]

            directions = self.cmbDirections.currentIndex()
            reportFilter['directions'] = ['col_odvlnsmwikqcp4dxsmoq', directions]

            statusName = self.cmbStatusName.value()
            splStatName = statusName.replace(u'‚ ', u'‚').split(u'‚')
            if splStatName != [u'']:
                reportFilter['statusName'] = ['status_name', splStatName]

            organisation = self.cmbOrganisation.value()
            splOrg = organisation.replace(u'‚ ', u'‚').split(u'‚')
            if splOrg != [u'']:
                reportFilter['organisation'] = ['col_pkm3viuqkam8fvren9ska', splOrg]

            self.modelReport.filter(reportFilter)
            self.setLenRecord(self.modelReport.getLen())

    @pyqtSignature('')
    def on_btnFilterReset_clicked(self):
        self.chkBegDate.setChecked(False)
        self.chkEndDate.setChecked(False)
        self.cmbDirections.setCurrentIndex(0)
        self.modelReport.filter()

    @pyqtSignature('')
    def on_btnPrint_clicked(self):
        clmnHide = []
        for column in range(self.tblReport.model().columnCount()):
            if self.tblReport.isColumnHidden(column):
                clmnHide.append(column)

        reportHeader = []
        for idx, val in enumerate(self.modelReport.getHeader()):
            if idx not in clmnHide:
                reportHeader.append(val)

        reportItems = []
        for value in self.modelReport.getItems():
            itms = []
            for idx, val in enumerate(value):
                if idx not in clmnHide:
                    itms.append(val)
            reportItems.append(itms)

        CReportTMKReports(self, reportHeader, reportItems).exec_()

    @pyqtSignature('QModelIndex')
    def on_tblReport_doubleClicked(self, index):
        row = index.row()
        data = []

        for i in range(0, len(self.tableName)):
            value = self.modelReport.item(row, i)
            data.append(value)

        ReportInfo(self, data, self.tableName).exec_()

    @pyqtSignature('int')
    def on_cmbTemplatesId_currentIndexChanged(self):
        fileId = self.cmbTemplatesId.currentIndex()
        self.setDescription(self.listDescription[fileId])
        self.chkGetData.setChecked(True)


class ReportInfo(QtGui.QDialog, Ui_tmkInfo):
    def __init__(self, parent, data, colName):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.setWindowTitle(u'Свойства записи')
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.data = data
        self.colName = colName

    def exec_(self):
        text = u''

        for colName in self.colName:
            text += u'{0}: {1}\n'.format(
                colName,
                self.data[self.colName.index(colName)])

        self.edtInfo.setText(text)
        return QtGui.QDialog.exec_(self)


class Col(object):
    def __init__(self, title):
        self._title = QVariant(title)
        self._switchOff = True

    def switchOff(self):
        return self._switchOff

    def title(self):
        return self._title


class CTMKReportModel(QAbstractTableModel):
    def __init__(self, parent):
        QAbstractTableModel.__init__(self, parent)
        self._items = []
        self.items = []
        self._cols = []
        self.header = []
        self.headerEn = []

    def columnCount(self, index = None):
        return len(self.header)

    def rowCount(self, index = None):
        return len(self.items)

    def flags(self, index):
        return Qt.ItemIsSelectable|Qt.ItemIsEnabled

    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return QVariant(self.header[section])
        return QVariant()

    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if role == Qt.DisplayRole:
            item = self.items[row]
            return QVariant(item[column])
        return QVariant()

    def loadData(self, items):
        self.items = items
        self.reset()

    def setHeader(self, header):
        self._cols = []
        self.header = header
        for clmnTitle in header:
            self._cols.append(Col(clmnTitle))
        self.reset()

    def setHeaderEn(self, header):
        self.headerEn = header

    def setItems(self, items):
        self._items = items
        self.loadData(items)

    def cols(self):
        return self._cols

    def getHeader(self):
        return self.header

    def getItems(self):
        return self.items

    def item(self, row, column):
        return self.items[row][column]

    def getLen(self):
        return len(self.items)

    def filter(self, filters=None):
        if filters:
            filterIterms = []

            for values in self._items:
                status = True
                if 'begDate' in filters and status:
                    idx = self.headerEn.index(filters['begDate'][0])
                    begDate = forceDate(datetime.strptime(values[idx], "%d.%m.%Y %H:%M"))
                    if begDate < filters['begDate'][1]:
                        status = False

                if 'endDate' in filters and status:
                    idx = self.headerEn.index(filters['endDate'][0])
                    begDate = forceDate(datetime.strptime(values[idx], "%d.%m.%Y %H:%M"))
                    if begDate > filters['endDate'][1]:
                        status = False

                if 'directions' in filters and status:
                    idx = self.headerEn.index(filters['directions'][0])
                    lpuFullName = forceString(QtGui.qApp.db.translate('Organisation', 'id', QtGui.qApp.currentOrgId(), 'fullName')).upper()
                    if filters['directions'][1] == 0:
                        pass
                    elif filters['directions'][1] == 1:
                        if lpuFullName == values[idx].replace('. ', '.'):
                            status = False
                    elif filters['directions'][1] == 2:
                        if lpuFullName != values[idx].replace('. ', '.'):
                            status = False

                if 'statusName' in filters and status:
                    if filters['statusName'][1]:
                        idx = self.headerEn.index(filters['statusName'][0])
                        if values[idx] not in filters['statusName'][1]:
                            status = False

                if 'organisation' in filters and status:
                    if filters['organisation'][1]:
                        idx = self.headerEn.index(filters['organisation'][0])
                        if values[idx] not in filters['organisation'][1]:
                            status = False

                if status:
                    filterIterms.append(values)

            self.loadData(filterIterms)
        else:
            self.loadData(self._items)

    def sort(self, column, order=Qt.AscendingOrder):
        # TODO Добавь логику сортировки в зависимости от типа колонки
        reverse = order == Qt.DescendingOrder
        if column in (0, 1, 2):
            self.items.sort(key=lambda x: forceDateTime(datetime.strptime(x[column], '%d.%m.%Y %H:%M')) if x and x[column] else None, reverse=reverse)
        elif column == 3:
            self.items.sort(key=lambda x: forceDate(datetime.strptime(x[column], '%d.%m.%Y')) if x else None, reverse=reverse)
        else:
            self.items.sort(key=lambda x: forceString(x[column]).lower() if x else None, reverse=reverse)
        self.reset()


class CReportTMKReports(CReport):
    def __init__(self, parent, header, items):
        CReport.__init__(self, parent)
        self.setTitle(u'Печать отчета')
        self.header = header
        self.items = items

    def getSetupDialog(self, parent):
        return CVoidSetupDialog(parent)

    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Печать отчета')
        cursor.insertBlock()

        tableColumns = []

        width = str(int(100 / len(self.header)))
        for head in self.header:
            tableColumns.append(('{0}%'.format(width), [u'{0}'.format(head)], CReportBase.AlignLeft))

        table = createTable(cursor, tableColumns)

        for values in self.items:
            row = table.addRow()
            for idx, val in enumerate(values):
                table.setText(row, idx, forceString(val))

        return doc
