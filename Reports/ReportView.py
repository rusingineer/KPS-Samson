# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2026 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
##
## Просмотр, печать, сохранение и подписание печатных материалов
## (отчётов и документов)
##
#############################################################################
import base64
import codecs
import os.path
import re
import time
from cStringIO import StringIO

import requests

from Exchange.PyServices import getPyServices, CSchematronService
from PyQt4 import QtGui
from PyQt4.QtCore import (
    Qt,
    pyqtSignature,
    QFileInfo,
    QSizeF,
    QString,
    QTemporaryFile,
    QUrl,
    pyqtSlot, QObject, SIGNAL, QFileSystemWatcher)
from PyQt4.QtGui import QPrintPreviewDialog

from library.Attach.Utils import prepareSignedReport
from library.PDF.fixPdf import fixPdf
from library.SignaturePad import CSignaturePad
from library.Utils import forceBool, forceString, forceInt

from Users.Rights import urAdmin, urEditReportForm
from Reports.Ui_ReportView import Ui_ReportViewDialog
from library.PrintDebug.PrintTemplateDebugWindow import PrintTemplateDebugWindow


class CPageFormat(object):
    # page size
    A2 = QtGui.QPrinter.A2
    A3 = QtGui.QPrinter.A3
    A4 = QtGui.QPrinter.A4
    A5 = QtGui.QPrinter.A5
    A6 = QtGui.QPrinter.A6
    # page orientation
    Portrait = QtGui.QPrinter.Portrait
    Landscape = QtGui.QPrinter.Landscape
    #
    validPageSizes = { A2: A2, 'A2': A2,
                       A3: A3, 'A3': A3,
                       A4: A4, 'A4': A4,
                       A5: A5, 'A5': A5,
                       A6: A6, 'A6': A6,
                     }

    paperSizes =     { A2: (420, 594),
                       A3: (297, 420),
                       A4: (210, 297),
                       A5: (148, 210),
                       A6: (105, 148),
                     }

    validOrientations = { Portrait: Portrait,  'PORTRAIT': Portrait,  'P':Portrait,
                          Landscape:Landscape, 'LANDSCAPE':Landscape, 'L':Landscape
                     }


    @classmethod
    def getPaperRect(cls, paperSize):
        width, hieght = cls.paperSizes.get(paperSize, cls.paperSizes[cls.A4])
        return QSizeF(width, hieght)


    def __init__(self, 
                 pageSize=QtGui.QPrinter.A4,
                 orientation=QtGui.QPrinter.Portrait,
                 leftMargin=10,
                 topMargin=10,
                 rightMargin=10,
                 bottomMargin=10
                ):
        self.pageSize = pageSize
        self.pageRect = None # для custom size
        self.orientation = orientation
        self.leftMargin = leftMargin
        self.topMargin = topMargin
        self.rightMargin = rightMargin
        self.bottomMargin = bottomMargin


    def setupPrinter(self, printer):
        if printer:
            # printerInfo = QtGui.QPrinterInfo(printer)
            supportedSizes = [QtGui.QPrinter.A4, QtGui.QPrinter.A5] #  printerInfo.supportedPaperSizes()
            if self.pageSize == QtGui.QPrinter.Custom:
                printer.setPaperSize(self.pageRect, QtGui.QPrinter.Millimeter)
            elif self.pageSize in supportedSizes:
                printer.setPaperSize(self.pageSize)
            else:
                paperRect = self.getPaperRect(self.pageSize)
                printer.setPaperSize(paperRect, QtGui.QPrinter.Millimeter)
            printer.setOrientation(self.orientation)
            # printer.setPageMargins(self.leftMargin, self.topMargin, self.rightMargin, self.bottomMargin, QtGui.QPrinter.Millimeter)


    def updateFromPrinter(self, printer):
        self.pageSize = printer.pageSize()
        if self.pageSize == QtGui.QPrinter.Custom:
            self.pageRect = printer.paperSize(QtGui.QPrinter.Millimeter)
        else:
            self.pageRect = None
        self.orientation = printer.orientation()


    def setPageSize(self, size):
        if isinstance(size, basestring):
            size = size.upper().strip()
            customSize = re.match(r'^(\d+)\s*[xX]\s*(\d+)$', size)
            if customSize:
                self.pageSize = QtGui.QPrinter.Custom
                sizes = customSize.groups()
                self.pageRect = QSizeF(float(sizes[0]), float(sizes[1]))
                return ''
        validPageSize = self.validPageSizes.get(size, None)
        if validPageSize is not None:
            self.pageSize = validPageSize
            self.pageRect = None
            return ''
        else:
            return u'[Invalid page size "%s"]' % size


    def setOrientation(self, orientation):
        if isinstance(orientation, basestring):
            orientation = orientation.upper().strip()
        validOrientation = self.validOrientations.get(orientation, None)
        if validOrientation is not None:
            self.orientation = validOrientation
            return ''
        else:
            return u'[Invalid orientation "%s"]' % orientation


    def setMargins(self, margin):
        if isinstance(margin, (int, float)):
            self.leftMargin = margin
            self.topMargin = margin
            self.rightMargin = margin
            self.bottomMargin = margin
            return ''
        else:
            return u'[Invalid margin "%s"]' % margin


    def setLeftMargin(self, margin):
        if isinstance(margin, (int, float)):
            self.leftMargin = margin
            return ''
        else:
            return u'[Invalid left margin "%s"]' % margin


    def setTopMargin(self, margin):
        if isinstance(margin, (int, float)):
            self.topMargin = margin
            return ''
        else:
            return u'[Invalid top margin "%s"]' % margin


    def setRightMargin(self, margin):
        if isinstance(margin, (int, float)):
            self.rightMargin = margin
            return ''
        else:
            return u'[Invalid right margin "%s"]' % margin


    def setBottomMargin(self, margin):
        if isinstance(margin, (int, float)):
            self.bottomMargin = margin
            return ''
        else:
            return u'[Invalid bottom margin "%s"]' % margin


def odtAvailable():
    try:
        if 'QTextDocumentWriter' not in QtGui.__dict__:
            return False
        return 'ODF' in QtGui.QTextDocumentWriter.supportedDocumentFormats()
    except:
        pass
    return False


class CReportViewDialog(QtGui.QDialog, Ui_ReportViewDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)

        self.btnRedo = QtGui.QPushButton(u'Повторить', self)
        self.btnRedo.setObjectName('btnRedo')
        self.btnRedo.setDefault(True)
        self.btnRedo.setVisible(False)
        
        self.btnPrint = QtGui.QPushButton(u'Печатать', self)
        self.btnPrint.setObjectName('btnPrint')
        self.btnPrint.setDefault(True)

        self.btnSignAndAttach = QtGui.QPushButton(u'Прикрепить и подписать', self)
        self.btnSignAndAttach.setObjectName('btnSignAndAttach')
        self.btnSignAndAttach.setEnabled(False)
        self.btnSignAndAttach.setVisible(False)

        self.btnSchematronValidate = QtGui.QPushButton(u'Проверить по схематрону', self)
        self.btnSchematronValidate.setObjectName('btnSchematronValidate')
        self.btnSchematronValidate.setVisible(False)
        self.btnSchematronValidate.setEnabled(False)

        self.btnSaveAction = QtGui.QPushButton(u'Сохранить в мероприятие', self)
        self.btnSaveAction.setObjectName('btnSaveAction')
        self.btnSaveAction.setEnabled(False)
        self.btnSaveAction.setVisible(False)

        self.tablet = None
        try:
            import hid
            import_hid = True
        except:
            import_hid = False
        if forceBool(QtGui.qApp.preferences.appPrefs.get('TabletSignEnable')) and import_hid:
            try:
                self.tablet = CSignaturePad(self)
                self.tablet.imageReceived.connect(self.setReportSignature)
            except Exception as e:
                self.tablet = None
                QtGui.QMessageBox.critical(self, u'Ошибка подключения планшета', unicode(e))
    
        if self.tablet:
            self.btnTablet = QtGui.QToolButton()
            self.btnTablet.setObjectName('btnTablet')
            self.btnTablet.setText(u'Планшет')
            self.btnTablet.setPopupMode(QtGui.QToolButton.InstantPopup)
            self.menuTablet = QtGui.QMenu(self.btnTablet)
            self.actGetSignature = QtGui.QAction(u"Получить подпись", self)
            self.actGetSignature.triggered.connect(self.getSignature)
            self.menuTablet.addAction(self.actGetSignature)
            self.actClearTablet = QtGui.QAction(u"Очистить", self)
            self.actClearTablet.triggered.connect(self.clearTabletScreen)
            self.menuTablet.addAction(self.actClearTablet)
            self.btnTablet.setMenu(self.menuTablet)

        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)

        if (QtGui.qApp.userHasRight(urEditReportForm) or QtGui.qApp.userHasRight(urAdmin)) and bool(QtGui.qApp.documentEditor()):
            self.btnEdit = QtGui.QPushButton(u'Редактировать', self)
            self.buttonBox.addButton(self.btnEdit, QtGui.QDialogButtonBox.ActionRole)
            self.btnEdit.clicked.connect(self.on_btnEdit_clicked)

        # self.buttonBox.addButton(self.btnSignAndAttach, QtGui.QDialogButtonBox.ActionRole)
        # self.buttonBox.addButton(self.btnSchematronValidate, QtGui.QDialogButtonBox.ActionRole)
        # self.buttonBox.addButton(self.btnEdit, QtGui.QDialogButtonBox.ActionRole)
        # self.buttonBox.addButton(self.btnSaveAction, QtGui.QDialogButtonBox.ActionRole)
        if self.tablet:
            self.buttonBox.addButton(self.btnTablet, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close | QtGui.QDialogButtonBox.Save)

        self.fileName = ''
        self.pageFormat = CPageFormat()
        self.actionButtons = []
        self.actions = []
        self.currentAction = None
        self.currentCdaCode = None
        self.supplements = {}
        self.isSignAndAttachResult = False
        self.textToPrinter = None
        self.textReport = None
        self.lineEditInterval.setEnabled(False)
        self.checkBoxInterval.setChecked(False)
        self.lineEditInterval.textChanged.connect(self.on_lineEditInterval_textChanged)
        self.txtReport.setOpenLinks(False)
        handler = self.handler
        QObject.connect(self.txtReport, SIGNAL("anchorClicked(const QUrl&)"), handler)
        self.btnPreview.clicked.connect(self.btnPreviewClicked)
        self.btnPrint.setFocus(Qt.OtherFocusReason)
        self._setFindVisible(False)
        self.pyServices = getPyServices(CSchematronService)
        self.txtReport.actFind.triggered.connect(self.on_actFind_triggered)
        self.templateId = None
        self.templateData = None
        self.signerPerson = None

    def on_lineEditInterval_textChanged(self):
        self.setText(self.textReport)

    def closeEvent(self, event):
        try:
            if self.tablet:
                self.tablet.close()
            event.accept()
        except Exception as e:
            print(str(e))

    def clearTabletScreen(self):
        self.tablet.clearScreen()
    
    def getSignature(self):
        self.tablet.getImage()

    def setReportSignature(self, imageData):
        content = self.templateContent.replace('<!-- signature_from_tablet -->', base64.encodestring(bytes(imageData))+'" />')
        content = content.replace('<!-- <img', ' <img')
        self.txtReport.setHtml(content)

    def enableDebugButton(self):
        self.fsWatcher = None
        self.debugView = PrintTemplateDebugWindow(self)
        self.btnPrintDebug = QtGui.QPushButton(u'Отладка', self)
        self.btnPrintDebug.setObjectName('btnPrintDebug')
        self.btnPrintDebug.setStyleSheet("QPushButton { background-color: #fff3c4 }")
        self.buttonBox.addButton(self.btnPrintDebug, QtGui.QDialogButtonBox.ActionRole)
        self.btnPrintDebug.clicked.connect(self.startPrintFormDebug)
    
    def setSignerPerson(self, personId):
        self.signerPerson = personId


    @pyqtSlot()
    def startPrintFormDebug(self):
        from library.PrintTemplates import compileAndExecTemplate
        dirPath = QtGui.QFileDialog.getExistingDirectory(
            QtGui.qApp.mainWindow,
            u'Выберите папку для сохранения шаблона:',
            QtGui.qApp.getTemplateDir(),
            QtGui.QFileDialog.ShowDirsOnly
        )
        if dirPath:
            self.debugView.showData(QtGui.qApp.debugPrintData.data)
            debugFilename = os.path.join(unicode(dirPath), u'debug_template.html')
            f = open(debugFilename, 'w')
            f.write(QtGui.qApp.debugPrintData.template.encode('utf8'))
            f.close()
            self.btnPrintDebug.setText(u'ИДЕТ ОТЛАДКА')
            self.btnPrintDebug.setStyleSheet("QPushButton { background-color: #ffcfc4 }")
            self.btnPrintDebug.setEnabled(False)
            self.fsWatcher = QFileSystemWatcher([debugFilename])
            self.fsWatcher.connect(self.fsWatcher, SIGNAL('fileChanged(QString)'), self.fileChanged)
            self.fileChanged(debugFilename)
            self.debugView.show()


    @pyqtSlot(str)
    def fileChanged(self, path):
        from library.PrintTemplates import compileAndExecTemplate
        try:
            with codecs.open(path, mode='r', encoding='utf-8') as templateFile:
                template = templateFile.read()
            startTime = time.time()
            templateResult = compileAndExecTemplate(
                documentName=QtGui.qApp.debugPrintData.name,
                template=template,
                data=QtGui.qApp.debugPrintData.data,
                pageFormat=QtGui.qApp.debugPrintData.pageFormat
            )
            self.setText(templateResult.content)
            execTime = time.time() - startTime
            self.debugView.showRenderTime(execTime)
        except Exception as e:
            import traceback
            errorTemplate = u"""<h1 style='color: red;'>%s</h1><pre>%s</pre>"""
            self.setText(errorTemplate % (unicode(e), traceback.format_exc()))


    def _setFindVisible(self, value):
        self._findVisible = value
        self.lblFind.setVisible(value)
        self.edtFind.setVisible(value)
        self.btnFindNext.setVisible(value)
        self.btnFindPrev.setVisible(value)
        self.chkCaseSensitive.setVisible(value)


    def on_actFind_triggered(self):
        self._findVisible = not self._findVisible
        self.lblFind.setVisible(self._findVisible)
        self.edtFind.setVisible(self._findVisible)
        self.btnFindNext.setVisible(self._findVisible)
        self.btnFindPrev.setVisible(self._findVisible)
        self.chkCaseSensitive.setVisible(self._findVisible)


    @pyqtSignature('')
    def on_btnFindNext_clicked(self):
        if self.chkCaseSensitive.isChecked():
            found = self.txtReport.find(self.edtFind.text(), QtGui.QTextDocument.FindCaseSensitively)
        else:
            found = self.txtReport.find(self.edtFind.text())
        if not found:
            QtGui.QMessageBox.information(self, u'', u'Поиск не дал результатов')


    @pyqtSignature('')
    def on_btnFindPrev_clicked(self):
        flags = QtGui.QTextDocument.FindBackward
        if self.chkCaseSensitive.isChecked():
            flags |= QtGui.QTextDocument.FindCaseSensitively
        found = self.txtReport.find(self.edtFind.text(), flags)
        if not found:
            QtGui.QMessageBox.information(self, u'', u'Поиск не дал результатов')


    @pyqtSlot("QUrl")
    def handler(self, url):
        if u'http' not in url.toString():
            if url.toString() != 'menu':
            #   self.reject()
                id_ = url.toString().toInt()[0]
                if id_ == 0:
                    if u'karta' in url.toString():
                        from Registry.RegistryWindow import CRegistryWindow
                        self.registry = CRegistryWindow(self)
                        karta = url.toString().split('_')
                        self.registry.editClient(karta[1])
                        return
                    if u'medKarta' in url.toString():
                        karta = url.toString().split('_')
                        QtGui.qApp.mainWindow.registry.findClient(karta[1])
                        QtGui.qApp.mainWindow.registry.tabMain.setCurrentIndex(2)
                        self.close()
                    elif u'event' in url.toString():
                       from Events.EventEditDialog import CEventEditDialog
                       self.eve = CEventEditDialog(self)
                       karta = url.toString().split('_')
                 #      self.eve.openEvent(int(karta[1]))
                       from Registry.RegistryWindow import CRegistryWindow
                       self.registry = CRegistryWindow(self)
                       karta = url.toString().split('_')
                       self.registry.on_btnEventEditTemplate_clicked(karta[1])
                       return
                    elif u'mseResult' in url.toString():
                        import posixpath
                        import cStringIO as StringIO

                        interface = QtGui.qApp.webDAVInterface
                        mse = url.toString().split('_')
                        localFile_old = None

                        if QtGui.qApp.templateMse:
                            for mseDoc in QtGui.qApp.templateMse:
                                if mseDoc[0] == mse[1]:
                                    localFile_old = mseDoc[1]
                        else:
                            return

                        if not localFile_old:
                            return

                        localFile = StringIO.StringIO(localFile_old.encode('utf-8'))

                        tmpDir = 'tmp/mseResult/' + str(mse[1])
                        name = str(mse[1]) + '.xml'
                        path = posixpath.join(tmpDir, name)

                        interface.client.mkdir(tmpDir)
                        interface.client.uploadStream(path=path, stream=localFile)
                        fileItem = interface.createTmpAttachedFileItem(path)

                        QtGui.QDesktopServices.openUrl(QUrl.fromEncoded(QtGui.qApp.getWebDAVUrl() + '/' + path))
                        return
                    elif u'orgStructure' in url.toString(): # пока ушел от этого
                        structure = url.toString().split('_')

                        from Registry.Utils import getClientInfo2
                        from library.PrintTemplates import getTemplate, compileAndExecTemplate

                        name, template, templateType, printBlank, code = getTemplate(111, True)

                        template = template.replace(u'_field_', unicode(structure[1]))

                        pageFormat = CPageFormat(pageSize=CPageFormat.A4, orientation=CPageFormat.Portrait, leftMargin=5,
                                                 topMargin=5,
                                                 rightMargin=5, bottomMargin=5)
                        content1, canvases = compileAndExecTemplate(template, self.data, pageFormat)

                        self.txtReport.setHtml(self.content + content1)
                    elif u'showContent' in url.toString():
                        replace = url.toString().split('_')
                        # первым делом смотрим то что подходит под наш параметр и скрыто и добавляем приставку "_replace_" для того чтобы скрыть то что надо сейчас и потом отобразить то что было скрыто

                        if '<!--'+replace[1]+']'+replace[1]+'-->' in self.templateContent:
                            self.templateContent = self.templateContent.replace('<!--' + replace[1] + '|','<!--' + replace[1] + '_replace_]' + replace[1] + '-->').replace('|' + replace[1] + '-->', '<!--' + replace[1] + '_replace_[' + replace[1] + '-->')
                            self.templateContent = self.templateContent.replace('<!--'+replace[1]+']'+replace[1]+'-->','<!--' + replace[1] + '|').replace('<!--'+replace[1]+'['+replace[1]+'-->', '|'+replace[1]+'-->')
                            self.templateContent = self.templateContent.replace('<!--' + replace[1] + '_replace_]' + replace[1] + '-->', '<!--' + replace[1] + ']' + replace[1] + '-->').replace('<!--' + replace[1] + '_replace_[' + replace[1] + '-->', '<!--' + replace[1] + '[' + replace[1] + '-->')
                        else:
                            self.templateContent = self.templateContent.replace('<!--'+replace[1]+'|','<!--'+replace[1]+']'+replace[1]+'-->').replace('|'+replace[1]+'-->','<!--'+replace[1]+'['+replace[1]+'-->')
                        self.txtReport.setHtml(self.templateContent)
                    elif u'portalMPI_' in url.toString():
                        karta = url.toString().split('_')
                        QtGui.qApp.mainWindow.registry.findClient(karta[1])
                        self.ind(karta[2], self.lineEditInterval.text())  
                    else:
                        QtGui.QMessageBox.critical(self.txtReport,
                                                   u'Ошибка',
                                                   u'Произошла ошибка при попытке распознать идентификатор шаблона',
                                                   QtGui.QMessageBox.Close)
                        self.txtReport.setHtml(self.content)
                else:
                    # self.lineEdit.setVisible(False)
                    self.ind(id_, self.lineEditInterval.text()) # переход к след шаблону по id типа <li><a href="194">Суперпродукты</a></li>
            else:
                self.lineEditInterval.setVisible(False)
                self.lineEditInterval.setText('')
                self.txtReport.setHtml(self.content)
        else:
            if u'download_Samson' in url.toString():
                documentsDir = unicode(QtGui.QDesktopServices.storageLocation(QtGui.QDesktopServices.DocumentsLocation))
                import os
                listDoc = [u'Документы(*.pdf *.odt *.ods *.doc *.xls *.docx *.xlsx)',
                 u'Изображения(*.png *.tiff *.jpg *.jpeg *.gif *.bmp *.xpm)',
                 u'Текстовые файлы(*.txt)',
                 u'Архивы(*.zip *.7z *.Z *.gz *.bz *.xz *.arj *.rar)',
                 u'Любые файлы(*)']
                file = requests.get(url.toString().replace('_download_Samson', ''), verify=False)
                if file.status_code == 200 and file.headers.get('Content-Disposition'):
                    fileName = file.headers.get('Content-Disposition').split('"')[1]
                    for doc in listDoc:
                        if '.' in fileName:
                            if fileName.split('.')[1] in doc:
                                tempDoc = doc
                        else:
                            tempDoc = doc
                    localFile = QtGui.QFileDialog.getSaveFileName(None,
                                                                  u'Сохранить файл',
                                                                  os.path.join(documentsDir, fileName.decode('utf-8')),
                                                                  tempDoc if tempDoc else u'Любые файлы(*)')
                    if localFile:
                        with open(unicode(localFile), 'wb') as stream:  # в случае отказа файл останется?
                            stream.write(file.content)
                            stream.close()
            elif u'_open' in url.toString():
                QtGui.QDesktopServices.openUrl(QUrl(url.toString().replace('_open', '')))
            else:
                self.txtReport.loadResource(2, url)

    def ind(self, id_, field):
        from Registry.Utils import getClientInfo2

        from library.PrintTemplates import getTemplate, compileAndExecTemplate
        clientId = QtGui.qApp._currentClientId
        clientInfo = getClientInfo2(clientId)

        name, template, templateType, printBlank, code = getTemplate(id_, True)

        if len(field) == 0:
            field = u'limit 10'
        else:
            field = "where lastName like '%" + unicode(field) + "%'"
        template = template.replace(u'_field_', unicode(field))

        data = {'client': clientInfo}

        pageFormat = CPageFormat(pageSize=CPageFormat.A4, orientation=CPageFormat.Portrait, leftMargin=5, topMargin=5,
                                 rightMargin=5, bottomMargin=5)
        templateResult = compileAndExecTemplate(name, template, data, pageFormat)


        self.txtReport.setHtml(templateResult.content)

    def btnPreviewClicked(self):
        defaultPrinterInfo = QtGui.QPrinterInfo.defaultPrinter()
        if not defaultPrinterInfo.isNull():
            printer = QtGui.QPrinter(defaultPrinterInfo, QtGui.QPrinter.HighResolution)
        else:
            printer = QtGui.QPrinter(QtGui.QPrinter.HighResolution)
        printer.setPrintRange(printer.AllPages)
        printer.setPaperSize(printer.A4)
        printer.setFullPage(False)
        if hasattr(printer, 'setNumCopies'):
            printer.setNumCopies(1)
        if hasattr(printer, 'setCopyCount'):
            printer.setCopyCount(1)
        self.setupPage(printer)
        self.previewDialog = QPrintPreviewDialog(printer, self)
        self.previewDialog.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowMaximizeButtonHint)
        self.previewDialog.paintRequested.connect(self.printPreview)
        self.previewDialog.setWindowTitle(u'Предпросмотр')
        self.previewDialog.exec_()


    def printPreview(self, printer):
        mm = forceString(self.lineEditInterval.displayText())
        if self.checkBoxInterval.isChecked() and mm.isdigit() and int(mm) > 12 and int(mm) <= 420:
            if self.textToPrinter:
                self.txtReport.setHtml(self.textToPrinter)
        printTextDocument(self.txtReport.document(), self.windowTitle(), self.pageFormat, printer)


    def setHtml(self, a, data = None):
        # self.txtReport = QWebView(self)
        self.content = a
        self.data = data
        self.txtReport.setHtml(a)

    def setWindowTitle(self, title):
        QtGui.QDialog.setWindowTitle(self, title)
        for x in ':?|()[]\"\';!*/\\':
            title = title.replace(x, '')
        self.fileName = title


    def setSignAndAttachHandler(self, signAndAttachHandler):
        self.signAndAttachHandler = signAndAttachHandler
        self.btnSignAndAttach.setEnabled(bool(self.signAndAttachHandler))
        if self.btnSignAndAttach.isEnabled():
            self.buttonBox.addButton(self.btnSignAndAttach, QtGui.QDialogButtonBox.ActionRole)
    
    
    def setRedoInfo(self, redoInfo):
        if redoInfo:
            self.btnRedo.setEnabled(True)
            if self.btnRedo.isEnabled():
                self.buttonBox.addButton(self.btnRedo, QtGui.QDialogButtonBox.ActionRole)
            self.templateId = redoInfo[0]
            self.templateData = redoInfo[1]
            self.signAndAttachHandler = redoInfo[2]


    def setCurrentAction(self, currentAction, propertiesData):
        self.currentAction = currentAction
        self.propertiesData = propertiesData
        self.btnSaveAction.setEnabled(bool(self.propertiesData))
        self.btnSaveAction.setVisible(bool(self.propertiesData))
        if self.btnSaveAction.isVisible():
            self.buttonBox.addButton(self.btnSaveAction, QtGui.QDialogButtonBox.ActionRole)


    def setOrientation(self, orientation):
        self.pageFormat.setOrientation(orientation)


    def setActions(self, actions):
        for action in actions:
            button = QtGui.QPushButton(action.getName(), self)
            button.setEnabled(action.isEnabled())
            self.buttonBox.addButton(button, QtGui.QDialogButtonBox.ActionRole)
            self.actionButtons.append(button)
            self.actions.append(action)


    def setRepeatButtonVisible(self, value=True):
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close|QtGui.QDialogButtonBox.Save|QtGui.QDialogButtonBox.Retry)


    def setText(self, reportResult):
        self.textReport = reportResult
        from library.PrintInfo import CInfo
        first = CInfo(u'test')
        mm = forceString(self.lineEditInterval.displayText())
        if mm.isdigit():
            if int(mm) > 12 and int(mm) <= 420:
                self.lineEditInterval.setStyleSheet("color: rgb(0, 128, 0);")
                # realheight = (int(mm) - 13.5) * 3.783
                realheight = float(int(mm) - 12) / 4.25
                height = realheight
                br = u'<br>'
                brCount = br * int(realheight)
                # first = first.__add__(u'<HTML><BODY><P><img src="white.png" width="1" height="' + forceString(height) + u'" alt="lorem"></P></BODY></HTML>')
                first = first.__add__(u'<HTML><BODY><P>' + brCount + u'</P></BODY></HTML>')
                second = CInfo(u'test')
                second = second.__add__(first)
            else:
                self.lineEditInterval.setStyleSheet("color: rgb(255, 0, 0);")
        else:
            interval = mm[:-1]
            self.lineEditInterval.setText(interval)
        if isinstance(reportResult, (list, tuple)):
            text = reportResult[0]
            actions = reportResult[1:]
        else:
            text = reportResult
            actions = []
        if actions:
            self.setActions(actions)
        if isinstance(text, QtGui.QTextDocument):
            interval = mm[:-1]
            self.lineEditInterval.setText(interval)
            self.checkBoxInterval.setChecked(False)
            self.checkBoxInterval.setEnabled(False)
            self.txtReport.setDocument(text.clone(self.txtReport))
#            text.setParent(self.txtReport)
        else:
            if mm.isdigit():
                if int(mm) > 12 and int(mm) <= 420:
                    self.textToPrinter = second.__add__(reportResult)
                else:
                    self.textToPrinter = reportResult
            self.txtReport.setHtml(text)


    def setCanvases(self, canvases):
        self.txtReport.setCanvases(canvases)


    def setSupplements(self, supplements):
        self.supplements = supplements
        self.updateValidationControls()


    def getSupplementFileName(self, mainFileName, supplementName):
        return ''.join((mainFileName,
                        '_supplement',
                        '' if supplementName.startswith('.') else '.',
                        supplementName
                        )
                       )


    def updateValidationControls(self):
        self.btnSchematronValidate.setVisible(False)
        self.btnSchematronValidate.setEnabled(False)

        if self.pyServices:
            for name, supplement in self.supplements.iteritems():
                if isinstance(supplement, unicode):
                    supplement = supplement.encode('utf-8')
                self.cdaCode = self.pyServices.getCdaCode(supplement)
                if self.cdaCode:
                    self.btnSchematronValidate.setVisible(True)
                    self.btnSchematronValidate.setEnabled(True)
                    self.buttonBox.addButton(self.btnSchematronValidate, QtGui.QDialogButtonBox.ActionRole)
                    return


    def setPageFormat(self, format):
        self.pageFormat = format


    def saveAsFile(self):
        defaultFileName = QtGui.qApp.getSaveDir()
        if self.fileName:
            defaultFileName = os.path.join(defaultFileName, self.fileName)

        saveFormats = [u'Веб-страница (*.html)',
                   u'Portable Document Format (*.pdf)',
                   u'PostScript (*.ps)',
                   u'Документ Microsoft Excel (*.xls)',
                  ]
        if odtAvailable():
            saveFormats.insert(-1, u'Текстовый документ OpenOffice.org (*.odt)')
        selectedFilter = QString('')

        fileName = QtGui.QFileDialog.getSaveFileName(
            self,
            u'Выберите имя файла',
            defaultFileName,
            ';;'.join(saveFormats),
            selectedFilter)
        if not fileName.isEmpty():
            exts = selectedFilter.section('(*.',1,1).section(')',0,0).split(';*.')
            ext = QFileInfo(fileName).suffix()
            if exts and not exts.contains(ext, Qt.CaseInsensitive):
                ext = exts[0]
                fileName.append('.'+ext)
            fileName = unicode(fileName)
            ext = unicode(ext)
            if ext.lower() == 'pdf':
                self.saveAsPdf(fileName)
            elif ext.lower() == 'ps':
                self.saveAsPS(fileName)
            elif ext.lower() == 'odt':
                self.saveAsOdt(fileName)
            elif ext.lower() == 'xls':
                self.saveAsXls(fileName)
            else:
                self.saveAsHtml(fileName)
            self.saveSupplements(os.path.splitext(fileName)[0])



    def saveAsHtml(self, fileName):
        QtGui.qApp.setSaveDir(fileName)
        baseDir, name = os.path.split(fileName)
        imageRelativePath = name.split('.', 1)[0]+'.files'
        imagesPath = os.path.join(baseDir, imageRelativePath)
        imagesDirCreated = False
        imageCounter = 0
        textDocument = self.txtReport.document()
        outTextDocument = textDocument.clone(textDocument)
        try:
            block = outTextDocument.begin()
            while block != outTextDocument.end():
                it = block.begin()
                while not it.atEnd():
                    fragment = it.fragment()
                    if fragment.isValid():
                        fm = fragment.charFormat().toImageFormat()
                        if fm.isValid() and not fm.name().isEmpty():
                            if not imagesDirCreated:
                                try:
                                    os.mkdir(imagesPath)
                                except:
                                    pass
                                imagesDirCreated = True
                            image = textDocument.resource(QtGui.QTextDocument.ImageResource, QUrl.fromEncoded(fm.name().toUtf8()))
                            imageFileName = imagesPath + '/'+str(imageCounter)+'.png'
                            writer = QtGui.QImageWriter(imageFileName, 'png')
                            writer.write(QtGui.QImage(image))
                            fm.setName('./'+imageRelativePath+'/'+str(imageCounter)+'.png')
                            cursor = QtGui.QTextCursor(outTextDocument)
                            cursor.setPosition(fragment.position())
                            cursor.setPosition(fragment.position() + fragment.length(), QtGui.QTextCursor.KeepAnchor)
                            cursor.setCharFormat(fm)
                            imageCounter+=1
                    it+=1
                block = block.next()
            txt = outTextDocument.toHtml('utf-8')
            file = codecs.open(unicode(fileName), encoding='utf-8', mode='w+')
            file.write(unicode(txt))
            file.close()
        finally:
            outTextDocument.deleteLater()



    def saveAsXls(self, fileName):
        self.saveAsHtml(fileName)


    def saveAsOdt(self, fileName):
        writer = QtGui.QTextDocumentWriter()
        try:
            QtGui.qApp.setSaveDir(fileName)
            writer.setFormat('odf')
            writer.setFileName(fileName)
            writer.write(self.txtReport.document())
        finally:
            writer = None
            pass


    def setupPage(self, printer):
            self.pageFormat.setupPrinter(printer)


    def saveAsPdf(self, fileName):
        QtGui.qApp.setSaveDir(fileName)
        printer = QtGui.QPrinter(QtGui.QPrinter.HighResolution)
        printer.setOutputFormat(QtGui.QPrinter.PdfFormat)

        tmpFile = QTemporaryFile()
        if tmpFile.open():
            try:
                printer.setOutputFileName(tmpFile.fileName())
                self.setupPage(printer)
                self.printReport(printer, 'doc')
                with open(unicode(tmpFile.fileName()),'rb') as source:
                    with open(fileName, 'wb') as destination:
                        fixPdf(source,
                               destination,
                               title=unicode(self.windowTitle()),
                               author=None,
                               subject=unicode(self.windowTitle()),
                               keywords=None,
                               creator='Qt4+PyPDF2',
                               producer='SAMSON')
            finally:
                tmpFile.close()


    def saveAsPS(self, fileName):
        QtGui.qApp.setSaveDir(fileName)
        printer = QtGui.QPrinter(QtGui.QPrinter.HighResolution)
        printer.setOutputFormat(QtGui.QPrinter.PostScriptFormat)
        printer.setOutputFileName(fileName)
        self.setupPage(printer)
        self.printReport(printer, self.windowTitle())


    def saveSupplements(self, mainFileName):
        for name, supplement in self.supplements.iteritems():
            fileName = self.getSupplementFileName(mainFileName, name)
            with codecs.open(fileName, 'w', 'utf-8') as f:
                f.write(supplement)


    def printReport(self, printer, docName):
        shortenedDocName = docName
        if len(docName) > 50: #tt3008 Будем обрезать слишком длинное название при печати
            name, ext = os.path.splitext(docName)
            name = name[:50 - len(ext)]
            shortenedDocName = name + ext
    
        mm = forceString(self.lineEditInterval.displayText())
        if self.checkBoxInterval.isChecked() and mm.isdigit() and int(mm) > 12 and int(mm) <= 420:
            if self.textToPrinter:
                self.txtReport.setHtml(self.textToPrinter)
        printTextDocument(self.txtReport.document(), shortenedDocName, self.pageFormat, printer)



    def handlePreview(self):
        previewDialog = QtGui.QPrintPreviewDialog()
        previewDialog.paintRequested.connect(self.txtReport.print_)
        printer = previewDialog.printer()
        if self.pageFormat:
            printer.setPageMargins(self.pageFormat.leftMargin, self.pageFormat.topMargin, self.pageFormat.rightMargin, self.pageFormat.bottomMargin, QtGui.QPrinter.Millimeter)
            printer.setOrientation(self.pageFormat.orientation)
            printer.setPageSize(self.pageFormat.pageSize)
        previewDialog.exec_()

    @pyqtSignature('')
    def on_btnRedo_clicked(self):
        from library.PrintTemplates import applyTemplate
        self.reject()
        parent = self.parentWidget()
        applyTemplate(parent, self.templateId, self.templateData, signAndAttachHandler = self.signAndAttachHandler)

    @pyqtSignature('')
    def on_btnPrint_clicked(self):
        if QtGui.qApp.enablePreview():
            self.handlePreview()
            return
        else:
            defaultPrinterInfo = QtGui.QPrinterInfo.defaultPrinter()
            if not defaultPrinterInfo.isNull():
                printer = QtGui.QPrinter(defaultPrinterInfo, QtGui.QPrinter.HighResolution)
            else:
                printer = QtGui.QPrinter(QtGui.QPrinter.HighResolution)
            printer.setPaperSize(printer.A4)
            printer.setFullPage(QtGui.qApp.printFullPage())
            self.setupPage(printer)
            printer.setPrintRange(printer.AllPages)
            if hasattr(printer, 'setNumCopies'):
                printer.setNumCopies(1)
            if hasattr(printer, 'setCopyCount'):
                printer.setCopyCount(1)

            if (   defaultPrinterInfo.isNull() 
                or not QtGui.qApp.enableFastPrint()
                or QtGui.qApp.keyboardModifiers() & Qt.ControlModifier
               ):
                if QtGui.qApp.showPageSetup():
                    dialog = QtGui.QPageSetupDialog(printer, self)
                    if dialog.exec_() != QtGui.QDialog.Accepted:
                        return
                dialog = QtGui.QPrintDialog(printer, self)
                dialog.setOption(dialog.PrintSelection, False)
                dialog.setOption(dialog.PrintPageRange, True)
                dialog.setOption(dialog.PrintShowPageSize, True)
                dialog.setOption(dialog.PrintCollateCopies, True)
                if hasattr(dialog, 'PrintCurrentPage'):
                    dialog.setOption(dialog.PrintCurrentPage, False)
                if dialog.exec_() != QtGui.QDialog.Accepted:
                    return
            self.printReport(printer, self.fileName)
            # if self.textReport:
            #     self.setText(self.textReport)


#    @pyqtSignature('')
#    def on_btnEMail_clicked(self):
#        pass

    @pyqtSignature('')
    def on_btnSaveAction_clicked(self):
        for key in self.propertiesData.keys():
            self.currentAction.action[key] = self.propertiesData[key]


    @pyqtSignature('')
    def on_btnSignAndAttach_clicked(self):
        self.isSignAndAttachResult = False
        if not QtGui.qApp.getAllowUnsignedAttachments() and not QtGui.qApp.isCspDefined():
            QtGui.QMessageBox.critical(
                self,
                u'Подписать и прикрепить',
                u'Запрещено прикреплять документ без подписи',
                QtGui.QMessageBox.Ok,
                QtGui.QMessageBox.Ok
            )
            return
        mainFileName = self.fileName
        ok, trail = self.signAndAttach()
        if ok:
            if trail[0]:
                resp_signature, org_signature = trail[1], trail[2]
                if QtGui.QMessageBox.question(
                        self,
                        u'Подпиcать и прикрепить',
                        u'Документ «%s» успешно сформирован, подписан и прикреплён.\nПоказать документ с оттисками ЭЦП?' % mainFileName,
                        QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                        QtGui.QMessageBox.Yes) == QtGui.QMessageBox.Yes:
                    html = self.templateContent
                    html = prepareSignedReport(html, [resp_signature], org_signature)
                    self.setText(html)
                    self.btnSignAndAttach.setEnabled(False)
            else:
                # QtGui.QMessageBox.
                # QtGui.QMessageBox.information(
                #     self,
                #     u'Подпиcать и прикрепить',
                #     u'Внимание!\nДокумент «%s» успешно сформирован, <font color="red" > прикреплён без подписи! </font>' % mainFileName,
                #     QtGui.QMessageBox.Ok,
                #     QtGui.QMessageBox.Ok,
                # )
                msg = QtGui.QMessageBox(QtGui.QMessageBox.Information, u'Подпиcать и прикрепить', u"Внимание!\nДокумент «%s» успешно сформирован, <strong><big><font color='#ff0000'; > прикреплён без подписи! </font></big></strong>" % mainFileName,
                                        QtGui.QMessageBox.Ok, self)
                msg.setTextFormat(Qt.RichText)
                msg.setDefaultButton(QtGui.QMessageBox.Ok)
                msg.exec_()
            self.isSignAndAttachResult = True
    
    
    def signAndAttach(self, templateId = None, snils=None, requireSignerPerson=0, silent=False):
        if self.currentAction:
            templateId = self.templateId
            db = QtGui.qApp.db
            actionRecord = self.currentAction.record
            personIdColName = 'person_id'
            requireSignerPerson = forceInt(db.translate('rbPrintTemplate', 'id', templateId, 'requireSignerPerson'))
            if requireSignerPerson == 1:
                personIdColName = 'setPerson_id'
            personId = forceInt(actionRecord.value(personIdColName))
            if personId:
                snils = forceString(db.translate('Person', 'id', personId, 'SNILS'))
            else:
                snils = 'empty'
        if not templateId and self.templateId:
            templateId = self.templateId
        
        if self.signerPerson:
            db = QtGui.qApp.db
            snils = forceString(db.translate('Person', 'id', self.signerPerson, 'SNILS'))

        printer = QtGui.QPrinter(QtGui.QPrinter.HighResolution)
        printer.setOutputFormat(printer.PdfFormat)

        pdfBytes = None
        tmpFile = QTemporaryFile()
        if tmpFile.open():
            try:
                printer.setOutputFileName(tmpFile.fileName())
                self.setupPage(printer)
                self.printReport(printer, 'doc')
                with open(unicode(tmpFile.fileName()),'rb') as source:
                    destination = StringIO()
                    fixPdf(source,
                           destination,
                           title=unicode(self.windowTitle()),
                           author=None,
                           subject=unicode(self.windowTitle()),
                           keywords=None,
                           creator='Qt4+PyPDF2',
                           producer='SAMSON')
                    pdfBytes = destination.getvalue()
                    destination.close()
            finally:
                tmpFile.close()

        pdfDoc = self.templateContent
        html = forceString(pdfDoc)
        mainFileName = self.fileName + '.pdf'
        items = [(mainFileName, pdfBytes, templateId, html)]
        for name, supplement in self.supplements.iteritems():
            supplementFileName = self.getSupplementFileName(self.fileName, name)
            if isinstance(supplement, unicode):
                supplement = supplement.encode('utf-8')
            items.append((supplementFileName, supplement, templateId))
        return QtGui.qApp.call(self, self.signAndAttachHandler, (items, snils, requireSignerPerson, silent))

    
    def getSignAndAttachResult(self):
        return self.isSignAndAttachResult
    

    @pyqtSignature('')
    def on_btnSchematronValidate_clicked(self):
        self.supplementsToValidate = []
        for name, supplement in self.supplements.iteritems():
            if isinstance(supplement, unicode):
                supplement = supplement.encode('utf-8')
            cdaCode = self.pyServices.getCdaCode(supplement)
            if cdaCode:
                listCdaCodes = self.pyServices.listCdaCodes()
                if cdaCode and listCdaCodes:
                    if cdaCode in listCdaCodes:
                        self.supplementsToValidate.append(name)
            else:
                QtGui.QMessageBox.critical(self, u'Ошибка', u"Не удалось определить идентификатор CDA-документа по справочнику 1.2.643.5.1.13.13.11.1522")
        if self.supplementsToValidate:
            for name in self.supplementsToValidate:
                supplement = self.supplements[name]
                try:
                    if isinstance(supplement, unicode):
                        supplement = supplement.encode('utf-8')
                    result = self.pyServices.validateCda(supplement)
                    if not result['schema_found']:
                        QtGui.QMessageBox.critical(self, u'Ошибка', u"Для вида документа '" + name + u"' отсутствует схематрон, документ не подлежит валидации!")
                    elif result['valid']:
                        QtGui.QMessageBox.information(self, u'Информация', u"Проверка документа '" + name + u"' выполнена, ошибок не обнаружено!")
                    else:
                        errors = u'\n'.join(result['errors'])
                        QtGui.QMessageBox.information(self, u'Информация', u"Проверка документа '" + name + u"' выполнена, обнаружены ошибки:\n" + errors)
                except Exception as e:
                    QtGui.QMessageBox.critical(self, u'Ошибка', u"Произошла ошибка при проверке документа '" + name + u"': " + unicode(e), QtGui.QMessageBox.Close)
        else:
            if listCdaCodes:
                QtGui.QMessageBox.critical(self, u'Ошибка', u"На сервере сервисов отсутствует схематрон, добавьте его или обратитесь к разработчику")
            else:
                QtGui.QMessageBox.critical(self, u'Ошибка', u"На данном рабочем месте нет доступа к серверу сервисов по адресу: {0}".format(self.pyServices.url))

    @pyqtSignature('')
    def on_btnEdit_clicked(self):
        editor = QtGui.qApp.documentEditor()
        if editor is not None:
            tmpDir = QtGui.qApp.getTmpDir('reportEdit')
            tmpFileName = os.path.join(tmpDir, 'report.html')
            self.saveAsHtml(tmpFileName)
            prg=QtGui.qApp.execProgram(editor, [tmpFileName], waitForFinished=False)
            if not prg[0]:
                QtGui.QMessageBox.critical(self,
                                       u'Внимание!',
                                       u'Не удалось запустить "%s"' % editor,
                                       QtGui.QMessageBox.Close)
            if prg[2]:
                QtGui.QMessageBox.critical(self,
                                       u'Внимание!',
                                       u'Ошибка при выполнении "%s"' % editor,
                                       QtGui.QMessageBox.Close)
            QtGui.qApp.removeTmpDir(tmpDir)
        else:
            QtGui.QMessageBox.critical(self,
                                    u'Ошибка!',
                                    u'Не указан исполняемый файл редактора документов\n'+
                                    u'Смотрите пункт меню "Настройки.Умолчания", закладка "Прочие настройки",\n'+
                                    u'строка "Внешний редактор документов".',
                                    QtGui.QMessageBox.Close)


    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Close:
            self.closeEvent(self)
            self.reject()
        elif buttonCode == QtGui.QDialogButtonBox.Retry:
            self.accept()
        elif buttonCode == QtGui.QDialogButtonBox.Save:
            QtGui.qApp.call(self, self.saveAsFile)
            # if self.textReport:
            #     self.setText(self.textReport)
        else:
            if button in self.actionButtons:
                i = self.actionButtons.index(button)
                self.actions[i].exec_(self)


def printTextDocument(document, documentName, pageFormat, printer):

    def uncolorDocument(document):
        cursor = QtGui.QTextCursor(document)
        cursor.beginEditBlock()
        cursor.select(QtGui.QTextCursor.Document)
        
        charFmt = QtGui.QTextCharFormat()
        charFmt.setForeground(QtGui.QBrush(QtGui.QColor(0, 0, 0)))
        if charFmt.hasProperty(QtGui.QTextFormat.BackgroundBrush):
            charFmt.clearProperty(QtGui.QTextFormat.BackgroundBrush)
        
        cursor.mergeCharFormat(charFmt)
        cursor.clearSelection()
        block = document.begin()
        while block.isValid():
            fmt = block.blockFormat()
            if fmt.hasProperty(QtGui.QTextFormat.BackgroundBrush):
                fmt.clearProperty(QtGui.QTextFormat.BackgroundBrush)
                
                cursor.setPosition(block.position())
                cursor.setBlockFormat(fmt)
                
            block = block.next()

        cursor.endEditBlock()

    printer.setCreator('SAMSON')
    printer.setDocName(documentName)
    outDocument = document.clone(document)
    if forceBool(QtGui.qApp.preferences.appPrefs.get('printBlackWhite', True)):
        uncolorDocument(outDocument)
    if pageFormat:
        pageFormat.updateFromPrinter(printer)
        pd = document.documentLayout().paintDevice()
        if pd is None:
            pd = QtGui.qApp.desktop()
            document.documentLayout().setPaintDevice(pd)
        pd_logicalDpiX = pd.logicalDpiX()
        pd_logicalDpiY = pd.logicalDpiY()
        p_logicalDpiX = printer.logicalDpiX()
        p_logicalDpiY = printer.logicalDpiY()

        pageRect = printer.pageRect() # in pixels
        paperRect = printer.paperRect() # in pixels

        # hardware defined margins, in printer pixels
        hl = (pageRect.left()   - paperRect.left())
        ht = (pageRect.top()    - paperRect.top())
        hr = (paperRect.right() - pageRect.right())
        hb = (paperRect.bottom() -pageRect.bottom())

        # software defined margins, in printer pixels
        sl = pageFormat.leftMargin * p_logicalDpiX / 25.4 # 25.4 mm = 1 inch
        st = pageFormat.topMargin * p_logicalDpiY / 25.4
        sr = pageFormat.rightMargin * p_logicalDpiX / 25.4
        sb = pageFormat.bottomMargin * p_logicalDpiY / 25.4

        # margins
        ml = max(0, sl-hl)
        mt = max(0, st-ht)
        mr = max(0, sr-hr)
        mb = max(0, sb-hb)

        fmt = outDocument.rootFrame().frameFormat()
        fmt.setLeftMargin(ml / p_logicalDpiX * pd_logicalDpiX) #Sets the frame's left margin in in some parrots (screen pixels?)
        fmt.setTopMargin(mt/ p_logicalDpiY * pd_logicalDpiY)
        fmt.setRightMargin(mr / p_logicalDpiX * pd_logicalDpiX)
        fmt.setBottomMargin(mb / p_logicalDpiY * pd_logicalDpiY)
        outDocument.rootFrame().setFrameFormat(fmt)
        # Calculate page width and height, in screen pixels
        pw = float(pageRect.width()) / p_logicalDpiX * pd_logicalDpiX
        ph = float(pageRect.height()) / p_logicalDpiY * pd_logicalDpiY
        # setup page size
        outDocument.setPageSize(QSizeF(pw, ph))
    outDocument.print_(printer)
    outDocument.deleteLater()
