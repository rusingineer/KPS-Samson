# -*- coding: utf-8 -*-

from PyQt4.QtCore import Qt, QObject, SIGNAL, QVariant, pyqtSignature, QAbstractTableModel
from PyQt4 import QtGui

from library.DialogBase import CDialogBase
from library.Utils import forceRef, forceString, anyToUnicode

from Ui_HospitalOrderSelectDialog import Ui_HospitalOrderSelectDialog

import Exchange.AttachService as AttachService

class CHospitalOrderSelectDialog(CDialogBase, Ui_HospitalOrderSelectDialog):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.bedProfileId = None
        self.usok = None
        self.organisationId = None
        self.addModels('CKDInformation', CCKDInformationModel(self))

        self.setupUi(self)
        self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(False)
        self.cmbHospitalBedProfile.setTable('rbHospitalBedProfile', addNone=True)

        view = self.tblCKDInformation
        h = view.fontMetrics().height()
        view.verticalHeader().setDefaultSectionSize(3*h/2)
        self.setModels(view, self.modelCKDInformation, self.selectionModelCKDInformation)
        QObject.connect(view.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.sortData)
        QObject.connect(view, SIGNAL("doubleClicked(QModelIndex)"),	self.on_ModelCKDInformationItem_doubleClicked)
        self.colSorting = {}
       
        
    def sortData(self, column):
        col = self.modelCKDInformation._columns[column]
        preOrder = self.colSorting.get(column, None)
        self.colSorting[column] = 1 if preOrder is not None and preOrder != 1 else 0
        self.modelCKDInformation.order = [col[0], self.colSorting[column]]
        self.modelCKDInformation.sort()
        header = self.tblCKDInformation.horizontalHeader()
        header.setSortIndicatorShown(True)
        header.setSortIndicator(column, Qt.AscendingOrder if not self.colSorting[column] else Qt.DescendingOrder)
   

    def updateCKDInformation(self):
        self.tblCKDInformation.setEnabled(False)
        QtGui.qApp.setWaitCursor()
        self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(False)
        QtGui.qApp.processEvents()
        try:
            id = self.cmbHospitalBedProfile.value()
            regionalCode = QtGui.qApp.db.translate('rbHospitalBedProfile', 'id', forceRef(id), 'regionalCode')
            self.modelCKDInformation.update(regionalCode)
            self.tblCKDInformation.setEnabled(True)
        except Exception, e:
            QtGui.QMessageBox.critical(self, u'Ошибка', anyToUnicode(str(e)), QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)
        finally:
            QtGui.qApp.restoreOverrideCursor()

    @pyqtSignature('int')
    def on_cmbHospitalBedProfile_currentIndexChanged(self, index):
        self.bedProfileId = self.cmbHospitalBedProfile.value()
        self.updateCKDInformation()

    @pyqtSignature('')
    def on_btnRefresh_clicked(self):
        self.updateCKDInformation()

    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelCKDInformation_currentChanged(self, current, previous):
        self.organisationId = None
        if current.isValid():
            rowIndex = current.row()
            row = self.modelCKDInformation.getRow(rowIndex)
            self.organisationId = row and row.get('organisationId')
            self.usok = row and row.get('usok')
        self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(self.organisationId is not None)
        
    
    @pyqtSignature('QModelIndex')
    def on_ModelCKDInformationItem_doubleClicked(self, index):
        self.buttonBox.emit(SIGNAL('accepted()'))


class CCKDInformationModel(QAbstractTableModel):
    def __init__(self, parent):
        QAbstractTableModel.__init__(self, parent)
        self._rows = []
        self._columns = [
            ('moCode',       u'Код ОМС',      Qt.AlignLeft),
            ('lpuName',      u'Наименование ЛПУ', Qt.AlignLeft),
            ('usok',         u'Тип стационара', Qt.AlignLeft),
            ('menBeds',      u'Мужских коек', Qt.AlignRight),
            ('womenBeds',    u'Женских коек', Qt.AlignRight),
            ('childrenBeds', u'Детских коек', Qt.AlignRight)
        ]
        self.order = ['moCode', 0]
   

    def columnCount(self, index = None):
        return len(self._columns)

    def rowCount(self, index = None):
        return len(self._rows)

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        column = self._columns[index.column()]
        row    = self._rows[index.row()]
        if role == Qt.DisplayRole:
            field = column[0]
            value = row[field]
            return QVariant(value)
        elif role == Qt.TextAlignmentRole:
            return QVariant(column[2] + Qt.AlignVCenter)
        return QVariant()

    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._columns[section][1]
        else:
            return QVariant()

    def update(self, code):
        self.clear()
        try:
            if code is not None:
                code = forceString(code)
                response = AttachService.getCKDInformationByKpk(code)
                if response['ok']:
                    if 'ckdlist' in response:
                        for infoElement in response['ckdlist']:
                            row = {}
                            row['moCode'] = moCode = infoElement.get('mo')
                            if moCode is not None:
                                organisation = QtGui.qApp.db.getRecordEx('Organisation', ['id', 'fullName'], where = ("isActive = 1 and isInsurer = 0 and deleted = 0 and infisCode = '%s'" % moCode))
                            else:
                                organisation = None
                            row['organisationId'] = organisation and forceRef(organisation.value('id'))
                            row['lpuName'] = organisation and forceString(organisation.value('fullName'))
                            row['usok'] = u'круглосуточный' if infoElement['usok'] == '1' else u'дневной'
                            row['menBeds'] = infoElement['freeBedsMen']
                            row['womenBeds'] = infoElement['freeBedsWomen']
                            row['childrenBeds'] = infoElement['freeBedsChildren']
                            self.addRow(row)
                else:
                    raise Exception(response['message'])
        except Exception, e:
            raise e
        finally:
            self.sort()
            self.reset()


    def addRow(self, row):
        self._rows.append(row)
        
    def sort(self):
        self._rows.sort(key = lambda(row): row[self.order[0]], reverse=self.order[1])
        self.reset()

    def getRow(self, index):
        return self._rows[index]

    def clear(self):
        self._rows = []
