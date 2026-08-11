# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2016-2026 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
##
## Кнопка, скрывающая под собой список прикреплённых файлов и её popup
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QSize, pyqtSignal

from .AttachedFile         import CAttachedFilesModel
from .AttachFilesPopup     import CAttachFilesPopup
from .AttachFilesTable     import CAttachFilesTable
from .AttachFilesTableFlag import CAttachFilesTableFlag

from library.MSCAPI        import MSCApi
from library.MSCAPI.certErrors import ECertNotFound

from Users.Rights              import urCanAttachFile, urCanSignForOrganisation
from library.Utils import forceInt


class CAttachButton(QtGui.QPushButton):
    """Кнопка, скрывающая под собой список прикреплённых файлов"""
    changed = pyqtSignal()

    def __init__(self, parent, text=None):
        QtGui.QPushButton.__init__(self, parent)
        if text:
            self.setText(text)
        self.modelFiles = CAttachedFilesModel(self)
        self.modelFiles.changed.connect(self.modelFiles_changed)
        self.pressed.connect(self.onPress)

        self._isEnabled = True       # разрешён с точки зрения Qt
        self._isAccessible = True    # разрешён (есть право добавлять или список файлов не пуст)
        self._forceShowDown = False  # показан popup (кнопку нужно рисовать нажатой)
        self._isSaveModel = False    # модель была сохранена
        self._isReadOnly = False     # нельзя изменять прикрепленные файлы

        self.modelFiles.setInterface(QtGui.qApp.webDAVInterface)

    def modelFiles_changed(self):
        self.changed.emit()

    def getIsSaveModel(self):
        return self._isSaveModel

    def setTable(self, tableName):
        self.modelFiles.setTable(tableName)

    def loadItems(self, masterId):
        self.modelFiles.loadItems(masterId)
        if self.modelFiles.rowCount() == 0 and not QtGui.qApp.userHasRight(urCanAttachFile):
            self._isAccessible = False
        else:
            self._isAccessible = True
        self.__setEnabled()

    def saveItems(self, masterId):
        self.modelFiles.saveItems(masterId, saveOnlyChanged = True)
        self._isSaveModel = True

    def setEnabled(self, val):
        self._isEnabled = val
        self.__setEnabled()

    def __setEnabled(self):
        interface = QtGui.qApp.webDAVInterface
        QtGui.QPushButton.setEnabled(self, self._isEnabled and self._isAccessible and bool(interface) )

    def sizeHint(self):
        self.ensurePolished()
        style = self.style()
        styleOptions = QtGui.QStyleOptionButton()
        QtGui.QPushButton.initStyleOption(self, styleOptions)
        styleOptions.features |= styleOptions.HasMenu

        w = h = 0
        icon = self.icon()
        if icon and not icon.isNull():
            iconSize = self.iconSize()
            w += iconSize.width()
            h = max(h, iconSize.height())
        text = self.text() or 'XXXX'
        fontMetrics = self.fontMetrics()
        textSize = fontMetrics.size(Qt.TextShowMnemonic, text)
        w += textSize.width()
        h = max(h, textSize.height())
        # место для индикатора меню
        w += style.pixelMetric(QtGui.QStyle.PM_MenuButtonIndicator, styleOptions, self)
        sizeHint = style.sizeFromContents(QtGui.QStyle.CT_PushButton,  # ContentsType type,
                                          styleOptions,                # const QStyleOption * option,
                                          QSize(w, h),                 # const QSize & contentsSize,
                                          self                         # const QWidget * widget = 0
                                         )
        return sizeHint.expandedTo(QtGui.qApp.globalStrut())

    def paintEvent(self, event):
        style = self.style()
        styleOptions = QtGui.QStyleOptionButton()
        QtGui.QPushButton.initStyleOption(self, styleOptions)

        if self.isDown() or self._forceShowDown:
            styleOptions.state &= ~style.State_Raised
            styleOptions.state |= style.State_Sunken

        if self.modelFiles.isNotEmpty():
            styleOptions.features |= styleOptions.HasMenu
        styleOptions.text = self.text()
        styleOptions.icon = self.icon()

        painter = QtGui.QPainter(self)
        style.drawControl(QtGui.QStyle.CE_PushButton, # ControlElement element
                          styleOptions,               # const QStyleOption * option
                          painter,                    # QPainter * painter
                          self                        # const QWidget * widget = 0
                          )

    def setAttachedFileItemList(self, attachedFileItemList):
        self.modelFiles.setAttachedFileItemList(attachedFileItemList)
    
    def setAction(self, action):
        self.modelFiles.setAction(action)

    def showPopup(self):
        popup = CAttachFilesPopup(self)
        popup.setFlags(CAttachFilesTableFlag.canAnything)
        popup.setModel(self.modelFiles)
        try:
            self._forceShowDown = True
            self.setDown(True)
            self.repaint()
            popup.exec_()
        finally:
            self._forceShowDown = False
            self.setDown(False)
            self.repaint()

    def onPress(self):
        if self.modelFiles.isNotEmpty():
            self.showPopup()
        else:
            if QtGui.qApp.userHasRight(urCanAttachFile):
                self.selectAndUploadFiles()

    def selectAndUploadFiles(self):
        ofr = CAttachFilesTable.selectFiles(self)
        if ofr:
            self.modelFiles.uploadFiles([unicode(fn) for fn in ofr])

    def getSignAndAttachHandler(self):
        def handler(items, execSnils=None, requireSignerPerson = 0, silent = False):
            userSignatures = []
            orgSignatures = []
            api = None
            try:
                api = MSCApi(QtGui.qApp.getCsp())
                userCert = QtGui.qApp.getUserCert(api)
            except:
                userCert = None
            if userCert and execSnils is not None and execSnils != 'empty':
                userSnils = userCert.snils()
                if forceInt(execSnils) == forceInt(userSnils):
                    try:
                        with userCert.provider() as master:  # для исключения массового запроса пароля
                            assert master  # silence pyflakes

                            # for fileName, fileBytes in items:
                            for item in items:
                                userSignatures.append(userCert.createDetachedSignature(item[1]))
                                # userSignatures.append(userCert.createDetachedSignature(fileBytes))
                    except:
                        userSignatures = [None] * len(items)
                else:
                    userSignatures = [None] * len(items)
                    if requireSignerPerson == 1:
                        informationText = (u'Внимание!\nПодпись в настройках не соответствует подписи назначившего!'
                                           u'\nДокумент не подписан!')
                    else:
                        informationText = (u'Внимание!\nПодпись в настройках не соответствует подписи исполнителя!'
                                           u'\nДокумент не подписан!')
                    if not silent:
                        QtGui.QMessageBox.information(self,
                                                    u'Прикрепить и подписать',
                                                    informationText,
                                                    QtGui.QMessageBox.Ok,
                                                    QtGui.QMessageBox.Ok
                                                    )
            elif userCert and (execSnils is None or execSnils == 'empty'):
                try:
                    with userCert.provider() as master:  # для исключения массового запроса пароля
                        assert master  # silence pyflakes

                        for item in items:
                            userSignatures.append(userCert.createDetachedSignature(item[1]))
                except:
                    userSignatures = [None] * len(items)
            else:
                userSignatures = [None] * len(items)

            orgCert = None
            if api and QtGui.qApp.userHasRight(urCanSignForOrganisation):
                try:
                    orgCert = QtGui.qApp.getOrgCert(api)
                except ECertNotFound:
                    pass
            if orgCert is None:
                orgSignatures = [None]*len(items)
            elif userCert is not None and orgCert.sha1() == userCert.sha1():
                orgSignatures = userSignatures
            else:
                try:
                    with orgCert.provider() as master:  # для исключения массового запроса пароля
                        assert master  # silence pyflakes

                        for item in items:
                            orgSignatures.append(orgCert.createDetachedSignature(item[1]))
                        # for fileName, fileBytes in items:
                        #     orgSignatures.append(orgCert.createDetachedSignature(fileBytes))
                except:
                    orgSignatures = [None] * len(items)
            # for i, (fileName, fileBytes, templateId, html) in enumerate(items):
            for i, item in enumerate(items):
                fileName = item[0]
                fileBytes = item[1]
                html = ''
                templateId = None
                if len(item) >= 3:
                    templateId = item[2]
                    if len(item) == 4:
                        html = item[3]

                if userSignatures[i] is None:
                    # Не даём подписать орг. если не подписан врачом
                    orgSignatures[i] = None

                self.modelFiles.uploadBytes(fileName,
                                            fileBytes,
                                            userSignatures[i],
                                            orgSignatures[i],
                                            templateId,
                                            html,
                                            )
            self.update()
            return bool(userSignatures[0]), userSignatures[0], orgSignatures[0]

        if self.isEnabled() and QtGui.qApp.userHasRight(urCanAttachFile):
            return handler
        else:
            return None
