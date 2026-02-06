# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2012-2022 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
from PyQt4 import QtGui
from PyQt4.QtCore import Qt, SIGNAL, pyqtSignature

from library.DbComboBox import CDbComboBox
from library.TableModel import CTableModel, CTextCol
from library.TableView import CTableView
from library.Utils import forceRef, forceString, forceInt
from library.database import CTableRecordCache



class CVaccineIdentificationModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.addColumn(CTextCol(u'Идентификатор',['code'], 6))
        self.addColumn(CTextCol(u'Торговое наименование МИБП', ['name'], 12))
        self.addColumn(CTextCol(u'Дозировка',         ['DOZA'], 5))
        self.addColumn(CTextCol(u'Количество доз', ['NUM_DOSA'], 5))
        self.addColumn(CTextCol(u'Упаковка', ['DRUGPACK'], 5))
        self.addColumn(CTextCol(u'Производитель',        ['PRODUCER'], 10))
        self.addColumn(CTextCol(u'Страна', ['COUNTRY'], 5))
        self.loadField('id')
        self.setTable()

    def flags(self, index):
        return Qt.ItemIsEnabled|Qt.ItemIsSelectable

    def setIdList(self, idList, realItemCount=None):
        return CTableModel.setIdList(self, [None] + idList, realItemCount)

    def setTable(self):
        db = QtGui.qApp.db
        tableRbVaccineIdentification = db.table('rbVaccine_Identification')
        tableSpr = db.table(QtGui.qApp.db.db.databaseName() + '.`v1.2.643.5.1.13.13.11.1078`').alias('tableSpr')
        queryTable = tableRbVaccineIdentification.innerJoin(tableSpr, tableRbVaccineIdentification['value_spr'].eq(tableSpr['id']))
        loadFields = []
        loadFields.append(u'''rbVaccine_Identification.id as id, tableSpr.code, tableSpr.name as name, tableSpr.DOZA as DOZA, tableSpr.DRUGPACK as DRUGPACK, tableSpr.NUM_DOSA as NUM_DOSA, tableSpr.PRODUCER as PRODUCER, tableSpr.COUNTRY as COUNTRY''')
        self._table = queryTable
        self._recordsCache = CTableRecordCache(db, self._table, loadFields)


class CVaccineIdentificationComboBoxPopup(QtGui.QFrame):
    __pyqtSignals__ = ('VaccineIdentIdSelected(int, QString)',
                      )

    def __init__(self, parent = None):
        QtGui.QFrame.__init__(self, parent, Qt.Popup)
        self.setFrameShape(QtGui.QFrame.StyledPanel)
        self.setAttribute(Qt.WA_WindowPropagation)
        self.tableModel = CVaccineIdentificationModel(self)
        self.tableSelectionModel = QtGui.QItemSelectionModel(self.tableModel, self)
        self.tableSelectionModel.setObjectName('tableSelectionModel')
        self.layout = QtGui.QGridLayout(self)
        self.tblVaccineIdentification = CTableView(self)
        self.layout.addWidget(self.tblVaccineIdentification)
        self.tblVaccineIdentification.setModel(self.tableModel)
        self.tblVaccineIdentification.setSelectionModel(self.tableSelectionModel)
        self.tblVaccineIdentification.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.tblVaccineIdentification.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.vaccineIdentId = None
        self.connect(self.tblVaccineIdentification, SIGNAL("doubleClicked(QModelIndex)"), self.on_tblVaccineIdentification_doubleClicked)

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

    def setIdList(self, idList, posToId):
        self.tblVaccineIdentification.setIdList(idList, posToId)
        self.tblVaccineIdentification.setFocus(Qt.OtherFocusReason)

    def selectVaccineIdentId(self, vaccineIdentId, vaccineIdentText):
        self.vaccineIdentId = vaccineIdentId
        self.emit(SIGNAL('VaccineIdentIdSelected(int, QString)'), vaccineIdentId, vaccineIdentText)
        self.close()

    @pyqtSignature('QModelIndex')
    def on_tblVaccineIdentification_doubleClicked(self, index):
        if index.isValid():
            row = index.row()
            modelRowRecord = self.tblVaccineIdentification.model().getRecordByRow(row)
            if not modelRowRecord:
                self.selectVaccineIdentId(-1, u'')
                return
            vaccineIdentId = forceInt(modelRowRecord.value('id'))
            vaccineIdentText = u' | '.join([forceString(modelRowRecord.value('code')), forceString(modelRowRecord.value('name')), forceString(modelRowRecord.value('DOZA')), forceString(modelRowRecord.value('PRODUCER'))])
            self.selectVaccineIdentId(vaccineIdentId, vaccineIdentText)


class CVaccineIdentificationComboBox(QtGui.QComboBox):
    def __init__(self, parent = None):
        QtGui.QComboBox.__init__(self, parent)
        self._popup = CVaccineIdentificationComboBoxPopup(self)
        self.connect(self._popup, SIGNAL('VaccineIdentIdSelected(int, QString)'), self.setValue)
        self.lastVaccineId = None
        self.vaccineIdentId = None
        self.idList = []
        self.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToMinimumContentsLength)


    def showPopup(self):
        if not self._popup:
            self._popup = CVaccineIdentificationComboBoxPopup(self)
            self.connect(self._popup,SIGNAL('VaccineIdentIdSelected(int, QString)'), self.setValue)
        pos = self.rect().bottomLeft()
        pos = self.mapToGlobal(pos)
        size = self._popup.sizeHint()
        screen = QtGui.QApplication.desktop().availableGeometry(pos)
        size.setWidth(screen.width())
        pos.setX( max(min(pos.x(), screen.right()-size.width()), screen.left()) )
        pos.setY( max(min(pos.y(), screen.bottom()-size.height()), screen.top()) )
        self._popup.move(pos)
        self._popup.resize(size)
        self._popup.setIdList(self.idList, self.vaccineIdentId)
        self._popup.show()
        self._popup.tblVaccineIdentification.horizontalHeader().setStretchLastSection(True)
        self._popup.tblVaccineIdentification.resizeColumnToContents(1)
        self._popup.tblVaccineIdentification.resizeColumnToContents(5)


    def setValue(self, vaccineIdentId, vaccineIdentText=None):
        if not vaccineIdentText:
            if not self._popup:
                self._popup = CVaccineIdentificationComboBoxPopup(self)
                self.connect(self._popup, SIGNAL('VaccineIdentIdSelected(int, QString)'), self.setValue)
            popupModelRecord = self._popup.tableModel.getRecordById(vaccineIdentId)
            if popupModelRecord:
                vaccineIdentText = u' | '.join([forceString(popupModelRecord.value('code')), forceString(popupModelRecord.value('name')), forceString(popupModelRecord.value('DOZA')), forceString(popupModelRecord.value('PRODUCER'))])
            else:
                vaccineIdentText = u''
        if vaccineIdentId == -1:
            self.vaccineIdentId = None
        else:
            self.vaccineIdentId = vaccineIdentId
        self.clear()
        self.addItems([vaccineIdentText])
        self.setCurrentIndex(0)

    def value(self):
        return self.vaccineIdentId

    def setVaccineId(self, vaccineId):
        if self.lastVaccineId and vaccineId != self.lastVaccineId:
            self.setValue(-1)
        db = QtGui.qApp.db
        tableRBVI = db.table('rbVaccine_Identification')
        tableSpr = db.table(QtGui.qApp.db.db.databaseName() + '.`v1.2.643.5.1.13.13.11.1078`').alias('tableSpr')
        queryTable = tableRBVI.innerJoin(tableSpr, tableRBVI['value_spr'].eq(tableSpr['id']))
        cond = [tableRBVI['deleted'].eq(0),
                tableRBVI['master_id'].eq(vaccineId)]
        self.idList = db.getIdList(queryTable, queryTable['id'].name(), cond)
        self.lastVaccineId = vaccineId

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Delete:
            self.setValue(None, None)
            event.accept()
        elif key == Qt.Key_Backspace:
            self.setValue(None, None)
            event.accept()
        else:
            QtGui.QComboBox.keyPressEvent(self, event)


class CVaccinationProbeIdentificationComboBox(CDbComboBox):
    def __init__(self, parent):
        CDbComboBox.__init__(self, parent)
        self.setNameField("CONCAT_WS(' | ', value, note)")
        self.setAddNone(True)
        self.setFilter('deleted = 0')
        self.setTable('rbVaccinationProbe_Identification')

    def setVaccinationProbeId(self, vaccineId):
        db = QtGui.qApp.db
        systemId = forceRef(db.translate('rbAccountingSystem', 'urn', 'urn:oid:1.2.643.5.1.13.13.11.1078', 'id'))
        table = db.table('rbVaccinationProbe_Identification')
        cond = [table['deleted'].eq(0),
                table['master_id'].eq(vaccineId),
                table['system_id'].eq(systemId),
                table['checkDate'].isNotNull()]
        self.setFilter(db.joinAnd(cond))
