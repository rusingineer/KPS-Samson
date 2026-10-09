# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2026 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
##
## Журнал планирования профилактического наблюдения
##
#############################################################################
from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDate, QDateTime, QMetaObject, QVariant, pyqtSignature, SIGNAL

from Surveillance.SurveillanceDialog import CSurveillanceDialog, CConsistsDiagnosisModel, isSurveillanceActive
from library.database                   import CTableRecordCache
from library.DialogBase                 import CDialogBase, CConstructHelperMixin
from library.interchange                import setTextEditValue, getComboBoxValue, getTextEditValue, getCheckBoxValue
from library.PreferencesMixin           import CDialogPreferencesMixin
from library.PrintInfo                  import CInfoContext
from library.PrintTemplates             import applyTemplate, CPrintAction, getPrintTemplates
from library.RecordLock                 import CRecordLockMixin
from library.SimpleProgressDialog       import CSimpleProgressDialog
from library.TableModel                 import CBoolCol, CEnumCol, CDateCol, CDesignationCol, CTextCol, CDateTimeCol, CCol, CRefBookCol, CTableModel
from library.Utils import formatName, toVariant, forceString, withWaitCursor, forceRef, forceTime, forceBool, \
    formatRecordsCount, forceDate, forceStringEx, formatSex, getPref, setPref
from library.ICDUtils                   import MKBwithoutSubclassification
from Registry.ProphylaxisPlanningInfo   import CProphylaxisPlanningInfo, CProphylaxisPlanningInfoList
from Orgs.Utils                         import getOrgStructureDescendants
from Registry.RegistryWindow            import CSchedulesModel, CVisitsBySchedulesModel, convertFilterToTextItem
from Registry.ProphylaxisPlanningEditor import CProphylaxisPlanningEditor
from Registry.Utils                     import getClientBanner
from Timeline.Schedule                  import CSchedule
from Users.Rights                       import urEditProphylaxisPlanning

from Registry.Ui_ProphylaxisPlanning import Ui_ProphylaxisPlanningWindow
from Registry.Ui_ProphylaxisPlanningMarksDialog import Ui_ProphylaxisPlanningMarksDialog
from Registry.Ui_ProphylaxisPlanningVisitEditor import Ui_ProphylaxisPlanningVisitEditor


class CProphylaxisPlanningWindow(QtGui.QScrollArea, Ui_ProphylaxisPlanningWindow, CDialogPreferencesMixin, CConstructHelperMixin, CRecordLockMixin):
    def __init__(self, parent):
        QtGui.QScrollArea.__init__(self, parent)
        CRecordLockMixin.__init__(self)
        self.addModels('ProphylaxisPlannings', CProphylaxisPlanningModel(self))
        self.addModels('Schedules', CSchedulesModel(self))
        self.addModels('VisitsBySchedules',    CVisitsBySchedulesModel(self))
        self.addModels('ProphylaxisPlanningType',    CProphylaxisPlanningTypeTableModel(self))
        self.addObject('actFilterAppointment', QtGui.QAction(u'Подобрать номерок', self))
        self.addObject('actSetProcessed',      QtGui.QAction(u'Отработать', self))
        self.addObject('actUnsetProcessed',    QtGui.QAction(u'Отменить', self))
        self.addObject('actProphylaxisEdit',   QtGui.QAction(u'Редактировать', self))
        self.addObject('actUpdateVisit',       QtGui.QAction(u'Редактировать Явку', self))
        self.addObject('actPlanningClientList', QtGui.QAction(u'Контрольная карта диспансерного наблюдения', self))
        self.addObject('actPlanningClientInfo', QtGui.QAction(u'Контрольная карта диспансерного наблюдения', self))
        self.setObjectName('ProphylaxisPlanningWindow')
        self.internal = QtGui.QWidget(self)
        self.setWidget(self.internal)
        self.setupUi(self.internal)

        self.setWindowTitle(self.internal.windowTitle())
        self.chkFilterExternalUserRole.setVisible(False)
        self.edtFilterExternalUserRole.setVisible(False)
        self.chkFilterExternalUserName.setVisible(False)
        self.edtFilterExternalUserName.setVisible(False)
        self.setWidgetResizable(True)
        QMetaObject.connectSlotsByName(self) # т.к. в setupUi параметр не self
        db = QtGui.qApp.db
        self.personCache = CTableRecordCache(db, db.forceTable('vrbPersonWithSpeciality'), u'*', capacity=None)
        suspenedTemplates = getPrintTemplates(['ProphylaxisPlanningList'])
        if not suspenedTemplates:
            self.btnPrint.setId(-1)
        else:
            for template in suspenedTemplates:
                action = CPrintAction(template.name, template.id, self.btnPrint, self.btnPrint)
                self.btnPrint.addAction(action)
            self.btnPrint.menu().addSeparator()
            self.btnPrint.addAction(CPrintAction(u'Напечатать список визитов', -1, self.btnPrint, self.btnPrint))
        self.setModels(self.tblProphylaxisPlannings, self.modelProphylaxisPlannings, self.selectionModelProphylaxisPlannings)
        self.setModels(self.tblSchedules, self.modelSchedules, self.selectionModelSchedules)
        self.setModels(self.tblVisitsBySchedules, self.modelVisitsBySchedules, self.selectionModelVisitsBySchedules)
        self.setModels(self.tblProphylaxisPlanningType, self.modelProphylaxisPlanningType, self.selectionModelProphylaxisPlanningType)
        self.tblProphylaxisPlannings.createPopupMenu([self.actFilterAppointment,
                                                      self.actSetProcessed,
                                                      self.actUnsetProcessed,
                                                      '-',
                                                      self.actProphylaxisEdit,
                                                      self.actUpdateVisit,
                                                      '-',
                                                      self.actPlanningClientList,
                                                      '-',
                                                      ]
                                                     )
        self.txtClientInfoBrowser.actions.append(self.actPlanningClientInfo)
        self.tblProphylaxisPlannings.addPopupDelRow()
        self.edtFilterBegBirthDay.canBeEmpty(True)
        self.edtFilterEndBirthDay.canBeEmpty(True)
        self.edtFilterBegDate.canBeEmpty(True)
        self.edtFilterEndDate.canBeEmpty(True)
        self.cmbFilterSpeciality.setTable('rbSpeciality', True)
        self.cmbFilterSceneVisit.setTable('rbScene')
        self.cmbFilterExportSystem.setTable('rbExternalSystem', True)

        self.tblProphylaxisPlanningType.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tblProphylaxisPlanningType.installEventFilter(self)
        self.tblProphylaxisPlanningType.model().setIdList(self.setProphylaxisPlanningTypeIdList())

        self.tblProphylaxisPlannings.enableColsHide()
        self.tblProphylaxisPlannings.enableColsMove()
        self.tblSchedules.enableColsHide()
        self.tblSchedules.enableColsMove()
        self.tblVisitsBySchedules.enableColsHide()
        self.tblVisitsBySchedules.enableColsMove()

        self.on_buttonBoxFilter_reset()
        # Мешает активации/деактивации окна в CMdiArea (s11main.CS11MainWindow.centralWidget)
        # self.focusProphylaxisPlanningsList()

        preferences = getPref(QtGui.qApp.preferences.windowPrefs, 'CProphylaxisPlanningWindow', {})
        self.tblProphylaxisPlannings.loadPreferences(preferences)

        self.connect(self.tblProphylaxisPlannings.horizontalHeader(), SIGNAL('sectionClicked(int)'), self._setSAOrderByColumn)
        self.connect(self.tblSchedules.horizontalHeader(), SIGNAL('sectionClicked(int)'), self._setSchedulesOrderByColumn)
        self.connect(self.tblVisitsBySchedules.horizontalHeader(), SIGNAL('sectionClicked(int)'), self._setVisitsBySchedulesOrderByColumn)

    def closeEvent(self, event):
        preferences = self.tblProphylaxisPlannings.savePreferences()
        setPref(QtGui.qApp.preferences.windowPrefs, 'CProphylaxisPlanningWindow', preferences)
        QtGui.QFrame.closeEvent(self, event)

    @pyqtSignature('')
    def on_actPlanningClientList_triggered(self):
        clientId, diagnosisIdList, MKB = self.getDiagnosisIdList()
        tableClient = CSurveillanceDialog(self, isFake=True)
        tableClient.surveillancePlanningShow(clientId)

    @pyqtSignature('')
    def on_actPlanningClientInfo_triggered(self):
        clientId, diagnosisIdList, MKB = self.getDiagnosisIdList()
        tableClient = CSurveillanceDialog(self, isFake=True)
        tableClient.surveillancePlanningShow(clientId)

    def getDiagnosisIdList(self):
        record = self.tblProphylaxisPlannings.currentItem()
        clientId = forceRef(record.value('client_id'))
        MKB = forceString(record.value('MKB'))
        diagList = CConsistsDiagnosisModel(self)
        diagnosisIdList = diagList.getDiagnosisIdList(clientId, {'begDate': QDate.currentDate()})
        return clientId, diagnosisIdList, MKB

    def getSelectProphylaxisPlanningTypeList(self):
        return self.tblProphylaxisPlanningType.selectedItemIdList()

    def setSelectProphylaxisPlanningTypeList(self, prophylaxisPlanningTypeList):
        self.tblProphylaxisPlanningType.clearSelection()
        if prophylaxisPlanningTypeList:
            self.tblProphylaxisPlanningType.setSelectedItemIdList(prophylaxisPlanningTypeList)

    def setProphylaxisPlanningTypeIdList(self):
        db = QtGui.qApp.db
        tablePPT = db.table('rbProphylaxisPlanningType')
        cond = []
        return db.getDistinctIdList(tablePPT,
                                    tablePPT['id'].name(),
                                    where=cond,
                                    order=u'rbProphylaxisPlanningType.code ASC, rbProphylaxisPlanningType.name ASC')

    def _setSAOrderByColumn(self, column):
        self.tblProphylaxisPlannings.setOrder(column)
        self.updateProphylaxisPlanningsList(self.tblProphylaxisPlannings.currentItemId())

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

    @pyqtSignature('int')
    def on_btnPrint_printByTemplate(self, templateId):
        if templateId == -1:
            self.tblProphylaxisPlannings.setReportHeader(u'Журнал планирования профилактического наблюдения')
            self.tblProphylaxisPlannings.setReportDescription(self.getProphylaxisPlanningFilterAsText())
            self.tblProphylaxisPlannings.printContent()
            self.tblProphylaxisPlannings.setFocus(Qt.TabFocusReason)
        else:
            idList = self.tblProphylaxisPlannings.model().idList()
            context = CInfoContext()
            ProphylaxisPlanningInfo = context.getInstance(CProphylaxisPlanningInfo, self.tblProphylaxisPlannings.currentItemId())
            ProphylaxisPlanningInfoList = context.getInstance(CProphylaxisPlanningInfoList, tuple(idList))
            data = {'ProphylaxisPlanningList': ProphylaxisPlanningInfoList,
                    'ProphylaxisPlanning'    : ProphylaxisPlanningInfo}
            QtGui.qApp.call(self, applyTemplate, (self, templateId, data))

    def getProphylaxisPlanningFilterAsText(self):
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
            ('begVisitDate', u'Планируемый период визита с', forceString),
            ('endVisitDate', u'Планируемый период визита по', forceString),
            ('orgStructureId', u'Подразделение',
                lambda id: forceString(db.translate('OrgStructure', 'id', id, 'name'))),
            ('specialityId', u'Специальность',
                lambda id: forceString(db.translate('rbSpeciality', 'id', id, 'name'))),
            ('personId', u'Врач',
                lambda id: forceString(db.translate('vrbPersonWithSpeciality', 'id', id, 'name'))),
            ('MKB', u'Диагноз', forceString),
            ('prophylaxisPlanningType_id', u'Тип планирования профилактики',
                lambda id: forceString(db.translate('rbProphylaxisPlanningType', 'id', id, 'name'))),
            ('scene_id', u'Место',
                lambda id: forceString(db.translate('rbScene', 'id', id, 'name'))),
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
        return '\n'.join([': '.join(item) for item in resList])

    @withWaitCursor
    def updateProphylaxisPlanningsList(self, posToId=None):
        db = QtGui.qApp.db
        table = db.table('ProphylaxisPlanning')
        tableClient = db.table('Client')
        queryTable = table.innerJoin(tableClient, tableClient['id'].eq(table['client_id']))
        cols = [table['id'].name()]
        cond = [table['deleted'].eq(0),
                tableClient['deleted'].eq(0),
               ]
        order = self.tblProphylaxisPlannings.order() if self.tblProphylaxisPlannings.order() else table['id'].name()
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
        if u'rbProphylaxisPlanningType.name' in order:
            tableProphylaxisPlanningType = db.table('rbProphylaxisPlanningType')
            queryTable = queryTable.leftJoin(tableProphylaxisPlanningType, tableProphylaxisPlanningType['id'].eq(table['prophylaxisPlanningType_id']))
        if u'rbScene.name' in order:
            tableScene = db.table('rbScene')
            queryTable = queryTable.leftJoin(tableScene, tableScene['id'].eq(table['scene_id']))
        if u'Schedule' in order:
            tableScheduleItem = db.table('Schedule_Item')
            tableSchedule = db.table('Schedule')
            condAppointment = [tableScheduleItem['id'].eq(table['appointment_id']),
                               tableScheduleItem['deleted'].eq(0),
                               tableScheduleItem['client_id'].eq(tableClient['id']),
                               ]
            queryTable = queryTable.leftJoin(tableScheduleItem, db.joinAnd(condAppointment))
            queryTable = queryTable.leftJoin(tableSchedule, db.joinAnd([tableSchedule['id'].eq(tableScheduleItem['master_id']), tableSchedule['deleted'].eq(0)]))

        prophylaxisPlanningsList = self.filter.get('prophylaxisPlanningsList', None)
        if prophylaxisPlanningsList:
            cond.append(table['prophylaxisPlanningType_id'].inlist(prophylaxisPlanningsList))

        if self.chkClientId.isChecked():
            clientId = self.filter.get('clientId')
            if clientId:
                cond.append(tableClient['id'].eq(clientId))
        else:
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

        dataRange = self.filter.get('dateRange')
        if dataRange:
            begDate, endDate = dataRange
            if begDate:
                cond.append(table['endDate'].ge(begDate))
            if endDate:
                cond.append(table['endDate'].le(endDate))

        notVisit = self.filter.get('notVisit')
        if notVisit == 1:
            cond.append(table['visit_id'].isNull())
        elif notVisit == 0:
            cond.append(table['visit_id'].isNotNull())

        orgStructureId = self.filter.get('orgStructureId')
        if orgStructureId:
            cond.append(table['orgStructure_id'].inlist(getOrgStructureDescendants(orgStructureId)))

        specialityId = self.filter.get('specialityId')
        if specialityId:
            cond.append(table['speciality_id'].eq(specialityId))

        personId = self.filter.get('personId')
        if personId:
            cond.append(table['person_id'].eq(personId))

        sceneId = self.filter.get('sceneId')
        if sceneId:
            cond.append(table['scene_id'].eq(sceneId))

        if 'actionMKB' in self.filter:
            if 'actionMKBFrom' in self.filter:
                actionMKBFrom = self.filter.get('actionMKBFrom', None)
            if 'actionMKBTo' in self.filter:
                actionMKBTo = self.filter.get('actionMKBTo', None)
            if actionMKBFrom or actionMKBTo:
                if actionMKBFrom and not actionMKBTo:
                   actionMKBTo = u'U'
                elif not actionMKBFrom and actionMKBTo:
                    actionMKBFrom = u'A'
                cond.append(table['MKB'].ge(actionMKBFrom))
                cond.append(table['MKB'].le(actionMKBTo))

        if 'exportStatus' in self.filter:
            exportStatus = self.filter.get('exportStatus', None)
            exportSystem = self.filter.get('exportSystem', None)
            tableExport = db.table('ProphylaxisPlanning_Export')
            queryTable = queryTable.leftJoin(tableExport, tableExport['master_id'].eq(table['id']))
            if exportStatus == 0:
                cond.append(tableExport['id'].isNotNull())
                if exportSystem:
                    cond.append(tableExport['system_id'].eq(exportSystem))
            else:
                if exportSystem:
                    cond.append(db.joinOr((db.joinAnd((tableExport['id'].isNotNull(), tableExport['system_id'].ne(exportSystem))), tableExport['id'].isNull())))
                else:
                    cond.append(tableExport['id'].isNull())

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

        cond.append(db.joinOr([table['parent_id'].isNotNull(), table['begDate'].isNotNull(), table['endDate'].isNotNull()]))

        idList = db.getDistinctIdList(queryTable,
                                      cols,
                                      cond,
                                      order
                                      )
        self.tblProphylaxisPlannings.setIdList(idList, posToId)
        self.lblRecordCount.setText(formatRecordsCount(len(idList)))
        self.focusProphylaxisPlanningsList()

    def update(self):
        self.updateProphylaxisPlanningsList(self.getCurrentClientId())
        # super(CProphylaxisPlanningWindow, self).update()

    def focusProphylaxisPlanningsList(self):
        self.tblProphylaxisPlannings.setFocus(Qt.TabFocusReason)

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
        record = self.tblProphylaxisPlannings.currentItem()
        if record:
            clientId = forceRef(record.value('client_id'))
            isActive = isSurveillanceActive(clientId, {}, {'begDate': QDate.currentDate()})
            self.actPlanningClientList.setEnabled(bool(isActive))
            self.actPlanningClientInfo.setEnabled(bool(isActive))
            return clientId
        self.actPlanningClientList.setEnabled(False)
        self.actPlanningClientInfo.setEnabled(False)
        return None

    def findAppointment(self, record):
        db = QtGui.qApp.db
        clientId = forceRef(record.value('client_id'))
        personId = forceRef(record.value('person_id'))
        specialityId = forceRef(record.value('speciality_id'))
        orgStructureId = forceRef(record.value('orgStructure_id'))
        begDate = forceDate(record.value('begDate'))
        # endDate = forceDate(record.value('endDate'))

        tableScheduleItem = db.table('Schedule_Item')
        tableSchedule = db.table('Schedule')
        table = tableScheduleItem.innerJoin(tableSchedule, tableSchedule['id'].eq(tableScheduleItem['master_id']))
        cond = [ tableScheduleItem['deleted'].eq(0),
                 tableSchedule['deleted'].eq(0),
                 tableSchedule['date'].ge(begDate),
                 # tableSchedule['date'].le(endDate),
                 tableScheduleItem['client_id'].eq(clientId),
               ]
        if personId:
            cond.append(tableSchedule['person_id'].eq(personId))
        else:
            tablePerson = db.table('Person')
            if specialityId or orgStructureId:
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

    def editMarks(self, onProcess):
        db = QtGui.qApp.db
        table = db.table('ProphylaxisPlanning')
        record = self.tblProphylaxisPlannings.currentItem()
        if record:
            id = forceRef(record.value('id'))
            appointmentId = forceRef(record.value('appointment_id'))
            if self.lock('ProphylaxisPlanning', id):
                try:
                    dlg = CProphylaxisPlanningMarksDialog(self)
                    dlg.setMarksFromRecord(record, onProcess)
                    if dlg.exec_():
                        tmpRecord = table.newRecord(['id', 'processed', 'notified', 'note', 'appointment_id'])
                        tmpRecord.setValue('id', id)
                        tmpRecord.setValue('appointment_id', appointmentId)
                        dlg.storeMarksToRecord(tmpRecord)
                        if onProcess:
                            if not appointmentId:
                                tmpRecord.setValue('appointment_id', self.findAppointment(record))
                        else:
                            tmpRecord.setNull('appointment_id')
                        db.updateRecord(table, tmpRecord)
                        self.updateProphylaxisPlanningsList(id)
                finally:
                    self.releaseLock()

    def createVisitEditor(self, items, recordPP, dlg):
        visitIdList = []
        prophylaxisPlanningIdList = []
        removeDate = None
        for item in items:
            visitId = forceRef(item.value('visit_id'))
            if visitId and visitId not in visitIdList:
                visitIdList.append(visitId)
            prophylaxisPlanningId = forceRef(item.value('id'))
            if prophylaxisPlanningId and prophylaxisPlanningId not in prophylaxisPlanningIdList:
                prophylaxisPlanningIdList.append(prophylaxisPlanningId)
            if not removeDate:
                removeDate = forceDate(item.value('removeDate'))
        record = recordPP
        takenDate = forceDate(record.value('takenDate'))
        MKB = forceStringEx(record.value('MKB'))
        MKB = MKB[:3]
        clientId = forceRef(record.value('client_id'))
        if MKB and clientId:
            db = QtGui.qApp.db
            tableVisit = db.table('Visit')
            tableEvent = db.table('Event')
            tableDiagnosis = db.table('Diagnosis')
            tableDiagnostic = db.table('Diagnostic')
            tableDispanser = db.table('rbDispanser')
            queryTable = tableEvent.innerJoin(tableVisit, tableVisit['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.innerJoin(tableDiagnostic, tableDiagnostic['event_id'].eq(tableEvent['id']))
            queryTable = queryTable.innerJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
            queryTable = queryTable.innerJoin(tableDispanser, tableDispanser['id'].eq(tableDiagnostic['dispanser_id']))
            cond = [#tableVisit['date'].dateGe(takenDate),
                    tableDiagnosis['client_id'].eq(clientId),
                    tableEvent['client_id'].eq(clientId),
                    tableDiagnosis['MKB'].like(MKB[:3]+'%'),
                    tableDiagnostic['dispanser_id'].isNotNull(),
                    tableVisit['deleted'].eq(0),
                    tableDiagnosis['deleted'].eq(0),
                    tableDiagnostic['deleted'].eq(0),
                    tableEvent['deleted'].eq(0)
                    ]
            if visitIdList:
                cond.append(tableVisit['id'].notInlist(visitIdList))
            if removeDate:
                cond.append(tableVisit['date'].dateLe(removeDate))
            cond.append(u'''NOT EXISTS(SELECT ProphylaxisPlanning.id
            FROM ProphylaxisPlanning
            WHERE ProphylaxisPlanning.visit_id = Visit.id
            AND ProphylaxisPlanning.MKB LIKE '%s'
            AND ProphylaxisPlanning.deleted = 0 %s)'''%(MKB[:3]+'%', (u'AND ProphylaxisPlanning.id NOT IN (%s)'%(u','.join(str(ppId) for ppId in prophylaxisPlanningIdList if ppId))) if prophylaxisPlanningIdList else u''))
            dlg.setFilter(cond, queryTable)
        return dlg

    def updateVisit(self):
        record = self.tblProphylaxisPlannings.currentItem()
        if record:
            id = forceRef(record.value('id'))
            if id:
                if self.lock('ProphylaxisPlanning', id):
                    try:
                        db = QtGui.qApp.db
                        db.transaction()
                        try:
                            table = db.table('ProphylaxisPlanning')
                            tableVisit = db.table('Visit')
                            recordPP = db.getRecordEx(table, '*', [table['id'].eq(id), table['deleted'].eq(0)])
                            parentId = forceRef(recordPP.value('parent_id')) if recordPP else None
                            if parentId:
                                items = db.getRecordList(table, '*', [table['parent_id'].eq(parentId), table['deleted'].eq(0)], order = u'ProphylaxisPlanning.begDate, ProphylaxisPlanning.endDate')
                                visitId = forceRef(recordPP.value('visit_id'))
                                dlg = CProphylaxisPlanningVisitEditor(self)
                                dlg = self.createVisitEditor(items, recordPP, dlg)
                                dlg.setVisitId(visitId)
                                if dlg.exec_():
                                    personId = toVariant(None)
                                    sceneId = toVariant(None)
                                    orgStructureId = toVariant(None)
                                    specialityId = toVariant(None)
                                    newVisitId = dlg.getVisitId()
                                    if newVisitId:
                                        visitCache = self.modelProphylaxisPlannings.cols()[CProphylaxisPlanningModel.Col_VisitId].caches
                                        visitRecord = visitCache.get(newVisitId, None) if newVisitId else None
                                        if not visitRecord:
                                            visitRecord = db.getRecordEx(tableVisit, '*', [tableVisit['id'].eq(newVisitId), tableVisit['deleted'].eq(0)])
                                            if visitRecord:
                                                self.modelProphylaxisPlannings.cols()[CProphylaxisPlanningModel.Col_VisitId].caches[newVisitId] = visitRecord
                                        if visitRecord:
                                            personId = visitRecord.value('person_id')
                                            sceneId = visitRecord.value('scene_id')
                                            personRecord = self.personCache.get(personId) if personId else None
                                            if personRecord:
                                                orgStructureId = personRecord.value('orgStructure_id')
                                                specialityId = personRecord.value('speciality_id')
                                        MKB = forceStringEx(recordPP.value('MKB'))
                                        MKBCaches = self.modelProphylaxisPlannings.cols()[CProphylaxisPlanningModel.Col_VisitId].MKBCaches
                                        MKBRecord = MKBCaches.get((newVisitId, MKB), None) if (newVisitId and MKB) else None
                                        if not MKBRecord and MKB:
                                            tableEvent = db.table('Event')
                                            tableDiagnosis = db.table('Diagnosis')
                                            tableDiagnostic = db.table('Diagnostic')
                                            tableDispanser = db.table('rbDispanser')
                                            queryTable = tableEvent.innerJoin(tableVisit, tableVisit['event_id'].eq(tableEvent['id']))
                                            queryTable = queryTable.innerJoin(tableDiagnostic, tableDiagnostic['event_id'].eq(tableEvent['id']))
                                            queryTable = queryTable.innerJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
                                            queryTable = queryTable.innerJoin(tableDispanser, tableDispanser['id'].eq(tableDiagnostic['dispanser_id']))
                                            cond = [tableVisit['id'].eq(newVisitId),
                                                    db.joinOr([tableDiagnosis['MKB'].eq(MKB), tableDiagnosis['MKB'].like(MKB[:3]+'%')]),
                                                    tableDiagnostic['dispanser_id'].isNotNull(),
                                                    tableVisit['deleted'].eq(0),
                                                    tableDiagnosis['deleted'].eq(0),
                                                    tableDiagnostic['deleted'].eq(0),
                                                    tableEvent['deleted'].eq(0)
                                                    ]
                                            MKBRecord = db.getRecordEx(queryTable, 'Diagnosis.MKB', cond)
                                            if MKBRecord:
                                                self.modelProphylaxisPlannings.cols()[CProphylaxisPlanningModel.Col_VisitId].MKBCaches[(newVisitId, MKB)] = MKBRecord
                                        if MKBRecord:
                                            MKBVisit = forceStringEx(MKBRecord.value('MKB'))
                                            if MKB != MKBVisit:
                                                res = QtGui.QMessageBox.warning(self,
                                                u'Внимание!',
                                                u'Диагноз по ДН События визита \'%s\' отличается от диагноза контроля \'%s\'.\nОбновить значение в поле МКБ?' % (MKBVisit, MKB),
                                                QtGui.QMessageBox.Ok|QtGui.QMessageBox.Cancel,
                                                QtGui.QMessageBox.Cancel)
                                                if res == QtGui.QMessageBox.Ok:
                                                    recordPP.setValue('MKB', toVariant(MKBVisit))
                                                    for item in items:
                                                        ppId = forceRef(item.value('id'))
                                                        if ppId != id:
                                                            item.setValue('MKB', toVariant(MKBVisit))
                                                            db.updateRecord(table, item)
                                    recordPP.setValue('person_id', personId)
                                    recordPP.setValue('scene_id', sceneId)
                                    recordPP.setValue('orgStructure_id', orgStructureId)
                                    recordPP.setValue('speciality_id', specialityId)
                                    recordPP.setValue('visit_id', toVariant(newVisitId))
                                    db.updateRecord(table, recordPP)
                                    self.updateProphylaxisPlanningsList(id)
                            db.commit()
                        except:
                            db.rollback()
                            raise
                    finally:
                        self.releaseLock()

    def findAppointments(self):
        def stepIterator(progressDialog):
            db = QtGui.qApp.db
            table = db.table('ProphylaxisPlanning')

            for idx in xrange(self.modelProphylaxisPlannings.rowCount()):
                record = self.modelProphylaxisPlannings.getRecordByRow(idx)
                if not forceBool(record.value('processed')):
                    id = forceRef(record.value('id'))
                    if self.lock('ProphylaxisPlanning', id):
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
#                                self.updateProphylaxisPlanningsList(id)
                        finally:
                            self.releaseLock()
                yield 1

        pd = CSimpleProgressDialog(self)
        pd.setWindowTitle(u'Подбор талонов')
        pd.setStepCount(self.modelProphylaxisPlannings.rowCount())
        pd.setAutoStart(True)
        pd.setAutoClose(False)
        pd.setStepIterator(stepIterator)
        pd.exec_()
        self.modelProphylaxisPlannings.invalidateRecordsCache()
        self.tblProphylaxisPlannings.update()

    def on_buttonBoxFilter_apply(self):
        def cmbToTristate(val):
            return val-1 if val>0 else None

        self.filter = {}
        if self.chkClientId.isChecked():
            self.filter['clientId'] = forceStringEx(self.edtClientId.text())
        else:
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
        if self.chkFilterDateRange.isChecked():
            self.filter['dateRange'] = self.edtFilterBegDate.date(), self.edtFilterEndDate.date()
            self.filter['begVisitDate'] = self.edtFilterBegDate.date()
            self.filter['endVisitDate'] = self.edtFilterEndDate.date()
        self.filter['notVisit'] = self.cmbFilterNotVisit.currentIndex()
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
        if self.chkFilterSceneVisit.isChecked():
            self.filter['sceneId'] = self.cmbFilterSceneVisit.value()
        if self.chkActionMKB.isChecked():
            self.filter['actionMKB'] = self.chkActionMKB.isChecked()
            self.filter['actionMKBFrom'] = MKBwithoutSubclassification(unicode(self.edtActionMKBFrom.text()))
            self.filter['actionMKBTo'] = MKBwithoutSubclassification(unicode(self.edtActionMKBTo.text()))
        if self.chkFilterExport.isChecked():
           self.filter['exportStatus'] = self.cmbFilterExportStatus.currentIndex()
           self.filter['exportSystem'] = self.cmbFilterExportSystem.value()
        if self.chkProphylaxisPlanningType.isChecked():
            self.filter['prophylaxisPlanningsList'] = self.getSelectProphylaxisPlanningTypeList()
        self.updateProphylaxisPlanningsList()

    def on_buttonBoxFilter_reset(self):
        self.chkClientId.setChecked(False)
        self.edtClientId.setText('')
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
        self.chkFilterDateRange.setChecked(False)
        self.edtFilterBegDate.setDate(QDate.currentDate())
        self.edtFilterEndDate.setDate(QDate.currentDate().addMonths(1))
        self.cmbFilterNotVisit.setCurrentIndex(2)
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
        self.chkFilterExport.setChecked(False)
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
        self.chkFilterSceneVisit.setChecked(False)
        self.cmbFilterSceneVisit.setValue(None)
        self.chkActionMKB.setChecked(False)
        self.chkProphylaxisPlanningType.setChecked(False)
        self.tblProphylaxisPlanningType.clearSelection()
        self.on_buttonBoxFilter_apply()

    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelProphylaxisPlannings_currentRowChanged(self, current, previous):
        self.updateClientInfo()

    @pyqtSignature('')
    def on_tblProphylaxisPlannings_popupMenuAboutToShow(self):
        dataPresent = self.tblProphylaxisPlannings.currentItem() is not None
        self.actFilterAppointment.setEnabled(dataPresent)
        self.actSetProcessed.setEnabled(dataPresent)
        self.actUnsetProcessed.setEnabled(dataPresent)
        self.actProphylaxisEdit.setEnabled(dataPresent and QtGui.qApp.userHasRight(urEditProphylaxisPlanning))
        self.actUpdateVisit.setEnabled(dataPresent and QtGui.qApp.userHasRight(urEditProphylaxisPlanning) and forceBool(QtGui.qApp.preferences.appPrefs.get('isPrefSurveillancePlanningDialog', False)))

    @pyqtSignature('')
    def on_actFilterAppointment_triggered(self):
        record = self.tblProphylaxisPlannings.currentItem()
        if record:
            orgStructureId = forceRef(record.value('orgStructure_id'))
            specialityId   = forceRef(record.value('speciality_id'))
            personId       = forceRef(record.value('person_id'))
            begDate        = forceDate(record.value('begDate'))
            QtGui.qApp.setupDocFreeQueue(CSchedule.atAmbulance, orgStructureId, specialityId, personId, begDate)

    @pyqtSignature('')
    def on_actProphylaxisEdit_triggered(self):
        itemId = self.tblProphylaxisPlannings.currentItemId()
        if itemId:
            dialog = CProphylaxisPlanningEditor(self)
            try:
                dialog.load(itemId)
                if dialog.exec_():
                    itemId = dialog.itemId()
                    self.on_buttonBoxFilter_apply()
                    self.tblProphylaxisPlannings.setCurrentItemId(itemId)
            finally:
                dialog.deleteLater()

    @pyqtSignature('')
    def on_actSetProcessed_triggered(self):
        self.editMarks(True)

    @pyqtSignature('')
    def on_actUnsetProcessed_triggered(self):
        self.editMarks(False)

    @pyqtSignature('')
    def on_actUpdateVisit_triggered(self):
        self.updateVisit()

    @pyqtSignature('bool')
    def on_chkFilterBirthDay_toggled(self, value):
        self.edtFilterEndBirthDay.setEnabled(value and self.chkFilterEndBirthDay.isChecked())

    @pyqtSignature('bool')
    def on_chkClientId_toggled(self, value):
        if value:
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
        self.chkFilterLastName.setEnabled(not value)
        self.chkFilterFirstName.setEnabled(not value)
        self.chkFilterPatrName.setEnabled(not value)
        self.chkFilterBirthDay.setEnabled(not value)
        self.chkFilterEndBirthDay.setEnabled(not value)
        self.chkFilterSex.setEnabled(not value)

    @pyqtSignature('QAbstractButton*')
    def on_buttonBoxFilter_clicked(self, button):
        buttonCode = self.buttonBoxFilter.standardButton(button)
        if buttonCode == QtGui.QDialogButtonBox.Apply:
            self.on_buttonBoxFilter_apply()
        elif buttonCode == QtGui.QDialogButtonBox.Reset:
            self.on_buttonBoxFilter_reset()
        self.focusProphylaxisPlanningsList()
        self.updateClientInfo()

    @pyqtSignature('')
    def on_btnFindProphylaxis_clicked(self):
        self.findAppointments()


class CProphylaxisPlanningModel(CTableModel):
    Col_VisitId = 14

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

    class CLocClientContactColumn(CCol):
        def __init__(self, title, fields, defaultWidth):
            CCol.__init__(self, title, fields, defaultWidth, 'l')
            self.phonesCache = {}

        def format(self, values):
            clientId = forceRef(values[1])
            if not self.phonesCache.get(clientId):
                db = QtGui.qApp.db
                table = db.table('ClientContact')
                cond  = []
                cond.append(table['client_id'].eq(clientId))
                cond.append(table['deleted'].eq(0))
                records = db.getRecordList(table,
                                        [table['contact'], table['notes']],
                                        cond,
                                        [u'ClientContact.id DESC'])
                result = []
                for record in records:
                    contact  = forceString(record.value(0))
                    notes    = forceString(record.value(1))
                    result.append((contact, notes))
                self.phonesCache[clientId] = ', '.join([(phone[0]+' ('+phone[1]+')') if phone[1] else (phone[0]) for phone in result])
            return toVariant(self.phonesCache.get(clientId))

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
                return toVariant(forceString(QDateTime(date, time))+' '+personName)
            return QVariant()

    class CLocVisitColumn(CCol):
        def __init__(self, title, fields, defaultWidth):
            CCol.__init__(self, title, fields, defaultWidth, 'l')
            self.caches = {}
            self.MKBCaches = {}

        def format(self, values):
            visitId = forceRef(values[0])
            MKB = forceStringEx(values[1])
            date = u''
            db = QtGui.qApp.db
            if visitId:
                visitRecord = self.caches.get(visitId, None)
                if not visitRecord:
                    table = db.table('Visit')
                    visitRecord = db.getRecordEx(table, '*', [table['id'].eq(visitId)])
                if visitRecord:
                    date = forceStringEx(forceDate(visitRecord.value('date')))
                self.caches[visitId] = visitRecord
                if MKB:
                    MKBRecord = self.MKBCaches.get((visitId, MKB), None)
                    if not MKBRecord:
                            table = db.table('Visit')
                            tableEvent = db.table('Event')
                            tableDiagnosis = db.table('Diagnosis')
                            tableDiagnostic = db.table('Diagnostic')
                            tableDispanser = db.table('rbDispanser')
                            queryTable = tableEvent.innerJoin(table, table['event_id'].eq(tableEvent['id']))
                            queryTable = queryTable.innerJoin(tableDiagnostic, tableDiagnostic['event_id'].eq(tableEvent['id']))
                            queryTable = queryTable.innerJoin(tableDiagnosis, tableDiagnosis['id'].eq(tableDiagnostic['diagnosis_id']))
                            queryTable = queryTable.innerJoin(tableDispanser, tableDispanser['id'].eq(tableDiagnostic['dispanser_id']))
                            cond = [table['id'].eq(visitId),
                                    db.joinOr([tableDiagnosis['MKB'].eq(MKB),
                                               tableDiagnosis['MKB'].like(MKB[:3]+'%')]),
                                    tableDiagnostic['dispanser_id'].isNotNull(),
                                    table['deleted'].eq(0),
                                    tableDiagnosis['deleted'].eq(0),
                                    tableDiagnostic['deleted'].eq(0),
                                    tableEvent['deleted'].eq(0)
                                    ]
                            MKBRecord = db.getRecordEx(queryTable, 'Diagnosis.MKB', cond)
                            if MKBRecord:
                                self.MKBCaches[(visitId, MKB)] = MKBRecord
            return toVariant(date)

        def getValue(self, values):
            return forceRef(values[0])

    class CLocBegDateColumn(CCol):
        def __init__(self, title, fields, defaultWidth):
            CCol.__init__(self, title, fields, defaultWidth, 'l')
            self.typeCaches = {}

        def format(self, values):
            planningTypeId = forceRef(values[0])
            endDate = forceStringEx(values[1])
            date = forceStringEx(values[2])
            db = QtGui.qApp.db
            if planningTypeId:
                typeRecord = self.typeCaches.get(planningTypeId, None)
                code = ''
                if not typeRecord:
                    table = db.table('rbProphylaxisPlanningType')
                    typeRecord = db.getRecordEx(table, '*', [table['id'].eq(planningTypeId)])
                if typeRecord:
                    code = forceStringEx(typeRecord.value('code'))
                self.typeCaches[planningTypeId] = typeRecord
                if code == u'ДН':
                    date = endDate
            return toVariant(date)

        def getValue(self, values):
            return forceRef(values[0])

    def __init__(self, parent):
        self.clientCache = CTableRecordCache(QtGui.qApp.db, 'Client', ('id', 'lastName', 'firstName', 'patrName', 'birthDate', 'sex'), 300)
        CTableModel.__init__(self, parent)
        self.addColumn(self.CLocClientColumn( u'Ф.И.О.', ('client_id',), 60, self.clientCache))
        self.addColumn(self.CLocClientBirthDateColumn(u'Дата рожд.', ('client_id',), 20, self.clientCache, ['birthDate']))
        self.addColumn(self.CLocClientSexColumn(u'Пол', ('client_id',), 5, self.clientCache, ['sex']))
        self.addColumn(self.CLocClientContactColumn(u'Телефон', ('contact', 'client_id'),  20))
        self.addColumn(self.CLocBegDateColumn(u'С',   ('prophylaxisPlanningType_id', 'endDate', 'begDate'), 10))
        self.addColumn(CDateCol(u'По',  ['endDate'], 10))
        self.addColumn(CDesignationCol(u'Подразделение', ('orgStructure_id',), ('OrgStructure', 'name'), 10))
        self.addColumn(CRefBookCol(u'Специальность',     ['speciality_id'],    'rbSpeciality', 30))
        self.addColumn(CRefBookCol(u'Врач',              ['person_id'],        'vrbPerson', 30))
        self.addColumn(CRefBookCol(u'Тип планирования профилактики', ['prophylaxisPlanningType_id'], 'rbProphylaxisPlanningType',    15))
        self.addColumn(CRefBookCol(u'Место', ['scene_id'], 'rbScene',    15))
        self.addColumn(CTextCol(u'Диагноз',    ['MKB'],  10))
        self.addColumn(CBoolCol(u'Отработан',            ['processed'],        7))
        self.addColumn(self.CScheduleItemCol(u'Талон на приём к врачу', ('appointment_id', 'client_id', ), 50))
        self.addColumn(self.CLocVisitColumn(u'Явка', ('visit_id', 'MKB'), 50))
        self.addColumn(CEnumCol(u'Оповещён',      ['notified'], (u'', u'телефон', u'СМС', u'эл.почта'),  10))
        self.addColumn(CTextCol(u'Примечание',    ['note'],  10))
        self.addColumn(CTextCol(u'Роль',          ['externalUserRole'],  10))
        self.addColumn(CTextCol(u'Внешний пользователь',  ['externalUserName'],  10))
        self.addColumn(CTextCol(u'Причина',       ['reason'],  10))
        self.addColumn(CDateTimeCol(u'Создано',   ['createDatetime'], 20))
        self.addColumn(CRefBookCol(u'Создал',    ['createPerson_id'], 'vrbPersonWithSpeciality', 30))
        self.addColumn(CDateTimeCol(u'Изменено',  ['modifyDatetime'], 20))
        self.addColumn(CRefBookCol(u'Изменил',    ['modifyPerson_id'], 'vrbPersonWithSpeciality', 30))
        self.setTable('ProphylaxisPlanning')
        self._mapColumnToOrder = {'client_id'          :'CONCAT(Client.lastName, Client.firstName, Client.patrName)',
                                  'birthDate'          :'Client.birthDate',
                                  'sex'                :'Client.sex',
                                  'contact'            :'ProphylaxisPlanning.contact',
                                  'begDate'            :'ProphylaxisPlanning.begDate',
                                  'endDate'            :'ProphylaxisPlanning.endDate',
                                  'orgStructure_id'    :'OrgStructure.name',
                                  'speciality_id'      :'rbSpeciality.name',
                                  'person_id'          :'vrbPerson.name',
                                  'processed'          :'ProphylaxisPlanning.processed',
                                  'appointment_id'     :'Schedule_Item.time',
                                  'notified'           :'ProphylaxisPlanning.notified',
                                  'note'               :'ProphylaxisPlanning.note',
                                  'externalUserRole'   :'ProphylaxisPlanning.externalUserRole',
                                  'externalUserName'   :'ProphylaxisPlanning.externalUserName',
                                  'reason'             :'ProphylaxisPlanning.reason',
                                  'createDatetime'     :'ProphylaxisPlanning.createDatetime',
                                  'createPerson_id'    :'createPerson',
                                  'modifyDatetime'     :'ProphylaxisPlanning.modifyDatetime',
                                  'modifyPerson_id'    :'modifyPerson',
                                  'MKB'                :'ProphylaxisPlanning.MKB',
                                  'prophylaxisPlanningType_id' : 'rbProphylaxisPlanningType.name',
                                  'scene_id'           : 'rbScene.name',
                                  }

    def getOrder(self, fieldName, column):
        if hasattr(self._cols[column], 'extraFields'):
            if len(self._cols[column].extraFields) > 0:
                fieldName = self._cols[column].extraFields[0]
        return self._mapColumnToOrder[fieldName]

    def invalidateRecordsCache(self):
        self.clientCache.invalidate()
        CTableModel.invalidateRecordsCache(self)


class CProphylaxisPlanningMarksDialog(CDialogBase, Ui_ProphylaxisPlanningMarksDialog):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.setupDirtyCather()

    def setMarksFromRecord(self, record, onProcess):
        if onProcess:
            self.chkProcessed.setChecked(True)
            self.cmbNotified.setCurrentIndex(1) # телефон
            self.setWindowTitle(u'Отработать')
        else:
            self.chkProcessed.setChecked(False)
            self.cmbNotified.setCurrentIndex(0) # нет
            self.setWindowTitle(u'Отменить отработку')
        setTextEditValue(self.edtNote,      record, 'note')
        self.setIsDirty(False)

    def storeMarksToRecord(self, record):
        getCheckBoxValue(self.chkProcessed, record, 'processed')
        getComboBoxValue(self.cmbNotified,  record, 'notified')
        getTextEditValue(self.edtNote,      record, 'note')


class CProphylaxisPlanningVisitEditor(CDialogBase, Ui_ProphylaxisPlanningVisitEditor):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.setupDirtyCather()

    def setFilter(self, cond, queryTable):
        self.cmbVisit.setFilter(cond, queryTable)

    def setVisitId(self, visitId):
        self.cmbVisit.setValue(visitId)
        self.setIsDirty(False)

    def getVisitId(self):
        return forceRef(self.cmbVisit.value())


class CProphylaxisPlanningTypeTableModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self._parent = parent
        self._specialValues = []
        self.addColumn(CTextCol(u'Код', ['code'], 5))
        self.addColumn(CTextCol(   u'Наименование',     ['name'], 40))
        self._fieldNames = ['rbProphylaxisPlanningType.id', 'rbProphylaxisPlanningType.code', 'rbProphylaxisPlanningType.name']
        self.setTable('rbProphylaxisPlanningType')

    def flags(self, index):
        return Qt.ItemIsEnabled|Qt.ItemIsSelectable

    def setTable(self, tableName):
        db = QtGui.qApp.db
        tablePPT= db.table('rbProphylaxisPlanningType')
        loadFields = []
        loadFields.append(u'DISTINCT '+ u', '.join(self._fieldNames))
        self._table = tablePPT
        self._recordsCache = CTableRecordCache(db, self._table, loadFields, fakeValues=self._specialValues)
