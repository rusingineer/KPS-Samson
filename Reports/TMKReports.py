# -*- coding: utf-8 -*-

import json
import base64
import re

import requests
from datetime import datetime, timedelta

from PyQt4 import QtGui
from library.DialogBase import CDialogBase
from PyQt4.QtCore import Qt, pyqtSignature, QVariant
from library.Utils import setPref, getPref, forceString

from Ui_TMKInfo import Ui_tmkInfo
from Ui_TMKReports import Ui_tmkReports



class CTMKReports(CDialogBase, Ui_tmkReports):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.parent = parent
        self.setWindowTitle(u"ТМК-Отчет")
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)

        url = forceString(QtGui.qApp.db.translate('GlobalPreferences', 'code', 'TMKServiceUrl', 'value'))
        ip_address = re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', url)
        self.url = u"http://{0}/tm-shared/api".format(ip_address.group(0))
        self.header = {'Accept': 'application/fhir+json'}

        self.token = forceString(QtGui.qApp.db.translate('GlobalPreferences', 'code', 'TMKServiceToken', 'value'))
        self.userId = forceString(QtGui.qApp.db.translate('GlobalPreferences', 'code', 'TMKServiceUserId', 'value'))
        if not self.token or not self.userId or not self.url:
            QtGui.QMessageBox.information(
                self,
        u'Ошибка',
        u'Для работы сервиса, в настройках - предпочтениях - глобальные настройки, нужно указать Token и userID для сервиса ТМП',
                QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)
        if self.token and self.userId and self.url:
            self.sessionId = self.getSessionId(self.token, self.userId)

        self.tableName = []
        self.tableTitle = []
        self.tableData = []

        self.cmbFilterI._popupView._view.horizontalHeader().setDefaultSectionSize(20)

        self.tableWidget.setSortingEnabled(True)
        self.tableWidget.verticalHeader().hide()
        self.tableWidget.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)

        self.chkGetData.setChecked(True)

        self.chkBoxPreferences = QtGui.qApp.preferences.appPrefs

        self.listId = [
            '4e61e410-6de1-426f-ad3a-a0b1c6d10673',
            '07f1a6d2-f38f-4466-b166-9529da109ea6'
        ]

        self.listName = []
        self.listDescription = []

        for i in self.listId:
            r = requests.get(self.url + '/Reports/templates/' + i)

            jsonRequests = r.json()

            if 'data' in jsonRequests:
                data = jsonRequests['data']
                data = base64.b64decode(data)
                data = (data.decode('utf-8'))
                data = json.loads(data)

                self.listName.append(data['name'])
                if data['accessDescription']:
                    self.listDescription.append(data['accessDescription'])
                else:
                    self.listDescription.append(u'Его нет')

        self.cmbTemplatesId.setToolTip(u"Описание: {0}".format(self.listDescription[0]))
        self.cmbTemplatesId.addItems(self.listName)


    def getSessionId(self, token, userId):
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
        sessionId = jsonRequests['parameter'][0]['valueString']

        return sessionId


    def getReportData(self, sessionId, fileId):
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
            newTable = []

            json_list = data['template']['reportColumns']
            sortedJsonList = sorted(json_list, key=lambda x: (unicode(x['name'])))

            for i in sortedJsonList:
                self.tableName.append(i['name'])

                self.tableTitle.append(i['title'])
            self.tableData = data['table']

            fileId = self.cmbTemplatesId.currentIndex()

            idChk = forceString(getPref(self.chkBoxPreferences, 'chkBoxTMKTemplaceId-{0}'.format(self.listId[fileId]), ''))
            if idChk:
                idChk = idChk.split(',')
                idChk = [int(x) for x in idChk]

            if idChk:
                setPref(self.chkBoxPreferences, 'chkBoxTMKTemplaceId-{0}'.format(self.listId[fileId]), QVariant(','.join(str(el) for el in idChk)))

            self.cmbFilterI.clear()
            self.cmbFilterI.addItems(self.tableName)

            textChk = u""

            if idChk:
                self.cmbFilterI.setCheckedRows(idChk)

                for i in idChk:
                    textChk += self.tableName[i] + u"\n"

            self.cmbFilterI.setToolTip(textChk)

            for i in self.tableData:
                if self.filter(i):
                    newTable.append(i)

            self.upTable(newTable)
        else:
            QtGui.QMessageBox.warning(self,
                                      u'Внимание!',
                                      u'Данные о отчета по шаблону {0} не найденны'.format(fileId),
                                      QtGui.QMessageBox.Ok)


    def updateTable(self):
        newTable = []

        for i in self.tableData:
            if self.filter(i):
                newTable.append(i)

        self.tableWidget.clear()
        self.upTable(newTable)


    def upTable(self, newTable):
        hide = self.cmbFilterI.getCheckedRows()

        if hide:
            fileId = self.cmbTemplatesId.currentIndex()
            setPref(self.chkBoxPreferences, 'chkBoxTMKTemplaceId-{0}'.format(self.listId[fileId]), QVariant(','.join(str(el) for el in hide)))

        self.tableWidget.setRowCount(len(newTable))
        self.tableWidget.setColumnCount(int(len(self.tableName)))
        self.tableWidget.setHorizontalHeaderLabels(self.tableName)
        self.tableWidget.resizeColumnsToContents()

        for n, i in enumerate(newTable):
            for t in self.tableTitle:
                self.tableWidget.setItem(n, self.tableTitle.index(t), QtGui.QTableWidgetItem(self.getText(t, i)))


        for n, i in enumerate(newTable):
            self.tableWidget.showColumn(n)

        for i in hide:
            self.tableWidget.hideColumn(i)


    def filter(self, data):
        status = True

        createApplBegDate = self.edtCreateApplicationBegDate.dateTime().toString('yyyy-MM-ddTHH:mm:ss')
        createApplEndDate = self.edtCreateApplicationEndDate.dateTime().toString('yyyy-MM-ddTHH:mm:ss')

        create_time = data['create_time']

        if self.chkCreateApplicationBegDate.isChecked() or self.chkCreateApplicationEndDate.isChecked():
            if self.chkCreateApplicationBegDate.isChecked():
                if createApplBegDate <= create_time:
                    status = True
                else:
                    status = False

            if self.chkCreateApplicationEndDate.isChecked():
                if createApplEndDate >= create_time:
                    status = True
                else:
                    status = False

            if self.chkCreateApplicationBegDate.isChecked() and self.chkCreateApplicationEndDate.isChecked():
                if createApplBegDate <= create_time <= createApplEndDate:
                    status = True
                else:
                    status = False

        return status


    def getText(self, t, i):
        text = u"   "

        if t in i:
            text = i[t] if i[t] else u'   '
        elif 'nsi_code_{0}'.format(t) in i:
            text = i['nsi_code_{0}'.format(t)] if i['nsi_code_{0}'.format(t)] else u'   '

        if u'-' in text and u':' in text:
            if u'T' in text:
                try:
                    date_obj = datetime.strptime(text, '%Y-%m-%dT%H:%M:%S')
                    text = date_obj.strftime('%d.%m.%Y %H:%M')
                except:
                    pass

            elif u"+" in text:
                try:
                    td = text.split(u"+")
                    date_obj = datetime.strptime(td[0], '%Y-%m-%d %H:%M:%S')
                    text = date_obj.strftime('%d.%m.%Y %H:%M')
                    # text = text + u" +" + td[1]
                except:
                    pass

        if text == u"True":
            text = u"Да"
        elif text == u"False":
            text = u"Нет"

        return text


    @pyqtSignature('')
    def on_btnFilterApply_clicked(self):
        if not self.token or not self.userId:
            QtGui.QMessageBox.information(
                self,
        u'Ошибка',
        u'Для работы сервиса, в настройках - предпочтениях - глобальные настройки, нужно указать Token и userID для сервиса ТМП',
                QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)

        else:
            fileId = self.cmbTemplatesId.currentIndex()

            if self.chkGetData.isChecked():
                # 4e61e410-6de1-426f-ad3a-a0b1c6d10673
                # 07f1a6d2-f38f-4466-b166-9529da109ea6

                self.getReportData(self.sessionId, self.listId[fileId])
                self.chkGetData.setChecked(False)
            else:
                # Фильтруем существующие данные
                self.updateTable()


    @pyqtSignature('')
    def on_btnFilterReset_clicked(self):
        self.chkCreateApplicationBegDate.setChecked(False)
        self.chkCreateApplicationEndDate.setChecked(False)

        # Фильтруем существующие данные
        self.updateTable()


    @pyqtSignature('QModelIndex')
    def on_tableWidget_doubleClicked(self, index):
        row = index.row()
        col = index.column()
        data = []

        for i in range(0, len(self.tableName)):
            try:
                value = self.tableWidget.item(row, i).text()
                data.append(value)
            except:
                data.append(u'   ')

        ReportInfo(self, data, self.tableName).exec_()


    @pyqtSignature('int')
    def on_cmbTemplatesId_currentIndexChanged(self):
        fileId = self.cmbTemplatesId.currentIndex()
        self.cmbTemplatesId.setToolTip(u"Описание: {0}".format(self.listDescription[fileId]))
        self.chkGetData.setChecked(True)



class ReportInfo(QtGui.QDialog, Ui_tmkInfo):
    def __init__(self, parent, data, colName):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.setWindowTitle(u'Свойства записи 2')
        self.data = data
        self.colName = colName


    def exec_(self):
        text = u''

        for i in self.colName:
            text += u'{0}: {1}\n'.format(i, self.data[self.colName.index(i)])

        self.edtInfo.setText(text)
        return QtGui.QDialog.exec_(self)
