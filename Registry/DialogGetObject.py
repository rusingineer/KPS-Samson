# coding=utf-8
############################################################################
#
# Copyright (C) 2023 SAMSON Group. All rights reserved.
#
############################################################################
#
# Это программа является свободным программным обеспечением.
# Вы можете использовать, распространять и/или модифицировать её согласно
# условиям GNU GPL версии 3 или любой более поздней версии.
#
############################################################################
from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignature, Qt

from Registry.Ui_DialogGetObject import Ui_DialogGetObject
from library.DialogBase import CDialogBase
from library.Utils import forceRef, forceInt, forceString


class CDialogGetObject(CDialogBase, Ui_DialogGetObject):
    objectNameDict = {
        'Action': u'Действие',
        'Event': u'Событие',
        'Client': u'Регистрационная карточка',
        'ProphylaxisPlanning': u'ККДН',
    }

    def __init__(self, parent, clientId, fileItem):
        CDialogBase.__init__(self, parent)
        self.addObject('btnGetFileObject', QtGui.QPushButton(u'Перейти к объекту', self))
        self.setupUi(self)

        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.buttonBox.addButton(self.btnGetFileObject, QtGui.QDialogButtonBox.ActionRole)
        self.setWindowTitle(u'Свойства объекта')

        self.clientId = clientId
        self.objectId = forceInt(fileItem._record.value('master_id'))
        self.objectTable = forceString(fileItem._record.value('objectTableName'))
        self.objectDate = fileItem.lastModified.toString("yyyy-MM-dd")

        self.edtObjectId.setText(str(self.objectId) if self.objectId else '')
        self.edtObjectName.setText(CDialogGetObject.objectNameDict[self.objectTable] if self.objectTable else '')
        self.edtObjectTable.setText(self.objectTable if self.objectTable else '')
        self.edtObjectDate.setText(self.objectDate if self.objectDate else '')

    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        if self.buttonBox.standardButton(button) == QtGui.QDialogButtonBox.Cancel:
            self.reject()

    @pyqtSignature('')
    def on_btnGetFileObject_clicked(self):
        targetObject = self.edtObjectTable.text()
        dialog = None
        widget = None
        if targetObject == 'Action':
            from Events.ActionEditDialog import CActionEditDialog
            dialog = CActionEditDialog(self)
            widget = dialog.btnAttachedFiles
            dialog.load(self.edtObjectId.text())
        elif targetObject == 'Event':
            from Events.EditDispatcher import getEventFormClass
            eventId = self.edtObjectId.text()
            formClass = getEventFormClass(eventId)
            self.close()
            if self.parent().parent().parent().objectName() == 'tabWidget':
                widget = None
                tabCount = self.parent().parentWidget().count()
                self.parent().parentWidget().parentWidget().setCurrentIndex(tabCount - 1)
            else:
                dialog = formClass(widget)
                dialog.load(eventId)
                widget = dialog.tabNotes.btnAttachedFiles
        elif targetObject == 'Client':
            from Registry.ClientEditDialog import CClientEditDialog
            dialog = CClientEditDialog(None)
            widget = dialog.btnAttachedFiles
            dialog.load(self.clientId)
        elif targetObject == 'ProphylaxisPlanning':
            from Surveillance.SurveillancePlanningDialog import CSurveillancePlanningEditDialog
            dispanserItems = getDiagnosticRecord(self.edtObjectId.text())
            dialog = CSurveillancePlanningEditDialog(self)
            widget = dialog.btnAttachedFiles
            dialog.setEventEditor(self)
            db = QtGui.qApp.db
            tableE = db.table('Event')
            eventId = forceRef(dispanserItems[0].value('event_id'))
            eventRecord = db.getRecordEx(tableE, u'*', [tableE['id'].eq(eventId), tableE['deleted'].eq(0)], u'Event.setDate DESC')
            dialog.setEventRecord(eventRecord)
            dialog.setDiagnosticEventLastRecords(dispanserItems)
            dialog.setDiagnosticRecords(dispanserItems)
        if dialog:
            self.close()
            try:
                if widget:
                    QtGui.qApp.restoreOverrideCursor()
                    dialog.setFocusToWidget(widget)
                    if dialog.exec_():
                        pass
            finally:
                dialog.deleteLater()


def getDiagnosticRecord(prophylaxisPlanningId):
    db = QtGui.qApp.db
    tablePP = db.table('ProphylaxisPlanning')
    tableD = db.table('Diagnosis')
    tableD2 = db.table('Diagnostic')
    cols = [
        u'Diagnostic.*',
        tableD['MKB'],
        tableD['MKBEx'],
        tableD['dispanserBegDate'],
        tableD['dispanser_id'].alias('diagnosisDispanser_id'),
    ]
    query = tablePP.join(tableD, tableD['client_id'].eq(tablePP['client_id']))
    query = query.join(tableD2, tableD2['diagnosis_id'].eq(tableD['id']))
    cond = [
        tablePP['id'].eq(prophylaxisPlanningId),
        tablePP['deleted'].eq(0),
        tableD['MKB'].eq(tablePP['MKB']),
        tableD['deleted'].eq(0),
        tableD2['deleted'].eq(0),
    ]
    record = db.getRecordList(query, cols, cond)
    return record
