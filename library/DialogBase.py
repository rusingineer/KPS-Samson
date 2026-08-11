# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2025 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
import platform

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QEvent, QAbstractItemModel, SIGNAL
from library.PreferencesMixin import CDialogPreferencesMixin
from library.SafeCleanupMixin import SafeCleanupMixin
from library.DateEdit import CDateEdit
from library.database import CSqlRecord


class CConstructHelperMixin:
    def addModels(self, name, model):
        modelName = 'model'+name
        self.__setattr__(modelName, model)
        model.setObjectName(modelName)
        selectionModelName = 'selectionModel'+name
        selectionModel = QtGui.QItemSelectionModel(model, self)
        self.__setattr__(selectionModelName, selectionModel)
        selectionModel.setObjectName(selectionModelName)


    def addObject(self, name, object):
        self.__setattr__(name, object)
        object.setObjectName(name)


    def setModels(self, widget, dataModel, selectionModel=None):
        widget.setModel(dataModel)
        if selectionModel:
            widget.setSelectionModel(selectionModel)


    def addBarcodeScanAction(self, name):
        action = QtGui.QAction(self)
        self.addObject(name, action)
        action.setShortcuts([QtGui.QKeySequence(Qt.CTRL+Qt.Key_B),
                             QtGui.QKeySequence(Qt.CTRL+Qt.SHIFT+Qt.Key_B),
                            ]
                           )
        # для регистрации hotkey в заданном widget
        # не забываем сделать widget.addAction(action) или self.addAction(action)


class CDialogBase(QtGui.QDialog, CDialogPreferencesMixin, CConstructHelperMixin, SafeCleanupMixin):
    forListView  = 0
    forSelection = 1

    # реaкция на выход из формы "крестиком" или кнопкой escape
    cdDiscard       = 1 # данные не сохранять
    cdContinueEdit  = 2 # продолжить редактирование
    cdSave          = 3 # сохранить


    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        # TT 3632 "Отсутствие кнопок масштабирования в Альте"
        if 'alt' in platform.uname()[2]:
            self.setWindowFlags(Qt.Window
                                | Qt.WindowTitleHint
                                | Qt.WindowMinMaxButtonsHint
                                | Qt.WindowSystemMenuHint
                                | Qt.WindowCloseButtonHint)
            self.setWindowModality(Qt.ApplicationModal)
        self.__isDirty  = False # данные диалога изменены
        self.__readOnly = False # данные диалога не требуется сохранять.
        self.__title = ''
        self.statusBar = None


    def _updateTitle(self):
        actualTitle = self.__title
        if self.__readOnly:
            if '[*]' in actualTitle:
                actualTitle = actualTitle.replace('[*]', u'(только просмотр)')
        QtGui.QDialog.setWindowTitle(self, actualTitle)


    def _updateSaveButton(self):
        saveChangesRoles = ( QtGui.QDialogButtonBox.AcceptRole,
                             QtGui.QDialogButtonBox.ApplyRole,
                           )
        for buttonBox in self.findChildren(QtGui.QDialogButtonBox):
            for button in buttonBox.buttons():
                role = buttonBox.buttonRole(button)
                if role in saveChangesRoles:
                    button.setEnabled(not self.__readOnly)


    def setWindowTitle(self,  title):
        title = unicode(title)
        if '[*]' not in title:
            title = title + ' [*]'
        self.__title = title
        self._updateTitle()


    def setWindowTitleEx(self, title):
        self.setWindowTitle(title)
        self.setObjectName(title)


    def setReadOnly(self, value=True):
        if self.__readOnly != value:
            self.__readOnly = value
            self._updateTitle()
            self._updateSaveButton()


    def isReadOnly(self):
        return self.__readOnly


    def isDirty(self):
        return self.__isDirty


    def setIsDirty(self, dirty=True):
        self.__isDirty = dirty
        self.setWindowModified(dirty)
        if hasattr(self, "_record"):
            if type(self._record) == CSqlRecord:
                self._record._dirty = dirty


    def saveData(self):
        return True


    def setWidgetVisible(self, widget):
        w = widget
        p = w.parent() if w is not None else None
        while w is not None and w != self:
            g = p.parent() if p is not None else None
            if isinstance(g, QtGui.QTabWidget):
                g.setCurrentIndex(g.indexOf(w))
            w, p = p, g
            # p = g


    def setFocusToWidget(self, widget, row=None, column=None):
        if widget is not None:
            self.setWidgetVisible(widget)
            if widget.hasFocus():
                widget.clearFocus()
            widget.setFocus(Qt.ShortcutFocusReason)
            widget.update()
            if isinstance(widget, QtGui.QTableView) and isinstance(row, int) and isinstance(column, int):
                widget.setCurrentIndex(widget.model().index(row, column))


    def checkUpdateMessage(self, message, edtBegDate, widget, date, row=None, column=None):
        res = QtGui.QMessageBox.warning( self,
                                         u'Внимание!',
                                         message,
                                         QtGui.QMessageBox.Ok|QtGui.QMessageBox.Cancel,
                                         QtGui.QMessageBox.Cancel)
        if res == QtGui.QMessageBox.Ok:
            if not date.isNull():
                edtBegDate.setDate(date)
            self.setFocusToWidget(widget, row, column)
            return False
        else:
            self.setFocusToWidget(widget, row, column)
            return False
        return True


    def checkUpdateDateTimeMessage(self, message, edtBegDate, edtBegTime, widget, datetime, row=None, column=None):
        res = QtGui.QMessageBox.warning( self,
                                         u'Внимание!',
                                         message,
                                         QtGui.QMessageBox.Ok|QtGui.QMessageBox.Cancel,
                                         QtGui.QMessageBox.Cancel)
        if res == QtGui.QMessageBox.Ok:
            if datetime and datetime.isValid():
                edtBegDate.setDate(datetime.date())
                edtBegTime.setTime(datetime.time())
            self.setFocusToWidget(widget, row, column)
            return False
        else:
            self.setFocusToWidget(widget, row, column)
            return False
        return True


    def checkValueMessage(self, message, skipable, widget, row=None, column=None, detailWdiget=None, setFocus=True):
        buttons = QtGui.QMessageBox.Ok
        if skipable:
            buttons = buttons | QtGui.QMessageBox.Ignore
        res = QtGui.QMessageBox.warning( self,
                                         u'Внимание!',
                                         message,
                                         buttons,
                                         QtGui.QMessageBox.Ok)
        if res == QtGui.QMessageBox.Ok:
            if setFocus:
                self.setFocusToWidget(widget, row, column)
                if isinstance(detailWdiget, QtGui.QWidget):
                    self.setFocusToWidget(detailWdiget, row, column)
            return False
        return True


    def checkValueMessageCritical(self, message, skipable, widget, row=None, column=None, detailWdiget=None,
                                  setFocus=True):
        buttons = QtGui.QMessageBox.Ok
        if skipable:
            buttons = buttons | QtGui.QMessageBox.Ignore
        res = QtGui.QMessageBox.critical(self if self.isVisible() else None,
                                         u'Внимание!',
                                         message,
                                         buttons,
                                         QtGui.QMessageBox.Ok)
        if res == QtGui.QMessageBox.Ok:
            if setFocus:
                self.setFocusToWidget(widget, row, column)
                if isinstance(detailWdiget, QtGui.QWidget):
                    self.setFocusToWidget(detailWdiget, row, column)
            return False
        return True


    def checkInputMessage(self, message, skipable, widget, row=None, column=None):
        return self.checkValueMessage(u'Необходимо указать %s' % message, skipable, widget, row, column)

    def checkValueMessageIgnore(self, message, skipable, widget, row=None, column=None):
        messageBox = QtGui.QMessageBox(self)
        messageBox.setWindowTitle(u'Внимание!')
        messageBox.setText(message)
        messageBox.addButton(QtGui.QPushButton(u'ОК'), QtGui.QMessageBox.ActionRole)
        if skipable:
            messageBox.addButton(QtGui.QPushButton(u'Игнорировать'), QtGui.QMessageBox.ActionRole)
        res = messageBox.exec_()
        if res == 0:
            self.setFocusToWidget(widget, row, column)
        return res

    def checkValueMessageIgnoreAll(self, message, skipable, widget, row=None, column=None, detailWdiget=None):
        messageBox = QtGui.QMessageBox()
        messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
        messageBox.setWindowTitle(u'Внимание!')
        messageBox.setText(message)
        messageBox.addButton(QtGui.QPushButton(u'ОК'), QtGui.QMessageBox.ActionRole)
        if skipable:
            messageBox.addButton(QtGui.QPushButton(u'Игнорировать'), QtGui.QMessageBox.ActionRole)
            messageBox.addButton(QtGui.QPushButton(u'Игнорировать все'), QtGui.QMessageBox.ActionRole)
        res = messageBox.exec_()
        if res == 0:
            self.setFocusToWidget(widget, row, column)
            if detailWdiget:
                self.setFocusToWidget(detailWdiget, row, column)
        return res


    def askSaveDiscardContinueEdit(self):
        if self.isDirty():
            msgBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning,
                                       u'Внимание!',
                                       u'Данные были изменены.\nСохранить данные?',
                                       QtGui.QMessageBox.Save | QtGui.QMessageBox.Discard | QtGui.QMessageBox.Cancel,
                                       self)
            msgBox.setWindowFlags(msgBox.windowFlags() | Qt.WindowStaysOnTopHint)
            msgBox.setDefaultButton(QtGui.QMessageBox.Save)
            #msgBox.setEscapeButton(QtGui.QMessageBox.Cancel)
            discardButton = msgBox.button(QtGui.QMessageBox.Discard)
            discardButton.setText(discardButton.parent().tr('Don\'t Save'))
            res = msgBox.exec_()
            return {QtGui.QMessageBox.Save: self.cdSave,  QtGui.QMessageBox.Discard:self.cdDiscard}.get(res, self.cdContinueEdit)
        return self.cdDiscard


    def done(self, result):
        if self.isReadOnly():
            scd = self.cdDiscard
        elif result < 0:    # закрытие из closeEvent или Esc
            scd = self.askSaveDiscardContinueEdit()
        elif result == 0:   # закрытие кнопкой отмены
            scd = self.cdDiscard
        else:               # закрытие кнопкой "ok"
            scd = self.cdSave

        if scd == self.cdDiscard:
            self.discardData()

        if scd == self.cdDiscard or (scd == self.cdSave and self.saveData()):
            self.saveDialogPreferences()
            if result < 0:
                result = 1 if scd == self.cdSave else 0
            QtGui.QDialog.done(self, result)

    def discardData(self):
        return

    def setVisible(self, visible):
        QtGui.QDialog.setVisible(self, visible)
        if visible:
            widget = self.focusWidget()
            if widget is not None:
                widget.clearFocus()
                widget.setFocus(Qt.ShortcutFocusReason)
                widget.update()


    def closeEvent(self, event):
#        self.saveDialogPreferences()
        if self.isVisible():
            self.setResult(-1)
            self.done(-1)
            if self.result() == QtGui.QDialog.Rejected:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            event.accept()
            self.close() # стандартный обработчик вызывает self.reject(), что не оставляет места для вопроса
                         # а я хочу задать вопрос - нужно сохранять/не нужно сохранять
        else:
            QtGui.QDialog.keyPressEvent(self, event)


    def event(self, event):
        if event.type() == QEvent.StatusTip and self.statusBar:
            self.statusBar.showMessage(event.tip())
            event.accept()
            return True
        else:
            return QtGui.QDialog.event(self, event)


    def on_textEditChanged(self):
        self.setIsDirty()

    def on_lineEditChanged(self, text):
        self.setIsDirty()

    def on_dateEditChanged(self, date):
        self.setIsDirty()

    def on_comboBoxChanged(self, index):
        self.setIsDirty()

    def on_checkBoxChanged(self, state):
        self.setIsDirty()

    def on_spinBoxChanged(self, value):
        self.setIsDirty()

    def on_abstractdataModelDataChanged(self, topLeft,  bottomRight):
        self.setIsDirty()

    def on_abstractdataModelRowsRemoved(self):
        self.setIsDirty()

    def setupDirtyCatherForObject(self, obj, exclude):
        if obj in exclude:
            return
        # Чтобы изменения фильтров в Мед карте не помечали события измененным
        if obj.objectName() == 'tabAmbCard':
            return
        for child in obj.children():
            if isinstance(child, QtGui.QLabel) or child in exclude:
                pass
            elif isinstance(child, CDateEdit):
                self.connect(child, SIGNAL('dateChanged(QDate)'), self.on_dateEditChanged)
            elif isinstance(child, QtGui.QLineEdit):
                self.connect(child, SIGNAL('textChanged(QString)'), self.on_lineEditChanged)
            elif isinstance(child, QtGui.QTextEdit):
                self.connect(child, SIGNAL('textChanged()'), self.on_textEditChanged)
            elif isinstance(child, QtGui.QDateEdit):
                self.connect(child, SIGNAL('dateChanged(QDate)'), self.on_dateEditChanged)
            elif isinstance(child, QtGui.QComboBox):
                self.connect(child, SIGNAL('currentIndexChanged(int)'), self.on_comboBoxChanged)
            elif isinstance(child, QtGui.QCheckBox):
                self.connect(child, SIGNAL('stateChanged(int)'), self.on_checkBoxChanged)
            elif isinstance(child, QtGui.QSpinBox):
                self.connect(child, SIGNAL('valueChanged(int)'), self.on_spinBoxChanged)
            elif isinstance(child, QAbstractItemModel):
                self.connect(child, SIGNAL('dataChanged(QModelIndex, QModelIndex)'), self.on_abstractdataModelDataChanged)
                self.connect(child, SIGNAL('removeRows()'), self.on_abstractdataModelRowsRemoved)
            else:
                self.setupDirtyCatherForObject(child, exclude)


    def setupDirtyCather(self, exclude={}):
        self.setupDirtyCatherForObject(self, exclude)


    def exec_(self):
        self.loadDialogPreferences()
        result = QtGui.QDialog.exec_(self)
        return result

    
    def deleteLater(self):
        if hasattr(self, 'safeDelete'):
            self.safeDelete()
        else:
            QtGui.QDialog.deleteLater(self)
