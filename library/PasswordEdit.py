from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QLineEdit, QToolButton, QHBoxLayout, QStyle, QAction


class CPasswordEdit(QLineEdit):

    def __init__(self, parent):
        self.parent = parent
        super(CPasswordEdit,self).__init__(self.parent)

        self.visibleIcon = QtGui.QIcon(':/new/prefix1/icons/visiblePassword.png')
        self.hiddenIcon =QtGui.QIcon(':/new/prefix1/icons/invisiblePassword.png')

        self.password_shown = False
        self.ButtonShowPassword = QToolButton(self)
        self.ButtonShowPassword.setIcon(self.hiddenIcon)
        self.ButtonShowPassword.setStyleSheet("background: transparent; border: none;")

        layout = QHBoxLayout(self)
        layout.addWidget(self.ButtonShowPassword, 0, Qt.AlignRight)

        layout.setSpacing(0)
        layout.setMargin(5)
        self.connect(self.ButtonShowPassword, QtCore.SIGNAL("clicked()"), self.on_toggle_showPassword)


    def on_toggle_showPassword(self):
        if not self.password_shown:
            self.setEchoMode(QLineEdit.Normal)
            self.password_shown = True
            self.ButtonShowPassword.setIcon(self.visibleIcon)
        else:
            self.setEchoMode(QLineEdit.Password)
            self.password_shown = False
            self.ButtonShowPassword.setIcon(self.hiddenIcon)
