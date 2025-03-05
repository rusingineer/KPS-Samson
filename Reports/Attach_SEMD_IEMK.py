# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2024 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

import re
from PyQt4 import QtGui
from PyQt4.QtCore import QDate, pyqtSignature, SIGNAL, Qt, QUrl
from PyQt4.QtGui import QColor, QBrush
from Events.EditDispatcher import getEventFormClass
from Exchange.PyServices import getPyServices, getCdaCode
from Reports.ReportBase import CReportBase, createTable
from Reports.ReportView import CPageFormat, CReportViewDialog
from Users.Rights import urCanOpenAnyAttachedFile, urCanOpenOwnAttachedFile
from Orgs.Utils import getOrgStructureDescendants
from Ui_Attach_SEMD_IEMK import Ui_Attach_SEMD_IEMK_Dialog
from library.DateEdit import CDateEdit
from library.DialogBase import CDialogBase
from library.InDocTable import CRecordListModel, CInDocTableCol
from library.SimpleProgressDialog import CSimpleProgressDialog
from library.Utils import forceString, toVariant, forceBool, anyToUnicode, forceInt, forceRef, forceDate, \
    formatNameInt, unformatSNILS, setPref, getPref, getPrefBool, getPrefString, forceDateTime
from F088.F088EditDialog import CF088EditDialog
from F088.F0882022EditDialog import CF0882022EditDialog
from Surveillance.SurveillanceDialog import CSurveillanceDialog
from Events.Utils import getActionTypeDescendants


class CAttach_SEMD_IEMK(CDialogBase, Ui_Attach_SEMD_IEMK_Dialog):
    def __init__(self, parent):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.listFilterIdentify = ""
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.addModels('ActionFileAttach', CActionFileAttachModel(self))
        self.setModels(self.tblActionFileAttach, self.modelActionFileAttach, self.selectionModelActionFileAttach)
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
        # self.chkFilterUploadedDocs.setChecked(True)
        self.btnFilterReset.clicked.connect(self.resetFilters)
        self.btnFilterApply.clicked.connect(self.applyFilters)
        self.selectionModelActionFileAttach.selectionChanged.connect(self.on_selectionModelFileAttach_currentRowChanged)
        self.btnOpenFile.setVisible(False)
        self.addObject('actPrintWindow', QtGui.QAction(u'Печать списка', self))
        self.addObject('actPrintSummaryDocuments', QtGui.QAction(u'Сводка по  документам', self))
        # self.addObject('actPrintGroupStrucPerson', QtGui.QAction(u'Группировка по подразделениям и врачам', self))
        # self.addObject('actPrintGroupPersonInfo', QtGui.QAction(u'Группировка по врачам с отображением количественных показателей', self))
        self.actPrintWindow.triggered.connect(self.on_actPrintWindow_triggered)
        self.actPrintSummaryDocuments.triggered.connect(self.on_actPrintSummaryDocuments_triggered)
        # self.actPrintGroupStrucPerson.triggered.connect(self.on_actPrintGroupStrucPerson_triggered)
        # self.actPrintGroupPersonInfo.triggered.connect(self.on_actPrintGroupPersonInfo_triggered)
        self.addObject('mnuPrint', QtGui.QMenu(self))
        self.mnuPrint.addAction(self.actPrintWindow)
        self.mnuPrint.addAction(self.actPrintSummaryDocuments)
        # self.mnuPrint.addAction(self.actPrintGroupStrucPerson)
        # self.mnuPrint.addAction(self.actPrintGroupPersonInfo)
        self.btnPrint.setMenu(self.mnuPrint)
        self.btnPrint.setShortcut('F6')
        self.cmbActionType.setClassesPopupVisible(True)
        self.cmbActionType.setClasses([0, 1, 2, 3])
        self.cmbActionType.setOrgStructure(None)
        # self.chkFilterSNILS.setEnabled(True)
        self.getDefaultParams()
        self.updateFilterIdentify()

        # if not QtGui.qApp.isAdmin():
        #     self.cmbFilterPerson.setValue(QtGui.qApp.userId)
        #     if not QtGui.qApp.userHasAnyRight([urAdmin, urCanSingOrgSertNoAdmin]):
        #         self.cmbFilterPerson.setEnabled(False)
        #     elif QtGui.qApp.userHasAnyRight([urAdmin, urCanSingOrgSertNoAdmin]):
        #         self.cmbFilterPerson.setEnabled(True)

        self.connect(self.tblActionFileAttach.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.sortByColumn)
        self.groupBoxFilters.setTitle(u'Фильтры по действиям')
        self.__sortColumn = None
        self.__sortAscending = False
        self.appPrefs = QtGui.qApp.preferences.appPrefs
        self.getPreferences()
        self.cols = ['id', 'master_id', 'comment', 'path', 'respSignatureBytes', 'respSigner_id', 'respSigningDatetime',
                     'orgSignatureBytes', 'orgSigner_id', 'orgSigningDatetime', 'respSigner_name']

        self.cmbFinance.setTable('rbFinance', True)
        self.cmbFinance.setValue(0)
        # self.cmbForPerson.setCurrentIndex(1)
        # self.on_cmbForPerson_currentIndexChanged(1)
        self.cmbSpeciality.setTable('rbSpeciality', True)

        self.edtFilterEventBegDate.setDate(QDate.currentDate())
        self.edtFilterEventEndDate.setDate(QDate.currentDate())

    def updateFilterIdentify(self, signal=False):
        self.cmbFilterIdentify.clear()
        doc = "'n3.medDocumentType.Cda'"

        db = QtGui.qApp.db
        stmt = u"""SELECT note, value, system_id as system, code FROM ActionType_Identification 
          LEFT JOIN rbAccountingSystem `as` ON ActionType_Identification.system_id = as.id
          WHERE as.code IN ({0})
          AND note != '' AND note IS not NULL and deleted = 0 group by note ORDER BY note """.format(doc)
        longest_word = ''

        list_auto_check = []
        x = 0

        if self.listFilterIdentify != "" and signal is False:
            lFilterIdentify = self.listFilterIdentify.replace(" ", "")
            lFilterIdentify = lFilterIdentify.split(',')

        query = db.query(stmt)
        while query.next():
            rec = query.record()
            value = forceString(rec.value('value'))
            name = forceString(rec.value('note'))

            self.cmbFilterIdentify.addItem("|" + value + "|" + name)
            if self.listFilterIdentify != "" and signal is False:
                if value in lFilterIdentify:
                    list_auto_check.append(x)
            else:
                list_auto_check.append(x)
            x += 1

            if len(forceString(rec.value('note'))) > len(longest_word):
                longest_word = forceString(rec.value('note'))

        self.cmbFilterIdentify._popupView._view.horizontalHeader().setDefaultSectionSize(20) # Изменяем ширину первого столбца
        self.cmbFilterIdentify.preferredWidth = (len(longest_word)) * 6 # Изменяем ширину второго столбца
        self.cmbFilterIdentify.setCheckedRows(list_auto_check)

    @pyqtSignature('int')
    def on_cmbTypeDoc_currentIndexChanged(self):
        self.updateFilterIdentify()

    def getModelAndTable(self):
        tbl = self.tblActionFileAttach
        model = self.modelActionFileAttach
        return tbl, model

    def getPreferences(self):
        # if forceBool(self.appPrefs.get('FileAttachSigned', 0)):
        #     self.cmbFilterSigned.setCurrentIndex(forceInt(self.appPrefs.get('FileAttachSigned', 0)))
        # if forceBool(self.appPrefs.get('FileAttachOrgStrChk', False)):
        #     self.chkFilterOrgStructure.setChecked(forceBool(self.appPrefs.get('FileAttachOrgStrChk', False)))
        # if forceBool(self.appPrefs.get('FileAttachOrgStrId')):
        #     self.cmbFilterOrgStructure.setValue(forceInt(self.appPrefs.get('FileAttachOrgStrId', '')))
        # if forceBool(self.appPrefs.get('FileAttachPersonId')) and QtGui.qApp.isAdmin():
        #     self.cmbFilterPerson.setValue(forceInt(self.appPrefs.get('FileAttachPersonId', '')))
        # if forceBool(self.appPrefs.get('FileAttachATChk', False)):
        #     self.chkFilterActionType.setChecked(forceBool(self.appPrefs.get('FileAttachATChk', False)))
        # if forceBool(self.appPrefs.get('FileAttachAT')):
        #     self.cmbActionType.setValue(forceInt(self.appPrefs.get('FileAttachAT', '')))
        self.applyFilters()

    def setPreferences(self):
        pass
        # signed = self.cmbFilterSigned.currentIndex()
        # orgStrId = self.cmbFilterOrgStructure.value() if self.chkFilterOrgStructure.isChecked() else ''
        # personId = self.cmbFilterPerson.value()
        # snilsCheck = self.chkFilterSNILS.isChecked()
        # actType = self.cmbActionType.value() if self.chkFilterActionType.isChecked() else ''
        # self.appPrefs['FileAttachSigned'] = toVariant(signed)
        # self.appPrefs['FileAttachOrgStrChk'] = toVariant(self.chkFilterOrgStructure.isChecked())
        # self.appPrefs['FileAttachOrgStrId'] = toVariant(orgStrId)
        # self.appPrefs['FileAttachPersonId'] = toVariant(personId)
        # self.appPrefs['FileAttachSNILS'] = toVariant(snilsCheck)
        # self.appPrefs['FileAttachATChk'] = toVariant(self.chkFilterActionType.isChecked())
        # self.appPrefs['FileAttachAT'] = toVariant(actType)

    def sortByColumn(self, column):
        tbl, model = self.getModelAndTable()
        header = tbl.horizontalHeader()
        if column == self.__sortColumn:
            self.__sortAscending = False if self.__sortAscending else True
        else:
            self.__sortColumn = column
            self.__sortAscending = True
        header.setSortIndicatorShown(True)
        header.setSortIndicator(column, Qt.AscendingOrder if self.__sortAscending else Qt.DescendingOrder)
        model.sortData(column, self.__sortAscending)

    @pyqtSignature('QModelIndex')
    def on_tblAttachFiles_clicked(self, index):
        self.rowCount()

    @pyqtSignature('QModelIndex, QModelIndex')
    def on_selectionModelFileAttach_currentRowChanged(self, current, previous):
        self.rowCount()

    def rowCount(self):
        tbl, model = self.getModelAndTable()

        rowCount = forceString(tbl.model().rowCount())
        selectedRows = tbl.selectedRowList()

        selectedRows = u', выделено: ' + forceString(len(selectedRows))
        self.lblCount.setText(u'Записей в списке: ' + rowCount + selectedRows)

    def contextMenuEvent(self, event):
        self.menu = QtGui.QMenu(self)
        tbl, model = self.getModelAndTable()
        selectedRows = self.getSelectedRows(tbl)
        currentRow = forceInt(tbl.currentRow())
        attachedFileId = forceInt(tbl.model().records[currentRow].value('afa_id'))
        if len(selectedRows) == 1:
            if attachedFileId != 0:
                openFile = QtGui.QAction(u'Открыть файл', self)
                openFile.triggered.connect(self.openAttachFile)
            actOpenEvent = QtGui.QAction(u'Открыть обращение', self)
            actOpenEvent.triggered.connect(self.on_actOpenEvent_triggered)

            if attachedFileId != 0:
                self.menu.addAction(openFile)
            self.menu.addAction(actOpenEvent)

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
        # self.cmbFilterPerson.setCurrentIndex(0)
        self.cmbActionType.setValue(None)
        self.cmbEventType.clearValue()
        # self.chkFilterSNILS.setEnabled(True)
        # self.chkFilterSNILS.setChecked(False)
        self.cmbFilterSigned.setCurrentIndex(0)
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
        # self.chkFilterActionNoFile.setChecked(False)
        # self.chkFilterUploadedDocs.setChecked(True)
        self.cmbFilterIdentify.setEnabled(False)
        self.cmbFilterIdentify.setCurrentIndex(0)
        self.cmbFilterIdentify.clearItemChecked()
        self.cmbFilterIdentify.setToolTip("")
        self.cmbSpeciality.clearItemChecked()
        self.cmbSpeciality.setToolTip("")
        self.cmbSpeciality.setEditText("")
        self.cmbFinance.setValue(0)
        # self.cmbForPerson.setCurrentIndex(1)
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
        tbl, model = self.getModelAndTable()
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
        actionNoFile = None
        typeDoc = None
        dateExecActionBegDate = None
        dateExecActionEndDate = None
        eventBegDate = None
        eventEndDate = None
        attachFileBegDate = None
        attachFileEndDate = None
        uploadedDocs = None

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

        actionType = self.cmbActionType.value()
        # forPerson = self.cmbForPerson.currentIndex()
        financeId = self.cmbFinance.value()
        specialityId = self.cmbSpeciality.value()
        if specialityId:
            specialityId = specialityId.split(',')

        identify = ", ".join(self.getListIdentify())

        eventType = self.cmbEventType.value()
        result['FilterIdentify'] = self.chkFilterIdentify.isChecked()
        result['listFilterIdentify'] = identify

        # actionNoFile = self.chkFilterActionNoFile.isChecked()
        actionNoFile = self.cmbFilterIsFile.currentIndex()
        actionNoFile = True if actionNoFile == 1 else False
        # uploadedDocs = self.chkFilterUploadedDocs.isChecked()
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
            model.sortData(4, True)
        else:
            model.sortData(self.__sortColumn, self.__sortAscending)
        self.setPreferences()

    def getListIdentify(self):
        listIdentify = []
        if self.chkFilterIdentify.isChecked():
            identify = self.cmbFilterIdentify.value()
            for i in re.split(' |\|', identify):
                if i.isdigit():
                    listIdentify.append(i)
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

    @pyqtSignature('int')
    def on_cmbFilterIsFile_currentIndexChanged(self, index):
        if index == 0:
            self.cmbFilterFileType.setEnabled(True)
        else:
            self.cmbFilterFileType.setEnabled(False)

    @pyqtSignature('int')
    def on_cmbFilterPerson_currentIndexChanged(self, index):
        if index == 0:
            self.chkFilterSNILS.setEnabled(False)
        else:
            self.chkFilterSNILS.setEnabled(True)

    @pyqtSignature('')
    def on_actPrintWindow_triggered(self):
        data = self.parseModel()
        html = self.createPageForPrintWindow(data)
        self.reportPage(html)

    @pyqtSignature('')
    def on_actPrintSummaryDocuments_triggered(self):
        dlg = CPrintSummaryDocumentsDialog(self)
        if dlg.exec_():
            parametrs = dlg.getParametrs()

            db = QtGui.qApp.db

            stmt = u"""
            SELECT DISTINCT
                CONCAT_WS(' ', p.lastName, p.firstName, p.patrName) AS person
              , CASE WHEN os.name IS NULL THEN 'Неизвестно' ELSE os.name end as orgStructure
              , COUNT(a.id) AS actionsSum
              , COUNT(ee.id) AS IEMK_Sum
              , COUNT(imS.id) AS successSum
              , COUNT(imF.id) AS failedSum
            FROM Action a
              INNER JOIN ActionType at ON a.actionType_id = at.id
              INNER JOIN rbAccountingSystem rbas ON rbas.urn = 'urn:oid:1.2.643.2.69.1.1.1.195.Cda'
              LEFT JOIN rbExternalSystem es ON es.code = 'N3.РЕГИСЗ.ИЭМК.v3'
              INNER JOIN ActionType_Identification ati ON at.id = ati.master_id AND ati.system_id = rbas.id
              INNER JOIN Person p ON p.id = CASE WHEN ati.value != '291' THEN a.person_id ELSE a.setPerson_id END
              INNER JOIN Event e ON a.event_id = e.id
              LEFT JOIN Event_Export ee ON e.id = ee.master_id AND ee.system_id = es.id AND ee.success = 1
              LEFT JOIN Action_FileAttach afa ON afa.master_id = a.id
              LEFT JOIN Information_Messages imS ON imS.IdMedDocumentMis_id = afa.id AND imS.typeMessages = 'REMDStatus' AND imS.status = 'Success' AND imS.IdFedRequest IS NOT NULL AND imS.RemdRegNumber != ''
              LEFT JOIN Information_Messages imF ON imF.IdMedDocumentMis_id = afa.id AND imF.typeMessages = 'REMDStatus' AND imF.status = 'Failed' AND imF.IdMedDocumentMis NOT IN (SELECT im.IdMedDocumentMis FROM Information_Messages im WHERE im.status = 'Success' AND im.IdFedRequest IS NOT NULL AND im.RemdRegNumber != '')
              LEFT JOIN OrgStructure os ON p.orgStructure_id = os.id
            WHERE 
              a.deleted = 0
              AND a.begDate >= '{0} 00:00' 
              AND a.endDate <= '{1} 00:00'
              {2}
            GROUP BY p.SNILS{3}
            ORDER BY {4}p.lastName, p.firstName, p.patrName;
            """.format(
                parametrs.get('edtDateStart').toString('yyyy-MM-dd'),
                parametrs.get('edtDateEnd').toString('yyyy-MM-dd'),
                'AND e.isClosed = 1' if parametrs.get('chkGroupByOrgStructure') else '',
                ', os.name' if parametrs.get('chkClosedEvents') else '',
                'os.name, ' if parametrs.get('chkClosedEvents') else ''
            )

            data = []
            query = db.query(stmt)
            while query.next():
                record = query.record()
                data.append(record)

            html = self.createPagePrintSummaryDocuments(data, parametrs.get('chkGroupByOrgStructure'))
            self.reportPage(html)

    # @pyqtSignature('')
    # def on_actPrintGroupStrucPerson_triggered(self):
    #     data = self.parseModel()
    #     html = self.createPageForPrintGroupStrucPerson(data)
    #     self.reportPage(html)

    # @pyqtSignature('')
    # def on_actPrintGroupPersonInfo_triggered(self):
    #     data = self.parseModel()
    #     html = self.createPageForPrintGroupPersonInfo(data)
    #     self.reportPage(html)

    def parseModel(self):
        tbl, model = self.getModelAndTable()
        listData = []
        items = model.items()
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
            data.statusREMD = forceString(item.value('statusREMD'))
            data.export_success = forceString(item.value('export_success'))
            listData.append(data)
        return listData

    def createPageForPrintWindow(self, data):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Печать списка')
        cursor.insertBlock()

        tableColumns = [
            ('3%',  [u'№'],                                                     CReportBase.AlignCenter),
            ('10%', [u'ФИО \nПациента'],                                        CReportBase.AlignLeft),
            ('3%',  [u'Код \nкарточки'],                                        CReportBase.AlignLeft),
            ('10%', [u'Тип \nсобытия'],                                         CReportBase.AlignLeft),
            ('10%', [u'Период \nобращения'],                                    CReportBase.AlignLeft),
            ('10%', [u'Тип \nдействия'],                                        CReportBase.AlignLeft),
            ('8%',  [u'Дата \nвыполнения \nдействия'],                          CReportBase.AlignLeft),
            ('8%',  [u'Дата \nприкрепления'],                                   CReportBase.AlignLeft),
            ('10%', [u'Назначил'],                                              CReportBase.AlignLeft),
            ('10%', [u'Врач'],                                                  CReportBase.AlignLeft),
            ('6%',  [u'Имя файла'],                                             CReportBase.AlignLeft),
            ('8%',  [u'Дата \nподписания \nЭЦП врача'],                         CReportBase.AlignLeft),
            ('8%',  [u'Дата \nподписания \nЭЦП МО'],                            CReportBase.AlignLeft),
            ('8%',  [u'Дата \nэкспорта'],                                       CReportBase.AlignLeft),
            ('10%', [u'Информация о \nприеме документа \nфедеральным РЭМД'],    CReportBase.AlignLeft),
            ('10%', [u'Отправка в \nРегиональный РЭМД'],                        CReportBase.AlignLeft),
        ]

        table = createTable(cursor, tableColumns)

        x = 0
        for value in data:
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
            table.setText(row, 14, forceString(value.statusREMD))
            table.setText(row, 15, forceString(value.export_success))

        return doc.toHtml()

    def createPagePrintSummaryDocuments(self, data, group):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Сводка по документам')
        cursor.insertBlock()

        tableColumns = [
            ('15%', [u'Врач'],                   CReportBase.AlignLeft),
            ('15%', [u'Введено действий'],       CReportBase.AlignLeft),
            ('20%', [u'Выгружено в ИЭМК'],       CReportBase.AlignLeft),
            ('15%', [u'Успешно принят РЭМД'],    CReportBase.AlignLeft),
            ('15%', [u'Отклонен РЭМД'],          CReportBase.AlignLeft),
            ('20%', [u'Статус РЭМД не получен'], CReportBase.AlignLeft),
        ]

        table = createTable(cursor, tableColumns)

        structure = None
        structureActionsSum = 0
        structureIEMK_Sum = 0
        structureSuccessSum = 0
        structureFailedSum = 0
        structureUnknownSum = 0

        boldChars = QtGui.QTextCharFormat()
        boldChars.setFontWeight(QtGui.QFont.Bold)

        for idx, record in enumerate(data):
            person = forceString(record.value('person'))
            actionsSum = forceInt(record.value('actionsSum'))
            IEMK_Sum = forceInt(record.value('IEMK_Sum'))
            successSum = forceInt(record.value('successSum'))
            failedSum = forceInt(record.value('failedSum'))
            unknownSum = IEMK_Sum - (successSum + failedSum)
            orgStructureRecord = forceString(record.value('orgStructure'))
            if successSum >= 500:
                textColor = Qt.green
            else:
                textColor = None
            if group:
                if orgStructureRecord != structure:
                    if idx != 0:
                        row = table.addRow()
                        table.setText(row, 0, structure, charFormat=boldChars)
                        table.setText(row, 1, structureActionsSum, charFormat=boldChars)
                        table.setText(row, 2, structureIEMK_Sum, charFormat=boldChars)
                        table.setText(row, 3, structureSuccessSum, charFormat=boldChars)
                        table.setText(row, 4, structureFailedSum, charFormat=boldChars)
                        table.setText(row, 5, structureUnknownSum, charFormat=boldChars)
                    structure = orgStructureRecord
                    structureActionsSum = 0
                    structureIEMK_Sum = 0
                    structureSuccessSum = 0
                    structureFailedSum = 0
                    structureUnknownSum = 0

            row = table.addRow()
            table.setText(row, 0, person, brushColor=textColor)
            table.setText(row, 1, actionsSum, brushColor=textColor)
            table.setText(row, 2, IEMK_Sum, brushColor=textColor)
            table.setText(row, 3, successSum, brushColor=textColor)
            table.setText(row, 4, failedSum, brushColor=textColor)
            table.setText(row, 5, unknownSum, brushColor=textColor)

            if group:
                structureActionsSum += actionsSum
                structureIEMK_Sum += IEMK_Sum
                structureSuccessSum += successSum
                structureFailedSum += failedSum
                structureUnknownSum += unknownSum

            if group and idx == len(data) - 1:
                row = table.addRow()
                table.setText(row, 0, structure, charFormat=boldChars)
                table.setText(row, 1, structureActionsSum, charFormat=boldChars)
                table.setText(row, 2, structureIEMK_Sum, charFormat=boldChars)
                table.setText(row, 3, structureSuccessSum, charFormat=boldChars)
                table.setText(row, 4, structureFailedSum, charFormat=boldChars)
                table.setText(row, 5, structureUnknownSum, charFormat=boldChars)

        return doc.toHtml()

    def createPageForPrintGroupStrucPerson(self, data):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Группировка по подразделениям и врачам')
        cursor.insertBlock()

        tableColumns = [
            ('15%', [u'Подразделение'],     CReportBase.AlignLeft),
            ('10%', [u'Врач'],              CReportBase.AlignLeft),
            ('15%', [u'ФИО Пациента'],      CReportBase.AlignLeft),
            ('10%', [u'Код карточки'],      CReportBase.AlignLeft),
            ('15%', [u'Тип события'],       CReportBase.AlignLeft),
            ('15%', [u'Период обращения'],  CReportBase.AlignLeft),
            ('20%', [u'Тип действия'],      CReportBase.AlignLeft),
        ]

        table = createTable(cursor, tableColumns)

        data.sort(key=lambda item: (item.structure, item.person))

        structure = None
        person = None

        for value in data:
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

        return doc.toHtml()

    def createPageForPrintGroupPersonInfo(self, data):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Группировка по врачам с отображением количественных показателей')
        cursor.insertBlock()

        tableColumns = [
            ('50%', [u'Врач'],                  CReportBase.AlignLeft),
            ('10%', [u'Действий'],              CReportBase.AlignLeft),
            ('10%', [u'Прикрепленно файлов'],   CReportBase.AlignLeft),
            ('10%', [u'Подписано врачем'],      CReportBase.AlignLeft),
            ('10%', [u'Выгруженно в рэмд'],     CReportBase.AlignLeft),
            ('10%', [u'Полученно успешных'],    CReportBase.AlignLeft)
        ]

        table = createTable(cursor, tableColumns)

        data.sort(key=lambda item: item.setPerson)

        person = None
        action = 0

        for value in data:
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
                numberAction = len([v for v in data if v.action_id == value.action_id])
                # сколько прикреплено прикреплено файлов
                numberFile = len([v for v in data if v.action_id == value.action_id and v.fileName])
                # сколько подписано врачом
                numberSugner = len([v for v in data if v.action_id == value.action_id and v.date_sign_ecp_person])
                # сколько выгружено в региональный РЭМД
                numberUnloadREMD = len([v for v in data if v.action_id == value.action_id and v.export_date])
                # Сколько полуено успешных уведослений из федерального РЭМД
                numberGoodPush = len([v for v in data if v.action_id == value.action_id and v.export_success == u'успех'])

                row = table.addRow()
                table.setText(row, 0, forceString(u"   "))
                table.setText(row, 1, forceString(numberAction))
                table.setText(row, 2, forceString(numberFile))
                table.setText(row, 3, forceString(numberSugner))
                table.setText(row, 4, forceString(numberUnloadREMD))
                table.setText(row, 5, forceString(numberGoodPush))

        return doc.toHtml()

    def reportPage(self, html):
        pageFormat = CPageFormat(pageSize=CPageFormat.A4,
                                 orientation=CPageFormat.Portrait,
                                 leftMargin=15,
                                 topMargin=15,
                                 rightMargin=15,
                                 bottomMargin=15)
        view = CReportViewDialog(self)
        view.setWindowTitle(u'Печать: Сводка о формировании СЭМД для РЭМД')
        if pageFormat:
            view.setPageFormat(pageFormat)
        view.setText(html)
        view.exec_()

    @pyqtSignature('')
    def on_actOpenEvent_triggered(self):
        QtGui.qApp.callWithWaitCursor(self, self.openEvent)

    @pyqtSignature('')
    def on_actOpenSurveillance_triggered(self):
        tbl, model = self.getModelAndTable()
        selectedRow = self.getSelectedRows(tbl)
        record = model.getRecordByRow(selectedRow[0])
        clientId = forceRef(record.value('client_id')) if record else None
        if clientId:
            try:
                surPlanningShow = CSurveillanceDialog(self, isFake=True)
                if surPlanningShow.surveillancePlanningShow(clientId):
                    tbl.setCurrentRow(selectedRow)
            finally:
                surPlanningShow.deleteLater()

    def openEvent(self):
        tbl, model = self.getModelAndTable()
        selectedRow = self.getSelectedRows(tbl)
        record = model.getRecordByRow(selectedRow[0])
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
        tbl, model = self.getModelAndTable()
        tbl.setReportHeader(reportHeader)
        return tbl.contentToHTML()

    def openAttachFile(self):
        interface = QtGui.qApp.webDAVInterface
        tbl, model = self.getModelAndTable()
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

    def validateFile(self):
        tbl, model = self.getModelAndTable()
        currentRows = tbl.selectedRowList()
        attachFilesIdList = self.modelActionFileAttach.getAttachFilesId(currentRows)

        db = QtGui.qApp.db
        interface = QtGui.qApp.webDAVInterface
        pyServices = getPyServices()
        results = {}

        if pyServices:
            availableCodes = pyServices.listCdaCodes()
            if availableCodes is not None:
                table = db.table('Action_FileAttach')
                cond = db.joinAnd([table['id'].inlist(attachFilesIdList), table['deleted'].eq(0)])
                cols = [table['id'], table['path']]
                records = db.getRecordList(table, cols, cond)
                countAll = len(records)

                def stepIterator(progressDialog):
                    for record in records:
                        id = forceRef(record.value('id'))
                        path = forceString(record.value('path'))
                        item = interface.createAttachedFileItem(path)
                        xmlText = interface.downloadBytes(item)
                        cdaCode = getCdaCode(xmlText)
                        if cdaCode is None or cdaCode not in availableCodes:
                            results[id] = CValidationResult(CValidationResult.UNAVAILABLE)
                        else:
                            jsonResult = pyServices.validateCda(xmlText)
                            results[id] = CValidationResult.fromJsonResult(jsonResult)
                        yield 1

                progressDialog = CSimpleProgressDialog(self)
                progressDialog.okButtonText = u"Проверить"
                progressDialog.setState(CSimpleProgressDialog.ReadyToWork)
                progressDialog.setMinimumWidth(500)
                progressDialog.setWindowTitle(u'Проверка документов по схематрону')
                progressDialog.setStepCount(countAll)
                progressDialog.setFormat(u'%v из %m')
                progressDialog.setAutoStart(False)
                progressDialog.setAutoClose(False)
                progressDialog.setStepIterator(stepIterator)
                try:
                    progressDialog.exec_()
                except Exception, e:
                    QtGui.QMessageBox.critical(self, u'Ошибка связи с сервисом валидации', anyToUnicode(e.message))
                if results:
                    countValidated = len(results)
                    self.modelActionFileAttach.updateValidationResults(results)
                    self.applyFilters()
                    QtGui.QMessageBox.information(self, u'Проверка документов по схематрону',
                                                  u'Проверено {0} из {1}'.format(countValidated, countAll))
            else:
                QtGui.QMessageBox.critical(self, u'Ошибка',
                                           u"На данном рабочем месте нет доступа к серверу сервисов по адресу: {0}".format(
                                               pyServices.url))
        self.gbValidationResult.setVisible(bool(self.modelActionFileAttach.validationResults))

    def setupValidationResultColors(self):
        self.setupValidationResultColor(CValidationResult.SUCCESS, self.chkValidationSuccess, QColor(200, 255, 200))
        self.setupValidationResultColor(CValidationResult.UNAVAILABLE, self.chkValidationUnavailable,
                                        QColor(255, 250, 200))
        self.setupValidationResultColor(CValidationResult.ERROR, self.chkValidationError, QColor(255, 200, 200))

    def setupValidationResultColor(self, resultCode, filterCheckbox, color):
        self.modelActionFileAttach.validationResultColors[resultCode] = color
        filterCheckbox.setStyleSheet("background-color: {0}".format(color.name()))


class CFileAttachModel(CRecordListModel):
    def getMasterId(self, index):
        return forceInt(self.records[index].value('master_id'))

    def getFileId(self, index):
        return forceInt(self.records[index].value('id'))

    def getRespSignerId(self, index):
        return forceString(self.records[index].value('isRespSigned')) == u'Подписан'

    def getAttachFilesId(self, indexList):
        idList = []
        for index in indexList:
            idList.append(forceInt(self.records[index].value('id')))
        return idList

    def updateValidationResults(self, newResults):
        for id, result in newResults.iteritems():
            self.validationResults[id] = result


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
        self.statusREMD = None
        self.export_success = None


class CPrintSummaryDocumentsDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        super(CPrintSummaryDocumentsDialog, self).__init__(parent)
        self.layout = QtGui.QGridLayout(self)

        self.setWindowTitle(u'Параметры отчёта')

        self.edtDateStart = CDateEdit()
        self.edtDateEnd = CDateEdit()
        self.chkGroupByOrgStructure = QtGui.QCheckBox(u'Группировать по подразделениям')
        self.chkClosedEvents = QtGui.QCheckBox(u'По закрытым событиям')

        self.buttonBox = QtGui.QDialogButtonBox()
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        self.connect(self.buttonBox, SIGNAL('accepted()'), self.accept)
        self.connect(self.buttonBox, SIGNAL('rejected()'), self.reject)

        self.layout.addWidget(QtGui.QLabel(u'Дата начала периода'), 0, 0)
        self.layout.addWidget(self.edtDateStart, 0, 1)

        self.layout.addWidget(QtGui.QLabel(u'Дата окончания периода'), 1, 0)
        self.layout.addWidget(self.edtDateEnd, 1, 1)

        self.layout.addWidget(self.chkGroupByOrgStructure, 2, 0)

        self.layout.addWidget(self.chkClosedEvents, 3, 0)

        self.layout.addWidget(self.buttonBox, 4, 0, 1, 2)

    def getParametrs(self):
        paramentrs = dict()
        paramentrs['edtDateStart'] = self.edtDateStart.date()
        paramentrs['edtDateEnd'] = self.edtDateEnd.date()
        paramentrs['chkGroupByOrgStructure'] = self.chkGroupByOrgStructure.isChecked()
        paramentrs['chkClosedEvents'] = self.chkClosedEvents.isChecked()
        return paramentrs


class CActionFileAttachModel(CFileAttachModel):
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
        self.addCol(CInDocTableCol(u'Имя файла', 'fileName', 40)).setReadOnly()
        self.addCol(CInDocTableCol(u'Дата \nподписания \nЭЦП врача', 'date_sign_ecp_person', 40)).setReadOnly()
        self.addCol(CInDocTableCol(u'Дата \nподписания \nЭЦП МО', 'date_sign_ecp_mo', 30)).setReadOnly()
        self.addCol(CInDocTableCol(u'Дата \nэкспорта', 'export_date', 30)).setReadOnly()
        self.addCol(CInDocTableCol(u'Информация о \nприеме документа \nфедеральным РЭМД', 'StatusREMD', 40)).setReadOnly()
        self.addCol(CInDocTableCol(u'Отправка в \nРегиональный РЭМД', 'export_success', 40)).setReadOnly()

        self.headerSortingCol = {0: True}
        self.records = None
        self.validationResults = {}
        self.validationResultColors = {}
        endDate = QDate().currentDate()
        begDate = QDate().currentDate().addDays(-2)
        self.loadData(begDate=begDate, endDate=endDate)

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
                 orgStructureList=None, personId=None, begDate=None, endDate=None, actionType=None,
                 identify=None, eventType=None, dateExecActionBegDate=None, dateExecActionEndDate=None,
                 eventBegDate=None, eventEndDate=None, attachFileBegDate=None, attachFileEndDate=None,
                 personSNILS=None, validationResultCodes=None, forPerson=0, specialityId=None,
                 financeId=None, actionNoFile=None, uploadedDocs=None):

        db = QtGui.qApp.db

        tableActionFileAttach = db.table('Action_FileAttach').alias('afa')
        tableAction = db.table('Action').alias('a')
        tableClient = db.table('Client')
        tableEvent = db.table('Event')
        tablePerson = db.table('Person')
        tablePersonOrgStructure = db.table('Person').alias('pOrgStructure')
        tableOrgStructure = db.table('OrgStructure').alias('os')
        tableActionType = db.table('ActionType').alias('AT')
        tableEventType = db.table('EventType')
        tableInformationMessages = db.table('Information_Messages').alias('IM')
        tableActionTypeIdentification = db.table('ActionType_Identification').alias('ati')
        tableActionFileAttachExport = db.table('Action_FileAttach_Export').alias('afe')
        tableAccountingSystem = db.table('rbAccountingSystem').alias('rbAS')

        # Общие колонки на вывод
        cols0 = [
            u"DISTINCT " + forceString(tableAction['id']),
            u"concat_ws(' ', " + forceString(tableActionType['name']) + u", 'от', DATE_FORMAT(a.endDate, '%d.%m.%Y')) as title",
            tableEvent['id'].alias('eventId'),
            tableEventType['name'].alias('event_type_name'),
            tablePersonOrgStructure['orgStructure_id'].alias('structure_id'),
            tableOrgStructure['name'].alias('structure'),
            u"concat_ws('|', " + forceString(tableActionType['code']) + u"," + forceString(tableActionType['name']) + u") AS action_type",
            u"concat_ws(' ', Client.`lastName`, Client.`firstName`, Client.`patrName`) AS fio_client",
            tableAction['endDate'].alias('actEndDate'),
            u"concat_ws(' - ', DATE_FORMAT(Event.setDate, '%d.%m.%Y'), DATE_FORMAT(Event.execDate, '%d.%m.%Y')) AS period",
            u"""(select concat_ws( '|', Person.`code`,  concat_ws(' ', Person.`lastName`, Person.`firstName`, Person.`patrName`))
                from Person where Person.id = a.`setPerson_id`) as setPerson""",

            u"""(select concat_ws( '|', Person.`code`, concat_ws(' ', Person.`lastName`, Person.`firstName`, Person.`patrName`))
                from Person where Person.id = CASE WHEN ati.value != '291' THEN a.person_id ELSE a.setPerson_id END) as person""",
        ]

        # Колонки первого запроса
        cols1 = [
            u"SUBSTRING_INDEX(afa.path, '/', -1 ) as fileName",
            tableActionFileAttach['id'].alias('afa_id'),
            tableActionFileAttach['respSigner_id'],
            tableActionFileAttach['respSigningDatetime'].alias('date_sign_ecp_person'),
            tableActionFileAttach['orgSigningDatetime'].alias('fileAttachDatetime'),
            tableActionFileAttachExport['dateTime'].alias('export_date'),
            tableActionFileAttachExport['note'],
            u"""case
            when IM.status = 'Success' then 'успех'
            when IM.status = 'Failed' then 'ошибка'
            end as export_success""",
            u"""case
            when IM.status = 'Success' and IM.Message <> '' AND IM.RemdRegNumber then CONCAT('Успех - ', IM.Message)
            when IM.status = 'Success' and IM.Message <> '' AND IM.RemdRegNumber = '' then 'Ожидается валидация документа на федеральном уровне'
            when IM.status = 'Failed' and IM.Message <> '' then CONCAT('Ошибка - ', IM.Message)
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
            u"NULL AS note",
            u"'Информация еще не получена' AS StatusREMD",
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
            tableAccountingSystem['code'].like(u'%n3.medDocumentType.%')
        ]

        cond1 = []

        cond2 = [
            u"""
            (SELECT MAX(afa.id) FROM Action_FileAttach afa
            left JOIN Action_FileAttach_Export afe ON
            afe.id = ( SELECT MAX(id) FROM Action_FileAttach_Export afae WHERE afa.id = afae.master_id)
            WHERE afa.master_id = a.id AND afa.deleted = 0) IS null"""
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

        # if forPerson == 0:
        #     pass
        #
        # elif forPerson == 1:  # Исполнитель
        #     tableQuery0 = tableQuery0.leftJoin(tablePerson, tablePerson['id'].eq(tableAction['person_id']))
        #
        #     if personId:
        #         cond0.append(tableAction['person_id'].eq(personId))
        #
        # elif forPerson == 2:  # Назначивший
        #     tableQuery0 = tableQuery0.leftJoin(tablePerson, tablePerson['id'].eq(tableAction['setPerson_id']))
        #
        #     if personId:
        #         cond0.append(tableAction['setPerson_id'].eq(personId))

        cond1 = cond0 + cond1
        cond2 = cond0 + cond2

        tableQuery1 = tableQuery0
        if uploadedDocs:
            tableQuery1 = tableQuery1.innerJoin(tableActionFileAttach,
            u"""
afa.id =(
    SELECT
        MAX(id)
    FROM
        Action_FileAttach afa
    WHERE
        afa.master_id = a.id
        AND afa.deleted = 0
        AND (
                ( right(SUBSTRING_INDEX(afa.path, '/', -1 ), 3) = "xml" 
                    AND RIGHT(rbAS.urn, 3)= "cda")
                OR ( right(SUBSTRING_INDEX(afa.path, '/', -1 ), 3) = "pdf" 
                    AND RIGHT(rbAS.urn, 3)= "pdf")
                OR ( right(SUBSTRING_INDEX(afa.path, '/', -1 ), 3) = "sms" 
                    AND RIGHT(rbAS.urn, 5)= "Vimis")
        )
    )
            """)
        else:
           tableQuery1 = tableQuery1.innerJoin(tableActionFileAttach,
           u"""
afa.id =(
   SELECT
       MAX(id)
   FROM
       Action_FileAttach afa
   WHERE
       afa.master_id = a.id
       AND afa.deleted = 0
       AND  ( right(SUBSTRING_INDEX(afa.path, '/', -1 ), 3) = "pdf" 
                   AND RIGHT(rbAS.urn, 3)= "pdf")
   )
           """)

        # tableQuery1 = tableQuery1.innerJoin(tableActionFileAttach,
        # u"""
        # afa.id =( SELECT MAX(id) FROM Action_FileAttach afa WHERE afa.master_id = a.id AND afa.deleted = 0
        # AND (( right(SUBSTRING_INDEX(afa.path, '/', -1 ), 3) = "xml" AND RIGHT(rbAS.urn, 3)= "cda")
        # OR ( right(SUBSTRING_INDEX(afa.path, '/', -1 ), 3) = "pdf" AND RIGHT(rbAS.urn, 3)= "pdf")
        # OR ( right(SUBSTRING_INDEX(afa.path, '/', -1 ), 3) = "sms" AND RIGHT(rbAS.urn, 5)= "Vimis")))
        # """)

        tableQuery1 = tableQuery1.leftJoin(tableActionFileAttachExport,
        u"""afe.id = (SELECT MAX(id) FROM Action_FileAttach_Export afae WHERE afa.id = afae.master_id)""")
        tableQuery1 = tableQuery1.leftJoin(tableInformationMessages,
        u"""
        IM.id = (
        SELECT MAX(Information_Messages.id) FROM Information_Messages WHERE
        typeMessages = 'REMDStatus'
        AND IdMedDocumentMis_id = afa.id
        AND (((status = 'Success' AND IdFedRequest IS NOT NULL ) OR (status = 'Failed'))
        OR (status = 'Success' AND IdFedRequest IS NOT NULL AND RemdRegNumber != '')))
        """)

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

        appendCond("""
            {0} in (
                SELECT
                    id
                FROM rbAccountingSystem `as`
                WHERE `as`.urn in (
                    'urn:oid:1.2.643.2.69.1.1.1.195.Cda', 
                    'urn:oid:1.2.643.2.69.1.1.1.195.Pdf', 
                    'urn:oid:1.2.643.2.69.1.1.1.195.Observa'))""".format(tableActionTypeIdentification['system_id']))

        # if specialityId and forPerson != 0:
        #     appendCond(tablePerson['speciality_id'].eq(specialityId))

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
            appendCond(tablePersonOrgStructure['orgStructure_id'].inlist(orgStructureList))

        if forceBool(personSNILS):
            appendCond(tablePerson['SNILS'].eq(personSNILS))

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
                    WHEN ati.value != '291' THEN (select SNILS from Person where a.person_id = id) = '{1}'
                                            ELSE (select SNILS from Person where a.setPerson_id = id) = '{1}'
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
            if not dateExecActionBegDate and not dateExecActionEndDate:
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
            appendCond(tableEventType['id'].inlist(eventType))

        if financeId:
            appendCond(tableAction['finance_id'].eq(financeId))
        # /\/\/\/\/\/\/\/\/\/\/\/\Filter/\/\/\/\/\/\/\/\/\/\/\

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


class CValidationResult:
    SUCCESS = 0
    UNAVAILABLE = 1
    ERROR = 2

    def __init__(self, code, errors=None):
        self.code = code
        self.errors = errors

    @classmethod
    def fromJsonResult(cls, jsonResult):
        if not jsonResult['schema_found']:
            return cls(CValidationResult.UNAVAILABLE)
        elif jsonResult['valid']:
            return cls(CValidationResult.SUCCESS)
        else:
            return cls(CValidationResult.ERROR, jsonResult['errors'])
