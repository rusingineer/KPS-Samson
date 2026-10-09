# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2026 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

import os
import codecs

from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignature, SIGNAL

from library.InDocTable import CInDocTableModel, CRBInDocTableCol, CEnumInDocTableCol
from library.interchange import (getCheckBoxValue, getComboBoxValue, getLineEditValue, getTextEditValue,
                                 setCheckBoxValue, setComboBoxValue, setLineEditValue, setTextEditValue)
from library.ItemsListDialog import CItemsListDialogWithProxy, CItemEditorDialog
from library.TableModel import CBoolCol, CEnumCol, CTextCol
from library.Utils import forceRef, forceString, forceStringEx
from library.ClientRecordProperties import CRecordProperties

from Users.Rights import urAdmin, urDeletePrintTemplate

from Ui_RBPrintTemplateListDialog import Ui_RBPrintTemplateListDialog
from Ui_RBPrintTemplateEditor import Ui_PrintTemplateEditorDialog


class CRBPrintTemplate(CItemsListDialogWithProxy, Ui_RBPrintTemplateListDialog):
    setupUi = Ui_RBPrintTemplateListDialog.setupUi
    retranslateUi = Ui_RBPrintTemplateListDialog.retranslateUi

    def __init__(self, parent):
        CItemsListDialogWithProxy.__init__(self, parent, [
            CTextCol(u'Контекст',                    ['context'], 20),
            CTextCol(u'Код',                         ['code'], 12),
            CTextCol(u'Наименование',                ['name'],   40),
            CTextCol(u'Группа',                      ['groupName'],   40),
            CTextCol(u'Файл',                        ['fileName'], 25),
            CBoolCol(u'Для отображения в Мед.карте', ['inAmbCard'], 7),
            CEnumCol(u'Тип',                         ['type'], [u'HTML', u'Exaro', u'SVG', u'CSS'], 10),
            CBoolCol(u'Требует идентификатор события', ['needEventId'], 7),
            ], 'rbPrintTemplate', ['context', 'code', 'groupName', 'name', 'type', 'id'])
        self.setWindowTitleEx(u'Шаблоны печати')

        self.actDuplicate = QtGui.QAction(u'Дублировать', self)
        self.actDuplicate.setObjectName('actDuplicate')
        self.actDuplicate.triggered.connect(self.duplicateCurrentRow)

        popupItems = [self.actDuplicate]
        if QtGui.qApp.userHasAnyRight([urAdmin, urDeletePrintTemplate]):
            self.actDelete = QtGui.QAction(u'Удалить', self)
            self.actDelete.setObjectName('actDelete')
            self.connect(self.actDelete, SIGNAL('triggered()'), self.markCurrentRowDeleted)
            popupItems.append(self.actDelete)

        self.actProperties = QtGui.QAction(u'Свойства записи', self)
        self.actProperties.setObjectName('actProperties')
        self.actProperties.triggered.connect(self.showRecordProperties)
        popupItems.append(self.actProperties)

        self.tblItems.createPopupMenu(popupItems)


    def getItemEditor(self):
        return CPrintTemplateEditor(self)


    def duplicateCurrentRow(self):
        currentIndex = self.currentIndex()
        if currentIndex.isValid():
            row = currentIndex.row()
            itemId = self.tblItems.model().idList()[row]
            newItemId = self.duplicateRecord(itemId)
            self.renewListAndSetTo(newItemId)


    def markCurrentRowDeleted(self):
        currentIndex = self.currentIndex()
        if currentIndex.isValid():
            row = currentIndex.row()
            itemId = self.tblItems.model().idList()[row]
            db = QtGui.qApp.db
            table = db.table('rbPrintTemplate')
            db.markRecordsDeleted(table, table['id'].eq(itemId))
            self.renewListAndSetTo()


    def showRecordProperties(self):
        currentIndex = self.currentIndex()
        if not currentIndex.isValid():
            return
        itemId = self.currentItemId()
        CTemplateRecordProperties(self, 'rbPrintTemplate', itemId).exec_()


    @pyqtSignature('QString')
    def on_edtCodeFilter_textChanged(self, text):
        if len(text) > 0:
            self.proxyModel.setFilter('code', text, self.proxyModel.MatchContains)
        else:
            self.proxyModel.removeFilter('code')


    @pyqtSignature('QString')
    def on_edtNameFilter_textChanged(self, text):
        if len(text) > 0:
            self.proxyModel.setFilter('name', text, self.proxyModel.MatchContains)
        else:
            self.proxyModel.removeFilter('name')


    @pyqtSignature('QString')
    def on_edtContextFilter_textChanged(self, text):
        if len(text) > 0:
            self.proxyModel.setFilter('context', text, self.proxyModel.MatchContains)
        else:
            self.proxyModel.removeFilter('context')


    @pyqtSignature('')
    def on_btnEdit_clicked(self):
        currentIndex = self.currentIndex()
        if currentIndex.isValid():
            row = currentIndex.row()
            itemId = self.tblItems.model().idList()[row]
            dialog = self.getItemEditor()
            try:
                dialog.load(itemId)
                if dialog.exec_():
                    itemId = dialog.itemId()
                    self.renewListAndSetTo(itemId)
            finally:
                dialog.deleteLater()


class CPrintTemplateEditor(Ui_PrintTemplateEditorDialog, CItemEditorDialog):
    def __init__(self, parent):
        CItemEditorDialog.__init__(self, parent, 'rbPrintTemplate')
        self.setWindowTitleEx(u'Шаблон печати')
        self.exaroEditor = forceString(QtGui.qApp.preferences.appPrefs.get('exaroEditor', ''))
        self.addModels('ClientConsents', CClientConsentInDocTable(self))
        self.setModels(self.tblClientConsents, self.modelClientConsents, self.selectionModelClientConsents)
        self.tblClientConsents.addPopupDelRow()
        self.btnApply = QtGui.QPushButton(u'Применить', self.buttonBox)
        self.btnApply.setObjectName('btnApply')
        self.buttonBox.addButton(self.btnApply, QtGui.QDialogButtonBox.ApplyRole)
        self.btnApply.clicked.connect(self.on_btnApply_clicked)


    def setRecord(self, record):
        CItemEditorDialog.setRecord(self, record)
        setLineEditValue(self.edtContext, record, 'context')
        setLineEditValue(self.edtGroupName, record, 'groupName')
        setLineEditValue(self.edtFileName, record, 'fileName')
        setTextEditValue(self.edtDefault, record, 'default')
        setCheckBoxValue(self.chkInAmbCard, record, 'inAmbCard')
        setCheckBoxValue(self.chkNeedEventId, record, 'needEventId')
        setCheckBoxValue(self.chkPrintBlank, record, 'printBlank')
        setComboBoxValue(self.cmbType, record, 'type')
        setComboBoxValue(self.cmbRequireSignerPerson, record, 'requireSignerPerson')
        self.modelClientConsents.loadItems(self.itemId())

    #        self.setIsDirty(False)

    def getRecord(self):
        record = CItemEditorDialog.getRecord(self)
        getLineEditValue(self.edtContext, record, 'context')
        getLineEditValue(self.edtGroupName, record, 'groupName')
        getLineEditValue(self.edtFileName, record, 'fileName')
        getTextEditValue(self.edtDefault, record, 'default')
        getCheckBoxValue(self.chkInAmbCard, record, 'inAmbCard')
        getCheckBoxValue(self.chkNeedEventId, record, 'needEventId')
        getCheckBoxValue(self.chkPrintBlank, record, 'printBlank')
        getComboBoxValue(self.cmbType, record, 'type')
        getComboBoxValue(self.cmbRequireSignerPerson, record, 'requireSignerPerson')
        return record


    def saveInternals(self, _id):
        self.modelClientConsents.saveItems(_id)


    def checkDataEntered(self):
        result = CItemEditorDialog.checkDataEntered(self)
        result = result and (forceStringEx(self.edtContext.text()) or self.checkInputMessage(u'контекст', False,
                                                                                             self.edtContext))
        result = result and self.checkClientConsentTypeValues()
        return result


    def checkClientConsentTypeValues(self):
        for row, item in enumerate(self.modelClientConsents.items()):
            clientConsentTypeId = forceRef(item.value('clientConsentType_id'))
            if not clientConsentTypeId:
                return self.checkInputMessage(u'тип согласия пациента', False, self.tblClientConsents, row,
                                              self.modelClientConsents.clientConsentTypeColumn)
        return True

    @pyqtSignature('int')
    def on_cmbType_currentIndexChanged(self, index):
        self.btnEdit.setEnabled((index == 1) and (self.exaroEditor != ''))


    @pyqtSignature('')
    def on_btnEdit_clicked(self):
        fileName = forceString(self.edtFileName.text())
        tmpDir = None
        try:
            if not fileName:
                tmpDir = QtGui.qApp.getTmpDir('edit')
                fullPath = os.path.join(tmpDir, 'template.bdrt')
                txt = self.edtDefault.toPlainText()
                _file = codecs.open(unicode(fullPath), encoding='utf-8', mode='w+')
                _file.write(unicode(txt))
                _file.close()
            else:
                fullPath = os.path.join(QtGui.qApp.getTemplateDir(), fileName)

            cmdLine = u'"%s" "%s"' % (self.exaroEditor, fullPath)
            started, error, exitCode = QtGui.qApp.execProgram(cmdLine)
            if started:
                if not fileName:
                    for enc in ('utf-8', 'cp1251'):
                        try:
                            _file = codecs.open(fullPath, encoding=enc, mode='r')
                            txt = _file.read()
                            _file.close()
                            self.edtDefault.setPlainText(txt)
                            return
                        except:
                            pass
                    QtGui.QMessageBox.critical(None,
                                               u'Внимание!',
                                               u'Не удалось загрузить "%s" после' % fullPath,
                                               QtGui.QMessageBox.Close)
            else:
                QtGui.QMessageBox.critical(None,
                                           u'Внимание!',
                                           u'Не удалось запустить "%s"' % self.exaroEditor,
                                           QtGui.QMessageBox.Close)
        finally:
            if tmpDir:
                QtGui.qApp.removeTmpDir(tmpDir)

    @pyqtSignature('')
    def on_btnApply_clicked(self):
        """Обработчик нажатия кнопки 'Применить'"""
        if self.checkDataEntered():
            try:
                self.saveData()
                self.afterSave()
                if hasattr(self.parent(), 'renewListAndSetTo'):
                    self.parent().renewListAndSetTo(self.itemId())
            except Exception as e:
                QtGui.qApp.logCurrentException()
                QtGui.QMessageBox.critical(self,
                                           u'Ошибка',
                                           u'Не удалось сохранить изменения:\n%s' % unicode(e),
                                           QtGui.QMessageBox.Close)
                return False
        return True


class CClientConsentInDocTable(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'rbPrintTemplate_ClientConsentType', 'id', 'master_id', parent)
        self.addCol(CRBInDocTableCol(u'Тип согласия', 'clientConsentType_id', 15, 'rbClientConsentType'))
        self.addCol(CEnumInDocTableCol(u'Значение', 'value', 10, [u'Нет', u'Да']))
        self.clientConsentTypeColumn = self.getColIndex('clientConsentType_id')


class CTemplateRecordProperties(CRecordProperties):
    def loadInfo(self):
        if self.recordId is None:
            return u''
        db = QtGui.qApp.db
        fields = [
            'createPerson_id',
            'modifyPerson_id',
            'createDatetime',
            'modifyDatetime',
        ]
        record = db.getRecord(self.table, fields, self.recordId)
        createPersonId = forceRef(record.value('createPerson_id'))
        modifyPersonId = forceRef(record.value('modifyPerson_id'))
        createPerson = db.translate('vrbPersonWithSpeciality', 'id', createPersonId, 'name')
        modifyPerson = db.translate('vrbPersonWithSpeciality', 'id', modifyPersonId, 'name')
        return u'\n'.join([
            u'Идентификатор: ' + forceString(self.recordId),
            u'Создатель записи: ' + forceString(createPerson),
            u'Дата создания записи: ' + forceString(record.value('createDatetime')),
            u'Редактор записи: ' + forceString(modifyPerson),
            u'Дата редактирования записи: ' + forceString(record.value('modifyDatetime')),
        ])
