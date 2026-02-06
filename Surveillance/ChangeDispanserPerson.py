# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2012-2025 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from library.ItemsListDialog import CItemEditorBaseDialog
from library.Utils import forceRef, toVariant
from library.interchange import setRBComboBoxValue, getRBComboBoxValue

from Surveillance.Ui_ChangeDispanserPerson import Ui_ChangeDispanserPerson


class CChangeDispanserPerson(CItemEditorBaseDialog, Ui_ChangeDispanserPerson):
    def __init__(self, parent):
        CItemEditorBaseDialog.__init__(self, parent, 'Diagnosis')
        self.setupUi(self)
        self.setWindowTitleEx(u'Изменить врача по диспансерному наблюдению')
        self.setupDirtyCather()


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        setRBComboBoxValue(self.cmbPerson, record, 'dispanserPerson_id')
        self.setIsDirty(False)


    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        getRBComboBoxValue(self.cmbPerson, record, 'dispanserPerson_id')
        return record


    def checkDataEntered(self):
        result = True
        personId = forceRef(self.cmbPerson.value())
        result = result and (personId or self.checkInputMessage(u'врача по диспансерному учету', True, self.cmbPerson))
        return result
    
    
    def save(self):
        if self.getRecord() and self._id:
            return CItemEditorBaseDialog.save(self)
        return True
    
    
    def getPersonId(self):
        return toVariant(self.cmbPerson.value())
