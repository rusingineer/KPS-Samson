# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2020 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################


from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QEvent, pyqtSignature, SIGNAL, QRegExp

from library.database   import CTableRecordCache
from library.TableModel import CTableModel, CTextCol
from library.Utils      import forceInt, getPref, setPref, addDots, forceStringEx

from RefBooks.NomenclatureActiveSubstance.Ui_ActiveSubstanceComboBoxPopup import Ui_ActiveSubstanceComboBoxPopup

__all__ = [ 'CActiveSubstanceComboBoxPopup',
          ]


class CActiveSubstanceComboBoxPopup(QtGui.QFrame, Ui_ActiveSubstanceComboBoxPopup):
    __pyqtSignals__ = ('activeSubstanceIdSelected(int)'
                      )

    def __init__(self, parent = None):
        QtGui.QFrame.__init__(self, parent, Qt.Popup)
        #self.setFrameShape(QtGui.QFrame.StyledPanel)
        self.setAttribute(Qt.WA_WindowPropagation)
        self.tableModel = CActiveSubstanceTableModel(self)
        self.tableSelectionModel = QtGui.QItemSelectionModel(self.tableModel, self)
        self.tableSelectionModel.setObjectName('tableSelectionModel')
        self.setupUi(self)
        self.tblActiveSubstance.setModel(self.tableModel)
        self.tblActiveSubstance.setSelectionModel(self.tableSelectionModel)
        self.buttonBox.button(QtGui.QDialogButtonBox.Apply).setDefault(True)
        self.buttonBox.button(QtGui.QDialogButtonBox.Apply).setShortcut(Qt.Key_Return)
        self.activeSubstanceId = None
        self.nomenclatureId = None
        self.tblActiveSubstance.installEventFilter(self)
        preferences = getPref(QtGui.qApp.preferences.windowPrefs, 'CActiveSubstanceComboBoxPopup', {})
        self.tblActiveSubstance.loadPreferences(preferences)
        rX = QRegExp(u"[-?!,.А-Яа-яёЁA-Za-z\\d\\s]+")
        self.edtFindName.setValidator(QtGui.QRegExpValidator(rX, self))


    def mousePressEvent(self, event):
        parent = self.parentWidget()
        if parent!=None:
            opt=QtGui.QStyleOptionComboBox()
            opt.init(parent)
            arrowRect = parent.style().subControlRect(
                QtGui.QStyle.CC_ComboBox, opt, QtGui.QStyle.SC_ComboBoxArrow, parent)
            arrowRect.moveTo(parent.mapToGlobal(arrowRect.topLeft()))
            if (arrowRect.contains(event.globalPos()) or self.rect().contains(event.pos())):
                self.setAttribute(Qt.WA_NoMouseReplay)
        QtGui.QFrame.mousePressEvent(self, event)


    def closeEvent(self, event):
        preferences = self.tblActiveSubstance.savePreferences()
        setPref(QtGui.qApp.preferences.windowPrefs, 'CActiveSubstanceComboBoxPopup', preferences)
        QtGui.QFrame.closeEvent(self, event)


    def eventFilter(self, watched, event):
        if watched == self.tblActiveSubstance:
            if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Select):
                event.accept()
                index = self.tblActiveSubstance.currentIndex()
                self.tblActiveSubstance.emit(SIGNAL('doubleClicked(QModelIndex)'), index)
                return True
        return QtGui.QFrame.eventFilter(self, watched, event)


    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_buttonBox_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_buttonBox_reset()


    def on_buttonBox_reset(self):
        self.edtFindName.setText('')


    def on_buttonBox_apply(self):
        QtGui.qApp.setWaitCursor()
        try:
            findName = forceStringEx(self.edtFindName.text())
            crIdList = self.getActiveSubstanceIdList(findName)
            self.setActiveSubstanceIdList(crIdList, None)
        finally:
            QtGui.qApp.restoreOverrideCursor()


    def setNomenclatureId(self, nomenclatureId):
        self.nomenclatureId = nomenclatureId


    def setActiveSubstanceIdList(self, idList, posToId):
        if idList:
            self.tblActiveSubstance.setIdList(idList, posToId)
            self.tblActiveSubstance.setFocus(Qt.OtherFocusReason)
        else:
            self.edtFindName.setFocus(Qt.OtherFocusReason)


    def getActiveSubstanceIdList(self, findName):
        db = QtGui.qApp.db
        table = db.table('rbNomenclatureActiveSubstance')
        cond = []
        compositionIdList = []
        order = u'code, name, mnnLatin'
        if self.nomenclatureId:
           tableNC = db.table('rbNomenclature_Composition')
           compositionIdList = db.getDistinctIdList(tableNC, tableNC['activeSubstance_id'], [tableNC['master_id'].eq(self.nomenclatureId), tableNC['type'].eq(0)])
        if compositionIdList:
            cond.append(table['id'].inlist(compositionIdList))
        if findName:
            cond.append(db.joinOr([table['name'].like(addDots(findName)), table['mnnLatin'].like(addDots(findName))]))
        idList = db.getDistinctIdList(table, table['id'].name(),
                              where=cond,
                              order=order,
                              limit=1000)
        return idList


    def setActiveSubstanceId(self, activeSubstanceId):
        db = QtGui.qApp.db
        table = db.table('rbNomenclatureActiveSubstance')
        self.activeSubstanceId = activeSubstanceId
        idList = []
        id = None
        if self.activeSubstanceId:
            record = db.getRecordEx(table, [table['id']], [table['id'].eq(self.activeSubstanceId)])
            id = forceInt(record.value(0)) if record else None
            if id:
                idList = [id]
        self.setActiveSubstanceIdList(idList, id)


    def selectActiveSubstanceCode(self, activeSubstanceId):
        self.activeSubstanceId = activeSubstanceId
        self.emit(SIGNAL('activeSubstanceIdSelected(int)'), self.activeSubstanceId)
        self.close()


    def getCurrentActiveSubstanceId(self):
        db = QtGui.qApp.db
        table = db.table('rbNomenclatureActiveSubstance')
        id = self.tblActiveSubstance.currentItemId()
        if id:
            record = db.getRecordEx(table, [table['id']], [table['id'].eq(id)])
            if record:
                return forceInt(record.value(0))
        return None


    @pyqtSignature('QModelIndex')
    def on_tblActiveSubstance_doubleClicked(self, index):
        if index.isValid():
            if (Qt.ItemIsEnabled & self.tableModel.flags(index)):
                activeSubstanceId = self.getCurrentActiveSubstanceId()
                self.selectActiveSubstanceCode(activeSubstanceId)


class CActiveSubstanceTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.addColumn(CTextCol(u'Код', ['code'], 30))
        self.addColumn(CTextCol(u'Наименование на русском', ['name'], 30))
        self.addColumn(CTextCol(u'Наименование на латыни',  ['mnnLatin'], 30))
        self.setTable('rbNomenclatureActiveSubstance')


    def flags(self, index):
        return Qt.ItemIsEnabled|Qt.ItemIsSelectable


    def setTable(self, tableName):
        db = QtGui.qApp.db
        table = db.table('rbNomenclatureActiveSubstance')
        loadFields = []
        loadFields.append(u'''DISTINCT id, code, name, mnnLatin''')
        self._table = table
        self._recordsCache = CTableRecordCache(db, self._table, loadFields)

