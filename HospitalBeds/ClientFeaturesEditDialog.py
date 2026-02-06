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
from PyQt4.QtCore import QDate

from library.ItemsListDialog     import CItemEditorBaseDialog
from library.Utils               import exceptionToUnicode, forceDate, forceInt, forceRef, forceString, forceStringEx, toVariant
from Registry.Utils              import getClientInfo, getClientBanner

from Registry.ClientEditDialog   import CAllergyModel, CIntoleranceMedicamentModel
from Ui_ClientFeaturesEditDialog import Ui_Dialog

class CClientFeaturesEditDialog(CItemEditorBaseDialog, Ui_Dialog):
    def __init__(self, parent, clientId):
        CItemEditorBaseDialog.__init__(self, parent, 'Client')
        self.clientInfo = None
        self.clientId    = clientId
        self.addModels('Allergy', CAllergyModel(self))
        self.addModels('IntoleranceMedicament', CIntoleranceMedicamentModel(self))
        self.setupUi(self)
        self.setObjectName('ClientFeaturesEditDialog')
        self.cmbBloodType.setTable('rbBloodType', True)
        self.edtBloodTypeDate.canBeEmpty(True)
        self.setModels(self.tblAllergy, self.modelAllergy, self.selectionModelAllergy)
        self.setModels(self.tblIntoleranceMedicament, self.modelIntoleranceMedicament, self.selectionModelIntoleranceMedicament)
        self.tblAllergy.addPopupRecordProperies()
        self.tblAllergy.addPopupDelRow()
        self.tblIntoleranceMedicament.addPopupRecordProperies()
        self.tblIntoleranceMedicament.addPopupDelRow()
        date = QDate.currentDate()
        self.clientInfo = getClientInfo(self.clientId, date=date)
        self.txtClientInfoBrowser.setHtml(getClientBanner(self.clientId, date))

    def checkDataEntered(self):
        result = True
        return result

    def save(self):
        try:
            db = QtGui.qApp.db
            db.transaction()
            try:
                record = self.getRecord()
                id = db.insertOrUpdate('Client', record)
                self.modelAllergy.saveItems(id)
                self.modelIntoleranceMedicament.saveItems(id)
                db.commit()
            except:
                db.rollback()
                QtGui.qApp.logCurrentException()
                raise
            self.setIsDirty(False)
            return id
        except Exception, e:
            QtGui.qApp.logCurrentException()
            QtGui.QMessageBox.critical( self,
                                        u'',
                                        exceptionToUnicode(e),
                                        QtGui.QMessageBox.Close)
            return None

    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        id = self.itemId()
        self.cmbBloodType.setValue(forceRef(record.value('bloodType_id')))
        self.edtBloodTypeDate.setDate(forceDate(record.value('bloodDate')))
        self.edtBloodTypeNotes.setText(forceString(record.value('bloodNotes')))
        self.edtBirthHeight.setValue(forceInt(record.value('birthHeight')))
        self.edtBirthWeight.setValue(forceInt(record.value('birthWeight')))
        self.edtBirthGestationalAge.setValue(forceInt(record.value('birthGestationalAge')))
        self.edtMenarhe.setValue(forceInt(record.value('menarhe')))
        self.edtMenoPausa.setValue(forceInt(record.value('menoPausa')))
        self.modelAllergy.loadItems(id)
        self.modelIntoleranceMedicament.loadItems(id)

    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        record.setValue('menarhe', toVariant(self.edtMenarhe.value()))
        record.setValue('menoPausa', toVariant(self.edtMenoPausa.value()))
        record.setValue('bloodType_id', toVariant(self.cmbBloodType.value()))
        record.setValue('bloodDate', toVariant(self.edtBloodTypeDate.date()))
        record.setValue('bloodNotes', toVariant(forceStringEx(self.edtBloodTypeNotes.text())))
        record.setValue('birthHeight',toVariant(self.edtBirthHeight.value()))
        record.setValue('birthWeight',toVariant(self.edtBirthWeight.value()))
        record.setValue('birthGestationalAge', toVariant(self.edtBirthGestationalAge.value()))
        record.setValue('menarhe', toVariant(self.edtMenarhe.value()))
        record.setValue('menoPausa', toVariant(self.edtMenoPausa.value()))
        return record
