# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2017 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

import codecs
import os.path
import re

from PyQt4 import QtGui
from PyQt4.QtCore import (
                            Qt,
                            pyqtSignature,
                            QFileInfo,
                            QSizeF,
                            QString,
                            QTemporaryFile,
                            QByteArray,
                            QUrl,
                            QObject,
                            pyqtSlot,
                            SIGNAL,
                            SLOT
                         )
from PyQt4.QtGui import QTextDocument

from library.Utils import forceBool, forceString
from suds.client import Client, WebFault

from Users.Rights import urAdmin, urEditReportForm
from PyQt4.QtWebKit import *
from Reports.Ui_ReportWEBView import Ui_ReportViewDialog


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


    def __init__(self, pageSize=QtGui.QPrinter.A4,
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
            if self.pageSize == QtGui.QPrinter.Custom:
                printer.setPaperSize(self.pageRect, QtGui.QPrinter.Millimeter)
            elif self.pageSize in [QtGui.QPrinter.A4]: #  printerInfo.supportedPaperSizes():
                printer.setPaperSize(self.pageSize)
            else:
                paperRect = self.getPaperRect(self.pageSize)
                printer.setPaperSize(paperRect, QtGui.QPrinter.Millimeter)
            printer.setOrientation(self.orientation)


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


class CReportWEBViewDialog(QtGui.QDialog, Ui_ReportViewDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)


        self.btnPrint = QtGui.QPushButton(u'Печатать', self)
        self.btnPrint.setObjectName('btnPrint')
        self.btnPrint.setDefault(True)

    #    self.lineEdit = QtGui.QLineEdit(self)

        # self.btnEMail = QtGui.QPushButton(u'Отправить', self)
        # self.btnEMail.setObjectName('btnEMail')
        # self.btnEMail.setEnabled(False)

        self.btnSignAndAttach = QtGui.QPushButton(u'Прикрепить и подписать', self)
        self.btnSignAndAttach.setObjectName('btnSignAndAttach')
        self.btnSignAndAttach.setEnabled(False)

        self.btnEdit = QtGui.QPushButton(u'Редактировать', self)
        self.btnEdit.setObjectName('btnEdit')
        self.btnEdit.setEnabled((QtGui.qApp.userHasRight(urEditReportForm) or QtGui.qApp.userHasRight(urAdmin)) and bool(QtGui.qApp.documentEditor()))
        # self.txtReport = QWebView(self)

        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnBack, QtGui.QDialogButtonBox.ActionRole)
        # self.buttonBox.addButton(self.btnEMail, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnSignAndAttach, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnEdit, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close|QtGui.QDialogButtonBox.Save)
        self.txtReport.setContextMenuPolicy(0)
        self.fileName = ''
        self.pageFormat = None
        self.pageFormat1 = 1
        self.orientation = QtGui.QPrinter.Portrait
        self.actionButtons = []
        self.actions = []
        self.textToPrinter = None
        self.textReport = None
        self.lineEdit.setVisible(False)
        self.txtReport.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        handler = self.handler
        QObject.connect(self.txtReport, SIGNAL("linkClicked(const QUrl&)"), handler)
        if not QtGui.QPrinterInfo.availablePrinters():
           self.btnPrint.setEnabled(False)
        self.btnPrint.setFocus(Qt.OtherFocusReason)

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
                    elif u'event' in url.toString():
                       from Events.EventEditDialog import CEventEditDialog
                       self.eve = CEventEditDialog(self)
                       karta = url.toString().split('_')
                 #      self.eve.openEvent(int(karta[1]))
                       from Registry.RegistryWindow import CRegistryWindow
                       self.registry = CRegistryWindow(self)
                       karta = url.toString().split('_')
                       self.registry.on_btnEventEditTemplate_clicked(karta[1])
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
                    else:
                        QtGui.QMessageBox.critical(self.txtReport,
                                                   u'Ошибка',
                                                   u'Произошла ошибка при попытке распознать идентификатор шаблона',
                                                   QtGui.QMessageBox.Close)
                        self.lineEdit.setVisible(True)
                        self.lineEdit.setText(u'')
                        self.txtReport.setHtml(self.content)
                else:
                    self.lineEdit.setVisible(False)
                    self.ind(id_, self.lineEdit.text()) # переход к след шаблону по id типа <li><a href="194">Суперпродукты</a></li>
            else:
                self.lineEdit.setVisible(False)
                self.lineEdit.setText('')
                self.txtReport.setHtml(self.content)
        else:
            self.txtReport.load(url)

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

        QtGui.qApp.cacheTemplate = ['css', templateResult.content, data]
        self.txtReport.setHtml(templateResult.content)


    def setHtml(self, content, data):
        # self.txtReport = QWebView(self)
        self.content = content
        self.data = data
        self.txtReport.setHtml(content)

    def setWindowTitle(self, title):
        QtGui.QDialog.setWindowTitle(self, title)
        for x in ':?|()[]\"\';!*/\\':
            title = title.replace(x, '')
        self.fileName = title


    def setSignAndAttachHandler(self, signAndAttachHandler):
        self.signAndAttachHandler = signAndAttachHandler
        self.btnSignAndAttach.setEnabled(bool(self.signAndAttachHandler))


    def setOrientation(self, orientation):
        self.orientation = orientation


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


    def setPageFormat(self, format):
        self.pageFormat = format


    def saveAsFile(self):
        defaultFileName = QtGui.qApp.getSaveDir()
        if self.fileName:
            defaultFileName = os.path.join(defaultFileName, self.fileName)

        saveFormats = [u'Веб-страница (*.html)',
                   u'Portable Document Format (*.pdf)',
                   u'PostScript (*.ps)',
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
                self.saveAsPdfOrPS(fileName, QtGui.QPrinter.PdfFormat)
            elif ext.lower() == 'ps':
                self.saveAsPdfOrPS(fileName, QtGui.QPrinter.PostScriptFormat)
            elif ext.lower() == 'odt':
                self.saveAsOdt(fileName)
            else:
                self.saveAsHtml(fileName)


    def saveAsHtml(self, fileName):
        QtGui.qApp.setSaveDir(fileName)
        baseDir, name = os.path.split(fileName)
        imageRelativePath = name.split('.', 1)[0]+'.files'
        imagesPath = os.path.join(baseDir, imageRelativePath)
        imagesDirCreated = False
        imageCounter = 0
        textDocument = self.txtReport.page().currentFrame()
        outTextDocument = textDocument
        try:

            txt = outTextDocument.toHtml()
            file = codecs.open(unicode(fileName), encoding='utf-8', mode='w+')
            file.write(unicode(txt))
            file.close()
        finally:
            outTextDocument.deleteLater()


    def saveAsOdt(self, fileName):
        writer = QtGui.QTextDocumentWriter()
        try:
            QtGui.qApp.setSaveDir(fileName)
            writer.setFormat('odf')
            writer.setFileName(fileName)
            doc = QTextDocument()
            doc.setHtml(self.txtReport.page().currentFrame().toHtml())
            # f = self.txtReport.page().currentFrame().documentElement()
            result = writer.write(doc)
        finally:
            writer = None
            pass


    def setupPage(self, printer):
        printer.setOrientation(self.orientation)
        if self.pageFormat:
            self.pageFormat.setupPrinter(printer)


    def saveAsPdfOrPS(self, fileName, format):
        QtGui.qApp.setSaveDir(fileName)
        printer = QtGui.QPrinter(QtGui.QPrinter.HighResolution)
        printer.setOutputFormat(format)
        printer.setOutputFileName(fileName)
        self.setupPage(printer)
        self.printReport(printer)


    def printReport(self, printer):
      #  mm = forceString(self.lineEditInterval.displayText())
      #  if self.checkBoxInterval.isChecked() and mm.isdigit() and int(mm) > 12 and int(mm) <= 420:
      #      if self.textToPrinter:
      #          self.txtReport.setHtml(self.textToPrinter)
        printTextDocument(self.txtReport.print_(printer), self.fileName, self.pageFormat, printer)


    @pyqtSignature('')
    def on_btnPrint_clicked(self):
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
        if (defaultPrinterInfo.isNull() or (QtGui.qApp.keyboardModifiers() & Qt.ControlModifier)) or not QtGui.qApp.enableFastPrint():
            dialog = QtGui.QPrintDialog(printer, self)
            if dialog.exec_() != QtGui.QDialog.Accepted:
                return
        self.printReport(printer)
        if self.textReport:
            self.setText(self.textReport)


    # @pyqtSignature('')
    # def on_btnEMail_clicked(self):
    #     pass


    @pyqtSignature('')
    def on_btnSignAndAttach_clicked(self):
        printer = QtGui.QPrinter(QtGui.QPrinter.HighResolution)
        printer.setOutputFormat(printer.PdfFormat)

        pdfBytes = None
        tmpFile = QTemporaryFile()
        if tmpFile.open():
            printer.setOutputFileName(tmpFile.fileName())
            self.setupPage(printer)
            self.printReport(printer)
            pdfBytes = tmpFile.readAll().data()
        tmpFile.close()
        ok, trail = QtGui.qApp.call(self, self.signAndAttachHandler, (self.fileName + '.pdf', pdfBytes))
        if ok:
            if trail:
                QtGui.QMessageBox.information(self,
                                              u'Прикрепить и подписать',
                                              u'Документ «%s» успешно сформирован, прикреплён и подписан' % self.fileName,
                                              QtGui.QMessageBox.Ok,
                                              QtGui.QMessageBox.Ok
                                              )
            else:
                QtGui.QMessageBox.information(self,
                                              u'Прикрепить и подписать',
                                              u'Внимание!\nДокумент «%s» успешно сформирован, прикреплён без подписи!' % self.fileName,
                                              QtGui.QMessageBox.Ok,
                                              QtGui.QMessageBox.Ok
                                              )


    @pyqtSignature('')
    def on_btnEdit_clicked(self):
        editor = QtGui.qApp.documentEditor()
        if editor is not None:
            tmpDir = QtGui.qApp.getTmpDir('reportEdit')
            tmpFileName = os.path.join(tmpDir, 'report.html')
            self.saveAsHtml(tmpFileName)
            cmdLine = u'"%s" "%s"'% (editor, tmpFileName)
            prg=QtGui.qApp.execProgram(cmdLine)
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
            self.reject()
        elif buttonCode == 0: # кнопка назад
            self.txtReport.setHtml(self.content)
        elif buttonCode == QtGui.QDialogButtonBox.Retry:
            self.accept()
        elif buttonCode == QtGui.QDialogButtonBox.Save:
            QtGui.qApp.call(self, self.saveAsFile)
            if self.textReport:
                self.setText(self.textReport)
        else:
            if button in self.actionButtons:
                i = self.actionButtons.index(button)
                self.actions[i].exec_(self)


def printTextDocument(document, documentName, pageFormat, printer):
    def uncolorCharFormat(charFormat):
        foreground = charFormat.foreground()
        background = charFormat.background()
        foreground.setColor(QtGui.QColor(0, 0, 0))
        background.setColor(QtGui.QColor(255, 255, 255))
        charFormat.setForeground(foreground)
        charFormat.setBackground(background)

    def uncolorDocument(document):
        cursor = QtGui.QTextCursor(document)
        while not cursor.atEnd(): # заменяем все заливки на белые, а все тексты - на чёрные
            charFormat = cursor.blockCharFormat()
            uncolorCharFormat(charFormat)
            cursor.setBlockCharFormat(charFormat)
            while not cursor.atBlockEnd(): # заменяем все заливки на белые, а все тексты - на чёрные
                cursor.movePosition(QtGui.QTextCursor.NextCharacter, QtGui.QTextCursor.KeepAnchor)
                charFormat = cursor.charFormat()
                uncolorCharFormat(charFormat)
                cursor.setCharFormat(charFormat)
                cursor.clearSelection()
            cursor.movePosition(QtGui.QTextCursor.NextBlock)

    printer.setCreator(u'САМСОН')
    printer.setDocName(documentName)
    outDocument = document
 #   if forceBool(QtGui.qApp.preferences.appPrefs.get('printBlackWhite', True)):
 #       uncolorDocument(outDocument)
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
#    outDocument.print_(printer)
