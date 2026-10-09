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
from PyQt4.QtCore import SIGNAL, Qt

from Registry.VisitComboBoxPopup import CVisitComboBoxPopup
from library.ROComboBox import CROComboBox
from library.Utils      import forceStringEx, forceDate


__all__ = [ 'CVisitComboBox',
          ]


class CVisitComboBox(CROComboBox):
    __pyqtSignals__ = ('textChanged(QString)',
                       'textEdited(QString)'
                      )

    def __init__(self, parent = None):
        CROComboBox.__init__(self, parent)
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self._popup = None
        self.visitId = None
        self.filter = []
        self.queryTable = []


    def showPopup(self):
        if not self._popup:
            self._popup = CVisitComboBoxPopup(self)
            self.connect(self._popup, SIGNAL('visitIdSelected(int)'), self.setValue)
        pos = self.rect().bottomLeft()
        pos = self.mapToGlobal(pos)
        size = self._popup.sizeHint()
        screen = QtGui.QApplication.desktop().availableGeometry(pos)
        size.setWidth(screen.width())
        pos.setX( max(min(pos.x(), screen.right()-size.width()), screen.left()) )
        pos.setY( max(min(pos.y(), screen.bottom()-size.height()), screen.top()) )
        self._popup.move(pos)
        self._popup.resize(size)
        self._popup.show()
        self._popup.setFilter(self.filter, self.queryTable)
        self._popup.on_buttonBox_apply()
        self._popup.setVisitId(self.visitId)


    def setFilter(self, filter, queryTable):
        self.filter = filter
        self.queryTable = queryTable


    def setValue(self, visitId):
        self.visitId = visitId
        self.updateText()


    def value(self):
        return self.visitId


    def updateText(self):
        date = u''
        if self.visitId:
            db = QtGui.qApp.db
            table = db.table('Visit')
            record = db.getRecordEx(table, '*', [table['id'].eq(self.visitId)])
            date = forceStringEx(forceDate(record.value('date'))) if record else u''
        self.setEditText(date)


    def keyPressEvent(self, event):
        if self.model().isReadOnly():
            event.accept()
        else:
            key = event.key()
            if key == Qt.Key_Escape or key == Qt.Key_Return or key == Qt.Key_Enter:
                event.ignore()
            elif key == Qt.Key_Delete or key == Qt.Key_Backspace:
                self.setValue(None)
                event.accept()
            else:
                QtGui.QComboBox.keyPressEvent(self, event)

