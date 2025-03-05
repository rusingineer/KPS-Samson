# -*- coding: utf-8 -*-

from PyQt4 import QtGui
from PyQt4.QtCore import *

from library.TableModel import *
from library.Utils import *

from Ui_MedServiceProfilesDialog import *
from library.DialogBase import CDialogBase
from addServiceProfiles import CMedServiceProfileDialog
from Utils import warninWindow
from UOServiceClient import CUOServiceClient
from library.database             import CTableRecordCache


class CMedServiceProfiles(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self.addColumn(CTextCol(u'Адрес', ['addres'], 10))
        self.addColumn(CTextCol(u'Телефон', ['phone'], 10))
        self.addColumn(CTextCol(u'Сайт', ['site'], 10))
        self.addColumn(CTextCol(u'Статус', ['STATUS'], 10))
        self.addColumn(CTextCol(u'Профиль', ['prof'], 10))
        self.addColumn(CTextCol(u'Дата начала', ['startDate'], 10))
        self.addColumn(CTextCol(u'Дата окончания', ['endDate'], 10))
        self.addColumn(CTextCol(u'Комментарий', ['comment'], 10))
        self.setTable()

    def setTable(self):
        db = QtGui.qApp.db
        tabMedServiceProfiles = db.table('MedServiceProfiles')
        tabrbMedicalAidProfile = db.table(db.db.databaseName() + '.`v1.2.643.2.69.1.1.1.56`').alias('rbNetrikaProfileUO')
        tabOrgStructure = db.table('OrgStructure')
        loadFields = []
        loadFields.append(u''' MedServiceProfiles.address AS addres,
                                 MedServiceProfiles.contactValue AS phone,
                                 MedServiceProfiles.site AS site,
                                 DATE_FORMAT(MedServiceProfiles.startDate, '%Y-%m-%d') as startDate,
                                 DATE_FORMAT(MedServiceProfiles.endDate, '%Y-%m-%d') as endDate,
                                 rbNetrikaProfileUO.name AS prof,
                              
                                 MedServiceProfiles.comment AS comment,
                            
                                 case when date(MedServiceProfiles.endDate) < date(NOW()) then 'Не активен'
                                        when MedServiceProfiles.accepted = 0  then 'Не выгружено' 
                                        when MedServiceProfiles.acceptModify = 0 AND MedServiceProfiles.modifyDatetime <> '0000-00-00 00:00:00'  then 'Не обновлено'
                                        when MedServiceProfiles.accepted = 1 OR MedServiceProfiles.acceptModify = 1 then 'Актуально' 
                                        ELSE 'Не выгружено'  END AS STATUS''')
        queryTable = tabMedServiceProfiles.leftJoin(tabrbMedicalAidProfile, '''rbNetrikaProfileUO.id = MedServiceProfiles.master_id''')
        queryTable = queryTable.leftJoin(tabOrgStructure, '''OrgStructure.id = MedServiceProfiles.targetMo''')

        self._table = queryTable
        self._recordsCache = CTableRecordCache(db, self._table, loadFields)

    def data(self, index, role):
        if role == Qt.BackgroundColorRole:
            record = self.getRecordByRow(index.row())
            if forceString(record.value('STATUS')) == u'Не активен':
                return toVariant(QtGui.QColor(255, 192, 203))  # красный
            elif forceString(record.value('STATUS')) == u'Не выгружено':
                return toVariant(QtGui.QColor(255, 127, 80))  # Оранжевый
            elif forceString(record.value('STATUS')) == u'Не обновлено':
                return toVariant(QtGui.QColor(32, 178, 170))  # синий
            elif forceString(record.value('STATUS')) == u'Актуально':
                return toVariant(QtGui.QColor(127, 255, 0))  # зелёный
            else:
                return QVariant()
        else:
            return CTableModel.data(self, index, role)


class CMedServiceProfilesDialog(CDialogBase, Ui_MedServiceProfilesDialog):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.addObject('mnuItems', QtGui.QMenu(self))
        self.addObject('actAdd', QtGui.QAction(u'Добавить', self))
        self.addObject('actEdit', QtGui.QAction(u'Изменить', self))
        self.mnuItems.addAction(self.actAdd)
        self.mnuItems.addAction(self.actEdit)
        self.mnuItems.addSeparator()
        self.addModels('MedServiceProfiles', CMedServiceProfiles(self))
        self.setupUi(self)
        self.setModels(self.tblViewMedProfiles, self.modelMedServiceProfiles, self.selectionModelMedServiceProfiles)
        self.tblViewMedProfiles.setPopupMenu(self.mnuItems)
        self.reset()
    #
    def state_changed(self, int):
        self.reset()

    def reset(self):
        db = QtGui.qApp.db
        med = db.table('MedServiceProfiles')
        cond = []
        idList = db.getIdList(med, '*', where=cond)
        self.tblViewMedProfiles.setIdList(idList)

    def editMedicalServiceProfile(self, medicalServiceProfileId):
        self.typeEv = 1
        if medicalServiceProfileId:
            db = QtGui.qApp.db
            med = db.table('MedServiceProfiles')
            cond = [med['id'].eq(medicalServiceProfileId)]
            record = db.getRecordEx(med, '*', where=cond)
            dialog = CMedServiceProfileDialog(self)
            dialog.setRecord(record)
            dialog.exec_()
        self.reset()

    @pyqtSignature('QModelIndex')
    def on_tblViewMedProfiles_doubleClicked(self, index):
        self.editMedicalServiceProfile(self.tblViewMedProfiles.currentItemId())

    @pyqtSignature('')
    def on_actEdit_triggered(self):
        self.editMedicalServiceProfile(self.tblViewMedProfiles.currentItemId())
        self.reset()

    @pyqtSignature('')
    def on_actAdd_triggered(self):
        self.typeEv = 0
        CMedServiceProfileDialog(self).exec_()
        self.reset()


    @pyqtSignature('')
    def on_btnSend_clicked(self):
        id = self.tblViewMedProfiles.currentItemId()
        if id is None:
            warninWindow(u'Требуется создать профиль УО.')
            return 
        client = CUOServiceClient()
        try:
            client.updatemedserviceprofile(id)
            warninWindow(u'Направление успешно добавлено\обновленно')
        except Exception, e:
            QtGui.QMessageBox.critical(self,
                                       u'Ошибка при регистрации профиля',
                                       exceptionToUnicode(e),
                                       QtGui.QMessageBox.Ok,
                                       QtGui.QMessageBox.Ok)

        self.reset()


