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
import os
import os.path
import re
import sys
import StringIO
import json
from urllib import urlencode
from urllib2 import urlopen, Request
from base64 import b64encode
from collections import namedtuple
from scipy import ndimage
import barcode

from PyQt4 import QtGui
from PyQt4.QtCore import SIGNAL, QBuffer, QByteArray, QDate, QDateTime, QUrl, QTemporaryFile
import tempfile


try:
    from bs4 import BeautifulSoup
    bsSupport = False
except ImportError,  e:
    BeautifulSoup = None

from Reports.ReportBrowser import CReportBrowser

try:
    exaroSupportError = u'QtScript: '
    import PyQt4.QtScript  # для cx_freeze, exaro неявно зависит от QtScript
    assert PyQt4.QtScript  # давим сообщение pyflakes
    exaroSupportError = u'Exaro: '
    import exaro
    exaroSupport = True
    exaroSupportError = u'-'
except ImportError as e:
    exaroSupport = False
    exaroSupportError += str(e).decode('cp1251') if sys.platform == 'win32' else str(e)

import io


from Reports.ReportView    import CPageFormat, CReportViewDialog, printTextDocument
from Orgs.Utils            import COrgInfo, COrgStructureInfo
from Orgs.PersonInfo       import CPersonInfo
from Orgs.ClientConsentAddingDialog import CClientConsentAddingDialog
from library.PrintInfo     import CInfoContext, CInfo, CDateInfo, CTimeInfo
from library.PrintDialog   import CDialogsInfo
from library.TextDocument  import CTextDocument
from library.AmountToWords import amountToWords, currencyRUR
from library.SVGView       import showSVG, printSVG
from library.code128       import code128
from library.qrcode.image.qimage import QRImage
from library.qrcode.main   import QRCode
import library.qrcode.constants
from library.BitsPack      import CBitsPack
from library.DbEntityCache import CDbEntityCache
from library.database      import decorateString
from library.userCertPlate import userCertPlate
from library.pdf417        import pdf417image
from library.Barcodes.qrcode     import qrcodeImage
from library.Barcodes.datamatrix import datamatrixImage
from library.Utils import forceInt, forceRef, forceString, forceStringEx, smartDict, unformatSNILS, toVariant, forceBool


u"""Шаблоны печати"""


__all__ = ( 'getPrintTemplates',
            'getFirstPrintTemplate',
            'getPrintAction',
            'getPrintButton',
            'customizePrintButton',
            'addButtonActions',
            'additionalCustomizePrintButton',
            'getPrintButtonWithOtherActions',
            'getTemplate',
            'execTemplate',
            'compileAndExecTemplate',
            'changeClientConsent',
            'applyTemplate',
            'applyTemplateInt',
            'applyTemplateList',
            'applyMultiTemplateList',
            'directPrintTemplate',
            'CPrintAction',
            'CPrintButton',
            'escape',
            'htmlTemplate',
          )


htmlTemplate = 0
exaroTemplate = 1
svgTemplate = 2
cssTemplate = 3

loadTemplatePageFormat = None

CPrintTemplateMiniDescr = namedtuple('CPrintTemplateMiniDescr', ['name', 'id', 'group'])


def getPrintTemplates(contexts, inAmbCard=None, isHtml=None, limit=None):
    u"""Returns array of print templates of context.
    Contexts may be list of scalar context.
    Print template is: CPrintTemplateMiniDescr(name, id, group)."""
    result = []
    if contexts:
        if not isinstance(contexts, list):
            contexts = [contexts]
        try:
            db = QtGui.qApp.db
            table = db.table('rbPrintTemplate')
            cond = [table['context'].inlist(contexts), table['deleted'].eq(0)]
            if inAmbCard is not None:
                cond.append(table['inAmbCard'].eq(inAmbCard))
            if isHtml:
                cond.append(table['type'].eq(0))

            for record in db.getRecordList(table,
                                           'name, id, groupName',
                                           cond,
                                           'code, name, id',
                                           limit=limit
                                           ):
                result.append(CPrintTemplateMiniDescr(forceString(record.value('name')),
                                                      forceInt(record.value('id')),
                                                      forceString(record.value('groupName'))
                                                      )
                              )
        except:
            QtGui.qApp.logCurrentException()
    return result


def getFirstPrintTemplate(context):
    templates = getPrintTemplates(context, limit=1)
    if templates:
        return templates[0]
    return None


def getClientConsentTypeListByPT(printTemplateId):
    result = []

    db = QtGui.qApp.db
    tablePTCCT = db.table('rbPrintTemplate_ClientConsentType')
    fields = [tablePTCCT['clientConsentType_id'].alias('clientConsentTypeId'),
              tablePTCCT['value'].alias('clientConsentValue')]
    cond = tablePTCCT['master_id'].eq(printTemplateId)
    recordList = db.getRecordList(tablePTCCT, fields, cond)
    for record in recordList:
        clientConsentTypeId = forceRef(record.value('clientConsentTypeId'))
        clientConsentValue  = forceInt(record.value('clientConsentValue'))
        result.append(smartDict(clientConsentTypeId=clientConsentTypeId, clientConsentValue=clientConsentValue))
    return result


def getPrintAction(parent, context, name=u'Печать', setShortcut=True):
    result = CPrintAction(name, None, None, parent)
    result.setContext(context, setShortcut)
    return result


def getPrintButton(parent, context='', name=u'Печать', shortcut='F6'):
    result = CPrintButton(parent, name, None)
    customizePrintButton(result, context, shortcut)
    return result


def customizePrintButton(btn, context, shortcut='F6'):
    u"""Set actions to btn: printing templates of context (or of list of contexts)"""
    templates = getPrintTemplates(context)
    if not templates:
        btn.setId(None)
        btn.setEnabled(False)
        btn.setShortcut(shortcut)
    elif len(templates) == 1:
        btn.setId(templates[0].id)
        btn.setShortcut('F6')
        btn.setEnabled(True)
    else:
        btn.setId(None)
        btn.setEnabled(True)
        subMenuDict = {}
        for i, template in enumerate(templates):
            if not template.group:
                action = CPrintAction(template.name, template.id, btn, btn)
                btn.addAction(action)
            else:
                subMenu = subMenuDict.get(template.group)
                if subMenu is None:
                    subMenu = QtGui.QMenu(template.group, btn.parentWidget())
                    subMenuDict[template.group] = subMenu
                action = CPrintAction(template.name, template.id, btn, btn)
                subMenu.addAction(action)
            if i == 0:
                action.setShortcut(shortcut)
        if subMenuDict:
            if not btn.menu():
                menu = QtGui.QMenu(btn.parentWidget())
                btn.setMenu(menu)
            for subMenuKey in sorted(subMenuDict.keys()):
                btn.menu().addMenu(subMenuDict[subMenuKey])
        btn.setShortcut('Alt+F6')


def addButtonActions(parent, btn, actions, connect=True):
    # otherActions - dictionaries for static actions from widget: {'action': action, 'slot':slot}
    for action in actions:
        btn.addAction(action['action'])
        if connect:
            action['action'].triggered.connect(action['slot'])


# todo: ликвидировать!
# у нас уже есть возможность создать action печати
# и всегда была возможность навесить на кнопку произвольный список действий.
# ergo: дополнительная кастомизация кнопки печати не нужна!
# ещё раз скажу: кнопка, которая кроме печати по заданному контексту позволяет делать ещё кое-что
# называется не "навороченная-кнопка-печати-с-блекджеком-и-шлюхами" а просто кнопка,
# не которую всегда можно было "повесить" хоть список произвольных действий, хоть развесистую менюшку...

def additionalCustomizePrintButton(parent, btn, context, otherActions=[]):
    #u"""Add new btn actions: printing templates of context (or list of contexts) and remove some actions"""
    additionalActions = []
    templates = getPrintTemplates(context)
    existsBtnMenu = None
    removeAdditionalActions(parent, btn, otherActions)
    if len(templates) > 0:
        prepareToAdditionalCustomizePrintButton(parent, btn, otherActions)
        existsBtnMenu = btn.menu()
        if existsBtnMenu and len(existsBtnMenu.actions()) > 0:
            btn.menu().addSeparator()
        if len(templates) == 1 and not existsBtnMenu:
            action = CPrintAction(templates[0].name, templates[0].id, btn, btn)
            btn.setId(templates[0].id)
            btn.setShortcut('F6')
            btn.setEnabled(True)
            additionalActions.append(action)
        else:
            subMenuDict={}
            for i, template in enumerate(templates):
                if not template.group:
                    action = CPrintAction(template.name, template.id, btn, btn)
                    additionalActions.append(action)
                    btn.addAction(action)
                    if i == 0:# and not existsBtnMenu:
                        action.setShortcut('F6')
                else:
                    subMenu = subMenuDict.get(template.group)
                    if subMenu is None:
                        subMenu = QtGui.QMenu(template.group, btn.parentWidget())
                        subMenuDict[template.group] = subMenu
                    action = CPrintAction(template.name, template.id, btn, btn)
                    subMenu.addAction(action)
                    additionalActions.append(subMenu.menuAction())
            if subMenuDict:
                for subMenuKey in sorted(subMenuDict.keys()):
                    btn.menu().addMenu(subMenuDict[subMenuKey])
            btn.setShortcut('Alt+F6')
        btn.setAdditionalActions(additionalActions)
    else:
        addButtonActions(parent, btn, otherActions)


# todo: надо убрать эту кнопку
def prepareToAdditionalCustomizePrintButton(parent, btn, otherActions=[]):
    if btn.isEnabled() and not btn.menu():
        if otherActions and len(otherActions) == 1:
            btn.clicked.disconnect(otherActions[0]['slot'])
            addButtonActions(parent, btn, otherActions)
        else:
            actionId = btn.id
            btn.setId(None)
            db = QtGui.qApp.db
            table = db.table('rbPrintTemplate')
            record = db.getRecord(table, 'name, id, dpdAgreement', actionId)
            if record:
                name = forceString(record.value('name'))
                id = forceInt(record.value('id'))
                # dpdAgreement = forceInt(record.value('dpdAgreement')) зачем?
                action = CPrintAction(name, id, btn, btn)
                btn.addAction(action)
    else:
        btn.setEnabled(True)
        for action in otherActions:
            action['action'].triggered.connect(action['slot'])


# todo: надо убрать эту кнопку
def removeAdditionalActions(parent, btn, otherActions):
    btnMenu = btn.menu()
    additionalActions = btn.popAdditionalActions()
    if btnMenu:
        for action in otherActions:
            action['action'].triggered.disconnect()
        for action in additionalActions:
            btnMenu.removeAction(action)
        for action in btnMenu.actions():
            if not forceStringEx(action.text()):
                btnMenu.removeAction(action)
        actionList = btnMenu.actions()
        if len(actionList) == 1:
            btn.setId(None)
            if otherActions and len(otherActions) == 1:
                btn.clicked.connect(otherActions[0]['slot'])
            else:
                action = actionList[0]
                btn.setId(action.id)
                btn.setShortcut('F6')
        elif len(actionList) == 0:
            btn.setMenu(None)
            btn.setId(None)
            btn.setEnabled(False)
    else:
        if btn.isEnabled() and len(additionalActions) == 1:
            id = btn.id
            actionId = additionalActions[0].id
            if id == actionId:
                btn.setId(None)
                btn.setEnabled(False)


# todo: надо убрать эту кнопку
def getPrintButtonWithOtherActions(parent, context, name=u'Печать', otherActions=[]):
    assert bool(context), 'need valid context'
    assert bool(otherActions),  'need set other actions'
    templates = getPrintTemplates(context)
    actionsCount = len(otherActions)
    if not templates:
        if actionsCount > 1:
            btn = CPrintButton(parent, name, None)
            btn.setId(None)
            btn.setEnabled(True)
            addButtonActions(parent, btn, otherActions)
        else:
            btn = CPrintButton(parent, name, None)
            if actionsCount == 1:
                btn.setEnabled(True)
                action = otherActions[0]
                btn.clicked.connect(action['slot'])
            else:
                btn.setEnabled(False)
    else:
        btn = CPrintButton(parent, name, None)
        btn.setId(None)
        btn.setEnabled(True)
        for i, template in enumerate(templates):
            action = CPrintAction(template.name, template.id, btn, btn)
            btn.addAction(action)
            if i == 0:
                action.setShortcut('F6')
        addButtonActions(parent, btn, otherActions)
        btn.setShortcut('Alt+F6')
    return btn


def getTemplate(templateId, retCode=False):
    u"""Возвращает код шаблона печати и код типа содержимого (html/exaro/svg)."""
    content = None
    code = None
    name = ''
    record = None
    printBlank = None
    type = None
    printBlank = False
    if templateId:
        record = QtGui.qApp.db.getRecord('rbPrintTemplate', '*', templateId)
    if record:
        if QtGui.qApp.isPrintDebugEnabled or forceBool(QtGui.qApp.preferences.appPrefs.get('templateEdit', False)):
            QtGui.qApp.debugPrintData.name = forceString(record.value('name'))
            QtGui.qApp.debugPrintData.context = forceString(record.value('context'))
            QtGui.qApp.debugPrintData.code = forceString(record.value('code'))
            QtGui.qApp.debugPrintData.groupName = forceString(record.value('groupName'))
        name = forceString(record.value('name'))
        code = forceString(record.value('code'))
        fileName = forceString(record.value('fileName'))
        printBlank = forceBool(record.value('printBlank'))
        if fileName:
            fullPath = os.path.join(QtGui.qApp.getTemplateDir(), fileName)
            if os.path.isfile(fullPath):
                for enc in ('utf-8', 'cp1251'):
                    try:
                        file = codecs.open(fullPath, encoding=enc, mode='r')
                        content = file.read()
                        break
                    except:
                        pass
        if not content:
            content = forceString(record.value('default'))
        type = forceInt(record.value('type'))

    if not content:
        name = u''
        content = u'<HTML><BODY>ШАБЛОН ДОКУМЕНТА ПУСТ ИЛИ ИСПОРЧЕН</BODY></HTML>'
        type = htmlTemplate
    if retCode:
        return name, content, type, printBlank, code
    return name, content, type, printBlank



def compileTemplate(template, fromWidget=None, templateId=None):
    # result is tuple (complied_code, source_code)
    parser = CTemplateParser(template, templateId=templateId)
    try:
        return parser.compileToCode()
    except:
        if fromWidget:
            fromWidget.setText(u'ОШИБКА ЗАПОЛНЕНИЯ ШАБЛОНА')
        else:
            QtGui.qApp.logCurrentException()
        raise


class CTemplateExecutionResult(object):
    __slots__ = ('documentName', 'content', 'canvases', 'supplements', 'currentAction', 'propertiesData')

    def __init__(self, documentName, content, canvases, supplements, currentAction=None, propertiesData={}):
        self.documentName = documentName
        self.content = content
        self.canvases = canvases
        self.supplements = supplements
        self.currentAction = currentAction
        self.propertiesData = propertiesData


def execTemplate(documentName, code, data, templateId, pageFormat=None, fromWidget=None):
    # code is tuple (complied_code, source_code, filename)
    filename = code[2]
    if not pageFormat:
        pageFormat = CPageFormat(pageSize=CPageFormat.A4, orientation=CPageFormat.Portrait, leftMargin=5, topMargin=5, rightMargin=5,  bottomMargin=5)
    try:
        infoContext = None
        for item in data.itervalues():
            if isinstance(item, CInfo):
                infoContext = item.context
                if infoContext:
                    break
        if not infoContext:
            infoContext = CInfoContext()

        stream = StringIO.StringIO()
        oldStdout = sys.stdout
        canvases = {}
        supplements = {}
        try:
            sys.stdout = stream
            execContext = CTemplateContext(data, infoContext, stream, documentName, pageFormat, templateId)
            # exec code[0] in execContext.globals, execContext
            execfile(filename, execContext.globals, execContext)
            global loadTemplatePageFormat
            if loadTemplatePageFormat:
                pageFormat.__dict__.update(loadTemplatePageFormat.__dict__)
                loadTemplatePageFormat = None
            canvases = execContext.getCanvases()
            supplements = execContext.getSupplements()
            documentName = execContext.getDocumentName()
            supressPreview = execContext.supressPreview
        except SystemExit:
            supressPreview = True
        finally:
            sys.stdout = oldStdout
        if os.path.exists(filename):
            os.remove(filename)
        if supressPreview:
            return CTemplateExecutionResult(None, None, None, None)
        else:
            return CTemplateExecutionResult(documentName, stream.getvalue(), canvases, supplements)
    except ETemplateContext, ex:
        if fromWidget:
            fromWidget.setText(u'ОШИБКА ЗАПОЛНЕНИЯ ШАБЛОНА')
        else:
            QtGui.QMessageBox.critical(None,  u'Печатная форма',
                ex.getRusMessage(),
                QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
            QtGui.qApp.logCurrentException()
            return CTemplateExecutionResult(None, None, None, None)
    except UserWarning:
        raise
    except Exception:
        if fromWidget:
            fromWidget.setText(u'ОШИБКА ЗАПОЛНЕНИЯ ШАБЛОНА')
        else:
            QtGui.qApp.log('Template code failed', "")
            QtGui.qApp.logCurrentException()
            raise


def compileAndExecTemplate(documentName, template, data, pageFormat=None, templateId=None):
    # u"""Заполняет шаблон печати данными и возвращает готовый код HTML/XML"""
        return execTemplate(documentName, compileTemplate(template), data, templateId, pageFormat)

class CConsentTypeListCache(CDbEntityCache):
    templateId2ConsentTypeList = {}

    @classmethod
    def get(cls, templateId):
        result = cls.templateId2ConsentTypeList.get(templateId, None)
        if result is None:
            cls.connect()
            result = getClientConsentTypeListByPT(templateId)
            cls.templateId2ConsentTypeList[templateId] = result
        return result

    @classmethod
    def purge(cls):
        cls.templateId2ConsentTypeList.clear()


def changeClientConsent(widget, clientId, templateId):
    consentTypeList = CConsentTypeListCache.get(templateId)
    if consentTypeList:
        dlg = CClientConsentAddingDialog(widget, clientId, consentTypeList)
        dlg.exec_()


def logRepCost(widget,  data):
    if QtGui.qApp.defaultKLADR()[:2] != u'23':
        return
    #  `id` INT NOT NULL AUTO_INCREMENT,
    #`event_id` INT NOT NULL COMMENT 'Событие {Event}',
    #`person_id` INT NOT NULL COMMENT 'Выдавший справку {Person}',
    #`date` DATETIME NOT NULL COMMENT 'Дата выдачи справки',
    event_id = data["event"].id
    person_id = QtGui.qApp.userId
    if (person_id==None or event_id==None):
        return
    date = QDateTime. currentDateTime()
    table = QtGui.qApp.db.table('soc_logRepCost')
    log = table.newRecord()
    log.setValue('event_id', toVariant(event_id))
    log.setValue('person_id', toVariant(person_id))
    log.setValue('date', toVariant(date))
    QtGui.qApp.db.insertRecord(table,log)


def applyTemplate(widget, templateId, data, fromWidget=None, signAndAttachHandler=None):
    # u'''Выводит на печать шаблон печати номер templateId с данными data'''
    name, template, templateType, printBlank, code = getTemplate(templateId, True)
    if code == '100':
        logRepCost(widget,  data)
    
    try:
        keys = data.keys()
        if data and ('client' in keys or 'clientId' in keys):
            if 'clientId' in keys:
                clientId = data['clientId']
            else:
                clientId = data['client'].id
            changeClientConsent(widget, clientId, templateId)
    except:
        pass

    applyTemplateInt(widget, name, template, data, templateType, fromWidget, signAndAttachHandler, printBlank, templateId)



def applyTemplateInt(widget, name, template, data, templateType=htmlTemplate, fromWidget=None, signAndAttachHandler=None, printBlank = None, templateId = None):
    # u'''Выводит на печать шаблон печати по имени name с кодом template и данными data'''
    pageFormat = CPageFormat(pageSize=CPageFormat.A4, orientation=CPageFormat.Portrait, leftMargin=5, topMargin=5, rightMargin=5,  bottomMargin=5)
    btnRedoInfo = [templateId, data, signAndAttachHandler]
    if QtGui.qApp.isPrintDebugEnabled or forceBool(QtGui.qApp.preferences.appPrefs.get('templateEdit', False)):
        QtGui.qApp.debugPrintData.template = template
        QtGui.qApp.debugPrintData.data = data
        QtGui.qApp.debugPrintData.pageFormat = pageFormat
    if templateType == exaroTemplate and not exaroSupport:
        templateType = htmlTemplate
        templateResult = exaroFallback()
    else:
        templateResult = compileAndExecTemplate(name, template, data, pageFormat)
    templateResult.propertiesData = {}
    if data.get('currentAction', None):
        templateResult.currentAction = data['currentAction']

    if templateResult.content is not None:
        if templateType == exaroTemplate:
            printExaroTemplate(templateResult.content, None, True)
        elif templateType == svgTemplate:
            showSVG(widget, templateResult, pageFormat, signAndAttachHandler, printBlank, btnRedoInfo)
        elif templateType == cssTemplate:
            showCSS(widget, templateResult.content, data)
        else:
            showHtml(widget, templateResult, pageFormat, fromWidget, signAndAttachHandler, btnRedoInfo)

# ###

def showCSS(widget, content, data):
    try:
        from Reports.ReportWEBView import CPageFormat, CReportWEBViewDialog, printTextDocument
        web = CReportWEBViewDialog(widget)
        web.btnSignAndAttach.setVisible(False)
        web.btnEdit.setVisible(False)
        # a = u'''<html>
        # <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
        # <head>
        #
        # <link href="C:\\Users\\prog9\\.samson-vista\\templates\\js\\style.css" rel="stylesheet">
        #
        #
        # </head>
        #
        # <!-- ПЕРВЫЙ ПРИМЕР -->
        #
        # <!-- ВТОРОЙ ПРИМЕР -->
        #
        # <ul id="menu">
        # <li><a href="#">Раздел меню №1</a></li>
        # <li><a href="#">Раздел меню №2</a>
        # 	<ul>
        # 		<li><a href="#">Подраздел №1 второго меню</a></li>
        # 		<li><a href="#">Подраздел №2 второго меню</a></li>
        # 	</ul>
        # </li>
        # <li><a href="#">Раздел меню №3</a>
        # 	<ul>
        # 		<li><a href="#">Подраздел №1 третьего меню</a></li>
        # 		<li><a href="#">Подраздел №2 третьего меню</a></li>
        # 		<li><a href="#">Подраздел №3 третьего меню</a></li>
        # 	</ul>
        # </li>
        # </ul>
        #
        #
        # </html>'''
        # web.txtReport = QWebView(web)
        if 'cacheTemplate' in content:
            QtGui.qApp.cacheTemplate = ['css', content, data]
        web.setHtml(content, data)
        web.exec_()
    except ImportError:
        pass


def applyTemplateList(widget, templateId, dataList, fromWidget=None, signAndAttachHandler=None):
    try:
        name, template, templateType, printBlank = getTemplate(templateId)
        applyTemplateListInt(widget, name, template, templateId, dataList, templateType, fromWidget, signAndAttachHandler, printBlank)
        if widget and hasattr(widget, 'lblTemplateName'): # WTF?
            widget.lblTemplateName.setText(name)
    except:
        fromWidget.setText(u'ОШИБКА ЗАПОЛНЕНИЯ ШАБЛОНА')


def applyTemplateListInt(widget, name, template, templateId, dataList, templateType=htmlTemplate, fromWidget=None, signAndAttachHandler=None, printBlank = None):
    pageFormat = CPageFormat(pageSize=CPageFormat.A4, orientation=CPageFormat.Portrait, leftMargin=5, topMargin=5, rightMargin=5,  bottomMargin=5)

    if templateType == exaroTemplate and not exaroSupport:
        templateType = htmlTemplate
        templateResult = exaroFallback()
    else:
        code = compileTemplate(template, fromWidget)
        content = None
        canvases = {}
        supplements = {}
        for idx, data in enumerate(dataList):
            # if idx > 0:
            #     content += '<BR clear=all style=\'page-break-before:always\'>'
            partTemplateResult = execTemplate(name, code, data, templateId, pageFormat=pageFormat, fromWidget=fromWidget)
            if partTemplateResult.content is not None:
                if content is None:
                    content = ''
                content += partTemplateResult.content
                canvases.update(partTemplateResult.canvases)
                supplements.update(partTemplateResult.supplements)
        templateResult = CTemplateExecutionResult(name, content, canvases, supplements)

    if templateResult.content is not None:
        if templateType == exaroTemplate:
            printExaroTemplate(templateResult.content, None, True)
        elif templateType == svgTemplate:
            showSVG(widget, templateResult, pageFormat, signAndAttachHandler, printBlank)
        else:
            showHtml(widget, templateResult, pageFormat, fromWidget, signAndAttachHandler)

# ###

def applyMultiTemplateList(widget, templateIdAndDataList, fromWidget=None, signAndAttachHandler=None, addPageBreaks=False):
    applyMultiTemplateListInt(widget, templateIdAndDataList, fromWidget, signAndAttachHandler, addPageBreaks)
    # if widget and hasattr(widget, 'lblTemplateName'):
    #     widget.lblTemplateName.setText(name)


def applyMultiTemplateListInt(widget, templateIdAndDataList, fromWidget=None, signAndAttachHandler=None, addPageBreaks=False):
    content = []
    pageFormats = []
    canvases = {}
    supplements = {}
    name = ''
    for templateId, data in templateIdAndDataList:
        name, template, templateType, printBlank = getTemplate(templateId)
        if templateType != htmlTemplate:
            continue
        pageFormat = CPageFormat(pageSize=CPageFormat.A4, orientation=CPageFormat.Portrait, leftMargin=5, topMargin=5, rightMargin=5,  bottomMargin=5)
        code = compileTemplate(template, fromWidget)
        partTemplateResult = execTemplate(name, code, data, templateId, pageFormat=pageFormat, fromWidget=fromWidget)
        if partTemplateResult and partTemplateResult.content is not None:
            content.append(partTemplateResult.content)
            pageFormats.append(pageFormat)
            canvases.update(partTemplateResult.canvases)
            supplements.update(partTemplateResult.supplements)
    if content:
        pageFormat = pageFormats[0]
        separator = "<div style='page-break-after: always;'></div><div>&nbsp;</div>" if addPageBreaks else "<br style='font-size:5pt'>"
        mergedContent = separator.join(content)
        templateResult = CTemplateExecutionResult(name, mergedContent, canvases, supplements)
        showHtml(widget, templateResult, pageFormat, fromWidget, signAndAttachHandler)


def showHtml(widget, templateResult, pageFormat, fromWidget=None, signAndAttachHandler=None, btnRedoInfo = None):
    if fromWidget:
        fromWidget.setText(templateResult.content)
        fromWidget.setCanvases(templateResult.canvases)
        if getattr(fromWidget, 'setPrintData', None):
            fromWidget.setPrintData({'templateResult': templateResult, 'pageFormat': pageFormat})
    else:
        reportView = CReportViewDialog(widget)
        reportView.setWindowTitle(unicode(templateResult.documentName))
        reportView.setText(templateResult.content)
        if 'cacheTemplate' in templateResult.content:
            QtGui.qApp.cacheTemplate = ['html', templateResult.content]
        reportView.setCanvases(templateResult.canvases)
        reportView.setSupplements(templateResult.supplements)
        reportView.setPageFormat(pageFormat)
        reportView.setSignAndAttachHandler(signAndAttachHandler)
        reportView.setRedoInfo(btnRedoInfo)

        # для самосборного эпикриза
        if BeautifulSoup:
            preparedText = templateResult.content.replace('<br>', '$br$').replace('<br/>', '$br$').replace('<br />', '$br$')
            dom = BeautifulSoup(preparedText, 'html.parser')
            # dom.prettify()
            textdata = dom.findAll('div')
            tmpDocument = CReportBrowser()

            for i in textdata:
                if i.attrs.get('id', None):
                    tmp_text = i.get_text().replace('$br$', '<br/>')
                    tmpDocument.setHtml(tmp_text)
                    templateResult.propertiesData[i.attrs['id']] = tmpDocument.document().toPlainText()
            #
        reportView.setCurrentAction(templateResult.currentAction, templateResult.propertiesData)
        if QtGui.qApp.isPrintDebugEnabled or forceBool(QtGui.qApp.preferences.appPrefs.get('templateEdit', False)):
            reportView.enableDebugButton()
        reportView.templateContent = templateResult.content
        reportView.exec_()
        reportView.deleteLater()


def directPrintTemplate(templateId, data, printer):
    name, template, templateType, printBlank = getTemplate(templateId)
    directPrintTemplateInt(name, template, data, printer, templateType)


def directPrintTemplateInt(name, template, data, printer, templateType=htmlTemplate):
    pageFormat = CPageFormat(pageSize=CPageFormat.A4, orientation=CPageFormat.Portrait, leftMargin=5, topMargin=5, rightMargin=5,  bottomMargin=5)
    pageFormat.setupPrinter(printer)

    if templateType == exaroTemplate and not exaroSupport:
        templateType = htmlTemplate
        templateResult = exaroFallback()
    else:
        templateResult = compileAndExecTemplate(name, template, data, pageFormat)

    if templateType == exaroTemplate:
        printExaroTemplate(templateResult.content, printer, False)
    elif templateType == svgTemplate:
        printSVG(unicode(templateResult.documentName), templateResult.content, printer)
    else:
        document = CTextDocument()
        document.setHtml(templateResult.content)
        document.setCanvases(templateResult.canvases)
        printTextDocument(document, unicode(templateResult.documentName), pageFormat, printer)


def printExaroTemplate(code, printer, showPreview):
#    u'Выводит на печать шаблон Exaro'
    report = exaro.Report.ReportEngine(QtGui.qApp)
    template = report.loadReportFromString(code.replace('\\{', '{').replace('\\}', '}'))
    if template:
        template.setShowSplashScreen(False)
        template.setShowExitConfirm(False)
        template.setShowPrintPreview(showPreview)
        template.setDatabase(QtGui.qApp.db.db)
        if printer:
            template.setPrinterName(printer)
        template.exec_()
        del template
    else:
        QtGui.QMessageBox.critical(None,  u'Внимание!',
            u'Невозможно сформировать отчет Exaro.',
            QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
    del report


def exaroFallback():
    return CTemplateExecutionResult('exaroFallback',
                                    u'<HTML><BODY>Поддержка отчетов в формате Exaro отключена. (%s)</BODY></HTML>' % exaroSupportError,
                                    {},
                                    {},
                                   )


class CPrintAction(QtGui.QAction):
    __pyqtSignals__ = ('printByTemplate(int)',
                      )
    def __init__(self, name, id, emitter, parent, metod=None):
        QtGui.QAction.__init__(self, name, parent)
        self.id = id
        self.emitter = emitter
        self.metod = metod
        self.context = None
        self.connect(self, SIGNAL('triggered()'), self.onTriggered)
        self._menu = None
        self.isNotEmpty = True


    def setEnabled(self, isEnabled):
        QtGui.QAction.setEnabled(self, isEnabled and self.isNotEmpty)


    def getMenu(self):
        if self._menu is None:
            self._menu = QtGui.QMenu(self.parentWidget())
        self.setMenu(self._menu)
        return self._menu


    def setContext(self, context, setShortcut=True):
        if self.context != context:
            templates = getPrintTemplates(context)
            self.isNotEmpty = bool(templates)
            if not templates:
                self.id = None
                self.setMenu(None)
                self.setEnabled(False)
#                if setShortcut:
#                    self.setShortcut(QtGui.QKeySequence())
            elif len(templates) == 1 and context!='reportsList':
                self.id = templates[0].id
                self.setMenu(None)
                self.setEnabled(True)
                if setShortcut and context!='ps':
                    self.setShortcut('F6')
            else:
                self.id = None
                menu = self.getMenu()
                subMenuDict={}
                menu.clear()
                firstTemplateWithoutGroup=0
                for i, template in enumerate(templates):
                    if not template.group:
                        action = CPrintAction(template.name, template.id, self, menu)
                        menu.addAction(action)
                        if setShortcut and firstTemplateWithoutGroup == 0 and context!='ps' and context!='reportsList':
                            action.setShortcut('F6')
                            firstTemplateWithoutGroup = 1
                    else:
                        subMenu = subMenuDict.get(template.group)
                        if subMenu is None:
                            subMenu = QtGui.QMenu(template.group, self.parentWidget())
                            subMenuDict[template.group] = subMenu
                        action = CPrintAction(template.name, template.id, self, menu)
                        subMenu.addAction(action)
                if subMenuDict:
                    for subMenuKey in sorted(subMenuDict.keys()):
                        menu.addMenu(subMenuDict[subMenuKey])
                self.setMenu(menu)
                self.setEnabled(True)
        self.context = context


    def onTriggered(self):
        if self.id:
            if self.metod:
                self.metod(self.id)
            else:
                emitter = self.emitter or self
                emitter.emit(SIGNAL('printByTemplate(int)'), self.id)




class CPrintButton(QtGui.QPushButton):
    __pyqtSignals__ = ('printByTemplate(int)',
                      )

    def __init__(self, parent, name='', id=None):
        QtGui.QPushButton.__init__(self, name, parent)
        self.setId(id)
        self.connect(self, SIGNAL('clicked()'), self.onClicked)
        self._additionalActions = []


    def additionalActions(self):
        return self._additionalActions


    def popAdditionalActions(self):
        result = self._additionalActions
        self._additionalActions = []
        return result


    def setAdditionalActions(self, additionalActions=[]):
        self._additionalActions = additionalActions


    def setId(self, id):
        self.id = id
        self.actions = []
        self._additionalActions = []
        self.setMenu(None)


    def addAction(self, action):
        menu = self.menu()
        if not menu:
            menu = QtGui.QMenu(self)
            self.setMenu(menu)
        self.actions.append(action)
        menu.addAction(action)


    def onClicked(self):
        if self.id:
            self.emit(SIGNAL('printByTemplate(int)'), self.id)


# ################################################


class CTemplateParser(object):
    def __init__(self, txt, filename = None, templateId=None):
        self.blockText = re.compile(r'''([^\\{]|\\.)*''')
        # self.blockCode = re.compile(r'''\{([^\\'"}]|\\.|'(\\.|[^'])*'|"(\\.|[^"])*")*\}''')
        self.keywords  = [('if',   re.compile(r'''\s*if\s*:\s*''')),
                          ('elif', re.compile(r'''\s*elif\s*:\s*''')),
                          ('else', re.compile(r'''\s*else\s*:\s*''')),
                          ('end',  re.compile(r'''\s*end\s*:\s*''')),
                          ('for',  re.compile(r'''\s*for\s*:\s*''')),
                          ('def',  re.compile(r'''\s*def\s*:\s*''')),
                          ('drop',  re.compile(r'''\s*drop\s*:\s*''')),
                          ('while',re.compile(r'''\s*while\s*:\s*''')),
                          ('break',re.compile(r'''\s*break\s*:\s*''')),
                          ('immed',re.compile(r'''\s*:\s*''')),
                          ('try',  re.compile(r'''\s*try\s*:\s*''')),
                          ('except',re.compile(r'''\s*except\s*:\s*''')),
                         ]
        self.pos = 0
        self.txt = txt
        self.filename = None
        if filename:
            self.filename = filename
        else:
            tmpFile = QTemporaryFile()
            tmpFile.open()
            self.filename = unicode(tmpFile.fileName())
            tmpFile.close()
        self.stream = StringIO.StringIO()


    def compileToStream(self):
        lex = self.compileInt(0, True)
        if lex:
            self.syntaxError('unexpected code', lex[1], lex[2])


#    def compileToString(self):
#        self.compileToStream()
#        return self.stream.getvalue()


    def compileToCode(self):
        self.compileToStream()
        program = self.stream.getvalue()
        if self.filename:
            with open(self.filename, 'w') as f:
                f.write('# -*- coding: utf-8 -*-\n')
                f.write(program.encode('utf-8'))
        return compile(program, self.filename, 'exec'), program, self.filename


    def compileInt(self, indent, check):
        prefix = '    '*indent
        oldLen = self.stream.len
        while True:
            lex = self.getLex()
            if not lex:
                break
            keyword = lex[0]
            if keyword == 'txt':
                if lex[2]:
                    print >>self.stream, prefix+'write('+repr(lex[2])+')'
            elif keyword == 'eval':
                expr = lex[2]
                if check:
                    self.checkExprSyntax(lex[1], expr)
                fmt = lex[3]
                if fmt == 'h' or lex[2].startswith('loadTemplate('):
                    print >>self.stream, prefix+'write('+expr+')'
                elif fmt == 'n':
                    print >>self.stream, prefix+'write(escapenl('+expr+'))'
                elif fmt == 'p':
                    print >>self.stream, prefix+'write(escapepar('+expr+'))'
                else:
                    print >>self.stream, prefix+'write(escape('+expr+'))'
            elif keyword == 'immed':
                txt = lex[2]
                if check:
                    self.checkImmedSyntax(lex[1], txt)
                print >>self.stream, prefix+txt
            elif keyword == 'for':
                startLex = lex
                txt = lex[2]
                if check:
                    self.checkForSyntax(lex[1], txt)
                print >>self.stream, prefix+'for '+txt+':'
                lex = self.compileInt(indent+1, check)
                if not lex:
                    self.syntaxError('for not closed', startLex[1], startLex[2])
                elif lex[0] != 'end':
                    self.syntaxError('unexpected code', lex[1], lex[2])
            elif keyword == 'while':
                startLex = lex
                if check:
                    self.checkExprSyntax(lex[1], lex[2])
                print >>self.stream, prefix+('while ')+lex[2]+':'
                lex = self.compileInt(indent+1, check)
                if not lex:
                    self.syntaxError('while not closed', startLex[1], startLex[2])
                elif lex[0] != 'end':
                    self.syntaxError('unexpected code', lex[1], lex[2])
            elif keyword == 'break':
                print >>self.stream, prefix+'break'
            elif keyword == 'if':
                startLex = lex
                if check:
                    self.checkExprSyntax(lex[1], lex[2])
                print >>self.stream, prefix+'if '+lex[2]+':'
                lex = self.compileInt(indent+1, check)
                while lex and lex[0] == 'elif':
                    startLex = lex
                    if check:
                        self.checkExprSyntax(lex[1], lex[2])
                    print >>self.stream, prefix+'elif '+lex[2]+':'
                    lex = self.compileInt(indent+1, check)
                if lex and lex[0] == 'else':
                    startLex = lex
                    print >>self.stream, prefix+'else:'
                    lex = self.compileInt(indent+1, check)
                if not lex:
                    self.syntaxError(startLex[0]+' not closed', startLex[1], startLex[2])
                elif lex[0] != 'end':
                    self.syntaxError('unexpected code', lex[1], lex[2])
            elif keyword == 'def':
                startLex = lex
                start = lex[1], self.stream.tell()
                print >>self.stream, prefix+'def '+lex[2]+':'
                lex = self.compileInt(indent+1, False)
                if not lex:
                    self.syntaxError('def not closed', startLex[1], startLex[2])
                elif lex[0] != 'end':
                    self.syntaxError('unexpected code', lex[1], lex[2])
                if check:
                    self.checkImmedSyntax(start[0], self.stream.getvalue()[start[1]:])
            elif keyword == 'drop':
                txt = lex[2]
                print >>self.stream, prefix+'try:'
                print >>self.stream, '    '*(indent+1)+txt+'.drop()'
                print >>self.stream, prefix+'except:'
                print >>self.stream, '    '*(indent+1)+'pass'
                print >>self.stream, prefix+'del '+txt
            elif keyword == 'try':
                startLex = lex
                print >>self.stream, prefix+'try:'
                lex = self.compileInt(indent+1, check)
                while lex and lex[0] == 'except':
                    if check:
                        self.checkExceptSyntax(lex[1], lex[2])
                    print >>self.stream, prefix+'except '+lex[2]+':'
                    lex = self.compileInt(indent+1, check)
                if not lex:
                    self.syntaxError('try not closed', startLex[1], startLex[2])
                elif lex[0] != 'end':
                    self.syntaxError('unexpected code', lex[1], lex[2])
            else:
                break
        if oldLen == self.stream.len:
            print >>self.stream, prefix+'pass'
        return lex


    def checkExprSyntax(self, loc, expr):
        try:
            code = 'if '+expr+' :\n    pass\n'
            compile(code,'<string>','exec')
            return
        except SyntaxError, err:
            self.syntaxError(err.msg, loc, expr)


    def checkExceptSyntax(self, loc, expr):
        try:
            code = 'try:\n    pass\nexcept '+expr+':\n    pass\n'
            compile(code, '<string>', 'exec')
            return
        except SyntaxError, err:
            self.syntaxError(err.msg, loc, expr)


    def checkImmedSyntax(self, loc, expr):
        try:
            code = expr+'\n'
            compile(code,'<string>','exec')
            return
        except SyntaxError, err:
            self.syntaxError(err.msg, loc, expr)


    def checkForSyntax(self, loc, expr):
        try:
            code = 'for '+expr+' :\n    pass\n'
            compile(code,'<string>','exec')
            return
        except SyntaxError, err:
            self.syntaxError(err.msg, loc, expr)


    def syntaxError(self, msg, offset, code):
        lineno = self.txt[:offset].count('\n')
        pos = -1
        for i in xrange(lineno):
            pos = self.txt.find('\n', pos+1)
        raise SyntaxError(msg, (self.filename, lineno+1, offset-pos-1, code if len(code)<48 else code[:48]+'...'))


    def matchBlockCode(self, txt, pos=0):
        startPos = txt.find('{', pos)
        if startPos == -1:
            return None
        endPos = startPos + 1
        unclosed = 0
        for char in txt[startPos:]:
            if char == '{':
                unclosed += 1
            elif char == '}':
                if unclosed > 0:
                    unclosed -= 1
                    if unclosed == 0:
                        break
                else:
                    return None
            endPos += 1
        return (startPos, endPos) if unclosed == 0 else None


    def getLex(self):
        if len(self.txt) == self.pos:
            return None
        elif self.txt[self.pos:self.pos+1] != '{':
            m = self.blockText.match(self.txt,self.pos)
            if m:
                self.pos = m.end()
                return ('txt', m.start(), self.txt[m.start(): m.end()]) # здесь stip не ставить, иначе ломаются шаблоны Exaro
        else:
            m = self.matchBlockCode(self.txt, self.pos)
            if m:
                (mStart, mEnd) = m  # unpack
                self.pos = mEnd
                for keyword, keywordre in self.keywords:
                    m2 = keywordre.match(self.txt, mStart+1)
                    if m2:
                        return (keyword, mStart, self.txt[m2.end():mEnd-1])
                txt = self.txt[mStart+1: mEnd-1]
                fmt = ''
                pos = txt.rfind(':')
                if pos>=0:
                    fmt = txt[pos+1:].strip()
                    if fmt in ('h','u','n','p',''):
                        txt = txt[:pos]
                        if fmt == 'u':
                            fmt = 'h'
                    else:
                        fmt = ''
                return ('eval', mStart, txt.lstrip(), fmt)
        self.syntaxError('bad block syntax', self.pos, self.txt[self.pos:])


# ####################################


class CDictProxy(object):
    def __init__(self, path, data):
        object.__setattr__(self, 'path', unicode(path))
        object.__setattr__(self, 'data', data)


    def __getattr__(self, name):
        if self.data.has_key(name):
            result = self.data[name]
            if type(result) == dict:
                return CDictProxy(self.path+'.'+unicode(name), result)
            else:
                return result
        else:
            s = self.path+'.'+unicode(name)
            QtGui.qApp.log(u'Ошибка при печати шаблона',
                           u'Переменная или функция "%s" не определена.\nвозвращается None'%s)
            return None


    def __setattr__(self, name, value):
        self.data[name] = value


    def __getitem__(self, name):
        return self.__getattr__(name)


    def __setitem__(self, name, value):
        self.__setattr__(name, value)


    def __repr__(self):
        return repr(self.data)


# ####################################


class CCanvas(object):
    black   = QtGui.QColor(  0,   0,   0)
    red     = QtGui.QColor(255,   0,   0)
    green   = QtGui.QColor(  0, 255,   0)
    yellow  = QtGui.QColor(255, 255,   0)
    blue    = QtGui.QColor(  0,   0, 255)
    magenta = QtGui.QColor(255,   0, 255)
    cyan    = QtGui.QColor(  0, 255, 255)
    white   = QtGui.QColor(255, 255, 255)

    def __init__(self, width, height):
        self.image = QtGui.QImage(width, height, QtGui.QImage.Format_RGB32)
        self.penColor = CCanvas.black
        self.brushColor = CCanvas.red
        self.fill(CCanvas.white)


    @staticmethod
    def rgb(self, r, g, b):
        return QtGui.QColor(r, g, b)


    def setPen(self, color):
        self.penColor = color


    def setBrush(self, color):
        self.brushColor = color


    def fill(self, color):
        painter = QtGui.QPainter(self.image)
        painter.fillRect(self.image.rect(), QtGui.QBrush(color))


    def line(self, x1, y1, x2, y2):
        painter = QtGui.QPainter(self.image)
        painter.setPen(QtGui.QPen(self.penColor))
        painter.drawLine(x1, y1, x2, y2)


    def ellipse(self, x, y, w, h):
        painter = QtGui.QPainter(self.image)
        painter.setPen(QtGui.QPen(self.penColor))
        painter.setBrush(QtGui.QBrush(self.brushColor))
        painter.drawEllipse(x, y, w, h)

    def setImage(self, path):
        self.image = QtGui.QImage(path)


# ####################################

class ExTemplateContext(Exception):
    def __init__(self, text):
        Exception.__init__(self, 'Template context error')
        self._rusText = u'Ошибка в данных печатной формы. %s'%text

    def getRusMessage(self):
        return self._rusText


# ####################################

class ETemplateContext(Exception):
    def __init__(self, text):
        Exception.__init__(self, 'Template context error')
        self._rusText = u'Ошибка в данных печатной формы. %s'%text

    def getRusMessage(self):
        return self._rusText


class CTemplateContext(object):
    def __init__(self, data, infoContext, stream, documentName, pageFormat, templateId):
        self.data = data
        self.pyplot = None
        now = QDateTime.currentDateTime()
        self.templateId = templateId
        builtins = {
                 'escape'              : escape,
                 'clearStyle'              : clearStyle,
                 'escapenl'            : escapenl,
                 'escapeNl'            : escapenl,
                 'escapepar'           : escapepar,
                 'escapePar'           : escapepar,
                 'escapesp'            : escapesp,
                 'escapeSpaces'        : escapesp,
                 'urlread'             : readUrl,
                 'readUrl'             : readUrl,
                 'loadJson'            : loadJson,
                 'loadTemplate'        : self.loadTemplate,
                 'runBrowser'          : self.runBrowser,
                 'currentDate'         : CDateInfo(now.date()),
                 'currentTime'         : CTimeInfo(now.time()),
                 'currentOrganisation' : infoContext.getInstance(COrgInfo, QtGui.qApp.currentOrgId()),
                 'currentOrgStructure' : infoContext.getInstance(COrgStructureInfo, QtGui.qApp.currentOrgStructureId()),
                 'currentPerson'       : infoContext.getInstance(CPersonInfo,  QtGui.qApp.userId),
                 'present'             : self.present,
                 'pdf417Url'           : self.pdf417Url,
                 'pdf417'              : self.pdf417,
                 'qrcodeUrl'           : self.qrcodeUrl,
                 'qrcode'              : self.qrcode,
                 'datamatrixUrl'       : self.datamatrixUrl,
                 'datamatrix'          : self.datamatrix,
                 'code128'             : code128,
                 'p38code'             : self.p38code,
                 'p38code23'           : self.p38code23,
                 'p38test'             : self.p38test,
                 'amountToWords'       : self.amountToWords,
                 'BitsPack'            : CBitsPack,
                 'Canvas'              : CCanvas,
                 'formatByTemplate'    : self.formatByTemplate,
                 'addSupplement'       : self.addSupplement,
                 'declination'       : self.declination,
                 'dialogs'             : infoContext.getInstance(CDialogsInfo),
                 'write'               : lambda string: '' if stream.write(string) else '',
                 'dbServerName'        : QtGui.qApp.preferences.dbServerName,
                 'defaultKLADR'        : QtGui.qApp.defaultKLADR(),
                 'provinceKLADR'       : QtGui.qApp.provinceKLADR(),
                 'getKLADRName'        : self.getKLADRName,
                 'getObjectGuidByKladr': self.getObjectGuidByKladr,
                 'getAddresByObjectGuid': self.getAddresByObjectGuid,
                 'setDocumentName'     : self.setDocumentName,
                 'getDocumentName'     : self.getDocumentName,
                 'userCertPlate'       : userCertPlate,
                 'exit'                : sys.exit,
                 'error'               : self.error,
                 'plt'                 : self.getPlt,
                 'getPltImage'         : self.getPltImage
               }
        if pageFormat:
            builtins['setPageSize'] = pageFormat.setPageSize
            builtins['setOrientation'] = pageFormat.setOrientation
            builtins['setPageOrientation'] = pageFormat.setOrientation
            builtins['setMargins'] = pageFormat.setMargins
            builtins['setLeftMargin'] = pageFormat.setLeftMargin
            builtins['setTopMargin'] = pageFormat.setTopMargin
            builtins['setRightMargin'] = pageFormat.setRightMargin
            builtins['setBottomMargin'] = pageFormat.setBottomMargin
        self.builtins = builtins
        self.globals = {}
        self.globals.update(data)
        self.globals.update(builtins)
        self._supplements = {}
        self._documentName = documentName
        self.supressPreview = False


    def __getitem__(self, key):
        if self.globals.has_key(key):
            result = self.globals[key]
        elif __builtins__.has_key(key):
            result = __builtins__[key]
        else:
            QtGui.qApp.log(u'Ошибка при печати шаблона',
                           u'Переменная или функция "%s" не определена.\nвозвращается None'%key)
            result = None

        if type(result) == dict:
            return CDictProxy(key, result)
        else:
            return result


    def __setitem__(self, key, value):
        if type(value) == CDictProxy:
            self.globals[key] = value.data
        else:
            self.globals[key] = value


    def __delitem__(self, key):
        del self.globals[key]


    def present(self, key):
        seq = key.split('.')
        key = seq[0]
        if self.globals.has_key(key):
            data = self.globals[key]
        elif __builtins__.has_key(key):
            data = __builtins__[key]
        else:
            return False
        for name in seq[1:]:
            if hasattr(data, 'has_key') and data.has_key(name):
                data = data[name]
            else:
                return False
        return True


    def runBrowser(self, url, getData=None):
        if getData is not None:
            if isinstance(getData, dict):
                url += '?' + urlencode(encodeDict(getData))
            elif isinstance(getData, (list, tuple)):
                url += '?' + urlencode(encodeList(getData))
            else:
                url += '?' + getData
        if QtGui.QDesktopServices.openUrl(QUrl.fromEncoded(url)):
            self.supressPreview = True
        else:
            raise ExTemplateContext(u'Невозможно открыть браузер')
        
    
    def loadTemplate(self, templateId=None):
        content = ''
        if not templateId or templateId == self.templateId:
            return content
        data = self.globals
        name, template, templateType, printBlank = getTemplate(templateId)
        pageFormat = CPageFormat(pageSize=CPageFormat.A4, orientation=CPageFormat.Portrait, leftMargin=5, topMargin=5,
                                 rightMargin=5, bottomMargin=5)
        templateResult = compileAndExecTemplate(name, template, data, pageFormat, templateId)
        if templateResult.content:
            content = templateResult.content
        if templateResult.supplements:
            self._supplements.update(templateResult.supplements)
        if pageFormat:
            global loadTemplatePageFormat
            loadTemplatePageFormat = pageFormat
        return content


    def __encodeUrl(self, scheme, params):
        return ( scheme
                 + '://localhost?'
                 + urlencode([(key, json.dumps(value))
                              for (key, value) in params.iteritems()
                             ]
                            )
               )


    def __generateImageAsUrl(self, imageGenerator, data, params):
        image = imageGenerator(data, **params)

        ba = QByteArray()
        buffer = QBuffer(ba)
        buffer.open(buffer.WriteOnly)
        image.save(buffer, 'PNG')
        return 'data:image/png;base64,' + b64encode(ba)

    
    def getPlt(self):
        if self.pyplot is None:
            try:
                configDir = QtGui.qApp.preferences.getDir()
                os.environ[ 'MPLCONFIGDIR' ] = os.path.join(configDir, 'matplotlib')
                os.environ[ 'MPLBACKEND' ] = 'Agg'
                self.pyplot = __import__('matplotlib.pyplot', fromlist=[''])
            except ImportError:
                self.pyplot = None
        if self.pyplot:
            return self.pyplot
        else:
            raise ETemplateContext(u'Отсутствует пакет matplotlib!')

    def getPltImage(self):
        if self.pyplot:
            buf = io.BytesIO()
            self.pyplot.savefig(buf, format='png')
            buf.seek(0)
            ba = QByteArray(buf.getvalue())
            return 'data:image/png;base64,' + b64encode(ba)
        else:
            raise ETemplateContext(u'Отсутствует пакет matplotlib!')


    def pdf417Url(self, data, **params):
#        params['data'] = data
#        return self.__encodeUrl('pdf417', params)
        return self.__generateImageAsUrl(pdf417image, data, params)


    def pdf417(self, data, **params):
        params['data'] = data
        return '<IMG SRC="%s">' % self.__encodeUrl('pdf417', params)


    def qrcodeUrl(self, data, **params):
#        params['data'] = data
#        return self.__encodeUrl('qrcode', params)
        return self.__generateImageAsUrl(qrcodeImage, data, params)



    def qrcode(self, data, **params):
        params['data'] = data
        return '<IMG SRC="%s">' % self.__encodeUrl('qrcode', params)


    def datamatrixUrl(self, data, **params):
#        params['data'] = data
#        return self.__encodeUrl('datamatrix', data, params)
        return self.__generateImageAsUrl(datamatrixImage, data, params)


    def datamatrix(self, data, **params):
        params['data'] = data
        return '<IMG SRC="%s">' % self.__encodeUrl('datamatrix', params)


    def p38test(self):
        return self.p38code('1027802751701', '1357', '41043', '4008', '4104300000002535', 'I67', '1', 100, 1, '3780115', u'4.5+80 мкг+мкг/доза', 1.234, u'008-656-445 65', '083', '1', QDate(2008, 3, 25))

    def p38code23(self, orgCode, doctorCode, SN, policySerial, policyNumber, MKB, fundingCode, benefitPersent, isIUN,
            remedyCode, remedyDosage, remedyQuantity, SNILS, cureFormCode, dosageUnitCode, personBenefitCategory, periodOfValidity,
            date, oneDose, countDays, dosesPerDay):
        def intToBits(data, bitsWidth):
            u"""Convert integer to base 2"""
            if isinstance(data,(int, long)):
                n = data
            elif not data:
                n = 0
            else:
                try:
                    n = int(data, 10)
                except:
                    n = 0
            result = format(n,'b')
            result = result.rjust(bitsWidth,'0') if len(result)<=bitsWidth else result[:bitsWidth]
            return result

        def strToBits(data, strWidth):
            s = unicode(data).encode('cp1251', 'ignore')
            s = s.ljust(strWidth,' ') if len(s)<=strWidth else s[:strWidth]
            result = ''.join(format(ord(c), '>08b') for c in s)
            return result

        def bitsToChars(bits):
            u"""Convert string with '0' and '1' to bytes"""
            result = ''
            for i in xrange(0, len(bits), 8):
                result += chr(int(bits[i:i+8], 2))
            return result

        bits  = strToBits(orgCode, 7) # Код ЛПУ 7 символов
        bits += strToBits(doctorCode, 7) # Таб. № 7 символов
        bits += strToBits(SN, 21) # Серия +" "+ Номер рецепта 21 символ
        bits += strToBits(policySerial + ' ' + policyNumber, 21) # Серия +" "+ Номер полиса 21 символ
        bits += strToBits(MKB, 6) # Код МКБ 6 символов
        bits += intToBits(fundingCode, 2) #  Источник финансирования 2 бита
        bits += ('0' if benefitPersent == 100 else '1') # Процент льготы 1 бит
        bits += intToBits(isIUN, 2) # Признак МНН/Торговое 2 бит
        bits += strToBits(remedyCode, 3) # Код МНН/Торгового 3 байта ???
        bits += intToBits(unformatSNILS(SNILS), 37) # СНИЛС 37 бит
        bits += intToBits(forceInt(cureFormCode), 10) # Код лек формы выпуска 10 бит ???
        bits += intToBits(dosageUnitCode, 8) # Код единицы измерения дозировки 8 бит
        bits += strToBits(remedyDosage, 12) # Дозировка 12 символов
        bits += intToBits(remedyQuantity, 14) # Количество единиц 14 бит
        bits += intToBits(personBenefitCategory, 10) # Льгота 10 бит
        # Дата выписки рецепта 16 бит
        bits += intToBits(date.year()-2000, 7)          
        bits += intToBits(date.month(), 4)              
        bits += intToBits(date.day(), 5)   
        bits += intToBits(oneDose, 14) # на 1 прием 14 бит ???
        bits += intToBits(countDays, 8) # Количество дней приема 8 бит
        bits += intToBits(forceInt(dosesPerDay), 6) # Количество приемов в день 6 бит
        chars = bitsToChars(bits)
        return 'p'+b64encode(chars)


    def p38code(self, OGRN, doctorCode, orgCode, series, number, MKB, fundingCode, benefitPersent, isIUN, remedyCode, remedyDosage, remedyQuantity, SNILS, personBenefitCategory, periodOfValidity, date, isVK=0):
        def intToBits(data, bitsWidth):
            u"""Convert integer to base 2"""
            if isinstance(data,(int, long)):
                n = data
            elif not data:
                n = 0
            else:
                try:
                    n = int(data, 10)
                except:
                    n = 0
            result = format(n,'b')
            result = result.rjust(bitsWidth,'0') if len(result)<=bitsWidth else result[:bitsWidth]
            return result

        def strToBits(data, strWidth):
            s = unicode(data).encode('cp1251', 'ignore')
            s = s.ljust(strWidth,' ') if len(s)<=strWidth else s[:strWidth]
            result = ''.join(format(ord(c), '>08b') for c in s)
            return result

        def bitsToChars(bits):
            u"""Convert string with '0' and '1' to bytes"""
            result = ''
            for i in xrange(0, len(bits), 8):
                result += chr(int(bits[i:i+8], 2))
            return result

        bits  = intToBits(OGRN, 50)                     #
        bits += strToBits(doctorCode, 7)                #
        bits += intToBits(OGRN, 50)                     #
        bits += strToBits(orgCode,  7)                  #
        bits += strToBits(series,  14)                  #
        bits += intToBits(number, 64)                   #
        bits += strToBits(MKB, 7)                       #
        bits += intToBits(fundingCode, 2)               #
        bits += ('0' if benefitPersent == 100 else '1') #
        bits += ('1' if isIUN else '0')                 #
        bits += intToBits(remedyCode, 44)               #
        bits += intToBits(unformatSNILS(SNILS), 37)     #
#        bits += strToBits(u'0'*13, 13)                  # 10. СНИЛС (Нозология) - возможно, потерянная ранее строка?
        bits += strToBits(remedyDosage, 20)             #
        bits += intToBits(int(float(remedyQuantity)*1000), 24) #
        bits += intToBits(personBenefitCategory, 10)    #
        bits += ('1' if periodOfValidity else '0')      #
        bits += intToBits(date.year()-2000, 7)          #
        bits += intToBits(date.month(), 4)              #
        bits += intToBits(date.day(), 5)                #
        bits += '1' if isVK else '0'                    # признак наличия ВК
        bits += '0'*(-len(bits)%8)                      # заполнение
        bits += intToBits(6, 8)                         # версия протокола
        chars = bitsToChars(bits)
        return 'p'+b64encode(chars)


    def qrcode(self, data, **kwargs):
        kwargs['image_factory'] = QRImage
        errorCorrection = kwargs.get('error_correction', None)
        if errorCorrection == 'L':
            kwargs['error_correction'] = library.qrcode.constants.ERROR_CORRECT_L
        elif errorCorrection == 'M':
            kwargs['error_correction'] = library.qrcode.constants.ERROR_CORRECT_M
        elif errorCorrection == 'Q':
            kwargs['error_correction'] = library.qrcode.constants.ERROR_CORRECT_Q
        elif errorCorrection == 'H':
            kwargs['error_correction'] = library.qrcode.constants.ERROR_CORRECT_H
        qr = QRCode(**kwargs)
        qr.add_data(data)
        image = qr.make_image().get_image()
        canvas = CCanvas(0, 0)
        canvas.setImage(image)
        return canvas


    def amountToWords(self, num, currency=currencyRUR):
        return amountToWords(num, currency)


#    def dbServerName(self):
#        return QtGui.qApp.preferences.dbServerName


    def getKLADRName(self, code):
        from KLADR.KLADRModel import getCityName
        return getCityName(code)


    def getObjectGuidByKladr(self, kladr):
        db = QtGui.qApp.db
        value = decorateString(unicode(kladr)[:15])
        query = db.query('SELECT fias.GetObjectGuidByKladr(%s)' % value)
        if query.first():
            return forceString(query.value(0))
        return u''


    def getAddresByObjectGuid(self, guid):
        db = QtGui.qApp.db
        value = decorateString(guid)
        query = db.query('SELECT fias.GetAddresByObjectGuid(%s)' % value)
        if query.first():
            return forceString(query.value(0))
        return u''


    def formatByTemplateId(self, templateId):
        templateName, template, templateType, printBlank = getTemplate(templateId)
        if templateType != htmlTemplate:
            template = u'<HTML><BODY>Поддержка шаблонов печати в формате'\
                u' отличном от html не реализована</BODY></HTML>'

        templateResult = compileAndExecTemplate(templateName, template, self.globals)
        return templateResult.content


    def formatByTemplate(self, name, printContext):
        # формирование html/xml по имени шаблона
        for template in getPrintTemplates(printContext):
            if template.name == name:
                return self.formatByTemplateId(template.id)
        return u'Шаблон "%s" не найден в контексте печати "%s"' % (name, printContext)


    def addSupplement(self, name, supplement):
        self._supplements[name] = supplement


    def getSupplements(self):
        return self._supplements

    def declination(self, name, code, shortName = None):
        last = False
        first = False
        patr = False

        if code == u'Р' or code == u'р':
            code = 1
        elif code == u'Д' or code == u'д':
            code = 2
        elif code == u'В' or code == u'в':
            code = 5
        elif code == u'Т' or code == u'т':
            code = 6
        elif code == u'П' or code == u'п':
            code = 7
        else:
            QtGui.QMessageBox.critical(None, u'Печатная форма', u'При склонении ФИО, указан некорректный падеж', QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
            return name.fullName


        result = ''
        a = name.lastName.lower()
        if u'неизвест' not in name.lastName.lower() or u'назвавш' not in name.lastName.lower():
            if u'назвавш' not in name.lastName.lower(): 
                alarm = False
                lastName = name.lastName
                firstName = name.firstName
            else:
                alarm = True
                lastName = name.firstName.split(' ')[0]
                firstName = name.firstName.split(' ')[-1]
        else:
            alarm = True
            lastName = name.lastName.split(' ')[1]
            firstName = name.firstName
        patrName = name.patrName
        sex = str(name.sexCode)
        for a in MainRowsSklonenie: #len(a[0])
            if a[0] == lastName[-len(a[0]):].upper() and a[4] == sex and a[3] == u'F' and a[code] != u'' and a[code] != u' ':
                last = lastName[:-len(a[0])] + a[code]
            if a[0] == firstName[-len(a[0]):].upper() and a[4] == sex and a[3] == u'N' and a[code] != u'' and a[code] != u' ':
                first = firstName[:-len(a[0])] + a[code]
            if a[0] == patrName[-len(a[0]):].upper() and a[4] == sex and a[3] == u'O' and a[code] != u'' and a[code] != u' ':
                patr = patrName[:-len(a[0])] + a[code]
        if last:
            result = last.capitalize() + ' '
        else:
            result = lastName + ' '
        if first:
            if shortName:
                result += first.capitalize()[0] + '.'
            else:
                result += first.capitalize() + ' '
        else:
            if shortName:
                result += firstName[0] + '.'
            else:
                result += firstName + ' '
        if patr:
            if shortName:
                result += patr.capitalize()[0] + '.'
            else:
                result += patr.capitalize()
        else:
            if shortName:
                result += patrName[0] + '.'
            else:
                result += patrName
        if alarm:
            if sex == '1':
                result = u'Неизвестного-Назвавшего-Себя' + ' ' + result
            else:
                result = u'Неизвестной-Назвавшей-Себя' + ' ' + result
        return result

    def getCanvases(self):
        result = {}
        for key, val in self.globals.iteritems():
            if isinstance(val, CCanvas):
                result[key] = val
        return result


    def error(self, text):
        raise ExTemplateContext(text)


    def setDocumentName(self, name):
        self._documentName = name


    def getDocumentName(self):
        return self._documentName



def escape(s):
    return unicode(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace('\'', '&#39;')

def clearStyle(s):
    if s and (isinstance(s, unicode) or isinstance(s, str)):
        if (u'<body' in s):
            start_body = s.find(u'<body')
            end_body = s[start_body:].find(u'>')
            kill_body = s[:(start_body + end_body) + 1]
            s = s.replace(kill_body, '')
            for i in range(s.count(u'<span')):
                beg_span = s.find(u'<span')
                end_span = s[beg_span:].find(u'>')
                kill_span = s[beg_span:(beg_span + end_span) + 1]
                s = s.replace(kill_span, '')
            s = s.replace(u'</span>', '').replace(u'</body>', '').replace(u'</html>', '')
            for i in range(s.count(u'<p')):
                beg_p = s.find(u'<p')
                end_p = s[beg_p:].find(u'>')
                kill_p = s[beg_p:(beg_p + end_p) + 1]
                s = s.replace(kill_p, '')
            s = s.replace(u'</p>', '')
            beg_table = s.find(u'<table')
            if beg_table > 0:
                kill_table = s[:beg_table]
                s = s.replace(kill_table, '')
            return s
        else:
            return s
    else:
        return

def escapenl(s):
    return escape(s).replace('\n', '<BR/>')


def escapepar(s):
    parBegin = '<P style="text-indent:20px">'
    parEnd = '</P>'
    return parBegin + escape(s).replace('\n', parEnd+parBegin)+parEnd


def escapesp(s):
    return escape(s).replace(' ', '&nbsp;')


def encodeDict(d):
    result = {}
    for key, val in d.items():
        result[key.encode('utf8') if isinstance(key, unicode) else str(key)] = val.encode('utf8') if isinstance(val, unicode) else str(val)
    return result


def encodeList(d):
    result = []
    for key, val in d:
        result.append( (key.encode('utf8') if isinstance(key, unicode) else str(key),
                        val.encode('utf8') if isinstance(val, unicode) else str(val)
                       )
                     )
    return result


def readUrl(url, getData=None, postData=None, timeout=10, jsonData=False,
            headers=None):
    if getData is not None:
        if isinstance(getData, dict):
            url += '?' + urlencode(encodeDict(getData))
        else:
            url += '?' + getData
    if postData is not None:
        if (isinstance(postData, dict) or
            (jsonData and isinstance(postData, list))):
            _headers = {}
            if jsonData:
                postData = json.dumps(postData)
                _headers = { 'content-type' : 'application/json',
                             'content-length': len(postData) }
                if headers:
                    _headers.update(headers)
            else:
                postData = urlencode(encodeDict(postData))
            url = Request(url, postData, _headers)

    stream = urlopen(url, timeout = timeout)
    result = stream.read().decode('utf8')
    stream.close()
    return loadJson(result) if jsonData else result


def loadJson(s):
    try:
        return json.loads(s)
    except:
        return s


if __name__ == '__main__':
    readUrl('http://ya.ru')
    app = QtGui.QApplication(sys.argv)
    if exaroSupport:
        reportEngine = exaro.Report.ReportEngine(app)
        report = reportEngine.loadReport('report.bdrt')
        if report:
            report.setShowSplashScreen(False)
            report.exec_()
        else:
            print 'report create failed'
    else:
        print 'Exaro is not supported'




# отступ | поиск | родительный | дательный | F- фамилия N- имя O - отчество | пол | винительный | творительный | предложный |
MainRowsSklonenie = [
    (u'ИН', u'ИНА', u'ИНУ', u'F', u'1', u'ИНА', u' ', u'ИНЕ'),
    (u'ОВ', u'ОВА', u'ОВУ', u'F', u'1', u'ОВА', u' ', u'ОВЕ'),
    (u'ОВА', u'ОВОЙ', u'ОВОЙ', u'F', u'2', u'ОВУ', u'ОВОЙ', u'ОВОЙ'),
    (u'АС', u'АСА', u'АСУ', u'F', u'1', u'АС', u'АСОМ', u'АСЕ'),
    (u'ЕВ', u'ЕВА', u'ЕВУ', u'F', u'1', u'ЕВА', u' ', u'ЕВЕ'),
    (u'АЙ', u'АЯ', u'АЮ', u'F', u'1', u'АЯ', u' ', u'АЕ'),
    (u'АД', u'АДА', u'АДУ', u'F', u'1', u'АДА', u' ', u'АДЕ'),
    (u'АК', u'АКА', u'АКУ', u'F', u'1', u'АКА', u' ', u'АКЕ'),
    (u'АН', u'АНА', u'АНУ', u'F', u'1', u'АНА', u' ', u'АНЕ'),
    (u'ЕД', u'ЕДА', u'ЕДУ', u'F', u'1', u'ЕДА', u' ', u'ЕДЕ'),
    (u'ЖА', u'ЖУ', u'ЖЕ', u'F', u'1', u'ЖУ', u' ', u'ЖЕ'),
    (u'ИЙ', u'ОГО', u'ОМУ', u'F', u'1', u'ОГО', u' ', u'ОМ'),
    (u'ИК', u'ИКА', u'ИКУ', u'F', u'1', u'ИКА', u' ', u'ИКЕ'),
    (u'ИЧ', u'ИЧА', u'ИЧУ', u'F', u'1', u'ИЧА', u' ', u'ИЧЕ'),
    (u'ЙМ', u'ЙМА', u'ЙМУ', u'F', u'1', u'ЙМА', u' ', u'ЙМЕ'),
    (u'КО', u'КО', u'КО', u'F', u'1', u'КО', u' ', u'КО'),
    (u'ЛИ', u'ЛИ', u'ЛИ', u'F', u'1', u'ЛИ', u' ', u'ЛИ'),
    (u'ЛО', u'ЛО', u'ЛО', u'F', u'1', u'ЛО', u' ', u'ЛО'),
    (u'НД', u'НДА', u'НДУ', u'F', u'1', u'НДА', u' ', u'НДЕ'),
    (u'НЬ', u'НЯ', u'НЮ', u'F', u'1', u'НЯ', u' ', u'НЕ'),
    (u'ОК', u'КА', u'КУ', u'F', u'1', u'КА', u' ', u'КЕ'),
    (u'УН', u'УНА', u'УНУ', u'F', u'1', u'УНА', u' ', u'УНЕ'),
    (u'ХА', u'ХУ', u'ХЕ', u'F', u'1', u'ХУ', u' ', u'ХЕ'),
    (u'ХО', u'ХО', u'ХО', u'F', u'1', u'ХО', u' ', u'ХО'),
    (u'ШИ', u'ШИ', u'ШИ', u'F', u'1', u'ШИ', u' ', u'ШИ'),
    (u'ЫК', u'ЫКА', u'ЫКУ', u'F', u'1', u'ЫКА', u' ', u'ЫКЕ'),
    (u'ЫХ', u'ЫХ', u'ЫХ', u'F', u'1', u'ЫХ', u' ', u'ЫХ'),
    (u'ЬЦ', u'ЬЦА', u'ЬЦУ', u'F', u'1', u'ЬЦА', u' ', u'ЬЦЕ'),
    (u'ИК', u'ИКА', u'ИКУ', u'N', u'1', u'ИКА', u'ИКОМ', u'ИКЕ'),
    (u'АС', u'АСА', u'АСУ', u'N', u'1', u'АС', u'АСОМ', u'АСЕ'),
    (u'АВ', u'АВА', u'АВУ', u'N', u'1', u'АВА', u' ', u'АВЕ'),
    (u'АЙ', u'АЯ', u'АЮ', u'N', u'1', u'АЯ', u' ', u'АЕ'),
    (u'АН', u'АНА', u'АНУ', u'N', u'1', u'АНА', u' ', u'АНЕ'),
    (u'АМ', u'АМА', u'АМУ', u'N', u'1', u'АМА', u' ', u'АМЕ'),
    (u'АТ', u'АТА', u'АТУ', u'N', u'1', u'АТА', u' ', u'АТЕ'),
    (u'АХ', u'АХА', u'АХУ', u'N', u'1', u'АХА', u' ', u'АХЕ'),
    (u'ДР', u'ДРА', u'ДРУ', u'N', u'1', u'ДРА', u' ', u'ДРЕ'),
    (u'ЕВ', u'ЬВА', u'ЬВУ', u'N', u'1', u'ЬВА', u' ', u'ЬВЕ'),
    (u'ЕГ', u'ЕГА', u'ЕГУ', u'N', u'1', u'ЕГА', u' ', u'ЕГЕ'),
    (u'ЕД', u'ЕДА', u'ЕДУ', u'N', u'1', u'ЕДА', u' ', u'ЕДЕ'),
    (u'ЕЙ', u'ЕЯ', u'ЕЮ', u'N', u'1', u'ЕЯ', u' ', u'ЕЕ'),
    (u'ЕЛ', u'ЛА', u'ЛУ', u'N', u'1', u'ЛА', u' ', u'ЛЕ'),
    (u'ЕН', u'ЕНА', u'ЕНУ', u'N', u'1', u'ЕНА', u' ', u'ЕНЕ'),
    (u'ЕФ', u'ЕФА', u'ЕФУ', u'N', u'1', u'ЕФА', u' ', u'ЕФЕ'),
    (u'ИМ', u'ИМА', u'ИМУ', u'N', u'1', u'ИМА', u' ', u'ИМЕ'),
    (u'ИР', u'ИРА', u'ИРУ', u'N', u'1', u'ИРА', u' ', u'ИРЕ'),
    (u'ЛЬ', u'ЛЯ', u'ЛЮ', u'N', u'1', u'ЛЯ', u' ', u'ЛЕ'),
    (u'ОД', u'ОДА', u'ОДУ', u'N', u'1', u'ОДА', u' ', u'ОДЕ'),
    (u'РД', u'РДА', u'РДУ', u'N', u'1', u'РДА', u' ', u'РДЕ'),
    (u'РЬ', u'РЯ', u'РЮ', u'N', u'1', u'РЯ', u' ', u'РЕ'),
    (u'ТР', u'ТРА', u'ТРУ', u'N', u'1', u'ТРА', u' ', u'ТРЕ'),
    (u'ТЬ', u'ТЯ', u'ТЮ', u'N', u'1', u'ТЯ', u' ', u'ТЕ'),
    (u'УР', u'УРА', u'УРУ', u'N', u'1', u'УРА', u' ', u'УРЕ'),
    (u'ША', u'ШУ', u'ШЕ', u'N', u'1', u'ШУ', u' ', u'ШЕ'),
    (u'УС', u'УСА', u'УСУ', u'N', u'1', u'УСА', u' ', u'УСЕ'),
    (u'ЫМ', u'ЫМА', u'ЫМУ', u'N', u'1', u'ЫМА', u' ', u'ЫМЕ'),
    (u'ЯЗ', u'ЯЗА', u'ЯЗУ', u'N', u'1', u'ЯЗА', u' ', u'ЯЗЕ'),
    (u'ЯМ', u'ЯМА', u'ЯМУ', u'N', u'1', u'ЯМА', u' ', u'ЯМЕ'),
    (u'ЯР', u'ЯРА', u'ЯРУ', u'N', u'1', u'ЯРА', u' ', u'ЯРЕ'),
    (u'ЯС', u'ЯСА', u'ЯСУ', u'N', u'1', u'ЯСА', u' ', u'ЯСЕ'),
    (u'ЯТ', u'ЯТА', u'ЯТУ', u'N', u'1', u'ЯТА', u' ', u'ЯТЕ'),
    (u'ИЧ', u'ИЧА', u'ИЧУ', u'O', u'1', u'ИЧА', u' ', u'ИЧЕ'),
    (u'НА', u'НЫ', u'НЕ', u'O', u'2', u'НУ', u'НОЙ', u'НЕ'),
    (u'ВЬ', u'ВИ', u'ВИ', u'N', u'2', u'ВЬ', u' ', u'ВИ'),
    (u'ЕЯ', u'ЕИ', u'ЕЕ', u'N', u'2', u'ЕЮ', u' ', u'ЕЕ'),
    (u'ИЯ', u'ИИ', u'ИЕ', u'N', u'2', u'ИЮ', u' ', u'ИЕ'),
    (u'ЛЯ', u'ЛИ', u'ЛЕ', u'N', u'2', u'ЛЮ', u' ', u'ЛЕ'),
    (u'РЯ', u'РИ', u'РЕ', u'N', u'2', u'РЮ', u' ', u'РЕ'),
    (u'ЬЯ', u'ЬИ', u'ЬЕ', u'N', u'2', u'ЬЮ', u' ', u'ЬЕ'),
    (u'ЬЯ', u'ЬИ', u'ЬЕ', u'N', u'1', u'ЬЮ', u' ', u'ЬЕ'),
    (u'АК', u'АК', u'АК', u'F', u'2', u'АК', u' ', u'АК'),
    (u'АЯ', u'ОЙ', u'ОЙ', u'F', u'2', u'УЮ', u' ', u'ОЙ'),
    (u'ВА', u'ВОЙ', u'ВОЙ', u'F', u'2', u'ВУ', u' ', u'ВОЙ'),
    (u'НА', u'НОЙ', u'НОЙ', u'F', u'2', u'НУ', u' ', u'НЕ'),
    (u'НД', u'НД', u'НД', u'F', u'2', u'НД', u' ', u'НД'),
    (u'ХА', u'ХИ', u'ХЕ', u'F', u'2', u'ХУ', u' ', u'ХУ'),
    (u'РС', u'РСА', u'РСУ', u'N', u'1', u'РСА', u' ', u'РСЕ'),
    (u'АЧ', u'АЧА', u'АЧУ', u'F', u'1', u'АЧА', u' ', u'АЧЕ'),
    (u'АР', u'АРА', u'АРУ', u'N', u'1', u'АРА', u' ', u'АРЕ'),
    (u'ИХ', u'ИХ', u'ИХ', u'F', u'1', u'ИХ', u' ', u'ИХ'),
    (u'А', u'Ы', u'Е', u'N', u'2', u'У', u' ', u'Е'),
    (u'НА', u'НЫ', u'НЕ', u'N', u'2', u'НУ', u' ', u'НЕ'),
    (u'ЕЙ', u'ЕЯ', u'ЕЮ', u'F', u'1', u'ЕЯ', u' ', u'ЕЕ'),
    (u'ЕК', u'ЕКА', u'ЕКУ', u'N', u'1', u'ЕКА', u' ', u'ЕКЕ'),
    (u'ЕМ', u'ЕМА', u'ЕМУ', u'N', u'1', u'ЕМА', u' ', u'ЕМЕ'),
    (u'ЕР', u'ЕРА', u'ЕРУ', u'F', u'1', u'ЕРА', u' ', u'ЕРЕ'),
    (u'ЕР', u'ЕРА', u'ЕРУ', u'N', u'1', u'ЕРА', u' ', u'ЕРЕ'),
    (u'ЕЦ', u'ЦА', u'ЦУ', u'F', u'1', u'ЦА', u' ', u'ЦЕ'),
    (u'ИЕЦ', u'ИЙЦА', u'ИЙЦУ', u'F', u'1', u'ИЙЦА', u' ', u'ИЙЦЕ'),
    (u'ЗЕ', u'ЗЕ', u'ЗЕ', u'F', u'1', u'ЗЕ', u' ', u'ЗЕ'),
    (u'ИД', u'ИДА', u'ИДУ', u'N', u'1', u'ИДА', u' ', u'ИДЕ'),
    (u'ИЙ', u'ИЯ', u'ИЮ', u'N', u'1', u'ИЯ', u' ', u'ИЕ'),
    (u'ИЛ', u'ИЛА', u'ИЛУ', u'N', u'1', u'ИЛА', u' ', u'ИЛЕ'),
    (u'ИМ', u'ИМА', u'ИМУ', u'F', u'1', u'ИМА', u' ', u'ИМЕ'),
    (u'ИН', u'ИНА', u'ИНУ', u'N', u'1', u'ИНА', u' ', u'ИНЕ'),
    (u'ИС', u'ИСА', u'ИСУ', u'N', u'1', u'ИСА', u' ', u'ИСЕ'),
    (u'ИСА', u'ИСЫ', u'ИСЕ', u'N', u'2', u'ИСУ', u'ИСА', u'ИСЕ'),
    (u'ИТ', u'ИТА', u'ИТУ', u'N', u'1', u'ИТА', u' ', u'ИТЕ'),
    (u'ИХ', u'ИХА', u'ИХУ', u'N', u'1', u'ИХА', u' ', u'ИХЕ'),
    (u'КА', u'КУ', u'КЕ', u'F', u'1', u'КУ', u' ', u'КЕ'),
    (u'ЛА', u'ЛУ', u'ЛЕ', u'F', u'1', u'ЛУ', u' ', u'ЛЕ'),
    (u'ЛЛ', u'ЛЛА', u'ЛЛУ', u'N', u'1', u'ЛЛА', u' ', u'ЛЛЕ'),
    (u'ЛН', u'ЛНА', u'ЛНУ', u'F', u'1', u'ЛНА', u' ', u'ЛНЕ'),
    (u'ЛЬ', u'ЛЯ', u'ЛЮ', u'F', u'1', u'ЛЯ', u' ', u'ЛЕ'),
    (u'МА', u'МУ', u'МЕ', u'N', u'1', u'МУ', u' ', u'МЕ'),
    (u'НО', u'НО', u'НО', u'F', u'1', u'НО', u' ', u'НО'),
    (u'НТ', u'НТА', u'НТУ', u'F', u'1', u'НТА', u' ', u'НТЕ'),
    (u'ОВ', u'ОВА', u'ОВУ', u'N', u'1', u'ОВА', u' ', u'ОВЕ'),
    (u'ОЙ', u'ОГО', u'ОМУ', u'F', u'1', u'ОГО', u' ', u'ОМ'),
    (u'ОН', u'ОНА', u'ОНУ', u'N', u'1', u'ОНА', u' ', u'НЕ'),
    (u'ОР', u'ОРА', u'ОРУ', u'N', u'1', u'ОРА', u' ', u'ОРЕ'),
    (u'РЬ', u'РЯ', u'РЮ', u'F', u'1', u'РЯ', u' ', u'РЕ'),
    (u'СЬ', u'СЯ', u'СЮ', u'N', u'1', u'СЯ', u' ', u'СЕ'),
    (u'УБ', u'УБА', u'УБУ', u'N', u'1', u'УБА', u' ', u'УБЕ'),
    (u'УК', u'УКА', u'УКУ', u'F', u'1', u'УКА', u' ', u'УКЕ'),
    (u'УП', u'УПА', u'УПУ', u'N', u'1', u'УПА', u' ', u'УПЕ'),
    (u'УС', u'УСА', u'УСУ', u'F', u'1', u'УСА', u' ', u'УСЕ'),
    (u'УХ', u'УХА', u'УХУ', u'F', u'1', u'УХА', u' ', u'УХЕ'),
    (u'ЦА', u'ЦУ', u'ЦЕ', u'F', u'1', u'ЦУ', u' ', u'ЦЕ'),
    (u'ША', u'ШУ', u'ШЕ', u'F', u'1', u'ШУ', u' ', u'ШЕ'),
    (u'ЫЙ', u'ОГО', u'ОМУ', u'F', u'1', u'ОГО', u' ', u'ОМ'),
    (u'ЫН', u'ЫНА', u'ЫНУ', u'F', u'1', u'ЫНА', u' ', u'ЫНЕ'),
    (u'ЫШ', u'ЫША', u'ЫШУ', u'F', u'1', u'ЫША', u' ', u'ЫШЕ'),
    (u'ЬМ', u'ЬМА', u'ЬМУ', u'F', u'1', u'ЬМА', u' ', u'ЬМЕ'),
    (u'ЮК', u'ЮКА', u'ЮКУ', u'F', u'1', u'ЮКА', u' ', u'ЮКЕ'),
    (u'Ч', u'Ч', u'Ч', u'F', u'2', u'Ч', u' ', u'Ч'),
    (u'Н', u'НА', u'НУ', u'F', u'1', u'НА', u' ', u'НЕ'),
    (u'УЖ', u'УЖА', u'УЖУ', u'F', u'1', u'УЖА', u' ', u'УЖЕ'),
    (u'КА', u'КИ', u'КЕ', u'F', u'2', u'КУ', u' ', u'КЕ'),
    (u'ОЧЬ', u'ОЧЕРИ', u'ОЧЕРИ', u'F', u'2', u'ОЧЬ', u' ', u'ОЧЕРИ'),
    (u'РА', u'РЫ', u'РЕ', u'F', u'2', u'РУ', u' ', u'РЕ'),
    (u'ЯТЬ', u'ЯТЯ', u'ЯТЮ', u'F', u'1', u'ЯТЯ', u' ', u'ЯТЕ'),
    (u'АТЬ', u'АТЕРИ', u'АТЕРИ', u'F', u'2', u'АТЬ', u' ', u'АТЕРИ'),
    (u'ЦА', u'ЦЫ', u'ЦЕ', u'F', u'2', u'ЦУ', u' ', u'ЦЕ'),
    (u'ЕКР', u'ЕКРА', u'ЕКРУ', u'F', u'1', u'ЕКРА', u' ', u'ЕКРЕ'),
    (u'ЕСТЬ', u'ЕСТЯ', u'ЕСТЮ', u'F', u'1', u'ЕСТЯ', u' ', u'ЕСТЕ'),
    (u'ЩА', u'ЩИ', u'ЩЕ', u'F', u'2', u'ЩУ', u' ', u'ЩЕ'),
    (u'КО', u'КО', u'КО', u'F', u'2', u'КО', u' ', u'КО'),
    (u'МУЖ', u'МУЖА', u'МУЖУ', u'W', u'1', u'МУЖА', u' ', u'МУЖЕ'),
    (u'ЖЕНА', u'ЖЕНЫ', u'ЖЕНЕ', u'W', u'2', u'ЖЕНУ', u' ', u'ЖЕНЕ'),
    (u'ОТЕЦ', u'ОТЦА', u'ОТЦУ', u'W', u'1', u'ОТЦА', u' ', u'ОТЦЕ'),
    (u'МАТЬ', u'МАТЕРИ', u'МАТЕРИ', u'W', u'2', u'МАТЬ', u' ', u'МАТЕРИ'),
    (u'СЫН', u'СЫНА', u'СЫНУ', u'W', u'1', u'СЫНА', u' ', u'СЫНЕ'),
    (u'ДОЧЬ', u'ДОЧЕРИ', u'ДОЧЕРИ', u'W', u'2', u'ДОЧЬ', u' ', u'ДОЧЕРИ'),
    (u'ТЕСТЬ', u'ТЕСТЯ', u'ТЕСТЮ', u'W', u'1', u'ТЕСТЯ', u' ', u'ТЕСТЕ'),
    (u'ТЕЩА', u'ТЕЩИ', u'ТЕЩЕ', u'W', u'2', u'ТЕЩУ', u' ', u'ТЕЩЕ'),
    (u'ЗЯТЬ', u'ЗЯТЯ', u'ЗЯТЮ', u'W', u'1', u'ЗЯТЯ', u' ', u'ЗЯТЕ'),
    (u'СНОХА', u'СНОХИ', u'СНОХЕ', u'W', u'2', u'СНОХУ', u' ', u'СНОХЕ'),
    (u'СВЕКР', u'СВЕКРА', u'СВЕКРУ', u'W', u'1', u'СВЕКРА', u' ', u'СВЕКРЕ'),
    (u'СВЕКРОВЬ', u'СВЕКРОВИ', u'СВЕКРОВИ', u'W', u'2', u'СВЕКРОВЬ', u' ', u'СВЕКРОВИ'),
    (u'ДЕД', u'ДЕДА', u'ДЕДУ', u'W', u'1', u'ДЕДА', u' ', u'ДЕДЕ'),
    (u'БАБКА', u'БАБКИ', u'БАБКЕ', u'W', u'2', u'БАБКУ', u' ', u'БАБКЕ'),
    (u'БРАТ', u'БРАТА', u'БРАТУ', u'W', u'1', u'БРАТА', u' ', u'БРАТЕ'),
    (u'СЕСТРА', u'СЕСТРЫ', u'СЕСТРЕ', u'W', u'2', u'СЕСТРУ', u' ', u'СЕСТРЕ'),
    (u'ПАСЫНОК', u'ПАСЫНКА', u'ПАСЫНКУ', u'W', u'1', u'ПАСЫНКА', u' ', u'ПАСЫНКЕ'),
    (u'ПАДЧЕРИЦА', u'ПАДЧЕРИЦЫ', u'ПАДЧЕРИЦЕ', u'W', u'2', u'ПАДЧЕРИЦУ', u' ', u'ПАДЧЕРИЦЕ'),
    (u'ВНУК', u'ВНУКА', u'ВНУКУ', u'W', u'1', u'ВНУКА', u' ', u'ВНУКЕ'),
    (u'ВНУЧКА', u'ВНУЧКИ', u'ВНУЧКЕ', u'W', u'2', u'ВНУЧКУ', u' ', u'ВНУЧКЕ'),
    (u'ЗНАКОМЫЙ', u'ЗНАКОМОГО', u'ЗАКОМОМУ', u'W', u'1', u'ЗНАКОМОГО', u' ', u'ЗНАКОМОМ'),
    (u'ЗНАКОМАЯ', u'ЗНАКОМОЙ', u'ЗНАКОМОЙ', u'W', u'2', u'ЗНАКОМУЮ', u' ', u'ЗНАКОМОЙ'),
    (u'ПОЛКОВНИК', u'ПОЛКОВНИКА', u'ПОЛКОВНИКУ', u'W', u'1', u'ПОЛКОВНИКА', u' ', u'ПОЛКОВНИКЕ'),
    (u'А', u'Ы', u'Е', u'N', u'1', u'У', u' ', u'Е'),
    (u'А', u'Ы', u'Е', u'F', u'1', u'У', u' ', u'Е'),
    (u'УН', u'УНА', u'УНУ', u'N', u'1', u'УНА', u' ', u'УНЕ'),
    (u'НАЧАЛЬНИК', u'НАЧАЛЬНИКА', u'НАЧАЛЬНИКУ', u'W', u'1', u'НАЧАЛЬНИКА', u' ', u'НАЧАЛЬНИКЕ'),
    (u'ОГЛЫ', u'ОГЛЫ', u'ОГЛЫ', u'O', u'1', u'ОГЛЫ', u' ', u'ОГЛЫ'),
    (u'КЫЗЫ', u'КЫЗЫ', u'КЫЗЫ', u'O', u'2', u'КЫЗЫ', u' ', u'КЫЗЫ'),
    (u'УСЬ', u'УСЯ', u'УСЮ', u'F', u'1', u'УСЯ', u' ', u'УСЕ'),
    (u'ЯН', u'ЯНА', u'ЯНУ', u'N', u'1', u'ЯНА', u' ', u'ЯНЕ'),
    (u'ТЕЙ', u'ТЕЙ', u'ТЕЙ', u'F', u'2', u'ТЕЙ', u' ', u'ТЕЙ'),
    (u'ЦОЙ', u'ЦОЙ', u'ЦОЙ', u'F', u'1', u'ЦОЙ', u' ', u'ЦОЙ'),
    (u'НИЕ', u'НИЯ', u'НИЮ', u'Z', u'1', u'НИЕ', u' ', u'НИИ'),
    (u'КА', u'КИ', u'КЕ', u'Z', u'1', u'КУ', u' ', u'КЕ'),
    (u'ЬЕ', u'ЬЯ', u'ЬЮ', u'Z', u'1', u'ЬЕ', u' ', u'ЬЕ'),
    (u'КИЙ', u'КОГО', u'КОМУ', u'Z', u'1', u'КИЙ', u' ', u'КОМ'),
    (u'НИЙ', u'НЕГО', u'НЕМУ', u'Z', u'1', u'НИЙ', u' ', u'НЕМ'),
    (u'ЫЙ', u'ОГО', u'ОМУ', u'Z', u'1', u'ЫЙ', u' ', u'ОМ'),

]
