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
from PyQt4.QtCore import QEvent, QUrl, QVariant, SIGNAL

from library.Utils         import forceString

from ActionPropertyValueType       import CActionPropertyValueType
from StringActionPropertyValueType import CStringActionPropertyValueType


class CUrlActionPropertyValueType(CActionPropertyValueType):
    name              = u'URL'
    variantType       = QVariant.String

    class CPropEditor(QtGui.QWidget):
        __pyqtSignals__ = ('editingFinished()',
                           'commit()',
                          )

        def __init__(self, action, domain, parent, clientId, eventTypeId, readOnly=False):
            QtGui.QWidget.__init__(self, parent)
            self.boxlayout = QtGui.QHBoxLayout(self)
            self.boxlayout.setMargin(0)
            self.boxlayout.setSpacing(0)
            self.boxlayout.setObjectName('boxlayout')
            self.edtUrl = QtGui.QLineEdit(self)
            self.edtUrl.setObjectName('edtUrl')
            self.boxlayout.addWidget(self.edtUrl)
            self.btnOpen = QtGui.QPushButton(self)
            self.btnOpen.setObjectName('btnOpen')
            self.btnOpen.setText(u'...')
            self.btnOpen.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Ignored)
            self.btnOpen.setFixedWidth(20)
            self.boxlayout.addWidget(self.btnOpen)
            self.setFocusProxy(self.edtUrl)
            self.connect(self.btnOpen, SIGNAL('clicked()'), self.on_btnOpen_clicked)
            self.edtUrl.setReadOnly(readOnly)
            if domain == 'ro':
                self.edtUrl.setReadOnly(True)
            #self.connect(self.edtUrl, SIGNAL('clicked()'), self.on_btnOpen_clicked)
            self.edtUrl.installEventFilter(self)
            self.btnOpen.installEventFilter(self)


        def eventFilter(self, widget, event):
            et = event.type()
            if et == QEvent.FocusOut:
                fw = QtGui.qApp.focusWidget()
                while fw and fw != self:
                    fw = fw.parentWidget()
                if not fw:
                    self.emit(SIGNAL('editingFinished()'))
            elif et == QEvent.Hide and widget == self.edtUrl:
                self.emit(SIGNAL('commit()'))
            return QtGui.QWidget.eventFilter(self, widget, event)


        def on_btnOpen_clicked(self):
            url = unicode(self.edtUrl.text())
            QtGui.QDesktopServices.openUrl(QUrl.fromEncoded(url))


        def setValue(self, value):
            self.edtUrl.setText(forceString(value))


        def value(self):
            return unicode(self.edtUrl.text())


    @staticmethod
    def convertDBValueToPyValue(value):
        return forceString(value)

    convertQVariantToPyValue = convertDBValueToPyValue


    def getTableName(self):
        return self.tableNamePrefix+CStringActionPropertyValueType.name


    def getEditorClass(self):
        return self.CPropEditor
