# -*- coding: utf-8 -*-

from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignature, SIGNAL

from Ui_SMPAddEventDialog import Ui_Dialog


class CSMPAddEventDialog(QtGui.QDialog, Ui_Dialog):
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.btnOK.clicked.connect(self.on_click_btnOK)

    def exec_(self):
        self.edtNote.clear()
        return QtGui.QDialog.exec_(self)

    def eventTypeId(self):
        return self.cmbEventType.itemData(self.cmbEventType.currentIndex()).toInt()[0]

    def note(self):
        return unicode(self.edtNote.text())

    @pyqtSignature('int')
    def on_cmbEventType_currentIndexChanged(self, index):
        res_id = str(self.cmbEventType.itemData(self.cmbEventType.currentIndex()).toString())
        self.edtNote.setEnabled(True)
        if res_id == "66":
            self.edtNote.setEnabled(False)
        pass

    def on_click_btnOK(self):
        res_id = str(self.cmbEventType.itemData(self.cmbEventType.currentIndex()).toString())
        if res_id == "77" and unicode(self.edtNote.text()).strip() == "":
            QtGui.QMessageBox.information(self, u'Информация', u'Поле примечание должно быть заполнено!',
                                          QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)
        else:
            self.accept()