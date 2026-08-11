# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2015 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignature, Qt, QEvent, QSize, QString, QVariant, SIGNAL

from library.DbComboBox  import CDbComboBox, CDbDataCache
from library.Utils       import forceString, forceStringEx

from KLADR.KLADRModel    import CKLADRStreetSearchModel, getKladrTreeModel, getAllSelectableKladrTreeModel, CStreetModel
from KLADR.KLADRTree     import CKLADRTreePopup
from KLADR.Ui_KLADRStreetPopup import Ui_KLADRStreetPopup


class CKLADRComboBox(QtGui.QComboBox):
    def __init__(self, parent):
        QtGui.QComboBox.__init__(self, parent)
        self.SizeAdjustPolicy(QtGui.QComboBox.AdjustToMinimumContentsLength)
#        self._searchString = ''
        self._popupView = CKLADRTreePopup(self)
        self._popupView.setObjectName('CKladrComboBoxPopupView')
#        self.setView(self._popupView)
#        self._popupView.installEventFilter(self)
#        self._popupView.viewport().installEventFilter(self)
#        self.connect(self._popupView, SIGNAL('activated(QModelIndex)'), self.on_ItemActivated)
#        self.connect(self._popupView, SIGNAL('entered(QModelIndex)'), self.setCurrentIndex)
        self.connect(self._popupView, SIGNAL('codeSelected(QString)'), self.setCode)
        self.connect(self._popupView, SIGNAL('codeSelected(QModelIndex)'), self.setIndex)
        self.setModelColumn(2)
        self._model = getKladrTreeModel()
        self.setModel(self._model)


    def setAreaSelectable(self, value=True):
        self._model.areaSelectable = value


    def getChildrenCodeList(self, code=None):
        if code is None:
            return None
        return self._model.getChildrenCodeList(code)


    def showPopup(self):
        pos = self.mapToGlobal(self.rect().bottomLeft())
        size=self._popupView.sizeHint()
#        size.setWidth(self.rect().width()+20) # magic. похоже, что sizeHint считается неправильно. русские буквы виноваты?
        size.setWidth(self.width()) # magic. похоже, что sizeHint считается неправильно. русские буквы виноваты?
        screen = QtGui.QApplication.desktop().availableGeometry(pos)
        pos.setX( max(min(pos.x(), screen.right()-size.width()), screen.left()) )
        pos.setY( max(min(pos.y(), screen.bottom()-size.height()), screen.top()) )
        self._popupView.resize(size)
        self._popupView.move(pos)
        self._popupView.beforeShow()
        self._popupView.setCurrentIndex(self._model.index(self.currentIndex(), 0, self.rootModelIndex()))
        self._popupView.show()


    def setIndex(self, index):
        self.setCurrentIndex(index)


    def setCode(self, code):
        index = self._model.findCode(code)
        self.setIndex(index)


    def code(self):
        modelIndex = self._model.index(self.currentIndex(), 0, self.rootModelIndex())
        return self._model.code(modelIndex)


    def on_ItemActivated(self, index):
        if index.isValid():
            if (int(index.flags()) & Qt.ItemIsSelectable) != 0:
                self.hidePopup()
                self.emit(SIGNAL('itemSelected(QModelIndex)'), index)
            else:
#                print self._popupView.isExpanded(index)
                self._popupView.setExpanded(index, not self._popupView.isExpanded(index))


#    def showPopup(self):
##        self._searchString = ''
#        modelIndex = self.model().index(self.currentIndex(), 0, self.rootModelIndex())
#        QtGui.QComboBox.showPopup(self)
#        self._popupView.setCurrentIndex(modelIndex)


    def setCurrentIndex(self, index):
        self.setRootModelIndex(index.parent())
        QtGui.QComboBox.setCurrentIndex(self, index.row())
        self.emit(SIGNAL('codeSelected(QString)'), self._model.code(index))


    def keyPressEvent(self, event):
#        print event.key(), Qt.Key_Equal
        if event.key() == Qt.Key_Equal:
            kladr = QtGui.qApp.defaultKLADR()
            if kladr:
                self.setCode(kladr)
            event.accept()
        elif event.key() == Qt.Key_Plus:
            kladr = QtGui.qApp.provinceKLADR()
            if kladr:
                self.setCode(kladr)
            event.accept()
        elif event.key() == Qt.Key_Delete:
            self.setCode('')
            event.accept()
        else:
            QtGui.QComboBox.keyPressEvent(self, event)


    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress: # and obj == self._popupView:
            if event.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Select):
                index = self._popupView.currentIndex()
                if index.isValid() and (int(index.flags()) & Qt.ItemIsSelectable) != 0:
                    self.hidePopup()
                    self.setCurrentIndex(index)
                    self.emit(SIGNAL('itemSelected(QModelIndex)'), index)
                return True
            return False
        if event.type() == QEvent.MouseButtonRelease and obj == self._popupView.viewport():
            return True
        return False


class CAllSelectableKLADRComboBox(CKLADRComboBox):
    def __init__(self, parent):
        CKLADRComboBox.__init__(self, parent)
        self._model = getAllSelectableKladrTreeModel()
        self.setModel(self._model)
        self._popupView.treeModel = self._model
        self._popupView.treeView.setModel(self._model)

#######################################################################################


class CStreetComboBox(QtGui.QComboBox):
    def __init__(self, parent):
        QtGui.QComboBox.__init__(self, parent)
        self._searchString = ''
        #self.setMinimumContentsLength(20)
        self._model = CStreetModel(None)
        self._popupView = CPopupView(self)
        self._popupView.setObjectName('CStreetComboBoxPopupView')
        #self.setView(self._popupView)
        self.connect(self._popupView, SIGNAL('codeSelected(QString)'), self.setCode)
        self.connect(self._popupView, SIGNAL('codeSelected(QModelIndex)'), self.setIndex)
        self.setModelColumn(2)
        self.setModel(self._model)
        self.setAddNone(True)

    
    def setCode(self, code):
        self._model.clearNoActualStreet()
        index = self._model.indexByCode(code)
        self.setCurrentIndex(index)

    def setCmbName(self, name):
        self._model._cmbName = name
    
    
    def setIndex(self, index):
        self.setCurrentIndex(index.row())
    
    
    def setCurrentIndex(self, index):
        QtGui.QComboBox.setCurrentIndex(self, index)
        self.emit(SIGNAL('codeSelected(QString)'), self._model.code(index))
    
    
    def setAreaSelectable(self, value=True):
        self._model.areaSelectable = value
    

    def setOkato(self, filter):
        code = self._model.code(self.currentIndex())
        self._model.setOkato(filter)
        index = self._model.indexByCode(code)
        if index:
            self.setCurrentIndex(index)
        else:
            self.setCurrentIndex(0)


    def sizeHint(self):
        return QSize(20, 20)


    def setAddNone(self, flag):
        code = self._model.code(self.currentIndex())
        self._model.setAddNone(flag)
        index = self._model.indexByCode(code)
        if index:
            self.setCurrentIndex(index)
        else:
            self.setCurrentIndex(0)


    def setPrefix(self, prefix):
        code = self._model.code(self.currentIndex())
        self._model.setPrefix(prefix)
        index = self._model.indexByCode(code)
        if index:
            self.setCurrentIndex(index)
        else:
            self.setCurrentIndex(0)
        if len(self._model.stringList.codes) < 1:
            self._popupView.tabWidget.setEnabled(False)
        else:
            self._popupView.tabWidget.setEnabled(True)
            

    def setCity(self, city):
        self._popupView.tableModel.searchString = ''
        self.setPrefix(city[0:-2])


    def addNone(self, flag):
        self._model


    def code(self):
        rowIndex = self.currentIndex()
        return self._model.code(rowIndex)


    def codeList(self):
        return self._model.codeList()


    def showPopup(self):
        self._searchString = ''
        pos = self.mapToGlobal(self.rect().bottomLeft())
        size=self._popupView.sizeHint()
        size.setWidth(self.width())
        screen = QtGui.QApplication.desktop().availableGeometry(pos)
        pos.setX( max(min(pos.x(), screen.right()-size.width()), screen.left()) )
        pos.setY( max(min(pos.y(), screen.bottom()-size.height()), screen.top()) )
        self._popupView.resize(size)
        self._popupView.move(pos)
        self._popupView.beforeShow()
        self._popupView.setCurrentIndex(self._model.createIndex(self.currentIndex(),0))
        self._popupView.show()


    def focusInEvent(self, event):
        self._searchString = ''
        QtGui.QComboBox.focusInEvent(self, event)


    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            event.ignore()
        elif key in (Qt.Key_Return, Qt.Key_Enter):
            event.ignore()
        if key == Qt.Key_Delete:
            self._searchString = ''
            self.lookup()
            event.accept()
        elif key == Qt.Key_Backspace : # BS
            self._searchString = self._searchString[:-1]
            self.lookup()
            event.accept()
        elif not event.text().isEmpty():
            char = event.text().at(0)
            if char.isPrint():
                self._searchString = self._searchString + unicode(QString(char)).upper()
                self.lookup()
                event.accept()
            else:
                QtGui.QComboBox.keyPressEvent(self, event)
        else:
            QtGui.QComboBox.keyPressEvent(self, event)

    
    def on_ItemActivated(self, index):
        if index.isValid():
            if (int(index.flags()) & Qt.ItemIsSelectable) != 0:
                self.hidePopup()
                self.emit(SIGNAL('itemSelected(QModelIndex)'), index)
    
    
    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress: 
            if event.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Select):
                index = self._popupView.currentIndex()
                if index.isValid() and (int(index.flags()) & Qt.ItemIsSelectable) != 0:
                    self.hidePopup()
                    self.setCurrentIndex(index)
                    self.emit(SIGNAL('itemSelected(QModelIndex)'), index)
                return True
            return False
        if event.type() == QEvent.MouseButtonRelease and obj == self._popupView.viewport():
            return True
        return False
    

    def lookup(self):
        i, self._searchString, len = self._model.searchStreet(self._searchString)
        if len>1 and QtGui.qApp.getKladrResearch():
            char = self._searchString[-1]
            self.showPopup()
            self._popupView.listView.keyboardSearchBase(char)
        elif i.row()>=0 and i.row()!=self.currentIndex() and len <= 1 or not QtGui.qApp.getKladrResearch():
            self.setCurrentIndex(i.row())


class CMainRegionsKLADRComboBox(QtGui.QComboBox):
    def __init__(self, parent):
        QtGui.QComboBox.__init__(self, parent)
        self.cacheIndexByCode = {}
        self.loadKLADRItems()


    def loadKLADRItems(self):
        self.addItem('', QVariant())
        records = QtGui.qApp.db.getRecordList('kladr.KLADR', 'NAME, CODE',
                                       'parent=\'\' AND RIGHT(CODE,2)=\'00\'',
                                       'NAME, SOCR, CODE')
        for record in records:
            self.addItem(forceString(record.value('NAME')), record.value('CODE'))
            self.cacheIndexByCode[forceString(record.value('CODE'))] = self.count()-1

    def getIndexByCode(self, code):
        return self.cacheIndexByCode.get(code, None)


# ##################################

def getKladrOkatoDBCheckSum(tableName, fieldName,  filter):
    return 1


class CKladrOkatoDbCache(CDbDataCache):
    @classmethod
    def getDBCheckSumFunc(cls):
        return getKladrOkatoDBCheckSum


class CKladrOkatoComboBox(CDbComboBox):
    def __init__(self, parent):
        CDbComboBox.__init__(self, parent, idFieldName='CODE', idConvertFunc=forceString)
        self.setTable('kladr.OKATO')
        self._filterCode = None
        self._kladrCode = None
        self._isEnabled = False


    def setModel(self, model):
        model.setDataCache(CKladrOkatoDbCache)
        CDbComboBox.setModel(self, model)


    def setEnabled(self, value):
        self._isEnabled = value
        self._setEnabled(value and bool(self._filterCode))


    def _setEnabled(self, value):
        CDbComboBox.setEnabled(self, value)


    def setKladrCode(self, kladrCode):
        if self._kladrCode != kladrCode:
            self._kladrCode = kladrCode
            filterCode = forceString(QtGui.qApp.db.translate('kladr.KLADR', 'CODE', self._kladrCode, 'OCATD'))[:2]
            if self._filterCode != filterCode:
                self._filterCode = filterCode
                filter = 'kladr.OKATO.P0=\'%s\' AND kladr.OKATO.P1 != \'\' AND kladr.OKATO.P2 = \'\'' % self._filterCode
                self.setFilter(filter)
        self._setEnabled(self._isEnabled and bool(self._filterCode))
        
        
class CPopupView(QtGui.QFrame, Ui_KLADRStreetPopup):
    def __init__(self, parent):
        QtGui.QFrame.__init__(self, parent, Qt.Popup)
        self.setFrameShape(QtGui.QFrame.StyledPanel)
        self.setAttribute(Qt.WA_WindowPropagation)
        self.listModel = parent._model
        self.tableModel = CKLADRStreetSearchModel(self)
        self.tableSelectionModel = QtGui.QItemSelectionModel(self.tableModel,  self)
        self.tableSelectionModel.setObjectName('tableSelectionModel')
        self.setupUi(self)
        self.listView.setModel(self.listModel)
        self.tblSearchResult.horizontalHeader().setResizeMode(3)
        self.tblSearchResult.horizontalHeader().hide()
        self.tblSearchResult.setModel(self.tableModel)
        self.tblSearchResult.setSelectionModel(self.tableSelectionModel)

        self.tabList.setFocusProxy(self.listView)
        self.tabSearch.setFocusProxy(self.edtWords)
        self.edtWords.installEventFilter(self)
    
    def mousePressEvent(self, event):
        parent = self.parentWidget()
        if parent!=None:
            opt=QtGui.QStyleOptionComboBox()
            opt.init(parent)
            arrowRect = parent.style().subControlRect(
                QtGui.QStyle.CC_ComboBox, opt, QtGui.QStyle.SC_ComboBoxArrow, parent)
            arrowRect.moveTo(parent.mapToGlobal(arrowRect.topLeft()))
            if (arrowRect.contains(event.globalPos()) or self.rect().contains(event.pos())):
                self.setAttribute(Qt.WA_NoMouseReplay)
        QtGui.QFrame.mousePressEvent(self, event)


    def eventFilter(self, watched, event):
        if watched == self.edtWords:
            if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Select):
                event.accept()
                self.btnSearch.animateClick()
                return True
        return QtGui.QFrame.eventFilter(self, watched, event)
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            self.selectCode('')
            event.accept()
        else:
            QtGui.QFrame.keyPressEvent(self, event)

    def beforeShow(self):
        self.tabWidget.setCurrentIndex(0)
        self.listView.setFocus()
        self.edtWords.clear()
    
    def setCurrentIndex(self, index):
        if self.listView.currentIndex() != index:
            self.listView.setCurrentIndex(index)
        
    def keyboardSearch(self):
        rowIndex, search = self.model().searchStreet(unicode(self._searchString))
        if rowIndex >= 0:
            index = self.model().index(rowIndex, 0)
            self.setCurrentIndex(index)
            
    def focusInEvent(self, event):
        self._searchString = ''
        QtGui.QListView.focusInEvent(self, event)
        
    def setCurrentCode(self, code):
        if code:
            index = self.listModel.createIndex(self.listModel.indexByCode(code), 0, code)
            self.setCurrentIndex(index)


    def selectIndex(self, index):
        self.emit(SIGNAL('codeSelected(QModelIndex)'), index)
        self.close()


    def selectCode(self, code):
        self.emit(SIGNAL('codeSelected(QString)'), QString(code))
        self.close()


    def getCurrentCode(self):
        index = self.tblSearchResult.currentIndex()
        code = self.tableModel.code(index.row())
        return code


    @pyqtSignature('int')
    def on_tabWidget_currentChanged(self, index):
        if index == 0:
            code = self.getCurrentCode()
            self.setCurrentCode(code)


    @pyqtSignature('QModelIndex')
    def on_listView_doubleClicked(self, index):
        flags = self.listModel.flags(index)
        if flags & Qt.ItemIsSelectable:
            self.selectIndex(index)


    @pyqtSignature('')
    def on_btnSearch_clicked(self):
        keyboardModifiers = QtGui.qApp.keyboardModifiers()
        if not(keyboardModifiers & (Qt.AltModifier|Qt.ShiftModifier)):
            index = self.listView.currentIndex()
            item = index.internalPointer()
        searchString = forceStringEx(self.edtWords.text())
        self.tableModel.setFilter(searchString, self.listModel._prefix, self.listModel._okato)


    @pyqtSignature('QModelIndex')
    def on_tblSearchResult_doubleClicked(self, index):
        code = self.tableModel.code(index.row())
        self.selectCode(code)
 