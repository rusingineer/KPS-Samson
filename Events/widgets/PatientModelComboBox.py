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
from PyQt4.QtCore import Qt, pyqtSignature, SIGNAL, QDate, QEvent

from library.TableModel import CRefBookCol, CTableModel, CTextCol, CDateCol
from library.Utils import forceString, getPref, setPref
from library.crbcombobox import CRBComboBox
from library.ROComboBox  import CROComboBox

from Ui_PatientModelComboBoxPopup import Ui_PatientModelComboBoxPopup


class CPatientModelComboBoxPopup(QtGui.QFrame, Ui_PatientModelComboBoxPopup):
    __pyqtSignals__ = ('patientModelSelected(int)'
                      )

    def __init__(self, parent, eventEditor = None):
        QtGui.QFrame.__init__(self, parent, Qt.Popup)
        self.setFrameShape(QtGui.QFrame.StyledPanel)
        self.setAttribute(Qt.WA_WindowPropagation)
        self.tableModel = CPatientModelTableModel(self)
        self.tableSelectionModel = QtGui.QItemSelectionModel(self.tableModel, self)
        self.tableSelectionModel.setObjectName('tableSelectionModel')
        self.setupUi(self)
        self.tblPatientModel.setModel(self.tableModel)
        self.tblPatientModel.setSelectionModel(self.tableSelectionModel)
        self.buttonBox.button(QtGui.QDialogButtonBox.Apply).setDefault(True)
        self.buttonBox.button(QtGui.QDialogButtonBox.Apply).setShortcut(Qt.Key_Return)
        self.patientModelId = None
        self.eventEditor = eventEditor
        self.tblPatientModel.installEventFilter(self)
        preferences = getPref(QtGui.qApp.preferences.windowPrefs, 'CPatientModelComboBoxPopup', {})
        self.tblPatientModel.loadPreferences(preferences)
        self.cmbQuoting.setShowFields(CRBComboBox.showCodeAndName)
        self._endDate = None
        if self.eventEditor:
            self.cmbQuoting.setBegDate(self.eventEditor.eventSetDateTime.date())
            self.cmbQuoting.setEndDate(self.eventEditor.eventDate)
            self.cmbQuoting.setClientId(self.eventEditor.clientId)
            self.cmbQuoting.popupView.setTable('QuotaType')
            self.cmbQuoting.setCurrentIndex(0)


    def getPreliminaryDiagnostics(self):
        if hasattr(self.eventEditor, 'modelPreliminaryDiagnostics'):
            for row, record in enumerate(self.eventEditor.modelPreliminaryDiagnostics.items()):
                return forceString(record.value('MKB'))
        else:
            return None


    def getFinalDiagnostics(self):
        if hasattr(self.eventEditor, 'modelFinalDiagnostics'):
            for row, record in enumerate(self.eventEditor.modelFinalDiagnostics.items()):
                return forceString(record.value('MKB'))
        elif hasattr(self.eventEditor, 'getModelFinalDiagnostics'):
            for row, record in enumerate(self.eventEditor.getModelFinalDiagnostics().items()):
                return forceString(record.value('MKB'))
        else:
            return None


    def getQuotaTypeId(self):
        return self.eventEditor.getQuotaTypeId() if (self.eventEditor and hasattr(self.eventEditor, 'getQuotaTypeId')) else None


    def mousePressEvent(self, event):
        parent = self.parentWidget()
        if parent is not None:
            opt=QtGui.QStyleOptionComboBox()
            opt.init(parent)
            arrowRect = parent.style().subControlRect(
                QtGui.QStyle.CC_ComboBox, opt, QtGui.QStyle.SC_ComboBoxArrow, parent)
            arrowRect.moveTo(parent.mapToGlobal(arrowRect.topLeft()))
            if (arrowRect.contains(event.globalPos()) or self.rect().contains(event.pos())):
                self.setAttribute(Qt.WA_NoMouseReplay)
        QtGui.QFrame.mousePressEvent(self, event)


    def closeEvent(self, event):
        preferences = self.tblPatientModel.savePreferences()
        setPref(QtGui.qApp.preferences.windowPrefs, 'CPatientModelComboBoxPopup', preferences)
        QtGui.QFrame.closeEvent(self, event)


    def eventFilter(self, watched, event):
        if watched == self.tblPatientModel:
            if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Select):
                event.accept()
                index = self.tblPatientModel.currentIndex()
                self.tblPatientModel.emit(SIGNAL('doubleClicked(QModelIndex)'), index)
                return True
        return QtGui.QFrame.eventFilter(self, watched, event)


    def on_buttonBox_reset(self):
        self.chkPreviousMKB.setChecked(True)
        self.chkQuotingEvent.setChecked(True)
        self.on_chkQuotingEvent_clicked(True)
        self.on_buttonBox_apply()


    def on_buttonBox_apply(self):
        QtGui.qApp.setWaitCursor()
        try:
            idList = self.getlPatientModelIdList()
            self.setPatientModelIdList(idList, None)
        finally:
            QtGui.qApp.restoreOverrideCursor()


    def setPatientModelIdList(self, idList, posToId):
        if idList:
            self.tblPatientModel.setIdList(idList, posToId)
            self.tabWidget.setCurrentIndex(0)
            self.tabWidget.setTabEnabled(0, True)
            self.tblPatientModel.setFocus(Qt.OtherFocusReason)
        else:
            self.tabWidget.setCurrentIndex(1)
            self.tabWidget.setTabEnabled(0, False)
            self.cmbQuoting.setFocus(Qt.OtherFocusReason)


    def getlPatientModelIdList(self):
        db = QtGui.qApp.db
        tableRBPatientModel = db.table('rbPatientModel')
        cond = []
        quotaTypeId = self.cmbQuoting.value()
        name = forceString(self.edtName.text()).strip()
        if quotaTypeId:
            cond.append(tableRBPatientModel['quotaType_id'].eq(quotaTypeId))
        if self.chkPreviousMKB.isChecked():
            MKB = self.getPreliminaryDiagnostics()
            if MKB:
                cond.append(tableRBPatientModel['MKB'].like(MKB[:3] + '%'))
        if self.chkFinalMKB.isChecked():
            MKB = self.getFinalDiagnostics()
            if MKB:
                cond.append(tableRBPatientModel['MKB'].like(MKB[:3] + '%'))
        if self.chkQuotingEvent.isChecked():
            quotaTypeId = self.getQuotaTypeId()
            if quotaTypeId:
                cond.append(tableRBPatientModel['quotaType_id'].eq(quotaTypeId))
        if self._endDate:
            cond.append(db.joinOr([tableRBPatientModel['endDate'].ge(self._endDate),
                                    tableRBPatientModel['endDate'].isNull()]))
        if name:
            cond.append(tableRBPatientModel['name'].like('%' + name + '%'))
        idList = db.getDistinctIdList(tableRBPatientModel, [tableRBPatientModel['id'].name()], cond)
        return idList


    def setPatientModel(self, patientModelId):
        if patientModelId:
            self.setPatientModelIdList([patientModelId], patientModelId)
        else:
            self.setPatientModelIdList([], None)


    def selectPatientModel(self, patientModelId):
        self.patientModelId = patientModelId
        self.emit(SIGNAL('patientModelSelected(int)'), patientModelId)
        self.close()


    def setDateFilter(self, date):
        u'Устанавливает фильтр по rbPatientModel.endDate'
        self._endDate = date
        self.on_buttonBox_apply()


    @pyqtSignature('QModelIndex')
    def on_tblPatientModel_doubleClicked(self, index):
        if index.isValid():
            if (Qt.ItemIsEnabled & self.tableModel.flags(index)):
                patientModelId = self.tblPatientModel.currentItemId()
                self.selectPatientModel(patientModelId)


    @pyqtSignature('bool')
    def on_chkQuotingPatientOnly_toggled(self, value):
        if value and self.eventEditor:
            self.cmbQuoting.setBegDate(self.eventEditor.eventSetDateTime.date())
            self.cmbQuoting.setEndDate(self.eventEditor.eventDate)
            self.cmbQuoting.setClientId(self.eventEditor.clientId)
        else:
            self.cmbQuoting.setBegDate(QDate())
            self.cmbQuoting.setEndDate(QDate())
            self.cmbQuoting.setClientId(None)
        self.cmbQuoting.popupView.setTable('QuotaType')
        self.cmbQuoting.setCurrentIndex(0)


    @pyqtSignature('bool')
    def on_chkQuotingEvent_clicked(self, checked):
        quotaTypeId = None
        if checked:
            quotaTypeId = self.getQuotaTypeId()
        self.cmbQuoting.setValue(quotaTypeId)


    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_buttonBox_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_buttonBox_reset()


class CPatientModelTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.addColumn(CTextCol(u'Код', ['code'], 30))
        self.addColumn(CTextCol(u'Модель пациента', ['name'], 30))
        self.addColumn(CTextCol(u'Диагнозы', ['MKB'], 30))
        self.addColumn(CRefBookCol(u'Квота', ['quotaType_id'], 'QuotaType', 20))
        self.addColumn(CDateCol(u'Дата окончания действия', ['endDate'],  10))
        self.setTable('rbPatientModel')


    def flags(self, index):
        return Qt.ItemIsEnabled|Qt.ItemIsSelectable
#        row = index.row()
#        record = self.getRecordByRow(row)
#        enabled = True
#        if enabled:
#            return Qt.ItemIsEnabled|Qt.ItemIsSelectable
#        else:
#            return Qt.ItemIsSelectable


class CPatientModelComboBox(CROComboBox):
    __pyqtSignals__ = ('valueChanged()',
                      )

    def __init__(self, parent):
        CROComboBox.__init__(self, parent)
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self._popup=None
        self.patientModelId = None
        self.quotingId = None
        self.previousMKB = False
        self.eventEditor = None
        self._endDate = None


    def showPopup(self):
        if not self.isReadOnly():
            if not self._popup:
                self._popup = CPatientModelComboBoxPopup(self, self.eventEditor)
                self._popup.setDateFilter(self._endDate)
                self.connect(self._popup, SIGNAL('patientModelSelected(int)'), self.setValue)

            pos = self.rect().bottomLeft()
            pos2 = self.rect().topLeft()
            pos = self.mapToGlobal(pos)
            pos2 = self.mapToGlobal(pos2)
            size = self._popup.sizeHint()
            #width= max(size.width(), self.width())
            #size.setWidth(width)
            screen = QtGui.QApplication.desktop().availableGeometry(pos)
            size.setWidth(screen.width()) # распахиваем на весь экран
            pos.setX( max(min(pos.x(), screen.right()-size.width()), screen.left()) )
            pos.setY( max(min(pos.y(), screen.bottom()-size.height()), screen.top()) )
            self._popup.move(pos)
            self._popup.resize(size)
            self._popup.eventEditor = self.eventEditor
            self._popup.cmbQuoting.setClientId(None)
            self._popup.cmbQuoting.setBegDate(QDate())
            self._popup.cmbQuoting.setEndDate(QDate())
            self._popup.on_chkQuotingEvent_clicked(True)
            self._popup.show()
            self._popup.setPatientModel(self.patientModelId)
            self._popup.on_buttonBox_apply()


    def getQuotaTypeId(self):
        return self.eventEditor.getQuotaTypeId() if (self.eventEditor and hasattr(self.eventEditor, 'getQuotaTypeId')) else None


    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor


    def setValue(self, patientModelId):
        toEmit = self.patientModelId != patientModelId
        self.patientModelId = patientModelId
        self.updateText()
        if toEmit:
            self.emitValueChanged()


    def value(self):
        return self.patientModelId


    def updateText(self):
        db = QtGui.qApp.db
        tableRBPatientModel = db.table('rbPatientModel')
        record = db.getRecordEx(tableRBPatientModel, [tableRBPatientModel['code'], tableRBPatientModel['name']], [tableRBPatientModel['id'].eq(self.patientModelId)])
        text = ''
        if record:
            text = ' - '.join([field for field in (forceString(record.value('code')), forceString(record.value('name'))) if field])
        self.setEditText(text)


    def keyPressEvent(self, event):
        if self.model().isReadOnly():
            event.accept()
        else:
            key = event.key()
            if key == Qt.Key_Delete:
                self.setValue(None)
                event.accept()
            elif key == Qt.Key_Backspace: # BS
                self.setValue(None)
                event.accept()
            else:
                CROComboBox.keyPressEvent(self, event)


    def emitValueChanged(self):
        self.emit(SIGNAL('valueChanged()'))


    def setDateFilter(self, date):
        u'Устанавливает фильтр по rbPatientModel.endDate'
        self._endDate = date
        if self._popup:
            self._popup.setDateFilter(date)

