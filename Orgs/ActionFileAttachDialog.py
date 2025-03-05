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
import datetime
import os
import re

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QDate, pyqtSignature, SIGNAL, Qt, QDateTime, QUrl, QByteArray, QVariant
from PyQt4.QtSql import QSqlField
from PyQt4.QtGui import QColor, QBrush

from Events.EditDispatcher import getEventFormClass
from Exchange.PyServices import getPyServices, getCdaCode
from Reports.ReportView import CPageFormat, CReportViewDialog
from Users.Rights import urAdmin, urCanSingOrgSertNoAdmin, urCanOpenAnyAttachedFile, urCanOpenOwnAttachedFile, \
    urchangeSignDOC, urCanSignForOrganisation
from Utils import getOrgStructureDescendants, getPersonInfo
from Ui_ActionFileAttachDialog import Ui_ActionFileAttachDialog
from library.DialogBase import CDialogBase
from library.InDocTable import CRecordListModel, CInDocTableCol
from library.MSCAPI import MSCApi
from library.MSCAPI.certErrors import ECertNotFound
from library.SimpleProgressDialog import CSimpleProgressDialog
from library.Utils import forceString, toVariant, forceBool, anyToUnicode, forceInt, forceRef, forceDate, \
    exceptionToUnicode, formatNameInt, unformatSNILS, setPref, getPref, getPrefBool, getPrefString, getPrefInt
from F088.F088EditDialog import CF088EditDialog
from F088.F0882022EditDialog import CF0882022EditDialog
from Surveillance.SurveillanceDialog import CSurveillanceDialog

class CActionFileAttach(CDialogBase, Ui_ActionFileAttachDialog):
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
        self.addModels('ProphylaxisPlanningFileAttach', CProphylaxisPlanningFileAttachModel(self))
        self.setModels(self.tblProphylaxisPlanningFileAttach, self.modelProphylaxisPlanningFileAttach, self.selectionModelProphylaxisPlanningFileAttach)
        self.tblProphylaxisPlanningFileAttach.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tblProphylaxisPlanningFileAttach.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tblProphylaxisPlanningFileAttach.horizontalHeader().setStretchLastSection(True)
        self.addModels('EventFileAttach', CEventFileAttach(self))
        self.setModels(self.tblEventFileAttach, self.modelEventFileAttach, self.selectionModelEventFileAttach)
        self.tblEventFileAttach.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tblEventFileAttach.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tblEventFileAttach.horizontalHeader().setStretchLastSection(True)
        self.setupValidationResultColors()
        self.edtFilterLastName.setDisabled(True)
        self.edtFilterFirstName.setDisabled(True)
        self.edtFilterPatrName.setDisabled(True)
        self.edtFilterEventId.setDisabled(True)
        self.edtFilterBegDate.setDisabled(True)
        self.edtFilterEndDate.setDisabled(True)
        self.cmbUserCert.setDisabled(True)
        self.cmbPersonCert.setDisabled(True)
        self.chkUserCert.setEnabled(False)
        self.edtFilterDocumentBegDate.setDisabled(True)
        self.edtFilterDocumentEndDate.setDisabled(True)
        self.cmbFilterOrgStructure.setDisabled(True)
        self.edtFilterBegDate.setDate(QDate().currentDate().addDays(-2))
        self.edtFilterEndDate.setDate(QDate().currentDate())
        self.edtFilterDocumentBegDate.setDate(QDate().currentDate())
        self.edtFilterDocumentEndDate.setDate(QDate().currentDate())
        self.btnFilterReset.clicked.connect(self.resetFilters)
        self.btnFilterApply.clicked.connect(self.applyFilters)
        self.selectionModelActionFileAttach.selectionChanged.connect(self.on_selectionModelFileAttach_currentRowChanged)
        self.selectionModelProphylaxisPlanningFileAttach.selectionChanged.connect(self.on_selectionModelFileAttach_currentRowChanged)
        self.cmbUserCert.currentIndexChanged.connect(self.on_selectionCertForm_currentIndexChanged)
        self.btnOpenFile.setVisible(False)
        self.btnPrint.setShortcut('F6')
        self.gbValidationResult.setVisible(False)
        self.signs.setVisible(False)
        self.cmbActionType.setClassesPopupVisible(True)
        self.cmbActionType.setClasses([0, 1, 2, 3])
        self.cmbActionType.setOrgStructure(None)
        self.chkFilterSNILS.setEnabled(False)
        self.getDefaultParams()
        self.updateFilterIdentify()

        if not QtGui.qApp.isAdmin():
            self.cmbFilterPerson.setValue(QtGui.qApp.userId)
            if not QtGui.qApp.userHasAnyRight([urAdmin, urCanSingOrgSertNoAdmin]):
                self.cmbFilterPerson.setEnabled(False)
            elif QtGui.qApp.userHasAnyRight([urAdmin, urCanSingOrgSertNoAdmin]):
                self.cmbFilterPerson.setEnabled(True)

        self.signs.setVisible(True)
        # self.chkUserCertSha1.setChecked(forceBool(QtGui.qApp.preferences.appPrefs.get('attachFileDefaultCert', QVariant)))

        # if QtGui.qApp.userHasAnyRight([urAdmin, urCanSingOrgSertNoAdmin, urCanSignForOrganisation]):
        if QtGui.qApp.userHasAnyRight([urAdmin, urCanSingOrgSertNoAdmin]):
            self.btnSign.setEnabled(True)
            self.cmbSign.setEnabled(True)
        else:
            self.btnSign.setEnabled(False)
            self.cmbSign.setEnabled(False)

        self.connect(self.tblActionFileAttach.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.sortByColumn)
        self.connect(self.tblProphylaxisPlanningFileAttach.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.sortByColumn)
        self.tabWidget.currentChanged.connect(self.on_tabCertWidget_currentChanged)
        self.groupBoxFilters.setTitle(u'Фильтры по действиям')
        self.__sortColumn = None
        self.__sortAscending = False
        if forceBool(QtGui.qApp.preferences.appPrefs.get('csp', '')):  # and QtGui.qApp.userHasRight(urAdmin):
            self.setCsp()
        self.appPrefs = QtGui.qApp.preferences.appPrefs
        self.getPreferences()
        self.cols = ['id', 'master_id', 'comment', 'path', 'respSignatureBytes', 'respSigner_id', 'respSigningDatetime',
                     'orgSignatureBytes', 'orgSigner_id', 'orgSigningDatetime', 'respSigner_name']

    @pyqtSignature('int')
    def on_cmbTypeDoc_currentIndexChanged(self):
        self.updateFilterIdentify(True)

    def updateFilterIdentify(self, signal=False):
        self.cmbFilterIdentify.clear()
        doc = "'n3.medDocumentType.Pdf'"

        if self.chkFilterTypeDoc.isChecked():
            typeDoc = self.cmbTypeDoc.currentText()
            if typeDoc == "pdf":
                doc = "'n3.medDocumentType.Pdf'"
            elif typeDoc == "xml":
                doc = "'n3.medDocumentType.Cda'"
            elif typeDoc == "sms":
                doc = "'n3.medDocumentType.Observation'"

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

    # def updateFilterIdentify(self):
    #     self.cmbFilterIdentify.clear()
    #     doc = "'n3.medDocumentType.Pdf','n3.medDocumentType.Cda','n3.medDocumentType.Observation'"
    #
    #     if self.chkFilterTypeDoc.isChecked():
    #         typeDoc = self.cmbTypeDoc.currentText()
    #         if typeDoc == "pdf":
    #             doc = "'n3.medDocumentType.Pdf'"
    #         elif typeDoc == "xml":
    #             doc = "'n3.medDocumentType.Cda'"
    #         elif typeDoc == "sms":
    #             doc = "'n3.medDocumentType.Observation'"
    #     else:
    #         doc = "'n3.medDocumentType.Pdf','n3.medDocumentType.Cda','n3.medDocumentType.Observation'"
    #
    #     db = QtGui.qApp.db
    #     stmt = u"""SELECT note, value, system_id as system, code FROM ActionType_Identification
    #       LEFT JOIN rbAccountingSystem `as` ON ActionType_Identification.system_id = as.id
    #       WHERE as.code IN ({0})
    #       AND note != '' AND note IS not NULL and deleted = 0 group by note ORDER BY note """.format(doc)
    #     longest_word = ''
    #
    #     query = db.query(stmt)
    #     while query.next():
    #         rec = query.record()
    #         value = forceString(rec.value('value'))
    #         name = forceString(rec.value('note'))
    #
    #         self.cmbFilterIdentify.addItem("|" + value + "|" + name)
    #
    #         if len(forceString(rec.value('note'))) > len(longest_word):
    #             longest_word = forceString(rec.value('note'))
    #
    #     self.cmbFilterIdentify._popupView._view.horizontalHeader().setDefaultSectionSize(20) # Изменяем ширину первого столбца
    #     self.cmbFilterIdentify.preferredWidth = (len(longest_word)) * 6 # Изменяем ширину второго столбца


    def on_tabCertWidget_currentChanged(self, index):
        if index == 0:
            self.groupBoxFilters.setTitle(u'Фильтры по действиям')
            self.chkFilterActionType.setEnabled(True)
            self.chkFilterIdentify.setEnabled(True)
            self.chkUserCert.setEnabled(True)
            self.signs.setEnabled(True)
            self.chkNotSignaturePerson.setEnabled(True)
        elif index == 1:
            self.groupBoxFilters.setTitle(u'Фильтры по ККДН')
            self.chkFilterActionType.setEnabled(False)
            self.chkFilterIdentify.setEnabled(True)
            self.chkUserCert.setEnabled(False)
            self.signs.setEnabled(False)
            self.chkNotSignaturePerson.setEnabled(False)
        else:
            self.groupBoxFilters.setTitle(u'Фильтры по событиям')
            self.chkFilterActionType.setEnabled(False)
            self.chkFilterIdentify.setEnabled(False)
            self.chkUserCert.setEnabled(False)
            self.signs.setEnabled(False)
            self.chkNotSignaturePerson.setEnabled(False)
        self.rowCount()

    def getModelAndTable(self):
        tabIdx = self.tabWidget.currentIndex()
        if tabIdx == 0:
            tbl = self.tblActionFileAttach
            model = self.modelActionFileAttach
        elif tabIdx == 1:
            tbl = self.tblProphylaxisPlanningFileAttach
            model = self.modelProphylaxisPlanningFileAttach
        else:
            tbl = self.tblEventFileAttach
            model = self.modelEventFileAttach
        return tbl, model

    def getPreferences(self):
        if forceBool(self.appPrefs.get('FileAttachSigned', 0)):
            self.cmbFilterSigned.setCurrentIndex(forceInt(self.appPrefs.get('FileAttachSigned', 0)))
        if forceBool(self.appPrefs.get('FileAttachOrgStrChk', False)):
            self.chkFilterOrgStructure.setChecked(forceBool(self.appPrefs.get('FileAttachOrgStrChk', False)))
        if forceBool(self.appPrefs.get('FileAttachOrgStrId')):
            self.cmbFilterOrgStructure.setValue(forceInt(self.appPrefs.get('FileAttachOrgStrId', '')))
        if forceBool(self.appPrefs.get('FileAttachPersonId')) and QtGui.qApp.isAdmin():
            self.cmbFilterPerson.setValue(forceInt(self.appPrefs.get('FileAttachPersonId', '')))
        if forceBool(self.appPrefs.get('FileAttachSNILS', False)):
            self.chkFilterSNILS.setChecked(forceBool(self.appPrefs.get('FileAttachSNILS', False)))
        if forceBool(self.appPrefs.get('FileAttachATChk', False)):
            self.chkFilterActionType.setChecked(forceBool(self.appPrefs.get('FileAttachATChk', False)))
        if forceBool(self.appPrefs.get('FileAttachAT')):
            self.cmbActionType.setValue(forceInt(self.appPrefs.get('FileAttachAT', '')))
        if forceBool(self.appPrefs.get('FileAttachUserCertChk', False)):
            self.chkUserCert.setChecked(forceBool(self.appPrefs.get('FileAttachUserCertChk', False)))
        if forceBool(self.appPrefs.get('FileAttachUserCert')):
            self.cmbUserCert.setValue(forceInt(self.appPrefs.get('FileAttachUserCert', '')))
        if forceBool(self.appPrefs.get('FileAttachPersonCert')):
            self.cmbPersonCert.setValue(forceInt(self.appPrefs.get('FileAttachPersonCert', '')))
        self.applyFilters()

    def setPreferences(self):
        signed = self.cmbFilterSigned.currentIndex()
        orgStrId = self.cmbFilterOrgStructure.value() if self.chkFilterOrgStructure.isChecked() else ''
        personId = self.cmbFilterPerson.value()
        snilsCheck = self.chkFilterSNILS.isChecked()
        actType = self.cmbActionType.value() if self.chkFilterActionType.isChecked() else ''
        userCert = self.cmbUserCert.value() if self.chkUserCert.isChecked() else ''
        personCert = self.cmbPersonCert.value()
        self.appPrefs['FileAttachSigned'] = toVariant(signed)
        self.appPrefs['FileAttachOrgStrChk'] = toVariant(self.chkFilterOrgStructure.isChecked())
        self.appPrefs['FileAttachOrgStrId'] = toVariant(orgStrId)
        self.appPrefs['FileAttachPersonId'] = toVariant(personId)
        self.appPrefs['FileAttachSNILS'] = toVariant(snilsCheck)
        self.appPrefs['FileAttachATChk'] = toVariant(self.chkFilterActionType.isChecked())
        self.appPrefs['FileAttachAT'] = toVariant(actType)
        self.appPrefs['FileAttachUserCertChk'] = toVariant(self.chkUserCert.isChecked())
        self.appPrefs['FileAttachUserCert'] = toVariant(userCert)
        self.appPrefs['FileAttachPersonCert'] = toVariant(personCert)

    def on_selectionCertForm_currentIndexChanged(self):
        try:
            api = MSCApi(QtGui.qApp.getCsp())
            userCertSha1 = self.cmbUserCert.value()
            cert = api.findCertInStores(api.SNS_OWN_CERTIFICATES, sha1hex=userCertSha1)
            if cert and cert.snils():
                filtr = u"vrbPersonWithSpecialityAndPost.id in (SELECT id FROM Person p WHERE p.SNILS = '{0}')".format(cert.snils())
            else:
                filtr = ''
            self.cmbPersonCert.setFilter(filtr)
        except Exception, e:
            QtGui.QMessageBox.critical(self,
                                       u'Произошла ошибка',
                                       exceptionToUnicode(e),
                                       QtGui.QMessageBox.Close)

    def setCsp(self):
        csp = QtGui.qApp.getCsp()
        if csp:
            try:
                api = MSCApi(csp)
            except Exception, e:
                QtGui.QMessageBox.critical(self,
                                           u'Произошла ошибка подключения к криптопровайдеру',
                                           exceptionToUnicode(e),
                                           QtGui.QMessageBox.Close)
                api = None
        else:
            api = None
        self.cmbUserCert.setApi(api)
        if not api:
            self.chkUserCert.setEnabled(False)
        else:
            if QtGui.qApp.userHasAnyRight([urAdmin, urchangeSignDOC]):
                self.cmbUserCert.setStores(api.SNS_OWN_CERTIFICATES)
                if not self.cmbUserCert.stores:
                    self.cmbPersonCert.setEnabled(False)
                else:
                    self.cmbPersonCert.setEnabled(False)

            else:
                snils = forceString(QtGui.qApp.db.translate(QtGui.qApp.db.table('Person'), 'id', QtGui.qApp.userId, 'SNILS'))
                self.cmbUserCert.setStores(api.SNS_OWN_CERTIFICATES)
                checkDels = []
                for a in range(0, len(self.cmbUserCert) + 1):
                    cert = api.findCertInStores(api.SNS_OWN_CERTIFICATES,
                                                sha1hex=forceString(self.cmbUserCert.itemData(a)))
                    if cert:
                        if cert.snils() != snils:
                            checkDels.append(a)
                checkDels.reverse()
                for checkDel in checkDels:
                    self.cmbUserCert.removeItem(checkDel)
                if not self.cmbUserCert.stores:
                    self.cmbPersonCert.setEnabled(False)
                else:
                    self.cmbPersonCert.setEnabled(False)
            if len(self.cmbUserCert) > 0:
                checkDels = []
                for a in range(0, len(self.cmbUserCert) + 1):
                    findCert = api.findCertInStores(api.SNS_OWN_CERTIFICATES,
                                                    sha1hex=forceString(self.cmbUserCert.itemData(a)))
                    if findCert:
                        if findCert.notAfter() < datetime.datetime.now():
                            checkDels.append(a)
                checkDels.reverse()
                for checkDel in checkDels:
                    self.cmbUserCert.removeItem(checkDel)
            self.chkUserCert.setEnabled(True)
           # self.chkUserCert.setEnabled(QtGui.qApp.userHasRight(urRegTabExpertChangeSignVUT))

    @pyqtSignature('bool')
    def on_chkUserCert_toggled(self, value):
        self.cmbUserCert.setEnabled(value)
        if not len(self.cmbUserCert):
            self.cmbPersonCert.setEnabled(False)
        else:
            self.cmbPersonCert.setEnabled(value)
        self.applyFilters()

    @pyqtSignature('bool')
    def on_chkNotSignaturePerson_toggled(self, value):
        if value:
            self.chkUserCert.setChecked(False)

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

    @pyqtSignature('')
    def on_btnSign_clicked(self):
        index = self.cmbSign.currentIndex()
        self.signFileUserAndOrgCert(index=index)

    def rowCount(self):
        tbl, model = self.getModelAndTable()

        rowCount = forceString(tbl.model().rowCount())
        selectedRows = tbl.selectedRowList()
        if len(selectedRows) == 1:
            currentRows = tbl.selectedRowList()
            attachFilesIdList = model.getAttachFilesId(currentRows)
            db = QtGui.qApp.db
            if self.tabWidget.currentIndex() == 0:
                tableFA = db.table('Action_FileAttach')
                tableMaster = db.table('Action')
                tableFAS = db.table('Action_FileAttach_Signature')
            else:
                tableFA = db.table('ProphylaxisPlanning_FileAttach')
                tableMaster = db.table('ProphylaxisPlanning')
                tableFAS = db.table('ProphylaxisPlanning_FileAttach_Signature')
            query = tableFA.leftJoin(tableMaster, tableMaster['id'].eq(tableFA['master_id']))
            query = query.leftJoin(tableFAS, tableFA['id'].eq(tableFAS['master_id']))
            cond = db.joinAnd([tableFA['id'].inlist(attachFilesIdList),
                               tableFA['deleted'].eq(0),
                               tableFA['respSigner_id'].isNotNull()])
            records = db.getRecordList(query, ['*', tableFAS['modifyPerson_id'].alias('infoSigner')], cond)

            Signs_ = ''
            Signs_sub = ''
            infoRespSigner = None
            infoRespSign = None
            infoSign = None
            indexSign = 0
            for record in records:
                indexSign += 1
                if indexSign == 2:
                    Signs_ += '\n'
                    indexSign = 1
                infoRespSigner = forceString(record.value('respSigner_name'))
                infoSigner = getPersonInfo(forceString(record.value('infoSigner')))
                if infoSigner:
                    if forceString(record.value('signerTitle')):
                        subSign = forceString(record.value('signerTitle')).split(',')[0].split(" ") 
                        infoSign = subSign[0] + ' '
                        if len(subSign) >= 2: 
                            infoSign += subSign[1][:1] + '. '
                        if len(subSign) >= 3: # Может отсутствовать отчество
                            infoSign += subSign[2][:1] + '.'
                    else:
                        infoSign = u''
                    # Signs_ = Signs_ + forceDate(record.value('signingDatetime')).toString('dd.MM.yyyy') + ' ' + \
                    #          infoSigner['shortName'] + " " + infoSigner['postName'] + u" <b>ЭЦП</b> " + infoSign + '<br>'
                    Signs_sub = u' '.join([Signs_sub + unicode(forceDate(record.value('signingDatetime')).toString('dd.MM.yyyy')),
                                        infoSigner['shortName'], infoSigner['postName'],
                                        u'<b>ЭЦП</b>', infoSign, u'<br>'])
                if infoRespSigner:
                    #if len(infoRespSigner.split(',')) == 2: Зачем?
                    respFIO = infoRespSigner.split(',')[0]
                    subSign = respFIO.split(" ")
                    infoRespSign = subSign[0] + ' '
                    if len(subSign) >= 2: 
                        infoRespSign += subSign[1][:1] + '. '
                    if len(subSign) >= 3: # Может отсутствовать отчество
                        infoRespSign += subSign[2][:1] + '.'
                    if respFIO:
                        Signs_ = u'<b>ЭЦП исполнителя</b> - ' + forceDate(record.value('respSigningDatetime')).toString('dd.MM.yyyy') + ' ' + infoRespSign
                        if Signs_sub:
                            Signs_ += u'<br> <b>Подписал:</b> <br>' + Signs_sub
            if len(Signs_) > 1:
                self.signs.setVisible(True)
                self.signs.setHtml(Signs_)
            else:
                self.signs.setVisible(False)
                self.signs.setText(u'Файл не подписан врачом')
        else:
            self.signs.setText(u'')
        selectedRows = u', выделено: ' + forceString(len(selectedRows))
        self.lblCount.setText(u'Записей в списке: ' + rowCount + selectedRows)

    def contextMenuEvent(self, event):
        self.menu = QtGui.QMenu(self)
        signFileUserCert = QtGui.QAction(u'Подписать выбранный документ сертификатом врача', self)
        signFileOrgCert = QtGui.QAction(u'Подписать выбранный документ сертификатом МО', self)
        tbl, model = self.getModelAndTable()
        selectedRows = self.getSelectedRows(tbl)
        canSign = True
        typeDoc = self.cmbTypeDoc.currentText() if self.chkFilterTypeDoc.isChecked() else None
        enableValidation = (typeDoc == 'xml' and bool(self.getListIdentify()))
        if len(selectedRows) == 1:
            openFile = QtGui.QAction(u'Открыть файл', self)
            currentRow = forceInt(tbl.currentRow())
            openFile.triggered.connect(self.openAttachFile)
            tabIdx = self.tabWidget.currentIndex()
            if tabIdx == 0 or tabIdx == 2:
                actOpenEvent = QtGui.QAction(u'Открыть обращение', self)
                actOpenEvent.triggered.connect(self.on_actOpenEvent_triggered)
            else:
                actOpenEvent = QtGui.QAction(u'Открыть контрольную карту диспансерного наблюдения', self)
                actOpenEvent.triggered.connect(self.on_actOpenSurveillance_triggered)
            if model.getRespSignerId(currentRow) and self.chkUserCert.isChecked():
                signFileCurrentFormCert = QtGui.QAction(u'Подписать документ выбранным сертификатом', self)
                signFileCurrentFormCert.setEnabled(True)
                signFileCurrentFormCert.triggered.connect(self.signFileCurrentFormCert)
                self.menu.addAction(signFileCurrentFormCert)
            if enableValidation:
                validateFile = QtGui.QAction(u'Проверить выбранный документ по схематрону', self)
                validateFile.triggered.connect(self.validateFile)
                self.menu.addAction(validateFile)
            self.menu.addAction(openFile)
            self.menu.addAction(actOpenEvent)
        elif len(selectedRows) > 1:
            signFileUserCert = QtGui.QAction(u'Подписать выбранные документы сертификатом врача', self)
            signFileOrgCert = QtGui.QAction(u'Подписать выбранные документы сертификатом МО', self)

            if self.chkUserCert.isChecked():
                signFileCurrentFormCert = QtGui.QAction(u'Подписать документы выбранным сертификатом', self)
                signFileCurrentFormCert.setEnabled(True)
                signFileCurrentFormCert.triggered.connect(self.signFileCurrentFormCert)
                self.menu.addAction(signFileCurrentFormCert)
            if enableValidation:
                validateFile = QtGui.QAction(u'Проверить выбранные документы по схематрону', self)
                validateFile.triggered.connect(self.validateFile)
                self.menu.addAction(validateFile)

        signFileOrgCert.triggered.connect(self.signFileOrgCert)
        signFileUserCert.triggered.connect(self.signFileUserCert)
        self.menu.addAction(signFileUserCert)
        self.menu.addAction(signFileOrgCert)

        # ТТ 2269 "не доступно подписнаие ЭЦП в сервисе"
        # if QtGui.qApp.userHasAnyRight([urAdmin, urCanSingOrgSertNoAdmin, urCanSignForOrganisation]):
        #     signFileOrgCert.setEnabled(True and canSign)
        #     signFileUserCert.setEnabled(True)
        # else:
        #     signFileOrgCert.setEnabled(False)
        #     signFileUserCert.setEnabled(False)

        self.menu.popup(QtGui.QCursor.pos())

    def compareAllMembersSign(self, masterId):
        db = QtGui.qApp.db
        tableAP = db.table('ActionProperty')
        tableAPT = db.table('ActionPropertyType')
        tableAPP = db.table('ActionProperty_Person')

        query = tableAP.join(tableAPT, tableAPT['id'].eq(tableAP['type_id']))
        query = query.join(tableAPP, tableAPP['id'].eq(tableAP['id']))
        cond = [
            tableAP['deleted'].eq(0),
            tableAP['action_id'].eq(masterId)
        ]
        recordCountMembers = db.getRecordList(query, tableAP['id'].name(), cond)

        tableAFA = db.table('Action_FileAttach')
        tableAFAS = db.table('Action_FileAttach_Signature')
        query = tableAFA.join(tableAFAS, tableAFAS['master_id'].eq(tableAFA['id']))
        recordSignMembers = db.getRecordList(query, tableAFA['id'].name(), [tableAFA['master_id'].eq(masterId)])

        if len(recordCountMembers) == len(recordSignMembers):
            return True
        return False

    def signFileOrgCert(self):
        tabIdx = self.tabWidget.currentIndex()
        tbl, model = self.getModelAndTable()
        currentRows = tbl.selectedRowList()
        attachFilesIdList = model.getAttachFilesId(currentRows)

        db = QtGui.qApp.db
        interface = QtGui.qApp.webDAVInterface
        try:
            api = MSCApi(QtGui.qApp.getCsp())
            cert = QtGui.qApp.getOrgCert(api)
        except Exception, e:
            QtGui.QMessageBox.information(self, u'Ошибка получения сертификата', anyToUnicode(e.message),
                                          QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)
            return
        if tabIdx == 0:
            tableFA = db.table('Action_FileAttach')
        elif tabIdx == 1:
            tableFA = db.table('ProphylaxisPlanning_FileAttach')
        else:
            tableFA = db.table('Event_FileAttach')
        cols = [tableFA.tableName + '.%s' % col for col in self.cols]
        cond = db.joinAnd([tableFA['id'].inlist(attachFilesIdList),
                           tableFA['deleted'].eq(0),
                           tableFA['orgSigner_id'].isNull()])
        records = db.getRecordList(tableFA, cols, cond)

        # tableEvent = db.table('Event')
        # tableAction = db.table('Action')
        # table2 = tableAction.leftJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
        all = len(records)
        self.cnt = 0
        tempPath = QtGui.qApp.getTmpDir()
        errorList = []

        def stepIterator(progressDialog):
            for record in records:
                signOrg = True
                path = forceString(record.value('path'))
                item = interface.createAttachedFileItem(path)
                if tabIdx == 0:
                    actionId = forceRef(record.value('master_id'))
                    # if forceInt(record.value('isNeedAllMembersSign')) == 1:
                    #     signOrg = self.compareAllMembersSign(actionId)
                item.setRecord(record)
                localPath = os.path.join(tempPath, item.oldName)
                interface.downloadFile(item, localPath)
                tmpFile = QtCore.QFile(localPath)
                tmpFile.open(QtCore.QIODevice.ReadOnly)
                pdfBytes = tmpFile.readAll().data()
                tmpFile.close()
                tmpFile.remove()
                try:
                    if not forceBool(record.value('orgSigningDatetime')) and signOrg:
                        detachedSignatureBytes = cert.createDetachedSignature(pdfBytes)
                        item.setOrgSignature(detachedSignatureBytes,
                                             QtGui.qApp.userId,
                                             QDateTime.currentDateTime())
                        record = item.getRecord(tableFA)
                        db.updateRecord(tableFA, record)

                        # eventRecord = db.getRecordEx(table2, 'Event.*', tableAction['id'].eq(actionId))
                        # db.updateRecord(tableEvent, eventRecord)
                        self.cnt += 1
                except Exception, e:
                    # QtGui.QMessageBox.information(self, u'Ошибка подписания документа', anyToUnicode(e.message),
                    #                               QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)
                    errorList.append(anyToUnicode(e.message))
                    if u'Действие было отменено пользователем' in anyToUnicode(e.message):
                        break
                yield 1

        progressDialog = CSimpleProgressDialog(self)
        progressDialog.okButtonText = u"Подписать"
        progressDialog.setState(CSimpleProgressDialog.ReadyToWork)
        progressDialog.setMinimumWidth(500)
        progressDialog.setWindowTitle(u'Подписание документов сертификатом МО')
        progressDialog.setStepCount(all)
        progressDialog.setFormat(u'%v из %m')
        progressDialog.setAutoStart(False)
        progressDialog.setAutoClose(False)
        progressDialog.setStepIterator(stepIterator)
        progressDialog.exec_()
        self.applyFilters()
        QtGui.qApp.removeTmpDir(tempPath)
        if len(errorList):
            errorString = self.sortErrors(errorList)
            QtGui.QMessageBox.information(
                self,
                u'Ошибки подписания документов',
                errorString
            )
        QtGui.QMessageBox.information(
            self,
            u'Подписание документов МО!',
            u'Успешно подписано {0} из {1}'. format(self.cnt, all))


    def signFileCurrentFormCert(self):
        tbl, model = self.getModelAndTable()

        currentRows = tbl.selectedRowList()
        attachFilesIdList = self.modelActionFileAttach.getAttachFilesId(currentRows)

        db = QtGui.qApp.db
        interface = QtGui.qApp.webDAVInterface
        tabIdx = self.tabWidget.currentIndex()

        if tabIdx == 0:
            tableFA = db.table('Action_FileAttach')
            tableMaster = db.table('Action')
        elif tabIdx == 1:
            tableFA = db.table('ProphylaxisPlanning_FileAttach')
            tableMaster = db.table('ProphylaxisPlanning')
        else:
            tableFA = db.table('Event_FileAttach')
            tableMaster = db.table('Event')

        sign = None
        self.personSign = None
        if self.chkUserCert.isChecked():
            api = MSCApi(QtGui.qApp.getCsp())
            userCertSha1 = self.cmbUserCert.value()
            cert = api.findCertInStores(api.SNS_OWN_CERTIFICATES, sha1hex=userCertSha1)
            sign = cert.snils() if cert else None
            self.personSign = self.cmbPersonCert.value()

        errorList = []
        query = tableFA.leftJoin(tableMaster, tableMaster['id'].eq(tableFA['master_id']))
        cols = [tableFA.tableName + '.%s' % col for col in self.cols]
        cond = db.joinAnd([tableFA['id'].inlist(attachFilesIdList),
                           tableFA['deleted'].eq(0),
                           tableFA['respSigner_id'].isNotNull()])
        records = db.getRecordList(query, cols, cond)

        if self.personSign:
            cols = '*'
        elif tabIdx == 0:
            tableActionType = db.table('ActionType')
            query = query.leftJoin(tableActionType, tableActionType['id'].eq(tableMaster['actionType_id']))
            query = query.leftJoin(db.table('ActionPropertyType').alias('apt'),
                                   'ActionType.id = apt.actionType_id AND apt.typeName="Person" ')
            query = query.leftJoin(db.table('ActionProperty').alias('ap'),
                                   'Action.id = ap.action_id AND apt.id = ap.type_id ')
            query = query.leftJoin(db.table('ActionProperty_Person').alias('app'), 'ap.id = app.id ')
            query = query.leftJoin(db.table('Person'), 'app.value=Person.id ')

            cond += " and Person.SNILS = '%s' and app.id is not null" % sign
            cond += " and NOT EXISTS(SELECT 1 FROM Action_FileAttach_Signature afas WHERE afas.master_id = Action_FileAttach.id AND afas.signer_id=app.value)"

            cols = [tableFA['id'],
                    tableFA['createDatetime'],
                    tableFA['createPerson_id'],
                    tableFA['modifyPerson_id'],
                    tableFA['deleted'],
                    tableFA['master_id'],
                    tableFA['path'],
                    tableFA['respSignatureBytes'],
                    tableFA['respSigner_id'],
                    tableFA['respSigningDatetime'],
                    tableFA['orgSignatureBytes'],
                    tableFA['orgSigner_id'],
                    tableFA['orgSigningDatetime'],
                    db.table('Person')['id'].alias('sig')
                    ]

        records = db.getDistinctRecordList(query, cols, cond)

        _all = len(records) if records else 0
        self.cnt = 0
        tempPath = QtGui.qApp.getTmpDir()

        def stepIterator(progressDialog):
            tabIdx = self.tabWidget.currentIndex()
            for record in records:
                if tabIdx != 2:
                    personIdColName = 'person_id'
                else:
                    personIdColName = 'execPerson_id'
                cert = None
                tableAction = db.table('Action')
                masterId = forceString(record.value('master_id'))
                if tabIdx == 0:
                    tableAFAPT = db.table('Action_FileAttach_PrintTemplate')
                    tableAFA = db.table('Action_FileAttach')
                    tablePT = db.table('rbPrintTemplate')
                    table = tableAFAPT.leftJoin(tablePT, tablePT['id'].eq(tableAFAPT['template_id']))
                    table = table.leftJoin(tableAFA, tableAFA['id'].eq(tableAFAPT['id']))
                    recordSigner = db.getRecordEx(table, tablePT['requireSignerPerson'],
                                                  [tableAFA['master_id'].eq(masterId),
                                                   tablePT['deleted'].eq(0)])
                    if recordSigner:
                        if forceInt(recordSigner.value('requireSignerPerson')) == 1:
                            personIdColName = 'setPerson_id'
                personId = db.getRecordEx(tableAction, tableAction[personIdColName], tableAction['id'].eq(masterId))
                personId = forceString(personId.value(personIdColName))

                if self.personSign is None:
                    self.personSign = forceString(record.value('sig'))

                try:
                    if self.chkUserCert.isChecked():
                        api = MSCApi(QtGui.qApp.getCsp())
                        now = QDateTime.currentDateTime().toPyDateTime()
                        userCertSha1 = self.cmbUserCert.value()
                        cert = api.findCertInStores(api.SNS_OWN_CERTIFICATES, sha1hex=userCertSha1)
                        if not QtGui.qApp.getAllowUnsignedAttachments() and not cert:
                            raise ECertNotFound(u'Не удалось найти сертификат пользователя с отпечатком sha1 %s' % userCertSha1)
                        if not QtGui.qApp.getAllowUnsignedAttachments() and not cert.notBefore() <= now <= cert.notAfter():
                            raise ECertNotFound(u'Сертификат пользователя с отпечатком sha1 %s найден, но сейчас не действителен' % userCertSha1)
                    else:
                        if QtGui.qApp.getAllowUnsignedAttachments():
                            try:
                                api = MSCApi(QtGui.qApp.getCsp())
                                cert = QtGui.qApp.getUserCertForAdmin(api, personId)
                            except:
                                cert = None
                        else:
                            api = MSCApi(QtGui.qApp.getCsp())
                            cert = QtGui.qApp.getUserCertForAdmin(api, personId)
                except Exception, e:
                    errorList.append(anyToUnicode(e.message))
                    yield 1

                if cert:
                    path = forceString(record.value('path'))
                    item = interface.createAttachedFileItem(path)
                    actionId = forceRef(record.value('master_id'))
                    item.setRecord(record)
                    localPath = os.path.join(tempPath, item.oldName)
                    interface.downloadFile(item, localPath)
                    tmpFile = QtCore.QFile(localPath)
                    tmpFile.open(QtCore.QIODevice.ReadOnly)
                    pdfBytes = tmpFile.readAll().data()
                    tmpFile.close()
                    tmpFile.remove()
                    try:
                        # if not forceDate(record.value('respSigningDatetime')):
                        if forceDate(record.value('respSigningDatetime')):
                            detachedSignatureBytes = cert.createDetachedSignature(pdfBytes)
                            item.setRespSignature(detachedSignatureBytes,
                                                  personId,
                                                  QDateTime.currentDateTime())
                            record = item.getRecord(tableFA)

                            # db.updateRecord(tableName, record) # Абаджян
                            tableAFAS = db.table('Action_FileAttach_Signature')
                            record = tableAFAS.newRecord()
                            record.setValue('createDatetime', item.respSignature.signingDatetime)
                            record.setValue('createPerson_id', QtGui.qApp.userId)
                            record.setValue('modifyDatetime', toVariant(item.respSignature.signingDatetime))
                            record.setValue('modifyPerson_id', QtGui.qApp.userId)
                            record.setValue('master_id', toVariant(item.id))
                            record.setValue('signatureBytes', QByteArray(item.respSignature.signatureBytes))
                            record.setValue('signer_id', toVariant(self.personSign))
                            record.setValue('signingDatetime', toVariant(item.respSignature.signingDatetime))
                            certName = cert.surName() + ' ' + cert.givenName() + ', ' + cert.snils()
                            record.setValue('signerTitle', toVariant(certName))

                            # availabilityPersonSign = db.getRecordEx(tableSign, 'signer_id', u'master_id = %s and signer_id = %s ' % (item.id, self.personSign))

                            # if not availabilityPersonSign and personId != str(self.personSign):
                            #     db.insertRecord(tableSign, record)
                            #     self.cnt += 1
                            db.insertRecord(tableAFAS, record)
                            self.cnt += 1

                    except Exception, e:
                        QtGui.QMessageBox.information(self, u'Ошибка подписания документа', anyToUnicode(e.message),
                                                      QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)
                    yield 1

        progressDialog = CSimpleProgressDialog(self)
        progressDialog.okButtonText = u"Подписать"
        progressDialog.setState(CSimpleProgressDialog.ReadyToWork)
        progressDialog.setMinimumWidth(500)
        progressDialog.setWindowTitle(u'Подписание документов сертификатом врача')
        progressDialog.setStepCount(_all)
        progressDialog.setFormat(u'%v из %m')
        progressDialog.setAutoStart(False)
        progressDialog.setAutoClose(False)
        progressDialog.setStepIterator(stepIterator)
        progressDialog.exec_()
        QtGui.qApp.removeTmpDir(tempPath)
        self.applyFilters()
        if len(errorList):
            errorString = self.sortErrors(errorList)
            QtGui.QMessageBox.information(
                self,
                u'Ошибки получения сертификата',
                errorString
            )
        QtGui.QMessageBox.information(
            self,
            u'Подписание документов МО!',
            u'Успешно подписано {0} из {1}'.format(self.cnt, _all))


    def signFileUserCert(self):
        tabIdx = self.tabWidget.currentIndex()
        tbl, model = self.getModelAndTable()
        currentRows = tbl.selectedRowList()
        attachFilesIdList = model.getAttachFilesId(currentRows)

        db = QtGui.qApp.db
        interface = QtGui.qApp.webDAVInterface

        if tabIdx == 0:
            tableFA = db.table('Action_FileAttach')
            tableMaster = db.table('Action')
        elif tabIdx == 1:
            tableFA = db.table('ProphylaxisPlanning_FileAttach')
            tableMaster = db.table('ProphylaxisPlanning')
        else:
            tableFA = db.table('Event_FileAttach')
            tableMaster = db.table('Event')

        if QtGui.qApp.userHasAnyRight([urAdmin, urCanSingOrgSertNoAdmin, urCanSignForOrganisation]):
            errorList = []

            query = tableFA.leftJoin(tableMaster, tableMaster['id'].eq(tableFA['master_id']))
            cols = [tableFA.tableName + '.%s' % col for col in self.cols]
            cond = db.joinAnd([
                tableFA['id'].inlist(attachFilesIdList),
                tableFA['deleted'].eq(0),
                tableFA['respSigner_id'].isNull()])
            records = db.getRecordList(query, cols, cond)

            tableEvent = db.table('Event')
            # table2 = tableMaster.leftJoin(tableEvent, tableEvent['id'].eq(tableMaster['event_id']))
            all = len(records)
            self.cnt = 0
            tempPath = QtGui.qApp.getTmpDir()

            def stepIterator(progressDialog):
                tabIdx = self.tabWidget.currentIndex()
                for record in records:
                    if tabIdx != 2:
                        personIdColName = 'person_id'
                    else:
                        personIdColName = 'execPerson_id'
                    cert = None
                    masterId = forceString(record.value('master_id'))
                    if tabIdx == 0:
                        tableAFAPT = db.table('Action_FileAttach_PrintTemplate')
                        tableAFA = db.table('Action_FileAttach')
                        tablePT = db.table('rbPrintTemplate')
                        table = tableAFAPT.leftJoin(tablePT, tablePT['id'].eq(tableAFAPT['template_id']))
                        table = table.leftJoin(tableAFA, tableAFA['id'].eq(tableAFAPT['id']))
                        recordSigner = db.getRecordEx(table, tablePT['requireSignerPerson'],
                                                      [tableAFA['master_id'].eq(masterId),
                                                       tablePT['deleted'].eq(0)])
                        if recordSigner:
                            if forceInt(recordSigner.value('requireSignerPerson')) == 1:
                                personIdColName = 'setPerson_id'
                    personId = db.getRecordEx(tableMaster, tableMaster[personIdColName], tableMaster['id'].eq(masterId))
                    personId = forceString(personId.value(personIdColName))

                    try:
                        if QtGui.qApp.getAllowUnsignedAttachments():
                            try:
                                api = MSCApi(QtGui.qApp.getCsp())
                                cert = QtGui.qApp.getUserCertForAdmin(api, personId)
                            except:
                                cert = None
                        else:
                            api = MSCApi(QtGui.qApp.getCsp())
                            cert = QtGui.qApp.getUserCertForAdmin(api, personId)
                    except Exception, e:
                        errorList.append(anyToUnicode(e.message))
                        yield 1
                    if cert:
                        path = forceString(record.value('path'))
                        item = interface.createAttachedFileItem(path)
                        masterId = forceRef(record.value('master_id'))
                        item.setRecord(record)
                        localPath = os.path.join(tempPath, item.oldName)
                        interface.downloadFile(item, localPath)
                        tmpFile = QtCore.QFile(localPath)
                        tmpFile.open(QtCore.QIODevice.ReadOnly)
                        pdfBytes = tmpFile.readAll().data()
                        tmpFile.close()
                        tmpFile.remove()
                        certName = cert.surName() + ' ' + cert.givenName() + ', ' + cert.snils()
                        record.setValue('respSigner_name', toVariant(certName))
                        try:
                            if not forceDate(record.value('respSigningDatetime')):
                                detachedSignatureBytes = cert.createDetachedSignature(pdfBytes)
                                item.setRespSignature(detachedSignatureBytes,
                                                      personId,
                                                      QDateTime.currentDateTime())
                                record = item.getRecord(tableFA)
                                db.updateRecord(tableFA, record)
                                # eventRecord = db.getRecordEx(table2, 'Event.*', tableAction['id'].eq(actionId))
                                # db.updateRecord(tableEvent, eventRecord)
                                self.cnt += 1
                        except Exception, e:
                            QtGui.QMessageBox.information(self, u'Ошибка подписания документа', anyToUnicode(e.message),
                                                          QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)
                        yield 1

            progressDialog = CSimpleProgressDialog(self)
            progressDialog.okButtonText = u"Подписать"
            progressDialog.setState(CSimpleProgressDialog.ReadyToWork)
            progressDialog.setMinimumWidth(500)
            progressDialog.setWindowTitle(u'Подписание документов сертификатом врача')
            progressDialog.setStepCount(all)
            progressDialog.setFormat(u'%v из %m')
            progressDialog.setAutoStart(False)
            progressDialog.setAutoClose(False)
            progressDialog.setStepIterator(stepIterator)
            progressDialog.exec_()
            self.applyFilters()
            QtGui.qApp.removeTmpDir(tempPath)
            if errorList:
                errorString = self.sortErrors(errorList)
                QtGui.QMessageBox.information(self, u'Ошибки получения сертификата',errorString)
            else:
                QtGui.QMessageBox.information(self,
                                              u'Подписание документов МО!',
                                              u'Успешно подписано {0} из {1}'.format(self.cnt, all))
        else:
            try:
                api = MSCApi(QtGui.qApp.getCsp())
                cert = QtGui.qApp.getUserCert(api)
            except Exception, e:
                QtGui.QMessageBox.information(self,
                                              u'Ошибка получения сертификата',
                                              anyToUnicode(e.message),
                                              QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)
                return
            errorList = []
            cond = db.joinAnd([tableFA['id'].inlist(attachFilesIdList),
                               tableFA['deleted'].eq(0),
                               tableFA['respSigner_id'].isNull()])
            records = db.getRecordList(tableFA, '*', cond)

            # tableEvent = db.table('Event')
            # tableAction = db.table('Action')
            # table2 = tableAction.leftJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
            all = len(records)
            self.cnt = 0
            tempPath = QtGui.qApp.getTmpDir()

            def stepIterator(progressDialog):
                for record in records:
                    path = forceString(record.value('path'))
                    item = interface.createAttachedFileItem(path)
                    masterId = forceRef(record.value('master_id'))
                    item.setRecord(record)
                    localPath = os.path.join(tempPath, item.oldName)
                    interface.downloadFile(item, localPath)
                    tmpFile = QtCore.QFile(localPath)
                    tmpFile.open(QtCore.QIODevice.ReadOnly)
                    pdfBytes = tmpFile.readAll().data()
                    tmpFile.close()
                    tmpFile.remove()
                    certName = cert.surName() + ' ' + cert.givenName() + ', ' + cert.snils()
                    record.setValue('respSigner_name', toVariant(certName))
                    try:
                        if not forceDate(record.value('respSigningDatetime')):
                            detachedSignatureBytes = cert.createDetachedSignature(pdfBytes)
                            item.setRespSignature(detachedSignatureBytes,
                                                  QtGui.qApp.userId,
                                                  QDateTime.currentDateTime())
                            record = item.getRecord(tableFA)
                            db.updateRecord(tableFA, record)

                            # eventRecord = db.getRecordEx(table2, 'Event.*', tableAction['id'].eq(actionId))
                            # db.updateRecord(tableEvent, eventRecord)
                            self.cnt += 1
                    except Exception, e:
                        # QtGui.QMessageBox.information(self, u'Ошибка подписания документа', anyToUnicode(e.message),
                        #                               QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)
                        errorList.append(anyToUnicode(e.message))
                        if u'Действие было отменено пользователем' in anyToUnicode(e.message):
                            break
                    yield 1

            progressDialog = CSimpleProgressDialog(self)
            progressDialog.okButtonText = u"Подписать"
            progressDialog.setState(CSimpleProgressDialog.ReadyToWork)
            progressDialog.setMinimumWidth(500)
            progressDialog.setWindowTitle(u'Подписание документов сертификатом врача')
            progressDialog.setStepCount(all)
            progressDialog.setFormat(u'%v из %m')
            progressDialog.setAutoStart(False)
            progressDialog.setAutoClose(False)
            progressDialog.setStepIterator(stepIterator)
            progressDialog.exec_()
            self.applyFilters()
            QtGui.qApp.removeTmpDir(tempPath)
            if len(errorList):
                errorString = self.sortErrors(errorList)
                QtGui.QMessageBox.information(
                    self,
                    u'Ошибки подписания документов',
                    errorString
                )
            QtGui.QMessageBox.information(
                self,
                u'Подписание документов МО!',
                u'Успешно подписано {0} из {1}'. format(self.cnt, all))

    def signFileUserAndOrgCert(self, index):
        tabIdx = self.tabWidget.currentIndex()
        tbl, model = self.getModelAndTable()

        if index == 0:
            currentRows = tbl.selectedRowList()
            attachFilesIdList = model.getAttachFilesId(currentRows)
        else:
            attachFilesIdList = []
            items = model.items()
            for item in items:
                attachFilesIdList.append(forceInt(item.value('id')))

        db = QtGui.qApp.db
        interface = QtGui.qApp.webDAVInterface

        if QtGui.qApp.userHasAnyRight([urAdmin, urCanSingOrgSertNoAdmin, urCanSignForOrganisation]):
            errorList = []
            try:
                api = MSCApi(QtGui.qApp.getCsp())
                certOrg = QtGui.qApp.getOrgCert(api)
            except Exception, e:
                errorList.append(anyToUnicode(e.message) + u'\n')
                certOrg = None

            if tabIdx == 0:
                tableFA = db.table('Action_FileAttach')
                tableMaster = db.table('Action')
            elif tabIdx == 1:
                tableFA = db.table('ProphylaxisPlanning_FileAttach')
                tableMaster = db.table('ProphylaxisPlanning')
            else:
                tableFA = db.table('Event_FileAttach')
                tableMaster = db.table('Event')
            cols = [tableFA.tableName + '.%s' % col for col in self.cols]
            if index == 0:
                cond = db.joinAnd([tableFA['id'].inlist(attachFilesIdList), tableFA['deleted'].eq(0),
                                   tableFA['respSigner_id'].isNull() + ' OR ' + tableFA['orgSigner_id'].isNull()])
            else:
                cond = db.joinAnd([tableFA['id'].inlist(attachFilesIdList), tableFA['deleted'].eq(0),
                                   tableFA['respSigner_id'].isNull() + ' OR ' + tableFA['orgSigner_id'].isNull()])
            records = db.getRecordList(tableFA, cols, cond)

            all = len(records)
            self.cnt = 0
            tempPath = QtGui.qApp.getTmpDir()

            def stepIterator(progressDialog):
                tabIdx = self.tabWidget.currentIndex()
                for record in records:
                    if tabIdx != 2:
                        personIdColName = 'person_id'
                    else:
                        personIdColName = 'execPerson_id'
                    masterId = forceString(record.value('master_id'))
                    if tabIdx == 0:
                        tableAFAPT = db.table('Action_FileAttach_PrintTemplate')
                        tableAFA = db.table('Action_FileAttach')
                        tablePT = db.table('rbPrintTemplate')
                        table = tableAFAPT.leftJoin(tablePT, tablePT['id'].eq(tableAFAPT['template_id']))
                        table = table.leftJoin(tableAFA, tableAFA['id'].eq(tableAFAPT['id']))
                        recordSigner = db.getRecordEx(table, tablePT['requireSignerPerson'],
                                                      [tableAFA['master_id'].eq(masterId),
                                                       tablePT['deleted'].eq(0)])
                        if recordSigner:
                            if forceInt(recordSigner.value('requireSignerPerson')) == 1:
                                personIdColName = 'setPerson_id'
                    personId = db.getRecordEx(tableMaster, tableMaster[personIdColName], tableMaster['id'].eq(masterId))
                    personId = forceString(personId.value(personIdColName))
                    certUser = None

                    if QtGui.qApp.getAllowUnsignedAttachments():
                        try:
                            api = MSCApi(QtGui.qApp.getCsp())
                            certUser = QtGui.qApp.getUserCertForAdmin(api, personId)
                        except Exception, e:
                            errorList.append(anyToUnicode(e.message))
                    else:
                        try:
                            api = MSCApi(QtGui.qApp.getCsp())
                            certUser = QtGui.qApp.getUserCertForAdmin(api, personId)
                        except Exception, e:
                            errorList.append(anyToUnicode(e.message))
                            yield 1

                    path = forceString(record.value('path'))
                    item = interface.createAttachedFileItem(path)
                    item.setRecord(record)
                    localPath = os.path.join(tempPath, item.oldName)
                    try:
                        interface.downloadFile(item, localPath)
                    except Exception, e:
                        errorList.append(anyToUnicode(e.message))
                        yield 1
                    tmpFile = QtCore.QFile(localPath)
                    tmpFile.open(QtCore.QIODevice.ReadOnly)
                    pdfBytes = tmpFile.readAll().data()
                    tmpFile.close()
                    tmpFile.remove()
                    certName = certUser.surName() + '' + certUser.givenName() + ', ' + certUser.snils() if certUser else None
                    record.setValue('respSigner_name', toVariant(certName))
                    try:
                        hasRespDate = forceDate(record.value('respSigningDatetime'))
                        hasOrgDate = forceDate(record.value('orgSigningDatetime'))
                        if not hasRespDate:
                            if record.value('respSigner_id') and certUser:
                                detachedSignatureBytesUser = certUser.createDetachedSignature(pdfBytes)
                                item.setRespSignature(detachedSignatureBytesUser,
                                                      personId,
                                                      QDateTime.currentDateTime())
                        if not hasOrgDate:
                            if record.value('orgSigner_id') and certOrg and QtGui.qApp.userHasAnyRight([urAdmin, urCanSingOrgSertNoAdmin, urCanSignForOrganisation]):
                                detachedSingatureBytesOrg = certOrg.createDetachedSignature(pdfBytes)
                                item.setOrgSignature(detachedSingatureBytesOrg,
                                                     QtGui.qApp.userId,
                                                     QDateTime.currentDateTime())
                        if (certOrg or certUser) and (not hasRespDate or not hasOrgDate):
                            record = item.getRecord(tableFA)
                            db.updateRecord(tableFA, record)
                            self.cnt += 1
                    except Exception, e:
                        errorList.append(anyToUnicode(e.message))
                    yield 1

            progressDialog = CSimpleProgressDialog(self)
            progressDialog.okButtonText = u"Подписать"
            progressDialog.setState(CSimpleProgressDialog.ReadyToWork)
            progressDialog.setMinimumWidth(500)
            progressDialog.setWindowTitle(u'Подписание документов сертификатом врача и МО')
            progressDialog.setStepCount(all)
            progressDialog.setFormat(u'%v из %m')
            progressDialog.setAutoStart(False)
            progressDialog.setAutoClose(False)
            progressDialog.setStepIterator(stepIterator)
            progressDialog.exec_()
            self.applyFilters()
            QtGui.qApp.removeTmpDir(tempPath)
            if len(errorList):
                errorString = self.sortErrors(errorList)
                QtGui.QMessageBox.information(self,
                                              u'Ошибки получения сертификата',
                                              errorString
                                              )
            QtGui.QMessageBox.information(self,
                                          u'Подписание документов МО!',
                                          u'Успешно подписано {0} из {1}'.format(self.cnt, all))
        else:
            try:
                api = MSCApi(QtGui.qApp.getCsp())
                certUser = QtGui.qApp.getUserCert(api)
                certOrg = QtGui.qApp.getOrgCert(api)
            except Exception, e:
                QtGui.QMessageBox.information(self, u'Ошибка получения сертификата', anyToUnicode(e.message),
                                              QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)
                return

            errorList = []
            # tableName = 'Action_FileAttach'
            tableAFA = db.table('Action_FileAttach')
            if index == 0:
                cond = db.joinAnd([tableAFA['id'].inlist(attachFilesIdList),
                                   tableAFA['deleted'].eq(0),
                                   tableAFA['respSigner_id'].isNull() + ' OR ' + tableAFA['orgSigner_id'].isNull()])
            else:
                cond = db.joinAnd([tableAFA['deleted'].eq(0),
                                   tableAFA['respSigner_id'].isNull() + ' OR ' + tableAFA['orgSigner_id'].isNull()])
            records = db.getRecordList(tableAFA, '*', cond)

            tableE = db.table('Event')
            tableA = db.table('Action')
            table2 = tableA.leftJoin(tableE, tableE['id'].eq(tableA['event_id']))
            all = len(records)
            self.cnt = 0
            tempPath = QtGui.qApp.getTmpDir()

            def stepIterator(progressDialog):
                for record in records:
                    path = forceString(record.value('path'))
                    item = interface.createAttachedFileItem(path)
                    actionId = forceRef(record.value('master_id'))
                    item.setRecord(record)
                    localPath = os.path.join(tempPath, item.oldName)
                    interface.downloadFile(item, localPath)
                    tmpFile = QtCore.QFile(localPath)
                    tmpFile.open(QtCore.QIODevice.ReadOnly)
                    pdfBytes = tmpFile.readAll().data()
                    tmpFile.close()
                    tmpFile.remove()
                    if certUser:
                        certName = certUser.surName() + '' + certUser.givenName() + ', ' + certUser.snils()
                    else:
                        certName = None
                    record.setValue('respSigner_name', toVariant(certName))
                    try:
                        hasRespDate = forceDate(record.value('respSigningDatetime'))
                        hasOrgDate = forceDate(record.value('orgSigningDatetime'))
                        if not hasRespDate:
                            if record.value('respSigner_id'):
                                detachedSignatureBytesUser = certUser.createDetachedSignature(pdfBytes)
                                item.setRespSignature(detachedSignatureBytesUser,
                                                      QtGui.qApp.userId,
                                                      QDateTime.currentDateTime())
                        if not hasOrgDate:
                            if record.value('orgSigner_id') and QtGui.qApp.userHasAnyRight([urAdmin, urCanSingOrgSertNoAdmin, urCanSignForOrganisation]):
                                detachedSingatureBytesOrg = certOrg.createDetachedSignature(pdfBytes)
                                item.setOrgSignature(detachedSingatureBytesOrg,
                                                     QtGui.qApp.userId,
                                                     QDateTime.currentDateTime())
                        if not hasRespDate or not hasOrgDate:
                            record = item.getRecord(tableAFA)
                            db.updateRecord(tableAFA, record)

                        # eventRecord = db.getRecordEx(table2, 'Event.*', tableAction['id'].eq(actionId))
                        # db.updateRecord(tableEvent, eventRecord)
                            self.cnt += 1
                    except Exception, e:
                        # QtGui.QMessageBox.information(self, u'Ошибка подписания документа', anyToUnicode(e.message),
                        #                               QtGui.QMessageBox.Close, QtGui.QMessageBox.Close)
                        errorList.append(anyToUnicode(e.message))
                        if u'Действие было отменено пользователем' in anyToUnicode(e.message):
                            break
                    yield 1

            progressDialog = CSimpleProgressDialog(self)
            progressDialog.okButtonText = u"Подписать"
            progressDialog.setState(CSimpleProgressDialog.ReadyToWork)
            progressDialog.setMinimumWidth(500)
            progressDialog.setWindowTitle(u'Подписание документов сертификатом врача и МО')
            progressDialog.setStepCount(all)
            progressDialog.setFormat(u'%v из %m')
            progressDialog.setAutoStart(False)
            progressDialog.setAutoClose(False)
            progressDialog.setStepIterator(stepIterator)
            progressDialog.exec_()
            self.applyFilters()
            QtGui.qApp.removeTmpDir(tempPath)
            if len(errorList):
                errorString = self.sortErrors(errorList)
                QtGui.QMessageBox.information(
                    self,
                    u'Ошибки получения сертификата',
                    errorString
                )
            QtGui.QMessageBox.information(
                self,
                u'Подписание документов МО!',
                u'Успешно подписано {0} из {1}'. format(self.cnt, all))

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
        self.edtFilterBegDate.setDate(QDate.currentDate())
        self.edtFilterEndDate.setDate(QDate.currentDate())
        self.edtFilterDocumentBegDate.setDate(QDate.currentDate())
        self.edtFilterDocumentEndDate.setDate(QDate.currentDate())
        self.cmbFilterPerson.setCurrentIndex(0)
        self.chkFilterSNILS.setEnabled(False)
        self.chkFilterSNILS.setChecked(False)
        self.cmbFilterSigned.setCurrentIndex(0)
        self.chkFilterLastName.setChecked(False)
        self.chkFilterFirstName.setChecked(False)
        self.chkFilterPatrName.setChecked(False)
        self.chkFilterBegDate.setChecked(False)
        self.chkFilterEndDate.setChecked(False)
        self.chkFilterDocumentBegDate.setChecked(False)
        self.chkFilterDocumentEndDate.setChecked(False)
        self.chkFilterOrgStructure.setChecked(False)
        self.chkFilterActionType.setChecked(False)
        self.chkFilterTypeDoc.setChecked(False)
        self.cmbTypeDoc.setEnabled(False)
        self.chkFilterIdentify.setChecked(False)
        self.cmbFilterIdentify.setEnabled(False)
        self.cmbFilterIdentify.setCurrentIndex(0)
        self.cmbFilterIdentify.clearItemChecked()
        self.cmbFilterIdentify.setToolTip("")
        self.chkUserCert.setChecked(False)
        self.cmbUserCert.setValue(None)
        self.cmbPersonCert.setValue(None)

    def saveDefaultParams(self, params):
        prefs = {}
        for param, value in params.iteritems():
            setPref(prefs, param, value)

        setPref(prefs, 'ActionFileAttach', toVariant(''))
        setPref(QtGui.qApp.preferences.reportPrefs, 'ActIon', prefs)

    def getDefaultParams(self):
        result = {}
        prefs = getPref(QtGui.qApp.preferences.reportPrefs, 'ActIon', {})

        result['FilterTypeDoc'] = getPrefBool(prefs, 'FilterTypeDoc', False)
        result['TypeDoc'] = getPrefInt(prefs, 'TypeDoc', 0)
        result['FilterIdentify'] = getPrefBool(prefs, 'FilterIdentify', False)
        result['listFilterIdentify'] = getPrefString(prefs, 'listFilterIdentify', '')
        result['NotSignaturePerson'] = getPrefBool(prefs, 'NotSignaturePerson', False)

        if result['FilterTypeDoc']:
            self.chkFilterTypeDoc.setChecked(result['FilterTypeDoc'])
        if result['TypeDoc']:
            self.cmbTypeDoc.setCurrentIndex(int(result['TypeDoc']))
        if result['FilterIdentify']:
            self.chkFilterIdentify.setChecked(result['FilterIdentify'])
        if result['listFilterIdentify']:
            self.listFilterIdentify = result['listFilterIdentify']
        if result['NotSignaturePerson']:
            self.chkNotSignaturePerson.setChecked(result['NotSignaturePerson'])

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
        actionTypeId = None
        typeDoc = None
        identify = None
        documentBegDate = None
        documentEndDate = None
        sign = None
        personSign = None
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
            orgStructureList = getOrgStructureDescendants(self.cmbFilterOrgStructure.value())
        if self.cmbFilterPerson.currentIndex() != 0:
            personId = self.cmbFilterPerson.value()
        if self.chkFilterSNILS.isChecked() and self.chkFilterSNILS.isEnabled():
            personSNILS = True
        if self.chkFilterBegDate.isChecked():
            begDate = self.edtFilterBegDate.date()
        if self.chkFilterEndDate.isChecked():
            endDate = self.edtFilterEndDate.date()
        if self.chkFilterDocumentBegDate.isChecked():
            documentBegDate = self.edtFilterDocumentBegDate.date()
        if self.chkFilterDocumentEndDate.isChecked():
            documentEndDate = self.edtFilterDocumentEndDate.date()
        if self.chkFilterActionType.isChecked():
            actionTypeId = self.cmbActionType.value()
        if self.chkFilterTypeDoc.isChecked():
            typeDoc = self.cmbTypeDoc.currentText()
        identify = ", ".join(self.getListIdentify())
        result['FilterTypeDoc'] = self.chkFilterTypeDoc.isChecked()
        result['TypeDoc'] = self.cmbTypeDoc.currentIndex()
        result['FilterIdentify'] = self.chkFilterIdentify.isChecked()
        result['NotSignaturePerson'] = self.chkNotSignaturePerson.isChecked()
        result['listFilterIdentify'] = identify

        if self.chkUserCert.isChecked():
            api = MSCApi(QtGui.qApp.getCsp())
            userCertSha1 = self.cmbUserCert.value()
            cert = api.findCertInStores(api.SNS_OWN_CERTIFICATES, sha1hex=userCertSha1)
            sign = cert.snils() if cert else None
            personSign = self.cmbPersonCert.value()
        validationResultCodes = None
        if self.gbValidationResult.isVisible():
            validationResultCodes = []
            if self.chkValidationSuccess.isChecked():
                validationResultCodes.append(CValidationResult.SUCCESS)
            if self.chkValidationUnavailable.isChecked():
                validationResultCodes.append(CValidationResult.UNAVAILABLE)
            if self.chkValidationError.isChecked():
                validationResultCodes.append(CValidationResult.ERROR)
            if self.chkValidationNoResult.isChecked():
                validationResultCodes.append(None)
        self.saveDefaultParams(result)
        notSignaturePerson = self.chkNotSignaturePerson.isChecked()
        model.loadData(lastName=lastName,
                       firstName=firstName,
                       patrName=patrName,
                       eventId=eventId,
                       signedIndex=signedIndex,
                       orgStructureList=orgStructureList,
                       personId=personId,
                       begDate=begDate,
                       endDate=endDate,
                       actionTypeId=actionTypeId,
                       typeDoc=typeDoc,
                       identify=identify,
                       documentBegDate=documentBegDate,
                       documentEndDate=documentEndDate,
                       sign=sign,
                       notSignaturePerson=notSignaturePerson,
                       personSign=personSign,
                       personSNILS=personSNILS,
                       validationResultCodes=validationResultCodes)
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
    def on_chkFilterTypeDoc_toggled(self, check):
        if self.chkFilterTypeDoc.isChecked():
            self.cmbTypeDoc.setEnabled(True)
            self.cmbTypeDoc.setFocus()
        else:
            self.cmbTypeDoc.setDisabled(True)
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

    @pyqtSignature('int')
    def on_cmbFilterPerson_currentIndexChanged(self):
        if self.cmbFilterPerson.currentIndex() != 0:
            self.chkFilterSNILS.setEnabled(True)

    @pyqtSignature('bool')
    def on_chkFilterBegDate_toggled(self):
        if self.chkFilterBegDate.isChecked():
            self.edtFilterBegDate.setEnabled(True)
            self.edtFilterBegDate.setFocus()
        else:
            self.edtFilterBegDate.setDisabled(True)

    @pyqtSignature('bool')
    def on_chkFilterEndDate_toggled(self):
        if self.chkFilterEndDate.isChecked():
            self.edtFilterEndDate.setEnabled(True)
            self.edtFilterEndDate.setFocus()
        else:
            self.edtFilterEndDate.setDisabled(True)

    @pyqtSignature('bool')
    def on_chkFilterDocumentBegDate_toggled(self):
        if self.chkFilterDocumentBegDate.isChecked():
            self.edtFilterDocumentBegDate.setEnabled(True)
            self.edtFilterDocumentBegDate.setFocus()
        else:
            self.edtFilterDocumentBegDate.setDisabled(True)

    @pyqtSignature('bool')
    def on_chkFilterDocumentEndDate_toggled(self):
        if self.chkFilterDocumentEndDate.isChecked():
            self.edtFilterDocumentEndDate.setEnabled(True)
            self.edtFilterDocumentEndDate.setFocus()
        else:
            self.edtFilterDocumentEndDate.setDisabled(True)

    @pyqtSignature('')
    def on_btnPrint_clicked(self):
        pageFormat = CPageFormat(pageSize=CPageFormat.A4,
                                 orientation=CPageFormat.Portrait,
                                 leftMargin=15,
                                 topMargin=15,
                                 rightMargin=15,
                                 bottomMargin=15)
        html = self.contentToHTML()
        view = CReportViewDialog(self)
        view.setWindowTitle(u'Печать: Подписание документов')
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
        reportHeader = u'Подписание документов'
        tbl, model = self.getModelAndTable()
        tbl.setReportHeader(reportHeader)
        return tbl.contentToHTML()

    def openAttachFile(self):
        interface = QtGui.qApp.webDAVInterface
        tbl, model = self.getModelAndTable()
        currentRow = forceInt(tbl.currentRow())
        attachedFileId = forceInt(tbl.model().records[currentRow].value('id'))
        tabIdx = self.tabWidget.currentIndex()
        if tabIdx == 0:
            tableName = 'Action_FileAttach'
        elif tabIdx == 1:
            tableName = 'ProphylaxisPlanning_FileAttach'
        else:
            tableName = 'Event_FileAttach'
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

    # def getNeedAllMembersSign(self, index):
    #     return forceInt(self.records[index].value('isNeedAllMembersSign'))

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


class CActionFileAttachModel(CFileAttachModel):
    def __init__(self, parent):
        CRecordListModel.__init__(self, parent)
        self.addCol(CInDocTableCol(u'Фамилия', 'lastName', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Имя', 'firstName', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Отчество', 'patrName', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Дата рождения', 'birthDate', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Врач', 'personFullName', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Дата изменения', 'modifyDatetime', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Подписан врачом', 'isRespSigned', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Подписан МО', 'isOrgSigned', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Тип действия', 'actionType', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Код карточки', 'eventId', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Дата документа', 'documentDate', 30)).setReadOnly()
        self.addCol(CInDocTableCol(u'Имя файла', 'fileName', 40)).setReadOnly()
        self.validationResultCol = CValidationResultCol(self)
        self.addCol(self.validationResultCol)
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

    def loadData(self, lastName=None, firstName=None, patrName=None, eventId=None, signedIndex=5, orgStructureList=None,
                 personId=None, begDate=None, endDate=None, actionTypeId=None, typeDoc=None, identify=None, documentBegDate=None,
                 documentEndDate=None, sign=None, notSignaturePerson=None, personSign=None, personSNILS=None, validationResultCodes=None):
        db = QtGui.qApp.db

        tableActionFileAttach = db.table('Action_FileAttach')
        tableAction = db.table('Action')
        tableClient = db.table('Client')
        tableEvent = db.table('Event')
        tablePerson = db.table('Person')
        tableActionType = db.table('ActionType')
        tableActionTypeIdentification = db.table('ActionType_Identification').alias('ati')
        tableActionFLPrintTemplate = db.table('Action_FileAttach_PrintTemplate')
        tablePrintTemplate = db.table('rbPrintTemplate')
        tableQuery = tableActionFileAttach
        tableQuery = tableQuery.leftJoin(tableAction, tableAction['id'].eq(tableActionFileAttach['master_id']))
        tableQuery = tableQuery.leftJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        tableQuery = tableQuery.leftJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))
        tableQuery = tableQuery.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
        tableQuery = tableQuery.leftJoin(tableActionFLPrintTemplate, tableActionFLPrintTemplate['id'].eq(tableActionFileAttach['id']))
        tableQuery = tableQuery.leftJoin(tablePrintTemplate, tablePrintTemplate['id'].eq(tableActionFLPrintTemplate['template_id']))
        tableQuery = tableQuery.leftJoin(tablePerson, 'CASE WHEN rbPrintTemplate.requireSignerPerson = 1 THEN Person.`id`=Action.`setPerson_id` ELSE Person.`id`=Action.`person_id` END')
        if identify:
            tableQuery = tableQuery.leftJoin(tableActionTypeIdentification,
                                             tableActionTypeIdentification['master_id'].eq(tableActionType['id']))

        if personSNILS and personId:
            rec = db.getRecordEx(tablePerson, [tablePerson['SNILS']], [tablePerson['id'].eq(personId)])
            personSNILS = forceString(rec.value('SNILS')) if rec else None

        cols = ['STRAIGHT_JOIN Action_FileAttach.`id`',
                tableActionFileAttach['master_id'],
                tableActionFileAttach['createDatetime'].alias('documentDate'),
                tableActionFileAttach['modifyDatetime'],
                u"SUBSTRING_INDEX(Action_FileAttach.path, '/', -1) AS fileName",
                tableEvent['id'].alias('eventId'),
                u"concat_ws('|', ActionType.`code`, ActionType.`name`) AS actionType",
                tableClient['lastName'],
                tableClient['firstName'],
                tableClient['patrName'],
                tableClient['birthDate'],
                u"concat_ws(' ', Person.`lastName`, Person.`firstName`, Person.`patrName`) AS personFullName",
                u"IF(Action_FileAttach.`respSignatureBytes` IS NULL, 'Не подписан', 'Подписан') AS isRespSigned",
                u"IF(Action_FileAttach.`orgSignatureBytes` IS NULL, 'Не подписан', 'Подписан') AS isOrgSigned",
                # tablePerson['orgStructure_id'],
                # tablePerson['SNILS'],
                # tableAction['person_id']
                ]
        cond = [tableActionFileAttach['deleted'].eq(0),
                tableAction['deleted'].eq(0),
                tableActionType['deleted'].eq(0),
                tableEvent['org_id'].eq(QtGui.qApp.currentOrgId())
                ]
        if sign:
            tableAPT = db.table('ActionPropertyType')
            tableAP = db.table('ActionProperty')
            tableAPP = db.table('ActionProperty_Person')
            tableSignPerson = db.table('Person').alias('p')
            tableAFAS = db.table('Action_FileAttach_Signature')
            tableAFA = db.table('Action_FileAttach').alias('afa')

            table = tableAP.leftJoin(tableAPT, [tableAP['type_id'].eq(tableAPT['id']), tableAPT['deleted'].eq(0)])
            table = table.leftJoin(tableAPP, tableAPP['id'].eq(tableAP['id']))
            table = table.leftJoin(tableSignPerson, tableSignPerson['id'].eq(tableAPP['value']))
            table = table.leftJoin(tableAFA, tableAFA['master_id'].eq(tableAP['action_id']))
            table = table.leftJoin(tableAFAS, [tableAFAS['signer_id'].eq(tableAPP['value']),
                                               tableAFAS['master_id'].eq(tableAFA['id'])])
            subCond = [tableAP['action_id'].eq(tableAction['id']),
                       tableAFA['id'].eq(tableActionFileAttach['id']),
                       tableAPT['typeName'].eq('Person'),
                       tableSignPerson['SNILS'].eq(sign),
                       tableAPP['id'].isNotNull(),
                       tableAPT['valueDomain'].like('%signer%'),
                       tableAFAS['id'].isNull()
                       ]
            if personSign:
                subCond.append(tableSignPerson['id'].eq(personSign))
            cond.append(db.existsStmt(table, subCond))

        if notSignaturePerson:
            cond.append(u"""
  # проверка на наличие в ТД свойства типа person и маячка signer
EXISTS (SELECT
    NULL
  FROM ActionProperty
    LEFT JOIN ActionPropertyType      ON (ActionProperty.type_id = ActionPropertyType.id)      AND (ActionPropertyType.deleted = 0)
    LEFT JOIN ActionProperty_Person      ON ActionProperty_Person.id = ActionProperty.id
  WHERE (ActionProperty.action_id = Action.id)
  AND (ActionPropertyType.typeName = 'Person')
  AND (ActionProperty_Person.id IS NOT NULL)
  AND (ActionPropertyType.valueDomain LIKE '%signer%'))""")

            cond.append(u"""
  # проверка signer на наличие подписи, если хоть 1 ннет то не выводим
NOT EXISTS (SELECT
    NULL
  FROM ActionProperty
    LEFT JOIN ActionPropertyType      ON (ActionProperty.type_id = ActionPropertyType.id)      AND (ActionPropertyType.deleted = 0)
    LEFT JOIN ActionProperty_Person      ON ActionProperty_Person.id = ActionProperty.id
    LEFT JOIN Person AS p      ON p.id = ActionProperty_Person.value
    LEFT JOIN Action_FileAttach AS afa  ON afa.master_id = ActionProperty.action_id
    LEFT JOIN Action_FileAttach_Signature ON (Action_FileAttach_Signature.signer_id = ActionProperty_Person.value)
      AND (Action_FileAttach_Signature.master_id = afa.id)
  WHERE (ActionProperty.action_id = Action.id)
  AND (afa.id = Action_FileAttach.id)
  AND (ActionPropertyType.typeName = 'Person')
  AND (ActionProperty_Person.id IS NOT NULL)
  AND (ActionPropertyType.valueDomain LIKE '%signer%')
  AND (Action_FileAttach_Signature.id IS NULL))""")

        if lastName:
            cond.append("Client.lastName like '%s%%'" % lastName)
        if firstName:
            cond.append("Client.firstName like '%s%%'" % firstName)
        if patrName:
            cond.append("Client.patrName like '%s%%'" % patrName)
            
        if eventId:
            cond.append(tableEvent['id'].eq(eventId))
             
        if signedIndex == 1:
            cond.append(tableActionFileAttach['respSignatureBytes'].isNull())
        elif signedIndex == 2:
            cond.append(tableActionFileAttach['orgSignatureBytes'].isNull())
        elif signedIndex == 3:
            cond.append(tableActionFileAttach['orgSignatureBytes'].isNotNull())
        elif signedIndex == 4:
            cond.append(tableActionFileAttach['respSignatureBytes'].isNotNull())
            cond.append(tableActionFileAttach['orgSignatureBytes'].isNull())
        elif signedIndex == 5:
            cond.append(db.joinOr([tableActionFileAttach['respSignatureBytes'].isNull(),
                                   tableActionFileAttach['orgSignatureBytes'].isNull()]))
        elif signedIndex == 6:
            cond.append(tableActionFileAttach['respSignatureBytes'].isNotNull())

        if orgStructureList:
            cond.append(tablePerson['orgStructure_id'].inlist(orgStructureList))

        if forceBool(personSNILS):
            cond.append(tablePerson['SNILS'].eq(personSNILS))
        elif personId:
            cond.append(tablePerson['id'].eq(personId))

        if begDate and endDate:
            cond.append(tableActionFileAttach['modifyDatetime'].ge(begDate))
            cond.append(tableActionFileAttach['modifyDatetime'].lt(endDate.addDays(1)))
        elif begDate:
            cond.append(tableActionFileAttach['modifyDatetime'].ge(begDate))
        elif endDate:
            cond.append(tableActionFileAttach['modifyDatetime'].lt(endDate.addDays(1)))
        else:
            if not documentBegDate and not documentEndDate:
                cond.append(tableActionFileAttach['modifyDatetime'].ge(QDate().currentDate().addDays(-2)))

        if documentBegDate and documentEndDate:
            cond.append(tableActionFileAttach['createDatetime'].ge(documentBegDate))
            cond.append(tableActionFileAttach['createDatetime'].lt(documentEndDate.addDays(1)))
        elif documentBegDate:
            cond.append(tableActionFileAttach['createDatetime'].ge(documentBegDate))
        elif documentEndDate:
            cond.append(tableActionFileAttach['createDatetime'].lt(documentEndDate.addDays(1)))

        if actionTypeId:
            actionTypeId = db.getDescendants('ActionType', 'group_id', actionTypeId)
            cond.append(tableActionType['id'].inlist(actionTypeId))
        if typeDoc:
            cond.append("Action_FileAttach.path LIKE '%.{0}'".format(typeDoc))
        else:
            cond.append("Action_FileAttach.path LIKE '%.pdf' OR Action_FileAttach.path LIKE '%.xml'")
        if identify:
            cond.append("ati.note != ''")
            cond.append("ati.note IS not NULL")
            cond.append("ati.deleted = 0")
            cond.append("ati.value IN ({0})".format(identify))

        records = db.getRecordList(tableQuery, cols, cond)

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




class CProphylaxisPlanningFileAttachModel(CFileAttachModel):
    def __init__(self, parent):
        CRecordListModel.__init__(self, parent)
        self.addCol(CInDocTableCol(u'Фамилия', 'lastName', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Имя', 'firstName', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Отчество', 'patrName', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Дата рождения', 'birthDate', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Врач', 'personLastName', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Дата изменения', 'modifyDatetime', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Подписан врачом', 'respSignatureBytes', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Подписан МО', 'orgSignatureBytes', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Код карточки', 'kkdnId', 12)).setReadOnly()
        self.addCol(CInDocTableCol(u'Дата документа', 'documentDate', 30)).setReadOnly()
        self.addCol(CInDocTableCol(u'Имя файла', 'fileName', 40)).setReadOnly()
        self.headerSortingCol = {0: True}
        self.records = None
        endDate = QDate().currentDate()
        begDate = QDate().currentDate().addDays(-2)
        self.loadData(begDate=begDate, endDate=endDate)

    def loadData(self, lastName=None, firstName=None, patrName=None, eventId=None, signedIndex=5, orgStructureList=None,
                 personId=None, begDate=None, endDate=None, actionTypeId=None, typeDoc=None, identify=None, documentBegDate=None,
                 documentEndDate=None, sign=None, notSignaturePerson=None, personSign=None, personSNILS=None, validationResultCodes=None):
        db = QtGui.qApp.db

        tablePPFA = db.table('ProphylaxisPlanning_FileAttach')
        tablePP = db.table('ProphylaxisPlanning')
        tableClient = db.table('Client')
        tablePerson = db.table('Person')
        query = tablePPFA.leftJoin(tablePP, tablePP['id'].eq(tablePPFA['master_id']))
        query = query.leftJoin(tableClient, tableClient['id'].eq(tablePP['client_id']))
        query = query.leftJoin(tablePerson, tablePerson['id'].eq(tablePP['person_id']))

        if personSNILS and personId:
            rec = db.getRecordEx(tablePerson, [tablePerson['SNILS']], [tablePerson['id'].eq(personId)])
            personSNILS = forceString(rec.value('SNILS')) if rec else None

        cols = ['DISTINCT(ProphylaxisPlanning_FileAttach.`id`) as id ',
                tablePPFA['master_id'],
                tablePPFA['path'],
                tablePP['id'].alias('kkdnId'),
                tablePP['client_id'],
                tableClient['lastName'],
                tableClient['firstName'],
                tableClient['patrName'],
                tableClient['birthDate'],
                tablePerson['lastName'].alias('personLastName'),
                tablePerson['firstName'].alias('personFirstName'),
                tablePerson['patrName'].alias('personPatrName'),
                tablePPFA['modifyDatetime'],
                tablePPFA['respSignatureBytes'],
                tablePPFA['orgSignatureBytes']]
        cond = [tablePPFA['deleted'].eq(0),
                tablePP['deleted'].eq(0),
                ]

        if lastName:
            cond.append("Client.lastName like '%s%%'" % lastName)
        if firstName:
            cond.append("Client.firstName like '%s%%'" % firstName)
        if patrName:
            cond.append("Client.patrName like '%s%%'" % patrName)
        
        if eventId:
            cond.append(tablePP['id'].eq(eventId))
        
        if signedIndex == 1:
            cond.append(tablePPFA['respSignatureBytes'].isNull())
        elif signedIndex == 2:
            cond.append(tablePPFA['orgSignatureBytes'].isNull())
        elif signedIndex == 3:
            cond.append(tablePPFA['orgSignatureBytes'].isNotNull())
        elif signedIndex == 4:
            cond.append(tablePPFA['respSignatureBytes'].isNotNull())
            cond.append(tablePPFA['orgSignatureBytes'].isNull())
        elif signedIndex == 5:
            cond.append(db.joinOr([tablePPFA['respSignatureBytes'].isNull(),
                                   tablePPFA['orgSignatureBytes'].isNull()]))
        elif signedIndex == 6:
            cond.append(tablePPFA['respSignatureBytes'].isNotNull())
        if orgStructureList:
            cond.append(tablePerson['orgStructure_id'].inlist(orgStructureList))
        if QtGui.qApp.userHasAnyRight([urAdmin, urCanSingOrgSertNoAdmin, urCanSignForOrganisation]) and not sign:
            if forceBool(personSNILS):
                cond.append(tablePerson['SNILS'].eq(personSNILS))
            elif personId:
                cond.append(tablePP['person_id'].eq(personId))
        else:
            if not sign:
                cond.append(tablePP['person_id'].eq(QtGui.qApp.userId))

        if begDate and endDate:
            cond.append(tablePPFA['modifyDatetime'].ge(begDate))
            cond.append(tablePPFA['modifyDatetime'].lt(endDate.addDays(1)))
        elif begDate:
            cond.append(tablePPFA['modifyDatetime'].ge(begDate))
        elif endDate:
            cond.append(tablePPFA['modifyDatetime'].lt(endDate.addDays(1)))
        else:
            if not documentBegDate and not documentEndDate:
                cond.append(tablePPFA['modifyDatetime'].ge(QDate().currentDate().addDays(-2)))
        if documentBegDate and documentEndDate:
            cond.append("REPLACE(SUBSTRING_INDEX(ProphylaxisPlanning_FileAttach.path, '/', 3),'/','-') BETWEEN '%s' and '%s'" % (
                documentBegDate.toString('yyyy-MM-dd'), documentEndDate.toString('yyyy-MM-dd')))
        elif documentBegDate:
            cond.append("REPLACE(SUBSTRING_INDEX(ProphylaxisPlanning_FileAttach.path, '/', 3),'/','-') >= '%s' " % (
                documentBegDate.toString('yyyy-MM-dd')))
        elif documentEndDate:
            cond.append("REPLACE(SUBSTRING_INDEX(ProphylaxisPlanning_FileAttach.path, '/', 3),'/','-') <= '%s' " % (
                documentEndDate.toString('yyyy-MM-dd')))

        orderBy = 'Person.lastName'
        records = db.getRecordList(query, cols, cond, orderBy)
        for record in records:
            if forceBool(record.value('respSignatureBytes')):
                record.setValue('respSignatureBytes', toVariant(u'Подписан'))
            else:
                record.setValue('respSignatureBytes', toVariant(u'Не подписан'))
            if forceBool(record.value('orgSignatureBytes')):
                record.setValue('orgSignatureBytes', toVariant(u'Подписан'))
            else:
                record.setValue('orgSignatureBytes', toVariant(u'Не подписан'))
            personLastName = forceString(record.value('personLastName'))
            personFirstName = forceString(record.value('personFirstName'))
            personPatrName = forceString(record.value('personPatrName'))
            personFullName = personLastName + u' ' + personFirstName + u' ' + personPatrName
            record.setValue('personLastName', toVariant(personFullName))
            filePath = forceString(record.value('path'))
            if forceBool(filePath):
                fileData = filePath.split('/')
                fileYear = forceInt(fileData[0])
                fileMonth = forceInt(fileData[1])
                fileDay = forceInt(fileData[2])
                fileName = forceString(fileData[4])
                date = QDate(fileYear, fileMonth, fileDay)
                record.append(QSqlField('documentDate'))
                record.setValue('documentDate', date)
                record.append(QSqlField('fileName'))
                record.setValue('fileName', fileName)
        self.records = records
        self.setItems(records)


class CEventFileAttach(CFileAttachModel):
    def __init__(self, parent):
        CRecordListModel.__init__(self, parent)
        self.addCol(CInDocTableCol(u'Фамилия', 'lastName', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Имя', 'firstName', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Отчество', 'patrName', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Дата рождения', 'birthDate', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Врач', 'personLastName', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Дата изменения', 'modifyDatetime', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Подписан врачом', 'respSignatureBytes', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Подписан МО', 'orgSignatureBytes', 20)).setReadOnly()
        self.addCol(CInDocTableCol(u'Код карточки', 'eventId', 12)).setReadOnly()
        self.addCol(CInDocTableCol(u'Дата документа', 'documentDate', 30)).setReadOnly()
        self.addCol(CInDocTableCol(u'Имя файла', 'fileName', 40)).setReadOnly()
        self.headerSortingCol = {0: True}
        self.records = None
        endDate = QDate().currentDate()
        begDate = QDate().currentDate().addDays(-2)
        self.loadData(begDate=begDate, endDate=endDate)

    def loadData(self, lastName=None, firstName=None, patrName=None, eventId=None, signedIndex=5, orgStructureList=None,
                 personId=None, begDate=None, endDate=None, actionTypeId=None, typeDoc=None, identify=None, documentBegDate=None,
                 documentEndDate=None, sign=None, notSignaturePerson=None, personSign=None, personSNILS=None, validationResultCodes=None):
        db = QtGui.qApp.db

        tableEventFileAttach = db.table('Event_FileAttach')
        tableEvent = db.table('Event')
        tableClient = db.table('Client')
        tablePerson = db.table('Person')
        query = tableEventFileAttach.leftJoin(tableEvent, tableEvent['id'].eq(tableEventFileAttach['master_id']))
        query = query.leftJoin(tableClient, tableClient['id'].eq(tableEvent['client_id']))
        query = query.leftJoin(tablePerson, tablePerson['id'].eq(tableEvent['execPerson_id']))

        if personSNILS and personId:
            rec = db.getRecordEx(tablePerson, [tablePerson['SNILS']], [tablePerson['id'].eq(personId)])
            personSNILS = forceString(rec.value('SNILS')) if rec else None

        cols = ['DISTINCT(Event_FileAttach.`id`) as id',
            tableEventFileAttach['master_id'],
            tableEventFileAttach['path'],
            tableEvent['id'].alias('eventId'),
            tableEvent['client_id'],
            tableClient['lastName'],
            tableClient['firstName'],
            tableClient['patrName'],
            tableClient['birthDate'],
            tablePerson['lastName'].alias('personLastName'),
            tablePerson['firstName'].alias('personFirstName'),
            tablePerson['patrName'].alias('personPatrName'),
            tableEventFileAttach['modifyDatetime'],
            tableEventFileAttach['respSignatureBytes'],
            tableEventFileAttach['orgSignatureBytes']]
        cond = [tableEventFileAttach['deleted'].eq(0),
                tableEvent['deleted'].eq(0),
                ]

        if lastName:
            cond.append("Client.lastName like '%s%%'" % lastName)
        if firstName:
            cond.append("Client.firstName like '%s%%'" % firstName)
        if patrName:
            cond.append("Client.patrName like '%s%%'" % patrName)

        if eventId:
            cond.append(tableEvent['id'].eq(eventId))

        if signedIndex == 1:
            cond.append(tableEventFileAttach['respSignatureBytes'].isNull())
        elif signedIndex == 2:
            cond.append(tableEventFileAttach['orgSignatureBytes'].isNull())
        elif signedIndex == 3:
            cond.append(tableEventFileAttach['orgSignatureBytes'].isNotNull())
        elif signedIndex == 4:
            cond.append(tableEventFileAttach['respSignatureBytes'].isNotNull())
            cond.append(tableEventFileAttach['orgSignatureBytes'].isNull())
        elif signedIndex == 5:
            cond.append(db.joinOr([tableEventFileAttach['respSignatureBytes'].isNull(),
                                   tableEventFileAttach['orgSignatureBytes'].isNull()]))
        elif signedIndex == 6:
            cond.append(tableEventFileAttach['respSignatureBytes'].isNotNull())
        if orgStructureList:
            cond.append(tablePerson['orgStructure_id'].inlist(orgStructureList))
        if QtGui.qApp.userHasAnyRight([urAdmin, urCanSingOrgSertNoAdmin, urCanSignForOrganisation]) and not sign:
            if forceBool(personSNILS):
                cond.append(tablePerson['SNILS'].eq(personSNILS))
            elif personId:
                cond.append(tableEvent['execPerson_id'].eq(personId))
        else:
            if not sign:
                cond.append(tableEvent['execPerson_id'].eq(QtGui.qApp.userId))

        if begDate and endDate:
            cond.append(tableEventFileAttach['modifyDatetime'].ge(begDate))
            cond.append(tableEventFileAttach['modifyDatetime'].lt(endDate.addDays(1)))
        elif begDate:
            cond.append(tableEventFileAttach['modifyDatetime'].ge(begDate))
        elif endDate:
            cond.append(tableEventFileAttach['modifyDatetime'].lt(endDate.addDays(1)))
        else:
            if not documentBegDate and not documentEndDate:
                cond.append(tableEventFileAttach['modifyDatetime'].ge(QDate().currentDate().addDays(-2)))
        if documentBegDate and documentEndDate:
            cond.append(tableEventFileAttach['createDatetime'].ge(documentBegDate))
            cond.append(tableEventFileAttach['createDatetime'].lt(documentEndDate.addDays(1)))
        elif documentBegDate:
            cond.append(tableEventFileAttach['createDatetime'].ge(documentBegDate))
        elif documentEndDate:
            cond.append(tableEventFileAttach['createDatetime'].lt(documentEndDate.addDays(1)))

        if typeDoc:
            cond.append("Event_FileAttach.path LIKE '%.{0}'".format(typeDoc))
        else:
            cond.append("Event_FileAttach.path LIKE '%.pdf' OR Event_FileAttach.path LIKE '%.xml'")

        orderBy = 'Person.lastName'
        records = db.getRecordList(query, cols, cond, orderBy)
        for record in records:
            if forceBool(record.value('respSignatureBytes')):
                record.setValue('respSignatureBytes', toVariant(u'Подписан'))
            else:
                record.setValue('respSignatureBytes', toVariant(u'Не подписан'))
            if forceBool(record.value('orgSignatureBytes')):
                record.setValue('orgSignatureBytes', toVariant(u'Подписан'))
            else:
                record.setValue('orgSignatureBytes', toVariant(u'Не подписан'))
            personLastName = forceString(record.value('personLastName'))
            personFirstName = forceString(record.value('personFirstName'))
            personPatrName = forceString(record.value('personPatrName'))
            personFullName = personLastName + u' ' + personFirstName + u' ' + personPatrName
            record.setValue('personLastName', toVariant(personFullName))
            filePath = forceString(record.value('path'))
            if forceBool(filePath):
                fileData = filePath.split('/')
                fileYear = forceInt(fileData[0])
                fileMonth = forceInt(fileData[1])
                fileDay = forceInt(fileData[2])
                fileName = forceString(fileData[4])
                date = QDate(fileYear, fileMonth, fileDay)
                record.append(QSqlField('documentDate'))
                record.setValue('documentDate', date)
                record.append(QSqlField('fileName'))
                record.setValue('fileName', fileName)
        self.records = records
        self.setItems(records)




class CValidationResultCol(CInDocTableCol):
    def __init__(self, model):
        CInDocTableCol.__init__(self, u'Валидация', 'id', 40)
        self.model = model
        self.setReadOnly()

    def toString(self, val, record):
        id = forceRef(val)
        result = self.model.validationResults.get(id)
        if not result:
            return QVariant()
        resultCode = result.code
        if resultCode == CValidationResult.SUCCESS:
            return QVariant(u'Пройдена успешно')
        elif resultCode == CValidationResult.UNAVAILABLE:
            return QVariant(u'Отсутствует схематрон, документ не подлежит валидации')
        elif resultCode == CValidationResult.ERROR:
            return QVariant(u'\n'.join(result.errors))
        else:
            return QVariant()


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
