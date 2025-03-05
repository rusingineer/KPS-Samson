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

from PyQt4 import QtGui
from PyQt4.QtCore import QObject, QTimer, QEvent, Qt

class CTimeoutLogout(QObject):
    # Функционал закрытия окна по истечении таймера

    # parent - окно, которому нужен функционал
    def __init__(self, parent):
        QObject.__init__(self, parent)
        self.__timer = QTimer(self)
        self.__timer.setSingleShot(True)
        self.__timer.timeout.connect(self.__showTimeoutAlert)
        self.__msec = 0
        self.__objectDescr = u'окно'
        self.__childDialogsToClose = []
        self.__timeoutFunc = getattr(parent, 'reject', None)
        QtGui.qApp.installEventFilter(self)


    # Настроить и включить таймер:
    # millisecondsInterval - кол-во милисекунд, через которое окно должно закрыться
    # objectDescr - название того, что должно закрыться (окно, событие, действие, ...)
    # timeoutFunc - функция, которая вызывается при закрытии окна (если не указано, то через reject)
    def setup(self, millisecondsInterval, objectDescr=None, timeoutFunc=None):
        self.stop()
        try:
            self.__timer.timeout.disconnect()
        except:
            pass
        self.__timer.timeout.connect(self.__showTimeoutAlert)
        if objectDescr:
            self.__objectDescr = objectDescr
        if timeoutFunc:
            self.__timeoutFunc = timeoutFunc
        self.setInterval(millisecondsInterval)
        self.restart()


    def isActive(self):
        return self.__timer.isActive()


    def setInterval(self, millisecondsInterval):
        # вычитаем одну минуту для отображения окна с предупреждением
        self.__msec = int(millisecondsInterval) - 60000
        # assert self.__msec >= 60000 # минимум одна минута должна оставаться


    def stop(self):
        self.__timer.stop()


    def restart(self):
        self.__timer.stop()
        if self.__msec >= 60000:
            self.__timer.start(self.__msec)


    def changeObjectDescr(self, objectDescr):
        if objectDescr:
            self.__objectDescr = objectDescr


    def eventFilter(self, obj, event):
        if self.__msec < 60000:
            return False
        # типы событий, по которым перезапускается таймер
        resetEventTypes = (
            QEvent.KeyRelease,
            QEvent.MouseButtonRelease,
            QEvent.MouseMove,
            QEvent.ShortcutOverride,
        )
        if event.type() in resetEventTypes:
            self.restart()
        elif event.type() == QEvent.Show:
            reject = getattr(obj, 'reject', None)
            if callable(reject) and obj not in self.__childDialogsToClose:
                self.__childDialogsToClose.append(obj)
        elif event.type() == QEvent.Hide:
            if obj in self.__childDialogsToClose:
                self.__childDialogsToClose.remove(obj)
        return False


    def __showTimeoutAlert(self):
        self.__timeoutWindow = QtGui.QMessageBox()
        self.__timeoutWindow.setWindowFlags(self.__timeoutWindow.windowFlags() | Qt.WindowStaysOnTopHint)
        self.__timeoutWindow.setText(u'Через 1 минуту %s будет закрыто из-за отсутствия действий пользователя' % self.__objectDescr)
        self.__timeoutWindow.setWindowTitle(u'Внимание!')
        self.__timeoutWindow.setStandardButtons(QtGui.QMessageBox.Cancel)

        self.__timer.stop()
        self.__timer.timeout.disconnect()
        self.__timer.timeout.connect(self.__preTimeoutFunc)
        self.__timer.start(60000)

        if self.__timeoutWindow.exec_() == QtGui.QMessageBox.Cancel:
            self.__timer.stop()
            self.__timer.timeout.disconnect()
            self.__timer.timeout.connect(self.__showTimeoutAlert)
            self.__timer.start(self.__msec)


    def __preTimeoutFunc(self):
        self.__timer.timeout.disconnect()
        if self.__timeoutWindow:
            self.__timeoutWindow.done(0)
        for dialog in reversed(self.__childDialogsToClose):
            dialog.reject()
        if self.__timeoutFunc:
            self.__timeoutFunc()
