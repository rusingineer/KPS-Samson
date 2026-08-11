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

from PyQt4 import QtGui
from PyQt4.QtCore import QObject, QVariant, SIGNAL

from Events.Utils  import getEventContextData
from library.Utils import forceString

from ActionPropertyValueType       import CActionPropertyValueType
from StringActionPropertyValueType import CStringActionPropertyValueType


class CHtmlActionPropertyValueType(CActionPropertyValueType):
    name         = 'Html'
    variantType  = QVariant.String
    preferredHeight = 20
    preferredHeightUnit = 1
    isHtml       = True
    initPresetValue = True

    class CPropEditor(QtGui.QTextEdit):
        def __init__(self, action, domain, parent, clientId, eventTypeId):
            QtGui.QTextEdit.__init__(self, parent)
            self.domain = domain
            self.eventEditor = None
            p = parent
            while p:
                if hasattr(p, 'eventEditor'):
                    self.eventEditor = p.eventEditor
                    break
                p = p.parent()


        def setValue(self, value):
            v = forceString(value)
            self.setHtml(v)


        def value(self):
            return unicode(self.toHtml())


        def contextMenuEvent(self, event):
            from library.PrintTemplates  import getPrintAction
            menu = self.createStandardContextMenu(event.pos())
            actions = menu.actions()
            topAction = actions[0] if actions else 0
            if self.domain and self.eventEditor is not None:
                action = getPrintAction(self, self.domain, name=u'Заполнить')
                QObject.connect(action, SIGNAL('printByTemplate(int)'), self.fillByTemplate)
                menu.insertAction(topAction, action)
                menu.insertSeparator(topAction)
            action = QtGui.QAction(u'Редактировать во внешнем редакторе', self)
            QObject.connect(action, SIGNAL('triggered()'), self.editInExternalEditor)
            action.setEnabled(bool(QtGui.qApp.documentEditor()))
            menu.insertAction(topAction, action)
            menu.insertSeparator(topAction)
            menu.exec_(event.globalPos())
            menu.deleteLater()


        def fillByTemplate(self, templateId):
            def work():
                from library.PrintTemplates  import getTemplate, compileAndExecTemplate, htmlTemplate
                data = getEventContextData(self.eventEditor)
                templateName, template, templateType, printBlank = getTemplate(templateId)
                if templateType != htmlTemplate:
                    template = u'<HTML><BODY>Поддержка шаблонов печати в формате'\
                        u' отличном от html не реализована</BODY></HTML>'
                templateResult = compileAndExecTemplate(templateName, template, data)
                self.setHtml(templateResult.content)
            QtGui.qApp.call(self, work)


        def editInExternalEditor(self):
            QtGui.qApp.editDocument(self.document())


    @staticmethod
    def convertDBValueToPyValue(value):
        return forceString(value)


    convertQVariantToPyValue = convertDBValueToPyValue


    def toInfo(self, context, v):
        return forceString(v) if v else ''


    @classmethod
    def getTableName(cls):
        return cls.tableNamePrefix+CStringActionPropertyValueType.name

    def getPresetValue(self, action):
        from library.PrintTemplates import getTemplate, compileAndExecTemplate, htmlTemplate
        from Events.ActionInfo import CCookedActionInfo
        from library.PrintInfo import CInfoContext
        from library.PrintTemplates import getPrintTemplates
        templates = getPrintTemplates(self.domain)
        if len(templates) > 0:
            context = CInfoContext()
            action = CCookedActionInfo(context, action.getRecord(), action)

            data = {'action': action}
            templateName, template, templateType, printBlank = getTemplate(templates[0].id)
            if templateType != htmlTemplate:
                template = u'<HTML><BODY>Поддержка шаблонов печати в формате' \
                           u' отличном от html не реализована</BODY></HTML>'
            templateResult = compileAndExecTemplate(templateName, template, data)
            return templateResult.content
        return None
