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
from PyQt4.QtCore import Qt, QEvent, pyqtSignature, SIGNAL

from library.database   import CTableRecordCacheEx
from library.TableModel import CTableModel, CTextCol
from library.Utils      import getPref, setPref, forceRef
from Stock.Utils        import getExistsNomenclatureIdList

from library.ESKLP.Ui_SmnnGrlsLfComboBoxPopupEx import Ui_SmnnGrlsLfComboBoxPopupEx

__all__ = [ 'CSmnnGrlsLfComboBoxPopupEx',
          ]


class CSmnnGrlsLfComboBoxPopupEx(QtGui.QFrame, Ui_SmnnGrlsLfComboBoxPopupEx):
    __pyqtSignals__ = ('smnnLfFormIdSelected(int)'
                      )

    def __init__(self, parent = None):
        QtGui.QFrame.__init__(self, parent, Qt.Popup)
        self.setAttribute(Qt.WA_WindowPropagation)
        self.tableModel = CSmnnGrlsLfTableModel(self)
        self.tableSelectionModel = QtGui.QItemSelectionModel(self.tableModel, self)
        self.tableSelectionModel.setObjectName('tableSelectionModel')
        self.setupUi(self)
        self.tblSmnn.setModel(self.tableModel)
        self.tblSmnn.setSelectionModel(self.tableSelectionModel)
#        self.buttonBox.button(QtGui.QDialogButtonBox.Apply).setDefault(True)
#        self.buttonBox.button(QtGui.QDialogButtonBox.Apply).setShortcut(Qt.Key_Return)
        self.lfFormId = None
        self.nomenclatureId = None
        self.financeId = None
        self.nomenclatureIdList = []
        self._smnnUUID = None
        self._isOnlySmnnUUID = False
        self.orgStructureId = None
        self.defaultOnlyExists = False
        self.tblSmnn.installEventFilter(self)
        preferences = getPref(QtGui.qApp.preferences.windowPrefs, 'CSmnnGrlsLfComboBoxPopupEx', {})
        self.tblSmnn.loadPreferences(preferences)


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
        preferences = self.tblSmnn.savePreferences()
        setPref(QtGui.qApp.preferences.windowPrefs, 'CSmnnGrlsLfComboBoxPopupEx', preferences)
        QtGui.QFrame.closeEvent(self, event)


    def eventFilter(self, watched, event):
        if watched == self.tblSmnn:
            if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Select):
                event.accept()
                index = self.tblSmnn.currentIndex()
                self.tblSmnn.emit(SIGNAL('doubleClicked(QModelIndex)'), index)
                return True
        return QtGui.QFrame.eventFilter(self, watched, event)


    def setOnlyExists(self, value):
        self.defaultOnlyExists = value
        self.chkOnlyExists.setChecked(value)


    def setFinanceId(self, value):
        self.financeId = value


    def setOnlyExistsEnabled(self, value=True):
        self.chkOnlyExists.setEnabled(value)


    @pyqtSignature('bool')
    def on_chkOnlyExists_toggled(self, value):
        self.on_buttonBox_apply()


#    @pyqtSignature('QAbstractButton*')
#    def on_buttonBox_clicked(self, button):
#        buttonCode = self.buttonBox.standardButton(button)
#        if buttonCode == QtGui.QDialogButtonBox.Apply:
#            self.on_buttonBox_apply()
#        elif buttonCode == QtGui.QDialogButtonBox.Reset:
#            self.on_buttonBox_reset()


    def on_buttonBox_reset(self):
        self.chkOnlyExists.setChecked(self.defaultOnlyExists)


    def on_buttonBox_apply(self):
        QtGui.qApp.setWaitCursor()
        try:
            crIdList = self.getLfFormIdList()
            self.setLfFormIdList(crIdList, self.lfFormId)
        finally:
            QtGui.qApp.restoreOverrideCursor()


    def setOnlySmnnUUID(self, value):
        self._isOnlySmnnUUID = value


    def setLfFormId(self, lfFormId):
        self.lfFormId = lfFormId


    def setNomenclatureId(self, nomenclatureId):
        self.nomenclatureId = nomenclatureId


    def setNomenclatureIdList(self, nomenclatureIdList):
        self.nomenclatureIdList = nomenclatureIdList


    def setNomenclatureSmnnUUID(self, smnnUUID):
        self._smnnUUID = smnnUUID


    def setLfFormIdList(self, idList, posToId):
        self.tblSmnn.setIdList(idList, posToId)
        self.tblSmnn.setFocus(Qt.OtherFocusReason)


    def setOrgStructureId(self, value):
        self.orgStructureId = value


    def getLfFormIdList(self):
        db = QtGui.qApp.db
        tableLfForm= db.table('rbLfForm')
        tableNC = db.table('rbNomenclature')
        tableESKLP_Klp = db.table('esklp.Klp')
        tableEsklp_SmnnGrlsLf = db.table('esklp.Smnn_GrlsLf')
        queryTable = tableNC.innerJoin(tableESKLP_Klp, tableESKLP_Klp['UUID'].eq(tableNC['esklpUUID']))
        queryTable = queryTable.innerJoin(tableEsklp_SmnnGrlsLf, tableEsklp_SmnnGrlsLf['master_id'].eq(tableESKLP_Klp['smnn_id']))
        queryTable = queryTable.innerJoin(tableLfForm, db.joinAnd([tableLfForm['name'].eq(tableEsklp_SmnnGrlsLf['lf_name']), tableLfForm['dosage'].eq(tableEsklp_SmnnGrlsLf['dosage_name'])]))
        cond = [tableLfForm['isESKLP'].eq(1)]
        findNomenclatureIdList = []
        order = u'esklp.Smnn_GrlsLf.lf_name, esklp.Smnn_GrlsLf.dosage_name'
        if self.nomenclatureId:
            cond.append(tableNC['id'].eq(self.nomenclatureId))
            findNomenclatureIdList = [self.nomenclatureId]
        if self.nomenclatureIdList:
            cond.append(tableNC['id'].inlist(self.nomenclatureIdList))
            findNomenclatureIdList = self.nomenclatureIdList
        if self._smnnUUID:
            tableEsklp_Smnn = db.table('esklp.Smnn')
            queryTable = queryTable.innerJoin(tableEsklp_Smnn, tableEsklp_Smnn['id'].eq(tableESKLP_Klp['smnn_id']))
            cond.append(tableEsklp_Smnn['UUID'].eq(self._smnnUUID))
        if self.nomenclatureId or self._smnnUUID or self.nomenclatureIdList:
            cond.append(tableLfForm['name'].eq(tableESKLP_Klp['lf_norm_name']))
            cond.append(tableLfForm['dosage'].eq(tableESKLP_Klp['dosage_norm_name']))
        elif self._isOnlySmnnUUID:
            return []
        if self.chkOnlyExists.isChecked():
            existsIdList = getExistsNomenclatureIdList(self.orgStructureId, nomenclatureIdList = findNomenclatureIdList)
            cond.append(tableNC['id'].inlist(existsIdList))
        idList = []
        records = db.getDistinctRecordList(queryTable, [tableLfForm['id']], cond, order=order, limit=1000)
        for record in records:
            lfFormId = forceRef(record.value('id'))
            if lfFormId and lfFormId not in idList:
                idList.append(lfFormId)
        return idList


    def selectSmnnCode(self, lfFormId):
        self.lfFormId = lfFormId
        self.emit(SIGNAL('smnnLfFormIdSelected(int)'), self.lfFormId)
        self.close()


    @pyqtSignature('QModelIndex')
    def on_tblSmnn_doubleClicked(self, index):
        if index.isValid():
            if (Qt.ItemIsEnabled & self.tableModel.flags(index)):
                lfFormId = self.tblSmnn.currentItemId()
                self.selectSmnnCode(lfFormId)


class CSmnnGrlsLfTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.addColumn(CTextCol(u'Наименование', ['name'], 30))
        self.addColumn(CTextCol(u'Дозировка', ['dosage'], 30))
        self.setTable('rbLfForm')


    def flags(self, index):
        return Qt.ItemIsEnabled|Qt.ItemIsSelectable


    def setTable(self, tableName):
        db = QtGui.qApp.db
        table = db.table('rbLfForm')
        loadFields = [u'''DISTINCT rbLfForm.id, rbLfForm.name, rbLfForm.dosage''']
        self._table = table
        self._recordsCache = CTableRecordCacheEx(db, self._table, loadFields, idFieldName = 'id')


