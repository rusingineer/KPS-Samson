# -*- coding: utf-8 -*-

from PyQt4 import QtGui
from PyQt4.QtCore import *
import uuid
from library.TableModel import *
from library.Utils import *

from Ui_ferzlDialog import *
from library.DialogBase import CDialogBase
from library.database import CTableRecordCache
from Registry.Ferzl_service import Ferzl_service
from Registry.ClientEditDialog  import CClientEditDialog
from datetime import datetime


class CferzlDialog(CDialogBase, Ui_ferzlDialog):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.res = {'clientId': 0 }
        self.setupUi(self)
        self.model = QtGui.QStandardItemModel()
        self.model.setHorizontalHeaderLabels([u"ФИО", u"Дата рождения", u"Пол", u"ЕНП"])
        self.tableView.setModel(self.model)
        self.tableView.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.tableView.setEnabled(False)
        self.btnAdd.setEnabled(True)


    @pyqtSignature('')
    def on_btnClose_clicked(self):
        self.close()


    @pyqtSignature('int')
    def on_cmbRbDoc_currentIndexChanged(self, index):
        self.seria.clear()
        self.number.clear()
        self.model.removeRows(0, self.model.rowCount())
        index = self.cmbRbDoc.currentIndex()
        if index == 5:
            self.seria.setEnabled(False)
        elif index == 6:
            self.seria.setEnabled(False)
        elif index == 8:
            self.seria.setEnabled(False)
        elif index == 9:
            self.seria.setEnabled(False)
        else:
            self.seria.setEnabled(True)


    @pyqtSignature('')
    def on_btnSearch_clicked(self):
        param_dict = {'external_id':str(uuid.uuid4())}
        type = self.cmbRbDoc.currentIndex()
        if len(str(self.number.text())) == 0:
            warninWindow(u'Не заполненно поле "Номер"!')
            return
        # Документы без серии 
        if type in (5, 6, 8, 9, 3, 4, 7):
            pcyNum = str(self.number.text())  # преобразуем QString в str
            if not pcyNum.isdigit():
                warninWindow(u'Поле "Номер" должно содержать только цифры!')
                self.btnAdd.setEnabled(False)
                return
            param_dict['enp'] = pcyNum
        elif type == 2: # для полисов возможно имеющих серию, не нашёл точной инфомации
            # pcyType = None, enp = None, pcySer = None, pcyNum = None
            pcySer = str(self.seria.text())
            pcyNum = str(self.number.text())
            if pcySer == '':
                pass
            else:
                param_dict['pcySer'] = pcySer
            if not pcyNum.isdigit():
                warninWindow(u'Поле "Номер" должно содержать только цифры!')
                self.btnAdd.setEnabled(False)
                return
            param_dict['pcyType'] = typePolicy(forceInt(self.cmbRbDoc.currentIndex()))
            # param_dict['enp'] = pcyNum
            param_dict['pcyNum'] = pcyNum
        # паспорт\свидетельство
        elif type in (0, 1):
            seria = forceString(self.seria.text())
            if type == 0:
                seria = validate_seria(seria)
                if seria == -1:
                    warninWindow(u'Поле "Серия" заполнено некорректно, введите "ХХХХ" или "ХХ ХХ"!')
                    return 
            if type == 0:
                param_dict['dudlType'] = 14
            elif type == 1:
                param_dict['dudlType'] = 3
            param_dict['dudlSer'] = seria
            param_dict['dudlNum'] = str(self.number.text())
        else:
            warninWindow(u'Не установленный документ!')
            self.btnAdd.setEnabled(False)
            return

        service = Ferzl_service()
        try:
            result_service = service.getfindPersonsByPersCriteria(param_dict)
        except:
            warninWindow(u'Произошла ошибка сервсиа ФЕРЗЛ!')
            return
        if 'massage' in result_service:
            warninWindow(u'{0}'.format(result_service['massage']))
            self.btnAdd.setEnabled(False)
            return
        if len(result_service['person']) == 0:
            warninWindow(u'Пациент не найден!')
            self.btnAdd.setEnabled(False)
            return
        self.model.clear()
        self.model.setHorizontalHeaderLabels([u"ФИО", u"Дата рождения", u"Пол", u"ЕНП"])
        for person in result_service['person']:
            fio = person.get('fio', '')
            birth = person.get('birthDay', '')
            gender_code = person.get('gender', '0')
            enp = person.get('enp', '')

            if gender_code == '1':
                gender_text = u"м"
            elif gender_code == '2':
                gender_text = u"ж"
            else:
                gender_text = u"Не известно"

            row_items = [
                QtGui.QStandardItem(fio),
                QtGui.QStandardItem(birth),
                QtGui.QStandardItem(gender_text),
                QtGui.QStandardItem(enp)
            ]
            self.model.appendRow(row_items)
        self.tableView.setEnabled(True)
        self.tableView.resizeColumnsToContents()
        self.btnAdd.setEnabled(True)


    @pyqtSignature('')
    def on_btnAdd_clicked(self):
        model = self.tableView.model()
        if model is None:
            warninWindow(u"Таблица пуста")
            return
        selection_model = self.tableView.selectionModel()
        if not selection_model.hasSelection():
            warninWindow(u"Не выбрана ни одна строка!")
            return
        current_index = selection_model.currentIndex()
        if not current_index.isValid():
            warninWindow(u"Неверный индекс")
            return
        row = current_index.row()
        column_count = model.columnCount()
        row_data = []
        for col in range(column_count):
            index = model.index(row, col)
            variant = model.data(index)
            value = unicode(variant.toString()) if variant and not variant.isNull() else u''
            row_data.append(value)
        if len(row_data) > 3:
            param_dict = {'external_id': str(uuid.uuid4())}
            param_dict['enp'] = row_data[3]
            service = Ferzl_service()
            self.result_service = service.getPersonDataFrom(param_dict, 1)
            mass = u'Хотите зарегистрировать пациента?' + u'\n' + self.result_service['massges_info']
            res = QtGui.QMessageBox.warning(self,
                                            u'Внимание',
                                            mass,
                                            QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel,
                                            QtGui.QMessageBox.Ok)
            if res == QtGui.QMessageBox.Ok:
                client_id = self.editNewClient()  # получаем ID созданного пациента
                if client_id is not None:
                    self.res['clientId'] = client_id
                    self.accept()  # Закрываем диалог с кодом Accepted
                else:
                    # Если создание не удалось, остаёмся в диалоге
                    pass
        else:
            warninWindow(u"Недостаточно данных")


    def editNewClient(self):
        dialog = CClientEditDialog(self)
        self.getParamsPerson()
        if self.dialogInfo:
            dialog.setClientDialogInfo(self.dialogInfo)
        client_id = None
        try:
            if dialog.exec_():
                client_id = dialog.itemId()
        finally:
            dialog.deleteLater()
        return client_id

    def getParamsPerson(self):
        self.dialogInfo = {}
        if 'elements' in self.result_service:
            result = self.result_service['elements']
            self.dialogInfo['lastName'] = forceString(result['surname'])
            self.dialogInfo['firstName'] = forceString(result['firstName'])
            self.dialogInfo['patrName'] = forceString(result['patronymic'])
            self.dialogInfo['birthDate'] = QDate.fromString(result['birthDay'], "dd.MM.yyyy")
            self.dialogInfo['sex'] = forceInt(result['gender'])
            if result['policy'][0]['policy_pcyType'] in (u'С',u'П'):
                self.dialogInfo['polisNumber'] = forceString(result['policy'][0]['policy_enp'])
                self.dialogInfo['polisCompany'] = forceString(result['policy'][0]['policy_insurfName'])
                self.dialogInfo['polisBegDate'] = QDate.fromString(result['policy'][0]['policy_pcyDateB'], "dd.MM.yyyy")
            policy = result.get('policy', None)
            if policy and len(policy) > 0:
                polis = policy[0]
                enp = polis.get('policy_enp', None)
                pcySer = polis.get('policy_pcySer', None)
                pcyNum = polis.get('policy_pcyNum', None)
                polisDateB = polis.get('policy_pcyDateB', None)
                polisDateE = polis.get('policy_pcyDateE', None)
                pcyType = polis.get('policy_pcyType', None)
                if enp:
                    self.dialogInfo['polisNumber'] = enp
                    self.dialogInfo['polisType'] = 1
                elif pcyNum or pcySer:
                    if pcyNum:
                        self.dialogInfo['polisNumber'] = enp
                    if pcySer:
                        self.dialogInfo['polisSerial'] = pcySer
                if polisDateB:
                    self.dialogInfo['polisBegDate'] = QDate.fromString(result['policy'][0]['policy_pcyDateB'], "dd.MM.yyyy")
                if polisDateE:
                    self.dialogInfo['polisEndDate'] = QDate.fromString(result['policy'][0]['policy_pcyDateB'], "dd.MM.yyyy")
                if pcyType:
                    pcyType_request = u"select id from rbPolicyKind where code = '/*CODE*/' "
                    if pcyType == u'П':
                        pcyType_request = pcyType_request.replace(u'/*CODE*/', u'3')
                        pcyType_query = QtGui.qApp.db.query(pcyType_request)
                        if pcyType_query.next():
                            pcyType_id = pcyType_query.record().value('id')
                            if pcyType_id:
                                self.dialogInfo['polisKind'] = forceInt(pcyType_id)
                    elif pcyType == u'С':
                        pcyType_request = pcyType_request.replace(u'/*CODE*/', u'1')
                        pcyType_query = QtGui.qApp.db.query(pcyType_request)
                        if pcyType_query.next():
                            pcyType_id = pcyType_query.record().value('id')
                            if pcyType_id:
                                self.dialogInfo['polisKind'] = forceInt(pcyType_id)
                    elif pcyType == u'В':
                        pcyType_request = pcyType_request.replace(u'/*CODE*/', u'2')
                        pcyType_query = QtGui.qApp.db.query(pcyType_request)
                        if pcyType_query.next():
                            pcyType_id = pcyType_query.record().value('id')
                            if pcyType_id:
                                self.dialogInfo['polisKind'] = forceInt(pcyType_id)
                    elif pcyType == u'Э':
                        pcyType_request = pcyType_request.replace(u'/*CODE*/', u'4')
                        pcyType_query = QtGui.qApp.db.query(pcyType_request)
                        if pcyType_query.next():
                            pcyType_id = pcyType_query.record().value('id')
                            if pcyType_id:
                                self.dialogInfo['polisKind'] = forceInt(pcyType_id)
                    elif pcyType == u'К':
                        pcyType_request = pcyType_request.replace(u'/*CODE*/', u'5')
                        pcyType_query = QtGui.qApp.db.query(pcyType_request)
                        if pcyType_query.next():
                            pcyType_id = pcyType_query.record().value('id')
                            if pcyType_id:
                                self.dialogInfo['polisKind'] = forceInt(pcyType_id)
                insurfCode = polis.get('policy_insurfCode', None)
                insurfOrgn = polis.get('policy_insurfOgrn', None)
                insurfOkato = polis.get('policy_okato', None)
                if insurfCode or insurfOrgn:
                    insurf_request = u"SELECT id from Organisation WHERE 1=1 and 2=2 and 3=3"
                    if insurfCode:
                        insurf_request = insurf_request.replace(u'1=1', u"smoCode = '" + forceString(insurfCode) + u"'")
                    if insurfOrgn:
                        insurf_request = insurf_request.replace(u'2=2', u"OGRN = '" + forceString(insurfOrgn) + u"'")
                    if insurfOkato:
                        insurf_request = insurf_request.replace(u'3=3', u"OKATO = '" + forceString(insurfOkato) + u"'")
                    insurf_query = QtGui.qApp.db.query(insurf_request)
                    if insurf_query.next():
                        insurf_id = insurf_query.record().value('id')
                        if insurf_id:
                            self.dialogInfo['polisCompany'] = forceInt(insurf_id)

    def getResult(self):
        """Возвращает словарь с результатом (clientId)."""
        return self.res


def validate_seria(seria):
    seria = seria.strip()
    # Вариант 1: 4 цифры подряд (например, "1234")
    if len(seria) == 4 and seria.isdigit():
        return seria[:2] + ' ' + seria[2:]   

    # Вариант 2: 2 цифры, пробел, 2 цифры (например, "12 34")
    if (len(seria) == 5 and
        seria[2] == ' ' and          
        seria[:2].isdigit() and
        seria[3:].isdigit()):        
        return seria

    # Если ни одно условие не подошло — ошибка
    return -1


def typePolicy(i):
    # 2 С - старого образца
    # 3 В - Временное свидетельство в форме бумажного бланка
    # 4 Е - Временное свидетельство в форме электронного документа
    # 7 К - Полис ОМС в составе универсальной электронной карты
    type = ''
    if i == 2:
        type = u'С'
    # Электронный полис ОМС единого образца
    elif i == 3:
        type = u'В'
    elif i == 4:
        type = u'Е'
    elif i == 7:
        type = u'К'
    return type
    
def warninWindow(massege):
    buttons = QtGui.QMessageBox.Ok
    QtGui.QMessageBox.warning(QtGui.qApp.mainWindow,
                              u'Информация',
                              massege,
                              buttons)