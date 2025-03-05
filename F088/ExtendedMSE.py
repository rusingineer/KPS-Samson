# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2024 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
import datetime
import json
import urlparse

import requests
from PyQt4 import QtGui, QtSql, QtCore
from PyQt4.QtCore import QVariant, QUrl, QDateTime, Qt, QDate

from F088.Ui_ExtendedMSE import Ui_ExtendedMSEWidget
from F088.Ui_ExtendedMSEServiceDialog import Ui_ExtendedMSEServiceDialog
from library.DialogBase import CConstructHelperMixin, CDialogBase
from library.InDocTable import CRecordListModel, CInDocTableCol, CBoolInDocTableCol
from library.Utils import forceString, forceDateTime, forceDate, toVariant, forceBool, formatDateTime, forceInt


class CExtendedMSEWidget(QtGui.QWidget, CConstructHelperMixin, Ui_ExtendedMSEWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)
        self.addModels('ExtendedMSE',    CExtendedMSEModel(self))
        self.setModels(self.tblExtendedMSE, self.modelExtendedMSE, self.selectionModelExtendedMSE)
        self.tblExtendedMSE.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.btnRequest.clicked.connect(self.sendRequest)
        self.edtBegDate.setDate(QDate.currentDate().addMonths(-1))
        self.edtEndDate.setDate(QDate.currentDate())
        self.servicesURL = forceString(QtGui.qApp.getGlobalPreference('23:servicesURL'))
        if self.servicesURL:
            self.servicesURL = self.servicesURL.replace('\\\\', '//')
            self.servicesURL = urlparse.urljoin(self.servicesURL, '/api/local/services/ExtendedMSE/')
        self.clientId = None
        self.lpuGuid = None
        self.actionId = None

    def setClientInfo(self, clientInfo):
        if clientInfo:
            self.clientId = clientInfo['clientId']
            self.lpuGuid = clientInfo['lpuGuid']
            self.actionId = clientInfo['actionId']
            model = self.tblExtendedMSE.model()
            model.loadData(self.actionId)


    def sendRequest(self):
        db = QtGui.qApp.db
        if QtGui.QMessageBox().question(self, u'Внимание!',
                                        u'Получить информацию по запросу\n'
                                        u'в Web-сервере "Расширенное направление на МСЭ"?',
                                        QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                        QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
            begDate = self.formatDate(self.edtBegDate.date())
            endDate = self.formatDate(self.edtEndDate.date().addDays(1))
            dbName = QtGui.qApp.preferences.dbDatabaseName
            patientId = forceString(self.clientId)
            if dbName in ('s11_01527', 's11_17020', 's11_11007', 's11_15001', 's11_13516', 's11_11031'):
                patientId = '{0}_'.format(patientId)
            params = {
                    "patientID": patientId,
                    "lpuID": self.lpuGuid,
                    "startDateRange": begDate,
                    "endDateRange": endDate
                     }

            if self.testRequest(params):
                dialog = CExtendedMSEService(self, params, self.actionId)
                dialog.exec_()
                if dialog.execResult == 1:
                    records = dialog.getRecords()
                    if records:
                        self.setDataFromRequest(records)

    def testRequest(self, params):
        if self.servicesURL and params:
            try:
                response = requests.post(self.servicesURL + 'documents', json=params)
                jsonData = response.json()
                if response.status_code == 200:
                    if forceBool(jsonData['Data']):
                        message = forceString(jsonData['Description'])
                        QtGui.QMessageBox().information(self, u'Информация', message, QtGui.QMessageBox.Close)
                        return True
                    else:
                        message = forceString(jsonData['Description'])
                        QtGui.QMessageBox().information(self, u'Информация', message, QtGui.QMessageBox.Close)
                        return None
                elif response.status_code >= 400:
                    message = forceString(jsonData['detail'])
                    QtGui.QMessageBox().critical(self, u'Ошибка', u'Произошла ошибка:\n' + message, QtGui.QMessageBox.Close)
                    return None
                else:
                    return None
            except Exception, e:
                return None

    def formatDate(self, val):
        return str(val.toString(Qt.ISODate))

    def setDataFromRequest(self, records):
        model = self.tblExtendedMSE.model()
        items = model.items()
        allList = []
        documentIdList = []
        for item in items:
            if forceBool(item):
                sourceId = forceString(item.value('source_id'))
                documentIdList.append(sourceId)
                allList.append(item)
        for record in records:
            if forceBool(record):
                if forceString(record.value('source_id')) not in documentIdList:
                    allList.append(record)
        model.setItems(allList)

    def saveData(self):
        model = self.tblExtendedMSE.model()
        items = model.items()

        for item in items:
            db = QtGui.qApp.db
            if not forceBool(item.value('id')):
                tableExtendedMSE = db.table('soc_ExtendedMSE')
                record = tableExtendedMSE.newRecord()
                record.setValue('createDatetime', toVariant(QDateTime.currentDateTime()))
                record.setValue('createPerson_id', forceString(QtGui.qApp.userId))
                record.setValue('deleted', 0)
                record.setValue('action_id', item.value('action_id'))
                record.setValue('documentCreationDate', forceDateTime(item.value('documentCreationDate')))
                record.setValue('orgGUID', item.value('orgGUID'))
                record.setValue('orgName', item.value('orgName'))
                record.setValue('documentType', item.value('documentType'))
                record.setValue('name', item.value('name'))
                record.setValue('source_id', item.value('source_id'))
                record.setValue('regDate', forceDateTime(item.value('regDate')))
                record.setValue('reg_id', item.value('reg_id'))
                db.insertOrUpdate(tableExtendedMSE, record)
            elif forceInt(item.value('deleted')):
                tableExtendedMSE = db.table('soc_ExtendedMSE')
                db.updateRecord(tableExtendedMSE, item)
        model.loadData(self.actionId)


    def contextMenuEvent(self, event):
        model = self.tblExtendedMSE.model()
        self.menu = QtGui.QMenu(self)
        rows = self.tblExtendedMSE.selectedRowList()
        if len(rows):
            openFile = QtGui.QAction(u'Просмотр', self)
            openFile.triggered.connect(self.openFile)
            self.menu.addAction(openFile)
            cancelDelete = None
            deleteFile = None
            for row in rows:
                deleted = forceInt(model.value(row, 'deleted'))
                if deleted:
                    cancelDelete = QtGui.QAction(u'Отменить открепление', self)
                    cancelDelete.triggered.connect(self.cancelDeleteFile)
                else:
                    deleteFile = QtGui.QAction(u'Открепить', self)
                    deleteFile.triggered.connect(self.deleteFile)
            if cancelDelete:
                self.menu.addAction(cancelDelete)
            if deleteFile:
                self.menu.addAction(deleteFile)
            self.menu.popup(QtGui.QCursor.pos())

    def openFile(self):
        model = self.tblExtendedMSE.model()
        for row in self.tblExtendedMSE.selectedRowList():
            docType = forceString(model.value(row, 'documentType'))
            docId = forceString(model.value(row, 'source_id'))
            if docType and docId:
                path = self.servicesURL + 'documents/{0}/{1}'.format(docType, docId)
                url = unicode(path)
                QtGui.QDesktopServices.openUrl(QUrl.fromEncoded(url))

    def deleteFile(self):
        model = self.tblExtendedMSE.model()
        for row in self.tblExtendedMSE.selectedRowList():
            _id = forceString(model.value(row, 'id'))
            if _id:
                model.setValue(row, 'deleted', 1)
            else:
                model.removeRows(row, 1)

    def cancelDeleteFile(self):
        model = self.tblExtendedMSE.model()
        for row in self.tblExtendedMSE.selectedRowList():
            _id = forceString(model.value(row, 'id'))
            if _id:
                model.setValue(row, 'deleted', 0)
            else:
                model.removeRows(row, 1)


class CExtendedMSEService(CDialogBase, Ui_ExtendedMSEServiceDialog):
    def __init__(self, parent, params, actionId=None):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.addModels('ExtendedMSEService',    CExtendedMSEServiceModel(self))
        self.setModels(self.tblExtendedMSEService, self.modelExtendedMSEService, self.selectionModelExtendedMSEService)
        self.btnSaveSelected.clicked.connect(self.saveSelected)
        self.servicesURL = forceString(QtGui.qApp.getGlobalPreference('23:servicesURL'))
        if self.servicesURL:
            self.servicesURL = self.servicesURL.replace('\\\\', '//')
            self.servicesURL = urlparse.urljoin(self.servicesURL, '/api/local/services/ExtendedMSE/')
        self.actionId = actionId
        self.execResult = 0
        self.records = []
        self.loadData(params)

    def saveSelected(self):
        model = self.tblExtendedMSEService.model()
        itemList = model.items()
        records = []
        for item in itemList:
            if forceBool(item.value('needSave')):
                records.append(item)
        self.records = records
        self.execResult = 1
        self.close()

    def getRecords(self):
        return self.records

    def loadData(self, params):
        jsonData = self.getDataFromService(params)
        if forceBool(jsonData['Data']):
            records = []
            model = self.tblExtendedMSEService.model()
            for data in jsonData['Data']:
                record = self.getEmptyRecord(model)
                docCreateDatetime = forceString(data['CreationDate'])
                docCreateDatetime = QDateTime.fromString(docCreateDatetime, Qt.ISODate)
                regDatetime = forceString(data['RegDate'])
                regDatetime = QDateTime.fromString(regDatetime, Qt.ISODate)
                record.setValue('createDatetime', toVariant(QDateTime.currentDateTime()))
                record.setValue('createPerson_id', forceString(QtGui.qApp.userId))
                record.setValue('deleted', 0)
                record.setValue('action_id', forceString(self.actionId))
                record.setValue('documentCreationDate', toVariant(docCreateDatetime))
                record.setValue('orgGUID', forceString(data['Organization']) if 'Organization' in data else '')
                record.setValue('orgName', forceString(data['OrganizationName']) if 'OrganizationName' in data else '')
                record.setValue('documentType', forceString(data['MedDocumentType']) if 'MedDocumentType' in data else '')
                record.setValue('name', forceString(data['MedDocumentTypeName']) if 'MedDocumentTypeName' in data else '')
                record.setValue('source_id', forceString(data['IdSource']) if 'IdSource' in data else '')
                record.setValue('regDate', toVariant(regDatetime))
                record.setValue('reg_id', forceString(data['RegId']) if 'RegId' in data else '')
                records.append(record)
            model.setItems(records)

    def getEmptyRecord(self, model):
        record = model.getEmptyRecord()
        record.append(QtSql.QSqlField('needSave', QVariant.Bool))
        record.append(QtSql.QSqlField('createDatetime', QVariant.DateTime))
        record.append(QtSql.QSqlField('createPerson_id', QVariant.Int))
        record.append(QtSql.QSqlField('deleted', QVariant.Int))
        record.append(QtSql.QSqlField('action_id', QVariant.Int))
        record.append(QtSql.QSqlField('documentCreationDate', QVariant.DateTime))
        record.append(QtSql.QSqlField('orgGUID', QVariant.String))
        record.append(QtSql.QSqlField('orgName', QVariant.String))
        record.append(QtSql.QSqlField('documentType', QVariant.Int))
        record.append(QtSql.QSqlField('name', QVariant.String))
        record.append(QtSql.QSqlField('source_id', QVariant.String))
        record.append(QtSql.QSqlField('regDate', QVariant.DateTime))
        record.append(QtSql.QSqlField('reg_id', QVariant.String))
        return record

    def getDataFromService(self, params):
        if self.servicesURL and params:
            try:
                response = requests.post(self.servicesURL + 'documents', json=params)
                jsonData = response.json()
                if response.status_code == 200:
                    # message = forceString(jsonData['Description'])
                    # QtGui.QMessageBox().information(self, u'Информация', message, QtGui.QMessageBox.Close)
                    return jsonData
                # elif response.status_code >= 400:
                #     message = forceString(jsonData['detail'])
                #     QtGui.QMessageBox().critical(self, u'Ошибка', u'Произошла ошибка:\n' + message, QtGui.QMessageBox.Close)
                else:
                    return None
            except Exception, e:
                QtGui.QMessageBox().critical(self, u'Ошибка',
                                             u'Произошла ошибка: ' + unicode(e),
                                             QtGui.QMessageBox.Close)

    def contextMenuEvent(self, event):
        self.menu = QtGui.QMenu(self)
        openFile = QtGui.QAction(u'Просмотр', self)
        selectAll = QtGui.QAction(u'Выбрать все', self)
        clearAll = QtGui.QAction(u'Очистить выбор', self)
        openFile.triggered.connect(self.openFile)
        selectAll.triggered.connect(self.selectAll)
        clearAll.triggered.connect(self.clearAll)
        self.menu.addAction(openFile)
        self.menu.addAction(selectAll)
        self.menu.addAction(clearAll)
        self.menu.popup(QtGui.QCursor.pos())

    def selectAll(self):
        model = self.tblExtendedMSEService.model()
        items = model.items()
        if items:
            for item in items:
                item.setValue('needSave', True)
            model.setItems(items)

    def clearAll(self):
        model = self.tblExtendedMSEService.model()
        items = model.items()
        if items:
            for item in items:
                item.setValue('needSave', False)
            model.setItems(items)

    def openFile(self):
        model = self.tblExtendedMSEService.model()
        row = self.tblExtendedMSEService.currentRow()
        docType = forceString(model.value(row, 'documentType'))
        docId = forceString(model.value(row, 'source_id'))
        if docType and docId:
            path = self.servicesURL + 'documents/{0}/{1}'.format(docType, docId)
            url = unicode(path)
            QtGui.QDesktopServices.openUrl(QUrl.fromEncoded(url))


class CExtendedMSEServiceModel(CRecordListModel):
    def __init__(self, parent):
        CRecordListModel.__init__(self, parent)
        self.addCol(CBoolInDocTableCol(u'Сохранить в базу', 'needSave', 20))
        self.addCol(CInDocTableCol(u'Дата создания', 'documentCreationDate', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Организация', 'orgName', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Код документа', 'source_id', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Тип документа', 'name', 20)).setReadOnly()


class CExtendedMSEModel(CRecordListModel):
    def __init__(self, parent):
        CRecordListModel.__init__(self, parent)
        self.addCol(CInDocTableCol(u'Дата создания', 'documentCreationDate', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Организация', 'orgName', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Код документа', 'source_id', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Тип документа', 'name', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Код типа документа', 'documentType', 20)).setReadOnly()
        self.loadData()

    def loadData(self, actionId=None):
        if actionId:
            db = QtGui.qApp.db
            tableExtendedMSE = db.table('soc_ExtendedMSE')
            cols = [tableExtendedMSE['id'],
                    tableExtendedMSE['deleted'],
                    tableExtendedMSE['action_id'],
                    tableExtendedMSE['documentCreationDate'],
                    tableExtendedMSE['orgGUID'],
                    tableExtendedMSE['orgName'],
                    tableExtendedMSE['documentType'],
                    tableExtendedMSE['name'],
                    tableExtendedMSE['source_id'],
                    tableExtendedMSE['regDate'],
                    tableExtendedMSE['reg_id']
                    ]
            cond = [tableExtendedMSE['action_id'].eq(actionId),
                    tableExtendedMSE['deleted'].eq(0)]
            tableQuery = tableExtendedMSE
            records = db.getRecordList(tableQuery, cols, cond)
            self.setItems(records)

    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if 0 <= row < len(self._items):

            if role == Qt.EditRole:
                col = self._cols[column]
                record = self._items[row]
                return record.value(col.fieldName())

            if role == Qt.DisplayRole:
                col = self._cols[column]
                record = self._items[row]
                return col.toString(record.value(col.fieldName()), record)

            if role == Qt.StatusTipRole:
                col = self._cols[column]
                record = self._items[row]
                return col.toStatusTip(record.value(col.fieldName()), record)

            if role == Qt.ToolTipRole and self.getColIndex('system_id') >= 0:
                db = QtGui.qApp.db
                record = db.getRecord('rbAccountingSystem', 'urn', forceString(self.items()[row].value('system_id')))
                if record:
                    result = forceString(record.value('urn'))
                else:
                    result = None
                return result

            if role == Qt.TextAlignmentRole:
                col = self._cols[column]
                return col.alignment()

            if role == Qt.CheckStateRole:
                col = self._cols[column]
                record = self._items[row]
                return col.toCheckState(record.value(col.fieldName()), record)

            record = self._items[row]
            if role == Qt.BackgroundRole and not forceInt(record.value('id')):
                return QtCore.QVariant(QtGui.QColor('#9ACD32'))
            if role == Qt.BackgroundRole and forceInt(record.value('deleted')):
                return QtCore.QVariant(QtGui.QColor('#FF4500'))
        else:
            if role == Qt.CheckStateRole:
                flags = self.flags(index)
                if (flags & Qt.ItemIsUserCheckable and flags & Qt.ItemIsEnabled):
                    col = self._cols[column]
                    return col.toCheckState(QVariant(False), None)

        return QVariant()
