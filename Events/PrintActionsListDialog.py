# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2025 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant, pyqtSignature, SIGNAL

from Events.Action import CActionTypeCache
from Events.Utils import getEventContextData
from library.DialogBase import CDialogBase
from library.PrintTemplates import getPrintTemplates
from library.Utils import forceRef, forceInt, forceString, forceDate

from Events.Ui_PrintActionsListDialog import Ui_PrintActionsListDialog


class CPrintActionsListDialog(CDialogBase, Ui_PrintActionsListDialog):
    def __init__(self, parent, eventEditor):
        CDialogBase.__init__(self, parent)
        self.eventEditor = eventEditor
        self.addModels('Actions', CPrintActionsModel(self, eventEditor))
        self.setupUi(self)
        self.setModels(self.tblActions, self.modelActions, self.selectionModelActions)
        self.tblActions.setSelectionBehavior(QtGui.QAbstractItemView.SelectItems)
        self.tblActions.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        h = self.fontMetrics().height() * 3 / 2
        self.tblActions.verticalHeader().setDefaultSectionSize(h)
        self.tblActions.verticalHeader().hide()
        self.tblActions.horizontalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents)
        self.tblActions.horizontalHeader().setStretchLastSection(True)
        self.tblActions.setItemDelegateForColumn(4, CTemplateComboBoxDelegate(self))
        self.updateAcceptButton()
        edtBegDateBlockSignals = self.edtBegDate.blockSignals(True)
        edtEndDateBlockSignals = self.edtEndDate.blockSignals(True)
        self.edtBegDate.setDate(None)
        self.edtEndDate.setDate(None)
        self.edtBegDate.blockSignals(edtBegDateBlockSignals)
        self.edtEndDate.blockSignals(edtEndDateBlockSignals)


    def printActions(self):
        items = self.modelActions.selectedItems()
        if self.rbSortByBegDate.isChecked():
            items.sort(key=lambda item: item['begDate'])
        elif self.rbSortByEndDate.isChecked():
            items.sort(key=lambda item: item['endDate'])
        self.templateIdAndDataList = []
        self.addPageBreaks = self.chbAddPageBreaks.isChecked()
        for item in items:
            actionIndex = item['actionIndex']
            selectedTemplateIndex = item['selectedTemplateIndex']
            data = getEventContextData(self.eventEditor)
            eventInfo = data['event']
            data['actions'] = eventInfo.actions
            data['action'] = eventInfo.actions[actionIndex]
            data['currentActionIndex'] = actionIndex
            templateId = item['templates'][selectedTemplateIndex][1]
            self.templateIdAndDataList.append((templateId, data))
        return True


    def updateAcceptButton(self):
        self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(self.modelActions.hasSelectedItems())


    @pyqtSignature('QModelIndex, QModelIndex')
    def on_modelActions_dataChanged(self, leftTop, rightBottom):
        self.updateAcceptButton()
        row = leftTop.row()
        column = rightBottom.column()
        if column == self.modelActions.colTemplate:
            record = self.modelActions.items[row]
            selectedTemplateIndex = record['selectedTemplateIndex']
            context = record['context']
            if QtGui.QMessageBox().question(self, 
                                         u'Внимание!', 
                                         u'Изменить шаблон для всех документов данного типа?', 
                                         QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                        QtGui.QMessageBox.No) == QtGui.QMessageBox.Yes:
                for item in self.modelActions.items:
                    if item['context'] == context:
                        item['selectedTemplateIndex'] = selectedTemplateIndex


    @pyqtSignature('')
    def on_buttonBox_accepted(self):
        try:
            if self.printActions():
                self.accept()
        except Exception as e:
            QtGui.QMessageBox.critical(self, u'Ошибка', unicode(e), QtGui.QMessageBox.Close)


    @pyqtSignature('')
    def on_buttonBox_rejected(self):
        self.reject()


    @pyqtSignature('')
    def on_btnSelectAll_clicked(self):
        self.modelActions.selectItemsByClasses([0, 1, 2, 3])


    @pyqtSignature('')
    def on_btnSelectStatus_clicked(self):
        self.modelActions.selectItemsByClasses([0])


    @pyqtSignature('')
    def on_btnSelectDiagnostic_clicked(self):
        self.modelActions.selectItemsByClasses([1])


    @pyqtSignature('')
    def on_btnSelectCure_clicked(self):
        self.modelActions.selectItemsByClasses([2])


    @pyqtSignature('')
    def on_btnSelectMisc_clicked(self):
        self.modelActions.selectItemsByClasses([3])


    @pyqtSignature('')
    def on_btnSelectNone_clicked(self):
        self.modelActions.selectItemsByClasses([])


    @pyqtSignature('QDate')
    def on_edtBegDate_dateChanged(self, date):
        self.modelActions.setDates(date, self.edtEndDate.date())

    @pyqtSignature('QDate')
    def on_edtEndDate_dateChanged(self, date):
        self.modelActions.setDates(self.edtBegDate.date(), date)



class CTemplateComboBoxDelegate(QtGui.QItemDelegate):
    def createEditor(self, parent, option, index):
        model = index.model()
        row = index.row()
        item = model.items[row]
        templates = item['templates']
        editor = QtGui.QComboBox(parent)
        editor.addItems([template[0] for template in templates])
        return editor


    def setEditorData(self, editor, index):
        model = index.model()
        data = model.data(index, Qt.EditRole)
        editor.setCurrentIndex(forceInt(data))


    def setModelData(self, editor, model, index):
        model.setData(index, QVariant(editor.currentIndex()))



class CPrintActionsModel(QAbstractTableModel):
    headers = [u'Печать', u'Действие', u'Дата начала', u'Дата окончания', u'Шаблон']
    colTemplate = 4

    def __init__(self, parent, eventEditor):
        QAbstractTableModel.__init__(self, parent)
        self.eventEditor = eventEditor
        self.eventContextData = getEventContextData(eventEditor)
        self.begDate = None
        self.endDate = None
        self.selectItems()


    def columnCount(self, index = None):
        return len(CPrintActionsModel.headers)


    def rowCount(self, index = QModelIndex()):
        return len(self.items)


    def flags(self, index = QModelIndex()):
        result = Qt.NoItemFlags
        row = index.row()
        item = self.items[row]
        if item['templates']:
            result |= Qt.ItemIsSelectable | Qt.ItemIsEnabled
            if index.column() == 0:
                result |= Qt.ItemIsUserCheckable
            if index.column() == 4:
                result |= Qt.ItemIsEditable
        return result


    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return QVariant(CPrintActionsModel.headers[section])
        else:
            return QVariant()


    def data(self, index, role = Qt.DisplayRole):
        row = index.row()
        column = index.column()
        item = self.items[row]
        record = item['record']
        if column == 0 and role == Qt.CheckStateRole:
            return QVariant(Qt.Checked if item['printed'] else Qt.Unchecked)
        elif column == 1 and role == Qt.DisplayRole:
            return QVariant(item['fullName'])
        elif column == 2 and role == Qt.DisplayRole:
            begDate = record.value('begDate')
            return QVariant(forceString(begDate))
        elif column == 3 and role == Qt.DisplayRole:
            endDate = record.value('endDate')
            return QVariant(forceString(endDate))
        elif column == 4 and role == Qt.DisplayRole:
            templates = item['templates']
            selectedTemplateIndex = item['selectedTemplateIndex']
            return QVariant(templates[selectedTemplateIndex][0]) if templates else QVariant()
        elif column == 4 and role == Qt.EditRole:
            return QVariant(item['selectedTemplateIndex'])
        return QVariant()


    def setData(self, index, value, role = Qt.EditRole):
        row = index.row()
        column = index.column()
        item = self.items[row]
        if column == 0 and role == Qt.CheckStateRole:
            item['printed'] = not item['printed']
            self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
            return True
        if column == 4 and role == Qt.EditRole:
            newTemplateIndex = value.toInt()
            if newTemplateIndex[1]:
                item['selectedTemplateIndex'] = newTemplateIndex[0]
                self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
                return True
        return False


    def selectedItems(self):
        return [item for item in self.items if item['printed']]


    def hasSelectedItems(self):
        for item in self.items:
            if item['printed']:
                return True
        return False


    def selectItemsByClasses(self, classes):
        for item in self.items:
            item['printed'] = (item['templates'] and item['actionType'].class_ in classes)
        topLeft = self.index(0, 0)
        bottomRight = self.index(self.rowCount() - 1, 0)
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), topLeft, bottomRight)


    def setDates(self, begDate, endDate):
        self.begDate = begDate
        self.endDate = endDate
        self.selectItems()


    def selectItems(self):
        self.items = []
        for index, rawItem in enumerate(self.eventContextData['event'].actions._rawItems):
            record, action = rawItem
            if self.begDate and not self.endDate:
                if not forceDate(record.value('begDate')) >= self.begDate:
                    continue
            elif self.endDate and not self.begDate:
                if not forceDate(record.value('begDate')) <= self.endDate:
                    continue
            elif self.begDate and self.endDate:
                if not (self.begDate <= forceDate(record.value('begDate')) <= self.endDate):
                    continue
            actionTypeId = forceRef(record.value('actionType_id'))
            actionType = CActionTypeCache.getById(actionTypeId) if actionTypeId else None
            context = actionType.context if actionType else ''
            templates = getPrintTemplates(context)
            selectedTemplateIndex = 0 if templates else None
            names = []
            if actionType:
                names.append(actionType.name)
            specifiedName = forceString(record.value('specifiedName'))
            if specifiedName:
                names.append(specifiedName)
            self.items.append({
                'printed': bool(templates),
                'record': record,
                'action': action,
                'actionType': actionType,
                'fullName': ' '.join(names),
                'templates': templates,
                'selectedTemplateIndex': selectedTemplateIndex,
                'actionIndex': index,
                'begDate': forceDate(record.value('begDate')),
                'endDate': forceDate(record.value('endDate')),
                'context': context,
            })
        topLeft = self.index(0, 0)
        bottomRight = self.index(self.rowCount() - 1, 0)
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), topLeft, bottomRight)
