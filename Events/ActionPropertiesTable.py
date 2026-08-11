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

import json
import math

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QAbstractTableModel, QPoint, QEvent, QMimeData, QModelIndex, QPointF, QRectF, QSize, QString, QVariant, pyqtSignature, SIGNAL, QRect, QTimer
from Events.ActionProperty.StringActionPropertyValueType import CStringActionPropertyValueType

from library.Utils import conv_data, foldText, forceDate, forceInt, forceDouble, forceRef, forceString, forceStringEx, \
    getPref, setPref, toVariant, trim, forceBool

from library.crbcombobox import CRBModelDataCache
from library.PreferencesMixin import CPreferencesMixin
from PropertyHistoryDialog import CPropertyHistoryDialog
from ActionPropertyChooser import CActionPropertyChooser
from Events.Action import CActionType


class InterpretationData(object):
    def __init__(self):
        self.map = {}

    def getEval(self, id):
        if not id:
            return None
        eval = self.map.get(id)
        if not eval:
            eval = QtGui.qApp.db.getRecord('rbResultInterpretation', '*', id)
            self.map[id] = eval
        return eval

    def getNameById(self, id):
        eval = self.getEval(id)
        return forceString(eval.value('name')) if eval else None

    def getColorById(self, id):
        eval = self.getEval(id)
        return forceString(eval.value('color')) if eval else None

    def isWhiteText(self, id):
        eval = self.getEval(id)
        return forceBool(eval.value('isWhiteText')) if eval else False


class CActionPropertiesTableModel(QAbstractTableModel):
    __pyqtSignals__ = ('actionNameChanged()',
                       'setEventEndDate(QDate)',
                       'setCurrentActionPlannedEndDate(QDate)',
                       'actionAmountChanged(double)',
                      )

    column = [u'Назначено', u'Значение',  u'Ед.изм.',  u'Норма', u'Оценка', u'Комментарий']
    visibleAll = 0
    visibleInJobTicket = 1
    ciIsAssigned   = 0
    ciValue      = 1
    ciUnit       = 2
    ciNorm       = 3
    ciEvaluation = 4
    ciComment = 5


    def __init__(self, parent, visibilityFilter=0):
        QAbstractTableModel.__init__(self, parent)
        self.action = None
        self.clientId = None
        self.clientNormalParameters = {}
        self.propertyTypeList = []
        self.unitData = CRBModelDataCache.getData('rbUnit', True)
        self.visibilityFilter = visibilityFilter
        self.readOnly = False
        self.actionStatusTip = None
        self.headerSortingCol = {}


    def getClientNormalParameters(self):
        clientNormalParameters = {}
        if self.clientId:
            db = QtGui.qApp.db
            table = db.table('Client_NormalParameters')
            cond = [table['client_id'].eq(self.clientId),
                    table['deleted'].eq(0)
                    ]
            records = db.getRecordList(table, '*', cond, order = table['idx'].name())
            for record in records:
                templateId = forceRef(record.value('template_id'))
                norm = forceStringEx(record.value('norm'))
                if templateId:
                    clientNormalParameters[templateId] = norm
        return clientNormalParameters


    def setReadOnly(self, value):
        self.readOnly = value


    def setAction(self, action, clientId, clientSex, clientAge, eventTypeId=None):
        self.action = action
        self.clientId = clientId
        self.clientNormalParameters = self.getClientNormalParameters()
        self.eventTypeId = eventTypeId
        if self.action:
            actionType = action.getType()
            propertyTypeList = actionType.getPropertiesById().items()
            propertyTypeList.sort(key=lambda x: (x[1].idx, x[0]))
            self.propertyTypeList = [x[1] for x in propertyTypeList if x[1].applicable(clientSex, clientAge) and self.visible(x[1])]
        else:
            self.propertyTypeList = []
        for propertyType in self.propertyTypeList:
            propertyType.shownUp(action, clientId)
        self.updateActionStatusTip()
        self.reset()

# WTF?
    def setAction2(self, action, clientId, clientSex=None, clientAge=None, eventTypeId=None):
        self.action = action
        self.clientId = clientId
        self.clientNormalParameters = self.getClientNormalParameters()
        self.eventTypeId = eventTypeId
        if self.action:
            propertyTypeList = [(id, prop.type()) for (id, prop) in action.getPropertiesById().items()]
            propertyTypeList.sort(key=lambda x: (x[1].idx, x[0]))
            self.propertyTypeList = [x[1] for x in propertyTypeList if x[1].applicable(clientSex, clientAge) and self.visible(x[1]) and x[1].typeName!='PacsImages']
            actionType = action.getType()
            propertyTypeList = actionType.getPropertiesTypeByTypeName('PacsImages')
            if propertyTypeList:
                self.propertyTypeList.extend(propertyTypeList)
        else:
            self.propertyTypeList = []

        for propertyType in self.propertyTypeList:
            propertyType.shownUp(action, clientId) ### WFT? почему showUp а не hideDown или не shiftLeft?
        self.updateActionStatusTip()
        self.reset()


    def updateActionStatusTip(self):
        # update self.actionStatusTip by self.action
        if self.action:
            actionType = self.action.getType()
            self.actionStatusTip = actionType.code + ': ' + actionType.name
        else:
            self.actionStatusTip = None


    def visible(self, propertyType):
        return self.visibilityFilter == self.visibleAll or \
               self.visibilityFilter == self.visibleInJobTicket and propertyType.visibleInJobTicket


    def columnCount(self, index = None):
        return 6


    def rowCount(self, index = QModelIndex()):
        return len(self.propertyTypeList)


    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return QVariant(self.column[section])
#            if role == Qt.ToolTipRole:
#                return self.__cols[section].toolTip()
#            if role == Qt.WhatsThisRole:
#                return self.__cols[section].whatsThis()
        elif orientation == Qt.Vertical:
            propertyType = self.propertyTypeList[section]
            property = self.action.getPropertyById(propertyType.id)
            if role == Qt.DisplayRole:
                return QVariant(foldText(propertyType.name, [CActionPropertiesTableView.titleWidth]))
            elif role == Qt.ToolTipRole:
                result = propertyType.descr if trim(propertyType.descr) else propertyType.name
                return QVariant(result)
            elif role == Qt.TextAlignmentRole:
                return QVariant(Qt.AlignLeft|Qt.AlignTop)
            elif role == Qt.ForegroundRole:
                evaluation = property.getEvaluation()
                if evaluation:
                    return QVariant(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
            elif role == Qt.FontRole:
                evaluation = property.getEvaluation()
                if (evaluation and abs(evaluation) == 2):
                    font = QtGui.QFont()
                    font.setBold(True)
                    return QVariant(font)
        return QVariant()


    def getPropertyType(self, row):
        return self.propertyTypeList[row]


    def hasCommonPropertyChangingRight(self, row):
        propertyType = self.propertyTypeList[row]
        if propertyType.canChangeOnlyOwner == 0:  # все могут редактировать свойство
            return True
        elif propertyType.canChangeOnlyOwner == 1 and self.action:
            setPersonId = forceRef(self.action.getRecord().value('setPerson_id'))
            return setPersonId == QtGui.qApp.userId
        elif propertyType.canChangeOnlyOwner == 2 and self.action:
            person_id = forceRef(self.action.getRecord().value('person_id'))
            return person_id == QtGui.qApp.userId
        return False

    def getProperty(self, row):
        propertyType = self.propertyTypeList[row]
        return self.action.getPropertyById(propertyType.id)

    def flags(self, index):
        row = index.row()
        column = index.column()
        propertyType = self.propertyTypeList[row]
        if propertyType.isPacsImage():
            return Qt.ItemIsSelectable|Qt.ItemIsEditable|Qt.ItemIsEnabled
        if self.readOnly or (self.action and self.action.isLocked()):
            if propertyType.isImage():
                return Qt.ItemIsSelectable|Qt.ItemIsEditable|Qt.ItemIsEnabled
            elif propertyType.isUrl():
                return Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled
            else:
                return Qt.ItemIsEnabled|Qt.ItemIsSelectable
        else:
            if column == self.ciIsAssigned and self.propertyTypeList[row].isAssignable:
                return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsUserCheckable
            if self.hasCommonPropertyChangingRight(row):
                if column == self.ciIsAssigned and propertyType.isAssignable:
                    return Qt.ItemIsSelectable|Qt.ItemIsEnabled|Qt.ItemIsUserCheckable
                elif column == self.ciValue:
                    if propertyType.isBoolean():
                        return Qt.ItemIsSelectable|Qt.ItemIsEnabled|Qt.ItemIsUserCheckable
                    return Qt.ItemIsSelectable|Qt.ItemIsEditable|Qt.ItemIsEnabled
                elif column == self.ciEvaluation:
                    propertyType = propertyType
                    if propertyType.defaultEvaluation in (0, 1):# 0-не определять, 1-автомат
                        return Qt.ItemIsSelectable|Qt.ItemIsEnabled
                    elif propertyType.defaultEvaluation in (2, 3):# 2-полуавтомат, 3-ручное
                        return Qt.ItemIsSelectable|Qt.ItemIsEditable|Qt.ItemIsEnabled
                elif column == self.ciComment:
                    return Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled
            elif propertyType.isUrl():
                return Qt.ItemIsSelectable | Qt.ItemIsEditable | Qt.ItemIsEnabled
            return Qt.ItemIsSelectable|Qt.ItemIsEnabled


    def data(self, index, role=Qt.DisplayRole):
        row = index.row()
        column = index.column()
        propertyType = self.propertyTypeList[row]
        property = self.action.getPropertyById(propertyType.id)
        if role == Qt.DisplayRole:
            if column == self.ciValue:
                if propertyType.isBoolean():
                    return toVariant('    ' + propertyType.descr)
                return toVariant(property.getText())
            elif column == self.ciUnit:
                return QVariant(self.unitData.getNameById(property.getUnitId()))
            elif column == self.ciNorm:
                return toVariant(property.getNorm())
            elif column == self.ciEvaluation:
                evaluation = property.getEvaluation()
                if evaluation is None:
                    s = self.getDefaultEvaluation(propertyType, property, index)
#                    s = ''
                else:
                    s = ('%+d'%evaluation) if evaluation else '0'
                return toVariant(s)
            elif column == self.ciComment:
                return QVariant(property.getComment())
            else:
                return QVariant()
        elif role == Qt.CheckStateRole:
            if column == self.ciValue:
                if propertyType.isBoolean():
                    return QVariant(Qt.Checked if property.getValue() else Qt.Unchecked)
            if column == self.ciIsAssigned:
                if propertyType.isAssignable:
                    return toVariant(Qt.Checked if property.isAssigned() else Qt.Unchecked)
        elif role == Qt.EditRole:
            if column == self.ciIsAssigned:
                return toVariant(property.getStatus())
            elif column == self.ciValue:
                return toVariant(property.getValue())
            elif column == self.ciUnit:
                return toVariant(property.getUnitId())
            elif column == self.ciNorm:
                return toVariant(property.getNorm())
            elif column == self.ciEvaluation:
                return toVariant(property.getEvaluation())
            elif column == self.ciComment:
                return toVariant(property.getComment())
            else:
                return QVariant()
        elif role == Qt.TextAlignmentRole:
            if column == self.ciValue:
                if propertyType.isBoolean():
                    return QVariant(Qt.AlignLeft | Qt.AlignVCenter)
            return QVariant(Qt.AlignLeft|Qt.AlignTop)
        elif role == Qt.DecorationRole:
            return QVariant()
#            if column == self.ciValue:
#                image = property.getImage()
#                if isinstance(image, QtGui.QImage):
#                    return toVariant(QtGui.QPixmap.fromImage(image))
#                return toVariant(image)
#            else:
#                return QVariant()
        elif role == Qt.ForegroundRole:
            evaluation = property.getEvaluation()
            if evaluation:
                return QVariant(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
        elif role in [Qt.FontRole,  Qt.BackgroundColorRole]:
            norm = property.getNorm()
            value = property.getValue()
            if QtGui.qApp.preferences.propertyColorTest and column == self.ciValue and propertyType.typeName in ['String', 'Integer', 'Double'] and norm and value:
                try:
                    if propertyType.typeName == 'String':
                        value = value.replace(',', '.')
                    value = forceDouble(value)
                    norm = norm.replace(',', '.')
                    for delim in ['-', '>', '<']:
                        parts = norm.split(delim)
                        if len(parts) == 2:
                            font = QtGui.QFont()
                            if delim == '-' and value >= forceDouble(parts[0]) and value <= forceDouble(parts[1]):
                                pass
                            elif delim == '>' and value > forceDouble(parts[1]):
                                pass
                            elif delim == '<' and value < forceDouble(parts[1]):
                                pass
                            else:
                                if role == Qt.FontRole:
                                    font.setBold(True)
                                    return QVariant(font)
                                else:
                                    return QVariant(QtGui.QBrush(QtGui.QColor(QtGui.qApp.preferences.propertyColorTest)))
                            break
                except ValueError:
                    return QVariant()
            elif QtGui.qApp.preferences.propertyColor:
                if role == Qt.BackgroundColorRole and (property.type().penalty > 0 or property.type().isFill) and not property.getValue():
                    return QVariant(QtGui.QBrush(QtGui.QColor(QtGui.qApp.preferences.propertyColor)))
            if role == Qt.FontRole:
                evaluation = property.getEvaluation()
                if evaluation and abs(evaluation) == 2:
                    font = QtGui.QFont()
                    font.setBold(True)
                    return QVariant(font)
        elif role == Qt.ToolTipRole:
            if column == self.ciIsAssigned:
                if propertyType.isAssignable:
                    return toVariant(u'Назначено' if property.isAssigned() else u'Не назначено')
        elif role == Qt.StatusTipRole:
            if self.actionStatusTip:
                return toVariant(self.actionStatusTip)
        return QVariant()


    def getDefaultEvaluation(self, propertyType, property, index):
        isClientNormalParameters = False
        templateId = property.getTemplateId()
        if templateId:
            clientNormalParameters = trim(self.clientNormalParameters.get(templateId, u''))
            if clientNormalParameters:
                property.setNorm(clientNormalParameters)
                isClientNormalParameters = True
        if propertyType.defaultEvaluation in (1, 2) or isClientNormalParameters:
            if propertyType.defaultEvaluation == 2 and not isClientNormalParameters:
                if property.getEvaluation() is not None:
                    return ('%+d'%property.getEvaluation())
            value = unicode(property.getText())
            if bool(value):
                try:
                    value = float(value)
                except ValueError:
                    return ''
                norm = property.getNorm()
                parts = norm.split('-')
                if len(parts) == 2:
                    try:
                        bottom = float(parts[0].replace(',', '.'))
                        top    = float(parts[1].replace(',', '.'))
                    except ValueError:
                        return ''
                    if bottom > top:
                        return ''
                    if value < bottom:
                        evaluation = -1
                    elif value > top:
                        evaluation = 1
                    else:
                        evaluation = 0
                    index = self.index(index.row(), self.ciEvaluation)
                    self.setData(index, QVariant(evaluation))
                    return '%+d'%evaluation
        return ''

# WFT?
    def sort(self, column, order):
        flag = False
        if order == 1:
            flag = True
        if column == self.ciIsAssigned:
            self.propertyTypeList.sort(key = lambda x: self.action.getPropertyById(x.id).isAssigned(), reverse = flag)
        if column == self.ciValue:
            self.propertyTypeList.sort(key = lambda x: conv_data(self.action.getPropertyById(x.id).getText()), reverse = flag)
        if column == self.ciUnit:
            self.propertyTypeList.sort(key = lambda x: conv_data(self.unitData.getNameById(self.action.getPropertyById(x.id).getUnitId())), reverse = flag)
        if column == self.ciNorm:
            self.propertyTypeList.sort(key = lambda x: conv_data(self.action.getPropertyById(x.id).getNorm()), reverse = flag)
        if column == self.ciEvaluation:
            self.propertyTypeList.sort(key = lambda x: conv_data(self.action.getPropertyById(x.id).getEvaluation()), reverse = flag)
        if column == self.ciComment:
            self.propertyTypeList.sort(key=lambda x: conv_data(self.action.getPropertyById(x.id).getComment()),
                                       reverse=flag)
        self.reset()


    def setData(self, index, value, role=Qt.EditRole):
        row = index.row()
        column = index.column()
        propertyType = self.propertyTypeList[row]
        property = self.action.getPropertyById(propertyType.id)

        if role == Qt.EditRole:
            if column == self.ciValue:
                if not propertyType.isVector:
                    oldValue = property.getValue()
                    newValue = propertyType.convertQVariantToPyValue(value)
                    if oldValue != newValue:
                        if property.type().isNomenclatureValueType():
                            property.preApplyDependents(self.action)
                            property.setValue(newValue)
                            self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
                            self.getDefaultEvaluation(propertyType, property, index)
                            if property.isActionNameSpecifier():
                                self.action.updateSpecifiedName()
                                self.emit(SIGNAL('actionNameChanged()'))
                            property.applyDependents(self.action)
                        else:
                            property.preApplyDependents(self.action)
                            property.setValue(propertyType.convertQVariantToPyValue(value))
                            self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
                            self.getDefaultEvaluation(propertyType, property, index)
                            if property.isActionNameSpecifier():
                                self.action.updateSpecifiedName()
                                self.emit(SIGNAL('actionNameChanged()'))
                            property.applyDependents(self.action)
                        if propertyType.isJobTicketValueType():
                            self.action.setPlannedEndDateOnJobTicketChanged(property.getValue())
                        if propertyType.whatDepends:
                            self.updateDependedProperties(propertyType.whatDepends)
                    return True
            elif column == self.ciEvaluation:
                property.setEvaluation(None if value.isNull() else forceInt(value))
                self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
                return True
            elif column == self.ciComment:
                property.setComment(forceString(value))
                self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
                return True
        elif role == Qt.CheckStateRole:
            if column == self.ciValue:
                if propertyType.isBoolean():
                    property.setValue(forceInt(value) == Qt.Checked)
                    self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
                    self.getDefaultEvaluation(propertyType, property, index)
                    if propertyType.whatDepends:
                        self.updateDependedProperties(propertyType.whatDepends)
                    return True
            if column == self.ciIsAssigned:
                property.setAssigned(forceInt(value) == Qt.Checked)
                self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
#                actionType = self.action.getType()
#                if actionType.amountEvaluation == CActionType.actionAssignedProps:
#                    self.updateAmountAsAssignedPropertyCount()
                return True
        return False


    def updateDependedProperties(self, vars):
        values = {}
        propertiesByVar = self.action.getPropertiesByVar()
        for var, property in propertiesByVar.iteritems():
            values[var] = property.getValue()

        for var in vars:
            property = propertiesByVar[var]
            propertyType = property.type()
            val = propertyType.evalValue(values)
            values[var] = val
            property.setValue(val)

            row = self.propertyTypeList.index(propertyType)
            index = self.index(row, self.ciValue)
            self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)


    def emitDataChanged(self):
        leftTop = self.index(0, 0)
        rightBottom = self.index(self.rowCount(), self.columnCount())
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), leftTop, rightBottom)


#    def updateAmountAsAssignedPropertyCount(self):
#        result = self.action.getAssignedPropertiesCount()
#        self.emit(SIGNAL('actionAmountChanged(double)'), float(result))


    def setLaboratoryCalculatorData(self, data):
        propertyTypeIdList = [propType.id for propType in self.propertyTypeList]
        for sValuePair in data.split(';'):
            sValuePair = trim(sValuePair).strip('()').split(',')
            propertyTypeId, value = forceInt(sValuePair[0]), sValuePair[1]
            if propertyTypeId in propertyTypeIdList:
                propertyTypeIndex = propertyTypeIdList.index(propertyTypeId)
                propertyType = self.propertyTypeList[propertyTypeIndex]
                property = self.action.getPropertyById(propertyTypeId)
                property.setValue(propertyType.convertQVariantToPyValue(QVariant(value)))
        begIndex = self.index(0, 0)
        endIndex = self.index(self.rowCount()-1, self.columnCount()-1)
        self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), begIndex, endIndex)


    def setPlannedEndDateByJobTicket(self, jobTicketId):
        db = QtGui.qApp.db
        date = forceDate(db.translate('Job_Ticket', 'id', jobTicketId, 'datetime'))
        jobId = forceRef(db.translate('Job_Ticket', 'id', jobTicketId, 'master_id'))
        jobTypeId = forceRef(db.translate('Job', 'id', jobId, 'jobType_id'))
        ticketDuration = forceInt(db.translate('rbJobType', 'id', jobTypeId, 'ticketDuration'))
        self.emit(SIGNAL('setCurrentActionPlannedEndDate(QDate)'), date.addDays(ticketDuration))


    def plannedEndDateByJobTicket(self):
        actionType = self.action.getType()
        return actionType.defaultPlannedEndDate == CActionType.dpedJobTicketDate



# ################################################

class CActionPropertyBaseDelegate(QtGui.QItemDelegate):
    def __init__(self, lineHeight, parent=None):
        QtGui.QItemDelegate.__init__(self, parent)
        self.lineHeight = lineHeight


    def eventFilter(self, editor, event):
        if event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter) and isinstance(editor, QtGui.QTextEdit):
                return False
        return QtGui.QItemDelegate.eventFilter(self, editor, event)
#            if event.key() == Qt.Key_Escape: # and isinstance(editor, QtGui.QTextEdit):
#                emit closeEditor(editor, QAbstractItemDelegate::RevertModelCache)
#                print ""
#                return True
#           return False


    def commit(self):
        editor = self.sender()
        self.emit(SIGNAL('commitData(QWidget *)'), editor)


    def commitAndCloseEditor(self):
        editor = self.sender()
        self.emit(SIGNAL('commitData(QWidget *)'), editor)
        self.emit(SIGNAL('closeEditor(QWidget *,QAbstractItemDelegate::EndEditHint)'), editor, QtGui.QAbstractItemDelegate.NoHint)



class CActionPropertyDelegate(CActionPropertyBaseDelegate):
    __pyqtSignals__ = ('editorCreated(QWidget *)')

    def __init__(self, lineHeight, parent):
        CActionPropertyBaseDelegate.__init__(self, lineHeight, parent)


    def paint(self, painter, option, index):
        model = index.model()
        row = index.row()
        propertyType = model.getPropertyType(row)
        if propertyType.isImage():
            if option.state & QtGui.QStyle.State_Selected:
                painter.fillRect(option.rect, option.palette.highlight())
            image = model.getProperty(row).getImage()
            if image:
                painter.save()
                iconMaxSize = option.rect.size()
                style = QtGui.qApp.style()
                xOffset = style.pixelMetric(QtGui.QStyle.PM_FocusFrameHMargin)+style.pixelMetric(QtGui.QStyle.PM_DefaultFrameWidth)
                yOffset = style.pixelMetric(QtGui.QStyle.PM_FocusFrameVMargin)+style.pixelMetric(QtGui.QStyle.PM_DefaultFrameWidth)
                iconMaxSize -= QSize( xOffset*2,  yOffset*2 )
                if image.height() > iconMaxSize.height() or image.width() > iconMaxSize.width():
                    image = image.scaled(iconMaxSize.width(), iconMaxSize.height(), Qt.KeepAspectRatio)
#                iconRect = option.rect.adjusted(xOffset, yOffset, -xOffset, -yOffset)
                painter.translate(option.rect.x(), option.rect.y())
                painter.drawImage((option.rect.width()-image.width())//2,
                                  (option.rect.height()-image.height())//2,
                                  image)
                painter.restore()
                return
        if propertyType.valueType.name == 'JSON':
            json_data = forceString(index.data(Qt.DisplayRole))
            if json_data != u'':
                data = json.loads(json_data)
                if data:
                    html_table = u"<table border='1'>"
                    html_table += u"<tr>"
                    for header in data[0].keys():
                        html_table += u"<th style='padding: 10px; font-size: 14px;'>{}</th>".format(header)
                    html_table += u"</tr>"
                    
                    for item in data:
                        html_table += u"<tr>"
                        for value in item.values():
                            html_table += u"<td style='padding: 10px; font-size: 12px;'>{}</td>".format(value)
                        html_table += u"</tr>"

                    html_table += u"</table>"
                    document = QtGui.QTextDocument()
                    document.setHtml(html_table)
                    context = QtGui.QAbstractTextDocumentLayout.PaintContext()
                    context.palette = option.palette
                    if option.state & QtGui.QStyle.State_Selected:
                        context.palette.setColor(QtGui.QPalette.Text, Qt.white)
                    else:
                        context.palette.setColor(QtGui.QPalette.Text, Qt.black)
                    painter.save()
                    layout = document.documentLayout()
                    painter.setClipRect(option.rect, Qt.IntersectClip)
                    painter.translate(option.rect.x(), option.rect.y())
                    layout.draw(painter, context)
                    painter.restore()
        elif propertyType.isHtml():
            if option.state & QtGui.QStyle.State_Selected:
                painter.fillRect(option.rect, option.palette.highlight())
            painter.setBrush(QtGui.QColor(Qt.black))
            document = QtGui.QTextDocument()
            document.setDefaultFont(option.font)
            
            textOption = QtGui.QTextOption(document.defaultTextOption())
            textOption.setWrapMode(QtGui.QTextOption.WrapAtWordBoundaryOrAnywhere)
            document.setDefaultTextOption(textOption)
            document.setHtml(index.data(Qt.DisplayRole).toString())
            document.setTextWidth(option.rect.width())
            context = QtGui.QAbstractTextDocumentLayout.PaintContext()
            context.palette = option.palette
            #if option.state & QtGui.QStyle.State_Selected:
            #    context.palette.setColor(QtGui.QPalette.Text,
            #                            option.palette.color(QtGui.QPalette.Active, QtGui.QPalette.HighlightedText))
            #else:
            #    context.palette.setColor(QtGui.QPalette.Text, Qt.black)
            painter.save()
            layout = document.documentLayout()
            painter.setClipRect(option.rect, Qt.IntersectClip)
            painter.translate(option.rect.x(), option.rect.y())
            layout.draw(painter, context)
            painter.restore()
        
        else:
            CActionPropertyBaseDelegate.paint(self, painter, option, index)


    def drawDisplay(self, painter, option, rect, text):
        if option.state & QtGui.QStyle.State_Enabled:
            if option.state & QtGui.QStyle.State_Active:
                cg = QtGui.QPalette.Normal
            else:
                cg = QtGui.QPalette.Inactive
        else:
            cg = QtGui.QPalette.Disabled

        if  option.state & QtGui.QStyle.State_Selected:
            painter.fillRect(rect, option.palette.brush(cg, QtGui.QPalette.Highlight))
            painter.setPen(option.palette.color(cg, QtGui.QPalette.HighlightedText))
        else:
            painter.setPen(option.palette.color(cg, QtGui.QPalette.Text))

        if text.isEmpty():
            return

        if (option.state & QtGui.QStyle.State_Editing):
            painter.save()
            painter.setPen(option.palette.color(cg, QtGui.QPalette.Text))
            painter.drawRect(rect.adjusted(0, 0, -1, -1))
            painter.restore()
#        widget = option.widget
        widget = None
        style = widget.style() if widget else QtGui.qApp.style()
        textMargin = style.pixelMetric(QtGui.QStyle.PM_FocusFrameHMargin, None, widget) + 1
        textRect = rect.adjusted(textMargin, 0, -textMargin, 0) # remove width padding
        textOption = QtGui.QTextOption()
        textOption.setWrapMode(textOption.WrapAtWordBoundaryOrAnywhere)
        textOption.setTextDirection(option.direction)
        textOption.setAlignment(QtGui.QStyle.visualAlignment(option.direction, option.displayAlignment))
        painter.save()
        try:
            painter.setFont(option.font)
            painter.drawText(QRectF(textRect), text, textOption)
            boundRect = painter.boundingRect(QRectF(textRect), text, textOption)
            if boundRect.height()>textRect.height():
                painter.setBrush(option.palette.color(cg, QtGui.QPalette.Button))
                x = rect.right()-1
                y = rect.bottom()-1
                h = w = painter.fontMetrics().averageCharWidth()
                painter.drawPolygon(QPointF(x-w*2, y-h),
                                    QPointF(x-w,   y),
                                    QPointF(x,     y-h)
                                   )
        finally:
            painter.restore()


    def createEditor(self, parent, option, index):
        model = index.model()
        row = index.row()
        propertyType = model.getPropertyType(row)
        isReadOnly = False
        if propertyType.isUrl():
            isReadOnly = self.checkIsUrlReadOnly(row, model)
        editor = propertyType.createEditor(model.action, parent, model.clientId, model.eventTypeId, isReadOnly)
        editor.setStatusTip(forceString(model.data(index, Qt.StatusTipRole)))
        self.connect(editor, SIGNAL('commit()'), self.commit)
        self.connect(editor, SIGNAL('editingFinished()'), self.commitAndCloseEditor)
        self.emit(SIGNAL('editorCreated(QWidget *)'), editor)
        return editor


    def checkIsUrlReadOnly(self, row, model):
        if not model.action._locked:
            propertyType = model.getPropertyType(row)
            if propertyType.canChangeOnlyOwner == 0:
                return False
            elif propertyType.canChangeOnlyOwner == 1:
                setPersonId = forceRef(model.action.getRecord().value('setPerson_id'))
                return setPersonId != QtGui.qApp.userId
            elif propertyType.canChangeOnlyOwner == 2:
                person_id = forceRef(model.action.getRecord().value('person_id'))
                return person_id != QtGui.qApp.userId
        else:
            return True
        return True


    def setEditorData(self, editor, index):
        model = index.model()
        value = model.data(index, Qt.EditRole)
        editor.setValue(value)
        if hasattr(editor, 'moveCursor'):
            editor.moveCursor(QtGui.QTextCursor.End)


    def setModelData(self, editor, model, index):
        model = index.model()
        if isinstance(editor, CStringActionPropertyValueType.CPlainPropEditor):
            editor.on_CloseValidate()
        value = editor.value()
        if type(value) == unicode:
            value = value.replace('\0', '')
        model.setData(index, toVariant(value))
        row = index.row()
        propertyType = model.getPropertyType(row)
        if propertyType.isJobTicketValueType():
            if model.plannedEndDateByJobTicket():
                model.setPlannedEndDateByJobTicket(value)
        if propertyType.valueType.expandingHeight:
            self.emit(SIGNAL('sizeHintChanged(const QModelIndex &)'), index)


    def sizeHint(self, option, index):
        model = index.model()
        col = CActionPropertiesTableModel.ciValue
        row = index.row()
        propertyType = model.getPropertyType(row)
        property = model.action.getPropertyById(propertyType.id)
        preferredHeightUnit, preferredHeight = property.getPreferredHeight()
        # if preferredHeightUnit == 1 and propertyType.typeName in (u'Html', u'Constructor'):
        if preferredHeightUnit == 1:
                preferredHeight = preferredHeight * self.lineHeight
        preferredHeight = math.ceil(preferredHeight * propertyType.getHeightFactor())
        if propertyType.valueType.expandingHeight:
            value = model.data(index, Qt.DisplayRole)
            tableView = self.parent()
            rect = QRect(0, 0, tableView.horizontalHeader().sectionSize(col) - 8, 5000)
            rect = tableView.fontMetrics().boundingRect(rect, Qt.TextWordWrap, forceString(value))
            autoHeight = rect.height() + 12
            if autoHeight > preferredHeight:
                preferredHeight = autoHeight
        return QSize(10, preferredHeight)


# virtual void updateEditorGeometry ( QWidget * editor, const QStyleOptionViewItem & option, const QModelIndex & index ) const

# ################################################

class CActionPropertyEvaluationDelegate(CActionPropertyBaseDelegate):
    def __init__(self, lineHeight, parent=None):
        CActionPropertyBaseDelegate.__init__(self, lineHeight, parent)


    def createEditor(self, parent, option, index):
#        model = index.model()
#        row = index.row()
#        propertyType = model.getPropertyType(row)
        editor = QtGui.QComboBox(parent)
        editor.addItem('', QVariant())
        editor.addItem(u'-2', QVariant(-2))
        editor.addItem(u'-1', QVariant(-1))
        editor.addItem(u'0', QVariant(0))
        editor.addItem(u'+1', QVariant(+1))
        editor.addItem(u'+2', QVariant(+2))
        return editor


    def setEditorData(self, editor, index):
        model = index.model()
        value = model.data(index, Qt.EditRole)
        index = 0 if value.isNull() else forceInt(value)+3
        editor.setCurrentIndex(index)


    def setModelData(self, editor, model, index):
        model = index.model()
        model.setData(index, editor.itemData(editor.currentIndex()))


    def sizeHint(self, option, index):
        return QSize(10, self.lineHeight)
# ################################################

class CActionPropertyCommentDelegate(CActionPropertyDelegate):
    def __init__(self, lineHeight, parent=None):
        CActionPropertyDelegate.__init__(self, lineHeight, parent)

    def createEditor(self, parent, option, index):
        editor = QtGui.QTextEdit(parent)
        editor.setLineWrapMode(QtGui.QTextEdit.WidgetWidth)
        editor.setWordWrapMode(QtGui.QTextOption.WrapAtWordBoundaryOrAnywhere)
        return editor

    def setEditorData(self, editor, index):
        model = index.model()
        value = model.data(index, Qt.EditRole)
        editor.setPlainText(forceStringEx(value))
        editor.moveCursor(QtGui.QTextCursor.End)

    def setModelData(self, editor, model, index):
        model = index.model()
        model.setData(index, QVariant(editor.toPlainText()))

    def alignment(self):
        return QVariant(Qt.AlignLeft + Qt.AlignTop)

    #def insertFromMimeData(self, mimeData):
    #    if (mimeData.hasText()):
    #        text = mimeData.text()
    #        self.insertPlainText(text)
    #    else:
    #        QtGui.QTextEdit.insertFromMimeData(self, mimeData)

# ################################################


class CActionPropertiestableVerticalHeaderView(QtGui.QHeaderView):
    def __init__(self, orientation, parent=None):
        QtGui.QHeaderView.__init__(self, orientation, parent)


    def sectionSizeFromContents(self, logicalIndex):
        model = self.model()
        if model:
            orientation = self.orientation()
            opt = QtGui.QStyleOptionHeader()
            self.initStyleOption(opt)
            var = model.headerData(logicalIndex, orientation, Qt.FontRole)
            if var and var.isValid() and var.type() == QVariant.Font:
                fnt = var.toPyObject()
            else:
                fnt = self.font()
#           fnt.setBold(True)
            opt.fontMetrics = QtGui.QFontMetrics(fnt)
            sizeText = QSize(4,4)
            opt.text = model.headerData(logicalIndex, orientation, Qt.DisplayRole).toString()
            sizeText = self.style().sizeFromContents(QtGui.QStyle.CT_HeaderSection, opt, sizeText, self)
            sizeFiller = QSize(4,4)
            opt.text = QString('x'*CActionPropertiesTableView.titleWidth)
            sizeFiller = self.style().sizeFromContents(QtGui.QStyle.CT_HeaderSection, opt, sizeFiller, self)
            return QSize(max(sizeText.width(), sizeFiller.width()),
                         max(sizeText.height(), sizeFiller.height())
                        )
        else:
            return QtGui.QHeaderView.sectionSizeFromContents(self, logicalIndex)


class CActionPropertiesTableView(QtGui.QTableView, CPreferencesMixin):
    titleWidth = 20

    def __init__(self, parent):
        QtGui.QTableView.__init__(self, parent)
        self.autoResizeColumns = forceBool(QtGui.qApp.preferences.appPrefs.get('autoResizeColumns', QVariant()))
        self._verticalHeader = CActionPropertiestableVerticalHeaderView(Qt.Vertical, self)
        self.setVerticalHeader(self._verticalHeader)
        h = self.fontMetrics().height()
        self.verticalHeader().setDefaultSectionSize(3*h/2)
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.setAlternatingRowColors(True)
        self.horizontalHeader().setStretchLastSection(True)
        self.valueDelegate = CActionPropertyDelegate(self.fontMetrics().height(), self)
        self.setItemDelegateForColumn(CActionPropertiesTableModel.ciValue, self.valueDelegate)
        self.evaluationDelegate = CActionPropertyEvaluationDelegate(self.fontMetrics().height(), self)
        self.setItemDelegateForColumn(CActionPropertiesTableModel.ciEvaluation, self.evaluationDelegate)
        self.commentDelegate = CActionPropertyCommentDelegate(self.fontMetrics().height(), self)
        self.setItemDelegateForColumn(CActionPropertiesTableModel.ciComment, self.commentDelegate)
        self.setEditTriggers(QtGui.QAbstractItemView.AllEditTriggers)
        self.connect(self.horizontalHeader(), SIGNAL('sectionResized(int,int,int)'), self.onHeaderSectionResized)
        self.connect(self.valueDelegate, SIGNAL('sizeHintChanged(const QModelIndex &)'), self.valueDelegateSizeHintChanged)
        self._popupMenu = None
        self._actCopy = None
        self._actCopyCell = None
        self.preferencesLocal = {}
        self.setVerticalScrollMode(QtGui.QAbstractItemView.ScrollPerPixel)
        self._inAutoResize = False #защита от рекурсии
        self._fitPanding = False # уже запланировано или нет
        if self.autoResizeColumns:
            # self._oldHPolicy = self.horizontalScrollBarPolicy()
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)


    def event(self, e):
        if self.autoResizeColumns:
            if e.type() in (QEvent.Show, QEvent.Resize):
                self.requestAutoFit('event_%d' % int(e.type()))
        return QtGui.QTableView.event(self, e)


    def setModel(self, model):
        QtGui.QTableView.setModel(self, model)
        if self.autoResizeColumns and model is not None:
            try:
                model.modelReset.connect(lambda *a: self.requestAutoFit('modelReset'))
                model.layoutChanged.connect(lambda *a: self.requestAutoFit('layoutChanged'))
                model.columnsInserted.connect(lambda *a: self.requestAutoFit('columnsInserted'))
                model.columnsRemoved.connect(lambda *a: self.requestAutoFit('columnsRemoved'))
            except Exception:
                pass
        self.requestAutoFit('setModel')

    def requestAutoFit(self, reason=''):
        if not self.autoResizeColumns:
            return
        if self._fitPanding:
            return
        self._fitPanding = True

        def _run():
            self._fitPanding = False
            if not self.isVisible():
                return

            self._inAutoResize = True

            try:
                self.resizeColumnsToView()
            finally:
                self._inAutoResize = False

            self.updateGeometries()
            self.viewport().update()

        QTimer.singleShot(0, _run)


    def onHeaderSectionResized(self, logicalIndex, oldSize, newSize):
        self.resizeRowsToContents()
        if not self.autoResizeColumns:
            return
        if self._inAutoResize:
            return
        self.requestAutoFit('userResize')


    def resizeColumnsToView(self):
        """Подгоняет все столбцы под размер виджета."""
        header = self.horizontalHeader()
        viewportWidth = max(0, self.viewport().width())
        # if not self.verticalScrollBar().isVisible():
        #     viewportWidth += self.verticalScrollBar().width()

        visibleCols = [i for i in range(header.count())
                        if not self.isColumnHidden(i)]
        if not visibleCols:
            return

        totalWidth = header.length()
        minSize = header.minimumSectionSize()
        header.blockSignals(True)
        try:
            if totalWidth > viewportWidth:
                excess = totalWidth - viewportWidth
                for colIndex in reversed(visibleCols):
                    if excess <= 0:
                        break
                    currentSize = header.sectionSize(colIndex)
                    if currentSize > minSize:
                        reduction = min(excess, currentSize - minSize)
                        newSize = currentSize - reduction
                        header.resizeSection(colIndex, newSize)
                        excess -= reduction
        finally:
            header.blockSignals(False)


    def mousePressEvent(self, event):
        index = self.indexAt(event.pos())
        if index.isValid() and index.column() == CActionPropertiesTableModel.ciIsAssigned:  # tt3349 Решил сделать так, чтобы не создавать еще один делегат
            model = self.model()
            propertyType = model.getPropertyType(index.row())
            if propertyType.isAssignable:
                opt = QtGui.QStyleOptionViewItem()
                opt.initFrom(self)
                opt.rect = self.visualRect(index)
                opt.state = QtGui.QStyle.State_Enabled
                if self.selectionModel() and self.selectionModel().isSelected(index):
                    opt.state |= QtGui.QStyle.State_Selected
                indicator_rect = self.style().subElementRect(QtGui.QStyle.SE_ItemViewItemCheckIndicator, opt, self)
                if indicator_rect.contains(event.pos()):
                    return QtGui.QTableView.mousePressEvent(self, event)
                current_state = model.data(index, Qt.CheckStateRole).toInt()[0]
                new_state = Qt.Unchecked if current_state == Qt.Checked else Qt.Checked
                model.setData(index, new_state, Qt.CheckStateRole)
                self.selectRow(index.row())
                return
        super(CActionPropertiesTableView, self).mousePressEvent(event)


    def valueDelegateSizeHintChanged(self, index):
        self.resizeRowToContents(index.row())


    @pyqtSignature('int, int')                                          # см. примечание 1
    def rowCountChanged(self, oldCount, newCount):                      # см. примечание 1
        self.verticalHeader().setUpdatesEnabled(True)                   # см. примечание 1


    def sizeHintForRow(self, row):
        model = self.model()
        if model:
            index = model.index(row, CActionPropertiesTableModel.ciValue)
            return max(self.valueDelegate.sizeHint(None, index).height(),
                       self.evaluationDelegate.sizeHint(None, index).height()
                      )
        else:
            return -1
    

    def sizeHintForColumn(self, column):
        if CActionPropertiesTableModel.ciIsAssigned == column:
            model = self.model()
            headerName = self.horizontalHeader().model().column[column]
            headerLen = len(headerName)-1
            headerSize = 20
            for i in range(headerLen):
                headerSize += self.fontMetrics().width(QString(headerName).at(i))
            colSizeList = [headerSize]
            if model:
                propertyTypeList = self.model().propertyTypeList
                for row, propertyType in enumerate(propertyTypeList):
                    colSizeList.append(self.columnWidth(column))
                return max(tuple(colSizeList))
            return -1
        else:
            return QtGui.QTableView.sizeHintForColumn(self, column)


    def createPopupMenu(self, actions=[]):
        self._popupMenu = QtGui.QMenu(self)
        self._popupMenu.setObjectName('popupMenu')
        for action in actions:
            if isinstance(action, QtGui.QAction):
                self._popupMenu.addAction(action)
            elif action == '-':
                self._popupMenu.addSeparator()
        self.connect(self._popupMenu, SIGNAL('aboutToShow()'), self.popupMenuAboutToShow)
        return self._popupMenu


    def popupMenu(self):
        if self._popupMenu is None:
            self.createPopupMenu()
        return self._popupMenu


    def addPopupSeparator(self):
        self.popupMenu().addSeparator()


    def addPopupAction(self, action):
        self.popupMenu().addAction(action)


    def addPopupCopyCell(self):
        self._actCopyCell = QtGui.QAction(u'Копировать', self)
        self._actCopyCell.setObjectName('actCopyCell')
        self.connect(self._actCopyCell, SIGNAL('triggered()'), self.copyCurrentCell)
        self.addPopupAction(self._actCopyCell)


    def focusInEvent(self, event):
        QtGui.QTableView.focusInEvent(self, event)
        self.updateStatusTip(self.currentIndex())


    def focusOutEvent(self, event):
        self.updateStatusTip(None)
        QtGui.QTableView.focusOutEvent(self, event)
    

    def wheelEvent(self, event):
        numPixelsPerStep = 20
        numSteps = event.delta() / 120.0
        numPixelsToScroll = -numSteps * numPixelsPerStep
        numPixelsToScroll = int(math.ceil(numPixelsToScroll) if numPixelsToScroll > 0 else math.floor(numPixelsToScroll))
        if event.orientation() == Qt.Vertical:
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + numPixelsToScroll)
        else:
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + numPixelsToScroll)
        event.accept()


    def updateStatusTip(self, index):
        tip = forceString(index.data(Qt.StatusTipRole)) if index else ''
        event = QtGui.QStatusTipEvent(tip)
        self.setStatusTip(tip)
        QtGui.qApp.sendEvent(self.parent(), event)

#    def _keyPressEvent_(self, event):
#        key = event.key()
#        if key == Qt.Key_Escape:
#            event.ignore()
#        elif key == Qt.Key_Return or key == Qt.Key_Enter:
#            event.ignore()
#        elif event.key() == Qt.Key_Tab:
#            index = self.currentIndex()
#            model = self.model()
#            if not index.isValid() or index.row() == model.rowCount()-1:
#                self.parent().focusNextChild()
#            else:
#                index = model.index(index.row()+1, 0)
#                QtGui.QTableView.setCurrentIndex(self, index)
##                self.selectionModel().setCurrentIndex(index, QtGui.QItemSelectionModel.ClearAndSelect)
#            event.accept()
#        elif event.key() == Qt.Key_Backtab:
#            index = self.currentIndex()
#            model = self.model()
#            if not index.isValid() or index.row() == 0:
#                self.parent().focusPreviousChild()
#            else:
#                index = model.index(index.row()-1, 0)
#                QtGui.QTableView.setCurrentIndex(self, index)
##                self.selectionModel().setCurrentIndex(index, QtGui.QItemSelectionModel.ClearAndSelect)
#            event.accept()
#        else:
#            QtGui.QTableView.keyPressEvent(self, event)


    def moveCursor(self, cursorAction, modifiers):
        if cursorAction in (QtGui.QAbstractItemView.MoveNext, QtGui.QAbstractItemView.MoveRight):
            return QtGui.QTableView.moveCursor(self, QtGui.QAbstractItemView.MoveDown, modifiers)
        elif cursorAction in (QtGui.QAbstractItemView.MovePrevious, QtGui.QAbstractItemView.MoveLeft):
            return QtGui.QTableView.moveCursor(self, QtGui.QAbstractItemView.MoveUp, modifiers)
        else:
            return QtGui.QTableView.moveCursor(self, QtGui.QAbstractItemView.CursorAction(cursorAction), modifiers)


    def contextMenuEvent(self, event):
        if self._popupMenu:
            self._popupMenu.exec_(event.globalPos())
            event.accept()
        else:
            event.ignore()


    def popupMenuAboutToShow(self):
        currentIndex = self.currentIndex()
        curentIndexIsValid = currentIndex.isValid()
        if self._actCopyCell:
            self._actCopyCell.setEnabled(curentIndexIsValid)


    def copyCurrentCell(self):
        index = self.currentIndex()
        if index.isValid():
            carrier = QMimeData()
            dataAsText = self.model().data(index, Qt.DisplayRole)
            carrier.setText(dataAsText.toString() if dataAsText else '' )
            QtGui.qApp.clipboard().setMimeData(carrier)


    def showHistory(self):
        index = self.currentIndex()
        model = self.model()
        row = index.row()
        if 0<=row<model.rowCount():
            actionProperty = model.getProperty(row)
            dlg = CPropertyHistoryDialog(model.clientId, [(actionProperty, True, True)], self)
            dlg.exec_()


    def showHistoryEx(self):
        index = self.currentIndex()
        model = self.model()
        row = index.row()
        if 0<=row<model.rowCount():
            dlgChooser = CActionPropertyChooser(self, self.model().propertyTypeList)
            if dlgChooser.exec_():
                propertyTypeList = dlgChooser.getSelectedPropertyTypeList()
                if propertyTypeList:
                    dlg = CPropertyHistoryDialog(model.clientId, [(model.action.getProperty(propertyType.name), showUnit, showNorm) for propertyType, showUnit, showNorm in propertyTypeList], self)
                    dlg.exec_()


    def colKey(self, col):
        return unicode('width '+forceString(col.title()))


    def loadPreferencesLoc(self, preferences, actionTypeId):
        width = 0
        model = self.model()
        nullSizeDetected = False
        if model and actionTypeId:
            for i in xrange(model.columnCount()):
                colWidth = forceInt(getPref(preferences, 'atid_%d_col_%d' % (actionTypeId, i), None))
                if colWidth and colWidth > width:
                    self.setColumnWidth(i, colWidth)
                else:
                    if not self.isColumnHidden(i):
                        nullSizeDetected = True
        if nullSizeDetected:
            self.resizeColumnsToContents()
            colCount = model.columnCount()
            for i in range(0, colCount):
                width += self.columnWidth(i)
            self.setColumnWidth(1, width * 2)  # значение
            for i in range(colCount - 1):
                if i != 1:
                    self.setColumnWidth(i, width / 2)


    def savePreferencesLoc(self, actionTypeId):
        model = self.model()
        if model and actionTypeId:
            for i in xrange(model.columnCount()):
                width = self.columnWidth(i)
                setPref(self.preferencesLocal, 'atid_%d_col_%d' % (actionTypeId, i), QVariant(width))
        return self.preferencesLocal


    def loadPreferences(self, preferences):
        self.preferencesLocal = preferences
        model = self.model()
        if model and model.action and model.action.actionType().id:
            actionTypeId = model.action.actionType().id
            self.loadPreferencesLoc(self.preferencesLocal, actionTypeId)


    def savePreferences(self):
        model = self.model()
        if model and model.action and model.action.actionType().id:
            actionTypeId = model.action.actionType().id
            self.savePreferencesLoc(actionTypeId)
        return self.preferencesLocal
    

    def lastVisibleCol(self):
        cols = (
            CActionPropertiesTableModel.ciComment,
            CActionPropertiesTableModel.ciEvaluation,
            CActionPropertiesTableModel.ciNorm,
            CActionPropertiesTableModel.ciUnit,
            CActionPropertiesTableModel.ciValue
        )
        for col in cols:
            if not self.isColumnHidden(col):
                return col
        return None


    def resizeLastColumn(self):
        lastVisibleCol = self.lastVisibleCol()
        if not lastVisibleCol:
            return
        # последняя колонка расширится обратно до конца таблицы, уменьшаем ее до минимальной ширины
        self.setColumnWidth(lastVisibleCol, 100)
        
