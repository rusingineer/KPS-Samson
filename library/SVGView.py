# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2024 SAMSON Group. All rights reserved.
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

from PyQt4.QtCore import Qt, pyqtSignature, QByteArray, QFileInfo, QRectF, QSizeF, QString,  QVariant, QChar, QTemporaryFile
from cStringIO import StringIO

from PyQt4 import QtGui
from PyQt4 import QtSvg
from PyQt4 import QtXml

from library.Utils import forceInt, forceString
from library.PDF.fixPdf import fixPdf

from Ui_SVGView import Ui_SVGViewDialog


def showSVG(widget, templateResult, pageFormat, signAndAttachHandler=None, printBlank=None, btnRedoInfo=None):
    view = CSVGView(pageFormat, widget)
    view.setDocName(unicode(templateResult.documentName))
    view.setContent(templateResult.content, templateResult.canvases, printBlank)
    view.setSignAndAttachHandler(signAndAttachHandler)
    view.setRedoInfo(btnRedoInfo)
    view.setSupplements(templateResult.supplements)
    view.currentAction = templateResult.currentAction
    view.templateContent = templateResult.content
    view.exec_()


def printSVG(name, content, printer):
    doc = CSVGDocument(content)
    doc.print_(name, printer)


class CSVGDocument(QtXml.QDomDocument):
    def __init__(self, content=None):
        QtXml.QDomDocument.__init__(self)
        self.image = None
        self.printBlank = None
        if content:
            self.setContent(content)


    def setContent(self, content):
        self.srcContent = content
        ok, errorMsg, errorLine, errorColumn = QtXml.QDomDocument.setContent(self, QByteArray(content.encode('utf-8')), False)
        if not ok:
            raise Exception(u'%s at (%d, %d)' % (errorMsg, errorLine, errorColumn))


    def isValid(self):
        svgElement = self.firstChildElement('svg')
        return svgElement is not None and not svgElement.isNull()


    def findPages(self):
        pageIdList = []
        svgElement = self.firstChildElement('svg')
        if svgElement:
            pageElement = svgElement.firstChildElement('g')
            while pageElement and not pageElement.isNull():
                pageId = unicode(pageElement.attribute('id'))
                if pageId.startswith('page'):
                    pageIdList.append(pageId)
#                    pageElement.setAttribute('visibility', 'hidden')
                pageElement = pageElement.nextSiblingElement('g')
        return pageIdList


    def getPageRectSizeF(self):
        def parseLength(txt):
            s = re.search(r'^\s*((?:\d+\.?\d*)|(?:\d*\.\d+))\s*([^ ]*)\s*$',txt)
            if s:
                qnt, unit = s.groups()
                result = float(qnt) if qnt and qnt != '.' else 0
                if unit == 'mm':
                    return result
                elif unit == 'sm':
                    return result*10
                elif unit == 'in':
                    return result*25.4
                else:
                    return result*25.4/72
            else:
                return None

        svgElement = self.firstChildElement('svg')
        if svgElement:
            width = parseLength(unicode(svgElement.attribute('width')))
            height = parseLength(unicode(svgElement.attribute('height')))
        else:
            width = height = None
        if width and height:
            return QSizeF(width, height)
        else:
            return None


    def hideAllPagesExceptOne(self, visiblePageId):
        svgElement = self.firstChildElement('svg')
        if svgElement:
            pageElement = svgElement.firstChildElement('g')
            while pageElement and not pageElement.isNull():
                pageId = unicode(pageElement.attribute('id'))
                if pageId.startswith('page'):
                    if pageId == visiblePageId:
                        pageElement.setAttribute('visibility', 'visible')
                    else:
                        pageElement.setAttribute('visibility', 'hidden')
                pageElement = pageElement.nextSiblingElement('g')


    def print_(self, docName, printer, svgItem = None):
        size = self.getPageRectSizeF()
        if size:
            w = size.width()
            h = size.height()
            if w < h:
                printer.setOrientation(QtGui.QPrinter.Portrait)
            else:
                size.transpose()
                printer.setOrientation(QtGui.QPrinter.Landscape)
            printer.setPaperSize(size, 0)

        printer.setFullPage(True)
        printer.setPageMargins(0,0,0,0,0)
        printer.setCreator('samson')
        printer.setDocName(docName)
        printer.setFontEmbeddingEnabled(True)
        painter = QtGui.QPainter()

        renderer = QtSvg.QSvgRenderer()
        painter.begin(printer)
        if self.image and not self.printBlank:
            painter.drawImage(QRectF(0, 0, printer.width(), printer.height()), self.image)
#        if printer.orientation() == QtGui.QPrinter.Landscape:
#            painterRect = painter.viewport()
#            painter.translate(0, painterRect.height())
#            painter.rotate(270)

        pageIdList = self.findPages()
        if pageIdList:
            fromPage = printer.fromPage()
            toPage   = printer.fromPage()
            if fromPage and toPage:
                pageIdList = pageIdList[fromPage-1:toPage]
            if printer.pageOrder == QtGui.QPrinter.LastPageFirst:
                pageIdList.reverse()
            firstPage = True
            for pageId in pageIdList:
                self.hideAllPagesExceptOne(pageId)
                renderer.load(self.toByteArray(0))
                if not firstPage:
                    printer.newPage()
                renderer.render(painter)
                firstPage = False
        else:
            if svgItem:
                dx = svgItem.x()
                dy = svgItem.y()
                rect = svgItem.boundingRect()
                painter.setWindow(rect.x()-dx, rect.y()-dy, rect.width()-dx, rect.height()-dy)
                svgItem.paint(painter, QtGui.QStyleOptionGraphicsItem())
            else:
                renderer.load(self.toByteArray())
                renderer.render(painter)
#        del renderer
        painter.end()


class CSVGView(QtGui.QDialog, Ui_SVGViewDialog):
    def __init__(self, pageFormat, parent=None):
        QtGui.QDialog.__init__(self, parent)

        self.btnRedo = QtGui.QPushButton(u'Повторить', self)
        self.btnRedo.setObjectName('btnRedo')
        self.btnRedo.setDefault(True)
        self.btnRedo.setVisible(False)

        self.btnPrint = QtGui.QPushButton(u'Печатать', self)
        self.btnPrint.setObjectName('btnPrint')
        self.btnPrint.setDefault(True)
        
        self.signAndAttachHandler = None
        self.supplements = {}
        self.btnSignAndAttach = QtGui.QPushButton(u'Подписать и прикрепить', self)
        self.btnSignAndAttach.setObjectName('btnSignAndAttach')
        self.btnSignAndAttach.setEnabled(False)

#        self.btnEMail = QtGui.QPushButton(u'Отправить', self)
#        self.btnEMail.setObjectName('btnEMail')
#        self.btnEMail.setEnabled(False)

        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)

        self.graphicsView.setScene(QtGui.QGraphicsScene(self.graphicsView))
        #style = self.style()
        #self.btnFirstPage.setIcon(style.standardIcon(QtGui.QStyle.SP_MediaSkipBackward))
        #self.btnLastPage.setIcon(style.standardIcon(QtGui.QStyle.SP_MediaSkipForward))
        self.doc = CSVGDocument()
        self.pageFormat = pageFormat
        self.pageIdList = []
        self.currentAction = None
        self.templateContent = None
        self.templateId = None
        self.templateData = None
        self.initItems()
        self.setupPagesControl()
        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnSignAndAttach, QtGui.QDialogButtonBox.ActionRole)
#        self.buttonBox.addButton(self.btnEMail, QtGui.QDialogButtonBox.ActionRole)
#        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close|QtGui.QDialogButtonBox.Save)
        self.setDocName('SVG View')
#        if not QtGui.QPrinterInfo.availablePrinters():
#            self.btnPrint.setEnabled(False)


    def initItems(self):
        darkGray = QtGui.QColor(64,64,64)
        boundingRect = QRectF(0,0,10,10)
        self.graphicsView.setBackgroundBrush(QtGui.QBrush(Qt.darkGray))
        scene = self.graphicsView.scene()
        #print type(scene)
        #print dir(scene)
        scene.clearSelection() #scene.clear()!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        self.svgItem = QtSvg.QGraphicsSvgItem()
        self.svgItem.setFlags(QtGui.QGraphicsItem.ItemClipsToShape)
#        self.svgItem.setCacheMode(QtGui.QGraphicsItem.NoCache)
        self.svgItem.setZValue(0)

        self.shadowItem = QtGui.QGraphicsRectItem(boundingRect.adjusted(-1, -1, 2, 2))
        self.shadowItem.setBrush(QtGui.QBrush(darkGray))
        self.shadowItem.setPen(QtGui.QPen(darkGray))
        self.shadowItem.setZValue(-2)
        self.shadowItem.setPos(4, 4)

        self.frameItem = QtGui.QGraphicsRectItem(boundingRect.adjusted(-1, -1, 2, 2))
        self.frameItem.setBrush(QtGui.QBrush(Qt.white))
        self.frameItem.setPen(QtGui.QPen(darkGray))
        self.frameItem.setZValue(-1)
        self.frameItem.setPos(-1, -1)

        scene.addItem(self.shadowItem)
        scene.addItem(self.frameItem)
        scene.addItem(self.svgItem)
        scene.setSceneRect(boundingRect.adjusted(-3, -3, 10, 10))


    def setDocName(self, name):
        self.docName = name
        self.setWindowTitle(name)
        fileName = name
        for x in ':?|()[]\"\';!*/\\':
            fileName = fileName.replace(x, '')
        self.fileName = fileName

    
    def setSignAndAttachHandler(self, signAndAttachHandler):
        self.signAndAttachHandler = signAndAttachHandler
        self.btnSignAndAttach.setEnabled(bool(self.signAndAttachHandler))


    def setRedoInfo(self, redoInfo):
        if redoInfo:
            self.btnRedo.setEnabled(True)
            if self.btnRedo.isEnabled():
                self.buttonBox.addButton(self.btnRedo, QtGui.QDialogButtonBox.ActionRole)
            self.templateId = redoInfo[0]
            self.templateData = redoInfo[1]
            self.signAndAttachHandler = redoInfo[2]


    def setSupplements(self, supplements):
        self.supplements = supplements
        if self.supplements is None:
            self.supplements = {}
            

    def setContent(self, content, canvases, printBlank = None):
        try:
            self.doc.setContent(content)
        except:
            pass

        if self.doc.isValid():
            self.pageIdList = self.doc.findPages()
            self.svgItem.renderer().load(QByteArray(content.encode('utf-8')))
            self.svgItem.setElementId('') # for recalc item.boundRect()
            if hasattr(self.svgItem, 'setX'):
                self.svgItem.setX(forceInt(QtGui.qApp.preferences.appPrefs.get(self.docName+'_svgX', QVariant())))
                self.svgItem.setY(forceInt(QtGui.qApp.preferences.appPrefs.get(self.docName+'_svgY', QVariant())))
            else:
                self.svgItem.setPos(forceInt(QtGui.qApp.preferences.appPrefs.get(self.docName+'_svgX', QVariant())), forceInt(QtGui.qApp.preferences.appPrefs.get(self.docName+'_svgY', QVariant())))
            self.label.setText(u'Сдвиг x: %i, y %i'%(self.svgItem.x(), self.svgItem.y()))
            boundingRect = self.svgItem.boundingRect()
            self.shadowItem.setRect(boundingRect.adjusted(-1, -1, 2, 2))
            self.frameItem.setRect(boundingRect.adjusted(-1, -1, 2, 2))
            self.graphicsView.scene().setSceneRect(boundingRect.adjusted(-3, -3, 10, 10))
            if canvases:
                self.doc.image = canvases[canvases.keys()[0]].image.scaled(boundingRect.width(), boundingRect.height())
                self.frameItem.setBrush(QtGui.QBrush(self.doc.image))
            self.setupPagesControl()
            if printBlank:
                self.doc.printBlank = printBlank


    def setupPagesControl(self):
        self.gotoPage(0)
        self.edtPageNum.setRange(1, len(self.pageIdList))
        self.grpPager.setVisible(len(self.pageIdList)>1)
        self.grpPager.setEnabled(len(self.pageIdList)>1)


    def gotoPage(self, n):
        self.btnFirstPage.setEnabled(n>0)
#        self.btnPrevPage.setEnabled(n>0)
#        self.btnNextPage.setEnabled(n+1<len(self.pageIdList))
        self.btnLastPage.setEnabled(n+1<len(self.pageIdList))
        self.edtPageNum.setValue(n+1)
        if 0<=n<len(self.pageIdList):
            self.doc.hideAllPagesExceptOne(self.pageIdList[n])
            self.svgItem.renderer().load(self.doc.toByteArray(0))
            self.svgItem.setElementId('')


    def saveAsFile(self):
        defaultFileName = QtGui.qApp.getSaveDir()
        if self.fileName:
            defaultFileName = os.path.join(defaultFileName, self.fileName)

        saveFormats = [u'изображение SVG (*.svg)',
                       u'Portable Document Format (*.pdf)',
                       u'PostScript (*.ps)',
                      ]
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
            else:
                self.saveAsSvg(fileName)


    def saveAsPdfOrPS(self, fileName, format):
        QtGui.qApp.setSaveDir(fileName)
        printer = QtGui.QPrinter(QtGui.QPrinter.HighResolution)
        printer.setOutputFormat(format)
        printer.setOutputFileName(fileName)
        printer.setFontEmbeddingEnabled(True)
        self.pageFormat.setupPrinter(printer)
        self.doc.print_(self.docName, printer)


    def saveAsSvg(self, fileName):
        QtGui.qApp.setSaveDir(fileName)
        file = codecs.open(unicode(fileName), encoding='utf-8', mode='w+')
        file.write(self.doc.srcContent)
        file.close()


    @pyqtSignature('')
    def on_btnFirstPage_clicked(self):
        self.edtPageNum.setValue(self.edtPageNum.minimum())


#    @pyqtSignature('')
#    def on_btnPrevPage_clicked(self):
#        self.edtPageNum.setValue(self.edtPageNum.value()-1)


#    @pyqtSignature('')
#    def on_btnNextPage_clicked(self):
#        self.edtPageNum.setValue(self.edtPageNum.value()+1)


    @pyqtSignature('')
    def on_btnLastPage_clicked(self):
        self.edtPageNum.setValue(self.edtPageNum.maximum())


    @pyqtSignature('int')
    def on_edtPageNum_valueChanged(self, val):
        self.gotoPage(val-1)


    @pyqtSignature('')
    def on_btnRedo_clicked(self):
        from library.PrintTemplates import applyTemplate
        self.reject()
        parent = self.parentWidget()
        applyTemplate(parent, self.templateId, self.templateData, signAndAttachHandler=self.signAndAttachHandler)


    @pyqtSignature('')
    def on_btnPrint_clicked(self):
        defaultPrinterInfo = QtGui.QPrinterInfo.defaultPrinter()
        if not defaultPrinterInfo.isNull():
            printer = QtGui.QPrinter(defaultPrinterInfo, QtGui.QPrinter.HighResolution)
        else:
            printer = QtGui.QPrinter(QtGui.QPrinter.HighResolution)
        printer.setPrintRange(printer.AllPages)
        printer.setOrientation(printer.Portrait)
        printer.setPaperSize(printer.A4)
        printer.setFullPage(False)
        if hasattr(printer, 'setNumCopies'):
            printer.setNumCopies(1)
        if hasattr(printer, 'setCopyCount'):
            printer.setCopyCount(1)

        self.pageFormat.setupPrinter(printer)
        if (defaultPrinterInfo.isNull() or (QtGui.qApp.keyboardModifiers() & Qt.ControlModifier)) or not QtGui.qApp.enableFastPrint():
            dialog = QtGui.QPrintDialog(printer, self)
            dialog.setMinMax(1, max(1, len(self.pageIdList)))
            if dialog.exec_() != QtGui.QDialog.Accepted:
                return
        self.doc.print_(self.docName, printer, self.svgItem)


    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Close:
            self.reject()
        elif buttonCode == QtGui.QDialogButtonBox.Retry:
            self.accept()
        elif buttonCode == QtGui.QDialogButtonBox.Save:
            QtGui.qApp.call(self, self.saveAsFile)
        else:
            pass
    
    
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
        mainFileName = unicode(self.windowTitle())
        ok, trail = self.signAndAttach()
        if ok:
            if trail:
                QtGui.QMessageBox.information(
                    self,
                    u'Подпиcать и прикрепить',
                    u'Документ «%s» успешно сформирован, подписан и прикреплён' % mainFileName,
                    QtGui.QMessageBox.Ok,
                    QtGui.QMessageBox.Ok,
                )
            else:
                QtGui.QMessageBox.information(
                    self,
                    u'Подпиcать и прикрепить',
                    u'Внимание!\nДокумент «%s» успешно сформирован, прикреплён без подписи!' % mainFileName,
                    QtGui.QMessageBox.Ok,
                    QtGui.QMessageBox.Ok,
                )
            self.isSignAndAttachResult = True


    def signAndAttach(self, templateId=None, snils=None, requireSignerPerson=0):
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

        tmpFile = QTemporaryFile()
        if not tmpFile.open():
            raise Exception('QTemporaryFile.open() failed')
        pdfBytes = None
        try:
            self.saveAsPdfOrPS(tmpFile.fileName(), QtGui.QPrinter.PdfFormat)
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
        if pdfBytes is None:
            raise Exception('no bytes to sign')

        pdfDoc = self.templateContent
        html = forceString(pdfDoc)
        mainFileName = unicode(self.windowTitle()) + '.pdf'
        items = [(mainFileName, pdfBytes, templateId, html)]
        for name, supplement in self.supplements.iteritems():
            supplementFileName = self.getSupplementFileName(self.fileName, name)
            if isinstance(supplement, unicode):
                supplement = supplement.encode('utf-8')
            items.append((supplementFileName, supplement, templateId))
        return QtGui.qApp.call(self, self.signAndAttachHandler, (items, snils, requireSignerPerson))


    def getSupplementFileName(self, mainFileName, supplementName):
        return ''.join((
            mainFileName,
            '_supplement',
            '' if supplementName.startswith('.') else '.',
            supplementName
        ))
        

    def getSignAndAttachResult(self):
        return self.isSignAndAttachResult


    def keyPressEvent(self, event):
        key = event.text().at(0)
        if key == QChar(0x77) or key == QChar(0x446): # w|ц
            if hasattr(self.svgItem, 'setY'):
                self.svgItem.setY(self.svgItem.y() - 1)
            else:
                self.svgItem.setPos(self.svgItem.x(), self.svgItem.y() - 1)
            QtGui.qApp.preferences.appPrefs[self.docName+'_svgY'] = QVariant(self.svgItem.y())
            self.label.setText(u'Сдвиг x: %i, y %i'%(self.svgItem.x(), self.svgItem.y()))
        elif key == QChar(0x73) or key == QChar(0x44b): # s|ы
            if hasattr(self.svgItem, 'setY'):
                self.svgItem.setY(self.svgItem.y() + 1)
            else:
                self.svgItem.setPos(self.svgItem.x(), self.svgItem.y() + 1)
            QtGui.qApp.preferences.appPrefs[self.docName+'_svgY'] = QVariant(self.svgItem.y())
            self.label.setText(u'Сдвиг x: %i, y %i'%(self.svgItem.x(), self.svgItem.y()))
        elif key == QChar(0x61) or key == QChar(0x444): # a|ф
            if hasattr(self.svgItem, 'setX'):
                self.svgItem.setX(self.svgItem.x() - 1)
            else:
                self.svgItem.setPos(self.svgItem.x() - 1, self.svgItem.y())
            QtGui.qApp.preferences.appPrefs[self.docName+'_svgX'] = QVariant(self.svgItem.x())
            self.label.setText(u'Сдвиг x: %i, y %i'%(self.svgItem.x(), self.svgItem.y()))
        elif key == QChar(0x64) or key == QChar(0x432): # d|в
            if hasattr(self.svgItem, 'setX'):
                self.svgItem.setX(self.svgItem.x() + 1)
            else:
                self.svgItem.setPos(self.svgItem.x() + 1, self.svgItem.y())
            QtGui.qApp.preferences.appPrefs[self.docName+'_svgX'] = QVariant(self.svgItem.x())
            self.label.setText(u'Сдвиг x: %i, y %i'%(self.svgItem.x(), self.svgItem.y()))
        self.parent().keyPressEvent(event)
        # Антон, а как это пересечётся с капс-локом или шифтом?
