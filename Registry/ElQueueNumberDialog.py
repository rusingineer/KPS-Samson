# -*- coding: utf-8 -*-

from PyQt4 import QtGui
from PyQt4.QtGui import QValidator

from Registry.Ui_ElQueueNumberDialog import Ui_ElQueueNumberDialog


class DigitValidator(QValidator):
    def validate(self, input_str, pos):
        queue_number = input_str.toUtf8()
        queue_number = queue_number.data().decode('utf8')
        if pos == 1:
            if ord(queue_number[pos - 1]) < ord(u'А') or ord(queue_number[pos - 1]) > ord(u'Я'):
                if ord(queue_number[pos - 1]) < ord(u'а') or ord(queue_number[pos - 1]) > ord(u'я'):
                    return (QtGui.QValidator.Invalid, pos)
        elif pos > 1:
            if ord(queue_number[pos - 1]) < ord(u'0') or ord(queue_number[pos - 1]) > ord(u'9'):
                return (QtGui.QValidator.Invalid, pos)
        return (QtGui.QValidator.Acceptable, pos)


class CElQueueNumberDialog(QtGui.QDialog, Ui_ElQueueNumberDialog):
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.btnOK.clicked.connect(self.on_click_btn_ok)
        self.btnCancel.clicked.connect(self.on_click_btn_cancel)
        self.btnSkip.clicked.connect(self.on_click_btn_skip)
        self.leQueueNumber.setFocus()
        self.queue_number = ""

        validator = DigitValidator()
        self.leQueueNumber.setValidator(validator)

    def exec_(self):
        return QtGui.QDialog.exec_(self)

    def on_click_btn_ok(self):
        queue_number = self.leQueueNumber.text().toUtf8()
        queue_number = queue_number.data().decode('utf8')
        if not queue_number or queue_number == "":
            QtGui.QMessageBox.warning(self.parent(), u'Ошибка', u'Введите номер талончика электронной очереди!',
                                      QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)
            return
        r = True
        if ord(queue_number[0]) < ord(u'А') or ord(queue_number[0]) > ord(u'Я'):
            if ord(queue_number[0]) < ord(u'а') or ord(queue_number[0]) > ord(u'я'):
                r = False
        for one in queue_number[1:queue_number.__len__()]:
            if ord(one) < ord(u'0') or ord(one) > ord(u'9'):
                r = False
        if not r:
            QtGui.QMessageBox.warning(self.parent(), u'Ошибка', u'Номер талончика электронной очереди '
                                                                u'имеет неверный формат!',
                                      QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)
            return
        if queue_number.__len__() <= 1:
            QtGui.QMessageBox.warning(self.parent(), u'Ошибка', u'Номер талончика электронной очереди '
                                                                u'имеет неверный формат! (Пример: Б5)',
                                      QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)
            return
        razn = 0 # Это если строчная буква введена
        if ord(queue_number[0]) >= ord(u'а') and ord(queue_number[0]) <= ord(u'я'):
            razn = 32
        queue_number = str(ord(queue_number[0]) - razn) + str(queue_number[1:queue_number.__len__()])
        self.queue_number = int(queue_number)
        self.accept()

    def on_click_btn_cancel(self):
        self.reject()

    def on_click_btn_skip(self):
        self.queue_number = 0
        self.accept()
