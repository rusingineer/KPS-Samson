# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2019 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
##
## Страница с глобальными настройками
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignature, Qt, QDateTime, QDate, QVariant

from library.TableModel       import CTableModel, CTextCol
from library.Utils import (
    forceString, forceStringEx, forceInt, forceDouble, forceTime
)
from library.LineEditWithRegExpValidator import CLineEditWithRegExpValidator

from Ui_GlobalsPage import Ui_globalsPage
import re


class CGlobalsPage(Ui_globalsPage, QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)
        self.modelGlobalPreferences = CGlobalPreferencesModel(self)
        self.selectionModelGlobalPreferences = QtGui.QItemSelectionModel(self.modelGlobalPreferences, self)
        self.tblGlobal.setModel(self.modelGlobalPreferences)
        self.tblGlobal.setSelectionModel(self.selectionModelGlobalPreferences)
        self.tblGlobal.setSortingEnabled(True)


    def setProps(self, props):
        self.refreshGlobalPreferences()


    def getProps(self, props):
        pass


    def refreshGlobalPreferences(self):
        self.modelGlobalPreferences.setIdList(QtGui.qApp.db.getIdList('GlobalPreferences'))


    @pyqtSignature('QModelIndex')
    def on_tblGlobal_doubleClicked(self, index):
        if QtGui.qApp.userHasAnyRight(['adm', 'setupGlobalPreferencesEdit']):
            item = self.tblGlobal.currentItem()
            currentValue = forceString(item.value('value'))
            note = forceString(item.value('note'))
            code = forceString(item.value('code'))
            if code == u'numberDecimalPlacesQnt':
                currentValue = forceInt(item.value('value'))
                newValue, ok = QtGui.QInputDialog.getInt(self,
                                                         u'Редактор',
                                                         u'Значение\n' + note,
                                                         value=currentValue, min=0, max=6, step=1)
            elif code == u'minQntConsumableUnitsStock':  # Минимальное количество ЛСиИМН в расходных единицах
                currentValue = forceDouble(item.value('value'))
                newValue, ok = QtGui.QInputDialog.getDouble(self,
                                            u'Редактор',
                                            u'Значение\n' + note,
                                            value=currentValue, decimals=QtGui.qApp.numberDecimalPlacesQnt())
            elif code == u'createStockResidualQuantityAuto':  # Создание документа в автоматическом режиме "Списание остаточных количеств ЛСиИМН"
                currentValue = forceStringEx(item.value('value'))
                newValue, ok = getRegExpInput(self,
                                            u'Редактор',
                                            u'''Создание документа "Списание остаточных количеств ЛСиИМН" в автоматическом режиме\n''' + note,
                                            value=currentValue)
            else:
                values = [y.replace("\"", '') for y in re.findall('\".*?\"', note)]
                if len(values) > 1:
                    if currentValue == u'жесткий':
                        currentValue.replace(u"е", u"ё")
                    ind = values.index(currentValue)
                    newValue, ok = QtGui.QInputDialog.getItem(self,
                                                              u'Редактор',
                                                              u'Значение\n' + note,
                                                              values,
                                                              ind,
                                                              False)
                else:
                    newValue, ok = QtGui.QInputDialog.getText(self,
                                                              u'Редактор',
                                                              u'Значение\n' + note,
                                                              QtGui.QLineEdit.Normal,
                                                              currentValue)
            if ok and unicode(newValue) != unicode(currentValue):
                item.setValue('value', newValue)
                recordId = QtGui.qApp.db.updateRecord('GlobalPreferences', item)
                self.refreshGlobalPreferences()
                if code == u'createStockResidualQuantityAuto' and recordId:
                    db = QtGui.qApp.db
                    tableGP = db.table('GlobalPreferences')
                    stmt = '''DROP EVENT IF EXISTS `evtCreateDocStockResidualQuantityAuto`'''
                    db.query(stmt)
                    vCreateStockQuantyAuto = 0
                    vQuantyRepeat = 24*60*60*365
                    vBegDateTime = QDateTime.currentDateTime()
                    recordGP = db.getRecordEx(tableGP, '*', [tableGP['id'].eq(recordId)])
                    if recordGP:
                        vValue = forceStringEx(recordGP.value('value'))
                        valueList = vValue.split(u'/')
                        if len(valueList) == 2:
                            vBegTime = valueList[0]
                            if vBegTime:
                                vBegDateTime = QDateTime(QDate.currentDate(), forceTime(QTime.fromString(vBegTime, 'hh:mm')))
                                vQuantyRepeatStr = valueList[1]
                                quantyRepeatVar = QVariant(vQuantyRepeatStr)
                                quantyRepeat = quantyRepeatVar.toInt()[0]
                                if quantyRepeat == 0:
                                    quantyRepeat = 1
                                vQuantyRepeat = (24*60*60)/quantyRepeat
                                vCreateStockQuantyAuto = 1
                                stmt = '''CREATE
                                            DEFINER=CURRENT_USER
                                            EVENT `evtCreateDocStockResidualQuantityAuto`
                                            ON SCHEDULE EVERY %s SECOND STARTS %s
                                            ON COMPLETION PRESERVE
                                            %s
                                            COMMENT '%s' DO
                                            BEGIN
                                                SELECT createDocStockResidualQuantityAuto(%d)
                                            END;
                                          END'''%(str(vQuantyRepeat), db.formatDate(vBegDateTime), u'ENABLE' if vCreateStockQuantyAuto else u'DISABLE', u'''Создание документа в автоматическом режиме "Списание остаточных количеств ЛСиИМН" ''', vCreateStockQuantyAuto)
                                db.query(stmt)


# ########################################################


class CGlobalPreferencesModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.addColumn(CTextCol(u'Код', ['code'], 10))
        self.addColumn(CTextCol(u'Наименование', ['name'], 18))
        self.addColumn(CTextCol(u'Значение', ['value'], 10))
        self.loadField('note')
        self.setTable('GlobalPreferences')
    
    
    def sort(self, col, order=Qt.AscendingOrder):
        reverse = order == Qt.DescendingOrder
        if self._idList:
            db = QtGui.qApp.db
            table = db.table('GlobalPreferences')
            colClass = self.cols()[col]
            colName = colClass.fields()[0]
            order = '{} {}'.format(colName, u'DESC' if order else u'ASC')
            self._idList = db.getIdList(table, order=order)
            self.reset()

class CInputDialog(QtGui.QDialog):
    def __init__(self, parent, widget, message=''):
        QtGui.QDialog.__init__(self, parent)
        self.widget = widget
        buttonBox = QtGui.QDialogButtonBox()
        buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok|QtGui.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        label = QtGui.QLabel(message)
        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(self.widget)
        layout.addStretch()
        layout.addWidget(buttonBox)


def getRegExpInput(parent, title, label, value):
    dialog = CInputDialog(parent, CLineEditWithRegExpValidator(parent), label)
    dialog.setWindowTitle(title)
#    dialog.widget.setInputMask('^[0-2]{1}[0-9]{1}:[0-5]{1}[0-9]{1}/[1-6]$')
    dialog.widget.setRegExp('^[0-2]{1}[0-9]{1}:[0-5]{1}[0-9]{1}/[1-6]$')
    dialog.widget.setText(forceStringEx(value))
    if dialog.exec_():
        return dialog.widget.text(), True
    return '', False
