# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2012-2020 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
##
## Работа с отложенной записью
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDate, QDateTime, QMetaObject, QVariant, pyqtSignature, SIGNAL, QObject

from Timeline.Schedule import freeScheduleItem
from library.database                  import CTableRecordCache
from library.DialogBase                import CDialogBase, CConstructHelperMixin
from library.interchange               import setTextEditValue, getComboBoxValue, getTextEditValue, getCheckBoxValue
from library.PreferencesMixin          import CDialogPreferencesMixin
from library.PrintInfo                 import CInfoContext, CDateInfo
from library.PrintTemplates            import applyTemplate, CPrintAction, getPrintTemplates
from library.RecordLock                import CRecordLockMixin
from library.SimpleProgressDialog      import CSimpleProgressDialog
from library.TableModel                import CBoolCol, CEnumCol, CDateCol, CDesignationCol, CTextCol, CDateTimeCol, CCol, CRefBookCol, CTableModel, CIntCol
from library.Utils import formatName, toVariant, forceString, withWaitCursor, forceRef, forceTime, forceBool, \
    formatRecordsCount, forceDate, forceStringEx, formatSex, forceInt, formatDate, nameCase
from Registry.SuspendedAppointmentInfo import CSuspendedAppointmentInfo, CSuspendedAppointmentInfoList
from Orgs.Utils                        import getOrgStructureDescendants, COrgStructureInfo
from Orgs.PersonInfo                   import CPersonInfo
from RefBooks.Speciality.Info          import CSpecialityInfo
from Registry.RegistryWindow           import CSchedulesModel, CVisitsBySchedulesModel, convertFilterToTextItem
from Registry.ClientEditDialog         import CClientEditDialog
from Registry.Utils import getClientBanner, getClientInfo, getClientCompulsoryPolicy
from Timeline.Schedule                 import CSchedule
from Users.Rights                      import urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry

from Registry.Ui_SuspendedAppointment import Ui_SuspenedAppointmentWindow
from Registry.Ui_SuspendedAppointmentMarksDialog import Ui_SuspendedAppointmentMarksDialog


class CSuspenedAppointmentWindow(QtGui.QScrollArea, Ui_SuspenedAppointmentWindow, CDialogPreferencesMixin, CConstructHelperMixin, CRecordLockMixin):
    def __init__(self, parent=None):
        QtGui.QScrollArea.__init__(self, parent)
        CRecordLockMixin.__init__(self)
        self.addModels('SuspendedAppointments', CSuspendedAppointmentModel(self))
        self.addModels('Schedules', CSchedulesModel(self))
        self.addModels('VisitsBySchedules',    CVisitsBySchedulesModel(self))
        self.addObject('actEditClient', QtGui.QAction(u'Открыть регистрационную карточку', self))
        self.addObject('actFilterAppointment', QtGui.QAction(u'Подобрать номерок', self))
        # self.addObject('actSetProcessed',      QtGui.QAction(u'Отработать', self))
        self.addObject('actUnsetProcessed',    QtGui.QAction(u'Отменить', self))

        self.setObjectName('SuspenedAppointmentWindow')
        self.internal = QtGui.QWidget(self)
        self.setWidget(self.internal)
        self.setupUi(self.internal)

        self.setWindowTitle(self.internal.windowTitle())
        self.setWidgetResizable(True)
        QMetaObject.connectSlotsByName(self) # т.к. в setupUi параметр не self
#        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        templates = getPrintTemplates(['suspendedAppointmentList'])
        if not templates:
            self.btnPrint.setId(-1)
        else:
            for template in templates:
                action = CPrintAction(template.name, template.id, self.btnPrint, self.btnPrint)
                self.btnPrint.addAction(action)
            self.btnPrint.menu().addSeparator()
            self.btnPrint.addAction(CPrintAction(u'Напечатать список визитов', -1, self.btnPrint, self.btnPrint))
        self.setModels(self.tblSuspendedAppointments, self.modelSuspendedAppointments, self.selectionModelSuspendedAppointments)

        self.setModels(self.tblSchedules, self.modelSchedules, self.selectionModelSchedules)
        self.setModels(self.tblVisitsBySchedules, self.modelVisitsBySchedules, self.selectionModelVisitsBySchedules)
        self.txtClientInfoBrowser.actions.append(self.actEditClient)
        self.tblSuspendedAppointments.createPopupMenu([self.actFilterAppointment,
                                                       # self.actSetProcessed,
                                                       self.actUnsetProcessed
                                                      ]
                                                     )

#        self.setFocusProxy(self.tabFilter)
#        self.tabFilter.setFocusProxy(self.tblSuspendedAppointments)

        self.edtFilterBegBirthDay.canBeEmpty(True)
        self.edtFilterEndBirthDay.canBeEmpty(True)
        self.edtFilterBegBegDate.canBeEmpty(True)
        self.edtFilterEndBegDate.canBeEmpty(True)
        self.edtFilterBegEndDate.canBeEmpty(True)
        self.edtFilterEndEndDate.canBeEmpty(True)
        self.cmbFilterSpeciality.setTable('rbSpeciality', True)

        self.connect(QtGui.qApp, SIGNAL('currentClientInfoSAChanged(int)'), self.updateScheduleItemId)
        self.connect(QtGui.qApp, SIGNAL('currentClientInfoJLWChanged(int)'), self.updateScheduleItemId)

#        self.connect(QtGui.qApp, SIGNAL('currentClientInfoJLWChanged(int)'), self.updateDataTable)
#        self.connect(QtGui.qApp, SIGNAL('currentClientInfoJLWDeleted(int)'), self.deletedScheduleItemId)

        self.filter = {}
        self.on_buttonBoxFilter_reset()
        # Мешает активации/деактивации окна в CMdiArea (CS11MainWindow.centralWidget)
        # self.focusSuspendedAppointmentsList()
        self.connect(self.tblSuspendedAppointments.horizontalHeader(), SIGNAL('sectionClicked(int)'), self._setSAOrderByColumn)
        self.connect(self.tblSchedules.horizontalHeader(), SIGNAL('sectionClicked(int)'), self._setSchedulesOrderByColumn)
        self.connect(self.tblVisitsBySchedules.horizontalHeader(), SIGNAL('sectionClicked(int)'), self._setVisitsBySchedulesOrderByColumn)
        self.btnFindAppointments.setVisible(False) # скрыли пока эту кнопку за ненадобностью
        self.tblSuspendedAppointments.enableColsHide()
        self.tblSuspendedAppointments.enableColsMove()
        self.tblSchedules.enableColsHide()
        self.tblSchedules.enableColsMove()
        self.tblVisitsBySchedules.enableColsHide()
        self.tblVisitsBySchedules.enableColsMove()
        self.loadDialogPreferences()
        self.setSortable(self.tblSuspendedAppointments, self.updateSuspendedAppointmentsList)

        actionPolicyUpdate = QtGui.QAction(u'Проверить полис ОМС', self)
        self.txtClientInfoBrowser.actions.append(actionPolicyUpdate)
        actionPolicyUpdate.triggered.connect(self.policyUpdate)


    def _setSAOrderByColumn(self, column):
        self.tblSuspendedAppointments.setOrder(column)
        self.updateSuspendedAppointmentsList(self.tblSuspendedAppointments.currentItemId())


    def _setSchedulesOrderByColumn(self, column):
        currentIndex = self.tblSchedules.currentIndex()
        self.tblSchedules.setOrder(column)
        clientId = self.getCurrentClientId()
        self.modelSchedules.setOrder(self.tblSchedules.order() if self.tblSchedules.order() else u'Schedule_Item.time DESC')
        self.modelSchedules.loadData(clientId)
        self.tblSchedules.setCurrentIndex(currentIndex)


    def _setVisitsBySchedulesOrderByColumn(self, column):
        currentIndex = self.tblVisitsBySchedules.currentIndex()
        self.tblVisitsBySchedules.setOrder(column)
        clientId = self.getCurrentClientId()
        self.modelVisitsBySchedules.setOrder(self.tblVisitsBySchedules.order() if self.tblVisitsBySchedules.order() else u'Schedule_Item.time DESC')
        self.modelVisitsBySchedules.loadData(clientId)
        self.tblVisitsBySchedules.setCurrentIndex(currentIndex)


    def policyUpdate(self):
        clientId = self.getCurrentClientId()
        result = getClientInfo(clientId)

        firstName = result.firstName
        lastName = result.lastName
        patrName = result.patrName
        sex = result.sexCode
        birthDate = result.birthDate
        snils = result.SNILS

        db = QtGui.qApp.db
        policyRecord = getClientCompulsoryPolicy(clientId)

        serial = policyRecord.value('serial')
        number = policyRecord.value('number')
        begDate = policyRecord.value('begDate')
        policyKindId = policyRecord.value('policyKind_id')

        descr = QtGui.qApp.identService(firstName,
                                        lastName,
                                        patrName,
                                        sex,
                                        birthDate,
                                        forceStringEx(snils).replace('-', '').replace(' ', ''),
                                        forceInt(QtGui.qApp.db.translate('rbPolicyKind', 'id', policyKindId,
                                                                         'regionalCode')),
                                        forceStringEx(serial),
                                        forceStringEx(number),
                                        0,
                                        forceStringEx(
                                            serial),
                                        forceStringEx(number))
        if descr:
            if 'hicId' not in descr and len(descr) == 3:
                return None
            if 'dd' in descr and descr.dd['VP']:
                ddMOCodeName = ' '.join([descr.dd['CODE_MO'], forceString(
                    db.translate('Organisation', 'infisCode', descr.dd['CODE_MO'], 'shortName'))])
                ddVP = descr.dd['VP']
                if ddVP == '211':
                    ddVPstr = u'Проведена: диспансеризация взрослого населения'
                else:
                    ddVPstr = u'Проведен: профилактический осмотр'
                ddDATN = formatDate(QDate.fromString(descr.dd['DATN'], Qt.ISODate))
                ddDATO = formatDate(QDate.fromString(descr.dd['DATO'], Qt.ISODate))
                ddInfoStr = u'Найдена информация о проведенной ранее\n' \
                            u'диспансеризации/профилактическом осмотре:\n' \
                            u'%s\n' \
                            u'МО: %s\n' \
                            u'Период проведения с %s по %s' % (ddVPstr, ddMOCodeName, ddDATN, ddDATO)
            else:
                ddInfoStr = ''

            hicId = descr.hicId
            if hicId:
                hicName = forceString(db.translate('Organisation', 'id', hicId, 'shortName'))
            else:
                hicName = u'в справочнике не найдено: %s' % descr.hicName

            policyTypeCode = descr.typeCode
            policyTypeId = forceRef(db.translate('rbPolicyType', 'code', policyTypeCode, 'id'))
            if policyTypeId:
                policyTypeName = forceString(db.translate('rbPolicyType', 'id', policyTypeId, 'name'))
            else:
                policyTypeName = '-'

            policyKindCode = descr.kindCode
            policyKindId = forceRef(db.translate('rbPolicyKind', 'code', policyKindCode, 'id'))
            if policyKindId:
                policyKindName = forceString(db.translate('rbPolicyKind', 'id', policyKindId, 'name'))
            else:
                policyKindName = '-'

            msgbox = QtGui.QMessageBox()
            msgbox.setWindowFlags(msgbox.windowFlags() | Qt.WindowStaysOnTopHint)
            msgbox.setIcon(QtGui.QMessageBox.Information)
            msgbox.setWindowTitle(u'Поиск полиса')
            msgbox.setText(u'Найден полис:\n' \
                           u'Владелец:   %s %s %s, %s, %s\n' \
                           u'СНИЛС:%s\n' \
                           u'СМО:   %s\n' \
                           u'серия: %s\n' \
                           u'номер: %s\n' \
                           u'тип:   %s\n' \
                           u'вид:   %s\n' \
                           u'действителен с %s по %s\n' \
                           u'Обновить данные?\n\n%s' % (
                               nameCase(descr.lastName), nameCase(descr.firstName),
                               nameCase(descr.patrName) if descr.patrName else '', [u'---', u'М', u'Ж'][descr.sex],
                               forceString(descr.birthDate),
                               descr.snils,
                               hicName,
                               descr.policySerial,
                               descr.policyNumber,
                               policyTypeName,
                               policyKindName,
                               forceString(descr.begDate),
                               forceString(descr.endDate),
                               ddInfoStr))

            btnUpdate = QtGui.QPushButton()
            btnAdd = QtGui.QPushButton()
            btnUpdate.setText(u'Обновить данные')
            btnAdd.setText(u'Добавить новую запись')

            msgbox.addButton(QtGui.QMessageBox.Cancel)

            # если дата начала полиса отличаются, то показывать кнопку добавить
            if forceDate(descr.begDate) != forceDate(begDate):
                msgbox.addButton(btnAdd, QtGui.QMessageBox.ActionRole)
                msgbox.setDefaultButton(btnAdd)
            else:
                msgbox.addButton(btnUpdate, QtGui.QMessageBox.ActionRole)
                msgbox.setDefaultButton(btnUpdate)

            msgbox.exec_()
            if msgbox.clickedButton() in (btnAdd, btnUpdate):
                if msgbox.clickedButton() == btnAdd:
                    currentDate = forceString(QDateTime.currentDateTime())
                    currentPersonId = QtGui.qApp.userId

                    if forceBool(descr.endDate):
                        endDateDescr = forceString(descr.endDate)
                    else:
                        endDateDescr = None
                    # дата закрытия текущего полиса
                    endDatePrevious = None
                    if forceDate(descr.begDate) > forceDate(begDate):
                        endDatePrevious = forceDate(descr.begDate)
                    elif forceDate(descr.begDate) < forceDate(begDate):
                        endDateDescr = forceDate(begDate)

                    tableClientPolicy = db.table('ClientPolicy')
                    newRecord = tableClientPolicy.newRecord()
                    newRecord.setValue('createDatetime', currentDate)
                    newRecord.setValue('createPerson', currentPersonId)
                    newRecord.setValue('modifyDatetime', currentDate)
                    newRecord.setValue('modifyPerson', currentPersonId)
                    newRecord.setValue('deleted', 0)
                    newRecord.setValue('client_id', clientId)
                    newRecord.setValue('insurer_id', hicId)
                    newRecord.setValue('policyType_id', policyTypeId)
                    newRecord.setValue('policyKind_id', policyKindId)
                    newRecord.setValue('serial', descr.policySerial)
                    newRecord.setValue('number', descr.policyNumber)
                    newRecord.setValue('begDate', forceDate(descr.begDate))
                    newRecord.setValue('endDate', endDateDescr)
                    newRecord.setValue('note', '')
                    db.insertRecord(tableClientPolicy, newRecord)

                    clientPolicyId = forceString(policyRecord.value('id'))
                    record = db.getRecordEx(tableClientPolicy, '*', tableClientPolicy['id'].eq(clientPolicyId))
                    record.setValue('modifyDatetime', currentDate)
                    record.setValue('modifyPerson', currentPersonId)
                    record.setValue('endDate', endDatePrevious)
                    db.updateRecord(tableClientPolicy, record)

                if msgbox.clickedButton() == btnUpdate:
                    tableClientPolicy = db.table('ClientPolicy')
                    clientPolicyId = forceString(policyRecord.value('id'))
                    record = db.getRecordEx(tableClientPolicy, '*', tableClientPolicy['id'].eq(clientPolicyId))
                    currentDate = forceString(QDateTime.currentDateTime())
                    currentPersonId = QtGui.qApp.userId
                    if forceBool(descr.endDate):
                        endDateDescr = forceString(descr.endDate)
                    else:
                        endDateDescr = None
                    record.setValue('modifyDatetime', currentDate)
                    record.setValue('modifyPerson', currentPersonId)
                    record.setValue('insurer_id', hicId)
                    record.setValue('policyType_id', policyTypeId)
                    record.setValue('policyKind_id', policyKindId)
                    record.setValue('serial', descr.policySerial)
                    record.setValue('number', descr.policyNumber)
                    record.setValue('begDate', forceDate(descr.begDate))
                    record.setValue('endDate', endDateDescr)
                    db.updateRecord(tableClientPolicy, record)

        else:
            messageBox = QtGui.QMessageBox(QtGui.QMessageBox.Information,
                                           u'Поиск полиса',
                                           u'Полис не найден',
                                           QtGui.QMessageBox.Ok)
            messageBox.setWindowFlags(messageBox.windowFlags() | Qt.WindowStaysOnTopHint)
            messageBox.exec_()
        self.updateClientInfo()


    def setSortingIndicator(self, tbl, col, asc):
        tbl.setSortingEnabled(True)
        tbl.horizontalHeader().setSortIndicator(col, Qt.AscendingOrder if asc else Qt.DescendingOrder)


    def setSortable(self, tbl, update_function=None):
        def on_click(col):
            hs = tbl.horizontalScrollBar().value()
            model = tbl.model()
            sortingCol = model.headerSortingCol.get(col, False)
            model.headerSortingCol = {}
            model.headerSortingCol[col] = not sortingCol
            if update_function:
                update_function()
            else:
                model.loadData()
            self.setSortingIndicator(tbl, col, not sortingCol)
            tbl.horizontalScrollBar().setValue(hs)
        header = tbl.horizontalHeader()
        header.setClickable(True)
        QObject.connect(header, SIGNAL('sectionClicked(int)'), on_click)

    def updateScheduleItemId(self, scheduleItemId):
        if scheduleItemId and self.getCurrentClientId() == QtGui.qApp.currentClientId():
            self.editMarks(True, scheduleItemId)


    @pyqtSignature('int')
    def on_btnPrint_printByTemplate(self, templateId):
        if templateId == -1:
            self.tblSuspendedAppointments.setReportHeader(u'Журнал отложенной записи')
            self.tblSuspendedAppointments.setReportDescription(self.getSuspenedAppointmentFilterAsText())
            self.tblSuspendedAppointments.printContent()
            self.tblSuspendedAppointments.setFocus(Qt.TabFocusReason)
        else:
            idList = self.tblSuspendedAppointments.model().idList()
            context = CInfoContext()
            suspenedAppointmentInfo = context.getInstance(CSuspendedAppointmentInfo, self.tblSuspendedAppointments.currentItemId())
            suspenedAppointmentInfoList = context.getInstance(CSuspendedAppointmentInfoList, tuple(idList))
            data = { 'suspendedAppointmentList': suspenedAppointmentInfoList,
                     'suspendedAppointment'    : suspenedAppointmentInfo,
                     'lastName' : forceString(self.edtFilterLastName.text() if self.chkFilterLastName.isChecked() else u''),
                     'firstName' : forceString(self.edtFilterFirstName.text() if self.chkFilterFirstName.isChecked() else u''),
                     'patrName' : forceString(self.edtFilterPatrName.text() if self.chkFilterPatrName.isChecked() else u''),
                     'begBirthDay' : CDateInfo(self.edtFilterBegBirthDay.date() if self.chkFilterBirthDay.isChecked() else None),
                     'endBirthDay' : CDateInfo(self.edtFilterEndBirthDay.date() if self.chkFilterEndBirthDay.isChecked() else None),
                     'sex' : formatSex(forceInt(self.cmbSex.currentIndex()) if self.chkFilterSex.isChecked() else 0),
                     'contact' : forceString(self.edtFilterContact.text() if self.chkFilterContact.isChecked() else u''),
                     'begVisitBegDate' : CDateInfo(self.edtFilterBegBegDate.date() if self.chkFilterBegDateRange.isChecked() else None),
                     'endVisitBegDate' : CDateInfo(self.edtFilterEndBegDate.date() if self.chkFilterBegDateRange.isChecked() else None),
                     'begVisitEndDate' : CDateInfo(self.edtFilterBegEndDate.date() if self.chkFilterEndDateRange.isChecked() else None),
                     'endVisitEndDate' : CDateInfo(self.edtFilterEndEndDate.date() if self.chkFilterEndDateRange.isChecked() else None),
                     'orgStructure'    : context.getInstance(COrgStructureInfo, self.cmbFilterOrgStructure.value() if self.chkFilterOrgStructure.isChecked() else None),
                     'speciality'      : context.getInstance(CSpecialityInfo, self.cmbFilterSpeciality.value() if self.chkFilterSpeciality.isChecked() else None),
                     'person'          : context.getInstance(CPersonInfo, self.cmbFilterPerson.value() if self.chkFilterPerson.isChecked() else None),
                     'externalUserRole' : forceString(self.edtFilterExternalUserRole.text() if self.chkFilterExternalUserRole.isChecked() else u''),
                     'externalUserName' : forceString(self.edtFilterExternalUserName.text() if self.chkFilterExternalUserName.isChecked() else u''),
                     'processed'        : forceString([u'Все', u'Неотработанные', u'Отработанные'][forceInt(self.cmbFilterProcessed.currentIndex())]),
                     'notification'     : forceString([u'-', u'Нет', u'Произведено'][forceInt(self.cmbFilterNotification.currentIndex())]),
                     'scheduled'        : forceString([u'-', u'Не произведена', u'Произведена'][forceInt(self.cmbFilterScheduled.currentIndex())]),
                     'note'             : forceString(self.edtFilterNote.text() if self.chkFilterNote.isChecked() else u''),
                     'createPerson'     : context.getInstance(CPersonInfo, self.cmbFilterExCreatePerson.value() if self.chkFilterExCreatePerson.isChecked() else None),
                     'begCreateDate'    : CDateInfo(self.edtFilterExBegCreateDate.date() if self.chkFilterExCreateDate.isChecked() else None),
                     'endCreateDate'    : CDateInfo(self.edtFilterExEndCreateDate.date() if self.chkFilterExCreateDate.isChecked() else None),
                     'modifyPerson'     : context.getInstance(CPersonInfo, self.cmbFilterExModifyPerson.value() if self.chkFilterExModifyPerson.isChecked() else None),
                     'begModifyDate'    : CDateInfo(self.edtFilterExBegModifyDate.date() if self.chkFilterExModifyDate.isChecked() else None),
                     'endModifyDate'    : CDateInfo(self.edtFilterExEndModifyDate.date() if self.chkFilterExModifyDate.isChecked() else None),
                    }
            QtGui.qApp.call(self, applyTemplate, (self, templateId, data))


    def getSuspenedAppointmentFilterAsText(self):
        db = QtGui.qApp.db
        filter  = self.filter
        resList = []
        tmpList = [
            ('lastName',  u'Фамилия', forceString),
            ('firstName', u'Имя', forceString),
            ('patrName',  u'Отчество', forceString),
            ('birthDate', u'Дата рождения', forceString),
            ('begBirthDay', u'Дата рождения с', forceString),
            ('endBirthDay', u'Дата рождения по', forceString),
            ('sex',       u'Пол',           formatSex),
            ('conract',   u'Контакт', forceString),
            ('begVisitBegDate', u'Дата начала периода визита с', forceString),
            ('endVisitBegDate', u'Дата начала периода визита по', forceString),
            ('begVisitEndDate', u'Дата окончания периода визита с', forceString),
            ('endVisitEndDate', u'Дата окончания периода визита по', forceString),
            ('orgStructureId', u'Подразделение',
                lambda id: forceString(db.translate('OrgStructure', 'id', id, 'name'))),
            ('specialityId', u'Специальность',
                lambda id: forceString(db.translate('rbSpeciality', 'id', id, 'name'))),
            ('personId', u'Врач',
                lambda id: forceString(db.translate('vrbPersonWithSpeciality', 'id', id, 'name'))),
            ('externalUserRole',   u'Роль внешнего пользователя', forceString),
            ('externalUserName', u'Внешний пользователь', forceString),
            ('processedName', u'Отображать', forceString),
            ('notifiedName', u'Оповещение', forceString),
            ('scheduledName', u'Запись', forceString),
            ('note', u'Примечание', forceString),
            ('createPersonId', u'Автор',
                lambda id: forceString(db.translate('vrbPersonWithSpeciality', 'id', id, 'name'))),
            ('begCreateDate', u'Дата создания с', forceString),
            ('endCreateDate', u'Дата создания по', forceString),
            ('modifyPersonId', u'Автор последнего изменения',
                lambda id: forceString(db.translate('vrbPersonWithSpeciality', 'id', id, 'name'))),
            ('begModifyDate', u'Дата последнего изменения с', forceString),
            ('endModifyDate', u'Дата последнего изменения по', forceString),
            ]

        for (x, y, z) in tmpList:
            convertFilterToTextItem(resList, filter, x, y, z)
        return '\n'.join([ ': '.join(item) for item in resList])


    @withWaitCursor
    def updateSuspendedAppointmentsList(self, posToId=None):
        db = QtGui.qApp.db
        table = db.table('SuspendedAppointment')
        tableClient = db.table('Client')
        queryTable = table.innerJoin(tableClient, tableClient['id'].eq(table['client_id']))

        cols = [table['id'].name()]
        cond = [table['deleted'].eq(0),
                tableClient['deleted'].eq(0),
               ]
        order = self.tblSuspendedAppointments.order() if self.tblSuspendedAppointments.order() else table['id'].name()
        if u'OrgStructure.name' in order:
            tableOrgStructure = db.table('OrgStructure')
            queryTable = queryTable.leftJoin(tableOrgStructure, [tableOrgStructure['id'].eq(table['orgStructure_id']), tableOrgStructure['deleted'].eq(0)])
        if u'rbSpeciality.name' in order:
            tableRBSpeciality = db.table('rbSpeciality')
            queryTable = queryTable.leftJoin(tableRBSpeciality, tableRBSpeciality['id'].eq(table['speciality_id']))
        if u'vrbPerson.name' in order:
            tableVRBPerson = db.table('vrbPerson')
            queryTable = queryTable.leftJoin(tableVRBPerson, tableVRBPerson['id'].eq(table['person_id']))
        if u'createPerson' in order:
            tableVRBPersonWithSpeciality = db.table('vrbPersonWithSpeciality')
            queryTable = queryTable.leftJoin(tableVRBPersonWithSpeciality, tableVRBPersonWithSpeciality['id'].eq(table['createPerson_id']))
            cols.append('vrbPersonWithSpeciality.name AS createPerson')
        if u'modifyPerson' in order:
            tableVRBPersonWithSpeciality = db.table('vrbPersonWithSpeciality')
            queryTable = queryTable.leftJoin(tableVRBPersonWithSpeciality, tableVRBPersonWithSpeciality['id'].eq(table['modifyPerson_id']))
            cols.append('vrbPersonWithSpeciality.name AS modifyPerson')
        if u'Schedule' in order:
            tableScheduleItem = db.table('Schedule_Item')
            tableSchedule = db.table('Schedule')
            condAppointment = [tableScheduleItem['id'].eq(table['appointment_id']),
                               tableScheduleItem['deleted'].eq(0),
                               tableScheduleItem['client_id'].eq(tableClient['id']),
                               ]
            queryTable = queryTable.leftJoin(tableScheduleItem, db.joinAnd(condAppointment))
            queryTable = queryTable.leftJoin(tableSchedule, db.joinAnd([tableSchedule['id'].eq(tableScheduleItem['master_id']), tableSchedule['deleted'].eq(0)]))

        lastName = self.filter.get('lastName')
        if lastName is not None:
            cond.append(tableClient['lastName'].like(lastName))

        firstName = self.filter.get('firstName')
        if firstName is not None:
            cond.append(tableClient['firstName'].like(firstName))

        patrName = self.filter.get('patrName')
        if patrName is not None:
            cond.append(tableClient['patrName'].like(patrName))

        begBirthDay = self.filter.get('begBirthDay', None)
        endBirthDay = self.filter.get('endBirthDay', None)
        if begBirthDay != endBirthDay:
            if begBirthDay:
                cond.append(tableClient['birthDate'].ge(begBirthDay))
            if endBirthDay:
                cond.append(tableClient['birthDate'].le(endBirthDay))
        elif begBirthDay:
            cond.append(tableClient['birthDate'].eq(begBirthDay))

        sex = self.filter.get('sex', None)
        if sex is not None:
            cond.append(tableClient['sex'].eq(sex))

        contact = self.filter.get('contact')
        if contact is not None:
            cond.append(table['contact'].like(contact))

        begDateRange = self.filter.get('begDateRange')
        if begDateRange:
            begVisitBegDate, endVisitBegDate = begDateRange
            if begVisitBegDate:
                cond.append(table['begDate'].ge(begVisitBegDate))
            if endVisitBegDate:
                cond.append(table['begDate'].le(endVisitBegDate))

        endDateRange = self.filter.get('endDateRange')
        if endDateRange:
            begVisitEndDate, endVisitEndDate = endDateRange
            if begVisitEndDate:
                cond.append(table['endDate'].ge(begVisitEndDate))
            if endVisitEndDate:
                cond.append(table['endDate'].le(endVisitEndDate))

        orgStructureId = self.filter.get('orgStructureId')
        if orgStructureId:
            cond.append(table['orgStructure_id'].inlist(getOrgStructureDescendants(orgStructureId)))

        specialityId = self.filter.get('specialityId')
        if specialityId:
            cond.append(table['speciality_id'].eq(specialityId))

        personId = self.filter.get('personId')
        if personId:
            cond.append(table['person_id'].eq(personId))

        externalUserRole = self.filter.get('externalUserRole')
        if externalUserRole:
            cond.append(table['externalUserRole'].like(externalUserRole))

        externalUserName = self.filter.get('externalUserName')
        if externalUserName:
            cond.append(table['externalUserName'].like(externalUserName))

        processed = self.filter.get('processed')
        if processed is not None:
            cond.append(table['processed'].eq(processed))

        notified = self.filter.get('notified')
        if notified is not None:
            if notified:
                cond.append(table['notified'].ne(0))
            else:
                cond.append(table['notified'].eq(0))

        scheduled = self.filter.get('scheduled')
        if scheduled is not None:
            if scheduled:
                cond.append(table['appointment_id'].isNotNull())
            else:
                cond.append(table['appointment_id'].isNull())

        note = self.filter.get('note')
        if note is not None:
            cond.append(table['note'].like(note))

        createPersonId = self.filter.get('createPersonId')
        if createPersonId:
            cond.append(table['createPerson_id'].eq(createPersonId))

        createDateRange = self.filter.get('createDateRange')
        if createDateRange:
            begDate, endDate = createDateRange
            if begDate:
                cond.append(table['createDatetime'].ge(begDate))
            if endDate:
                cond.append(table['createDatetime'].lt(endDate.addDays(1)))

        modifyPersonId = self.filter.get('modifyPersonId')
        if modifyPersonId:
            cond.append(table['modifyPerson_id'].eq(modifyPersonId))

        modifyDateRange = self.filter.get('modifyDateRange')
        if modifyDateRange:
            begDate, endDate = modifyDateRange
            if begDate:
                cond.append(table['modifyDatetime'].ge(begDate))
            if endDate:
                cond.append(table['modifyDatetime'].lt(endDate.addDays(1)))


        order = self.getOrderBy()
        idList = db.getDistinctIdList(queryTable,
                                      cols,
                                      cond,
                                      order
                                     )
        self.tblSuspendedAppointments.setIdList(idList, posToId)
        self.lblRecordCount.setText(formatRecordsCount(len(idList)))


    def getOrderBy(self):
        orderBY = u'Client.lastName ASC'
        for key, value in self.modelSuspendedAppointments.headerSortingCol.items():
            if value:
                ASC = u'ASC'
            else:
                ASC = u'DESC'
            if key == 0:
                orderBY = u'Client.id %s' % ASC
            elif key == 1:
                orderBY = u'Client.lastName %s' % ASC
            elif key == 2:
                orderBY = u'Client.birthDate %s' % ASC
            elif key == 3:
                orderBY = u'Client.sex %s' % ASC
            elif key == 4:
                orderBY = u'SuspendedAppointment.contact %s' % ASC
            elif key == 5:
                orderBY = u'SuspendedAppointment.begDate %s' % ASC
            elif key == 6:
                orderBY = u'SuspendedAppointment.endDate %s' % ASC
            elif key == 7:
                orderBY = u'OrgStructure.name %s' % ASC
            elif key == 8:
                orderBY = u'rbSpeciality.name %s' % ASC
            elif key == 9:
                orderBY = u'vrbPerson.name %s' % ASC
            elif key == 10:
                orderBY = u'SuspendedAppointment.processed %s' % ASC
            elif key == 11:
                orderBY = u'Schedule.date %s, Schedule_Item.time %s' % (ASC, ASC)
            elif key == 12:
                orderBY = u'SuspendedAppointment.notified %s' % ASC
            elif key == 13:
                orderBY = u'SuspendedAppointment.note %s' % ASC
            elif key == 14:
                orderBY = u'SuspendedAppointment.externalUserRole %s' % ASC
            elif key == 15:
                orderBY = u'SuspendedAppointment.externalUserName %s' % ASC
            elif key == 16:
                orderBY = u'SuspendedAppointment.reason %s' % ASC
            elif key == 17:
                orderBY = u'SuspendedAppointment.createDatetime %s' % ASC
            elif key == 18:
                orderBY = u'SuspendedAppointment.modifyDatetime'
            elif key == 19:
                orderBY = u'vrbPersonWithSpeciality.name %s' % ASC

        return orderBY


    def focusSuspendedAppointmentsList(self):
        self.tblSuspendedAppointments.setFocus(Qt.TabFocusReason)


    def update(self):
        self.updateSuspendedAppointmentsList(self.getCurrentClientId())
        # super(CSuspenedAppointmentWindow, self).update()


    def updateClientInfo(self):
        clientId = self.getCurrentClientId()
        if clientId:
            self.txtClientInfoBrowser.setHtml(getClientBanner(clientId))
        else:
            self.txtClientInfoBrowser.setText('')
        QtGui.qApp.setCurrentClientId(clientId)
        self.loadSchedules(clientId)


    def loadSchedules(self, clientId):
        self.modelSchedules.setOrder(self.tblSchedules.order() if self.tblSchedules.order() else u'Schedule_Item.time DESC')
        self.modelSchedules.loadData(clientId)
        self.modelVisitsBySchedules.setOrder(self.tblVisitsBySchedules.order() if self.tblVisitsBySchedules.order() else u'Schedule_Item.time DESC')
        self.modelVisitsBySchedules.loadData(clientId)


    def getCurrentClientId(self):
        record = self.tblSuspendedAppointments.currentItem()
        if record:
            return forceRef(record.value('client_id'))
        return None


    def findAppointment(self, record):
        db = QtGui.qApp.db
        clientId = forceRef(record.value('client_id'))
        personId = forceRef(record.value('person_id'))
        specialityId = forceRef(record.value('speciality_id'))
        orgStructureId = forceRef(record.value('orgStructure_id'))
        begDate = forceDate(record.value('begDate'))
#           endDate = forceDate(record.value('endDate'))

        tableScheduleItem = db.table('Schedule_Item')
        tableSchedule = db.table('Schedule')
        table = tableScheduleItem.innerJoin(tableSchedule, tableSchedule['id'].eq(tableScheduleItem['master_id']))
        cond = [ tableScheduleItem['deleted'].eq(0),
                 tableSchedule['deleted'].eq(0),
                 tableSchedule['date'].ge(begDate),
#                 tableSchedule['date'].le(endDate),
                 tableScheduleItem['client_id'].eq(clientId),
               ]
        if personId:
            cond.append(tableSchedule['person_id'].eq(personId))
        else:
            if specialityId or orgStructureId:
                tablePerson = db.table('Person')
                table = table.innerJoin(tablePerson, tablePerson['id'].eq(tableSchedule['person_id']))
                if specialityId:
                    cond.append(tablePerson['speciality_id'].eq(specialityId))
                if orgStructureId:
                    cond.append(tablePerson['orgStructure_id'].inlist(getOrgStructureDescendants(orgStructureId)))

        ids = db.getIdList(table,
                           tableScheduleItem['id'],
                           cond,
                           tableScheduleItem['time'].name(),
                           1)
        return ids[0] if ids else None


    def editMarks(self, onProcess, scheduleItemId=None):
        db = QtGui.qApp.db
        table = db.table('SuspendedAppointment')
        record = self.tblSuspendedAppointments.currentItem()
        if record:
            id = forceRef(record.value('id'))
            appointmentId = forceRef(record.value('appointment_id'))
            if self.lock('SuspendedAppointment', id):
                try:
                    dlg = CSuspendedAppointmentMarksDialog(self)
                    dlg.setMarksFromRecord(record, onProcess)
                    if dlg.exec_():
                        tmpRecord = table.newRecord(['id', 'processed', 'notified', 'note', 'appointment_id', 'refusal'])
                        tmpRecord.setValue('id', id)
                        tmpRecord.setValue('appointment_id', appointmentId)
                        dlg.storeMarksToRecord(tmpRecord)
                        if onProcess:
                            if not appointmentId:
                                #tmpRecord.setValue('appointment_id', self.findAppointment(record))
                                tmpRecord.setValue('appointment_id', scheduleItemId)
                        else:
                            if appointmentId:
                                freeScheduleItem(self, appointmentId, forceRef(record.value('client_id')))
                            tmpRecord.setNull('appointment_id')
                        db.updateRecord(table, tmpRecord)
                        self.updateSuspendedAppointmentsList(id)
                finally:
                    self.releaseLock()


    def findAppointments(self):
        def stepIterator(progressDialog):
            db = QtGui.qApp.db
            table = db.table('SuspendedAppointment')

            for idx in xrange(self.modelSuspendedAppointments.rowCount()):
                record = self.modelSuspendedAppointments.getRecordByRow(idx)
                if not forceBool(record.value('processed')):
                    id = forceRef(record.value('id'))
                    if self.lock('SuspendedAppointment', id):
                        try:
                            appointmentId = self.findAppointment(record)
                            if appointmentId:
                                tmpRecord = table.newRecord(['id', 'processed', 'notified', 'note', 'appointment_id'])
                                tmpRecord.setValue('id', id)
                                tmpRecord.setValue('processed', True)
                                tmpRecord.setValue('notified', 0)
                                tmpRecord.setValue('note', u'Номерок подобран при обработке журнала')
                                tmpRecord.setValue('appointment_id', appointmentId)
                                db.updateRecord(table, tmpRecord)
#                                self.updateSuspendedAppointmentsList(id)
                        finally:
                            self.releaseLock()
                yield 1

        pd = CSimpleProgressDialog(self)
        pd.setWindowTitle(u'Подбор талонов')
        pd.setStepCount(self.modelSuspendedAppointments.rowCount())
        pd.setAutoStart(True)
        pd.setAutoClose(False)
        pd.setStepIterator(stepIterator)
        pd.exec_()
        self.modelSuspendedAppointments.invalidateRecordsCache()
        self.tblSuspendedAppointments.update()


    def on_buttonBoxFilter_apply(self):
        def cmbToTristate(val):
            return val-1 if val>0 else None

        self.filter = {}
        if self.chkFilterLastName.isChecked():
            self.filter['lastName'] = forceStringEx(self.edtFilterLastName.text())
        if self.chkFilterFirstName.isChecked():
            self.filter['firstName'] = forceStringEx(self.edtFilterFirstName.text())
        if self.chkFilterPatrName.isChecked():
            self.filter['patrName'] = forceStringEx(self.edtFilterPatrName.text())
        if self.chkFilterBirthDay.isChecked():
            if self.chkFilterEndBirthDay.isChecked():
                self.filter['begBirthDay'] = self.edtFilterBegBirthDay.date()
                self.filter['endBirthDay'] = self.edtFilterEndBirthDay.date()
            else:
                self.filter['begBirthDay'] = self.filter['endBirthDay'] = self.edtFilterBegBirthDay.date()
        if self.chkFilterSex.isChecked():
            self.filter['sex'] = self.cmbFilterSex.currentIndex()
        if self.chkFilterContact.isChecked():
            self.filter['contact'] = forceStringEx(self.edtFilterContact.text())
        if self.chkFilterBegDateRange.isChecked():
            self.filter['begDateRange'] = self.edtFilterBegBegDate.date(), self.edtFilterEndBegDate.date()
            self.filter['begVisitBegDate'] = self.edtFilterBegBegDate.date()
            self.filter['endVisitBegDate'] = self.edtFilterEndBegDate.date()
        if self.chkFilterEndDateRange.isChecked():
            self.filter['endDateRange'] = self.edtFilterBegEndDate.date(), self.edtFilterEndEndDate.date()
            self.filter['begVisitEndDate'] = self.edtFilterBegEndDate.date()
            self.filter['endVisitEndDate'] = self.edtFilterEndEndDate.date()
        if self.chkFilterOrgStructure.isChecked():
            self.filter['orgStructureId'] = self.cmbFilterOrgStructure.value()
        if self.chkFilterSpeciality.isChecked():
            self.filter['specialityId'] = self.cmbFilterSpeciality.value()
        if self.chkFilterPerson.isChecked():
            self.filter['personId'] = self.cmbFilterPerson.value()
        if self.chkFilterExternalUserRole.isChecked():
            self.filter['externalUserRole'] = forceStringEx(self.edtFilterExternalUserRole.text())
        if self.chkFilterExternalUserName.isChecked():
            self.filter['externalUserName'] = forceStringEx(self.edtFilterExternalUserName.text())
        self.filter['processed'] = cmbToTristate(self.cmbFilterProcessed.currentIndex())
        self.filter['processedName'] = self.cmbFilterProcessed.currentText()
        self.filter['notified']  = cmbToTristate(self.cmbFilterNotification.currentIndex())
        self.filter['notifiedName']  = self.cmbFilterNotification.currentText()
        self.filter['scheduled'] = cmbToTristate(self.cmbFilterScheduled.currentIndex())
        self.filter['scheduledName'] = self.cmbFilterScheduled.currentText()
        if self.chkFilterNote.isChecked():
            self.filter['note'] = forceStringEx(self.edtFilterNote.text())
        if self.chkFilterExCreatePerson.isChecked():
            self.filter['createPersonId'] = self.cmbFilterExCreatePerson.value()
        if self.chkFilterExCreateDate.isChecked():
            self.filter['createDateRange'] = self.edtFilterExBegCreateDate.date(), self.edtFilterExEndCreateDate.date()
            self.filter['begCreateDate'] = self.edtFilterExBegCreateDate.date()
            self.filter['endCreateDate'] = self.edtFilterExEndCreateDate.date()
        if self.chkFilterExModifyPerson.isChecked():
            self.filter['modifyPersonId'] = self.cmbFilterExModifyPerson.value()
        if self.chkFilterExModifyDate.isChecked():
            self.filter['modifyDateRange'] = self.edtFilterExBegModifyDate.date(), self.edtFilterExEndModifyDate.date()
            self.filter['begModifyDate'] = self.edtFilterExBegModifyDate.date()
            self.filter['endModifyDate'] = self.edtFilterExEndModifyDate.date()
        self.updateSuspendedAppointmentsList()


    def on_buttonBoxFilter_reset(self):
        self.chkFilterLastName.setChecked(False)
        self.edtFilterLastName.setText('')
        self.chkFilterFirstName.setChecked(False)
        self.edtFilterFirstName.setText('')
        self.chkFilterPatrName.setChecked(False)
        self.edtFilterPatrName.setText('')
        self.chkFilterBirthDay.setChecked(False)
        self.edtFilterBegBirthDay.setDate(QDate())
        self.chkFilterEndBirthDay.setChecked(False)
        self.edtFilterEndBirthDay.setDate(QDate())
        self.chkFilterSex.setChecked(False)
        self.cmbFilterSex.setCurrentIndex(0)
        self.chkFilterContact.setChecked(False)
        self.edtFilterContact.setText('')
        self.chkFilterBegDateRange.setChecked(False)
        self.edtFilterBegBegDate.setDate(QDate.currentDate())
        self.edtFilterEndBegDate.setDate(QDate.currentDate().addMonths(1))
        self.chkFilterEndDateRange.setChecked(False)
        self.edtFilterBegEndDate.setDate(QDate.currentDate())
        self.edtFilterEndEndDate.setDate(QDate.currentDate().addMonths(1))
        self.chkFilterOrgStructure.setChecked(False)
        self.cmbFilterOrgStructure.setValue(None)
        self.chkFilterSpeciality.setChecked(False)
        self.cmbFilterSpeciality.setValue(None)
        self.chkFilterPerson.setChecked(False)
        self.cmbFilterPerson.setValue(None)
        self.chkFilterExternalUserRole.setChecked(False)
        self.edtFilterExternalUserRole.setText('')
        self.chkFilterExternalUserName.setChecked(False)
        self.edtFilterExternalUserName.setText('')
        self.cmbFilterProcessed.setCurrentIndex(1)
        self.cmbFilterNotification.setCurrentIndex(0)
        self.chkFilterNote.setChecked(False)
        self.edtFilterNote.setText('')
        self.cmbFilterScheduled.setCurrentIndex(0)
        self.chkFilterExCreatePerson.setChecked(False)
        self.cmbFilterExCreatePerson.setValue(None)
        self.chkFilterExCreateDate.setChecked(False)
        self.edtFilterExBegCreateDate.setDate(QDate())
        self.edtFilterExEndCreateDate.setDate(QDate())
        self.chkFilterExModifyPerson.setChecked(False)
        self.cmbFilterExModifyPerson.setValue(None)
        self.chkFilterExModifyDate.setChecked(False)
        self.edtFilterExBegModifyDate.setDate(QDate())
        self.edtFilterExEndModifyDate.setDate(QDate())

        self.on_buttonBoxFilter_apply()


    def editClient(self, clientId):
        if QtGui.qApp.userHasAnyRight([urAdmin, urRegTabWriteRegistry, urRegTabReadRegistry]):
            dialog = CClientEditDialog(self)
            try:
                if clientId:
                    dialog.load(clientId)
                if dialog.exec_():
                    clientId = dialog.itemId()
                    self.updateSuspendedAppointmentsList()
            finally:
                dialog.deleteLater()


    def currentClientId(self):
        return QtGui.qApp.currentClientId()


    def focusClients(self):
        self.tblSuspendedAppointments.setFocus(Qt.TabFocusReason)


##############################################
## SLOTS #####################################

    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelSuspendedAppointments_currentRowChanged(self, current, previous):
        self.updateClientInfo()


    @pyqtSignature('')
    def on_tblSuspendedAppointments_popupMenuAboutToShow(self):
        record = self.tblSuspendedAppointments.currentItem()
        appointmentId = forceRef(record.value('appointment_id')) if record else None
        self.actFilterAppointment.setEnabled(record is not None and appointmentId is None)
        # self.actSetProcessed.setEnabled(appointmentId is not None)
        self.actUnsetProcessed.setEnabled(record is not None)


    @pyqtSignature('')
    def on_actFilterAppointment_triggered(self):
        record = self.tblSuspendedAppointments.currentItem()
        if record:
            orgStructureId = forceRef(record.value('orgStructure_id'))
            specialityId   = forceRef(record.value('speciality_id'))
            personId       = forceRef(record.value('person_id'))
            begDate        = forceDate(record.value('begDate'))
            QtGui.qApp.setupDocFreeQueue(CSchedule.atAmbulance, orgStructureId, specialityId, personId, begDate)


    @pyqtSignature('')
    def on_actEditClient_triggered(self):
        clientId = self.currentClientId()
        self.editClient(clientId)
        self.focusClients()


    @pyqtSignature('')
    def on_actSetProcessed_triggered(self):
        self.editMarks(True)

    # @pyqtSignature('')
    # def on_actSetProcessed_triggered(self):
    #     self.editMarks(True)


    @pyqtSignature('')
    def on_actUnsetProcessed_triggered(self):
        self.editMarks(False)


    @pyqtSignature('bool')
    def on_chkFilterBirthDay_toggled(self, value):
        self.edtFilterEndBirthDay.setEnabled(value and self.chkFilterEndBirthDay.isChecked())


    @pyqtSignature('QAbstractButton*')
    def on_buttonBoxFilter_clicked(self, button):
        buttonCode = self.buttonBoxFilter.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_buttonBoxFilter_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_buttonBoxFilter_reset()
        self.focusSuspendedAppointmentsList()
        self.updateClientInfo()


    @pyqtSignature('')
    def on_btnFindAppointments_clicked(self):
        self.findAppointments()


    def closeEvent(self, event):
        self.saveDialogPreferences()
        QtGui.QScrollArea.closeEvent(self, event)



class CSuspendedAppointmentModel(CTableModel):

    class CLocClientColumn(CCol):
        def __init__(self, title, fields, defaultWidth, clientCache):
            CCol.__init__(self, title, fields, defaultWidth, 'l')
            self.clientCache = clientCache

        def format(self, values):
            val = values[0]
            clientId  = forceRef(val)
            clientRecord = self.clientCache.get(clientId)
            if clientRecord:
                name  = formatName(clientRecord.value('lastName'),
                                   clientRecord.value('firstName'),
                                   clientRecord.value('patrName'))
                return toVariant(name)
            return CCol.invalid


    class CLocClientBirthDateColumn(CCol):
        def __init__(self, title, fields, defaultWidth, clientCache, extraFields=[]):
            CCol.__init__(self, title, fields, defaultWidth, 'l')
            self.extraFields = extraFields
            self.clientCache = clientCache

        def format(self, values):
            val = values[0]
            clientId  = forceRef(val)
            clientRecord = self.clientCache.get(clientId)
            if clientRecord:
                return toVariant(forceString(clientRecord.value('birthDate')))
            return CCol.invalid


    class CLocClientSexColumn(CCol):
        def __init__(self, title, fields, defaultWidth, clientCache, extraFields=[]):
            CCol.__init__(self, title, fields, defaultWidth, 'l')
            self.extraFields = extraFields
            self.clientCache = clientCache

        def format(self, values):
            val = values[0]
            clientId  = forceRef(val)
            clientRecord = self.clientCache.get(clientId)
            if clientRecord:
                return toVariant(formatSex(clientRecord.value('sex')))
            return CCol.invalid


    class CScheduleItemCol(CCol):
        def __init__(self, title, fields, defaultWidth):
            CCol.__init__(self, title, fields, defaultWidth, 'l')

            db = QtGui.qApp.db
            tableScheduleItem = db.table('Schedule_Item')
            tableSchedule = db.table('Schedule')
            tablePerson = db.table('vrbPersonWithSpeciality')
            tableOrgStructure = db.table('OrgStructure')
            cols = ['Schedule_Item.id',
                    'Schedule_Item.client_id',
                    'Schedule_Item.time',
                    'Schedule.date',
                    'OrgStructure.name AS osName',
                    'vrbPersonWithSpeciality.name AS personName',
                    '(Schedule_Item.deleted OR Schedule.deleted) AS deleted'
                   ]
            cond = [tableSchedule['id'].eq(tableScheduleItem['master_id']),
                    tableScheduleItem['deleted'].eq(0),
                    tableSchedule['deleted'].eq(0)
                    ]
            table = tableScheduleItem.innerJoin(tableSchedule, db.joinAnd(cond))
            table = table.innerJoin(tablePerson, tablePerson['id'].eq(tableSchedule['person_id']))
            table = table.innerJoin(tableOrgStructure, tableOrgStructure['id'].eq(tablePerson['orgStructure_id']))
            self.recordCache = CTableRecordCache(db, table, cols)

        def invalidateRecordsCache(self):
            self.recordCache.invalidate()

        def format(self, values):
            clientId = forceRef(values[1])
            record = self.recordCache.get(values[0])
            if record and not forceBool(record.value('deleted')) and clientId == forceRef(record.value('client_id')):
                date = forceDate(record.value('date'))
                time = forceTime(record.value('time'))
                personName = forceString(record.value('personName'))
#                osName = forceString(record.value('osName'))
                return toVariant(forceString(QDateTime(date, time))+' '+personName)
            return QVariant()


    def __init__(self, parent):
        self.clientCache = CTableRecordCache(QtGui.qApp.db, 'Client', ('id', 'lastName', 'firstName', 'patrName', 'birthDate', 'sex'), 300)
        CTableModel.__init__(self, parent)
        self.addColumn(CIntCol(u'Код пациента', ('client_id',), 10))
        self.addColumn(self.CLocClientColumn( u'Ф.И.О.', ('client_id',), 60, self.clientCache))
        self.addColumn(self.CLocClientBirthDateColumn(u'Дата рожд.', ('client_id',), 20, self.clientCache, ['birthDate']))
        self.addColumn(self.CLocClientSexColumn(u'Пол', ('client_id',), 5, self.clientCache, ['sex']))
        self.addColumn(CTextCol(u'Телефон',    ('contact', ),  10))
        self.addColumn(CDateCol(u'С',   ('begDate',), 10))
        self.addColumn(CDateCol(u'По',  ('endDate',), 10))
        self.addColumn(CDesignationCol(u'Подразделение', ('orgStructure_id',), ('OrgStructure', 'name'), 10))
        self.addColumn(CRefBookCol(u'Специальность',     ('speciality_id',),    'rbSpeciality', 30))
        self.addColumn(CRefBookCol(u'Врач',              ('person_id',),        'vrbPerson', 30))
        self.addColumn(CBoolCol(u'Отработан',            ('processed',),        7))
        self.addColumn(self.CScheduleItemCol(u'Талон на приём к врачу', ('appointment_id', 'client_id', ), 50))
        self.addColumn(CEnumCol(u'Оповещён',      ('notified', ), (u'', u'телефон', u'СМС', u'эл.почта'),  10))
        self.addColumn(CTextCol(u'Примечание',    ('note', ),  10))
        self.addColumn(CTextCol(u'Роль',          ('externalUserRole', ),  10))
        self.addColumn(CTextCol(u'Внешний пользователь',  ('externalUserName', ),  10))
        self.addColumn(CTextCol(u'Причина',       ('reason', ),  10))
        self.addColumn(CDateTimeCol(u'Создано',   ('createDatetime',), 20))
        self.addColumn(CRefBookCol(u'Создал',    ('createPerson_id',), 'vrbPersonWithSpeciality', 30))
        self.addColumn(CDateTimeCol(u'Изменено',  ('modifyDatetime',), 20))
        self.addColumn(CRefBookCol(u'Изменил',    ('modifyPerson_id',), 'vrbPersonWithSpeciality', 30))
        self.setTable('SuspendedAppointment')
        self.headerSortingCol = {}
        self._mapColumnToOrder = {'client_ID'          :'Client.id',
                                  'client_id'          :'CONCAT(Client.lastName, Client.firstName, Client.patrName)',
                                  'birthDate'          :'Client.birthDate',
                                  'sex'                :'Client.sex',
                                  'contact'            :'SuspendedAppointment.contact',
                                  'begDate'            :'SuspendedAppointment.begDate',
                                  'endDate'            :'SuspendedAppointment.endDate',
                                  'orgStructure_id'    :'OrgStructure.name',
                                  'speciality_id'      :'rbSpeciality.name',
                                  'person_id'          :'vrbPerson.name',
                                  'processed'          :'SuspendedAppointment.processed',
                                  'appointment_id'     :'Schedule_Item.time',
                                  'notified'           :'SuspendedAppointment.notified',
                                  'note'               :'SuspendedAppointment.note',
                                  'externalUserRole'   :'SuspendedAppointment.externalUserRole',
                                  'externalUserName'   :'SuspendedAppointment.externalUserName',
                                  'reason'             :'SuspendedAppointment.reason',
                                  'createDatetime'     :'SuspendedAppointment.createDatetime',
                                  'createPerson_id'    :'createPerson',
                                  'modifyDatetime'     :'SuspendedAppointment.modifyDatetime',
                                  'modifyPerson_id'    :'modifyPerson'
                                  }


    def getOrder(self, fieldName, column):
        if hasattr(self._cols[column], 'extraFields'):
            if len(self._cols[column].extraFields) > 0:
                fieldName = self._cols[column].extraFields[0]
        return self._mapColumnToOrder[fieldName]


    def invalidateRecordsCache(self):
        self.clientCache.invalidate()
        CTableModel.invalidateRecordsCache(self)


class CSuspendedAppointmentMarksDialog(CDialogBase, Ui_SuspendedAppointmentMarksDialog):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.setupDirtyCather()
        self.setCancelVariant()


    def setMarksFromRecord(self, record, onProcess):
        self.chkProcessed.setVisible(False)
        self.lblProcessed.setVisible(False)
        if onProcess:
            self.chkProcessed.setChecked(True)
            self.cmbNotified.setCurrentIndex(1) # телефон
            self.setWindowTitle(u'Отработать')
            self.cmbCancelVariant.setVisible(False)
            self.lblCancelVariant.setVisible(False)
            self.cmbOrgStructure.setVisible(False)
            self.lblOrgStructure.setVisible(False)
            self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(True)
        else:
            self.chkProcessed.setChecked(True)
            self.cmbNotified.setCurrentIndex(0) # нет
            self.setWindowTitle(u'Отменить отработку')
            self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(False)
        setTextEditValue(self.edtNote,      record, 'note')
        self.setIsDirty(False)

    def setCancelVariant(self):
        self.cmbCancelVariant.setTable('rbScheduleCancel', True)
        self.cmbCancelVariant.setCurrentIndex(0)

    @pyqtSignature('int')
    def on_cmbCancelVariant_currentIndexChanged(self, index):
        if index != 0:
            self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(True)
        else:
            self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(False)


    def storeMarksToRecord(self, record):
        getCheckBoxValue(self.chkProcessed, record, 'processed')
        getComboBoxValue(self.cmbNotified,  record, 'notified')
        getTextEditValue(self.edtNote,      record, 'note')
        getComboBoxValue(self.cmbCancelVariant, record, 'refusal')



