# -*- coding: utf-8 -*-

from PyQt4 import QtGui
from PyQt4.QtCore import *

from library.DialogBase import CConstructHelperMixin
from library.Utils import exceptionToUnicode

from UOServiceClient import CUOServiceClient

from Ui_UOAppointmentsTableDialog import Ui_UOAppointmentsTableDialog


class CUOAppointmentsTableDialog(QtGui.QDialog, CConstructHelperMixin, Ui_UOAppointmentsTableDialog):
    def __init__(self, parent, action):
        QtGui.QDialog.__init__(self, parent)
        self.addModels('Doctors', CUODoctorsListModel(self))
        self.addModels('Appointments', CUOAppointmentsTableModel(self))
        self.setupUi(self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setModels(self.lvDoctors, self.modelDoctors, self.selectionModelDoctors)
        self.setModels(self.tblAppointments, self.modelAppointments, self.selectionModelAppointments)
        self.btnSetAppointment.setEnabled(False)
        self.btnRegisterReferral.setEnabled(False)
        self.action = action
        try:
            self.clientId = parent.clientId()
        except:
            self.clientId = parent.clientId
        self.orgId = action[u'Куда направляется']
        self.profileId = action[u'Профиль']
        h = self.tblAppointments.fontMetrics().height()
        self.tblAppointments.verticalHeader().setDefaultSectionSize(3 * h / 2)
        self.tblAppointments.verticalHeader().hide()
        w = self.tblAppointments.fontMetrics().width('00.00.0000')
        self.tblAppointments.horizontalHeader().setDefaultSectionSize(w + h * 2)
        self.actionChanged = False

    def showEvent(self, event):
        QTimer.singleShot(0, self.updateList)

    def enableControls(self, enabled):
        self.lvDoctors.setEnabled(enabled)
        self.tblAppointments.setEnabled(enabled)
        self.btnUpdateList.setEnabled(enabled)
        self.btnSetAppointment.setEnabled(enabled and self.selectionModelAppointments.hasSelection())
        self.btnRegisterReferral.setEnabled(enabled and not self.action[u'Идентификатор направления'])
        self.btnClose.setEnabled(enabled)

    def updateList(self):
        self.modelAppointments.setList(None)
        self.modelDoctors.setList(None)
        self.lblStatus.setText(u"Загрузка списка талонов...")
        self.lblStatus.setVisible(True)
        self.enableControls(False)
        QtGui.qApp.setWaitCursor()
        try:
            QtGui.qApp.processEvents()
            client = CUOServiceClient()
            serviceData = client.getAvailableAppointments(self.orgId, self.profileId, self.clientId)
            self.modelDoctors.setList(serviceData)
        except Exception, e:
            if exceptionToUnicode(e) == 'timed out':
                error = u'В данный момент целевая медицинская организация не доступна.\nПопробуйте записать позже.'
            else:
                error = exceptionToUnicode(e)
            QtGui.QMessageBox.critical(self,
                                       u'Ошибка при получении списка доступных талонов',
                                       error,
                                       QtGui.QMessageBox.Ok,
                                       QtGui.QMessageBox.Ok)
        QtGui.qApp.restoreOverrideCursor()
        self.enableControls(True)
        if len(self.modelDoctors.rows) > 0:
            self.lblStatus.setVisible(False)
        else:
            self.lblStatus.setText(u'Нет доступных талонов')

    def getSelectedDoctor(self):
        index = self.selectionModelDoctors.currentIndex()
        if index.isValid():
            return self.modelDoctors.getDoctorByIndex(index)
        else:
            return None

    def getSelectedAppointment(self):
        index = self.selectionModelAppointments.currentIndex()
        if index.isValid():
            return self.modelAppointments.getAppointmentByIndex(index)
        else:
            return None

    @pyqtSignature('')
    def on_btnUpdateList_clicked(self):
        self.updateList()

    @pyqtSignature('')
    def on_btnSetAppointment_clicked(self):
        if self.action[u'Идентификатор талона'] and self.action[
            u'Идентификатор талона'] != u'Направление для самостоятельной записи через ЕПГУ':
            return
        client = CUOServiceClient()
        self.lblStatus.setText(u"Регистрация направления и запись на прием...")
        self.lblStatus.setVisible(True)
        self.enableControls(False)
        QtGui.qApp.setWaitCursor()
        try:
            if not self.action[u'Идентификатор направления']:
                self.lblStatus.setText(u"Регистрация направления...")
                QtGui.qApp.processEvents()
                try:
                    idMq = client.registerReferral(self.action)
                    self.action[u'Идентификатор направления'] = idMq
                    self.actionChanged = True
                except Exception as e:
                    if exceptionToUnicode(e) == 'timed out':
                        error = u'В данный момент целевая медицинская организация не доступна.\nПопробуйте записать позже.'
                    else:
                        error = exceptionToUnicode(e)
                    QtGui.QMessageBox.critical(self,
                                               u'Ошибка при регистрации направления',
                                               error,
                                               QtGui.QMessageBox.Ok,
                                               QtGui.QMessageBox.Ok)
                    return
            self.lblStatus.setText(u"Запись на прием...")
            QtGui.qApp.processEvents()
            doctor = self.getSelectedDoctor()
            appointment = self.getSelectedAppointment()
            appointmentId = appointment['id']
            doctorId = doctor['id']
            specialityId = doctor['specialityId']
            try:
                client.setAppointment(self.action, specialityId, doctorId, appointmentId)
                self.actionChanged = True
            except Exception as e:
                if exceptionToUnicode(e) == 'timed out':
                    error = u'В данный момент целевая медицинская организация не доступна.\nПопробуйте записать позже.'
                else:
                    error = exceptionToUnicode(e)
                QtGui.QMessageBox.critical(self,
                                           u'Ошибка при записи на прием',
                                           exceptionToUnicode(e),
                                           QtGui.QMessageBox.Ok,
                                           QtGui.QMessageBox.Ok)
                return
            QtGui.QMessageBox.information(self,
                                          u'Внимание!',
                                          u'Запись на прием выполнена успешно',
                                          QtGui.QMessageBox.Ok,
                                          QtGui.QMessageBox.Ok)
            self.accept()
        finally:
            QtGui.qApp.restoreOverrideCursor()
            self.enableControls(True)
            self.lblStatus.setVisible(False)

    @pyqtSignature('')
    def on_btnRegisterReferral_auto_clicked(self):
        client = CUOServiceClient()
        self.lblStatus.setText(u"Регистрация направления и запись на прием...")
        self.lblStatus.setVisible(True)
        self.enableControls(False)
        QtGui.qApp.setWaitCursor()
        try:
            if not self.action[u'Идентификатор направления']:
                self.lblStatus.setText(u"Регистрация направления...")
                QtGui.qApp.processEvents()
                try:
                    idMq = client.registerReferral(self.action)
                    self.action[u'Идентификатор направления'] = idMq
                    self.actionChanged = True
                except Exception as e:
                    if exceptionToUnicode(e) == 'timed out':
                        error = u'В данный момент целевая медицинская организация не доступна.\nПопробуйте записать позже.'
                    else:
                        error = exceptionToUnicode(e)
                    QtGui.QMessageBox.critical(self,
                                               u'Ошибка при регистрации направления',
                                               error,
                                               QtGui.QMessageBox.Ok,
                                               QtGui.QMessageBox.Ok)
                    return
            QtGui.QMessageBox.information(self,
                                          u'Внимание!',
                                          u'Направление зарегистрировано',
                                          QtGui.QMessageBox.Ok,
                                          QtGui.QMessageBox.Ok)
            self.accept()
        finally:
            QtGui.qApp.restoreOverrideCursor()
            self.enableControls(True)
            self.lblStatus.setVisible(False)

    @pyqtSignature('')
    def on_btnRegisterReferral_clicked(self):
        if not self.action[u'Идентификатор направления']:
            self.on_btnRegisterReferral_auto_clicked()
        if self.action[u'Идентификатор талона']:
            return
        self.action[u'Идентификатор талона'] = u'Направление для самостоятельной записи через ЕПГУ'
        self.accept()

    @pyqtSignature('')
    def on_btnClose_clicked(self):
        self.reject()

    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelDoctors_currentChanged(self, current, previous):
        if current.isValid():
            doctor = self.modelDoctors.getDoctorByIndex(current)
            self.modelAppointments.setList(doctor['appointments'])
        else:
            self.modelAppointments.setList(None)

    @pyqtSignature('')
    def on_modelDoctors_modelReset(self):
        self.btnSetAppointment.setEnabled(False)

    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelAppointments_currentChanged(self, current, previous):
        if current.isValid():
            appointment = self.modelAppointments.getAppointmentByIndex(current)
        else:
            appointment = None
        if appointment:
            self.btnSetAppointment.setEnabled(True)
        else:
            self.btnSetAppointment.setEnabled(False)

    @pyqtSignature('')
    def on_modelAppointments_modelReset(self):
        self.btnSetAppointment.setEnabled(False)


class CUODoctorsListModel(QAbstractItemModel):
    def __init__(self, parent):
        QAbstractItemModel.__init__(self, parent)
        self.rows = []
        self.doctors = {}

    def index(self, row, col, parent):
        return self.createIndex(row, col, None)

    def parent(self, child):
        return QModelIndex()

    def setList(self, serviceData):
        self.rows = []
        self.doctors = {}
        if serviceData:
            for speciality in serviceData['specialityList']:
                for doctor in speciality['doctorList']:
                    if doctor['appointmentList']:
                        key = speciality['id'] + '|' + doctor['id']
                        self.doctors[key] = {
                            'id': doctor['id'],
                            'name': u"%s, %s" % (doctor['name'], speciality['name']),
                            'specialityId': speciality['id'],
                            'appointments': doctor['appointmentList']
                        }
            self.rows = sorted(self.doctors.keys(), key=lambda k: self.doctors[k]['name'])
        self.reset()

    def columnCount(self, parent):
        return 1

    def rowCount(self, parent):
        return len(self.rows)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            row = index.row()
            col = index.column()
            if col == 0:
                key = self.rows[row]
                return QVariant(self.doctors[key]['name'])
        return QVariant()

    def getDoctorByIndex(self, index):
        row = index.row()
        key = self.rows[row]
        return self.doctors[key]


class CUOAppointmentsTableModel(QAbstractTableModel):
    def __init__(self, parent):
        QAbstractTableModel.__init__(self, parent)
        self.appointmentsByDate = {}
        self.maxRowCount = 0
        self.columns = []

    def setList(self, serviceData):
        self.appointmentsByDate = {}
        self.maxRowCount = 0
        if serviceData:
            for appointment in serviceData:
                visitStart = QDateTime.fromString(appointment['visitStart'], Qt.ISODate)
                visitEnd = QDateTime.fromString(appointment['visitEnd'], Qt.ISODate)
                appointmentDate = visitStart.date().toString('dd.MM.yyyy')
                if appointmentDate not in self.appointmentsByDate:
                    self.appointmentsByDate[appointmentDate] = []
                self.appointmentsByDate[appointmentDate].append({
                    'id': appointment['id'],
                    'start': visitStart.time(),
                    'end': visitEnd.time(),
                    'address': appointment['address'],
                    'num': appointment['num'],
                    'room': appointment['room'],
                })
        for appointments in self.appointmentsByDate.values():
            appointments.sort(key=lambda appointment: appointment['start'])
            if len(appointments) > self.maxRowCount:
                self.maxRowCount = len(appointments)
        self.columns = sorted(self.appointmentsByDate.keys())
        self.reset()

    def columnCount(self, index=None):
        return len(self.columns)

    def rowCount(self, index=None):
        return self.maxRowCount

    def data(self, index, role):
        appointment = self.getAppointmentByIndex(index)
        if appointment:
            if role == Qt.DisplayRole:
                return QVariant(appointment['start'].toString('hh:mm'))
            elif role == Qt.TextAlignmentRole:
                return Qt.AlignHCenter + Qt.AlignVCenter
            elif role == Qt.ToolTipRole:
                toolTip = []
                toolTip.append(u"Начало: %s" % appointment['start'].toString('hh:mm'))
                toolTip.append(u"Окончание: %s" % appointment['end'].toString('hh:mm'))
                if appointment['address']:
                    toolTip.append(u"Адрес: %s" % appointment['address'])
                if appointment['room']:
                    toolTip.append(u"Кабинет: %s" % appointment['room'])
                if appointment['num']:
                    toolTip.append(u"Номер талона: %s" % appointment['num'])
                return QVariant('\n'.join(toolTip))
        return QVariant()

    def flags(self, index):
        appointment = self.getAppointmentByIndex(index)
        if appointment:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        else:
            return Qt.NoItemFlags

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return QVariant(self.columns[section])
        return QVariant()

    def getAppointmentByIndex(self, index):
        row = index.row()
        col = index.column()
        date = self.columns[col]
        appointments = self.appointmentsByDate[date]
        if 0 <= row < len(appointments):
            return appointments[row]
        else:
            return None