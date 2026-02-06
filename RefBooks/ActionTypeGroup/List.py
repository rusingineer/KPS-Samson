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
from PyQt4.QtCore import SIGNAL, Qt, pyqtSignature, QDateTime, QTimer, QVariant

from library.DialogBase import CDialogBase
from library.Utils import forceBool, forceRef, forceInt, toVariant, forceStringEx, addDotsEx, forceBool
from library.TableModel import CTableModel, CTextCol, CEnumCol, CDesignationCol, CRefBookCol, CDateCol
from library.crbcombobox import CRBComboBox

from Users.Rights import urAdmin, urCanCreateNewActionTypeGroup, urCanEditForeignActionTypeGroup, urCanDeleteForeignActionTypeGroup

from RefBooks.ActionTypeGroup.RBActionTypeSelectorDialog import CActionTypeSelector
from RefBooks.ActionTypeGroup.RBActionTypeGroupEditor import ActionTypeGroupEditor
from Ui_RBActionTypeGroupList import Ui_RBActionTypeGroupList


ACTION_TYPE_GROUP_APPOINTMENT = 0


class CRBActionTypeGroup(CDialogBase, Ui_RBActionTypeGroupList):
    """
    Диалог 'Шаблоны назначения действий'
    """
    _groupType = None
    
    # Тип доступа - автор (значение из/для БД)
    ACTION_TYPE_GROUP_AVAILABILITY_AUTHOR = 2

    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.addModels('ActionTypeGroups', CActionTypeGroupsModel(self))
        self.addModels('ActionTypeGroupItems', CActionTypeGroupItemsModel(self))
        self.addObject('actEditTemplate', QtGui.QAction(u'Редактировать запись', self))
        self.addObject('actDelTemplate', QtGui.QAction(u'Удалить запись', self))

        self.setupUi(self)
        self.setModels(self.tblActionTypeGroups, self.modelActionTypeGroups, self.selectionModelActionTypeGroups)
        self.setModels(self.tblActionTypeGroupItems,
                       self.modelActionTypeGroupItems,
                       self.selectionModelActionTypeGroupItems)

        self.tblActionTypeGroupItems.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        self.tblActionTypeGroupItems.setColumnHidden(CActionTypeGroupItemsModel.columnShowInForm, False)
        self.tblActionTypeGroups.addPopupAction(self.actEditTemplate)
        self.tblActionTypeGroups.addPopupAction(self.actDelTemplate)
        self.tblActionTypeGroups.addPopupRecordProperies()
        self.connect(self.selectionModelActionTypeGroups,
                     SIGNAL('currentChanged(QModelIndex,QModelIndex)'),
                     self.on_selectionModelActionTypeGroupsCurrentChanged)
        self.btnEditTemplate.clicked.connect(self.on_actEditTemplate_triggered)
        self.actDelTemplate.triggered.connect(self.tblActionTypeGroups.removeSelectedRows)
        self.btnDelTemplate.clicked.connect(self.tblActionTypeGroups.removeSelectedRows)
        self.modelActionTypeGroups.modelReset.connect(self.modelActionTypeGroupsReset)
        
        # Настраиваем таймер задержки старта поиска в БД при вводе символов в строку поиска наименования
        self._inputTimer = QTimer()
        self._inputTimer.setSingleShot(True)
        self._inputTimer.setInterval(600)
        self._inputTimer.timeout.connect(self._inputTimerExp)
        
        db = QtGui.qApp.db
        self._owner = None
        self._enSnils = 0
        self._speciality = None
        self._access = None
        self._begDate = QDateTime()
        self._endDate = QDateTime()
        self._searchString = ''
        self.cmbAccess.setCurrentIndex(0)
        self.cmbSpeciality.setTable('rbSpeciality')
        self.cmbCreatePerson.setValue(QtGui.qApp.userId)
        self.chkSnils.setChecked(False)
        self.edtBegCreateDate.canBeEmpty()
        self.edtBegCreateDate.setDate(None)
        self.edtEndCreateDate.canBeEmpty()
        self.edtEndCreateDate.setDate(None)
        self.setWindowTitle(u'Шаблоны назначения действий')


    def getTemplateOwner(self):
        return self._owner

    def getEnSnils(self):
        return self._enSnils

    def getTemplateSpeciality(self):
        return self._speciality

    def getTemplateAccess(self):
        return self._access

    def getTemplateCreationBegDate(self):
        return self._begDate

    def getTemplateCreationEndDate(self):
        return self._endDate

    def getSearchString(self):
        return self._searchString

    def exec_(self):
        self.modelActionTypeGroups.loadData()
        return CDialogBase.exec_(self)
    
    @pyqtSignature('')
    def on_actEditTemplate_triggered(self):
        curTemplateId = self.tblActionTypeGroups.currentItemId()
        dialog = ActionTypeGroupEditor(self, curTemplateId)
        dialog.exec_()
        templateId = dialog.getTemplateId()
        self.modelActionTypeGroups.reloadData()
        if templateId:
            row = self.modelActionTypeGroups.findItemIdIndex(templateId)
            index = self.modelActionTypeGroups.index(row, 0)
            self.tblActionTypeGroups.setCurrentIndex(index)
        else:
            self.on_selectionModelActionTypeGroupsCurrentChanged(None, None)
    
    @pyqtSignature('')
    def on_btnNewTemplate_clicked(self):
        curTemplateId = None
        dialog = ActionTypeGroupEditor(self, curTemplateId)
        dialog.exec_()
        templateId = dialog.getTemplateId()
        self.modelActionTypeGroups.reloadData()
        if templateId:
            row = self.modelActionTypeGroups.findItemIdIndex(templateId)
            index = self.modelActionTypeGroups.index(row, 0)
            self.tblActionTypeGroups.setCurrentIndex(index)
        else:
            self.on_selectionModelActionTypeGroupsCurrentChanged(None, None)

    def on_selectionModelActionTypeGroupsCurrentChanged(self, current, previous):
        """
        Изменение выделения в списке шаблонов
        Обновляем таблицу со списком действий, меняем активность элементов управления
        """
        itemId = self.tblActionTypeGroups.currentItemId()
        if not itemId:
            self.tblActionTypeGroupItems.setIdList([])
        else:
            db = QtGui.qApp.db
            table = db.table('ActionTypeGroup_Item')
            idList = db.getIdList(table, where=[table['master_id'].eq(itemId), table['deleted'].eq(0)])
            self.tblActionTypeGroupItems.setIdList(idList)
        self.tblActionTypeGroupsControlsEnable(bool(self.modelActionTypeGroups.rowCount()))

    def tblActionTypeGroupsControlsEnable(self, enable):
        """
        Управление активностью элементов управления

        :param enable: общее управление активностью элементов Редактировать, Удалить
        :type enable: bool
        """
        record = self.tblActionTypeGroups.currentItem()
        userHasRightToEdit = False
        userHasRightToDelete = False
        userHasRightToCreate = QtGui.qApp.userHasRight(urAdmin) or QtGui.qApp.userHasRight(urCanCreateNewActionTypeGroup)
        if record:
            createPersonId = forceRef(record.value('createPerson_id'))
             # Свой шаблон или работаем под администратором - можем править и удалять любые шаблоны
            if createPersonId == QtGui.qApp.userId or QtGui.qApp.userHasRight(urAdmin):
                userHasRightToEdit = True
                userHasRightToDelete = True
            # Есть право на редактирование чужих шаблонов
            if QtGui.qApp.userHasRight(urCanEditForeignActionTypeGroup):
                userHasRightToEdit = True
            # Есть право на редактирование чужих шаблонов
            if QtGui.qApp.userHasRight(urCanDeleteForeignActionTypeGroup):
                userHasRightToDelete = True
        else: # Если в таблице нет текущей записи (например - таблица пустая) решение о включении элементов управленя будет определять параметр enable
            userHasRightToEdit = True
            userHasRightToDelete = True
        self.btnNewTemplate.setEnabled(userHasRightToCreate)
        self.actEditTemplate.setEnabled(enable and userHasRightToEdit)
        self.btnEditTemplate.setEnabled(enable and userHasRightToEdit)
        self.actDelTemplate.setEnabled(enable and userHasRightToDelete)
        self.btnDelTemplate.setEnabled(enable and userHasRightToDelete)

    @pyqtSignature('int')
    def on_cmbCreatePerson_currentIndexChanged(self, index):
        """Обработчик смены индекса в комбобоксе 'Владелец'"""
        db = QtGui.qApp.db
        self._owner = self.cmbCreatePerson.getValue()
        self.cmbSpeciality.blockSignals(True)
        specId = db.translate('vrbPersonWithSpeciality', 'id', self._owner, 'speciality_id')
        if specId:
            self.cmbSpeciality.setValue(specId.toInt()[0])
        else:
            self.cmbSpeciality.setValue(0)
        self.chkSnils.setEnabled(forceBool(self._owner))
        self.cmbSpeciality.blockSignals(False)
        self.modelActionTypeGroups.reloadData()

    @pyqtSignature('int')
    def on_cmbSpeciality_currentIndexChanged(self, index):
        """Обработчик смены индекса в комбобоксе 'Специальность'"""
        self._owner = None
        self._speciality = self.cmbSpeciality.getValue()
        self.cmbCreatePerson.blockSignals(True)
        self.cmbCreatePerson.setValue(self._owner)
        self.cmbCreatePerson.blockSignals(False)
        self.modelActionTypeGroups.reloadData()

    @pyqtSignature('int')
    def on_cmbAccess_currentIndexChanged(self, index):
        """Обработчик смены индекса в комбобоксе 'Доступ'"""
        self._access = None if index == 0 else index - 1
        self.modelActionTypeGroups.reloadData()

    @pyqtSignature('QDate')
    def on_edtBegCreateDate_dateChanged(self, date):
        """Обработчик смены индекса в комбобоксе 'Дата создания с'"""
        self._begDate = self.edtBegCreateDate.date()
        self.modelActionTypeGroups.reloadData()

    @pyqtSignature('QDate')
    def on_edtEndCreateDate_dateChanged(self, index):
        """Обработчик смены индекса в комбобоксе 'Дата создания по'"""
        self._endDate = self.edtEndCreateDate.date()
        self.modelActionTypeGroups.reloadData()

    @pyqtSignature('QString')
    def on_edtNameContains_textChanged(self, string):
        """Обработчик смены индекса в строке 'Наименование содержит'"""
        self._inputTimer.start()

    def _inputTimerExp(self):
        self._searchString = forceStringEx(self.edtNameContains.text())
        self.modelActionTypeGroups.reloadData()
    
    def modelActionTypeGroupsReset(self):
        """Обработчик события сброса модели (используется фильтрами)"""
        resetIndex = self.modelActionTypeGroups.index(0, 0)
        self.tblActionTypeGroups.setCurrentIndex(resetIndex)
        self.on_selectionModelActionTypeGroupsCurrentChanged(resetIndex, None)

    @pyqtSignature('int')
    def on_chkSnils_stateChanged(self, int):
        """Обработчик чекбокса 'Использовать СНИЛС'"""
        self._enSnils = self.chkSnils.isChecked()
        self.modelActionTypeGroups.reloadData()
    
    @pyqtSignature('QModelIndex')
    def on_tblActionTypeGroups_doubleClicked(self, index):
        """Обработчик двойного клика в списке шаблонов действий"""
        self.on_actEditTemplate_triggered()


class CRBActionTypeGroupAppointment(CRBActionTypeGroup):
    _groupType = ACTION_TYPE_GROUP_APPOINTMENT


class CActionTypeGroupsModel(CTableModel):
    """
    Модель данных для таблицы списка шаблонов
    """
    class CLocEnumCol(CEnumCol):
        def format(self, values):
            val = values[0]
            if val.isNull():
                return self.invalid
            return CEnumCol.format(self, values)

    def __init__(self, parent, show_class=True):
        CTableModel.__init__(self, parent)
        self.addColumn(CTextCol(u'Код', ['code'], 20))
        self.addColumn(CTextCol(u'Наименование', ['name'], 20))
        if show_class:
            self.addColumn(
                self.CLocEnumCol(u'Класс', ['class'], [u'статус', u'диагностика', u'лечение', u'прочие мероприятия'], 10)
            )
        self.addColumn(CDesignationCol(u'Автор', ['createPerson_id'], ('vrbPerson', 'name'), 10))
        self.addColumn(CDesignationCol(u'Специальность', ['createPerson_id'], [('Person', 'speciality_id'), ('rbSpeciality', 'name')], 10))
        self.addColumn(CDateCol(u'Дата создания', ['createDatetime'], 10))
        self.addColumn(CEnumCol(u'Доступ', ['availability'], [u'Все', u'Специальность автора', u'Автор'], 12))
        self.loadField('createPerson_id')
        self.setTable('ActionTypeGroup')
        self._loaded = False
        self._class = None
        self._parent = parent

    def deleteRecord(self, table, itemId):
        QtGui.qApp.db.markRecordsDeleted(table, table[self.idFieldName].eq(itemId))
        QtGui.qApp.db.markRecordsDeleted('ActionTypeGroup_Item', 'ActionTypeGroup_Item.master_id=%d' % itemId)

    def loadData(self, class_=None):
        if self._loaded and class_ == self._class:
            return
        self.reloadData(class_)
        self._loaded = True

    def reloadData(self, class_=None):
        """Загрузка данных о шаблонах из БД в соответствии с фильтрами"""
        db = QtGui.qApp.db
        tableAction = db.table('ActionTypeGroup')
        tablePerson = db.table('Person')
        querytable = db.join(tableAction, tablePerson, tableAction['createPerson_id'].eq(tablePerson['id']))
        ownerId = self._parent.getTemplateOwner()
        enableSNILS = self._parent.getEnSnils()
        specialityId = self._parent.getTemplateSpeciality()
        searchString = self._parent.getSearchString()
        cond = tableAction['deleted'].eq(0)
        if ownerId is None:
            if specialityId is not None:
                cond = db.joinAnd([cond, tablePerson['speciality_id'].eq(specialityId)])
        else:
            if enableSNILS:
                ownerSNILS = db.translate(tablePerson, 'id', ownerId, 'SNILS')
                cond = db.joinAnd([cond, tablePerson['SNILS'].eq(ownerSNILS)])
            else:
                cond = db.joinAnd([cond, tableAction['createPerson_id'].eq(ownerId)])
        if self._parent.getTemplateAccess() is not None:
            cond = db.joinAnd([cond, tableAction['availability'].eq(self._parent.getTemplateAccess())])
        if self._parent.getTemplateCreationBegDate().isValid():
            cond = db.joinAnd([cond, tableAction['createDatetime'].ge(self._parent.getTemplateCreationBegDate())])
        if self._parent.getTemplateCreationEndDate().isValid():
            cond = db.joinAnd([cond, tableAction['createDatetime'].le(self._parent.getTemplateCreationEndDate())])
        if searchString:
            cond = db.joinAnd([cond, tableAction['name'].like(addDotsEx(searchString))])
        idList = db.getIdList(querytable, idCol=tableAction['id'], where=cond, order=tableAction['code'].name())
        self.setIdList(idList)


class CActionTypeGroupItemsModel(CTableModel):
    """
    Модель данных для таблицы списка действий в шаблоне
    """
    
    columnShowInForm = 3
    
    class CClassEnum(CDesignationCol):
        class_name_list = [u'статус', u'диагностика', u'лечение', u'прочие мероприятия']
        def format(self, values):
            class_ = forceInt(CDesignationCol.format(self, values))
            return toVariant(self.class_name_list[class_])
        
    class CShowInFormCol(CDesignationCol):
        def format(self, values):
            res = forceBool(CDesignationCol.format(self, values))
            return toVariant(u'Да' if res else u'Нет')
        
    def __init__(self, parent):
        cols = [
            CRefBookCol(u'Код', ['actionType_id'], 'ActionType', 1, showFields=CRBComboBox.showCode),
            CRefBookCol(u'Наименование', ['actionType_id'], 'ActionType', 1, showFields=CRBComboBox.showName),
            self.CClassEnum(u'Класс', ['actionType_id'], ('ActionType', 'class'), 1),
            self.CShowInFormCol(u'Выбор в событии', ['actionType_id'], ('ActionType', 'showInForm'), 20),
        ]
        CTableModel.__init__(self, parent, cols, 'ActionTypeGroup_Item')

    def deleteRecord(self, table, itemId):
        QtGui.qApp.db.markRecordsDeleted(table, table[self.idFieldName].eq(itemId))
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        
        if role == Qt.FontRole:
            row = index.row()
            (col, values) = self.getRecordValues(self.columnShowInForm, row)
            if not col.format(values) == u'Да':
                font = QtGui.QFont()
                font.setItalic(True)
                font.setBold(True)
                return font
        
        return CTableModel.data(self, index, role)
