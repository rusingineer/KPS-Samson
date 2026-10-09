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

import re
import datetime
from collections import OrderedDict
from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4.QtCore import QDate, pyqtSignature, SIGNAL, Qt, QUrl
from PyQt4.QtGui import QBrush
from Reports.Report      import CReport
from Reports.Report     import CVoidSetupDialog
from Reports.ReportBase import CReportBase, createTable
from Events.EditDispatcher import getEventFormClass
from Events.Utils import getActionTypeDescendants
from Events.ActionGroupSignDialog import CActionGroupSignDialog
from Users.Rights import urCanOpenAnyAttachedFile, urCanOpenOwnAttachedFile
from Orgs.Utils import getOrgStructureDescendants
from Orgs.OrgStructComboBoxes import COrgStructureComboBox
from library.DateEdit import CDateEdit
from library.DialogBase import CDialogBase
from library.InDocTable import CRecordListModel, CInDocTableCol
from library.RecordLock import CRecordLockMixin
from library.SortFilterProxyTableModel import CSortFilterProxyTableModel
from library.Utils import forceString, toVariant, forceInt, forceRef, forceDate, \
    formatNameInt, unformatSNILS, setPref, getPref, getPrefBool, getPrefString, forceDateTime, forceBool, trim
from library.MultivalueComboBox import CRecordMultivalueComboBox
from F088.F088EditDialog import CF088EditDialog
from F088.F0882022EditDialog import CF0882022EditDialog
from Ui_Attach_SEMD_IEMK import Ui_Attach_SEMD_IEMK_Dialog


class CAttach_SEMD_IEMK(CDialogBase, Ui_Attach_SEMD_IEMK_Dialog, CRecordLockMixin):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        CRecordLockMixin.__init__(self)
        self.setupUi(self)
        self.listFilterIdentify = ""
        self.setWindowFlags(Qt.Window)
        self.addModels('ActionFileAttach', CActionFileAttachModel(self))
        self.addModels('ActionFileAttachSort', CActionFileAttachSortFilterProxyTableModel(self, self.modelActionFileAttach))
        self.setModels(self.tblActionFileAttach, self.modelActionFileAttachSort, self.selectionModelActionFileAttachSort)
        self.tblActionFileAttach.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tblActionFileAttach.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tblActionFileAttach.horizontalHeader().setStretchLastSection(True)
        self.cmbEventType.setTable("EventType")
        self.tblActionFileAttach.enableColsHide()
        self.tblActionFileAttach.enableColsMove()
        self.edtFilterLastName.setDisabled(True)
        self.edtFilterFirstName.setDisabled(True)
        self.edtFilterPatrName.setDisabled(True)
        self.edtFilterEventId.setDisabled(True)
        self.edtFilterDateExecActionBegDate.setDisabled(True)
        self.edtFilterDateExecActionEndDate.setDisabled(True)
        self.edtFilterEventBegDate.setDisabled(True)
        self.edtFilterEventEndDate.setDisabled(True)
        self.edtFilterAttachFileBegDate.setDisabled(True)
        self.edtFilterAttachFileEndDate.setDisabled(True)
        self.cmbFilterOrgStructure.setDisabled(True)
        self.edtFilterDateExecActionBegDate.setDate(QDate().currentDate())
        self.edtFilterDateExecActionEndDate.setDate(QDate().currentDate())
        self.edtFilterEventBegDate.setDate(QDate().currentDate())
        self.edtFilterEventEndDate.setDate(QDate().currentDate())
        self.edtFilterAttachFileBegDate.setDate(QDate().currentDate())
        self.edtFilterAttachFileEndDate.setDate(QDate().currentDate())
        self.btnFilterReset.clicked.connect(self.resetFilters)
        self.btnFilterApply.clicked.connect(self.applyFilters)
        self.selectionModelActionFileAttachSort.selectionChanged.connect(self.on_selectionModelFileAttach_currentRowChanged)
        self.btnOpenFile.setVisible(False)
        self.addObject('actPrintWindow', QtGui.QAction(u'Печать списка', self))
        self.addObject('actPrintSummaryDocuments', QtGui.QAction(u'Сводка по  документам', self))
        self.addObject('actPrintWindowSelected', QtGui.QAction(u'Печать списка(выделенных пациентов)', self))
        # self.addObject('actPrintGroupStrucPerson', QtGui.QAction(u'Группировка по подразделениям и врачам', self))
        # self.addObject('actPrintGroupPersonInfo', QtGui.QAction(u'Группировка по врачам с отображением количественных показателей', self))
        self.actPrintWindow.triggered.connect(self.on_actPrintWindow_triggered)
        self.actPrintWindowSelected.triggered.connect(self.on_actPrintWindowSelected_triggered)
        self.actPrintSummaryDocuments.triggered.connect(self.on_actPrintSummaryDocuments_triggered)
        # self.actPrintGroupStrucPerson.triggered.connect(self.on_actPrintGroupStrucPerson_triggered)
        # self.actPrintGroupPersonInfo.triggered.connect(self.on_actPrintGroupPersonInfo_triggered)
        self.addObject('mnuPrint', QtGui.QMenu(self))
        self.mnuPrint.addAction(self.actPrintWindow)
        self.mnuPrint.addAction(self.actPrintSummaryDocuments)
        self.mnuPrint.addAction(self.actPrintWindowSelected)
        # self.mnuPrint.addAction(self.actPrintGroupStrucPerson)
        # self.mnuPrint.addAction(self.actPrintGroupPersonInfo)
        self.btnPrint.setMenu(self.mnuPrint)
        self.btnPrint.setShortcut('F6')
        self.cmbActionType.setClassesPopupVisible(True)
        self.cmbActionType.setClasses([0, 1, 2, 3])
        self.cmbActionType.setOrgStructure(None)
        self.getDefaultParams()
        self.updateFilterIdentify()
        self.connect(self.tblActionFileAttach.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.sortByColumn)
        self.groupBoxFilters.setTitle(u'Фильтры по действиям')
        self.__sortColumn = None
        self.__sortAscending = False
        self.appPrefs = QtGui.qApp.preferences.appPrefs
        self.getPreferences()
        self.cmbFinance.setTable('rbFinance', True)
        self.cmbFinance.setValue(0)
        self.cmbSpeciality.setTable('rbSpeciality', True)
        self.cmbFilterIdentify.enableFilter(True)

        self.edtFilterEventBegDate.setDate(QDate.currentDate())
        self.edtFilterEventEndDate.setDate(QDate.currentDate())

    def updateFilterIdentify(self, signal=False):
        self.cmbFilterIdentify.clear()
        doc = "'n3.medDocumentType.Cda'"

        db = QtGui.qApp.db
        stmt = u"""SELECT note, value, system_id as sys, code FROM ActionType_Identification 
          LEFT JOIN rbAccountingSystem rbas ON ActionType_Identification.system_id = rbas.id
          WHERE rbas.code IN ({0})
          AND note != '' AND note IS not NULL and deleted = 0 group by note ORDER BY note """.format(doc)
        #longest_word = ''

        list_auto_check = []
        x = 0

        if self.listFilterIdentify != "" and signal is False:
            lFilterIdentify = self.listFilterIdentify.replace(" ", "")
            lFilterIdentify = lFilterIdentify.split(',')

        query = db.query(stmt)
        filterItems = OrderedDict()
        while query.next():
            rec = query.record()
            value = forceString(rec.value('value'))
            name = forceString(rec.value('note'))

            filterItems[value] = name.replace(u'\xa0', '')
            if self.listFilterIdentify != "" and signal is False:
                if value in lFilterIdentify:
                    list_auto_check.append(x)
            else:
                list_auto_check.append(x)
            x += 1

            #if len(forceString(rec.value('note'))) > len(longest_word):
            #    longest_word = forceString(rec.value('note'))

        self.cmbFilterIdentify.setItems(OrderedDict(sorted(filterItems.items())))
        #self.cmbFilterIdentify._popupView._view.horizontalHeader().setDefaultSectionSize(20)  # Изменяем ширину первого столбца
        #self.cmbFilterIdentify.preferredWidth = (len(longest_word)) * 6  # Изменяем ширину второго столбца
        self.cmbFilterIdentify.setCheckedRows(list_auto_check)

    def getModelAndTable(self):
        tbl = self.tblActionFileAttach
        sortModel = self.modelActionFileAttachSort
        model = self.modelActionFileAttachSort.model()
        return tbl, sortModel, model

    def getPreferences(self):
        if forceBool(self.appPrefs.get('AttachSEMDChkLastName', False)):
            self.chkFilterLastName.setChecked(forceBool(self.appPrefs.get('AttachSEMDChkLastName', False)))

        if forceBool(self.appPrefs.get('AttachSEMDChkFirstName', False)):
            self.chkFilterFirstName.setChecked(forceBool(self.appPrefs.get('AttachSEMDChkFirstName', False)))

        if forceBool(self.appPrefs.get('AttachSEMDChkPatrName', False)):
            self.chkFilterPatrName.setChecked(forceBool(self.appPrefs.get('AttachSEMDChkPatrName', False)))

        if forceBool(self.appPrefs.get('AttachSEMDChkEventId', False)):
            self.chkFilterEventId.setChecked(forceBool(self.appPrefs.get('AttachSEMDChkEventId', False)))

        if forceBool(self.appPrefs.get('AttachSEMDChkActionType', False)):
            self.chkFilterActionType.setChecked(forceBool(self.appPrefs.get('AttachSEMDChkActionType', False)))

        if forceBool(self.appPrefs.get('AttachSEMDChkEventType', False)):
            self.chkFilterEventType.setChecked(forceBool(self.appPrefs.get('AttachSEMDChkEventType', False)))

        if forceBool(self.appPrefs.get('AttachSEMDChkDateExecActionBegDate', False)):
            self.chkFilterDateExecActionBegDate.setChecked(forceBool(self.appPrefs.get('AttachSEMDChkDateExecActionBegDate', False)))
        if forceBool(self.appPrefs.get('AttachSEMDChkDateExecActionEndDate', False)):
            self.chkFilterDateExecActionEndDate.setChecked(forceBool(self.appPrefs.get('AttachSEMDChkDateExecActionEndDate', False)))

        if forceBool(self.appPrefs.get('AttachSEMDChkEventBegDate', False)):
            self.chkFilterEventBegDate.setChecked(forceBool(self.appPrefs.get('AttachSEMDChkEventBegDate', False)))
        if forceBool(self.appPrefs.get('AttachSEMDChkEventEndDate', False)):
            self.chkFilterEventEndDate.setChecked(forceBool(self.appPrefs.get('AttachSEMDChkEventEndDate', False)))

        if forceBool(self.appPrefs.get('AttachSEMDChkAttachFileBegDate', False)):
            self.chkFilterAttachFileBegDate.setChecked(forceBool(self.appPrefs.get('AttachSEMDChkAttachFileBegDate', False)))
        if forceBool(self.appPrefs.get('AttachSEMDChkAttachFileEndDate', False)):
            self.chkFilterAttachFileEndDate.setChecked(forceBool(self.appPrefs.get('AttachSEMDChkAttachFileEndDate', False)))

        if forceBool(self.appPrefs.get('AttachSEMDChkIdentify', False)):
            self.chkFilterIdentify.setChecked(forceBool(self.appPrefs.get('AttachSEMDChkIdentify', False)))
        
        if forceBool(self.appPrefs.get('AttachSEMDChkExportErrors', False)):
            self.chkFilterExportErrors.setChecked(forceBool(self.appPrefs.get('AttachSEMDChkExportErrors', False)))
        else:
            self.edtFilterExportErrors.setVisible(False)

        if forceBool(self.appPrefs.get('AttachSEMDChkSchematronErrors', False)):
            self.chkFilterSchematronErrors.setChecked(forceBool(self.appPrefs.get('AttachSEMDChkSchematronErrors', False)))
        else:
            self.edtFilterSchematronErrors.setVisible(False)

        self.applyFilters()

    def setPreferences(self):
        self.appPrefs['AttachSEMDChkLastName'] = toVariant(self.chkFilterLastName.isChecked())
        self.appPrefs['AttachSEMDChkFirstName'] = toVariant(self.chkFilterFirstName.isChecked())
        self.appPrefs['AttachSEMDChkPatrName'] = toVariant(self.chkFilterPatrName.isChecked())
        self.appPrefs['AttachSEMDChkEventId'] = toVariant(self.chkFilterEventId.isChecked())
        self.appPrefs['AttachSEMDChkActionType'] = toVariant(self.chkFilterActionType.isChecked())
        self.appPrefs['AttachSEMDChkEventType'] = toVariant(self.chkFilterEventType.isChecked())

        self.appPrefs['AttachSEMDChkDateExecActionBegDate'] = toVariant(self.chkFilterDateExecActionBegDate.isChecked())
        self.appPrefs['AttachSEMDChkDateExecActionEndDate'] = toVariant(self.chkFilterDateExecActionEndDate.isChecked())

        self.appPrefs['AttachSEMDChkEventBegDate'] = toVariant(self.chkFilterEventBegDate.isChecked())
        self.appPrefs['AttachSEMDChkEventEndDate'] = toVariant(self.chkFilterEventEndDate.isChecked())

        self.appPrefs['AttachSEMDChkAttachFileBegDate'] = toVariant(self.chkFilterAttachFileBegDate.isChecked())
        self.appPrefs['AttachSEMDChkAttachFileEndDate'] = toVariant(self.chkFilterAttachFileEndDate.isChecked())

        self.appPrefs['AttachSEMDChkIdentify'] = toVariant(self.chkFilterIdentify.isChecked())
        self.appPrefs['AttachSEMDChkSchematronErrors'] = toVariant(self.chkFilterSchematronErrors.isChecked())
        self.appPrefs['AttachSEMDChkExportErrors'] = toVariant(self.chkFilterExportErrors.isChecked())


    def sortByColumn(self, column, sortBy=None):
        tbl, sortModel, model = self.getModelAndTable()
        header = tbl.horizontalHeader()
        if not sortBy:
            if column == self.__sortColumn:
                self.__sortAscending = False if self.__sortAscending else True
            else:
                self.__sortColumn = column
                self.__sortAscending = True
            sortBy = self.__sortAscending
        header.setSortIndicatorShown(True)
        header.setSortIndicator(column, Qt.AscendingOrder if sortBy else Qt.DescendingOrder)
        sortModel.sort(column, sortBy)
        model.emitRowsChanged(0, len(model._items)-1)

    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelFileAttach_currentRowChanged(self, current, previous):
        self.rowCount()

    def rowCount(self):
        tbl, sortModel, model = self.getModelAndTable()

        rowCount = forceString(tbl.model().rowCount())
        selectedRows = tbl.selectedRowList()

        selectedRows = u', выделено: ' + forceString(len(selectedRows))
        self.lblCount.setText(u'Записей в списке: ' + rowCount + selectedRows)

    def contextMenuEvent(self, event):
        self.menu = QtGui.QMenu(self)
        tbl, sortModel, model = self.getModelAndTable()
        selectedRows = self.getSelectedRows(tbl)
        if len(selectedRows) == 1:
            currentRow = forceInt(tbl.currentRow())
            index = model.index(currentRow, 0)
            proxyIndex = sortModel.mapFromSource(index)
            currentRow = forceInt(proxyIndex.row())
            attachedFileId = forceInt(model.records[currentRow].value('afa_id'))
            if attachedFileId != 0:
                openFile = QtGui.QAction(u'Открыть файл', self)
                openFile.triggered.connect(self.openAttachFile)
            actOpenEvent = QtGui.QAction(u'Открыть обращение', self)
            actOpenEvent.triggered.connect(self.on_actOpenEvent_triggered)
            actGroupSign = QtGui.QAction(u'Групповое подписание и прикрепление', self)
            actGroupSign.triggered.connect(self.on_actGroupSign_triggered)

            if attachedFileId != 0:
                self.menu.addAction(openFile)
            self.menu.addAction(actOpenEvent)
            self.menu.addAction(actGroupSign)

        self.menu.popup(QtGui.QCursor.pos())

    def sortErrors(self, errorList):
        errorSet = set(errorList)
        errorNotFoundSNILS = u'Для текущего пользователя не определён СНИЛС: '
        errorNotActiveSNILS = u'Не удалось найти действующий сертификат пользователя по СНИЛС: '
        eNFS, eNAS, other = 0, 0, 0
        stringError = u''
        errorOther = u''
        for error in errorSet:
            if error.find(u'Для текущего пользователя') != -1:
                error = re.search(r'\d{1,}', error)
                if error:
                    errorNotFoundSNILS += u' "' + error.group(0) + u'" '
                    eNFS = 1
            elif error.find(u'Не удалось найти действующий сертификат пользователя') != -1:
                error = re.search(r'\d{3}-\d{3}-\d{3}\D\d{2}', error)
                fullname = QtGui.qApp.db.getRecordEx('Person', 'lastName, firstName, patrName', 'SNILS = {0}'.format(unformatSNILS(error.group(0))))
                fullname = formatNameInt(forceString(fullname.value('lastName')), forceString(fullname.value('firstName')), forceString(fullname.value('patrName')))
                if error:
                    errorNotActiveSNILS += u' "' + error.group(0) + u'" '+fullname+' '
                    eNAS = 1
            else:
                other = 1
                errorOther = error
        if other:
            stringError += errorOther
        if eNFS:
            stringError += errorNotFoundSNILS + u'\n'
        if eNAS:
            stringError += errorNotActiveSNILS
        return stringError

    def getSelectedRows(self, tbl):
        result = [index.row() for index in tbl.selectedIndexes()]
        if result:
            result = list(set(result) & set(result))
            result.sort()
            return result
        else:
            return []

    def resetFilters(self):
        self.edtFilterFirstName.clear()
        self.edtFilterLastName.clear()
        self.edtFilterPatrName.clear()
        self.edtFilterEventId.clear()
        self.edtFilterDateExecActionBegDate.setDate(QDate.currentDate())
        self.edtFilterDateExecActionEndDate.setDate(QDate.currentDate())
        self.edtFilterEventBegDate.setDate(QDate.currentDate())
        self.edtFilterEventEndDate.setDate(QDate.currentDate())
        self.edtFilterAttachFileBegDate.setDate(QDate.currentDate())
        self.edtFilterAttachFileEndDate.setDate(QDate.currentDate())
        self.cmbFilterPerson.setCurrentIndex(0)
        self.cmbActionType.setValue(None)
        self.cmbEventType.clearValue()
        self.cmbFilterSigned.setCurrentIndex(0)
        self.cmbFilterOrgStructure.setCurrentIndex(-1)
        self.chkFilterLastName.setChecked(False)
        self.chkFilterFirstName.setChecked(False)
        self.chkFilterPatrName.setChecked(False)
        self.chkFilterEventId.setChecked(False)
        self.chkFilterDateExecActionBegDate.setChecked(False)
        self.chkFilterDateExecActionEndDate.setChecked(False)
        self.chkFilterEventEndDate.setChecked(False)
        self.chkFilterEventBegDate.setChecked(False)
        self.chkFilterAttachFileBegDate.setChecked(False)
        self.chkFilterAttachFileEndDate.setChecked(False)
        self.chkFilterOrgStructure.setChecked(False)
        self.chkFilterActionType.setChecked(False)
        self.chkFilterEventType.setChecked(False)
        self.chkFilterIdentify.setChecked(False)
        self.chkFilterExportErrors.setChecked(False)
        self.chkFilterSchematronErrors.setChecked(False)
        self.cmbFilterIdentify.setEnabled(False)
        self.cmbFilterIdentify.setCurrentIndex(0)
        self.cmbFilterIdentify.clearItemChecked()
        self.cmbFilterIdentify.setToolTip("")
        self.cmbSpeciality.clearItemChecked()
        self.cmbSpeciality.setToolTip("")
        self.cmbSpeciality.setEditText("")
        self.cmbFinance.setValue(0)
        self.applyFilters()

    def saveDefaultParams(self, params):
        prefs = {}
        for param, value in params.iteritems():
            setPref(prefs, param, value)

        setPref(prefs, 'ActionFileAttach', toVariant(''))
        setPref(QtGui.qApp.preferences.reportPrefs, 'ActIon', prefs)

    def getDefaultParams(self):
        result = {}
        prefs = getPref(QtGui.qApp.preferences.reportPrefs, 'ActIon', {})

        result['FilterIdentify'] = getPrefBool(prefs, 'FilterIdentify', False)
        result['listFilterIdentify'] = getPrefString(prefs, 'listFilterIdentify', '')
        result['NotSignaturePerson'] = getPrefBool(prefs, 'NotSignaturePerson', False)

        if result['FilterIdentify']:
            self.chkFilterIdentify.setChecked(result['FilterIdentify'])
        if result['listFilterIdentify']:
            self.listFilterIdentify = result['listFilterIdentify']

    def applyFilters(self):
        result = {}
        tbl, sortModel, model = self.getModelAndTable()
        QtGui.qApp.setWaitCursor()

        lastName = None
        firstName = None
        patrName = None
        eventId = None
        personId = None
        personSNILS = None
        begDate = None
        endDate = None
        orgStructureList = None
        dateExecActionBegDate = None
        dateExecActionEndDate = None
        eventBegDate = None
        eventEndDate = None
        attachFileBegDate = None
        attachFileEndDate = None
        uploadedDocs = None
        actionType = None
        identify = None
        eventType = None

        if self.chkFilterLastName.isChecked():
            lastName = forceString(self.edtFilterLastName.text())
        if self.chkFilterFirstName.isChecked():
            firstName = forceString(self.edtFilterFirstName.text())
        if self.chkFilterPatrName.isChecked():
            patrName = forceString(self.edtFilterPatrName.text())
        if self.chkFilterEventId.isChecked():
            eventId = forceString(self.edtFilterEventId.text())
        signedIndex = self.cmbFilterSigned.currentIndex()
        if self.chkFilterOrgStructure.isChecked():
            if self.cmbFilterOrgStructure.value():
                orgStructureList = getOrgStructureDescendants(self.cmbFilterOrgStructure.value())
        if self.cmbFilterPerson.currentIndex() != 0:
            personId = self.cmbFilterPerson.value()
        if self.chkFilterSNILS.isChecked() and self.chkFilterSNILS.isEnabled():
            personSNILS = True
        if self.chkFilterDateExecActionBegDate.isChecked():
            dateExecActionBegDate = self.edtFilterDateExecActionBegDate.date()
        if self.chkFilterDateExecActionEndDate.isChecked():
            dateExecActionEndDate = self.edtFilterDateExecActionEndDate.date()
        if self.chkFilterEventBegDate.isChecked():
            eventBegDate = self.edtFilterEventBegDate.date()
        if self.chkFilterEventEndDate.isChecked():
            eventEndDate = self.edtFilterEventEndDate.date()
        if self.chkFilterAttachFileBegDate.isChecked():
            attachFileBegDate = self.edtFilterAttachFileBegDate.date()
        if self.chkFilterAttachFileEndDate.isChecked():
            attachFileEndDate = self.edtFilterAttachFileEndDate.date()

        if self.chkFilterActionType.isChecked():
            actionType = self.cmbActionType.value()
        financeId = self.cmbFinance.value()
        
        specialityId = self.cmbSpeciality.value()
        if specialityId:
            specialityId = specialityId.split(',')

        if self.chkFilterEventType.isChecked():
            eventType = self.cmbEventType.value()
            
        result['FilterIdentify'] = self.chkFilterIdentify.isChecked()
        if self.chkFilterIdentify.isChecked():
            identify = ", ".join(self.getListIdentify())
            result['listFilterIdentify'] = identify

        #if self.chkFilterIExportSuccess.isChecked():
        #    exportSuccess = self.cmbExportSuccess.currentIndex()

        actionNoFile = self.cmbFilterIsFile.currentIndex()
        actionNoFile = True if actionNoFile == 1 else False
        if self.cmbFilterFileType.isEnabled():
            uploadedDocs = self.cmbFilterFileType.currentIndex()
            uploadedDocs = False if uploadedDocs == 1 else True

        validationResultCodes = None
        self.saveDefaultParams(result)
        model.loadData(lastName=lastName,
                       firstName=firstName,
                       patrName=patrName,
                       eventId=eventId,
                       signedIndex=signedIndex,
                       orgStructureList=orgStructureList,
                       personId=personId,
                       begDate=begDate,
                       endDate=endDate,
                       actionType=actionType,
                       identify=identify,
                       eventType=eventType,
                       dateExecActionBegDate=dateExecActionBegDate,
                       dateExecActionEndDate=dateExecActionEndDate,
                       eventBegDate=eventBegDate,
                       eventEndDate=eventEndDate,
                       attachFileBegDate=attachFileBegDate,
                       attachFileEndDate=attachFileEndDate,
                       personSNILS=personSNILS,
                       validationResultCodes=validationResultCodes,
                       financeId=financeId,
                       specialityId=specialityId,
                       actionNoFile=actionNoFile,
                       uploadedDocs=uploadedDocs
                       )
        QtGui.qApp.restoreOverrideCursor()
        self.rowCount()
        if type(self.__sortColumn) == type(None):
            self.sortByColumn(4, True)
        else:
            self.sortByColumn(self.__sortColumn, self.__sortAscending)
        self.setPreferences()

    def getListIdentify(self):
        listIdentify = []
        if self.chkFilterIdentify.isChecked():
            identify = self.cmbFilterIdentify.value()
            for i in re.split(',', identify):
                if trim(i).isdigit():
                    listIdentify.append(trim(i))
        return listIdentify

    def getEventType(self):
        listEventType = []
        if self.chkFilterEventType.isChecked():
            identify = self.cmbEventType.value()
            for i in re.split(' |\|', identify):
                if i.isdigit():
                    listEventType.append(i)
        return listEventType

    @pyqtSignature('bool')
    def on_chkFilterLastName_toggled(self):
        if self.chkFilterLastName.isChecked():
            self.edtFilterLastName.setEnabled(True)
            self.edtFilterLastName.setFocus()
        else:
            self.edtFilterLastName.setDisabled(True)

    @pyqtSignature('bool')
    def on_chkFilterFirstName_toggled(self):
        if self.chkFilterFirstName.isChecked():
            self.edtFilterFirstName.setEnabled(True)
            self.edtFilterFirstName.setFocus()
        else:
            self.edtFilterFirstName.setDisabled(True)

    @pyqtSignature('bool')
    def on_chkFilterEventId_toggled(self):
        if self.chkFilterEventId.isChecked():
            self.edtFilterEventId.setEnabled(True)
            self.edtFilterEventId.setFocus()
        else:
            self.edtFilterEventId.setDisabled(True)
            
    @pyqtSignature('bool')
    def on_chkFilterActionType_toggled(self, check):
        if self.chkFilterActionType.isChecked():
            self.cmbActionType.setEnabled(True)
            self.cmbActionType.setFocus()
        else:
            self.cmbActionType.setDisabled(True)

    @pyqtSignature('bool')
    def on_chkFilterEventType_toggled(self, check):
        if self.chkFilterEventType.isChecked():
            self.cmbEventType.setEnabled(True)
            self.cmbEventType.setFocus()
        else:
            self.cmbEventType.setDisabled(True)

    @pyqtSignature('bool')
    def on_chkFilterTypeDoc_toggled(self, check):
        self.updateFilterIdentify()

    @pyqtSignature('bool')
    def on_chkFilterIdentify_toggled(self, check):
        if self.chkFilterIdentify.isChecked():
            self.cmbFilterIdentify.setEnabled(True)
            self.cmbFilterIdentify.setFocus()
        else:
            self.cmbFilterIdentify.setDisabled(True)

    @pyqtSignature('bool')
    def on_chkFilterPatrName_toggled(self):
        if self.chkFilterPatrName.isChecked():
            self.edtFilterPatrName.setEnabled(True)
            self.edtFilterPatrName.setFocus()
        else:
            self.edtFilterPatrName.setDisabled(True)

    @pyqtSignature('bool')
    def on_chkFilterOrgStructure_toggled(self):
        if self.chkFilterOrgStructure.isChecked():
            self.cmbFilterOrgStructure.setEnabled(True)
            self.cmbFilterOrgStructure.setFocus()
        else:
            self.cmbFilterOrgStructure.setDisabled(True)

    @pyqtSignature('bool')
    def on_chkFilterDateExecActionBegDate_toggled(self):
        if self.chkFilterDateExecActionBegDate.isChecked():
            self.edtFilterDateExecActionBegDate.setEnabled(True)
            self.edtFilterDateExecActionBegDate.setFocus()
        else:
            self.edtFilterDateExecActionBegDate.setDisabled(True)

    @pyqtSignature('bool')
    def on_chkFilterDateExecActionEndDate_toggled(self):
        if self.chkFilterDateExecActionEndDate.isChecked():
            self.edtFilterDateExecActionEndDate.setEnabled(True)
            self.edtFilterDateExecActionEndDate.setFocus()
        else:
            self.edtFilterDateExecActionEndDate.setDisabled(True)

    @pyqtSignature('bool')
    def on_chkFilterEventBegDate_toggled(self):
        if self.chkFilterEventBegDate.isChecked():
            self.edtFilterEventBegDate.setEnabled(True)
            self.edtFilterEventBegDate.setFocus()
        else:
            self.edtFilterEventBegDate.setDisabled(True)

    @pyqtSignature('bool')
    def on_chkFilterEventEndDate_toggled(self):
        if self.chkFilterEventEndDate.isChecked():
            self.edtFilterEventEndDate.setEnabled(True)
            self.edtFilterEventEndDate.setFocus()
        else:
            self.edtFilterEventEndDate.setDisabled(True)

    @pyqtSignature('bool')
    def on_chkFilterAttachFileBegDate_toggled(self):
        if self.chkFilterAttachFileBegDate.isChecked():
            self.edtFilterAttachFileBegDate.setEnabled(True)
            self.edtFilterAttachFileBegDate.setFocus()
        else:
            self.edtFilterAttachFileBegDate.setDisabled(True)

    @pyqtSignature('bool')
    def on_chkFilterAttachFileEndDate_toggled(self):
        if self.chkFilterAttachFileEndDate.isChecked():
            self.edtFilterAttachFileEndDate.setEnabled(True)
            self.edtFilterAttachFileEndDate.setFocus()
        else:
            self.edtFilterAttachFileEndDate.setDisabled(True)

    @pyqtSignature('bool')
    def on_chkFilterExportErrors_toggled(self, check):
        self.edtFilterExportErrors.setText(u'')
        if self.chkFilterExportErrors.isChecked():
            self.edtFilterExportErrors.setVisible(True)
            self.modelActionFileAttachSort.setFilter('StatusREMD', [u'успех',
                                                                    u'информация ещё не получена',
                                                                    u'информация еще не получена',
                                                                    u'ожидается валидация документа на федеральном уровне'], 
                                                     CSortFilterProxyTableModel.MatchNotContainsAnyNotEmpty)
        else:
            self.edtFilterExportErrors.setVisible(False)
            self.modelActionFileAttachSort.removeFilter('StatusREMD')
    
    @pyqtSignature('QString')
    def on_edtFilterExportErrors_textChanged(self, text):
        if self.edtFilterExportErrors.isVisible():
            if text:
                self.modelActionFileAttachSort.setFilter('StatusREMD', [forceString(text), 
                                                                        u'успех', 
                                                                        u'информация ещё не получена', 
                                                                        u'информация еще не получена',
                                                                        u'ожидается валидация документа на федеральном уровне'], 
                                                         CSortFilterProxyTableModel.MatchContainsButFilterOut)
            else:
                self.modelActionFileAttachSort.setFilter('StatusREMD', [u'успех',
                                                                    u'информация ещё не получена',
                                                                    u'информация еще не получена',
                                                                    u'ожидается валидация документа на федеральном уровне'], 
                                                     CSortFilterProxyTableModel.MatchNotContainsAnyNotEmpty)
        else:
            self.modelActionFileAttachSort.removeFilter('StatusREMD')

    @pyqtSignature('bool')
    def on_chkFilterSchematronErrors_toggled(self, check):
        self.edtFilterSchematronErrors.setText(u'')
        if self.chkFilterSchematronErrors.isChecked():
            self.edtFilterSchematronErrors.setVisible(True)
            self.modelActionFileAttachSort.setFilter('StatusSchematron', u'', CSortFilterProxyTableModel.MatchNotEmpty)
        else:
            self.edtFilterSchematronErrors.setVisible(False)
            self.modelActionFileAttachSort.removeFilter('StatusSchematron')

    @pyqtSignature('QString')
    def on_edtFilterSchematronErrors_textChanged(self, text):
        if self.edtFilterSchematronErrors.isVisible():
            self.modelActionFileAttachSort.setFilter('StatusSchematron', forceString(text),
                                                     CSortFilterProxyTableModel.MatchContains if text else CSortFilterProxyTableModel.MatchNotEmpty)
        else:
            self.modelActionFileAttachSort.removeFilter('StatusSchematron')

    @pyqtSignature('int')
    def on_cmbFilterPerson_currentIndexChanged(self, index):
        if index == 0:
            self.chkFilterSNILS.setEnabled(False)
        else:
            self.chkFilterSNILS.setEnabled(True)

    @pyqtSignature('int')
    def on_cmbFilterIsFile_currentIndexChanged(self, index):
        if index == 0:
            self.cmbFilterSigned.setEnabled(True)
            self.cmbFilterFileType.setEnabled(True)
        elif index == 1:
            self.cmbFilterSigned.setEnabled(False)
            self.cmbFilterFileType.setEnabled(False)
            self.cmbFilterSigned.setCurrentIndex(0)

    @pyqtSignature('')
    def on_actPrintWindow_triggered(self):
        '''Печать списка'''
        data = self.parseModel()
        CReportPrintWindow(self, data).exec_()


    @pyqtSignature('')
    def on_actPrintWindowSelected_triggered(self):
        '''Печать списка пациентов, которых выделили в таблице'''
        data = self.parseModel(isSelected=True)
        CReportPrintWindow(self, data).exec_()


    @pyqtSignature('')
    def on_actPrintSummaryDocuments_triggered(self):
        '''Сводка по  документам'''
        CReportPrintSummaryDocuments(self).exec_()

    # @pyqtSignature('')
    # def on_actPrintGroupStrucPerson_triggered(self):
    #     '''Группировка по подразделениям и врачам'''
    #     data = self.parseModel()
    #     CReportGroupStrucPerson(self, data).exec_()

    # @pyqtSignature('')
    # def on_actPrintGroupPersonInfo_triggered(self):
    #     '''Группировка по врачам с отображением количественных показателей'''
    #     data = self.parseModel()
    #     CReportGroupPersonInfo(self, data).exec_()

    def parseModel(self, isSelected=None):
        tbl, sortModel, model = self.getModelAndTable()
        listData = []
        items = []
        if isSelected:
            indexes = tbl.selectionModel().selectedRows()
        else:
            indexes = [sortModel.index(row, 0) for row in range(sortModel.rowCount())]

        for proxyIndex in indexes:
            if not proxyIndex.isValid():
                continue
            sourceIndex = sortModel.mapToSource(proxyIndex)
            item = model.items()[sourceIndex.row()]
            items.append(item)
            
        for item in items:
            data = dataclass()
            data.fio_client = forceString(item.value('fio_client'))
            data.event_id = forceInt(item.value('eventId'))
            data.event_type_name = forceString(item.value('event_type_name'))
            data.structure = forceString(item.value('structure'))
            data.period = forceString(item.value('period'))
            data.action_id = forceString(item.value('id'))
            if forceString(item.value('action_type')):
                data.action_type = forceString(item.value('action_type')).split('|')[1]
                data.action_typeCode = forceString(item.value('action_type')).split('|')[0]
            data.actEndDate = forceString(item.value('actEndDate'))
            data.fileAttachDatetime = forceString(item.value('fileAttachDatetime'))
            if forceString(item.value('setPerson')):
                data.setPerson = forceString(item.value('setPerson')).split('|')[1]
                data.setPersonCode = forceString(item.value('setPerson')).split('|')[0]
            if forceString(item.value('person')):
                data.person = forceString(item.value('person')).split('|')[1]
                data.personCode = forceString(item.value('person')).split('|')[0]
            data.fileName = forceString(item.value('fileName'))
            data.date_sign_ecp_person = forceString(item.value('date_sign_ecp_person'))
            data.date_sign_ecp_mo = forceString(item.value('date_sign_ecp_mo'))
            data.export_date = forceDateTime(item.value('export_date'))
            data.statusSchematron = forceString(item.value('statusSchematron'))
            data.statusREMD = forceString(item.value('statusREMD'))
            data.export_success = forceString(item.value('export_success'))
            listData.append(data)
        return listData

    @pyqtSignature('')
    def on_actOpenEvent_triggered(self):
        QtGui.qApp.callWithWaitCursor(self, self.openEvent)
    
    @pyqtSignature('')
    def on_actGroupSign_triggered(self):
        actionIdList = []
        tbl, sortModel, model = self.getModelAndTable()
        for row in range(sortModel.rowCount()):
            record = sortModel.getRecordByRow(row)
            actionIdList.append(forceRef(record.value('actionId')))
        actionIdList = list(set(actionIdList))

        if QtGui.qApp.checkGlobalPreference(u'23:ActionGroupSignLockByRecord', u'да'):
            try:
                dialog = CActionGroupSignDialog(self, innerAppLock=True, noFilters=True)
                dialog.setActionIdList(actionIdList)
                dialog.exec_()
            except:
                QtGui.qApp.logCurrentException()
        else:
            lockIdList = []
            excludedActionIdList = []
            alreadyLockedCount = 0
            lockErrorCount = 0
            for actionId in actionIdList:
                appLockId, message = self.tryLock('Action', actionId, shorted=1)
                if appLockId:
                    lockIdList.append(appLockId)
                else:
                    excludedActionIdList.append(actionId)
                    if message == u'Не удалось установить блокировку':
                        lockErrorCount += 1
                    if message.startswith(u'Данные'):
                        alreadyLockedCount += 1
            if len(excludedActionIdList) > 0:
                QtGui.QMessageBox.information(self, u'Внимание',
                    (u'Из списка были исключены Действия, заблокированные другими пользователями (%d шт)'
                    u' или блокировку на которые установить не удалось (%d шт)') % (alreadyLockedCount, lockErrorCount))

            actionIdList = list(set(actionIdList) - set(excludedActionIdList))
            try:
                dialog = CActionGroupSignDialog(self, noFilters=True)
                dialog.setActionIdList(actionIdList)
                dialog.exec_()
            finally:
                for lockId in lockIdList:
                    self.releaseLock(lockId)
    
    def openEvent(self):
        tbl, sortModel, model = self.getModelAndTable()
        selectedRow = self.getSelectedRows(tbl)
        record = sortModel.getRecordByRow(selectedRow[0])
        eventId = forceRef(record.value('eventId')) if record else None
        if eventId:
            try:
                formClass = getEventFormClass(eventId)
                if formClass == CF088EditDialog:
                    db = QtGui.qApp.db
                    tableAction = db.table('Action')
                    recordAction = db.getRecordEx(tableAction, [tableAction['createDatetime'], tableAction['id']],
                                                [tableAction['event_id'].eq(eventId), tableAction['deleted'].eq(0)])
                    createDate = forceDate(recordAction.value('createDatetime')) if recordAction else None
                    actionId = forceRef(recordAction.value('id')) if recordAction else None
                    if createDate and createDate >= QDate(2022, 1, 1):
                        formClass = CF0882022EditDialog
                    dialog = formClass(self)
                    dialog.load(actionId)
                else:
                    dialog = formClass(self)
                    dialog.load(eventId)
                QtGui.qApp.restoreOverrideCursor()
                dialog.setReadOnly(True)
                if dialog.exec_():
                    tbl.setCurrentRow(selectedRow)
            finally:
                dialog.deleteLater()

    def contentToHTML(self):
        reportHeader = u'Сводка о формировании СЭМД для РЭМД'
        tbl, sortModel, model = self.getModelAndTable()
        tbl.setReportHeader(reportHeader)
        return tbl.contentToHTML()

    def openAttachFile(self):
        interface = QtGui.qApp.webDAVInterface
        tbl, sortModel, model = self.getModelAndTable()
        currentRow = forceInt(tbl.currentRow())
        attachedFileId = forceInt(tbl.model().records[currentRow].value('afa_id'))
        tableName = 'Action_FileAttach'
        attachedFile = self.loadItem(interface, tableName, attachedFileId)

        fileOk = bool(attachedFile) and not attachedFile.isLost
        if fileOk and self.canOpen(attachedFile):
            url = interface.getUrl(attachedFile)
            QtGui.QDesktopServices.openUrl(QUrl(url))

    def canOpen(self, fileItem):
        return self.userHasRights(fileItem, urCanOpenAnyAttachedFile, urCanOpenOwnAttachedFile)

    def userHasRights(self, fileItem, anyRight, ownRight):
        app = QtGui.qApp
        if app.userHasRight(anyRight):
            return True
        ownFile = bool(fileItem) and not fileItem.isLost and fileItem.authorId == app.userId
        return ownFile and app.userHasRight(ownRight)

    def loadItem(self, interface, tableName, attachFileId):
        db = QtGui.qApp.db
        table = db.table(tableName)
        cond = db.joinAnd([table['deleted'].eq(0), table['id'].eq(attachFileId)])
        record = db.getRecordEx(table, '*', cond)
        result = None
        if record:
            path = forceString(record.value('path'))
            item = interface.createAttachedFileItem(path)
            item.setRecord(record)
            result = item
        return result


class CActionFileAttachModel(CRecordListModel):
    def __init__(self, parent):
        CRecordListModel.__init__(self, parent)
        self.addCol(CInDocTableCol(u'ФИО \nПациента', 'fio_client', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Код \nкарточки', 'eventId', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Тип \nсобытия', 'event_type_name', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Период \nобращения', 'period', 30)).setReadOnly()
        self.addCol(CInDocTableCol(u'Тип \nдействия', 'action_type', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Дата \nвыполнения \nдействия', 'actEndDate', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Дата \nприкрепления', 'documentDate', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Назначил', 'setPerson', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Врач', 'person', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Подразделение', 'orgStructureName', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Имя файла', 'fileName', 40)).setReadOnly()
        self.addCol(CInDocTableCol(u'Дата \nподписания \nЭЦП врача', 'date_sign_ecp_person', 40)).setReadOnly()
        self.addCol(CInDocTableCol(u'Дата \nподписания \nЭЦП МО', 'date_sign_ecp_mo', 30)).setReadOnly()
        self.addCol(CInDocTableCol(u'Дата \nэкспорта', 'export_date', 30)).setReadOnly()
        self.addCol(CInDocTableCol(u'Информация по схематрону', 'StatusSchematron', 40)).setReadOnly()
        self.addCol(CInDocTableCol(u'Информация о \nприеме документа \nфедеральным РЭМД', 'StatusREMD', 40)).setReadOnly()
        self.addCol(CInDocTableCol(u'Отправка в \nРегиональный РЭМД', 'export_success', 40)).setReadOnly()
        self.addHiddenCol('actionId')

        self.headerSortingCol = {0: True}
        self.records = None
        self.validationResults = {}
        self.validationResultColors = {}
        dateExecActionBegDate = QDate().currentDate().addDays(-2)
        self.loadData(dateExecActionBegDate=dateExecActionBegDate)

    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if 0 <= row < len(self._items) and role == Qt.BackgroundRole:
            record = self._items[row]
            id = forceRef(record.value('id'))
            result = self.validationResults.get(id)
            if result:
                color = self.validationResultColors.get(result.code)
                if color:
                    if row % 2 == 1:
                        color = color.darker(110)
                    return QBrush(color)
        return CRecordListModel.data(self, index, role)

    def getActionTypeIdListByFlatCode(self, flatCode):
        if not isinstance(flatCode, list):
            flatCode = [flatCode]
        db = QtGui.qApp.db
        tableActionType = db.table('ActionType')
        cond = [tableActionType['deleted'].eq(0),
                db.joinOr([tableActionType['flatCode'].like(flatCodeItem) for flatCodeItem in flatCode]),
                ]
        return db.getDistinctIdList(tableActionType, 'id', cond)

    def loadData(self, lastName=None, firstName=None, patrName=None, eventId=None, signedIndex=5,
                 orgStructureList=None, begDate=None, endDate=None, actionType=None, personId=None,
                 identify=None, eventType=None, dateExecActionBegDate=None, dateExecActionEndDate=None,
                 eventBegDate=None, eventEndDate=None, attachFileBegDate=None, attachFileEndDate=None,
                 validationResultCodes=None, specialityId=None, personSNILS=None,
                 financeId=None, actionNoFile=None, uploadedDocs=None):

        db = QtGui.qApp.db

        tableActionFileAttach = db.table('Action_FileAttach').alias('afa')
        tableActionFileAttachPDF = db.table('Action_FileAttach').alias('afaPDF')
        tableAction = db.table('Action').alias('a')
        tableClient = db.table('Client')
        tableEvent = db.table('Event')
        tablePerson = db.table('Person')
        tablePersonOrgStructure = db.table('Person').alias('pOrgStructure')
        tableSetPersonOrgStructure = db.table('Person').alias('labPers')
        tableOrgStructureLab = db.table('OrgStructure').alias('oslabPers')
        tableOrgStructure = db.table('OrgStructure').alias('os')
        tableActionType = db.table('ActionType').alias('AT')
        tableEventType = db.table('EventType')
        tableInformationMessages1 = db.table('Information_Messages').alias('IM1')
        tableInformationMessages2 = db.table('Information_Messages').alias('IM2')
        tableActionTypeIdentification = db.table('ActionType_Identification').alias('ati')
        tableActionFileAttachExport = db.table('Action_FileAttach_Export').alias('afe')
        tableAccountingSystem = db.table('rbAccountingSystem').alias('rbAS')
        tableContract = db.table('Contract')

        # Общие колонки на вывод
        cols0 = [
            u"DISTINCT " + forceString(tableAction['id'].alias('actionId')),
            u"concat_ws(' ', " + forceString(tableActionType['name']) + u", 'от', DATE_FORMAT(a.endDate, '%d.%m.%Y')) as title",
            tableEvent['id'].alias('eventId'),
            tableEventType['name'].alias('event_type_name'),
            u"CASE WHEN ati.value != '291' THEN  pOrgStructure.orgStructure_id ELSE labPers.orgStructure_id END as structure_id",
            tableOrgStructure['name'].alias('structure'),
            u"concat_ws('|', " + forceString(tableActionType['code']) + u"," + forceString(tableActionType['name']) + u") AS action_type",
            u"concat_ws(' ', Client.`lastName`, Client.`firstName`, Client.`patrName`) AS fio_client",
            tableAction['endDate'].alias('actEndDate'),
            u"concat_ws(' - ', DATE_FORMAT(Event.setDate, '%d.%m.%Y'), DATE_FORMAT(Event.execDate, '%d.%m.%Y')) AS period",
            u"""concat( labPers.code,'|', formatPersonName(labPers.id)) as setPerson""",

            u"""CASE WHEN ati.value != '291' THEN  concat( pOrgStructure.code,'|', formatPersonName(pOrgStructure.id))
            ELSE  concat( labPers.code,'|', formatPersonName(labPers.id))    END as person""",
            u"""CASE WHEN ati.value != '291' THEN  os.name
            ELSE  oslabPers.name END as orgStructureName""",
        ]

        # Колонки первого запроса
        cols1 = [
            u"SUBSTRING_INDEX(afa.path, '/', -1 ) as fileName",
            tableActionFileAttach['id'].alias('afa_id'),
            tableActionFileAttach['respSigner_id'],
            tableActionFileAttach['respSigningDatetime'].alias('date_sign_ecp_person'),
            tableActionFileAttach['orgSigningDatetime'].alias('fileAttachDatetime'),
            tableActionFileAttachExport['dateTime'].alias('export_date'),
            tableActionFileAttachExport['note'].alias('StatusSchematron'),
            u"""if(afe.id is null and IM2.id IS NULL and IM1.id IS NULL, '', IF((afe.success = 1 or afe.note = 'XML - документ не подписан') OR IM2.id IS NOT NULL OR IM1.id IS NOT NULL, 'успешно', 'ошибка')) as export_success""",
            u"""case
            when IM1.RemdRegNumber                      then CONCAT('Успех - ', IM1.RemdRegNumber)
            when IM1.id is NULL AND IM2.status = 'Success' then 'Ожидается валидация документа на федеральном уровне'
            when IM1.id is NULL AND IM2.status = 'Failed'  then CONCAT('Ошибка - ', IM2.Message)
            when IM1.id is NULL AND IM2.id IS NULL AND (afe.id IS NULL OR afe.success=0 OR afe.note = 'XML - документ не подписан')  then ''
            ELSE 'Информация еще не получена'
            END AS StatusREMD""",
            tableActionFileAttach['master_id'],
            tableActionFileAttach['createDatetime'].alias('documentDate'),
            tableActionFileAttach['modifyDatetime'],
            u"IF(afa.`respSignatureBytes` IS NULL, 'Не подписан', 'Подписан') AS isRespSigned",
            u"IF(afa.`orgSignatureBytes` IS NULL, 'Не подписан', 'Подписан') AS isOrgSigned",
            tableActionFileAttach['orgSigningDatetime'].alias('date_sign_ecp_mo'),
        ]
        cols1 = cols0 + cols1

        # Колонки второго запроса
        cols2 = [
            u"'' as fileName",
            u"NULL as afa_id",
            u"NULL AS respSigner_id",
            u"NULL AS date_sign_ecp_person",
            u"NULL as fileAttachDatetime",
            u"NULL AS export_date",
            u"'' as export_success",
            u"NULL AS StatusSchematron",
            u"'' AS StatusREMD",
            u"NULL AS master_id",
            u"NULL AS documentDate",
            u"NULL AS modifyDatetime",
            u"NULL AS isRespSigned",
            u"NULL AS isOrgSigned",
            u"NULL AS date_sign_ecp_mo",
        ]
        cols2 = cols0 + cols2

        cond0 = [
            tableAction['deleted'].eq(0),
            tableActionType['deleted'].eq(0),
            tableActionTypeIdentification['deleted'].eq(0),
            tableActionType['flatCode'].notlike(u'%temperatureSheet%'),
            tableAccountingSystem['urn'].eq(u'urn:oid:1.2.643.2.69.1.1.1.195.Cda')
        ]

        tableQuery0 = tableAction
        tableQuery0 = tableQuery0.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        tableQuery0 = tableQuery0.innerJoin(tableActionTypeIdentification, tableActionTypeIdentification['master_id'].eq(tableActionType['id']))
        tableQuery0 = tableQuery0.innerJoin(tableAccountingSystem, tableAccountingSystem['id'].eq(tableActionTypeIdentification['system_id']))
        tableQuery0 = tableQuery0.leftJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
        tableQuery0 = tableQuery0.leftJoin(tableEventType, tableEventType['id'].eq(tableEvent['eventType_id']))
        tableQuery0 = tableQuery0.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
        tableQuery0 = tableQuery0.leftJoin(tablePersonOrgStructure, tablePersonOrgStructure['id'].eq(tableAction['person_id']))
        tableQuery0 = tableQuery0.leftJoin(tableOrgStructure, tableOrgStructure['id'].eq(tablePersonOrgStructure['orgStructure_id']))
        tableQuery0 = tableQuery0.leftJoin(tableSetPersonOrgStructure, tableSetPersonOrgStructure['id'].eq(tableAction['setPerson_id']))
        tableQuery0 = tableQuery0.leftJoin(tableOrgStructureLab, tableOrgStructureLab['id'].eq(tableSetPersonOrgStructure['orgStructure_id']))
        tableQuery0 = tableQuery0.leftJoin(tableContract, tableContract['id'].eq(tableEvent['contract_id']))

        if uploadedDocs:
            tableQuery0 = tableQuery0.leftJoin(tableActionFileAttach,
                                               u"""
                                   afa.id =(  SELECT    MAX(id) FROM    Action_FileAttach afa
                                     WHERE    afa.master_id = a.id    AND afa.deleted = 0
                                       AND ( right(SUBSTRING_INDEX(afa.path, '/', -1 ),  3) = "xml" AND RIGHT(rbAS.urn, 3)= "cda") )
                                               """)
        else:
            tableQuery0 = tableQuery0.leftJoin(tableActionFileAttach,
                                               u"""
                                    afa.id =(  SELECT    MAX(id) FROM    Action_FileAttach afa
                                      WHERE    afa.master_id = a.id    AND afa.deleted = 0
                                        AND ( right(SUBSTRING_INDEX(afa.path, '/', -1 ),  3) = "xml" AND RIGHT(rbAS.urn, 3)= "cda") )
                                               """)
            tableQuery0 = tableQuery0.leftJoin(tableActionFileAttachPDF,
                                               u"""
                                    afaPDF.id =(  SELECT    MAX(id) FROM    Action_FileAttach afa 
                                    WHERE    afa.master_id = a.id    AND afa.deleted = 0 AND right(SUBSTRING_INDEX(afa.path, '/', -1 ),  3) = "pdf" )
                                               """)

        tableQuery0 = tableQuery0.leftJoin(tableActionFileAttachExport,
                                           u"""afe.id = (SELECT MAX(id) FROM Action_FileAttach_Export afae WHERE afa.id = afae.master_id)""")
        tableQuery0 = tableQuery0.leftJoin(tableInformationMessages1,
                                           u"""
                                           IM1.id = (SELECT MAX(id) FROM 
                                           Information_Messages WHERE typeMessages = 'REMDStatus' AND IdMedDocumentMis_id = afe.master_id 
                                           AND IdFedRequest IS NOT NULL AND IdFedRequest IS NOT NULL AND RemdRegNumber != '')
                                           """)
        tableQuery0 = tableQuery0.leftJoin(tableInformationMessages2,
                                           u"""
                                           IM2.id = (SELECT MAX(id) FROM 
                                           Information_Messages WHERE typeMessages = 'REMDStatus' AND IdMedDocumentMis_id = afe.master_id )
                                           """)

        if uploadedDocs:
            cond1 = cond0 + [u"""afa.id IS not NULL"""]
            cond2 = cond0
        elif uploadedDocs == False:
            cond1 = cond0 + [u"""afaPDF.id IS not NULL"""] + [u"""afa.id IS NULL"""]
            cond2 = cond0
        else:
            cond2 = cond0 + [u"""afaPDF.id IS NULL"""] + [u"""afa.id IS NULL"""]
            cond1 = cond0

        tableQuery1 = tableQuery0
        tableQuery2 = tableQuery0

        def appendCond(cond):
            cond1.append(cond)
            cond2.append(cond)

        # \/\/\/\/\/\/Filter\/\/\/\/\/\/\/\/\/\/\/\/
        appendCond(tableEvent['org_id'].eq(QtGui.qApp.currentOrgId()))
        appendCond(tableEventType['code'].notInlist(['rmDisp', 'smp', 'hospDir']))
        appendCond(tableEventType['context'].notInlist(['relatedAction']))
        appendCond(tableActionTypeIdentification['note'].isNotNull())
        appendCond(tableActionTypeIdentification['note'].ne(''))
        appendCond(tableActionTypeIdentification['deleted'].eq(0))

        if lastName:
            appendCond("Client.lastName like '%s%%'" % lastName)
        if firstName:
            appendCond("Client.firstName like '%s%%'" % firstName)
        if patrName:
            appendCond("Client.patrName like '%s%%'" % patrName)

        if eventId:
            appendCond(tableEvent['id'].eq(eventId))

        if signedIndex == 1:
            cond1.append(tableActionFileAttach['respSignatureBytes'].isNull())
        elif signedIndex == 2:
            cond1.append(tableActionFileAttach['orgSignatureBytes'].isNull())
        elif signedIndex == 3:
            cond1.append(tableActionFileAttach['orgSignatureBytes'].isNotNull())
        elif signedIndex == 4:
            cond1.append(tableActionFileAttach['respSignatureBytes'].isNotNull())
            cond1.append(tableActionFileAttach['orgSignatureBytes'].isNull())
        elif signedIndex == 5:
            cond1.append(db.joinOr([tableActionFileAttach['respSignatureBytes'].isNull(),
                                   tableActionFileAttach['orgSignatureBytes'].isNull()]))
        elif signedIndex == 6:
            cond1.append(tableActionFileAttach['respSignatureBytes'].isNotNull())

        if orgStructureList:
            appendCond(' CASE WHEN ati.value != "291" THEN  pOrgStructure.orgStructure_id in (' + (
                    ','.join(map(str, orgStructureList))) + ') ELSE labPers.orgStructure_id in (' + (
                                   ','.join(map(str, orgStructureList))) + ') END ')

        if personSNILS and personId:
            rec = db.getRecordEx(tablePerson, [tablePerson['SNILS']], [tablePerson['id'].eq(personId)])
            personSNILS = forceString(rec.value('SNILS')) if rec else None

        if personId and forceBool(personSNILS) == False:
            appendCond(u"""
                CASE
                    WHEN ati.value != '291' THEN a.person_id = {0}
                        ELSE a.setPerson_id = {0}
                    END""".format(int(personId)))
        elif personId and forceBool(personSNILS):
            appendCond(u"""
                CASE
                    WHEN ati.value != '291' THEN pOrgStructure.SNILS = '{1}'
                                            ELSE labPers.SNILS = '{1}'
                    END""".format(int(personId), personSNILS))

        # Дата выполнения действия
        if dateExecActionBegDate and dateExecActionEndDate:
            appendCond(tableAction['endDate'].ge(dateExecActionBegDate))
            appendCond(tableAction['endDate'].lt(dateExecActionEndDate.addDays(1)))
        elif dateExecActionBegDate:
            appendCond(tableAction['endDate'].ge(dateExecActionBegDate))
        elif dateExecActionEndDate:
            appendCond(tableAction['endDate'].lt(dateExecActionEndDate.addDays(1)))
        else:
            if not dateExecActionBegDate and not dateExecActionEndDate and not eventBegDate\
                    and not eventEndDate and not attachFileBegDate and not attachFileEndDate:
                appendCond(tableAction['endDate'].ge(QDate().currentDate().addDays(-2)))

        # Дата окончания события
        if eventBegDate and eventEndDate:
            appendCond(tableEvent['execDate'].ge(eventBegDate))
            appendCond(tableEvent['execDate'].lt(eventEndDate.addDays(1)))
        elif eventBegDate:
            appendCond(tableEvent['execDate'].ge(eventBegDate))
        elif eventEndDate:
            appendCond(tableEvent['execDate'].lt(eventEndDate.addDays(1)))
        else:
            pass

        # Дата прикрепления файла
        if attachFileBegDate and attachFileEndDate:
            cond1.append(tableActionFileAttach['createDatetime'].ge(attachFileBegDate))
            cond1.append(tableActionFileAttach['createDatetime'].lt(attachFileEndDate.addDays(1)))
        elif attachFileBegDate:
            cond1.append(tableActionFileAttach['createDatetime'].ge(attachFileBegDate))
        elif attachFileEndDate:
            cond1.append(tableActionFileAttach['createDatetime'].lt(attachFileEndDate.addDays(1)))

        if actionType:
            appendCond(tableActionType['id'].inlist(getActionTypeDescendants(actionType)))

        if identify:
            appendCond("{0} IN ({1})".format(tableActionTypeIdentification['value'], identify))

        if eventType:
            appendCond(tableEventType['id'].inlist([eventType]))

        if financeId:
            appendCond(tableContract['finance_id'].eq(financeId))
        
        if specialityId:
            appendCond(tablePersonOrgStructure['speciality_id'].inlist(specialityId))
        #/\/\/\/\/\/\/\/\/\/\/\/\Filter/\/\/\/\/\/\/\/\/\/\/\

        stmt1 = db.selectStmt(tableQuery1, cols1, cond1, 'a.id')  # С прикрепленными файлами
        stmt2 = db.selectStmt(tableQuery2, cols2, cond2, 'a.id')  # Без прикрепленных файлов

        if actionNoFile:
            stmt = stmt2
        else:
            stmt = stmt1

        records = []
        query = db.query(stmt)
        while query.next():
            record = query.record()
            records.append(record)

        recordModify = []
        for record in records:
            addRecord = True
            if validationResultCodes:
                id = forceRef(record.value('id'))
                result = self.validationResults.get(id)
                resultCode = result.code if result else None
                if resultCode not in validationResultCodes:
                    addRecord = False
            if addRecord:
                recordModify.append(record)
        self.records = recordModify
        self.setItems(recordModify)


class dataclass():
    def __init__(self):
        self.fio_client = None
        self.event_id = None
        self.event_type_name = None
        self.structure = None
        self.period = None
        self.action_id = None
        self.action_type = None
        self.action_typeCode = None
        self.actEndDate = None
        self.fileAttachDatetime = None
        self.setPerson = None
        self.setPersonCode = None
        self.person = None
        self.personCode = None
        self.fileName = None
        self.date_sign_ecp_person = None
        self.date_sign_ecp_mo = None
        self.export_date = None
        self.statusSchematron = None
        self.statusREMD = None
        self.export_success = None


class CPrintSummaryDocumentsDialog(CDialogBase):
    def __init__(self, parent=None):
        CDialogBase.__init__(self, parent)
        self.layout = QtGui.QGridLayout(self)
        self.listFilterIdentify = ""
        self.filterItems = None

        self.setWindowTitle(u'Параметры отчёта')

        self.edtBegDate = CDateEdit(self)
        self.edtEndDate = CDateEdit(self)
        self.cmbOrgStructure = COrgStructureComboBox(self)
        self.cmbEventStatus = CRecordMultivalueComboBox(self)
        self.cmbEventStatus.enableFilter(True)
        self.cmbEventStatus.setMaximumWidth(500)
        self.setCmbEventStatus()
        self.chkGroupByOrgStructure = QtGui.QCheckBox(u'Группировать по подразделениям')
        self.chkClosedEvents = QtGui.QCheckBox(u'По закрытым событиям')

        self.buttonBox = QtGui.QDialogButtonBox()
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        self.connect(self.buttonBox, SIGNAL('accepted()'), self.accept)
        self.connect(self.buttonBox, SIGNAL('rejected()'), self.reject)

        self.layout.addWidget(QtGui.QLabel(u'Дата начала периода'), 0, 0)
        self.layout.addWidget(self.edtBegDate, 0, 1)

        self.layout.addWidget(QtGui.QLabel(u'Дата окончания периода'), 1, 0)
        self.layout.addWidget(self.edtEndDate, 1, 1)

        self.layout.addWidget(QtGui.QLabel(u'Подразделение'), 2, 0)
        self.layout.addWidget(self.cmbOrgStructure, 2, 1)

        self.layout.addWidget(QtGui.QLabel(u'Детализировать по'), 3, 0)
        self.layout.addWidget(self.cmbEventStatus, 3, 1)

        self.layout.addWidget(self.chkGroupByOrgStructure, 4, 0)

        self.layout.addWidget(self.chkClosedEvents, 5, 0)

        self.layout.addWidget(self.buttonBox, 6, 0, 1, 2)


    def setCmbEventStatus(self, signal=False):
        self.cmbEventStatus.clear()

        db = QtGui.qApp.db
        stmt = u'''SELECT note, value, master_id
FROM ActionType_Identification LEFT JOIN rbAccountingSystem `as` ON
ActionType_Identification.system_id = `as`.id WHERE
`as`.code IN ('n3.medDocumentType.Pdf', 'n3.medDocumentType.Cda')
AND note != '' AND note IS not NULL and deleted = 0 ORDER BY note '''

        list_auto_check = []
        x = 0

        if self.listFilterIdentify != "" and signal is False:
            lFilterIdentify = self.listFilterIdentify.replace(" ", "")
            lFilterIdentify = lFilterIdentify.split(',')

        query = db.query(stmt)

        filterItems = OrderedDict()
        while query.next():
            rec = query.record()
            value = forceString(rec.value('value'))
            name = forceString(rec.value('note'))

            filterItems[value] = name.replace(u'\xa0', '')
            if self.listFilterIdentify != "" and signal is False:
                if value in lFilterIdentify:
                    list_auto_check.append(x)
            else:
                list_auto_check.append(x)
            x += 1

        self.cmbEventStatus.setItems(OrderedDict(sorted(filterItems.items())))
        # self.cmbEventStatus.setCheckedRows(list_auto_check)
        self.filterItems = filterItems

    def getListCode(self):
        listIdentify = []
        identify = self.cmbEventStatus.value()
        for i in re.split(',', identify):
            if trim(i).isdigit():
                listIdentify.append(trim(i))
        return listIdentify

    def getListName(self):
        listName = []
        listId = self.getListCode()
        for i in listId:
            name = self.filterItems[i]
            listName.append(name)
        return listName

    def params(self):
        paramentrs = dict()
        paramentrs['begDate'] = self.edtBegDate.date()
        paramentrs['endDate'] = self.edtEndDate.date()
        paramentrs['orgStructureId'] = self.cmbOrgStructure.value()
        paramentrs['chkGroupByOrgStructure'] = self.chkGroupByOrgStructure.isChecked()
        paramentrs['chkClosedEvents'] = self.chkClosedEvents.isChecked()
        paramentrs['checkCode'] = self.getListCode()
        paramentrs['checkName'] = self.getListName()
        return paramentrs

    def setParams(self, params):
        today = QtCore.QDate.currentDate()
        self.edtBegDate.setDate(params.get('begDate', today))
        self.edtEndDate.setDate(params.get('endDate', today))
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        self.chkGroupByOrgStructure.setChecked(params.get('chkGroupByOrgStructure', False))
        self.chkClosedEvents.setChecked(params.get('chkClosedEvents', False))
        if params.get('checkName', None):
            listName = params.get('checkName')
            self.cmbEventStatus.setCheckedDict(listName, True)


class CReportPrintSummaryDocuments(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Сводка по  документам')

    def getSetupDialog(self, parent):
        result = CPrintSummaryDocumentsDialog(parent)
        result.setWindowTitle(self.title())
        return result

    def select(self, params):
        db = QtGui.qApp.db

        listMaster_id = params.get('checkCode')

        begDate = params.get('begDate')
        begDate = db.formatDate(begDate).replace("'", "") + 'T00:00:00'

        endDate = params.get('endDate').addDays(1)
        endDate = db.formatDate(endDate).replace("'", "") + 'T00:00:00'

        chkClosedEvents = params.get('chkClosedEvents')
        orgStructureId = params.get('orgStructureId', None)
        orgStructureIdList = None
        if orgStructureId:
            orgStructureIdList = getOrgStructureDescendants(orgStructureId)
        if orgStructureIdList:
            orgStructure = ' and CASE WHEN ati.value != "291" THEN  pOrgStructure.orgStructure_id in (' + (','.join(map(str, orgStructureIdList))) + ') ELSE labPers.orgStructure_id in (' + (','.join(map(str, orgStructureIdList))) + ') END '
        else:
            orgStructure = ''

        if listMaster_id:
            actionTypeIden = u'AND (ati.`value` in ({0}))'.format(u', '.join(listMaster_id))
        else:
            actionTypeIden = ''

        stmt = u"""
SELECT
  COUNT(DISTINCT a.`id`) AS '1', # кол-во действий в которых может быть файл
  CASE
      WHEN ati.value != '291' THEN  pOrgStructure.SNILS
      ELSE  labPers.SNILS
    END
  as person,
CASE
      WHEN ati.value != '291' THEN  pOrgStructure.id
      ELSE  labPers.id
    END AS gg,
CASE
      WHEN ati.value != '291' THEN concat_ws(' ', pOrgStructure.`lastName`, pOrgStructure.`firstName`, pOrgStructure.`patrName`)
      ELSE concat_ws(' ', labPers.`lastName`, labPers.`firstName`, labPers.`patrName`)
    END AS gg2
  ,
  CASE
      WHEN ati.value != '291' THEN  CASE
    WHEN os.name IS NULL THEN 'Неизвестно'
    ELSE os.name
  end
      ELSE  CASE
    WHEN oslabPers.name IS NULL THEN 'Неизвестно'
    ELSE oslabPers.name
  end
    END as orgStructure,
     CASE
      WHEN ati.value != '291' THEN  CASE
    WHEN os.name IS NULL THEN '0'
    ELSE os.id
  end
      ELSE  CASE
    WHEN oslabPers.name IS NULL THEN '0'
    ELSE oslabPers.id
  end
    END as orgStructureId,
  count(IFNULL(afa.id,null)) as '2', # наличие файла
count(IF(afe.success = 1 OR IM1.id IS NOT NULL OR IM2.id IS NOT NULL OR afe.note = 'XML - документ не подписан', 1, null)) AS '3' , # наличие выгрузки в регион
count(IM1.RemdRegNumber) AS '4', # успешность федералов
  count(if(IM1.RemdRegNumber, NULL, if(IM2.status='Failed',1,null))) AS '5', # ошибка федералов (последнее полученное сообщение за исключением тех услучаев где мы получили ранее статус 4)
count(if(IM1.id is null AND IM2.id IS NULL AND afe.success=1, 1, null)) AS '6' # нет сообщений

FROM
  Action AS a
INNER JOIN ActionType AS AT ON  AT.`id` = a.`actionType_id`
INNER JOIN ActionType_Identification AS ati ON  ati.`master_id` = AT.`id`
INNER JOIN rbAccountingSystem AS rbAS ON  rbAS.`id` = ati.`system_id`
LEFT JOIN Event ON  Event.`id` = a.`event_id`
LEFT JOIN EventType ON  EventType.`id` = Event.`eventType_id`
LEFT JOIN Client ON  Client.`id` = Event.`client_id`
LEFT JOIN Person AS pOrgStructure ON  pOrgStructure.`id` = a.`person_id`
  LEFT JOIN Person AS labPers ON  labPers.`id` = a.setPerson_id
LEFT JOIN OrgStructure AS os ON  os.`id` = pOrgStructure.`orgStructure_id`
LEFT JOIN OrgStructure AS oslabPers ON  oslabPers.`id` = labPers.`orgStructure_id`
LEFT JOIN Action_FileAttach AS afa ON  afa.id =(  SELECT    MAX(id)
  FROM    Action_FileAttach afa
  WHERE    afa.master_id = a.id    AND afa.deleted = 0
    AND ( right(SUBSTRING_INDEX(afa.path, '/', -1 ),  3) = "xml" AND RIGHT(rbAS.urn, 3)= "cda") 
                                        )
LEFT JOIN Action_FileAttach_Export AS afe ON  afe.id = (  SELECT
    MAX(id)
  FROM
    Action_FileAttach_Export afae
  WHERE
    afa.id = afae.master_id)

LEFT JOIN Information_Messages AS IM1 ON  IM1.id = (SELECT MAX(id) FROM 
    Information_Messages WHERE typeMessages = 'REMDStatus' AND IdMedDocumentMis_id = afe.master_id 
    AND IdFedRequest IS NOT NULL AND IdFedRequest IS NOT NULL AND RemdRegNumber != '')

LEFT JOIN Information_Messages AS IM2 ON  IM2.id = (SELECT MAX(id) FROM 
    Information_Messages WHERE typeMessages = 'REMDStatus' AND IdMedDocumentMis_id = afe.master_id )

WHERE
  (a.`deleted` = 0)
  AND (AT.`deleted` = 0)
  AND (ati.`deleted` = 0)
  AND (AT.`flatCode` NOT LIKE '%temperatureSheet%')
  AND (rbAS.urn = 'urn:oid:1.2.643.2.69.1.1.1.195.Cda')
  AND (a.`endDate` >= '{begDate}')
  AND (a.`endDate`<'{endDate}')
  {orgStructure}
  {eventClose}
  {actionTypeIden}
  AND (Event.`org_id` = {currentOgrId})
  AND (EventType.`code` NOT IN ('rmDisp', 'smp', 'hospDir'))
  AND (EventType.`context` NOT IN ('relatedAction'))
  AND (ati.`note` IS NOT NULL)
  AND (ati.`note` != '')
  AND (ati.`deleted` = 0)
  AND (afa.id IS not NULL)
  GROUP BY person

ORDER BY orgStructure, orgStructureId, gg2;

;
""".format(
            begDate=begDate,
            endDate=endDate,
            eventClose=u'AND (Event.isClosed = 1)' if chkClosedEvents else '',
            orgStructure=orgStructure,
            currentOgrId=QtGui.qApp.currentOrgId(),
            actionTypeIden=actionTypeIden)

        records = []
        query = db.query(stmt)
        while query.next():
            record = query.record()
            clmn1 = forceInt(record.value('1'))
            clmn2 = forceInt(record.value('2'))
            clmn3 = forceInt(record.value('3'))
            clmn4 = forceInt(record.value('4'))
            clmn5 = forceInt(record.value('5'))
            clmn6 = forceInt(record.value('6'))

            snils = forceInt(record.value('person'))
            orgStructure = forceInt(record.value('orgStructureId'))
            orgStructureName = forceString(record.value('orgStructure'))
            labPersId = forceInt(record.value('gg'))
            person = forceString(record.value('gg2'))

            records.append(
                {
                    'clmn1': clmn1,
                    'clmn2': clmn2,
                    'clmn3': clmn3,
                    'clmn4': clmn4,
                    'clmn5': clmn5,
                    'clmn6': clmn6,
                    'snils': snils,
                    'orgStructure': orgStructure,
                    'orgStructureName': orgStructureName,
                    'labPersId': labPersId,
                    'person': person
                }
            )

        return records

    def build(self, params):
        group = params.get('chkGroupByOrgStructure')
        checkName = params.get('checkName')
        
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Сводка по документам')
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        if checkName:
            cursor.insertText(u'Тип электронного документа: ' + u'; '.join(checkName))
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        data = self.select(params)

        tableColumns = [
            ('40%', [u'Врач'],                   CReportBase.AlignLeft),
            ('10%', [u'Введено действий'],       CReportBase.AlignLeft),
            ('10%', [u'Сформировано документов'], CReportBase.AlignLeft),
            ('10%', [u'Выгружено в ИЭМК'],       CReportBase.AlignLeft),
            ('10%', [u'Успешно принят РЭМД'],    CReportBase.AlignLeft),
            ('10%', [u'Отклонен РЭМД'],          CReportBase.AlignLeft),
            ('10%', [u'Статус РЭМД не получен'], CReportBase.AlignLeft),
        ]

        table = createTable(cursor, tableColumns, duplicateHeaderOnNewPage=False)

        boldChars = QtGui.QTextCharFormat()
        boldChars.setFontWeight(QtGui.QFont.Bold)

        orgStr = None
        resultClmn1 = 0
        resultClmn2 = 0
        resultClmn3 = 0
        resultClmn4 = 0
        resultClmn5 = 0
        resultClmn6 = 0

        def getColor(clmn):
            if int(clmn) >= 500:
                return Qt.green
            else:
                return None

        for rec in data:
            clmn1 = rec['clmn1']
            clmn2 = rec['clmn2']
            clmn3 = rec['clmn3']
            clmn4 = rec['clmn4']
            clmn5 = rec['clmn5']
            clmn6 = rec['clmn6']
            orgStructure = rec['orgStructure']
            orgStructureName = rec['orgStructureName']
            person = rec['person']

            if not group:
                textColor = getColor(clmn4)

                row = table.addRow()
                table.setText(row, 0, forceString(person), brushColor=textColor)
                table.setText(row, 1, forceString(clmn1), brushColor=textColor)
                table.setText(row, 2, forceString(clmn2), brushColor=textColor)
                table.setText(row, 3, forceString(clmn3), brushColor=textColor)
                table.setText(row, 4, forceString(clmn4), brushColor=textColor)
                table.setText(row, 5, forceString(clmn5), brushColor=textColor)
                table.setText(row, 6, forceString(clmn6), brushColor=textColor)

                resultClmn1 += clmn1
                resultClmn2 += clmn2
                resultClmn3 += clmn3
                resultClmn4 += clmn4
                resultClmn5 += clmn5
                resultClmn6 += clmn6

            else:
                if orgStr != orgStructure:
                    orgStr = orgStructure

                    allClmn1 = sum([i['clmn1'] for i in data if i['orgStructure'] == orgStructure])
                    allClmn2 = sum([i['clmn2'] for i in data if i['orgStructure'] == orgStructure])
                    allClmn3 = sum([i['clmn3'] for i in data if i['orgStructure'] == orgStructure])
                    allClmn4 = sum([i['clmn4'] for i in data if i['orgStructure'] == orgStructure])
                    allClmn5 = sum([i['clmn5'] for i in data if i['orgStructure'] == orgStructure])
                    allClmn6 = sum([i['clmn6'] for i in data if i['orgStructure'] == orgStructure])


                    row = table.addRow()
                    table.setText(row, 0, forceString(orgStructureName), charFormat=boldChars)
                    table.setText(row, 1, forceString(allClmn1), charFormat=boldChars)
                    table.setText(row, 2, forceString(allClmn2), charFormat=boldChars)
                    table.setText(row, 3, forceString(allClmn3), charFormat=boldChars)
                    table.setText(row, 4, forceString(allClmn4), charFormat=boldChars)
                    table.setText(row, 5, forceString(allClmn5), charFormat=boldChars)
                    table.setText(row, 6, forceString(allClmn6), charFormat=boldChars)

                    resultClmn1 += allClmn1
                    resultClmn2 += allClmn2
                    resultClmn3 += allClmn3
                    resultClmn4 += allClmn4
                    resultClmn5 += allClmn5
                    resultClmn6 += allClmn6

                textColor = getColor(clmn4)

                row = table.addRow()
                table.setText(row, 0, forceString(person), brushColor=textColor)
                table.setText(row, 1, forceString(clmn1), brushColor=textColor)
                table.setText(row, 2, forceString(clmn2), brushColor=textColor)
                table.setText(row, 3, forceString(clmn3), brushColor=textColor)
                table.setText(row, 4, forceString(clmn4), brushColor=textColor)
                table.setText(row, 5, forceString(clmn5), brushColor=textColor)
                table.setText(row, 6, forceString(clmn6), brushColor=textColor)

        row = table.addRow()
        if not group:
            table.setText(row, 0, forceString(u"Результат по врачам:"), charFormat=boldChars)
        else:
            table.setText(row, 0, forceString(u"Результат по МО/врачам:"), charFormat=boldChars)
        table.setText(row, 1, forceString(resultClmn1), charFormat=boldChars)
        table.setText(row, 2, forceString(resultClmn2), charFormat=boldChars)
        table.setText(row, 3, forceString(resultClmn3), charFormat=boldChars)
        table.setText(row, 4, forceString(resultClmn4), charFormat=boldChars)
        table.setText(row, 5, forceString(resultClmn5), charFormat=boldChars)
        table.setText(row, 6, forceString(resultClmn6), charFormat=boldChars)

        return doc


class CReportPrintWindow(CReport):
    def __init__(self, parent, data):
        CReport.__init__(self, parent)
        self.setTitle(u'Печать списка')
        self.data = data

    def getSetupDialog(self, parent):
        return CVoidSetupDialog(parent)

    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Печать списка')
        cursor.insertBlock()

        reportSchematron = bool([i.statusSchematron for i in self.data if i.statusSchematron != u''])
        reportREMD = bool([i.statusREMD for i in self.data if i.statusREMD != u''])

        colInfSchm = '3%'
        colInfREMD = '16.5%'
        if reportSchematron and reportREMD:
            colInfSchm = '7%'
            colInfREMD = '12.5%'
        elif reportSchematron:
            colInfSchm = '16.5%'
            colInfREMD = '3%'
        elif reportREMD:
            colInfSchm = '3%'
            colInfREMD = '16.5%'

        tableColumns = [
            ('1%', [u'№'], CReportBase.AlignCenter),
            ('8.5%', [u'ФИО \nПациента'], CReportBase.AlignLeft),
            ('3%', [u'Код \nкарточки'], CReportBase.AlignLeft),
            ('8%', [u'Тип \nсобытия'], CReportBase.AlignLeft),
            ('4%', [u'Период \nобращения'], CReportBase.AlignLeft),
            ('8%', [u'Тип \nдействия'], CReportBase.AlignLeft),
            ('4%', [u'Дата \nвыполнения \nдействия'], CReportBase.AlignLeft),
            ('4%', [u'Дата \nприкрепления'], CReportBase.AlignLeft),
            ('7.5%', [u'Назначил'], CReportBase.AlignLeft),
            ('7.5%', [u'Врач'], CReportBase.AlignLeft),
            ('7.5%', [u'Имя файла'], CReportBase.AlignLeft),
            ('4%', [u'Дата \nподписания \nЭЦП врача'], CReportBase.AlignLeft),
            ('4%', [u'Дата \nподписания \nЭЦП МО'], CReportBase.AlignLeft),
            ('4%', [u'Дата \nэкспорта'], CReportBase.AlignLeft),
            (colInfSchm, [u'Информация по схематрону'], CReportBase.AlignLeft),
            (colInfREMD, [u'Информация о \nприеме документа \nфедеральным РЭМД'], CReportBase.AlignLeft),
            ('5.5%', [u'Отправка в \nРегиональный РЭМД'], CReportBase.AlignLeft),
        ]

        table = createTable(cursor, tableColumns, duplicateHeaderOnNewPage=False)

        x = 0
        for value in self.data:
            row = table.addRow()
            x = x + 1
            table.setText(row, 0, forceString(x))
            table.setText(row, 1, value.fio_client)
            table.setText(row, 2, forceString(value.event_id))
            table.setText(row, 3, forceString(value.event_type_name))
            table.setText(row, 4, forceString(value.period))
            table.setText(row, 5, forceString(value.action_type))
            table.setText(row, 6, forceString(value.actEndDate))
            table.setText(row, 7, forceString(value.fileAttachDatetime))
            table.setText(row, 8, forceString(value.setPerson))
            table.setText(row, 9, forceString(value.person))
            table.setText(row, 10, forceString(value.fileName))
            table.setText(row, 11, forceString(value.date_sign_ecp_person))
            table.setText(row, 12, forceString(value.date_sign_ecp_mo))
            table.setText(row, 13, forceString(value.export_date))
            table.setText(row, 14, forceString(value.statusSchematron))
            table.setText(row, 15, forceString(value.statusREMD))
            table.setText(row, 16, forceString(value.export_success))

        return doc


class CReportGroupStrucPerson(CReport):
    def __init__(self, parent, data):
        CReport.__init__(self, parent)
        self.setTitle(u'Печать списка')
        self.data = data

    def getSetupDialog(self, parent):
        return CVoidSetupDialog(parent)

    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Группировка по подразделениям и врачам')
        cursor.insertBlock()

        tableColumns = [
            ('15%', [u'Подразделение'], CReportBase.AlignLeft),
            ('10%', [u'Врач'], CReportBase.AlignLeft),
            ('15%', [u'ФИО Пациента'], CReportBase.AlignLeft),
            ('10%', [u'Код карточки'], CReportBase.AlignLeft),
            ('15%', [u'Тип события'], CReportBase.AlignLeft),
            ('15%', [u'Период обращения'], CReportBase.AlignLeft),
            ('20%', [u'Тип действия'], CReportBase.AlignLeft),
        ]

        table = createTable(cursor, tableColumns, duplicateHeaderOnNewPage=False)

        self.data.sort(key=lambda item: (item.structure, item.person))

        structure = None
        person = None

        for value in self.data:
            if value.structure != structure:
                structure = value.structure
                row = table.addRow()
                table.setText(row, 0, forceString(value.structure))
                table.setText(row, 1, forceString(u"   "))
                table.setText(row, 2, forceString(u"   "))
                table.setText(row, 3, forceString(u"   "))
                table.setText(row, 4, forceString(u"   "))
                table.setText(row, 5, forceString(u"   "))
                table.setText(row, 6, forceString(u"   "))

            if value.structure == structure:
                if value.person != person:
                    person = value.person
                    row = table.addRow()
                    table.setText(row, 0, forceString(u"   "))
                    table.setText(row, 1, forceString(value.person))
                    table.setText(row, 2, forceString(value.fio_client))
                    table.setText(row, 3, forceString(value.event_id))
                    table.setText(row, 4, forceString(value.event_type_name))
                    table.setText(row, 5, forceString(value.period))
                    table.setText(row, 6, forceString(value.action_type))
                elif value.person == person:
                    row = table.addRow()
                    table.setText(row, 0, forceString(u"   "))
                    table.setText(row, 1, forceString(u"   "))
                    table.setText(row, 2, forceString(value.fio_client))
                    table.setText(row, 3, forceString(value.event_id))
                    table.setText(row, 4, forceString(value.event_type_name))
                    table.setText(row, 5, forceString(value.period))
                    table.setText(row, 6, forceString(value.action_type))

        return doc


class CReportGroupPersonInfo(CReport):
    def __init__(self, parent, data):
        CReport.__init__(self, parent)
        self.setTitle(u'Печать списка')
        self.data = data

    def getSetupDialog(self, parent):
        return CVoidSetupDialog(parent)

    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Группировка по врачам с отображением количественных показателей')
        cursor.insertBlock()

        tableColumns = [
            ('50%', [u'Врач'], CReportBase.AlignLeft),
            ('10%', [u'Действий'], CReportBase.AlignLeft),
            ('10%', [u'Прикрепленно файлов'], CReportBase.AlignLeft),
            ('10%', [u'Подписано врачем'], CReportBase.AlignLeft),
            ('10%', [u'Выгруженно в рэмд'], CReportBase.AlignLeft),
            ('10%', [u'Полученно успешных'], CReportBase.AlignLeft)
        ]

        table = createTable(cursor, tableColumns, duplicateHeaderOnNewPage=False)

        self.data.sort(key=lambda item: item.setPerson)

        person = None
        action = 0

        for value in self.data:
            numberAction = 0
            numberFile = 0
            numberSugner = 0
            numberUnloadREMD = 0
            numberGoodPush = 0

            if value.person != person:
                person = value.person
                row = table.addRow()
                table.setText(row, 0, forceString(value.person))
                table.setText(row, 1, forceString(u"   "))
                table.setText(row, 2, forceString(u"   "))
                table.setText(row, 3, forceString(u"   "))
                table.setText(row, 4, forceString(u"   "))
                table.setText(row, 5, forceString(u"   "))

            if value.person == person and action != value.action_id:
                action = value.action_id
                # сколько действий
                numberAction = len([v for v in self.data if v.action_id == value.action_id])
                # сколько прикреплено прикреплено файлов
                numberFile = len([v for v in self.data if v.action_id == value.action_id and v.fileName])
                # сколько подписано врачом
                numberSugner = len([v for v in self.data if v.action_id == value.action_id and v.date_sign_ecp_person])
                # сколько выгружено в региональный РЭМД
                numberUnloadREMD = len([v for v in self.data if v.action_id == value.action_id and v.export_date])
                # Сколько полуено успешных уведослений из федерального РЭМД
                numberGoodPush = len(
                    [v for v in self.data if v.action_id == value.action_id and v.export_success == u'успех'])

                row = table.addRow()
                table.setText(row, 0, forceString(u"   "))
                table.setText(row, 1, forceString(numberAction))
                table.setText(row, 2, forceString(numberFile))
                table.setText(row, 3, forceString(numberSugner))
                table.setText(row, 4, forceString(numberUnloadREMD))
                table.setText(row, 5, forceString(numberGoodPush))

        return doc


class CActionFileAttachSortFilterProxyTableModel(CSortFilterProxyTableModel):


    def _parseDate(self, value):
        text = forceString(value).strip()
        if not text:
            return QDate()

        datePart = text.split(u'-')[0].strip()

        try:
            dt = datetime.datetime.strptime(datePart, '%d.%m.%Y').date()
            return QDate(dt.year, dt.month, dt.day)
        except ValueError:
            return QDate() 
        
        
    def lessThan(self, left, right):
        if left.column() == 3:
            leftKey = self._parseDate(left.data(Qt.DisplayRole))
            rightKey = self._parseDate(right.data(Qt.DisplayRole))
            return leftKey < rightKey

        return CSortFilterProxyTableModel.lessThan(self, left, right)
