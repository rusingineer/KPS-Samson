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
from PyQt4.QtCore import Qt, pyqtSignature, SIGNAL, QDate, QEvent, QObject

from library.TableModel import CRefBookCol, CTableModel, CTextCol
from library.Utils import getPref, setPref

from Ui_MESComboBoxPopupEx import Ui_MESComboBoxPopupEx


class CMESComboBoxPopupEx(QtGui.QFrame, Ui_MESComboBoxPopupEx):
    __pyqtSignals__ = ('MESSelected(int)',
                      )

    def __init__(self, parent = None):
        QtGui.QFrame.__init__(self, parent, Qt.Popup)
        self.setFrameShape(QtGui.QFrame.StyledPanel)
        self.setAttribute(Qt.WA_WindowPropagation)
        self.tableModel = CMESTableModel(self)
        self.tableSelectionModel = QtGui.QItemSelectionModel(self.tableModel, self)
        self.tableSelectionModel.setObjectName('tableSelectionModel')
        self.setupUi(self)
        self.tblMES.setModel(self.tableModel)
        self.tblMES.setSelectionModel(self.tableSelectionModel)
        self.mesId = None
        self.tblMES.installEventFilter(self)
        preferences = getPref(QtGui.qApp.preferences.windowPrefs, 'CMESComboBoxPopup', {})
        self.tblMES.loadPreferences(preferences)
        self.headerMESCol = self.tblMES.horizontalHeader()
        self.headerMESCol.setClickable(True)
        QObject.connect(self.headerMESCol,
                               SIGNAL('sectionClicked(int)'),
                               self.onHeaderMESColClicked)


    def onHeaderMESColClicked(self, col):
        headerSortingCol = self.tableModel.headerSortingCol.get(col, False)
        self.tableModel.headerSortingCol = {}
        self.tableModel.headerSortingCol[col] = not headerSortingCol
        self.tableModel.sortDataModel()


    def mousePressEvent(self, event):
        parent = self.parentWidget()
        if parent!=None:
            opt=QtGui.QStyleOptionComboBox()
            opt.init(parent)
            arrowRect = parent.style().subControlRect(
                QtGui.QStyle.CC_ComboBox, opt, QtGui.QStyle.SC_ComboBoxArrow, parent)
            arrowRect.moveTo(parent.mapToGlobal(arrowRect.topLeft()))
            if (arrowRect.contains(event.globalPos()) or self.rect().contains(event.pos())):
                self.setAttribute(Qt.WA_NoMouseReplay)
        QtGui.QFrame.mousePressEvent(self, event)

    def setMESCodeTemplate(self, mesCodeTemplate):
        self.mesCodeTemplate = mesCodeTemplate


    def setMESNameTemplate(self, mesNameTemplate):
        self.mesNameTemplate = mesNameTemplate



    def closeEvent(self, event):
        preferences = self.tblMES.savePreferences()
        setPref(QtGui.qApp.preferences.windowPrefs, 'CMESComboBoxPopup', preferences)
        QtGui.QFrame.closeEvent(self, event)


    def eventFilter(self, watched, event):
        if watched == self.tblMES:
            if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Select):
                event.accept()
                index = self.tblMES.currentIndex()
                self.tblMES.emit(SIGNAL('doubleClicked(QModelIndex)'), index)
                return True
        return QtGui.QFrame.eventFilter(self, watched, event)


    def on_buttonBox_apply(self):
        idList = self.getMesIdList()
        self.setMESIdList(idList)


    def setMESIdList(self, idList):
        self.tblMES.setIdList(idList, self.mesId)


    def getMesIdList(self):
        db = QtGui.qApp.db
        tableMES = db.table('mes.MES')
        cond = [tableMES['deleted'].eq(0)]
        if self.mesCodeTemplate:
            cond.append(tableMES['code'].regexp(self.mesCodeTemplate))
        if self.mesNameTemplate:
            cond.append(tableMES['name'].regexp(self.mesNameTemplate))
        idList = db.getIdList(tableMES, tableMES['id'].name(),
                              where=cond,
                              order='mes.MES.code, mes.MES.id'
                              )
        return idList


    def setup(self, mesId):
        self.mesId = mesId
        self.on_buttonBox_apply()


    @pyqtSignature('QModelIndex')
    def on_tblMES_doubleClicked(self, index):
        if index.isValid():
            if (Qt.ItemIsEnabled & self.tableModel.flags(index)):
                mesId = self.tblMES.currentItemId()
                self.mesId = mesId
                self.emit(SIGNAL('MESSelected(int)'), mesId)
                self.close()


class CMESTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.addColumn(CRefBookCol(u'Группа',       ['group_id'],  'mes.mrbMESGroup', 10))
        self.addColumn(CTextCol(u'Код',             ['code'],  20))
        self.addColumn(CTextCol(u'Наименование',    ['name'],  40))
        self.addColumn(CTextCol(u'Описание',        ['descr'], 40))
        self.addColumn(CTextCol(u'Модель пациента', ['patientModel'], 20))
        self.setTable('mes.MES')
        self.date = QDate.currentDate()


    def flags(self, index):
        return Qt.ItemIsEnabled|Qt.ItemIsSelectable

