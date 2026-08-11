# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2023 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QSize, QVariant, pyqtSignature, SIGNAL

from library.angel import CAngelDialog, getMarksSettingsForImageMapActionPropertyType
from library.Utils import forceInt, forceString
from library.PrintInfo import CImageInfo

from ActionPropertyValueType import CActionPropertyValueType


class CImageMapActionPropertyValueType(CActionPropertyValueType):
    name = 'ImageMap'
    variantType = QVariant.String
    preferredHeight = 64
    preferredHeightUnit = 0
    domain = None
    isHtml = True
    isImage = True

    class CPropEditor(QtGui.QPushButton):
        __pyqtSignals__ = ('commit()',
                           )

        def __init__(self, action, domain, parent, clientId, eventTypeId):
            QtGui.QPushButton.__init__(self, parent)
            self.setFocusPolicy(Qt.StrongFocus)
            actionType = action.getType()
            self.domain = domain
            self.propCode = u'<code>%s</code>' % domain
            tableView = self.parent().parent()
            row = tableView.currentIndex().row()
            valueAction = tableView.model().getProperty(row).getValue()
            _valueAction = valueAction.split('</code>') if valueAction else ''
            self.propMark = _valueAction[1] if len(_valueAction) > 1 else ''
            self._value = QVariant(self.propCode + self.propMark)
            self.markSize = 1
            self.actionTypeName = actionType.name
            self.openEditorAbility = True
            self.connect(self, SIGNAL('clicked()'), self.runEditor)

        def setValue(self, value):
            if not value:
                self._value = QVariant(self.propCode + self.propMark)
            self.setIconByValue()

        def setIconByValue(self):
            preparedImage = CImageMapActionPropertyValueType(self.domain)
            preparedImage.imgValue = self.getValueFromDomain()
            image = preparedImage._getUpdatedImage(self._value)
            iconMaxSize = self.size()
            style = self.style()
            iconMaxSize -= QSize(style.pixelMetric(QtGui.QStyle.PM_FocusFrameHMargin) * 2
                                 + style.pixelMetric(QtGui.QStyle.PM_DefaultFrameWidth) * 2,
                                 style.pixelMetric(QtGui.QStyle.PM_FocusFrameVMargin) * 2
                                 + style.pixelMetric(QtGui.QStyle.PM_DefaultFrameWidth) * 2,
                                 )
            if image:
                if image.height() > iconMaxSize.height() or image.width() > iconMaxSize.width():
                    preview = image.scaled(iconMaxSize.width(), iconMaxSize.height(), Qt.KeepAspectRatio)
                else:
                    preview = image
            else:
                preview = QtGui.QImage(self.preferredHeight, self.preferredHeight)
            pixmap = QtGui.QPixmap.fromImage(preview)
            self.setIcon(QtGui.QIcon(pixmap))
            self.setIconSize(preview.size())

        def getValueFromDomain(self):
            db = QtGui.qApp.db
            where = 'code=\'%s\'' % self.domain
            record = db.getRecordEx('rbImageMap', '*', where)
            try:
                ba = record.value('image').toByteArray()
                image = QtGui.QImage().fromData(ba)
                image = convertImageToPreferredFormat(image)
                self.markSize = forceInt(record.value('markSize'))
                self.openEditorAbility = True
                return image
            except Exception:
                msg = QtGui.QMessageBox()
                msg.addButton('Ok', msg.AcceptRole)
                txt = u'В свойствах действия %s указан неверный код' % self.actionTypeName
                msg.setText(txt)
                msg.exec_()
                self.openEditorAbility = False
                return None

        @pyqtSignature('')
        def runEditor(self):
            if self.openEditorAbility:
                dlg = CAngelDialog(self._value, self)
                dlg.setMarkSize(self.markSize)
                if dlg.exec_():
                    try:
                        self._value = self.propCode + dlg.marksData
                        self.propMark = dlg.marksData
                    except:
                        self._value = self.propCode
                    finally:
                        self.setValue(self.propCode + dlg.marksData if dlg.marksData else self.propCode)
                    self.emit(SIGNAL('commit'))
                dlg.deleteLater()

        def value(self):
            return self._value

    def __init__(self, domain=None):
        CActionPropertyValueType.__init__(self, domain)

        value = self.getValueFromDomain()
        if value:
            self.imgValue = self.convertDBImageToPyValue(value)
        else:
            self.imgValue = QtGui.QImage()

    def getEditorClass(self):
        return self.CPropEditor

    def getValueFromDomain(self):
        db = QtGui.qApp.db
        where = 'code=\'%s\'' % self.domain
        record = db.getRecordEx('rbImageMap', 'image', where)
        try:
            ba = record.value('image')
            return ba
        except Exception:
            msg = QtGui.QMessageBox()
            msg.addButton('Ok', msg.AcceptRole)
            msg.setText(u'В действиях типа \'ImageMap\' указаны неверные коды')
            msg.exec_()
            return None

    @classmethod
    def getTableName(cls):
        return cls.tableNamePrefix + 'ImageMap'

    def convertDBImageToPyValue(self, value):
        if value.type() == QVariant.ByteArray:
            byteArray = value.toByteArray()
            if byteArray:
                image = QtGui.QImage()
                if image.loadFromData(byteArray):
                    return convertImageToPreferredFormat(image)
                else:
                    return None
        return None

    @staticmethod
    def convertDBValueToPyValue(value):
        if type(value) == QVariant:
            if value.type() == QVariant.String:
                str = forceString(value)
                return str
        elif isinstance(value, basestring):
            return value
        return None

    @staticmethod
    def convertQVariantToPyValue(value):
        if type(value) == QVariant:
            if value.type() == QVariant.String:
                str = forceString(value)
                return str
        elif isinstance(value, basestring):
            return value
        return None

    @staticmethod
    def convertPyValueToDBValue(value):
        if value:
            return QVariant(value)
        return None

    def _getUpdatedImage(self, marksData):
        if not marksData:
            return self.imgValue

        resultImage = QtGui.QImage(self.imgValue)
        painter = QtGui.QPainter(resultImage)
        marksSettings = getMarksSettingsForImageMapActionPropertyType(marksData)

        for itemTypeName, settingsList in marksSettings.items():
            for itemSettings in settingsList:
                if itemTypeName == 'CGraphicsEllipseItem':
                    point, rect, pen = itemSettings
                    painter.setPen(pen)
                    brush = QtGui.QBrush(pen)
                    painter.setBrush(brush)
                    painter.drawEllipse(point.x(), point.y(), rect.width(), rect.height())
                elif itemTypeName == 'CGraphicsRectItem':
                    point, rect, pen = itemSettings
                    painter.setPen(pen)
                    brush = QtGui.QBrush(pen)
                    painter.setBrush(brush)
                    painter.fillRect(point.x(), point.y(), rect.width(), rect.height(), pen)

                elif itemTypeName == 'CGraphicsTextItem':
                    pos, text, colour, size, rotation = itemSettings
                    font = QtGui.QFont()
                    font.setPixelSize(size * 10)
                    brush = QtGui.QBrush(colour)
                    painter.save()
                    painter.setFont(font)
                    painter.setPen(colour)
                    painter.setBrush(brush)
                    painter.translate(pos.x(), pos.y());
                    painter.rotate(rotation)
                    painter.drawText(0, size * 10, text)
                    painter.setFont(QtGui.QFont())
                    painter.restore()
        return resultImage

    def toText(self, v):
        return ''

    def toImage(self, v):
        updatedImage = self._getUpdatedImage(v)
        #        if updatedImage.height() > self.preferredHeight:
        #            return updatedImage.scaledToHeight(self.preferredHeight, Qt.FastTransformation)
        return updatedImage

    def toInfo(self, context, v):
        return CImageInfo(context, self._getUpdatedImage(v))


# #################

def convertImageToPreferredFormat(image):
    format = image.format()
    if format in (image.Format_Mono,
                  image.Format_MonoLSB,
                  image.Format_Indexed8,
                  image.Format_RGB16,
                  image.Format_RGB666,
                  image.Format_RGB555,
                  image.Format_RGB888,
                  image.Format_RGB444,
                  ):
        return image.convertToFormat(image.Format_RGB32)
    if format == image.Format_RGB32:
        return image
    if format == image.Format_ARGB32_Premultiplied:
        return image
    if format in (image.Format_ARGB32,
                  image.Format_ARGB8565_Premultiplied,
                  image.Format_ARGB6666_Premultiplied,
                  image.Format_ARGB8555_Premultiplied,
                  image.Format_ARGB4444_Premultiplied
                  ):
        return image.convertToFormat(image.Format_ARGB32_Premultiplied)
    # fallback
    return image.convertToFormat(image.Format_ARGB32_Premultiplied)
