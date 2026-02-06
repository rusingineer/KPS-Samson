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
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt, QVariant, SIGNAL, pyqtSignature

from library.ICDCodeEdit import CICDCodeEdit, CICDCodeEditEx
from library.ICDInDocTableCol import CICDInDocTableCol
from library.ICDTree import CICDTreeModel, CICDDiagTreeItem, CICDDiagExTreeItem, CICDDiagSubclassTreeItem, \
    CICDBlockTreeItem, CICDClassTreeItem, CICDRootTreeItem, CICDTreePopup
from library.Utils import forceString, forceRef


class CMultiICDTreeModel(CICDTreeModel):

    """Модель дерева МКБ с поддержкой чекбоксов"""

    __pyqtSignals__ = ('diagnosisToggled(QString, bool)',)

    def __init__(self, parent=None, filter = '', findFilter=None):
        CICDTreeModel.__init__(self, parent, filter, findFilter)
        self._rootItem = CMultiICDRootTreeItem(self.filter)

    def setFindFilter(self, findFilter=None):
        self.findFilter = findFilter
        if self._rootItem:
            self._rootItem = CMultiICDRootTreeItem(self.filter, self.findFilter)
            self.reset()


    def setFilter(self, filter=None):
        if self.filter != filter:
            self.filter = filter
            if self._rootItem:
                self._rootItem = CMultiICDRootTreeItem(self.filter, self.findFilter)
                self.reset()


    def flags(self, index):
        if index.isValid():
            item = index.internalPointer()
            if item.selectable() and item.childCount() == 0 and index.column() == 1:
                return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable
        return Qt.ItemIsEnabled

    def data(self, index, role):
        if index.isValid() and role == Qt.CheckStateRole and index.column() == 1:
            item = index.internalPointer()
            if item.selectable() and item.childCount() == 0 and hasattr(item, 'isChecked'):
                return Qt.Checked if item.isChecked() else Qt.Unchecked

        return CICDTreeModel.data(self, index, role)

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.CheckStateRole and index.isValid() and index.column() == 1:
            item = index.internalPointer()
            if hasattr(item, 'isChecked') and hasattr(item, 'setChecked') and item.selectable() and item.childCount() == 0:
                checked = value == Qt.Checked
                item.setChecked(checked)
                diagCode = forceString(item.data(0))
                self.emit(SIGNAL('dataChanged(QModelIndex, QModelIndex)'), index, index)
                self.emit(SIGNAL('diagnosisToggled(QString, bool)'), diagCode, checked)
                return True

        return CICDTreeModel.setData(self, index, value, role)


class CMultiICDDiagTreeItem(CICDDiagTreeItem):
    def __init__(self, code, name, index, subclassId, parent=None, filter='', findFilter=''):
        CICDDiagTreeItem.__init__(self, code, name, index, subclassId, parent, filter, findFilter)
        self._checked = False

    def isChecked(self):
        return self._checked

    def setChecked(self, checked):
        self._checked = checked

    def loadChilds(self):
        result = []
        i = 0
        if self.subclassId:
            for code, name in self.getSubclassItems(self.subclassId):
                result.append( CICDDiagSubclassTreeItem(self.code + '. '+ code, ' -/- '+name, i, None, self, self.filter, self.findFilter) )
                i += 1
        findFilter = (self.findFilter[1]) if self.findFilter and isinstance(self.findFilter, tuple) else self.findFilter
        stmt   = 'SELECT DiagID, DiagName, MKBSubclass_id FROM %s WHERE DiagID LIKE \'%s.%%\' %s %s ORDER BY DiagID' %('MKB', self.code, (' AND %s'% self.filter) if self.filter else '', (' AND %s'% findFilter) if findFilter else '')
        query = QtGui.qApp.db.query(stmt)
        while query.next():
            record = query.record()
            code   = forceString(record.value('DiagID'))
            name   = forceString(record.value('DiagName'))
            subclassId = forceRef(record.value('MKBSubclass_id'))
            result.append(CMultiICDDiagExTreeItem(code, name, i, subclassId, self, self.filter, self.findFilter))
            i += 1
        return result

class CMultiICDDiagExTreeItem(CICDDiagExTreeItem):
    def __init__(self, code, name, index, subclassId, parent=None, filter='', findFilter=''):
        CICDDiagExTreeItem.__init__(self, code, name, index, subclassId, parent, filter, findFilter)
        self._checked = False

    def isChecked(self):
        return self._checked

    def setChecked(self, checked):
        self._checked = checked

    def loadChilds(self):
        result = []
        i = 0
        if self.subclassId:
            for code, name in self.getSubclassItems(self.subclassId):
                result.append(CMultiICDDiagSubclassTreeItem(self.code + code, ' -/- ' + name, i, None, self, self.filter, self.findFilter))
                i += 1
        return result

class CMultiICDDiagSubclassTreeItem(CICDDiagSubclassTreeItem):
    def __init__(self, code, name, index, subclassId, parent=None, filter='', findFilter=''):
        CICDDiagSubclassTreeItem.__init__(self, code, name, index, subclassId, parent, filter, findFilter)
        self._checked = False

    def isChecked(self):
        return self._checked

    def setChecked(self, checked):
        self._checked = checked



class CMultiICDBlockTreeItem(CICDBlockTreeItem):
    def loadChilds(self):
        result = []
        findFilter = (self.findFilter[0]) if self.findFilter and isinstance(self.findFilter, tuple) else self.findFilter
        stmt   = 'SELECT DiagID, DiagName, MKBSubclass_id FROM %s WHERE BlockID = \'%s\' AND DiagID LIKE \'___\' %s %s ORDER BY DiagID' %('MKB', self.code, (' AND %s'% self.filter) if self.filter else '', (' AND %s'% findFilter) if findFilter else '')
        query = QtGui.qApp.db.query(stmt)
        i = 0
        while query.next():
            record = query.record()
            code   = forceString(record.value('DiagID'))
            name   = forceString(record.value('DiagName'))
            subclassId = forceRef(record.value('MKBSubclass_id'))
            result.append(CMultiICDDiagTreeItem(code, name, i, subclassId, self, self.filter, self.findFilter))
            i += 1
        return result

class CMultiCICDClassTreeItem(CICDClassTreeItem):
    def loadChilds(self):
        result = []
        findFilter = (self.findFilter[0]) if self.findFilter and isinstance(self.findFilter, tuple) else self.findFilter
        stmt   = 'SELECT DISTINCT BlockID, BlockName FROM %s WHERE ClassID = \'%s\' %s %s ORDER BY BlockID' %('MKB', self.code, (' AND %s'% self.filter) if self.filter else '', (' AND %s'% findFilter) if findFilter else '')
        query = QtGui.qApp.db.query(stmt)
        i = 0
        while query.next():
            record = query.record()
            code   = forceString(record.value('BlockID'))
            name   = forceString(record.value('BlockName'))
            result.append(CMultiICDBlockTreeItem(code, name, i, None, self, self.filter, self.findFilter))
            i += 1
        return result

class CMultiICDRootTreeItem(CICDRootTreeItem):
    def loadChilds(self):
        result = []
        stmtFilter = u''
        if self.filter or self.findFilter:
            findFilter = (self.findFilter[0]) if self.findFilter and isinstance(self.findFilter, tuple) else self.findFilter
            stmtFilter = ('WHERE %s'%(u' AND '.join(filter for filter in [self.filter, findFilter] if filter)))
        stmt   = 'SELECT DISTINCT ClassID, ClassName FROM MKB %s ORDER BY ClassID'%(stmtFilter)
        query = QtGui.qApp.db.query(stmt)
        i = 0
        while query.next():
            record = query.record()
            code   = forceString(record.value('ClassID'))
            name   = forceString(record.value('ClassName'))
            result.append(CMultiCICDClassTreeItem(code, name, i, None, self, self.filter, self.findFilter))
            i += 1
        return result

class CMultiICDTreePopup(CICDTreePopup):
    __pyqtSignals__ = ('diagnosesChanged(QString)',)

    def __init__(self, parent=None, filter=u'', findfilter=u''):
        CICDTreePopup.__init__(self, parent, filter, findfilter)
        self.treeModel = CMultiICDTreeModel(self, filter, findfilter)
        self.treeView.setModel(self.treeModel)
        self.connect(self.treeModel, SIGNAL('diagnosisToggled(QString, bool)'),
                     self.onDiagnosisToggled)
        self._selectedDiagnoses = []
        currentText = forceString(parent.text())
        if currentText:
            self._selectedDiagnoses = [forceString(code).strip() for code in currentText.split(',') if forceString(code).strip()]
            self._setInitialCheckStates(self._selectedDiagnoses)

    def onDiagnosisToggled(self, diagCode, checked):
        diagStr = forceString(diagCode)
        if checked:
            if diagStr not in self._selectedDiagnoses:
                self._selectedDiagnoses.append(forceString(diagCode))
        else:
            if diagStr in self._selectedDiagnoses:
                self._selectedDiagnoses.remove(forceString(diagCode))
        diagnoses_str =u','.join(self._selectedDiagnoses)
        self.emit(SIGNAL('diagnosesChanged(QString)'), diagnoses_str)

    def _setInitialCheckStates(self, diagList):
        # Устанавливаем чекбоксы для кодов, которые уже были выбраны до открытия popup
        for diagCode in diagList:
            strCode = forceString(diagCode).strip()
            if strCode:
                index = self.treeModel.findDiag(strCode)
                if index.isValid():
                    item = index.internalPointer()
                    if hasattr(item, 'setChecked'):
                        item.setChecked(True)

    def setCurrentDiag(self, diagList):
        self.treeView.collapseAll()
        diagList = forceString(diagList)
        if diagList:
            codes = [code.strip() for code in diagList.split(',') if code.strip()]
            if codes:
                self.diag = codes[-1]
        if self.diag or self.findDiagId:
            index = self.treeModel.findDiag(self.diag if self.diag else self.findDiagId)
            self.treeView.scrollTo(index)
            self.treeView.setCurrentIndex(index)
            self.treeView.setExpanded(index, True)



    @pyqtSignature('QModelIndex')
    def on_treeView_doubleClicked(self, index):
        pass



class CMultiICDCodeEdit(CICDCodeEdit):
    def __init__(self, parent):
        CICDCodeEdit.__init__(self, parent)
        # Убираем маску ввода, т.к. у нас множественные коды
        self.setInputMask('')
        regex = QtCore.QRegExp(r'^[A-Z][0-9]{2}(\.[0-9])?(\s*,\s*[A-Z][0-9]{2}(\.[0-9])?)*$')
        validator = QtGui.QRegExpValidator(regex, self)
        self.setValidator(validator)


class CMultiICDCodeEditEx(CICDCodeEditEx):
    def __init__(self, parent=None):
        CICDCodeEditEx.__init__(self, parent)
        self._lineEdit = CMultiICDCodeEdit(self)
        self.setLineEdit(self._lineEdit)

    def showPopup(self):
        if not self.isReadOnly():
            if not self.ICDTreePopup:
                self.ICDTreePopup = CMultiICDTreePopup(self, self.filter, self.findfilter)
                self.connect(self.ICDTreePopup, SIGNAL('diagnosesChanged(QString)'), self.setText)
            pos = self.rect().bottomLeft()
            pos2 = self.rect().topLeft()
            pos = self.mapToGlobal(pos)
            pos2 = self.mapToGlobal(pos2)
            size = self.ICDTreePopup.sizeHint()
            screen = QtGui.QApplication.desktop().availableGeometry(pos)
            size.setWidth(screen.width())  # наименования длинные, распахиваем на весь экран
            pos.setX(max(min(pos.x(), screen.right() - size.width()), screen.left()))
            pos.setY(max(min(pos.y(), screen.bottom() - size.height()), screen.top()))
            self.ICDTreePopup.move(pos)
            self.ICDTreePopup.resize(size)
            self.ICDTreePopup.setLUDEnabled(self.isLUDEnabled)
            self.ICDTreePopup.setLUDChecked(self.isLUDSelected, self.clientId)
            self.ICDTreePopup.setCurrentDiag(self.text())
            self.ICDTreePopup.show()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Backspace:
            self._lineEdit.keyPressEvent(event)
        else:
            CICDCodeEditEx.keyPressEvent(self, event)

class CMultiICDInDocTableCol(CICDInDocTableCol):

    def createEditor(self, parent):
        editor = CMultiICDCodeEditEx(parent)
        return editor


