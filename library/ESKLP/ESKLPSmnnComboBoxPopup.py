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

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QEvent, pyqtSignature, SIGNAL, QDateTime

from library.database import CTableRecordCacheEx
from library.TableModel import CTableModel, CTextCol, CCol, CEnumCol
from library.Utils import toVariant, forceStringEx, forceInt, setPref, getPref, addDotsEx

from Ui_ESKLPSmnnComboBoxPopup import Ui_ESKLPSmnnComboBoxPopup

__all__ = ['CESKLPSmnnComboBoxPopup',
           ]


class CESKLPSmnnComboBoxPopup(QtGui.QFrame, Ui_ESKLPSmnnComboBoxPopup):
    __pyqtSignals__ = ('ESKLPSmnnUUIDSelected(QString)'
                       )

    def __init__(self, parent=None):
        QtGui.QFrame.__init__(self, parent, Qt.Popup)
        self.setFrameShape(QtGui.QFrame.StyledPanel)
        self.setAttribute(Qt.WA_WindowPropagation)
        self.tableModel = CESKLPTableModel(self)
        self.tableSelectionModel = QtGui.QItemSelectionModel(self.tableModel, self)
        self.tableSelectionModel.setObjectName('tableSelectionModel')
        self.setupUi(self)
        self.tblESKLPSmnn.setModel(self.tableModel)
        self.tblESKLPSmnn.setSelectionModel(self.tableSelectionModel)
        self.tblESKLPSmnn.installEventFilter(self)
        preferences = getPref(QtGui.qApp.preferences.windowPrefs, 'CESKLPSmnnComboBoxPopup', {})
        self.tblESKLPSmnn.loadPreferences(preferences)
        if not preferences:
            self.resizeESKLPSmnnHeader()
        self.buttonBox.button(QtGui.QDialogButtonBox.Apply).setDefault(True)
        self.buttonBox.button(QtGui.QDialogButtonBox.Apply).setShortcut(Qt.Key_Return)
        self.UUID = None
        self.dialogInfo = {}

    def resizeESKLPSmnnHeader(self):
        for column in range(self.tblESKLPSmnn.horizontalHeader().count()):
            text = self.tableModel.headerData(column, orientation=Qt.Horizontal, role=Qt.DisplayRole).toString()
            fm = QtGui.QFontMetrics(QtGui.QFont(text))
            width = fm.width(text)
            self.tblESKLPSmnn.horizontalHeader().resizeSection(column, width)

    def mousePressEvent(self, event):
        parent = self.parentWidget()
        if parent is not None:
            opt = QtGui.QStyleOptionComboBox()
            opt.init(parent)
            arrowRect = parent.style().subControlRect(
                QtGui.QStyle.CC_ComboBox, opt, QtGui.QStyle.SC_ComboBoxArrow, parent)
            arrowRect.moveTo(parent.mapToGlobal(arrowRect.topLeft()))
            if arrowRect.contains(event.globalPos()) or self.rect().contains(event.pos()):
                self.setAttribute(Qt.WA_NoMouseReplay)
        QtGui.QFrame.mousePressEvent(self, event)

    def closeEvent(self, event):
        preferences = self.tblESKLPSmnn.savePreferences()
        setPref(QtGui.qApp.preferences.windowPrefs, 'CESKLPSmnnComboBoxPopup', preferences)
        QtGui.QFrame.closeEvent(self, event)

    def eventFilter(self, watched, event):
        if watched == self.tblESKLPSmnn:
            if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Select):
                event.accept()
                index = self.tblESKLPSmnn.currentIndex()
                self.tblESKLPSmnn.emit(SIGNAL('doubleClicked(QModelIndex)'), index)
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
        self.edtESKLPSmnnCode.setText(u'')
        self.edtESKLPSmnn_mnn.setText(u'')
        self.edtESKLPSmnn_form.setText(u'')
        self.edtESKLPSmnn_ftg.setText(u'')
        self.edtESKLPSmnn_trade_name.setText(u'')
        self.cmbESKLPSmnn_is_znvlp.setCurrentIndex(0)
        self.cmbESKLPSmnn_is_narcotic.setCurrentIndex(0)
        self.edtESKLPSmnn_Dosage_grls_value.setText(u'')
        self.getParamsDialogFilter()

    def on_buttonBox_apply(self):
        self.setESKLPPopupUpdate(self.UUID)

    def checkParamsDialogFilter(self):
        defaults = {
            'ESKLPSmnnCode': u'',
            'ESKLPSmnn_mnn': u'',
            'ESKLPSmnn_form': u'',
            'ESKLPSmnn_trade_name': u'',
            'ESKLPSmnn_ftg': u'',
            'ESKLPSmnn_is_znvlp': 0,
            'ESKLPSmnn_is_narcotic': 0,
            'ESKLPSmnn_Dosage_grls_value': u'',
        }
        hasAnyValue = any(
            self.dialogInfo.get(field, default)
            for field, default in defaults.items()
        )
        return hasAnyValue

    def getParamsDialogFilter(self):
        self.dialogInfo = {'ESKLPSmnnCode': forceStringEx(self.edtESKLPSmnnCode.text()),
                           'ESKLPSmnn_mnn': forceStringEx(self.edtESKLPSmnn_mnn.text()),
                           'ESKLPSmnn_form': forceStringEx(self.edtESKLPSmnn_form.text()),
                           'ESKLPSmnn_trade_name': forceStringEx(self.edtESKLPSmnn_trade_name.text()),
                           'ESKLPSmnn_ftg': forceStringEx(self.edtESKLPSmnn_ftg.text()),
                           'ESKLPSmnn_is_znvlp': forceInt(self.cmbESKLPSmnn_is_znvlp.currentIndex()),
                           'ESKLPSmnn_is_narcotic': forceInt(self.cmbESKLPSmnn_is_narcotic.currentIndex()),
                           'ESKLPSmnn_Dosage_grls_value': forceStringEx(self.edtESKLPSmnn_Dosage_grls_value.text())}

    def setESKLPIdList(self, idList, posToId):
        self.tblESKLPSmnn.setIdList(idList, posToId)
        if idList:
            self.tabWidget.setCurrentIndex(0)
            self.tabWidget.setTabEnabled(0, True)
            self.tblESKLPSmnn.setFocus(Qt.OtherFocusReason)
        else:
            self.tabWidget.setCurrentIndex(1)
            self.tabWidget.setTabEnabled(0, False)
            widgetHasFocus = self.getWidgetHasFocus()
            if widgetHasFocus:
                widgetHasFocus.setFocus(Qt.OtherFocusReason)
            else:
                self.edtESKLPSmnnCode.setFocus(Qt.OtherFocusReason)

    def getESKLPIdList(self):
        db = QtGui.qApp.db
        tableEsklp_Smnn = db.table('esklp.Smnn')
        tableESKLP_Smnn_Dosage = db.table('esklp.Smnn_Dosage')
        queryTable = tableEsklp_Smnn.innerJoin(tableESKLP_Smnn_Dosage,
                                               tableESKLP_Smnn_Dosage['master_id'].eq(tableEsklp_Smnn['id']))
        ESKLPSmnnCode = self.dialogInfo.get('ESKLPSmnnCode', u'')
        ESKLPSmnn_mnn = self.dialogInfo.get('ESKLPSmnn_mnn', u'')
        ESKLPSmnn_form = self.dialogInfo.get('ESKLPSmnn_form', u'')
        ESKLPSmnn_trade_name = self.dialogInfo.get('ESKLPSmnn_trade_name', None)
        ESKLPSmnn_ftg = self.dialogInfo.get('ESKLPSmnn_ftg', u'')
        ESKLPSmnn_is_znvlp = self.dialogInfo.get('ESKLPSmnn_is_znvlp', 0)
        ESKLPSmnn_is_narcotic = self.dialogInfo.get('ESKLPSmnn_is_narcotic', 0)
        ESKLPSmnn_Dosage_grls_value = self.dialogInfo.get('ESKLPSmnn_Dosage_grls_value', u'')
        cond = [db.joinOr([tableEsklp_Smnn['date_end'].isNull(), tableEsklp_Smnn['date_end'].ge(QDateTime.currentDateTime())])]
        orderList = [tableEsklp_Smnn['code'].name(), tableEsklp_Smnn['mnn'].name()]
        if ESKLPSmnnCode:
            cond.append(tableEsklp_Smnn['code'].like(addDotsEx(ESKLPSmnnCode)))
        if ESKLPSmnn_mnn:
            cond.append(tableEsklp_Smnn['mnn'].like(addDotsEx(ESKLPSmnn_mnn)))
        if ESKLPSmnn_form:
            cond.append(tableEsklp_Smnn['form'].like(addDotsEx(ESKLPSmnn_form)))
        if ESKLPSmnn_trade_name:
            tableESKLP_Klp = db.table('esklp.Klp')
            queryTable = queryTable.leftJoin(tableESKLP_Klp, tableESKLP_Klp['smnn_id'].eq(tableEsklp_Smnn['id']))
            cond.append(tableESKLP_Klp['trade_name'].contain(ESKLPSmnn_trade_name))
        if ESKLPSmnn_ftg:
            cond.append(tableEsklp_Smnn['ftg'].like(addDotsEx(ESKLPSmnn_ftg)))
        if ESKLPSmnn_is_znvlp:
            cond.append(tableEsklp_Smnn['is_znvlp'].eq(ESKLPSmnn_is_znvlp - 1))
        if ESKLPSmnn_is_narcotic:
            cond.append(tableEsklp_Smnn['is_narcotic'].eq(ESKLPSmnn_is_narcotic - 1))
        if ESKLPSmnn_Dosage_grls_value:
            cond.append(tableESKLP_Smnn_Dosage['grls_value'].like(addDotsEx(ESKLPSmnn_Dosage_grls_value)))
        orderStr = ', '.join([fieldName for fieldName in orderList])
        idList = []
        records = db.getDistinctRecordList(queryTable, [tableEsklp_Smnn['UUID']], cond, order=orderStr, limit=1000)
        for record in records:
            UUID = forceStringEx(record.value('UUID'))
            if UUID and UUID not in idList:
                idList.append(UUID)
        return idList

    def setUUIDESKLPPopupUpdate(self, UUID):
        self.UUID = UUID
        self.setESKLPIdList([], self.UUID)

    def getWidgetHasFocus(self):
        for widget in [self.edtESKLPSmnnCode,
                       self.edtESKLPSmnn_mnn,
                       self.edtESKLPSmnn_form,
                       self.edtESKLPSmnn_ftg,
                       self.cmbESKLPSmnn_is_znvlp,
                       self.cmbESKLPSmnn_is_narcotic,
                       self.edtESKLPSmnn_Dosage_grls_value]:
            if widget.hasFocus():
                return widget
        return None

    def setESKLPPopupUpdate(self, UUID):
        QtGui.qApp.setWaitCursor()
        try:
            self.getParamsDialogFilter()
            if self.checkParamsDialogFilter():
                crIdList = self.getESKLPIdList()
                self.setESKLPIdList(crIdList, UUID)
            else:
                self.setESKLPIdList([], UUID)
        finally:
            QtGui.qApp.restoreOverrideCursor()

    def selectESKLPUUID(self, UUID):
        self.UUID = UUID
        self.emit(SIGNAL('ESKLPSmnnUUIDSelected(QString)'), UUID)
        self.close()

    @pyqtSignature('QModelIndex')
    def on_tblESKLPSmnn_doubleClicked(self, index):
        if index.isValid():
            if Qt.ItemIsEnabled & self.tableModel.flags(index):
                UUID = self.tblESKLPSmnn.currentItemId()
                self.selectESKLPUUID(UUID)
    
    
    @pyqtSignature('QString')
    def on_edtESKLPSmnn_trade_name_textChanged(self, text):
        self.tableModel.setTradeNameFilter(unicode(text))


class CESKLPTableModel(CTableModel):
    class CDosageCol(CCol):
        def __init__(self, title, fields, defaultWidth, alignment='l'):
            CCol.__init__(self, title, fields, defaultWidth, alignment)
            self._cache = {}

        def format(self, values):
            smnnUUID = forceStringEx(values[0])
            if smnnUUID:
                grls_value = self._cache.get(smnnUUID, u'')
                if grls_value:
                    return toVariant(grls_value)
                else:
                    db = QtGui.qApp.db
                    tableEsklp_Smnn = db.table('esklp.Smnn')
                    tableEsklp_Smnn_Dosage = db.table('esklp.Smnn_Dosage')
                    queryTable = tableEsklp_Smnn.innerJoin(tableEsklp_Smnn_Dosage,
                                                           tableEsklp_Smnn_Dosage['master_id'].eq(
                                                               tableEsklp_Smnn['id']))
                    record = db.getRecordEx(queryTable, [tableEsklp_Smnn_Dosage['grls_value']],
                                            [tableEsklp_Smnn['UUID'].eq(smnnUUID)])
                    if record:
                        grls_value = forceStringEx(record.value('grls_value'))
                        self._cache[smnnUUID] = grls_value
                        return toVariant(grls_value)
            return CCol.invalid

        def clearCache(self):
            self._cache = {}
            
            
    class CTradeNameCol(CCol):
        def __init__(self, title, fields, defaultWidth, alignment='l'):
            CCol.__init__(self, title, fields, defaultWidth, alignment)
            self._cache = {}
            self.tradeNameFilter = None

        def format(self, values):
            smnnID = forceStringEx(values[0])
            if smnnID:
                tn_value = self._cache.get(smnnID, u'')
                if tn_value:
                    return toVariant(tn_value)
                else:
                    db = QtGui.qApp.db
                    tableEsklp_Klp = db.table('esklp.Klp')
                    recordList = db.getRecordList(tableEsklp_Klp, [tableEsklp_Klp['trade_name']],
                                            [tableEsklp_Klp['smnn_id'].eq(smnnID),
                                             tableEsklp_Klp['trade_name'].contain(self.tradeNameFilter) if self.tradeNameFilter else "True"])
                    if recordList:
                        tn_values = []
                        for record in recordList:
                            tn_value = forceStringEx(record.value('trade_name'))
                            if tn_value not in tn_values:
                                tn_values.append(tn_value)
                        self._cache[smnnID] = '| '.join(tn_values)
                        return toVariant(tn_value)
            return CCol.invalid

        def clearCache(self):
            self._cache = {}
        
        def setTradeNameFilter(self, filter):
            self.tradeNameFilter = filter

    Col_TradeName = 3

    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.addColumn(CTextCol(u'Код узла СМНН', ['code'], 30))
        self.addColumn(CTextCol(u'Наименование МНН на русском языке', ['mnn'], 30))
        self.addColumn(CTextCol(u'Название лекарственной формы', ['form'], 30))
        self.addColumn(self.CTradeNameCol(u'Торговое наименование', ['id'], 10))
        self.addColumn(CTextCol(u'Название ФТГ', ['ftg'], 20))
        self.addColumn(CEnumCol(u'ЖНВЛП', ['is_znvlp'], [u'Нет', u'Да'], 4))
        self.addColumn(
            CEnumCol(u'Наличие в лекарственном препарате наркотических средств', ['is_narcotic'], [u'Нет', u'Да'], 4))
        self.addColumn(self.CDosageCol(u'Дозировка', ['UUID'], 10))
        self.setTable('esklp.Smnn')

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def setTable(self, tableName):
        db = QtGui.qApp.db
        tableEsklp_Smnn = db.table('esklp.Smnn')
        loadFields = [
            u'''DISTINCT esklp.Smnn.id, esklp.Smnn.code, esklp.Smnn.mnn, esklp.Smnn.form, esklp.Smnn.ftg, esklp.Smnn.is_znvlp, esklp.Smnn.is_narcotic, esklp.Smnn.UUID''']
        self._table = tableEsklp_Smnn
        self._recordsCache = CTableRecordCacheEx(db, self._table, loadFields, idFieldName='UUID')
    
    def setTradeNameFilter(self, filter):
        self.cols()[self.Col_TradeName].setTradeNameFilter(filter)
