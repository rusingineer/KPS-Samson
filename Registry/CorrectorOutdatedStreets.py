# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2025 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from itertools import groupby
from operator import itemgetter
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt, QAbstractTableModel, QVariant, pyqtSignature, SIGNAL

from KLADR.KLADRModel import getCityName, getStreetName
from library.DialogBase import CDialogBase
from Ui_CorrectorOutdatedStreets import Ui_CorrectorOutdatedStreetsDialog
from library.Utils import forceString, forceInt, toVariant, forceDate
from Registry.Utils import getAddressId
from KLADR.kladrComboxes import CStreetComboBox, CKLADRComboBox


class CProgressSaveData(CDialogBase):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.parent = parent
        self.setObjectName('progressSaveData')
        self.setWindowTitle(u"Идет сохранение изменений")
        self.layoutWidget = QtGui.QWidget(self)
        self.layoutWidget.setGeometry(QtCore.QRect(10, 20, 291, 52))
        self.layoutWidget.setObjectName("layoutWidget")
        self.gridLayout = QtGui.QGridLayout(self.layoutWidget)
        self.gridLayout.setMargin(0)
        self.gridLayout.setObjectName("gridLayout")
        self.progressBar = QtGui.QProgressBar(self.layoutWidget)
        self.progressBar.setMaximum(100)
        self.progressBar.setProperty("value", 1)
        self.progressBar.setTextVisible(False)
        self.progressBar.setFormat("")
        self.progressBar.setObjectName("progressBar")
        self.gridLayout.addWidget(self.progressBar, 0, 0, 1, 2)
        spacerItem = QtGui.QSpacerItem(188, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 1, 0, 1, 1)
        self.btnCancel = QtGui.QPushButton(self.layoutWidget)
        self.btnCancel.setObjectName("btnCancel")
        self.gridLayout.addWidget(self.btnCancel, 1, 1, 1, 1)
        self.btnCancel.setText(u"Прервать")
        self.connect(self.btnCancel, SIGNAL('clicked()'), self.on_btnCancel_clicked)

    @pyqtSignature('')
    def on_btnCancel_clicked(self):
        self.parent.stopRecUpdated()
        self.progressBar.setValue(0)
        self.close()

    def setProgress(self, value):
        self.progressBar.setValue(value)


class CCorrectorOutdatedStreets(CDialogBase, Ui_CorrectorOutdatedStreetsDialog):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.resize(1360, 760)
        self.setWindowTitle(u'Корректор неактуальных улиц в картах пациентов')

        self.addObject('actCopyKLADR', QtGui.QAction(u'Копировать код КЛАДР', self))
        self.actCopyKLADR.triggered.connect(self.copyKLADRCode)
        self.ctrlCopyKLADR = QtGui.QShortcut(QtGui.QKeySequence('Ctrl+C'), self)
        self.connect(self.ctrlCopyKLADR, SIGNAL('activated()'), self.copyKLADRCode)

        self.addModels('Street', CStreetModel(self))
        self.setModels(self.tbl, self.modelStreet, self.selectionModelStreet)
        self.KLADRDelegate = CReplaceAddress(self)
        self.tbl.setItemDelegateForColumn(5, self.KLADRDelegate)
        self.tbl.createPopupMenu([self.actCopyKLADR])

        self.cmbAddress.setCode(QtGui.qApp.defaultKLADR())
        self.connect(self.cmbAddress, SIGNAL('currentIndexChanged(int)'), self.setFocusInFind)

        self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setText(u"Заменить")

        self.btnUpdate.setFocus()
        self.recUpdated = False

    def setFocusInFind(self):
        if self.cmbAddress.code() != QtGui.qApp.defaultKLADR():
            self.btnUpdate.setFocus()

    @pyqtSignature('QAbstractButton*')
    def on_buttonBox_clicked(self, button):
        self.tbl.setCurrentIndex(self.modelStreet.index(0, 0))
        buttonCode = self.buttonBox.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Ok:
            numClient = self.modelStreet.getLenEditItems()
            if numClient != 0 and self.recUpdated == False:
                allEdit = self.modelStreet.isAllEdit()
                if allEdit:
                    res = QtGui.QMessageBox.warning(
                        self,
                        u'Внимание!',
                        u'''В регистрационных картах {0} (кол-во уникальных карт) пациентов будут изменены улицы. 
                        \nВы не поправили следующие улицы: {1}
                        \nОни не будут затронуты при редактировании.
                        \nВнесенные изменения отменить невозможно.
                        \n\nПродолжить ?'''.format(
                            numClient,
                            u', '.join(allEdit)),
                        QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel,
                        QtGui.QMessageBox.Cancel)
                else:
                    res = QtGui.QMessageBox.warning(
                        self,
                        u'Внимание!',
                        u'''В регистрационных картах {0} (кол-во уникальных карт) пациентов будут изменены улицы.
                        \n\nВнесенные изменения отменить невозможно 
                        \n\nПродолжить ?'''.format(numClient),
                        QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel,
                        QtGui.QMessageBox.Cancel)
                if res == QtGui.QMessageBox.Yes:
                    dlg = CProgressSaveData(self)
                    dlg.show()

                    status = self.modelStreet.saveData(dlg.setProgress)

                    dlg.hide()

                    if status == True:
                        self.recUpdated = True
                        QtGui.QMessageBox.warning(
                            self,
                            u'Внимание!',
                            u'Все изменения улиц были успешно внесенны.',
                            QtGui.QMessageBox.Ok)
                    else:
                        QtGui.QMessageBox.warning(
                            self,
                            u'Внимание!',
                            u'Произошла ошибка при внесении изменений. Все правки были отменены. \n\nОшибка: {0}'.format(status),
                            QtGui.QMessageBox.Ok)
            else:
                QtGui.QMessageBox.warning(
                    self,
                    u'Внимание!',
                    u'Не найдены регистрационные карты для выполнения замены. Вероятно замена уже была проведена. Обновите список неактуальных улиц в окне сервиса.',
                    QtGui.QMessageBox.Ok)

        elif buttonCode == QtGui.QDialogButtonBox.Close:
            self.close()

    @pyqtSignature('')
    def on_btnUpdate_clicked(self):
        self.recUpdated = False
        code = self.cmbAddress.code()
        street = self.edtStreet.text()
        self.modelStreet.loadData(code, street)
        self.modelStreet.sort(1, Qt.AscendingOrder)
        self.lblInfo.setText(u'Всего записей: {0}'.format(self.modelStreet.getLen()))

    @pyqtSignature('QString')
    def on_edtStreet_textChanged(self, text):
        self.modelStreet.filter(text)

    def copyKLADRCode(self):
        if self.modelStreet.getLen() != 0:
            currentRow = self.tbl.currentIndex().row()
            code = self.modelStreet.getItems(currentRow).get('code')
            clipBoard = QtGui.qApp.clipboard()
            clipBoard.setText(code)

    def stopRecUpdated(self):
        self.recUpdated = False
        self.modelStreet.stopRecUpdated()


class CStreetModel(QAbstractTableModel):
    headers = [u'Населенный пункт', u'Наименование улицы', u'Тип улицы', u'Код КЛАДР', u'Количество пациентов', u'Заменить на']
    def __init__(self, parent):
        QAbstractTableModel.__init__(self, parent)
        self._items = []
        self.items = []
        self.street = None
        self.recUpdated = False
        self.edtClient = []
        self._map = {}

    def columnCount(self, index = None):
        return len(self.headers)

    def rowCount(self, index = None):
        return len(self.items)

    def getLen(self):
        return len(self.items)

    def getLenItems(self):
        return len(self._items)

    def getLenEditItems(self):
        num = 0
        for val in self._items:
            if val.get('repCity') and val.get('repStreet'):
                num = num + val.get('num')
        return num

    def flags(self, index):
        column = index.column()
        if column in (0, 1, 2, 3, 4):
            return Qt.ItemIsSelectable|Qt.ItemIsEnabled
        elif column == 5:
            return Qt.ItemIsSelectable|Qt.ItemIsEnabled|Qt.ItemIsEditable

    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return QVariant(CStreetModel.headers[section])
        return QVariant()

    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if role == Qt.DisplayRole:
            item = self.items[row]
            if column in (0, 1, 2, 3, 4):
                return QVariant(item[column])
            elif column == 5:
                if item[column][0] in self._map:
                    city = self._map[item[column][0]]
                else:
                    city = getCityName(item[column][0]) if item[column][0] else u''
                    self._map[item[column][0]] = city

                if item[column][1] in self._map:
                    street = self._map[item[column][1]]
                else:
                    street = getStreetName(item[column][1]) if item[column][1] else u''
                    self._map[item[column][1]] = street
                return QVariant(u'%s %s' % (city, street))
        return QVariant()

    def getAddress(self, addressType, clientId, newStreet, newKladr):
        db = QtGui.qApp.db
        number = None
        corpus = None
        flat = None
        freeInput = None
        livingArea = None
        addressDate = None
        resident = None

        stmt = """
select 
	ah.`number`
,	ah.corpus
,	a.flat
, 	ca.freeInput
,	ca.livingArea
,	ca.addressDate
,	ca.resident
from ClientAddress ca
left join Address a on a.id = ca.address_id 
left join AddressHouse ah on ah.id = a.house_id
where ca.id = (
	select 
		max(ClientAddress.id) 
	from ClientAddress 
	where ClientAddress.deleted=0  
		AND ClientAddress.type={0} 
		AND ClientAddress.client_id={1}
	);""".format(addressType, clientId)
        query = db.query(stmt)
        while query.next():
            record = query.record()
            number = forceString(record.value('number'))
            corpus = forceString(record.value('corpus'))
            flat = forceString(record.value('flat'))
            freeInput = forceString(record.value('freeInput'))
            livingArea = forceInt(record.value('livingArea'))
            addressDate = forceDate(record.value('addressDate'))
            resident = forceInt(record.value('resident'))

        return { 'useKLADR'         : True,             # True

                 'KLADRCode'        : newKladr,         #  AddressHouse
                 'KLADRStreetCode'  : newStreet,        #  AddressHouse
                 'number'           : number,           #  AddressHouse
                 'corpus'           : corpus,           #  AddressHouse

                 'flat'             : flat,             #  Address

                 'freeInput'        : freeInput,        #  ClientAddress
                 'livingArea'       : livingArea,       #  ClientAddress
                 'addressDate'      : addressDate,      #  ClientAddress
                 'resident'         : resident}         #  ClientAddress

    def saveData(self, setProgress=None):
        db = QtGui.qApp.db
        self.recUpdated = True
        maxClient = self.getLenEditItems()

        db.transaction()
        try:
            for idx, val in enumerate(self.edtClient):
                valueNew = [i for i in self._items if i.get('code') == val.get('street')][0]
                if valueNew.get('repCity') and valueNew.get('repStreet'):
                    address = self.getAddress(val.get('type'), val.get('clientId'), valueNew.get('repStreet'), valueNew.get('repCity'))
                    addressId = getAddressId(address)

                    record = db.record('ClientAddress')
                    record.setValue('client_id',  toVariant(val.get('clientId')))
                    record.setValue('type',       toVariant(val.get('type')))
                    record.setValue('address_id', toVariant(addressId))
                    record.setValue('freeInput',  toVariant(address['freeInput']))
                    record.setValue('livingArea', toVariant(None))
                    record.setValue('addressDate', toVariant(address['addressDate']))
                    if val.get('type') == 1:
                        if address['resident'] == 0:
                            record.setValue('resident', toVariant(None))
                        elif address['resident'] == 1:
                            record.setValue('resident', toVariant(0))
                        elif address['resident'] == 2:
                            record.setValue('resident', toVariant(1))
                    db.insertOrUpdate('ClientAddress', record)

                prgrs = int((float(idx) / float(maxClient))*float(100))
                setProgress(prgrs)
                QtGui.qApp.processEvents()

                if self.recUpdated == False:
                    raise Exception(u'Сохранение записей было отменено')
        except Exception as e:
            db.rollback()
            return e
        else:
            db.commit()
            return True

    def stopRecUpdated(self):
        self.recUpdated = False


    def isAllEdit(self):
        noEdit = []
        for val in self._items:
            if val.get('repCity') and val.get('repStreet'):
                pass
            else:
                noEdit.append(val.get('street'))
        return noEdit

    def itemsClear(self):
        self.edtClient = []
        self._items = []
        self.items = []

    def getItems(self, row):
        recId = self.getIdRecByRow(row)
        item = [val for val in self._items if val.get('id') == recId][0]
        idx = self._items.index(item)
        return self._items[idx]

    def setItem(self, row, column, value):
        recId = self.getIdRecByRow(row)
        if column == 5:
            item = [val for val in self._items if val.get('id') == recId][0]
            idx = self._items.index(item)
            newItem = self._items[idx]
            newItem['repCity'] = value[0]
            newItem['repStreet'] = value[1]

            self.items[row][column] = [value[0], value[1]]
            self._items[idx] = newItem

        self.reset()

    def getIdRecByRow(self, row):
        listShow = [val.get('id') for val in self._items if val.get('isShow') == True]
        return listShow[row]

    def loadData(self, address=None, street=None):
        db = QtGui.qApp.db
        idRec = 0
        values = []
        self.itemsClear()
        stmt = """
select 
    k.NAME as kName
,   k.SOCR as ksocr
,   s.NAME as street
,   s.SOCR as typeStreet
,   ah.KLADRStreetCode as code
,   c.id as clientId
,   ca.type as caType
from Client c
left join ClientAddress ca on ca.id = (select max(ClientAddress.id) from ClientAddress where ClientAddress.deleted = 0  AND ClientAddress.type=0 AND ClientAddress.client_id=c.id)
left join Address a on a.id = ca.address_id 
left join AddressHouse ah on ah.id = a.house_id
left join kladr.KLADR k on k.CODE = ah.KLADRCode
left join kladr.STREET s on s.CODE = ah.KLADRStreetCode 
where c.deleted = 0
    AND ca.deleted = 0
    AND a.deleted = 0
    AND a.deleted = 0
    AND s.CODE is not null
    AND (s.IS_ACTUAL = 0 OR s.IS_ACTUAL is null)
    AND ah.KLADRCode = {0}

UNION

select 
    k.NAME as kName
,   k.SOCR as ksocr 
,   s.NAME as street
,   s.SOCR as typeStreet
,   ah.KLADRStreetCode as code
,   c.id as clientId
,   ca.type as caType
from Client c
left join ClientAddress ca on ca.id = (select max(ClientAddress.id) from ClientAddress where ClientAddress.deleted = 0  AND ClientAddress.type=1 AND ClientAddress.client_id=c.id)
left join Address a on a.id = ca.address_id 
left join AddressHouse ah on ah.id = a.house_id
left join kladr.KLADR k on k.CODE = ah.KLADRCode
left join kladr.STREET s on s.CODE = ah.KLADRStreetCode 
where c.deleted = 0
    AND ca.deleted = 0
    AND a.deleted = 0
    AND a.deleted = 0
    AND s.CODE is not null
    AND (s.IS_ACTUAL = 0 OR s.IS_ACTUAL is null) 
    AND ah.KLADRCode = {0};""".format(address)
        query = db.query(stmt)
        while query.next():
            record = query.record()
            idRec = idRec + 1
            kName = forceString(record.value('kName'))
            ksocr = forceString(record.value('ksocr'))
            recStreet = forceString(record.value('street'))
            typeStreet = forceString(record.value('typeStreet'))
            code = forceString(record.value('code'))
            clientId = forceInt(record.value('clientId'))
            caType = forceString(record.value('caType'))

            values.append([idRec, kName, ksocr, recStreet, typeStreet, code, clientId, caType])

        values.sort(key=itemgetter(1, 2, 3, 4, 5))
        idRec = 0

        for key, group in groupby(values, key=itemgetter(1, 2, 3, 4, 5)):
            liGroup = list(group)

            for cb in liGroup:
                self.edtClient.append({'street': cb[5], 'clientId': cb[6], 'type': cb[7]})

            idRec = idRec + 1

            self._items.append({
                'id': idRec,
                'city': u"{0} {1}".format(liGroup[0][1], liGroup[0][2]),
                'street': liGroup[0][3],
                'type': liGroup[0][4],
                'code': liGroup[0][5],
                'num': len(list(set([i[6] for i in liGroup]))),
                'repCity': address,
                'repStreet': None,
                'isShow': True
            })

        self.filter(street)

    def showAll(self):
        for val in self._items:
            val['isShow'] = True

    def filter(self, street=None):
        self.showAll()
        self.items = []
        self.street = street

        for val in self._items:
            if street:
                if forceString(street).lower() in forceString(val['street']).lower():
                    val['isShow'] = True
                else:
                    val['isShow'] = False

            if val.get('isShow'):
                self.items.append(
                    [
                        val.get('city'),
                        val.get('street'),
                        val.get('type'),
                        val.get('code'),
                        val.get('num'),
                        [val.get('repCity'), val.get('repStreet')]
                    ])

        self.reset()

    def sort(self, column, order=Qt.AscendingOrder):
        clmn = ['city', 'street', 'type', 'code', 'num', 'repStreet']
        reverse = order == Qt.DescendingOrder

        if column in (0, 1, 2, 5):
            self._items.sort(key=lambda x: forceString(x[clmn[column]]).lower() if x else None, reverse=reverse)
            self.items.sort(key=lambda x: forceString(x[column]).lower() if x else None, reverse=reverse)
        elif column in (3, 4):
            self._items.sort(key=lambda x: forceInt(x[clmn[column]]) if x else None, reverse=reverse)
            self.items.sort(key=lambda x: forceInt(x[column]) if x else None, reverse=reverse)

        self.reset()


class CReplaceAddress(QtGui.QItemDelegate):
    def __init__(self, parent):
        QtGui.QItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        self.container = QtGui.QWidget(parent)

        self.horizontalLayout = QtGui.QHBoxLayout(parent)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.horizontalLayout.setSpacing(5)
        self.horizontalLayout.setContentsMargins(1, 1, 1, 1)
        self.cmbAddress = CKLADRComboBox(parent)
        self.cmbAddress.setObjectName("cmbAddress")
        self.horizontalLayout.addWidget(self.cmbAddress)
        self.cmbSreet = CStreetComboBox(parent)
        self.cmbSreet.setObjectName("cmbSreet")
        self.horizontalLayout.addWidget(self.cmbSreet)

        self.connect(self.cmbAddress, SIGNAL('currentIndexChanged(int)'), self.on_cmbAddress)

        self.container.setLayout(self.horizontalLayout)

        return self.container

    def on_cmbAddress(self, index):
        code = self.cmbAddress.code()
        self.cmbSreet.setCity(code)

    def setEditorData(self, editor, index):
        value = index.model().getItems(index.row())
        if value.get('repCity'):
            self.cmbAddress.setCode(value.get('repCity'))

    def setModelData(self, editor, model, index):
        index.model().setItem(index.row(), index.column(), [self.cmbAddress.code(), self.cmbSreet.code()])

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)
