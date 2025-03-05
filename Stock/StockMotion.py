# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2017 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################


from PyQt4 import QtGui

from library.Utils                         import forceInt

from Stock.IncomingInvoiceEditDialog       import CIncomingInvoiceEditDialog
from Stock.InternalInvoiceEditDialog       import CInternalInvoiceEditDialog
from Stock.InventoryEditDialog             import CInventoryEditDialog
from Stock.FinTransferEditDialog           import CFinTransferEditDialog
from Stock.ProductionEditDialog            import CProductionEditDialog
from Stock.StockUtilizationEditDialog      import CStockUtilizationEditDialog, CStockInternalConsumptionEditDialog
from Stock.StockResidualQuantityWriteDownEditDialog import CStockResidualQuantityWriteDownEditDialog
from Stock.ClientInvoiceEditDialog         import (
                                                    CClientInvoiceEditDialog,
                                                    CClientRefundInvoiceEditDialog,
                                                    CClientInvoiceReservationEditDialog,
                                                  )
from Stock.StockSupplierRefundEditDialog   import CStockSupplierRefundEditDialog

stockMotionType = {
    0  : (u'Внутренняя накладная',       CInternalInvoiceEditDialog),
    1  : (u'Инвентаризация',             CInventoryEditDialog),
    2  : (u'Финансовый перенос',         CFinTransferEditDialog),
    3  : (u'Производство',               CProductionEditDialog),
    4  : (u'Списание на пациента',       CClientInvoiceEditDialog),
    5  : (u'Возврат от пациента',        CClientRefundInvoiceEditDialog),
    6  : (u'Резервирование на пациента', CClientInvoiceReservationEditDialog),
    7  : (u'Утилизация',                 CStockUtilizationEditDialog),
    8  : (u'Внутреннее потребление',     CStockInternalConsumptionEditDialog),
    9  : (u'Возврат поставщику',         CStockSupplierRefundEditDialog),
    10 : (u'Накладная от поставщика',    CIncomingInvoiceEditDialog),
    11 : (u'Списание остаточных количеств', CStockResidualQuantityWriteDownEditDialog),
}


stockPurchaseType = {0 : u'Контракт на закупку',
                     1 : u'Заявка на поставку'
                    }


class CStockPurchaseType:
    purchaseContract = 0
    purchaseInvoice = 1


def getStockPurchaseTypeDocumentName(type):
    if type in stockPurchaseType:
        return stockPurchaseType[type]
    else:
        return '{%s}' % type


def getDialogName(type):
    if type in stockMotionType:
        return stockMotionType[type][0]
    else:
        return '{%s}' % type


def getDialogClass(type):
    return stockMotionType[type][1]


def getStockMotionTypeNames():
    return [value[0] for value in stockMotionType.values()]


def editStockMotion(widget, id):
    type = forceInt(QtGui.qApp.db.translate('StockMotion', 'id', id, 'type'))
    dialogClass = getDialogClass(type)
    dialog = dialogClass(widget)
    try:
        dialog.load(id)
        return dialog.exec_()
    finally:
        dialog.deleteLater()


def openReadOnlyMotion(widget, id):
    type = forceInt(QtGui.qApp.db.translate('StockMotion', 'id', id, 'type'))
    dialogClass = getDialogClass(type)
    dialog = dialogClass(widget)
    try:
        dialog.load(id)
        setReadOnly(dialog)
        return dialog.exec_()
    finally:
        dialog.deleteLater()


def setReadOnly(dialog):
    actualTitle = dialog.windowTitle()
    if '[*]' in actualTitle:
        actualTitle = actualTitle.replace('[*]', u'(только просмотр)')
    QtGui.QDialog.setWindowTitle(dialog, actualTitle)

    dialog.setReadOnly(True)
    if hasattr(dialog, 'edtNumber'):
        dialog.edtNumber.setReadOnly(True)
    if hasattr(dialog, 'edtDate'):
        dialog.edtDate.setReadOnly(True)

    if hasattr(dialog, 'edtReason'):
        dialog.edtReason.setReadOnly(True)
    if hasattr(dialog, 'cmbPlaceOfBusiness'):
        dialog.cmbPlaceOfBusiness.setEnabled(False)
        dialog.cmbPlaceOfBusiness.setStyleSheet("color: rgb(0,0,0)")
    if hasattr(dialog, 'cmbReason'):
        dialog.cmbReason.setEnabled(False)
        dialog.cmbReason.setStyleSheet("color: rgb(0,0,0)")
    if hasattr(dialog, 'edtReasonDate'):
        dialog.edtReasonDate.setReadOnly(True)
    if hasattr(dialog, 'edtTime'):
        dialog.edtTime.setReadOnly(True)
    if hasattr(dialog, 'cmbSupplier'):
        dialog.cmbSupplier.setEnabled(False)
    if hasattr(dialog, 'cmbSupplierPerson'):
        dialog.cmbSupplierPerson.setEnabled(False)
    if hasattr(dialog, 'edtNote'):
        dialog.edtNote.setReadOnly(True)
    if hasattr(dialog, 'tblItems'):
        dialog.tblItems.model().setReadOnly(True)
    if hasattr(dialog, 'cmbSupplierOrg'):
        dialog.cmbSupplierOrg.setEnabled(False)
        dialog.cmbSupplierOrg.setStyleSheet("color: rgb(0,0,0)")
    if hasattr(dialog, 'edtSupplierOrgPerson'):
        dialog.edtSupplierOrgPerson.setReadOnly(True)
    if hasattr(dialog, 'tblInItems'):
        dialog.tblInItems.model().setReadOnly(True)
    if hasattr(dialog, 'tblOutItems'):
        dialog.tblOutItems.model().setReadOnly(True)
    if hasattr(dialog, 'cmbReceiver'):
        dialog.cmbReceiver.setEnabled(False)
        dialog.cmbReceiver.setStyleSheet("color: rgb(0,0,0)")
    if hasattr(dialog, 'cmbReceiverPerson'):
        dialog.cmbReceiverPerson.setEnabled(False)
        dialog.cmbReceiverPerson.setStyleSheet("color: rgb(0,0,0)")

    if hasattr(dialog, 'edtDocDate'):
        dialog.edtDocDate.setReadOnly(True)
    if hasattr(dialog, 'edtInvoiceNumber'):
        dialog.edtInvoiceNumber.setReadOnly(True)
    if hasattr(dialog, 'edtInvoiceDate'):
        dialog.edtInvoiceDate.setReadOnly(True)
    if hasattr(dialog, 'btnSelectOrganisation'):
        dialog.btnSelectOrganisation.setEnabled(False)
    if hasattr(dialog, 'btnMDLPExchange'):
        dialog.btnMDLPExchange.setEnabled(False)
    if hasattr(dialog, 'btnFill'):
        dialog.btnFill.setEnabled(False)

