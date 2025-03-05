# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2024 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4              import QtGui #, QtSql
from PyQt4.QtCore       import SIGNAL
from library.InDocTable import CInDocTableView, CLocItemDelegate
from library.Utils      import forceRef, toVariant


class CLocItemDelegateEx(CLocItemDelegate):
    def __init__(self, parent):
        CLocItemDelegate.__init__(self, parent)


    def createEditor(self, parent, option, index):
        editor = index.model().createEditor(index, parent)
        if editor is not None:
            self.connect(editor, SIGNAL('commit()'), self.emitCommitData)
            self.connect(editor, SIGNAL('editingFinished()'), self.commitAndCloseEditor)
        self.editor   = editor
        self.row = index.row()
        filter = u''
        if self.row >= 0 and self.row <= len(index.model().items()):
            item = index.model().items()[self.row]
            specialityId = forceRef(item.value('speciality_id'))
            if specialityId:
                personId = forceRef(item.value('person_id'))
                if personId:
                    personRecord = QtGui.qApp.db.getRecord('Person', 'speciality_id', personId)
                    personSpecialityId = forceRef(personRecord.value('speciality_id')) if personRecord else None
                    if personSpecialityId != specialityId:
                        index.model().items()[self.row].setValue('person_id', toVariant(None))
                filter = u'''vrbPerson.speciality_id = %s'''%(str(specialityId))
            index.model().cols()[index.model().getColIndex('person_id')].setFilter(filter)
        self.rowcount = index.model().rowCount()
        self.column   = index.column()
        return editor


class CInspectionsResultInDocTableView(CInDocTableView):
    def __init__(self, parent):
        CInDocTableView.__init__(self, parent)
        self.setItemDelegate(CLocItemDelegateEx(self))

