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

import json
import requests
import urlparse

from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignature, SIGNAL, Qt, QObject
from library.SortFilterProxyTableModel import CSortFilterProxyTableModel
from library.interchange import getCheckBoxValue, getLineEditValue, setCheckBoxValue, setLineEditValue
from library.ItemsListDialog import CItemsListDialog, CItemEditorBaseDialog
from library.TableModel import CBoolCol, CTextCol, CTableModel
from RefBooks.Tables import rbAccountingSystem, rbCode, rbName
from library.Utils import forceString, forceRef
from Ui_RBAccountingSystemEditor import Ui_ItemEditorDialog
from Ui_RBAccountingSystemListDialog import Ui_RBAccountingSystemListDialog


class CRBAccountingSystemList(CItemsListDialog, Ui_RBAccountingSystemListDialog):
    setupUi = Ui_RBAccountingSystemListDialog.setupUi
    retranslateUi = Ui_RBAccountingSystemListDialog.retranslateUi

    def __init__(self, parent):
        CItemsListDialog.__init__(self, parent, [
            CTextCol(u'Код',          [rbCode], 10),
            CTextCol(u'Наименование', [rbName], 50),
            CTextCol(u'URN',          ['urn'],  50),
            CTextCol(u'Версия', ['version'], 10),
            CBoolCol(u'Разрешать изменение',         ['isEditable'], 30),
            CBoolCol(u'Разрешать удаление',          ['isDeletable'], 30),
            CBoolCol(u'Отображать в информации о пациенте',         ['showInClientInfo'], 20),
            CBoolCol(u'Требует ввода уникального значения',         ['isUnique'], 20),

            ], rbAccountingSystem, [rbCode, rbName])
        self.setWindowTitleEx(u'Внешние учётные системы')

    def setup(self, cols, tableName, order, forSelect=False, filterClass=None):
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.forSelect = forSelect
        self.filterClass = filterClass
        self.props = {}
        self.order = order

        self.addModels('', CTableModel(self, cols))
        self.addModels('AccountingSystemSort', CSortFilterProxyTableModel(self, self.model))
        self.model = self.modelAccountingSystemSort.sourceModel()
        self.model.idFieldName = self.idFieldName
        self.model.setTable(tableName, recordCacheCapacity=QtGui.qApp.db.getCount(tableName, 'id'))
        self.setModels(self.tblItems, self.modelAccountingSystemSort, self.selectionModelAccountingSystemSort)

        QObject.connect(self.tblItems.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.setSort)

    def currentItemId(self):
        index = self.tblItems.currentIndex()
        sourceRow = self.modelAccountingSystemSort.mapToSource(index).row()
        return forceRef(self.model.getRecordByRow(sourceRow).value('id'))

    def getItemEditor(self):
        return CRBAccountingSystemEditor(self)

    def preSetupUi(self):
        self.addObject('btnSync', QtGui.QPushButton(u'Синхронизировать версии', self))
        super(CRBAccountingSystemList, self).preSetupUi()

    def postSetupUi(self):
        self.buttonBox.addButton(self.btnSync, QtGui.QDialogButtonBox.ActionRole)
        super(CRBAccountingSystemList, self).postSetupUi()
        self.btnFilter.setVisible(False)
        self.btnSelect.setVisible(False)

    @pyqtSignature('')
    def on_btnSync_clicked(self):
        servicesURL = forceString(QtGui.qApp._globalPreferences.get('23:servicesURL'))
        if servicesURL:
            servicesURL = servicesURL.replace('${dbServerName}', QtGui.qApp.preferences.dbServerName)
            servicesURL = urlparse.urljoin(servicesURL, '/api/local/services/terminology')
            try:
                response = requests.get(servicesURL + '/update/$versions')
                content = json.loads(response.content.decode('utf-8'))
                if content[u'success'] is True:
                    count = content[u'count_updated']
                    result = u'Обновлено ' + unicode(count) + u' справочника(-ов)\n'
                    if content[u'errors']:
                        result += u'Ошибки: \n'
                    for error in content[u'errors']:
                        result += u'urn' + error[u'urn'] + u', ошибка: ' + error[u'message'] + u'\n'
                    QtGui.QMessageBox().information(self, u'Сообщение', u'Ответ: \n' + result,
                                                    QtGui.QMessageBox.Close)
                else:
                    QtGui.QMessageBox().critical(self, u'Ошибка', u'Произошла ошибка: ' + unicode(content[u'error']),
                                                 QtGui.QMessageBox.Close)
            except Exception, e:
                QtGui.QMessageBox().critical(self, u'Ошибка', u'Произошла ошибка: ' + unicode(e),
                                             QtGui.QMessageBox.Close)
        else:
            QtGui.QMessageBox().critical(self, u'Ошибка', u'Не указан адрес сервера сервисов в глобальных настройках МИС', QtGui.QMessageBox.Close)

    @pyqtSignature('QString')
    def on_edtCodeFilter_textChanged(self, text):
        if text.isEmpty():
            self.modelAccountingSystemSort.removeFilter('code')
        else:
            self.modelAccountingSystemSort.setFilter('code', text, CSortFilterProxyTableModel.MatchContains)

    @pyqtSignature('QString')
    def on_edtNameFilter_textChanged(self, text):
        if text.isEmpty():
            self.modelAccountingSystemSort.removeFilter('name')
        else:
            self.modelAccountingSystemSort.setFilter('name', text, CSortFilterProxyTableModel.MatchContains)

    @pyqtSignature('QString')
    def on_edtUrnFilter_textChanged(self, text):
        if text.isEmpty():
            self.modelAccountingSystemSort.removeFilter('urn')
        else:
            self.modelAccountingSystemSort.setFilter('urn', text, CSortFilterProxyTableModel.MatchContains)


class CRBAccountingSystemEditor(CItemEditorBaseDialog, Ui_ItemEditorDialog):
    def __init__(self,  parent):
        CItemEditorBaseDialog.__init__(self, parent, rbAccountingSystem)
        self.setWindowTitleEx(u'Внешняя учётная система')
        self.setupUi(self)
        self.setupDirtyCather()

    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        setLineEditValue(self.edtCode,             record, 'code')
        setLineEditValue(self.edtName,             record, 'name')
        setLineEditValue(self.edtUrn,              record, 'urn')
        setLineEditValue(self.edtVersion,          record, 'version')
        setLineEditValue(self.edtDomain,           record, 'domain')
        setCheckBoxValue(self.chkEditable,         record, 'isEditable')
        setCheckBoxValue(self.chkDeletable,        record, 'isDeletable')
        setCheckBoxValue(self.chkShowInClientInfo, record, 'showInClientInfo')
        setCheckBoxValue(self.chkIsUnique,         record, 'isUnique')

    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        getLineEditValue(self.edtCode,             record, 'code')
        getLineEditValue(self.edtName,             record, 'name')
        getLineEditValue(self.edtUrn,              record, 'urn')
        getLineEditValue(self.edtVersion,          record, 'version')
        getLineEditValue(self.edtDomain,           record, 'domain')
        getCheckBoxValue(self.chkEditable,         record, 'isEditable')
        getCheckBoxValue(self.chkDeletable,        record, 'isDeletable')
        getCheckBoxValue(self.chkShowInClientInfo, record, 'showInClientInfo')
        getCheckBoxValue(self.chkIsUnique,         record, 'isUnique')
        return record

    def saveData(self):
        if not self.checkDataEntered():
            QtGui.QMessageBox.critical(
                self,
                u'Ошибка сохранения',
                u'Невозможно добавление справочника с уже существующим URN\n',
                QtGui.QMessageBox.Close)
            return False
        else:
            return self.save()

    def checkDataEntered(self):
        # проверка на уникальность urn
        par = self.parent().model
        record = self.getRecord()
        urn = forceString(record.value('urn'))
        id = forceString(record.value('id'))
        unique_urn = True
        if urn:
            for _ in range(par.rowCount()):
                rec = par.getRecordByRow(_)
                rec_id = forceString(rec.value('id'))
                rec_urn = forceString(rec.value('urn'))
                if rec_id != id and rec_urn == urn:
                    unique_urn = False
                    break
        return unique_urn
