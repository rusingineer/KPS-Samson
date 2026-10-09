# -*- coding: utf-8 -*-
#############################################################################
##
## Страница настройки - панель настройки облачной телефонии "UISCom"
##
#############################################################################

from PyQt4 import QtGui

from library.Utils            import (
                                         forceBool,
                                         toVariant,
                                     )

from Ui_UISComPage import Ui_UISComPage


class CUISComPage(Ui_UISComPage, QtGui.QWidget):
    UISCOM_ENABLED = 'UISComClientEnabled'
    UISCOM_INC_CALL_NOTIFICATION_ENABLED = 'UISComIncCallNotificationEnabled'
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)


    def setProps(self, props):
        self.chkUISComEnabled.setChecked(forceBool(props.get(self.UISCOM_ENABLED, False)))
        self.chkIncCallNotification.setChecked(forceBool(props.get(self.UISCOM_INC_CALL_NOTIFICATION_ENABLED, True)))


    def getProps(self, props):
        props[self.UISCOM_ENABLED] = toVariant(bool(self.chkUISComEnabled.checkState()))
        props[self.UISCOM_INC_CALL_NOTIFICATION_ENABLED] = toVariant(bool(self.chkIncCallNotification.checkState()))