# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2023 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
##
## Диалог выбора и вставки хронических диагнозов с формах ввода
##
#############################################################################

from PyQt4 import QtGui, QtSql
from PyQt4.QtGui import QStyledItemDelegate
from PyQt4.QtCore import QModelIndex, Qt, QVariant, QRect

from library.DialogBase         import CDialogBase
from library.InDocTable         import CInDocTableCol, CRecordListModel
from library.Utils              import forceRef, forceString
from Events.Ui_EventAddChronicDiseasesDialog import Ui_EventAddChronicDiseasesDialog

class CenteredCheckBoxItem(QStyledItemDelegate):
    """
    Чекбокс по центру ячейки
    Заменяет стандартный чекбокс + текст в ячейке на чекбокс по центру
    Чекбокс нередактируемый, только отображение данных из модели
    """
    def __init__(self, parent):
        super(CenteredCheckBoxItem, self).__init__(parent)

    def paint(self, painter, option, index):
        """
        Рисует чекбокс по центру
        Рисует рамку фокуса в ячейке таблицы
        """
        if not index.isValid():
            return QtGui.QItemDelegate.paint(self, painter, option, index)

        col = index.column()
        if col:
            return QtGui.QItemDelegate.paint(self, painter, option, index)
        else:
            checkBoxStyle = QtGui.QStyleOptionButton()
            centerpoint = option.rect.center()
            checkBoxStyle.rect = QRect(0, 0, 10, 10)
            checkBoxStyle.rect.moveCenter(centerpoint)
            if index.data() == Qt.Checked:
                checkBoxStyle.state = QtGui.QStyle.State_On
            else:
                checkBoxStyle.state = QtGui.QStyle.State_Off
            style = self.parent().style()
            style.drawControl(QtGui.QStyle.CE_CheckBox, checkBoxStyle, painter)

            if index == self.parent().currentIndex():
                focusRectStyle = QtGui.QStyleOptionFocusRect()
                focusRectStyle.rect = option.rect
                style.drawPrimitive(QtGui.QStyle.PE_FrameFocusRect, focusRectStyle, painter)


class CChronicDiseasesLoadDialog(CDialogBase, Ui_EventAddChronicDiseasesDialog):
    """
    Диалог выбора и вставки хронических диагнозов с формах ввода (Блок диагнозов)
    """
    class LocChronicDiseasesLoadModel(CRecordListModel):
        def __init__(self, excludeMKBList, parent):
            super(CChronicDiseasesLoadDialog.LocChronicDiseasesLoadModel, self).__init__(parent)
            self._extColsPresent = False
            self.mapDiseaseCharacterCodeToId = {}
            self._excludeDiagnoses = excludeMKBList
            self.addExtCol(CInDocTableCol(u'Включить', 'Check', 1, **{'readOnly': True}), QVariant.Bool)
            self.addCol(CInDocTableCol(u'Шифр', 'MKB', 10, **{'readOnly': True}))
            self.addCol(CInDocTableCol(u'Установлен', 'setDate', 10, **{'readOnly': True}))
            self.addCol(CInDocTableCol(u'Последнее', 'endDate', 10, **{'readOnly': True}))
            self.addCol(CInDocTableCol(u'Д.Н.', 'dispanser_id', 10, **{'readOnly': True}))
            self.addCol(CInDocTableCol(u'Поставлен на учет', 'dispanserBegDate', 10, **{'readOnly': True}))
            self.addHiddenCol(CInDocTableCol(u'TNM-Ст', 'TNMS', 10, **{'readOnly': True}))
            self.addHiddenCol(CInDocTableCol(u'MKBEx', 'MKBEx', 10, **{'readOnly': True}))
            self.addHiddenCol(CInDocTableCol(u'exSubclassMKB', 'exSubclassMKB', 10, **{'readOnly': True}))
            self.addHiddenCol(CInDocTableCol(u'morphologyMKB', 'morphologyMKB', 10, **{'readOnly': True}))
            self.addHiddenCol(CInDocTableCol(u'character_id', 'character_id', 10, **{'readOnly': True}))
            self.addHiddenCol(CInDocTableCol(u'traumaType_id', 'traumaType_id', 10, **{'readOnly': True}))
            self.addHiddenCol(CInDocTableCol(u'id', 'id', 10, **{'readOnly': True}))

        def loadItems(self, masterId):
            """
            Загрузка хронических диагнозов клиента с id=masterId
            """
            db = QtGui.qApp.db
            cols = []
            diseaseCharacterIdList = []
            for diseaseCharacterCode in [2, 3, 4]:
                diseaseCharacterIdList.append(self.getdiseaseCharacterIdFromCode(diseaseCharacterCode))
            tableDiagnosis = db.table('Diagnosis')
            table = tableDiagnosis
            for col in self._cols:
                if not col.external():
                    cols.append(tableDiagnosis[col.fieldName()])
            for col in self._hiddenCols:
                cols.append(tableDiagnosis[col.fieldName()])
            filter = [table['deleted'].eq(0), table['client_id'].eq(masterId), table['character_id'].inlist(diseaseCharacterIdList), table['MKB'].notInlist(self._excludeDiagnoses)]
            order = tableDiagnosis['endDate'].name() + 'DESC'
            self._items = db.getRecordList(table, cols, filter, order)
            if self._extColsPresent:
                extSqlFields = []
                for col in self._cols:
                    if col.external():
                        fieldName = col.fieldName()
                        if fieldName not in cols:
                            extSqlFields.append(QtSql.QSqlField(fieldName, col.valueType()))
                if extSqlFields:
                    for item in self._items:
                        for field in extSqlFields:
                            item.append(field)
            self.reset()

        def getdiseaseCharacterIdFromCode(self, diseaseCharacterCode):
            """
            Позволяет получить id характера заболевания по его коду из справочника rbDiseaseCharacter
            :param diseaseCharacterCode:
            :return:
            """
            characterId = self.mapDiseaseCharacterCodeToId.get(diseaseCharacterCode)
            if not characterId:
                db = QtGui.qApp.db
                characterId = forceRef(db.translate('rbDiseaseCharacter', 'code', diseaseCharacterCode, 'id'))
                self.mapDiseaseCharacterCodeToId[diseaseCharacterCode] = characterId
            return characterId

    def __init__(self, clientId, diagnosesModel, parent, exclusiveCheck=False):
        super(CChronicDiseasesLoadDialog, self).__init__(parent)
        self._parentDiagnosesModel = diagnosesModel
        excludeMKBList = []
        for item in self._parentDiagnosesModel.items():
            diagnos = forceString(item.value('MKB'))
            if diagnos:
                excludeMKBList.append(diagnos)
        self.addModels('ChronicDiagnoses', self.LocChronicDiseasesLoadModel(excludeMKBList, self))
        self.setupUi(self)
        self.btnSelectAll = self.buttonBox.addButton(u'Выбрать всё', QtGui.QDialogButtonBox.ActionRole) if not exclusiveCheck else None
        self.btnDeSelectAll = self.buttonBox.addButton(u'Очистить выбор', QtGui.QDialogButtonBox.ActionRole)
        self.tblChronicalDiagnoses.setModel(self.modelChronicDiagnoses)
        self.tblChronicalDiagnoses.setSelectionModel(self.selectionModelChronicDiagnoses)
        self.tblChronicalDiagnoses.setItemDelegateForColumn(0, CenteredCheckBoxItem(self.tblChronicalDiagnoses))
        self.tblChronicalDiagnoses.setSelectionMode(QtGui.QAbstractItemView.SingleSelection if exclusiveCheck else QtGui.QAbstractItemView.MultiSelection)
        self.tblChronicalDiagnoses.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.modelChronicDiagnoses.loadItems(clientId)


    def on_selectionModelChronicDiagnoses_selectionChanged(self, selected, deselected):
        """
        Этот обработчик нужен чтобы сбрасывать галочки в колонке Check, если мышью сбросили выделение
        Используется только когда включен режим выбора мышью (QAbstractItemView.SelectionMode != QAbstractItemView.NoSelection)
        :param selected:
        :param deselected:
        :return:
        """
        for rowNum, item in enumerate(self.modelChronicDiagnoses.items()):
            index = self.modelChronicDiagnoses.index(rowNum, 0, QModelIndex())
            value = Qt.Checked if index in self.selectionModelChronicDiagnoses.selectedRows() else Qt.Unchecked
            item.setValue('Check', QVariant(value))


    def on_buttonBox_clicked(self, button):
        """
        Выбор всех элементов, либо снятие выделения
        :param button:
        :return:
        """
        if button in (self.btnSelectAll, self.btnDeSelectAll):
            if button == self.btnSelectAll:
                self.tblChronicalDiagnoses.selectAll()
            if button == self.btnDeSelectAll:
                self.tblChronicalDiagnoses.clearSelection()
