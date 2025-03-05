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
from PyQt4.QtCore import SIGNAL, QDate

from library.DbComboBox import CDbComboBox

from library.adjustPopup import adjustPopupToWidget

from StockPurchaseContractComboBoxPopup import CStockPurchaseContractComboBoxPopup

__all__ = [ 'CStockPurchaseContractComboBox',
          ]


class CStockPurchaseContractComboBox(CDbComboBox):
    def __init__(self, parent):
        CDbComboBox.__init__(self, parent)
        self.setTable(tableName='StockPurchaseContract',
                      nameField=u'CONCAT(number, \' от \', DATE_FORMAT(date,\'%d.%m.%Y\'), \' \', name)',
                      addNone = True,
                      order = 'number, date, begDate'
                     )
        self.setAddNone(True, u'не задано')
        self._date = QDate.currentDate()
        self._supplierOrgId = None
        self.updateFilter()
        self._popup = None


    def setDate(self, date):
        if self._date != date:
            self._date = date
            self.updateFilter()


    def setSupplierOrgId(self, supplierOrgId):
        if self._supplierOrgId != supplierOrgId:
            self._supplierOrgId = supplierOrgId
            self.updateFilter()


    def updateFilter(self):
        db = QtGui.qApp.db
        value = self.value()
        tableStockPurchaseContract = db.table('StockPurchaseContract')
        cond = [tableStockPurchaseContract['deleted'].eq(0),
                tableStockPurchaseContract['begDate'].dateLe(self._date),
                tableStockPurchaseContract['endDate'].dateGe(self._date),
                tableStockPurchaseContract['supplierOrg_id'].eq(self._supplierOrgId),
               ]
        self.setFilter(db.joinAnd(cond))
        self.setValue(value)




#    def eventFilter(self, obj, event):
#        if event.type() == QEvent.Close:
#            self.hidePopup()
#            return True
#        return CDbComboBox.eventFilter(self, obj, event)

    def showPopup(self):
        if not self.isReadOnly():
            if not self._popup:
                self._popup = CStockPurchaseContractComboBoxPopup(self)
                self._popup.installEventFilter(self)
                self.connect(self._popup, SIGNAL('valueSelected(int)'), self.setValue)

            adjustPopupToWidget(self, self._popup)
            self._popup.setup(self._supplierOrgId, self._date, self.value())
            self._popup.show()
            self._popup.setFocus()


    def hidePopup(self):
        if self._popup and self._popup.isVisible():
            self._popup.removeEventFilter(self)
            self._popup.close()
#            if self._deletePopupOnClose:
#                if self._popup:
            self._popup.deleteLater()
            self._popup = None
        QtGui.QComboBox.hidePopup(self)
#        self.setFocus()
#        self.emit(SIGNAL('editingFinished()'))



#   def emitValueChanged(self):
#        self.emit(SIGNAL('valueChanged()'))


