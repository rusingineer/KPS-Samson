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

from PyQt4 import QtGui
from PyQt4.QtCore import SIGNAL

from library.crbcombobox            import CRBComboBox
from library.MES.MESComboBoxPopupEx import CMESComboBoxPopupEx
from library.Utils                  import forceString


__all__ = ('CMESComboBoxEx',
          )

class CMESComboBoxEx(CRBComboBox):
    __pyqtSignals__ = ('textChanged(QString)',
                       'textEdited(QString)'
                      )
    def __init__(self, parent):
        CRBComboBox.__init__(self, parent)
        self._tableName = 'mes.MES'
        self._addNone = True
        self._customFilter = None
        self.mesCodeTemplate = ''
        self.mesNameTemplate = ''
        CRBComboBox.setTable(self, self._tableName, self._addNone, self.compileFilter(), self._order)
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self._popup = None
        self.mesId = None
        self.setShowFields(CRBComboBox.showCodeAndName)


    def setTable(self, tableName, addNone=True, filter='', order=None):
        assert False


    def setAddNone(self, addNone=True):
        if self._addNone != addNone:
            self._addNone = addNone
            self.updateFilter()


    def setMESCodeTemplate(self, mesCodeTemplate):
        self.mesCodeTemplate = mesCodeTemplate


    def setMESNameTemplate(self, mesNameTemplate):
        self.mesNameTemplate = mesNameTemplate


    def showPopup(self):
        if not self._popup:
            self._popup = CMESComboBoxPopupEx(self)
            self.connect(self._popup, SIGNAL('MESSelected(int)'), self.setValue)
        self._popup.setMESCodeTemplate(self.mesCodeTemplate)
        self._popup.setMESNameTemplate(self.mesNameTemplate)
        pos = self.rect().bottomLeft()
        pos2 = self.rect().topLeft()
        pos = self.mapToGlobal(pos)
        pos2 = self.mapToGlobal(pos2)
        size = self._popup.sizeHint()
        width = max(size.width(), self.width())
        size.setWidth(width)
        screen = QtGui.QApplication.desktop().availableGeometry(pos)
        pos.setX(max(min(pos.x(), screen.right()-size.width()), screen.left()))
        pos.setY(max(min(pos.y(), screen.bottom()-size.height()), screen.top()))
        self._popup.move(pos)
        self._popup.resize(size)
        self._popup.show()
        self._popup.setup(self.mesId)


    def setValue(self, mesId):
        self.mesId = mesId
        self.updateText()


    def value(self):
        return self.mesId


    @staticmethod
    def getText(mesId):
        if mesId:
            db = QtGui.qApp.db
            table = db.table('mes.MES')
            record = db.getRecordEx(table, ['code','name'], [table['id'].eq(mesId), table['deleted'].eq(0)])
            if record:
                code = forceString(record.value('code'))
                name = forceString(record.value('name'))
                text = code + ' | ' + name
            else:
                text = '{%s}' % mesId
        else:
            text = ''
        return text


    def updateText(self):
        self.setEditText(self.getText(self.mesId))


    def compileFilter(self):
        db = QtGui.qApp.db
        tableMES = db.table('mes.MES')
        cond = [tableMES['deleted'].eq(0)]
        if self.mesCodeTemplate:
            cond.append(tableMES['code'].regexp(self.mesCodeTemplate))
        if self.mesNameTemplate:
            cond.append(tableMES['name'].regexp(self.mesNameTemplate))
        return db.joinAnd(cond)


    def updateFilter(self):
        v = self.value()
        CRBComboBox.setTable(self, self._tableName, self._addNone, self.compileFilter(), self._order)
        self.setValue(v)


    def lookup(self):
        i, self._searchString = self._model.searchCodeEx(self._searchString)
        if i >= 0 and i != self.currentIndex():
            self.setCurrentIndex(i)
            rowIndex = self.currentIndex()
            self.mesId = self._model.getId(rowIndex)
