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

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, pyqtSignature, SIGNAL, QDate, QEvent, QVariant

from Accounting.Utils import getWeekProfile
from Events.Utils import getEventDuration, getEventWeekProfileCode
from library.database import CTableRecordCache
from library.Utils import getPref, setPref, forceString, forceDate, calcAgeTuple
from library.TableModel import CTableModel, CTextCol, CDoubleCol

from Ui_CSGComboBoxPopup import Ui_CSGComboBoxPopup


__all__ = ('CCSGComboBoxPopup',
          )

TABLE_CSG = 'mes.CSG'
TABLE_CSG_MKB = 'mes.CSG_Diagnosis'

class CCSGComboBoxPopup(QtGui.QFrame, Ui_CSGComboBoxPopup):
    __pyqtSignals__ = ('CSGSelected(int)',
                      )

    def __init__(self, parent = None, eventEditor = None):
        QtGui.QFrame.__init__(self, parent, Qt.Popup)
        self.setFrameShape(QtGui.QFrame.StyledPanel)
        self.setAttribute(Qt.WA_WindowPropagation)
        self.tableModel = CCSGTableModel(self)
        self.tableSelectionModel = QtGui.QItemSelectionModel(self.tableModel, self)
        self.tableSelectionModel.setObjectName('tableSelectionModel')
        self.setupUi(self)
        self.tblCSG.setModel(self.tableModel)
        self.tblCSG.setSelectionModel(self.tableSelectionModel)
        # self.buttonBox.button(QtGui.QDialogButtonBox.Apply).setDefault(True)
#       к сожалению в данном случае setDefault обеспечивает рамочку вокруг кнопочки
#       но enter не работает...
#         self.buttonBox.button(QtGui.QDialogButtonBox.Apply).setShortcut(Qt.Key_Return)
        self.eventBegDate = None
        self.clientSex = 0
        self.clientBirthDate = None
        self.MKB = ''
        self.associatedMKB = None
        self.complicationMKB = None
        self.codeMask = None
        self.eventProfileId = None
        self.csgId = None
        self.krit = None
        self.fractions = None
        self.csgBegDate = None
        self.csgEndDate = None
        self.eventEditor = eventEditor
        self.tblCSG.installEventFilter(self)
        preferences = getPref(QtGui.qApp.preferences.windowPrefs, 'CCSGComboBoxPopup', {})
        self.tblCSG.loadPreferences(preferences)
        # self.on_buttonBox_reset()


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


    def closeEvent(self, event):
        preferences = self.tblCSG.savePreferences()
        setPref(QtGui.qApp.preferences.windowPrefs, 'CCSGComboBoxPopup', preferences)
        QtGui.QFrame.closeEvent(self, event)


    def eventFilter(self, watched, event):
        if watched == self.tblCSG:
            if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Select):
                event.accept()
                index = self.tblCSG.currentIndex()
                self.tblCSG.emit(SIGNAL('doubleClicked(QModelIndex)'), index)
                return True
        return QtGui.QFrame.eventFilter(self, watched, event)


    # @pyqtSignature('QAbstractButton*')
    # def on_buttonBox_clicked(self, button):
    #     buttonCode = self.buttonBox.standardButton(button)
    #     if buttonCode == QtGui.QDialogButtonBox.Apply:
    #         self.on_buttonBox_apply()
    #     elif buttonCode == QtGui.QDialogButtonBox.Reset:
    #         self.on_buttonBox_reset()


    # def on_buttonBox_reset(self):
    #     parent = self.parentWidget()
    #     if parent.filterValues:
    #         self.chkSex.setChecked(parent.filterValues.get('sex', True))
    #         self.chkAge.setChecked(parent.filterValues.get('age', True))
    #         self.chkCsgServices.setChecked(parent.filterValues.get('csgServices', True))
    #         self.cmbMKB.setCurrentIndex(parent.filterValues.get('mkbCond', 2))
    #         self.cmbEventProfile.setCurrentIndex(parent.filterValues.get('isEventProfile', 1))
    #     else:
    #         self.chkSex.setChecked(True)
    #         self.chkAge.setChecked(True)
    #         self.chkCsgServices.setChecked(True)
    #         self.cmbMKB.setCurrentIndex(2)
    #         self.cmbEventProfile.setCurrentIndex(1)


    # def on_buttonBox_apply(self):
    #     parent = self.parentWidget()
    #     useSex        = self.chkSex.isChecked()
    #     useAge        = self.chkAge.isChecked()
    #     useCsgServices = self.chkCsgServices.isChecked()
    #     mkbCond    = self.cmbMKB.currentIndex()
    #     isEventProfile = self.cmbEventProfile.currentIndex()
    #     parent.filterValues = {'age': useAge,
    #                            'sex': useSex,
    #                            'csgServices': useCsgServices,
    #                            'mkbCond': mkbCond,
    #                            'isEventProfile': isEventProfile}
    #     parent.model().dbdata.select(parent.filterValues)
    #     idList = parent.model().dbdata.idList
    #     self.setCSGIdList(idList)


    def setCSGIdList(self, idList):
        if idList:
            self.tblCSG.setIdList(idList, self.csgId)
            self.tabWidget.setCurrentIndex(0)
            self.tabWidget.setTabEnabled(0, True)
            self.tblCSG.setFocus(Qt.OtherFocusReason)
        else:
            # self.tabWidget.setCurrentIndex(1)
            # self.tabWidget.setTabEnabled(0, False)
            self.tblCSG.setIdList(idList)
            self.tabWidget.setCurrentIndex(0)
            self.tabWidget.setTabEnabled(0, True)
            self.chkContractTariff.setFocus(Qt.OtherFocusReason)

    @pyqtSignature('bool')
    def on_chkContractTariff_toggled(self, checked):
        parent = self.parentWidget()
        parent.filterValues = {'showOnlyByContract': checked}
        parent.model().dbdata.select(parent.filterValues)
        idList = parent.model().dbdata.idList
        self.setCSGIdList(idList)


    def setup(self, clientSex, clientBirthDate, MKB, csgId, eventBegDate, mesServiceTemplate, codeMask = None,
              eventProfileId = None, krit = None, associatedMKB = None, complicationMKB = None, fractions = None,
              csgBegDate = None, csgEndDate = None):
        self.clientSex = clientSex
        self.clientBirthDate = clientBirthDate
        self.MKB = MKB
        self.csgId = csgId
        self.eventBegDate = eventBegDate
        self.codeMask = codeMask
        self.eventProfileId = eventProfileId
        self.mesServiceTemplate = mesServiceTemplate
        self.krit = krit
        self.associatedMKB = associatedMKB
        self.complicationMKB = complicationMKB
        self.fractions = fractions
        self.csgBegDate = csgBegDate
        self.csgEndDate = csgEndDate
        parent = self.parentWidget()
        idList = parent.model().dbdata.idList
        self.setCSGIdList(idList)


    @pyqtSignature('QModelIndex')
    def on_tblCSG_doubleClicked(self, index):
        if index.isValid():
            if (Qt.ItemIsEnabled & self.tableModel.flags(index)):
                csgId = self.tblCSG.currentItemId()
                self.csgd = csgId
                self.emit(SIGNAL('CSGSelected(int)'), csgId)
                self.close()


class CCSGTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.addColumn(CTextCol(u'Код', ['infis'],  20))
        self.addColumn(CTextCol(u'Наименование', ['name'],  40))
        # self.addColumn(CTextCol(u'Описание',        ['note'], 40))
        self.addColumn(CTextCol(u'Коэф. затратоёмкости', ['ksgkoef'], 70))
        self.addColumn(CTextCol(u'Тариф', ['price'], 40))
        self.addColumn(CTextCol(u'МКБ', ['mkb'], 40))
        self.addColumn(CTextCol(u'Соп. МКБ', ['mkb2'], 40))
        self.addColumn(CTextCol(u'МКБ осл.', ['mkb3'], 40))
        self.addColumn(CTextCol(u'Услуга', ['kusl'], 60))
        self.addColumn(CTextCol(u'Критерий', ['KRIT'], 35))
        self.addColumn(CTextCol(u'Фракции', ['fr'], 35))
        self.addColumn(self.CDlitCol(u'Длительность', ['dlit'], 50))
        self.addColumn(self.CAgeCol(u'Возраст', ['age'], 50))

        csgComboBox = parent.parent()
        eventEditor = csgComboBox.eventEditor
        self.contractId = csgComboBox._contractId
        self.mkb = csgComboBox.MKB
        self.associatedMKB = csgComboBox.associatedMKB
        self.complicationMKB = csgComboBox.complicationMKB
        
        self.krit = csgComboBox.krit
                
        # clientAge = eventEditor.clientAge
        self.clientSex = u'М' if csgComboBox.clientSex == 1 else u'Ж'

        self.fractions = csgComboBox.fractions
        self.fractions = forceString(self.fractions) if self.fractions else u''

        self.csgBegDate = csgComboBox.csgBegDate
        self.csgEndDate = csgComboBox.csgEndDate
        if not self.csgBegDate and not self.csgEndDate:
            self.csgBegDate = forceDate(eventEditor.edtBegDate.date())
            self.csgEndDate = forceDate(eventEditor.edtEndDate.date())
        if not self.csgEndDate:
            if not self.csgBegDate:
                self.csgBegDate = forceDate(QDate.currentDate())
            self.csgEndDate = self.csgBegDate

        clientAge = calcAgeTuple(eventEditor.clientBirthDate, self.csgEndDate)
        self.age = []
        if clientAge[0] < 29:
            self.age = ['1', '4', '5']
        elif 29 <= clientAge[0] < 91:
            self.age = ['2', '4', '5']
        elif clientAge[0] >= 91 and clientAge[3] == 0:
            self.age = ['3', '4', '5']
        elif clientAge[3] < 2:
            self.age.extend(['4', '5'])
        elif clientAge[3] < 18:
            self.age.append('5')
        elif clientAge[3] >= 18:
            self.age.append('6')

        duration = getEventDuration(self.csgBegDate, self.csgEndDate, getWeekProfile(getEventWeekProfileCode(eventEditor.eventTypeId)), eventEditor.eventTypeId)

        # duration = self.csgBegDate.daysTo(self.csgEndDate)
        if duration <= 3:
            self.duration = ['1']
        elif 4 <= duration <= 10:
            self.duration = ['2']
        elif 11 <= duration <= 20:
            self.duration = ['3']
        elif duration == 30:
            self.duration = ['5']
        elif 21 <= duration <= 30:
            self.duration = ['4']
        else:
            self.duration = []

        if '5' in self.duration:
            self.duration.append('4')

        self.codeList = [forceString(_) for _ in eventEditor.getServiceActionCode()]

        self.setTable('rbService')
        self.date = QDate.currentDate()

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        column = index.column()
        row    = index.row()
        if role == Qt.DisplayRole and column in (10, 11) and row == 0:
            # чтобы не выводить подпись возраста и длительности для пустой строки
            (col, values) = self.getRecordValues(column, row)
            values[0] = '-1'
            return col.format(values)
        else:
            return CTableModel.data(self, index, role)

    def flags(self, index):
        return Qt.ItemIsEnabled|Qt.ItemIsSelectable

    def setTable(self, table, recordCacheCapacity=300):
        db = QtGui.qApp.db
        tableSpr69 = db.table('soc_spr69').alias('s69')
        tableTariff = db.table('Contract_Tariff')
        self._table = db.forceTable(table)
        self._table = self._table.innerJoin(
            tableSpr69,
            db.joinAnd([
                tableSpr69['ksgkusl'].eq(self._table['infis']),
                tableSpr69['datn'].le(self.csgEndDate),
                db.joinOr([tableSpr69['dato'].ge(self.csgEndDate), tableSpr69['dato'].isNull()]),
                db.joinOr([
                    "'{0}' BETWEEN s69.mkbMin AND s69.mkbMax".format(forceString(self.mkb)),
                    tableSpr69['mkb'].isNull()
                ]),
                db.joinOr([
                    "'{0}' BETWEEN s69.mkb2Min AND s69.mkb2Max".format(forceString(self.associatedMKB)),
                    tableSpr69['mkb2'].isNull()
                ]),
                db.joinOr([
                    "'{0}' BETWEEN s69.mkb3Min AND s69.mkb3Max".format(forceString(self.complicationMKB)),
                    tableSpr69['mkb3'].isNull()
                ]),
                db.joinOr([tableSpr69['KRIT'].inlist(self.krit), tableSpr69['KRIT'].isNull()]),
                db.joinOr([tableSpr69['age'].inlist(self.age), tableSpr69['age'].isNull()]),
                db.joinOr([
                    u"(cast('{0}' AS INT) BETWEEN cast(SUBSTRING_INDEX(REPLACE(s69.`fr`, 'fr', ''), '-', 1) AS INT) AND cast(SUBSTRING_INDEX(REPLACE(s69.`fr`, 'fr', ''), '-', -1) as INT))".format(self.fractions),
                    tableSpr69['fr'].isNull()
                ]),
                db.joinOr([tableSpr69['kusl'].inlist(self.codeList), tableSpr69['kusl'].isNull()]),
                db.joinOr([tableSpr69['dlit'].inlist(self.duration), tableSpr69['dlit'].isNull()]),
                db.joinOr([tableSpr69['pol'].eq(self.clientSex), tableSpr69['pol'].isNull()])
            ])
        )
        self._table = self._table.leftJoin(
            tableTariff, db.joinAnd([
                tableTariff['service_id'].eq(self._table['id']),
                tableTariff['master_id'].eq(self.contractId),
                tableTariff['begDate'].le(self.csgEndDate),
                db.joinOr([tableTariff['endDate'].ge(self.csgEndDate), tableTariff['endDate'].isNull()])
            ])
        )
        loadFields = [self.idFieldName]
        loadFields.extend(self._loadFields)
        for col in self._cols:
            loadFields.extend(col.fields())
        loadFields = set(loadFields)
        if '*' in loadFields:
            loadFields = '*'
        else:
            loadFields = ', '.join([self._table[fieldName].name() for fieldName in loadFields])
        self._recordsCache = CTableRecordCache(db, self._table, loadFields, recordCacheCapacity)


    class CAgeCol(CTextCol):
        def format(self, values):
            age = forceString(values[0])
            if age == '1':
                return u'от 0 до 28 дней (или новорожденный)'
            elif age == '2':
                return u'от 29 дней до 90 дней'
            elif age == '3':
                return u'от 91 дня до 1 года'
            elif age == '4':
                return u'от 0 дней до 2 лет'
            elif age == '5':
                return u'от 0 дней до 18 лет'
            elif age == '6':
                return u'старше 18 лет'
            elif age == '-1':
                return u''
            else:
                return u'не учитывается'

    class CDlitCol(CTextCol):
        def format(self, values):
            dlit = forceString(values[0])
            if dlit == '1':
                return u'от 1 до 3 дней'
            elif dlit == '2':
                return u'от 4 до 10 дней'
            elif dlit == '3':
                return u'от 11 до 20 дней'
            elif dlit == '4':
                return u'от 21 до 30 дней'
            elif dlit == '5':
                return u'30 дней'
            elif dlit == '-1':
                return u''
            else:
                return u'не учитывается'
