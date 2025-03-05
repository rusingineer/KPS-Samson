# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2023 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from library.ItemsListDialog    import CItemsListDialog, CItemEditorBaseDialog
from library.TableModel         import CTextCol, CDateCol
from Ui_ObservationGroupEditor  import Ui_ObservationGroupEditor


class CRBObservationGroupList(CItemsListDialog):
    def __init__(self, parent):
        CItemsListDialog.__init__(self, parent, [
            CTextCol(u'Код', ['code'], 20),
            CTextCol(u'Наименование', ['name'], 40),
            CDateCol(u'Дата начала', ['begDate'], 40),
            CDateCol(u'Дата окончания', ['endDate'], 40),
            ], 'rbObservationGroup', ['code', 'name'])
        self.setWindowTitleEx(u'Группы наблюдения')


    def getItemEditor(self):
        return CRBObservationGroupEditor(self)


class CRBObservationGroupEditor(CItemEditorBaseDialog, Ui_ObservationGroupEditor):
    def __init__(self,  parent):
        CItemEditorBaseDialog.__init__(self, parent, 'rbObservationGroup')
        self.setupUi(self)
        self.setWindowTitleEx(u'Группы наблюдения')


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        self.edtCode.setText(record.value('code').toString())
        self.edtName.setText(record.value('name').toString())
        self.edtBegDate.setDate(record.value('begDate').toDate())
        self.edtEndDate.setDate(record.value('endDate').toDate())


    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        record.setValue('code', self.edtCode.text())
        record.setValue('name', self.edtName.text())
        record.setValue('begDate', self.edtBegDate.date())
        record.setValue('endDate', self.edtEndDate.date())
        return record
