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
from PyQt4.QtCore import Qt, SIGNAL, pyqtSignature

from library.DialogBase import CConstructHelperMixin
from library.TableModel import CTableModel, CDateCol, CEnumCol, CTextCol, CRefBookCol
from library.Utils      import getPref, setPref, withWaitCursor

from Ui_StockPurchaseContractComboBoxPopup import Ui_StockPurchaseContractComboBoxPopup

__all__ = [ 'CStockPurchaseContractComboBoxPopup',
          ]


class CStockPurchaseContractComboBoxPopup(Ui_StockPurchaseContractComboBoxPopup,
                                          QtGui.QFrame,
                                          CConstructHelperMixin
                                         ):
    __pyqtSignals__ = ('valueSelected(int)'
                      )

    def __init__(self, parent = None):
        QtGui.QFrame.__init__(self, parent, Qt.Popup)
        self.setFrameShape(QtGui.QFrame.StyledPanel)
        self.setAttribute(Qt.WA_WindowPropagation)

        self.addObject('actSelect', QtGui.QAction(self))
        self.addObject('actSearch', QtGui.QAction(self))
        self.addModels('PurchaseContracts', CPurchaseContractsModel(self))

        self.setupUi(self)

        self.tabContracts.addAction(self.actSelect)
        self.actSelect.setShortcuts([Qt.Key_Return, Qt.Key_Enter, Qt.Key_Select])

        self.setModels(self.tblPurchaseContracts,
                       self.modelPurchaseContracts,
                       self.selectionModelPurchaseContracts
                      )
        #self.setFocusProxy(self.tblPurchaseContracts)

        self.actSearch.setShortcuts([Qt.Key_Return, Qt.Key_Enter])
        self.tabSearch.addAction(self.actSearch)

        preferences = getPref(QtGui.qApp.preferences.windowPrefs, 'CStockPurchaseContractComboBoxPopup', {})
        self.tblPurchaseContracts.loadPreferences(preferences)

        self.edtDate.canBeEmpty(True)
        self.edtDate.setDate(None)

        self._supplierOrgId = None
        self._actDate = None
        self._contractId = None


    def setup(self, supplierOrgId, actDate, contractId):
        self._supplierOrgId = supplierOrgId
        self._actDate = actDate
        self._contractId = contractId
        self.on_buttonBox_apply()


#    def mousePressEvent(self, event):
#        parent = self.parentWidget()
#        if parent!=None:
#            opt=QtGui.QStyleOptionComboBox()
#            opt.init(parent)
#            arrowRect = parent.style().subControlRect(
#                QtGui.QStyle.CC_ComboBox, opt, QtGui.QStyle.SC_ComboBoxArrow, parent)
#            arrowRect.moveTo(parent.mapToGlobal(arrowRect.topLeft()))
#            if (arrowRect.contains(event.globalPos()) or self.rect().contains(event.pos())):
#                self.setAttribute(Qt.WA_NoMouseReplay)
#        QtGui.QFrame.mousePressEvent(self, event)


    def closeEvent(self, event):
        preferences = self.tblPurchaseContracts.savePreferences()
        setPref(QtGui.qApp.preferences.windowPrefs, 'CStockPurchaseContractComboBoxPopup', preferences)
        QtGui.QFrame.closeEvent(self, event)


    def on_buttonBox_reset(self):
        self.edtNumber.setText(u'')
        self.edtName.setText(u'')
        self.edtDate.setDate(None)


    @withWaitCursor
    def on_buttonBox_apply(self):
        idList = self.getStockPurchaseContractIdList()
        self.setStockPurchaseContractIdList(idList, self._contractId)


    def setStockPurchaseContractIdList(self, idList, posToId):
        if idList:
            self.tblPurchaseContracts.setIdList(idList, posToId)
            self.tabWidget.setCurrentIndex(0)
            self.tabWidget.setTabEnabled(0, True)
            self.tblPurchaseContracts.setFocus(Qt.OtherFocusReason)
        else:
            self.tabWidget.setCurrentIndex(1)
            self.setFocusProxy(self.edtNumber)
            self.tabWidget.setTabEnabled(0, False)


    def getStockPurchaseContractIdList(self):
        db = QtGui.qApp.db
        tableStockPurchaseContract = db.table('StockPurchaseContract')
        cond = [tableStockPurchaseContract['deleted'].eq(0),
                tableStockPurchaseContract['begDate'].dateLe(self._actDate),
                tableStockPurchaseContract['endDate'].dateGe(self._actDate),
                tableStockPurchaseContract['supplierOrg_id'].eq(self._supplierOrgId),
               ]
        number = unicode(self.edtNumber.text())
        date   = self.edtDate.date()
        name   = unicode(self.edtName.text())
        if number:
            cond.append(tableStockPurchaseContract['number'].like(number))
        if date:
            cond.append(tableStockPurchaseContract['date'].eq(date))
        if name:
            cond.append(tableStockPurchaseContract['date'].like(name))
        idList = db.getIdList(tableStockPurchaseContract,
                              idCol='id',
                              where=cond,
                              order='number, date, begDate')
        return idList


    @pyqtSignature('')
    def on_actSelect_triggered(self):
        purchaseContractId = self.tblPurchaseContracts.currentItemId()
        if purchaseContractId:
            self.emit(SIGNAL('valueSelected(int)'), purchaseContractId)
            self.close()


    @pyqtSignature('QModelIndex')
    def on_tblPurchaseContracts_clicked(self, index):
        purchaseContractId = self.tblPurchaseContracts.currentItemId()
        self.emit(SIGNAL('valueSelected(int)'), purchaseContractId)
        self.close()


    @pyqtSignature('')
    def on_actSearch_triggered(self):
        self.buttonBox.button(QtGui.QDialogButtonBox.Apply).animateClick()


    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_buttonBox_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_buttonBox_reset()


class CPurchaseContractsModel(CTableModel):
#    class CSupplierCol(CCol):
#        def __init__(self):
#            CCol.__init__(self, u'Организация поставщик', ['supplierOrg_id'], defaultWidth=15, alignment='l')
#            self.organisationCache = CDbDataCache.getData('Organisation', 'shortName', filter='isSupplier=1', addNone=True, noneText='', order='id')
#
#        def format(self, values):
#            supplierOrgId = forceRef(values[0])
#            if supplierOrgId:
#                if supplierOrgId in self.organisationCache.idList:
#                    dataIndex = self.organisationCache.idList.index(supplierOrgId)
#                    value = self.organisationCache.strList[dataIndex]
#                else:
#                    value = u'{ %d }' % supplierOrgId
#                return toVariant(value)
#            else:
#                return CCol.invalid
#
#        def invalidateRecordsCache(self):
#            self.organisationCache = CDbDataCache.getData('Organisation', 'shortName', filter='isSupplier=1', addNone=True, noneText='', order='id')


    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.addColumn(CTextCol(u'Номер', ['number'], 30))
        self.addColumn(CDateCol(u'Дата', ['date'], 30))
        self.addColumn(CTextCol(u'Наименование', ['name'], 30))
        self.addColumn(CTextCol(u'Наименование для печати', ['title'], 20))
        self.addColumn(CEnumCol(u'Является государственным', ['isState'], [u'Нет', u'Да'], 10))
        self.addColumn(CDateCol(u'Действует c', ['begDate'], 20))
        self.addColumn(CDateCol(u'Действует по', ['endDate'], 20))
#        CPurchaseContractsModel.CSupplierCol(),
        self.addColumn(CRefBookCol(u'Тип финансирования', ['finance_id'], 'rbFinance',  20))
        self.setTable('StockPurchaseContract')


    def flags(self, index):
        return Qt.ItemIsEnabled|Qt.ItemIsSelectable


#    def setTable(self, tableName):
#        db = QtGui.qApp.db
#        table = db.table('StockPurchaseContract')
#        loadFields = '*'
#        self._table = table
#        self._recordsCache = CTableRecordCache(db, self._table, loadFields)
