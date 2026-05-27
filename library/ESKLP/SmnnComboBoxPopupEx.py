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

from library.database   import CTableRecordCacheEx
from library.TableModel import CTableModel, CTextCol
from library.DialogBase import CConstructHelperMixin
from library.SortFilterProxyTableModel import CSortFilterProxyTableModel
from library.Utils      import getPref, setPref, addDots, forceStringEx
from Stock.Utils        import getExistsNomenclatureIdList

from library.ESKLP.Ui_SmnnComboBoxPopupEx import Ui_SmnnComboBoxPopupEx

__all__ = [ 'CSmnnComboBoxPopupEx',
          ]


class CSmnnComboBoxPopupEx(QtGui.QFrame, Ui_SmnnComboBoxPopupEx, CConstructHelperMixin):
    __pyqtSignals__ = ('smnnUUIDSelected(QString)'
                      )

    def __init__(self, parent = None):
        QtGui.QFrame.__init__(self, parent, Qt.Popup)
        self.setAttribute(Qt.WA_WindowPropagation)
#        self.tableModel = CSmnnTableModel(self)
#        self.tableSelectionModel = QtGui.QItemSelectionModel(self.tableModel, self)
#        self.tableSelectionModel.setObjectName('tableSelectionModel')
        self.addModels('', CSmnnTableModel(self))
        self.addModels('SmnnSortModel', CSortFilterProxyTableModel(self, self.model))
        self.model = self.modelSmnnSortModel.sourceModel()
#        self.tableSelectionModel = QtGui.QItemSelectionModel(self.model, self)
#        self.tableSelectionModel.setObjectName('tableSelectionModel')
        self.setupUi(self)
#        self.tblSmnn.setModel(self.model)
#        self.tblSmnn.setSelectionModel(self.tableSelectionModel)
        self.setModels(self.tblSmnn, self.modelSmnnSortModel, self.selectionModelSmnnSortModel)
#        self.buttonBox.button(QtGui.QDialogButtonBox.Apply).setDefault(True)
#        self.buttonBox.button(QtGui.QDialogButtonBox.Apply).setShortcut(Qt.Key_Return)
        self.UUID = None
        self.nomenclatureId = None
        self.financeId = None
        self.nomenclatureIdList = []
        self.orgStructureId = None
        self.defaultOnlyExists = False
        self.tblSmnn.installEventFilter(self)
        preferences = getPref(QtGui.qApp.preferences.windowPrefs, 'CSmnnComboBoxPopupEx', {})
        self.tblSmnn.loadPreferences(preferences)
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
        preferences = self.tblSmnn.savePreferences()
        setPref(QtGui.qApp.preferences.windowPrefs, 'CSmnnComboBoxPopupEx', preferences)
        QtGui.QFrame.closeEvent(self, event)


    def eventFilter(self, watched, event):
        if watched == self.tblSmnn:
            if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Select):
                event.accept()
                index = self.tblSmnn.currentIndex()
                self.tblSmnn.emit(SIGNAL('doubleClicked(QModelIndex)'), index)
                return True
        return QtGui.QFrame.eventFilter(self, watched, event)


    def setOnlyExistsEnabled(self, value=True):
        self.chkOnlyExists.setEnabled(value)


    def setOnlyExists(self, value):
        self.defaultOnlyExists = value
        self.chkOnlyExists.setChecked(value)


    def setFinanceId(self, value):
        self.financeId = value


    @pyqtSignature('QString')
    def on_edtFindName_textChanged(self, text):
        if text.isEmpty():
            self.modelSmnnSortModel.removeFilter('mnn')
        else:
            self.modelSmnnSortModel.setFilter('mnn', text, CSortFilterProxyTableModel.MatchContains)


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
        self.edtFindName.setText('')
        self.chkOnlyExists.setChecked(self.defaultOnlyExists)


    def on_buttonBox_apply(self):
        QtGui.qApp.setWaitCursor()
        try:
            findName = forceStringEx(self.edtFindName.text())
            crIdList = self.getUUIDList(findName)
            self.setUUIDList(crIdList, self.UUID)
        finally:
            QtGui.qApp.restoreOverrideCursor()


    def setUUID(self, UUID):
        self.UUID = UUID


    def setNomenclatureId(self, nomenclatureId):
        self.nomenclatureId = nomenclatureId


    def setNomenclatureIdList(self, nomenclatureIdList):
        self.nomenclatureIdList = nomenclatureIdList


    def setUUIDList(self, idList, posToId):
        self.tblSmnn.setIdList(idList, posToId)
        self.tblSmnn.setFocus(Qt.OtherFocusReason)
        if not idList:
            self.edtFindName.setFocus(Qt.OtherFocusReason)


    def setOrgStructureId(self, value):
        self.orgStructureId = value


    def getUUIDList(self, findName):
        db = QtGui.qApp.db
        tableEsklp_Smnn = db.table('esklp.Smnn')
        tableNC = db.table('rbNomenclature')
        tableESKLP_Klp = db.table('esklp.Klp')
        queryTable = tableNC.innerJoin(tableESKLP_Klp, tableESKLP_Klp['UUID'].eq(tableNC['esklpUUID']))
        queryTable = queryTable.innerJoin(tableEsklp_Smnn, tableEsklp_Smnn['id'].eq(tableESKLP_Klp['smnn_id']))
        cond = []
        findNomenclatureIdList = []
        order = u'esklp.Smnn.code, esklp.Smnn.mnn, esklp.Smnn.form'
        if self.nomenclatureId:
            cond.append(tableNC['id'].eq(self.nomenclatureId))
            findNomenclatureIdList = [self.nomenclatureId]
        if self.nomenclatureIdList:
            cond.append(tableNC['id'].inlist(self.nomenclatureIdList))
            findNomenclatureIdList = self.nomenclatureIdList
        if self.chkOnlyExists.isChecked():
            existsIdList = getExistsNomenclatureIdList(self.orgStructureId, nomenclatureIdList = findNomenclatureIdList)
            cond.append(tableNC['id'].inlist(existsIdList))
        if findName:
            cond.append(db.joinOr([tableEsklp_Smnn['code'].like(addDots(findName)), tableEsklp_Smnn['mnn'].like(addDots(findName)), tableEsklp_Smnn['form'].like(addDots(findName))]))
        idList = []
        records = db.getDistinctRecordList(queryTable, [tableEsklp_Smnn['UUID']], cond, order=order, limit=1000)
        for record in records:
            UUID = forceStringEx(record.value('UUID'))
            if UUID and UUID not in idList:
                idList.append(UUID)
        return idList


    def selectSmnnCode(self, UUID):
        self.UUID = UUID
        self.emit(SIGNAL('smnnUUIDSelected(QString)'), self.UUID)
        self.close()


    @pyqtSignature('QModelIndex')
    def on_tblSmnn_doubleClicked(self, index):
        if index.isValid():
            if (Qt.ItemIsEnabled & self.model.flags(index)):
                curIndex = self.tblSmnn.currentIndex()
                if curIndex.isValid():
                    sourceRow = self.modelSmnnSortModel.mapToSource(curIndex).row()
                    UUID = forceStringEx(self.tblSmnn.model().getRecordByRow(sourceRow).value('UUID'))
                    #UUID = self.tblSmnn.currentItemId()
                    self.selectSmnnCode(UUID)


class CSmnnTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.addColumn(CTextCol(u'Код', ['code'], 30))
        self.addColumn(CTextCol(u'МНН', ['mnn'], 30))
        self.addColumn(CTextCol(u'Лекарственная форма',  ['form'], 30))
        self.setTable('esklp.Smnn')


    def flags(self, index):
        return Qt.ItemIsEnabled|Qt.ItemIsSelectable


    def setTable(self, tableName):
        db = QtGui.qApp.db
        tableEsklp_Smnn = db.table('esklp.Smnn')
        loadFields = [u'''DISTINCT esklp.Smnn.id, esklp.Smnn.code, esklp.Smnn.mnn, esklp.Smnn.form, esklp.Smnn.UUID''']
        self._table = tableEsklp_Smnn
        self._recordsCache = CTableRecordCacheEx(db, self._table, loadFields, idFieldName = 'UUID')


