# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2021 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4.QtCore import QVariant, SIGNAL, Qt, pyqtSignature
from PyQt4 import QtGui, QtSql

from Events.Ui_DiagnosticServiceComboBoxPopup import Ui_DiagnosticServiceComboBoxPopup
from RefBooks.DiagnosticService.Info import CDiagnosticServiceInfo
from library.PrintInfo import CRBInfo
from library.TableModel import CTableModel, CTextCol
from library.Utils import forceRef, forceString, forceStringEx, addDotsEx, getPref, setPref

from ActionPropertyValueType import CActionPropertyValueType
from library.crbcombobox import CRBComboBox


class CDiagnosticServiceActionPropertyValueType(CActionPropertyValueType):
    name = u'Инструментальные диагностические исследования'
    variantType = QVariant.Int
    badDomain = u'Неверное описание области определения значения свойства действия типа "Инструментальные диагностические исследования":\n%(domain)s'
    badKey = u'Недопустимый ключ "%(key)s" в описание области определения значения свойства действия типа "Инструментальные диагностические исследования":\n%(domain)s'
    badValue = u'Недопустимое значение "%(val)s" ключа "%(key)s" в описание области определения значения свойства действия типа "Инструментальные диагностические исследования":\n%(domain)s'

    # class CDiagnosticServiceInfo(CRBInfo):
    #     tableName = 'rbDiagnosticService'

    class CPropEditor(CRBComboBox):
        def __init__(self, action, domain, parent, clientId, eventTypeId):
            CRBComboBox.__init__(self, parent)
            self._tableName = 'rbDiagnosticService'
            self._addNone = True
            self._customFilter = domain
            self.setOrderByName()
            if self._tableName:
                CRBComboBox.setTable(self, self._tableName, self._addNone, self.compileFilter(), self._order)
            self._popup = None

        def _createPopup(self):
            if not self._popup:
                self._popup = CDiagnosticServicePopup(self)
                self.connect(self._popup, SIGNAL('serviceIdSelected(int)'), self.setValue)

        def showPopup(self):
            if not self.isReadOnly():
                self._createPopup()
                self._popup.setFilter(self._customFilter)
                pos = self.rect().bottomLeft()
                pos = self.mapToGlobal(pos)
                size = self._popup.sizeHint()
                screen = QtGui.QApplication.desktop().availableGeometry(pos)
                size.setWidth(screen.width())
                size.setHeight(screen.height()/3)
                pos.setX(max(min(pos.x(), screen.right() - size.width()), screen.left()))
                pos.setY(max(min(pos.y(), screen.bottom() - size.height()), screen.top()))
                self._popup.move(pos)
                self._popup.resize(size)
                self._popup.on_buttonBox_apply()
                self._popup.show()

        def setOrderByCode(self):
            self._order = 'code, name'

        def setOrderByName(self):
            self._order = 'name, code'

        def setFilter(self, _filter):
            if self._customFilter != _filter:
                self._customFilter = _filter
                self.updateFilter()

        def compileFilter(self):
            if not QtGui.qApp.db:
                QtGui.qApp.openDatabase()
            db = QtGui.qApp.db
            cond = []
            if self._customFilter:
                cond.append(self._customFilter)
            return db.joinAnd(cond)

        def updateFilter(self):
            v = self.value()
            CRBComboBox.setTable(self, self._tableName, self._addNone, self.compileFilter(), self._order)
            self.setValue(v)

        def setValue(self, value):
            CRBComboBox.setValue(self, forceRef(value))

    def __init__(self, domain=None):
        CActionPropertyValueType.__init__(self, domain)
        self.rawDomain = domain
        self.domain = self.parseDomain(domain)

    def parseDomain(self, domain):
        codeList = []
        method = []
        for word in domain.split(','):
            if word:
                parts = word.split(':')
                if len(parts) == 1:
                    key, val = u'код', parts[0].strip()
                elif len(parts) == 2:
                    key, val = parts[0].strip(), parts[1].strip()
                else:
                    raise ValueError, self.badDomain % locals()
                keylower = key.lower()
                vallower = val.lower()
                if keylower == u'код':
                    codeList.extend(vallower.split(';'))
                elif keylower == u'метод':
                    method.extend(vallower.split(';'))
                else:
                    raise ValueError, self.badKey % locals()

        db = QtGui.qApp.db
        table = db.table('rbDiagnosticService')
        cond = [table['applicability'].eq(1)]

        if codeList:
            cond.append(table['code'].inlist(codeList))
        if method:
            cond.append(table['method'].inlist(method))
        return db.joinAnd(cond)

    @staticmethod
    def convertDBValueToPyValue(value):
        return forceRef(value)

    convertQVariantToPyValue = convertDBValueToPyValue

    def toText(self, v):
        return forceString(QtGui.qApp.db.translate('rbDiagnosticService', 'id', v, 'CONCAT(code,\' | \',name)'))

    def toInfo(self, context, v):
        return CDiagnosticServiceInfo(context, v)

    def getTableName(self):
        return self.tableNamePrefix + 'Integer'


class CDiagnosticServicePopup(QtGui.QFrame, Ui_DiagnosticServiceComboBoxPopup):
    __pyqtSignals__ = ('serviceIdSelected(int)',)

    def __init__(self, parent=None):
        QtGui.QFrame.__init__(self, parent, Qt.Popup)
        self._parent = parent
        self.setupUi(self)
        self.tableModel = CDiagnosticServiceTableModel(self)
        self.tableSelectionModel = QtGui.QItemSelectionModel(self.tableModel, self)
        self.tableSelectionModel.setObjectName('tableSelectionModel')
        self.tblServices.setModel(self.tableModel)
        self.tblServices.setSelectionModel(self.tableSelectionModel)
        self.tblServices.setSortingEnabled(True)
        self.buttonBox.button(QtGui.QDialogButtonBox.Apply).setDefault(True)
        self.buttonBox.button(QtGui.QDialogButtonBox.Apply).setShortcut(Qt.Key_Return)
        self.connect(self.tblServices.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.sort)
        preferences = getPref(QtGui.qApp.preferences.windowPrefs, 'CDiagnosticServiceExPopup', {})
        self.tblServices.loadPreferences(preferences)
        self._customFilter = None
        self.serviceId = None
        self.tabWidget.removeTab(self.tabWidget.indexOf(self.tabSearch))


    def sort(self, col):
        sortAscending = self.tableModel.headerSortingCol.get(col, False)
        self.tableModel.headerSortingCol = {col: not sortAscending}
        self.on_buttonBox_apply()


    def getActualEmptyRecord(self):
        return self.tableModel.getActualEmptyRecord()

    def getStringValue(self, _id):
        return self.tableModel.getStringValue(_id)

    def addNotSetValue(self):
        self.tableModel.addNotSetValue()

    def setSpecialValues(self, specialValues):
        self.tableModel.setSpecialValues(specialValues)

    def setFilter(self, _filter):
        self._customFilter = _filter

    def mousePressEvent(self, event):
        parent = self.parentWidget()
        if parent is not None:
            opt = QtGui.QStyleOptionComboBox()
            opt.init(parent)
            arrowRect = parent.style().subControlRect(QtGui.QStyle.CC_ComboBox, opt, QtGui.QStyle.SC_ComboBoxArrow, parent)
            arrowRect.moveTo(parent.mapToGlobal(arrowRect.topLeft()))
            if arrowRect.contains(event.globalPos()) or self.rect().contains(event.pos()):
                self.setAttribute(Qt.WA_NoMouseReplay)
        QtGui.QFrame.mousePressEvent(self, event)

    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_buttonBox_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_buttonBox_reset()

    def on_buttonBox_reset(self):
        pass

    def on_buttonBox_apply(self, _id=None):
        db = QtGui.qApp.db
        table = db.table('rbDiagnosticService')
        name = forceStringEx(self.edtName.text())
        cond = []
        order = table['name'].name()
        for col, value in self.tableModel.headerSortingCol.items():
            order = ' '.join([['code', 'name', 'fullName', 'synonyms', 'method', 'area', 'localization', 'components'][col], u'ASC' if value else u'DESC'])
        if self._customFilter:
            cond.append(self._customFilter)
        if name:
            nameFilter = []
            dotedName = addDotsEx(name)
            nameFilter.append(table['name'].like(dotedName))
            nameFilter.append(table['fullName'].like(dotedName))
            nameFilter.append(table['synonyms'].like(dotedName))
            cond.append(db.joinOr(nameFilter))

        idList = db.getDistinctIdList(table, [table['id'].name()], where=cond, order=order, limit=1000)
        self.setIdList(idList, id)

    def closeEvent(self, event):
        preferences = self.tblServices.savePreferences()
        setPref(QtGui.qApp.preferences.windowPrefs, 'CDiagnosticServiceExPopup', preferences)
        QtGui.QFrame.closeEvent(self, event)

    def initModel(self, _id=None):
        self.on_buttonBox_apply(_id)

    def setIdList(self, idList, posToId):
        if idList:
            self.tblServices.setIdList(idList, posToId)
            self.tabWidget.setCurrentIndex(0)
            self.tabWidget.setTabEnabled(0, True)
        else:
            self.tblServices.setIdList(idList)
            self.tabWidget.setTabEnabled(0, True)
            
    @pyqtSignature('QString')
    def on_edtSearch_textChanged(self, text):
        self.loadData(forceString(text))

    def loadData(self, name=None):
        db = QtGui.qApp.db
        table = db.table('rbDiagnosticService')
        cond = []
        order = table['name'].name()
        for col, value in self.tableModel.headerSortingCol.items():
            order = ' '.join(
                [['code', 'name', 'fullName', 'synonyms', 'method', 'area', 'localization', 'components'][col],
                 u'ASC' if value else u'DESC'])
        if self._customFilter:
            cond.append(self._customFilter)
        if name:
            if any(ch.isdigit() for ch in name):
                cond.append(table['code'].like('%' + name + '%'))
            else:
                nameFilter = []
                dotedName = addDotsEx(name)
                nameFilter.append(table['name'].like(dotedName))
                nameFilter.append(table['fullName'].like(dotedName))
                nameFilter.append(table['synonyms'].like(dotedName))
                cond.append(db.joinOr(nameFilter))

        idList = db.getDistinctIdList(table, [table['id'].name()], where=cond, order=order, limit=1000)
        self.setIdList(idList, id)

    @pyqtSignature('QModelIndex')
    def on_tblServices_doubleClicked(self, index):
        if index.isValid():
            if Qt.ItemIsEnabled & self.tableModel.flags(index):
                serviceId = self.tblServices.currentItemId()
                self.selectServiceId(serviceId)

    def selectServiceId(self, serviceId):
        self.serviceId = serviceId
        self.emit(SIGNAL('serviceIdSelected(int)'), serviceId)
        self.close()


class CDiagnosticServiceTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self._parent = parent
        self._specialValues = []
        self.addColumn(CTextCol(u'Код', ['code'], 5))
        self.addColumn(CTextCol(u'Наименование', ['name'], 15))
        self.addColumn(CTextCol(u'Полное наименование', ['fullName'], 15))
        self.addColumn(CTextCol(u'Синонимы', ['synonyms'], 15))
        self.addColumn(CTextCol(u'Метод', ['method'], 15))
        self.addColumn(CTextCol(u'Область', ['area'], 15))
        self.addColumn(CTextCol(u'Локализация', ['localization'], 15))
        self.addColumn(CTextCol(u'Компоненты', ['components'], 15))
        self._fieldNames = ['code', 'name', 'fullName', 'synonyms', 'method', 'area', 'localization', 'components']
        self.setTable('rbDiagnosticService')

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def getActualEmptyRecord(self):
        record = QtSql.QSqlRecord()
        record.append(QtSql.QSqlField('code', QVariant.String))
        record.append(QtSql.QSqlField('name', QVariant.String))
        record.append(QtSql.QSqlField('fullName', QVariant.String))
        record.append(QtSql.QSqlField('synonyms', QVariant.String))
        record.append(QtSql.QSqlField('method', QVariant.String))
        record.append(QtSql.QSqlField('area', QVariant.String))
        record.append(QtSql.QSqlField('localization', QVariant.String))
        record.append(QtSql.QSqlField('components', QVariant.String))
        return record
