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
import datetime
import hashlib
from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDate, QObject, pyqtSignature, SIGNAL, QVariant, QRegExp
from PyQt4.QtGui import QAction

from library.IdentificationModel import CIdentificationModel, checkIdentification
from library.InDocTable          import CInDocTableModel, CDateInDocTableCol, CEnumInDocTableCol, CInDocTableCol, CRBInDocTableCol, CDateTimeInDocTableCol
from library.interchange         import (
                                          getCheckBoxValue,
                                          getComboBoxValue,
                                          getDateEditValue,
                                          getLineEditValue,
                                          getRBComboBoxValue,
                                          getSpinBoxValue,
                                          setCheckBoxValue,
                                          setComboBoxValue,
                                          setDateEditValue,
                                          setLineEditValue,
                                          setRBComboBoxValue,
                                          setSpinBoxValue,
                                        )
from library.ItemsListDialog     import CItemsListDialog, CItemEditorBaseDialog
from library.TableModel import CDesignationCol, CRefBookCol, CTextCol, CDateTimeCol
from library.Utils import (
    addDotsEx,
    agreeNumberAndWord,
    exceptionToUnicode,
    forceDate,
    forceInt,
    forceRef,
    forceString,
    forceStringEx,
    nameCase,
    toVariant,
    trim,
    formatSNILS,
    isNameValid,
    forceBool,
)
from library.PrintTemplates      import (
                                          getPrintButton,
                                          applyTemplate,
                                          CPrintAction,
                                          getPrintTemplates,
                                        )
from library.PrintInfo           import CInfoContext
from library.DialogBase          import CDialogBase
from library.RecordLock          import CRecordLockMixin
from library.database            import CTableRecordCache

from Orgs.Utils                  import getOrgStructureDescendants, COrgStructureInfoList, CActivityInfo, COrgInfo
from Orgs.PersonInfo             import CPersonInfoListEx
from Registry.ClientEditDialog   import checkSNILSEntered
from Registry.Utils              import getAddressId,  getAddress
from Reports.ReportBase          import CReportBase, createTable
from Reports.ReportView          import CReportViewDialog
from Timeline.PersonTimeTable    import CPersonTimeTableModel

from RefBooks.DocumentType.Descr import getDocumentTypeDescr
from RefBooks.Speciality.Info    import CSpecialityInfo
from Users.Rights                import urEditLoginPasswordProfileUser
from Users.UserInfo              import CUserProfileInfo

from Ui_PersonsListDialog       import Ui_PersonsListDialog
from Ui_PersonEditor            import Ui_ItemEditorDialog
from Ui_MultiplePersonEditor    import Ui_MultiplePersonEditorDialog



class CPersonList(Ui_PersonsListDialog, CItemsListDialog):
    def __init__(self, parent):
        CItemsListDialog.__init__(self, parent, [
            CTextCol(u'Код', ['code'], 6),
            CSNILSCol(u'СНИЛС', ['SNILS'], 20),
            CTextCol(u'Фамилия', ['lastName'], 20),
            CTextCol(u'Имя', ['firstName'], 20),
            CTextCol(u'Отчество', ['patrName'], 20),
            # CTextCol(u'Регистрационное имя', ['login'], 20),
            CTextCol(u'Федеральный код', ['federalCode'], 10),
            CDesignationCol(u'ЛПУ', ['org_id'], ('Organisation', 'infisCode'), 5),
            CDesignationCol(u'Подразделение', ['orgStructure_id'], ('OrgStructure', 'name'), 5),
            CRefBookCol(u'Должность', ['post_id'], 'rbPost', 20),
            CRefBookCol(u'Специальность', ['speciality_id'], 'rbSpeciality', 10),
            CRefBookCol(u'Профиль', ['userProfile_id'], 'rbUserProfile', 10),
            CDateTimeCol(u'Дата увольнения', ['retireDate'], 8),
###            CTextCol(u'ИНФИС код', ['infis'], 20),
            ], 'Person',
#            ['code', 'lastName', 'firstName', 'patrName'])
            # 1. кодов может не быть; 2. лучше видно повторы
            ['lastName', 'firstName', 'patrName'])
        self.setWindowTitleEx(u'Сотрудники')
        self.cmbUserRightsProfile.setTable('rbUserProfile')
        self.cmbUserRightsProfile.setFilter('deleted=0')
        self.cmbUserRightsProfile.setAddNone(True, u'все,не задано')
        self.cmbUserRightsProfile.setValue(None)

        
        self._recordList = []
        self._tableName = 'rbPost'

        self.tblItems.setContextMenuPolicy(Qt.CustomContextMenu)
        QObject.connect(self.tblItems, SIGNAL('customContextMenuRequested(QPoint)'), self.customMenuRequested)

        # stmt = "SELECT DISTINCT speciality_id, name FROM Person JOIN rbSpeciality ON rbSpeciality.id=Person.speciality_id ORDER BY name"
        # self.specialityList = [None, None]
        # query = QtGui.qApp.db.query(stmt)
        # self.boxSpec.addItem(u'Без специальности')
        # self.boxSpec.addItem(u'Любая специальность')
        # while query.next():
        #     record = query.record()
        #     speciality_id = forceInt(record.value('speciality_id'))
        #     name = forceString(record.value('name'))
        #     self.boxSpec.addItem(name)
        #     self.specialityList.append(speciality_id)

        self.boxSpec.setTable('rbSpeciality')

        stmt = "SELECT DISTINCT org_id, infisCode FROM Person LEFT JOIN Organisation ON Organisation.id=Person.org_id ORDER BY infisCode"
        self.LPUList = []
        query = QtGui.qApp.db.query(stmt)
        while query.next():
            record = query.record()
            org_id = forceInt(record.value('org_id'))
            infisCode = forceString(record.value('infisCode')) if org_id else u'не задано'
            self.boxLPU.addItem(infisCode)
            self.LPUList.append(org_id)

        stmt = 'SELECT DISTINCT id, CONCAT(code," | ", name) AS name FROM rbActivity'
        self.activityList = [None, None]
        query = QtGui.qApp.db.query(stmt)
        self.cmbActivity.addItem(u'Без вида деятельности')
        self.cmbActivity.addItem(u'Любой вид деятельности')
        while query.next():
            record = query.record()
            id = forceRef(record.value('id'))
            name = forceString(record.value('name'))
            self.cmbActivity.addItem(name)
            self.activityList.append(id)

        # stmt = 'SELECT DISTINCT rbPost.name, rbPost.id FROM Person JOIN rbPost ON Person.post_id=rbPost.id'
        # self.cmbPost.addItem(u'Без должности')
        # self.cmbPost.addItem(u'Любая должность')
        # self.postIdList = [None, None]
        # query = QtGui.qApp.db.query(stmt)
        # while query.next():
        #     record = query.record()
        #     self.postIdList.append(forceInt(record.value('id')))
        #     self.cmbPost.addItem(forceString(record.value('name')))

        self.cmbPost.setTable('rbPost')

        # QObject.connect(self.tblItems.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.setSort)
        templates = getPrintTemplates(getPersonContext())
        if not templates:
            self.btnPrint.setId(-1)
        else:
            for template in templates:
                action = CPrintAction(template.name, template.id, self.btnPrint, self.btnPrint)
                self.btnPrint.addAction(action)
            self.btnPrint.menu().addSeparator()
            self.btnPrint.addAction(CPrintAction(u'Список Сотрудники', -1, self.btnPrint, self.btnPrint))
        self.btnPrint.setEnabled(True)
        self.tblItems.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tblItems.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.chkUserLogin.setVisible(False)
        self.edtUserLogin.setVisible(False)
        self.personItems = []


    def preSetupUi(self):
        self.addObject('btnPrint',  getPrintButton(self, '', u'Печать F6'))
        self.addObject('btnNew',    QtGui.QPushButton(u'Вставка F9', self))
        self.addObject('btnEdit',   QtGui.QPushButton(u'Правка F4', self))
        self.addObject('btnFilter', QtGui.QPushButton(u'Фильтр', self))
        self.addObject('btnSelect', QtGui.QPushButton(u'Выбор', self))


    @pyqtSignature('')
    def on_btnPrint_clicked(self):
        pass


    def getItemEditor(self):
        return CPersonEditor(self)


    def select(self, props):
        table = self.model.table()
        cond = [table['deleted'].eq(0)]
        onlyOwn = self.chkOnlyOwn.isChecked()
        onlyWorking = self.chkOnlyWorking.isChecked()
        onlyRetired = self.chkOnlyRetired.isChecked()
        if self.chkChairPerson.isChecked():
            cond.append(table['chairPerson'].eq(1))
        if onlyOwn:
            cond.append(table['org_id'].eq(QtGui.qApp.currentOrgId()))
        if onlyWorking:
            cond.append(table['retireDate'].isNull())
        if onlyRetired:
            cond.append(table['retireDate'].isNotNull())
        if self.chkStrPodr.isChecked():
            orgStructure_id = self.boxStrPodr.value()
            orgStructureIdList = getOrgStructureDescendants(orgStructure_id)
            cond.append(table['orgStructure_id'].inlist(orgStructureIdList))
        if self.chkSpec.isChecked():
            index = self.boxSpec.currentIndex()
            if index == 0:
                cond.append(table['speciality_id'].isNull())
            else:
                cond.append(table['speciality_id'].eq(self.boxSpec.getValue()))
        if self.chkActivity.isChecked():
            index = self.cmbActivity.currentIndex()
            c = '%s (SELECT `id` FROM `Person_Activity` WHERE `master_id` = Person.`id`  %s AND `deleted` = 0)'
            if index == 0:
                cond.append(c % ('NOT EXISTS', ''))
            elif index == 1:
                cond.append(c % ('EXISTS', 'AND `activity_id` IS NOT NULL'))
            else:
                activityId = self.activityList[index]
                cond.append(c % ('EXISTS', 'AND `activity_id` ='+str(activityId)))
        if self.chkLPU.isChecked():
            org_id = self.LPUList[self.boxLPU.currentIndex()]
            cond.append(table['org_id'].eq(toVariant(org_id)))
        if self.chkUserRightsProfile.isChecked():
            userProfileId = self.cmbUserRightsProfile.value()
            if userProfileId:
                if userProfileId > 0:
                    cond.append(table['userProfile_id'].eq(toVariant(userProfileId)))
                elif userProfileId == -1:
                    cond.append(table['userProfile_id'].isNotNull())
        if self.chkUserLogin.isChecked():
            userLogin = trim(self.edtUserLogin.text())
            cond.append(table['login'].like(addDotsEx(userLogin)))
        if self.chkSurname.isChecked():
            surname = trim(self.edtSurname.text())
            if surname:
                cond.append(table['lastName'].like(u'%%%s%%' % surname))
            else:
                cond.append(table['lastName'].eq(u''))
        if self.chkSNILS.isChecked():
            SNILS = forceString(self.edtSNILS.text()).replace(' ', '-').split('-')
            if SNILS:
                if SNILS[0]:
                    cond.append(table['SNILS'].like(u'{}%%'.format(SNILS[0])))

                if SNILS[1]:
                    cond.append(table['SNILS'].like(u'___{}%%'.format(SNILS[1])))

                if SNILS[2]:
                    cond.append(table['SNILS'].like(u'______{}%%'.format(SNILS[2])))

                if SNILS[3]:
                    cond.append(table['SNILS'].like(u'_________{}%%'.format(SNILS[3])))
            else:
                cond.append(table['SNILS'].eq(u''))
        if self.chkPost.isChecked():
            index = self.cmbPost.currentIndex()
            if index == 0:
                cond.append(table['post_id'].isNull())
            else:
                cond.append(table['post_id'].eq(self.cmbPost.getValue()))

        return QtGui.qApp.db.getIdList(table, 'id', where=cond, order=self.order)


    def customMenuRequested(self, pos):
        menu = QtGui.QMenu(self)
        edtDuplicate = menu.addAction(u'Дублировать')
        QObject.connect(edtDuplicate, SIGNAL('triggered()'), lambda: self.duplicateCurrentRow())
        if len(self.tblItems.selectionModel().selectedRows()) > 1:
            edtMultipleEditor = menu.addAction(u'Групповой редактор')
            QObject.connect(edtMultipleEditor, SIGNAL('triggered()'), lambda: self.openMultipleEditor())
        menu.popup(self.tblItems.viewport().mapToGlobal(pos))


    def openMultipleEditor(self):
        editor = CMultiplePersonEditor(self)
        if editor.exec_(self.tblItems.selectedItemIdList()):
            editor.save()


    def duplicateRecord(self, itemId):
        def duplicateRecordInternal():
            db = QtGui.qApp.db
            record = db.getRecord(self.model.table(), '*', itemId)
            code = forceString(record.value('code'))
            record.setNull('id')  # чтобы не дублировался id
            record.setValue('code', code + u' - копия')
            record.setValue('login', None)
            record.setValue('password', None)
            db.transaction()
            try:
                newItemId = db.insertRecord(self.model.table(), record)
                self.copyInternals(newItemId, itemId)
                db.commit()
                return newItemId
            except:
                db.rollback()
                raise
        ok, result = QtGui.qApp.call(self, duplicateRecordInternal)
        return result


    @pyqtSignature('int')
    def on_chkOnlyOwn_stateChanged(self, state):
        self.renewListAndSetTo(self.currentItemId())


    @pyqtSignature('int')
    def on_chkChairPerson_stateChanged(self, state):
        self.renewListAndSetTo(self.currentItemId())


    @pyqtSignature('int')
    def on_chkIsHideQueue_stateChanged(self, text):
        self.renewListAndSetTo(self.currentItemId())


    @pyqtSignature('int')
    def on_chkIsHideSchedule_stateChanged(self, text):
        self.renewListAndSetTo(self.currentItemId())


    @pyqtSignature('int')
    def on_chkOnlyWorking_stateChanged(self, state):
        self.chkStateChangeWithoutRenew(state, self.chkOnlyRetired, self.on_chkOnlyRetired_stateChanged)
        self.renewListAndSetTo(self.currentItemId())

    @pyqtSignature('int')
    def on_chkOnlyRetired_stateChanged(self, state):
        # синхронизирую состояние чекбоксов
        self.chkStateChangeWithoutRenew(state, self.chkOnlyWorking, self.on_chkOnlyWorking_stateChanged)
        self.renewListAndSetTo(self.currentItemId())

    def chkStateChangeWithoutRenew(self, state, wgt, fn):
        if state and isinstance(wgt, QtGui.QCheckBox):
            wgt.stateChanged.disconnect()
            wgt.setChecked(not state)
            wgt.stateChanged.connect(fn)

    @pyqtSignature('int')
    def on_chkStrPodr_stateChanged(self, state):
        self.renewListAndSetTo(self.currentItemId())


    @pyqtSignature('int')
    def on_boxStrPodr_currentIndexChanged(self, index):
        if self.chkStrPodr.isChecked():
            self.renewListAndSetTo(self.currentItemId())


    @pyqtSignature('int')
    def on_cmbUserRightsProfile_currentIndexChanged(self, index):
        if self.chkUserRightsProfile.isChecked():
            self.renewListAndSetTo(self.currentItemId())


    @pyqtSignature('int')
    def on_chkUserRightsProfile_stateChanged(self, state):
        self.renewListAndSetTo(self.currentItemId())

    @pyqtSignature('int')
    def on_chkUserLogin_stateChanged(self, state):
        self.renewListAndSetTo(self.currentItemId())

    @pyqtSignature('int')
    def on_chkSpec_stateChanged(self, state):
        self.renewListAndSetTo(self.currentItemId())


    @pyqtSignature('int')
    def on_boxSpec_currentIndexChanged(self, index):
        if self.chkSpec.isChecked():
            self.renewListAndSetTo(self.currentItemId())

    @pyqtSignature('int')
    def on_chkActivity_stateChanged(self, state):
        self.renewListAndSetTo(self.currentItemId())


    @pyqtSignature('int')
    def on_cmbActivity_currentIndexChanged(self, index):
        if self.chkActivity.isChecked():
            self.renewListAndSetTo(self.currentItemId())


    @pyqtSignature('int')
    def on_chkLPU_stateChanged(self, state):
        self.renewListAndSetTo(self.currentItemId())


    @pyqtSignature('int')
    def on_boxLPU_currentIndexChanged(self, index):
        if self.chkLPU.isChecked():
            self.renewListAndSetTo(self.currentItemId())


    @pyqtSignature('int')
    def on_cmbPost_currentIndexChanged(self, index):
        if self.chkPost.isChecked():
            self.renewListAndSetTo(self.currentItemId())


    @pyqtSignature('int')
    def on_chkPost_stateChanged(self, state):
        self.renewListAndSetTo(self.currentItemId())


    @pyqtSignature('int')
    def on_chkSurname_stateChanged(self, state):
        self.renewListAndSetTo(self.currentItemId())


    @pyqtSignature('QString')
    def on_edtSurname_textChanged(self, text):
        if self.chkSurname.isChecked():
            self.renewListAndSetTo(self.currentItemId())
    
    
    @pyqtSignature('int')
    def on_chkSNILS_stateChanged(self, state):
        self.renewListAndSetTo(self.currentItemId())


    @pyqtSignature('QString')
    def on_edtSNILS_textChanged(self, text):
        if self.chkSNILS.isChecked():
            self.renewListAndSetTo(self.currentItemId())


    @pyqtSignature('QString')
    def on_edtUserLogin_textChanged(self, text):
        if self.chkUserLogin.isChecked():
            self.renewListAndSetTo(self.currentItemId())


    @pyqtSignature('int')
    def on_btnPrint_printByTemplate(self, templateId):
        tbl = self.tblItems
        model = tbl.model()
        if templateId == -1:
            doc = QtGui.QTextDocument()
            cursor = QtGui.QTextCursor(doc)
            cursor.setCharFormat(CReportBase.ReportTitle)
            cursor.insertText(u'Сотрудники\n')
            cursor.insertBlock()
            cursor.setCharFormat(CReportBase.ReportBody)
            if self.chkOnlyOwn.isChecked():
                cursor.insertText(u'Только свои\n')
            if self.chkOnlyWorking.isChecked():
                cursor.insertText(u'Только работающие\n')
            if self.chkOnlyRetired.isChecked():
                cursor.insertText(u'Только уволенные\n')
            if self.chkStrPodr.isChecked():
                cursor.insertText(u'Структурное подразделение: %s\n' % self.boxStrPodr.currentText())
            if self.chkSpec.isChecked():
                cursor.insertText(u'Специальность: %s\n' % self.boxSpec.currentText())
            if self.chkActivity.isChecked():
                cursor.insertText(u'Вид деятельности: %s\n' % self.cmbActivity.currentText())
            if self.chkLPU.isChecked():
                cursor.insertText(u'Внешнее ЛПУ: %s\n' % self.boxLPU.currentText())
            if self.chkUserRightsProfile.isChecked():
                cursor.insertText(u'Профиль прав: %s\n' % self.cmbUserRightsProfile.currentText())
            if self.chkUserLogin.isChecked():
                cursor.insertText(u'Регистрационное имя: %s\n' % self.edtUserLogin.text())
            cursor.insertBlock()
            cols = model.cols()
            colWidths = [tbl.columnWidth(i) for i in xrange(len(cols))]
            colWidths.insert(0, 10)
            totalWidth = sum(colWidths)
            tableColumns = []
            for iCol, colWidth in enumerate(colWidths):
                widthInPercents = str(max(1, colWidth*90/totalWidth))+'%'
                if iCol == 0:
                    tableColumns.append((widthInPercents, [u'№'], CReportBase.AlignRight))
                else:
                    col = cols[iCol-1]
                    colAlingment = Qt.AlignHorizontal_Mask & forceInt(col.alignment())
                    format = QtGui.QTextBlockFormat()
                    format.setAlignment(Qt.AlignmentFlag(colAlingment))
                    tableColumns.append((widthInPercents, [forceString(col.title())], format))
            table = createTable(cursor, tableColumns)
            for iModelRow in xrange(model.rowCount()):
                iTableRow = table.addRow()
                table.setText(iTableRow, 0, iModelRow+1)
                for iModelCol in xrange(len(cols)):
                    index = model.createIndex(iModelRow, iModelCol)
                    text = forceString(model.data(index))
                    table.setText(iTableRow, iModelCol+1, text)
            html = doc.toHtml('utf-8')
            view = CReportViewDialog(self)
            view.setText(html)
            view.exec_()
        else:
            context = CInfoContext()
            orgStructureIdList = []
            if self.chkStrPodr.isChecked():
                orgStructureId = self.boxStrPodr.value()
                orgStructureIdList = getOrgStructureDescendants(orgStructureId) if orgStructureId else []
            specialityType = 0
            specialityId = None
            if self.chkSpec.isChecked():
                index = self.boxSpec.currentIndex()
                if index == 0:
                    specialityType = 1  # Без специальности (speciality_id IS NULL)
                elif index == 1:
                    specialityType = 2  # Любая специальность (speciality_id IS NOT NULL)
                else:
                    specialityId = self.specialityList[index]
            activityType = 0
            activityId = None
            if self.chkActivity.isChecked():
                index = self.cmbActivity.currentIndex()
                if index == 0:
                    activityType = 1  # Без вида деятельности (NOT EXISTS(SELECT id FROM Person_Activity WHERE master_id = Person.id AND deleted = 0))
                elif index == 1:
                    activityType = 2  # Любой вид деятельности (EXISTS(SELECT id FROM Person_Activity WHERE master_id = Person.id AND activity_id IS NOT NULL AND deleted = 0))
                else:
                    activityId = self.activityList[index]  # (EXISTS(SELECT id FROM Person_Activity WHERE master_id = Person.id AND activity_id = %s AND deleted = 0))%(str(activityId))
            orgId = None
            if self.chkLPU.isChecked():
                orgId = self.LPUList[self.boxLPU.currentIndex()]
            userProfileType = 0
            userProfileId = None
            if self.chkUserRightsProfile.isChecked():
                userProfileId = self.cmbUserRightsProfile.value()
                if userProfileId:
                    if userProfileId == -1:  # Все (userProfile_id IS NOT NULL)
                        userProfileType = 1
                        userProfileId = None
            userLogin = u''
            if self.chkUserLogin.isChecked():
                userLogin = trim(self.edtUserLogin.text())
            personInfoList = context.getInstance(CPersonInfoListEx, model.idList())
            data = {
                    'isOnlyOwn':           self.chkOnlyOwn.isChecked(),  # Только свои (org_id = QtGui.qApp.currentOrgId())
                    'isOnlyWorking':       self.chkOnlyWorking.isChecked(),  # Только работающие (retireDate IS NULL)
                    'isOnlyRetired':       self.chkOnlyRetired.isChecked(),  # Только уволенные (retireDate IS NOT NULL)
                    'isChairPerson':       self.chkChairPerson.isChecked(),  # Председатель ВК (chairPerson = 1)
                    'orgStructureIdList':  context.getInstance(COrgStructureInfoList, orgStructureIdList),  # Структурное подразделение
                    'specialityType':      specialityType,  # Специальность 0:'Не задано', 1:'Без специальности', 2:'Любая специальность'
                    'specialityId':        context.getInstance(CSpecialityInfo, specialityId),  # Специальность
                    'activityType':        activityType,  # Вид деятельности 0:'Не задано', 1:'Без вида деятельности', 2:'Любой вид деятельности'
                    'activityId':          context.getInstance(CActivityInfo, activityId),  # Вид деятельности
                    'orgId':               context.getInstance(COrgInfo, orgId),  # Внешнее ЛПУ
                    'userProfileType':     userProfileType,  # Профиль прав 0:'Не задано', 1:'Все'
                    'userProfileId':       context.getInstance(CUserProfileInfo, userProfileId),  # Профиль прав
                    'userLogin':           userLogin,  # Регистрационное имя (login = addDotsEx(userLogin))
                    'personInfoList':      personInfoList,  # Список сотрудников из таблицы
                    }
            QtGui.qApp.call(self, applyTemplate, (self, templateId, data))

    def setSort(self, col):
        name = self.model.cols()[col].fields()[0]
        self.order = name
        if self.order == u'post_id':
            self.order = u' (select rbPost.name from rbPost where rbPost.id = Person.post_id) '
        elif self.order == u'speciality_id':
            self.order = u' (select rbSpeciality.name from rbSpeciality where rbSpeciality.id = Person.speciality_id) '
        elif self.order == u'userProfile_id':
            self.order = u' (select rbUserProfile.name from rbUserProfile where rbUserProfile.id = Person.userProfile_id) '
        elif self.order == u'orgStructure_id':
            self.order = u' (select OrgStructure.name from OrgStructure where OrgStructure.id = Person.orgStructure_id) '
        header = self.tblItems.horizontalHeader()
        header.setSortIndicatorShown(True)
        self.isAscending = not self.isAscending
        header.setSortIndicator(col, Qt.AscendingOrder if self.isAscending else Qt.DescendingOrder)
        if self.isAscending:
            self.order = self.order + u' ASC'
        else:
            self.order = self.order + u' DESC'
        self.renewListAndSetTo(self.currentItemId())


class CSNILSCol(CTextCol):
    def format(self, values):
        val = unicode(values[0].toString())
        return QVariant(formatSNILS(val))

#
# ##########################################################################
#

class CMultiplePersonEditor(Ui_MultiplePersonEditorDialog, CDialogBase, CRecordLockMixin):
    def __init__(self, parent=None):
        CDialogBase.__init__(self, parent)
        CRecordLockMixin.__init__(self)
        self.setupUi(self)
        self.cmbUserRightsProfile.setTable('rbUserProfile')
        self.cmbUserRightsProfile.setFilter('deleted=0')
        self.edtLastAccessibleTimelineDate.setDate(QDate())
        self._recordList = []
        self._tableName = 'Person'


    def setRecordList(self, recordList):
        self._recordList = recordList
        self.setRecord(recordList[0])
        availableForExternal = (self.cmbAvailableForExternal.currentIndex() == 1)
        isDoctor = True
        for rec in recordList:
            isDoctor = isDoctor and rec.value('speciality_id').toBool()
        self.chkAvailableForExternal.setEnabled(isDoctor)
        self.chkLastAccessibleTimelineDate.setEnabled(isDoctor)
        self.chkPrimaryQuota.setEnabled(isDoctor)
        self.chkOwnQuota.setEnabled(isDoctor)
        self.chkConsultancyQuota.setEnabled(isDoctor)
        self.chkExternalQuota.setEnabled(isDoctor and availableForExternal)


    def setRecord(self, record):
        setRBComboBoxValue(self.cmbUserRightsProfile,  record,  'userProfile_id')
        setComboBoxValue(self.cmbAvailableForExternal, record, 'availableForExternal')
        setComboBoxValue(self.cmbIsHideQueue, record, 'isHideQueue')
        setComboBoxValue(self.cmbIsHideSchedule, record, 'isHideSchedule')
        setDateEditValue(self.edtLastAccessibleTimelineDate, record, 'lastAccessibleTimelineDate')
        setSpinBoxValue(self.edtTimelineAccessibilityDays, record, 'timelineAccessibleDays')
        setSpinBoxValue(self.edtPrimaryQuota,     record, 'primaryQuota')
        setSpinBoxValue(self.edtOwnQuota,         record, 'ownQuota')
        setSpinBoxValue(self.edtConsultancyQuota, record, 'consultancyQuota')
        setSpinBoxValue(self.edtExternalQuota,    record, 'externalQuota')
        setComboBoxValue(self.cmbShowTypeTemplate,record, 'showTypeTemplate')


    def getRecord(self, index=0):
        record = self._recordList[index]
        if self.chkUserRightsProfile.isChecked():
            getRBComboBoxValue(self.cmbUserRightsProfile, record,  'userProfile_id')
        if self.chkAvailableForExternal.isChecked():
            getComboBoxValue(self.cmbAvailableForExternal, record, 'availableForExternal')
        if self.chkIsHideQueue.isChecked():
            getComboBoxValue(self.cmbIsHideQueue, record, 'isHideQueue')
        if self.chkIsHideSchedule.isChecked():
            getComboBoxValue(self.cmbIsHideSchedule, record, 'isHideSchedule')
        if self.chkLastAccessibleTimelineDate.isChecked():
            getDateEditValue(self.edtLastAccessibleTimelineDate, record, 'lastAccessibleTimelineDate')
        if self.chkTimelineAccessibilityDays.isChecked():
            getSpinBoxValue(self.edtTimelineAccessibilityDays, record, 'timelineAccessibleDays')
        if self.chkPrimaryQuota.isChecked():
            getSpinBoxValue(self.edtPrimaryQuota, record, 'primaryQuota')
        if self.chkOwnQuota.isChecked():
            getSpinBoxValue(self.edtOwnQuota, record, 'ownQuota')
        if self.chkConsultancyQuota.isChecked():
            getSpinBoxValue(self.edtConsultancyQuota, record, 'consultancyQuota')
        if self.chkExternalQuota.isChecked():
            getSpinBoxValue(self.edtExternalQuota, record, 'externalQuota')
        if self.chkShowTypeTemplate.isChecked():
            getComboBoxValue(self.cmbShowTypeTemplate, record, 'showTypeTemplate')
        return record


    def exec_(self, idList):
        self.lockList(self._tableName, idList)
        if self.locked():
            try:
                if idList:
                    db = QtGui.qApp.db
                    table = db.table('Person')
                    recordList = db.getRecordList(table, '*', table['id'].inlist(idList))
                    self.setRecordList(recordList)
                return CDialogBase.exec_(self)
            finally:
                self.releaseLock()
        else:
            return QtGui.QDialog.Rejected


    def save(self):
        try:
            db = QtGui.qApp.db
            db.transaction()
            try:
                for i in xrange(len(self._recordList)):
                    record = self.getRecord(i)
                    db.insertOrUpdate(db.table(self._tableName), record)
                db.commit()
            except:
                db.rollback()
                raise
        except Exception, e:
            QtGui.qApp.logCurrentException()
            QtGui.QMessageBox().critical(self, u'', exceptionToUnicode(e), QtGui.QMessageBox.Close)


class CPersonEditor(Ui_ItemEditorDialog, CItemEditorBaseDialog):
    prevAddress = None

    def __init__(self,  parent):
        CItemEditorBaseDialog.__init__(self, parent, 'Person')

        self.__regAddressRecord = None
        self.__regAddress = None
        self.__locAddressRecord = None
        self.__locAddress = None
        self.__documentRecord = None

        self.addModels('EducationDocs',  CEducationDocsModel(self))
        self.addModels('OrderDocs',      COrderDocsModel(self))
        self.addModels('PersonActivity', CPersonActivityModel(self))
        self.addModels('PersonJobType',  CPersonJobTypeModel(self))
        self.addModels('TimeTable',      CPersonTimeTableModel(self))
        self.addModels('PersonContacts', CPersonContactsModel(self))
        self.addModels('Identification', CIdentificationModel(self, 'Person_Identification', 'Person'))
        self.addModels('CombinedArea',   CCombinedAreaModel(self))

        self.setupUi(self)

        self.setWindowTitleEx(u'Сотрудник')
        self.edtBirthDate.setHighlightRedDate(False)
        self.cmbPost.setTable('rbPost')
        self.cmbSpeciality.setTable('rbSpeciality')
        self.cmbTariffCategory.setTable('rbTariffCategory')
        self.cmbFinance.setTable('rbFinance')
        self.cmbOrg.setValue(QtGui.qApp.currentOrgId())
        self.edtRetireDate.setDate(QDate())
        self.edtLastAccessibleTimelineDate.setDate(QDate())
        self.chkChangePassword.setChecked(False)
        self.edtPassword.setEnabled(False)
        self.cmbUserRightsProfile.setTable('rbUserProfile')
        self.cmbUserRightsProfile.setFilter('deleted=0')
        self.btnCopyPrevAddress.setEnabled(bool(CPersonEditor.prevAddress))
        self.cmbDocType.setTable('rbDocumentType', True, 'group_id IN (SELECT id FROM rbDocumentTypeGroup WHERE code=\'1\')')
        if QtGui.qApp.defaultKLADR()[:2] == u'23':
            self.chkAvailableForStand.setVisible(False)
            self.chkAvailableForSuspendedAppointment.setVisible(False)
        else:
            self.chkAvailableForStand.setVisible(True)
            self.chkAvailableForSuspendedAppointment.setVisible(True)

#        self.tblCombinedArea.setModel(self.__modelSortCombinedArea)
        self.setModels(self.tblEducationDocs,  self.modelEducationDocs,  self.selectionModelEducationDocs)
        self.setModels(self.tblOrderDocs,      self.modelOrderDocs,      self.selectionModelOrderDocs)
        self.setModels(self.tblPersonActivity, self.modelPersonActivity, self.selectionModelPersonActivity)
        self.setModels(self.tblPersonJobType,  self.modelPersonJobType,  self.selectionModelPersonJobType)
        self.setModels(self.tblTimeTable,      self.modelTimeTable,      self.selectionModelTimeTable)
        self.setModels(self.tblPersonContacts, self.modelPersonContacts, self.selectionModelPersonContacts)
        self.setModels(self.tblIdentification, self.modelIdentification, self.selectionModelIdentification)
        self.setModels(self.tblCombinedArea,   self.modelCombinedArea, self.selectionModelCombinedArea)
        
        self.tblEducationDocs.addPopupDelRow()
        self.tblEducationDocs.addPopupRecordProperies()
        self.tblEducationDocs.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.tblPersonJobType.addPopupDelRow()
        self.tblPersonContacts.addPopupDelRow()
        self.tblIdentification.addPopupDelRow()
        self.tblIdentification.setDelRowsChecker(self.modelIdentification.delRowsChecker)
        self.tblCombinedArea.addPopupDelRow()

        self.modelTimeTable.setPeriod(0, 1) # для новой записи
        self.setupDirtyCather()
        self.setLoginPasswordProfileEnable()
        self.modelCombinedArea.setEventEditor(self)
        self.modelCombinedArea.setCurrentAreaId(self.cmbOrgStructure.value())

        self.lblLogin.setVisible(False)
        self.edtLogin.setVisible(False)
        self.chkChangePassword.setVisible(False)
        self.edtPassword.setVisible(False)

        self.orderDocId = None


    def setLoginPasswordProfileEnable(self):
        isEnable = QtGui.qApp.userHasAnyRight([urEditLoginPasswordProfileUser])
        # self.edtLogin.setEnabled(isEnable)
        # self.chkChangePassword.setEnabled(isEnable)
        # self.edtPassword.setEnabled(isEnable)
        self.cmbUserRightsProfile.setEnabled(isEnable)


    def destroy(self):
        pass

    def checkPersonOrderDocsMoving(self):
        is_uncorrect_row = False
        for indx in range(self.modelOrderDocs.items().__len__()):
            if self.modelOrderDocs.value( indx,'type').toString() == u'6':
                if not ((self.modelOrderDocs.value(indx, 'post_id').toString() != u'0' \
                         and self.modelOrderDocs.value(indx, 'post_id').toString() != u'') \
                        and (self.modelOrderDocs.value( indx,'orgStructure_id').toString() != u'0' \
                                and self.modelOrderDocs.value( indx,'orgStructure_id').toString() != u'')):
                    is_uncorrect_row = True
                    self.checkValueMessage(u'Для типа перемещения "Прикрепление к участку" обязательно указание '
                                           u'Должности и Подразделения', False,\
                                           self.tblOrderDocs)
                    break

        return is_uncorrect_row

    # WTF? свой save - так неожиданно...
    def save(self):
        try:
            db = QtGui.qApp.db
            db.transaction()
            try:
                record = self.getRecord()
                id = db.insertOrUpdate('Person', record)
                regAddressRecord, regAddress, regAddressRecordChanged = self.getAddressRecord(id, 0)
                if regAddressRecordChanged and regAddressRecord is not None:
                    db.insertOrUpdate('Person_Address', regAddressRecord)
                locAddressRecord, locAddress, locAddressRecordChanged = self.getAddressRecord(id, 1)
                if locAddressRecordChanged and locAddressRecord is not None:
                    db.insertOrUpdate('Person_Address', locAddressRecord)
                documentRecord, documentRecordChanged = self.getDocumentRecord(id)
                if documentRecordChanged and documentRecord is not None:
                    db.insertOrUpdate('Person_Document', documentRecord)
                try:
                    self.modelEducationDocs.saveItems(id)
                    self.modelOrderDocs.saveItems(id)
                    self.modelPersonActivity.saveItems(id)
                    self.modelPersonJobType.saveItems(id)
                    self.modelTimeTable.saveItems(id)
                    self.modelPersonContacts.saveItems(id)
                    self.modelIdentification.saveItems(id)
                    self.modelCombinedArea.saveItems(id)
                    if not forceRef(record.value('userProfile_id')):
                        tableLoginPerson = db.table('Login_Person')
                        db.deleteRecordSimple(tableLoginPerson, tableLoginPerson['person_id'].eq(id))
                    db.commit()
                except UserWarning:
                    db.rollback()
                    return None
            except:
                db.rollback()
                QtGui.qApp.logCurrentException()
                raise
            self.setItemId(id)
            self.__regAddressRecord = regAddressRecord
            self.__regAddress = regAddress
            self.__locAddressRecord = locAddressRecord
            self.__locAddress = locAddress
            self.__documentRecord = documentRecord
            self.setIsDirty(False)
            CPersonEditor.prevAddress = (regAddress, forceStringEx(regAddressRecord.value('freeInput')), locAddress)
            return id

        except Exception, e:
            QtGui.qApp.logCurrentException()
            QtGui.QMessageBox().critical(self,
                                         u'',
                                         exceptionToUnicode(e),
                                         QtGui.QMessageBox.Close)
            return None


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        id = self.itemId()
        setLineEditValue(self.edtLastName,     record, 'lastName')
        setLineEditValue(self.edtFirstName,    record, 'firstName')
        setLineEditValue(self.edtPatrName,     record, 'patrName')
        setLineEditValue(self.edtCode,         record, 'code')
        setLineEditValue(self.edtFederalCode,  record, 'federalCode')
        setLineEditValue(self.edtRegionalCode, record, 'regionalCode')
        setRBComboBoxValue(self.cmbOrg,        record, 'org_id')
        setRBComboBoxValue(self.cmbOrgStructure,  record, 'orgStructure_id')
        setRBComboBoxValue(self.cmbPost,       record, 'post_id')
        setRBComboBoxValue(self.cmbSpeciality, record, 'speciality_id')
        setLineEditValue(self.edtAcademicDegree, record, 'academicDegree')
        setLineEditValue(self.edtMedicalCategory, record, 'medicalCategory')
        setLineEditValue(self.edtOffice,       record, 'office')
        setLineEditValue(self.edtOffice2,      record, 'office2')
        setRBComboBoxValue(self.cmbTariffCategory,    record, 'tariffCategory_id')
        setRBComboBoxValue(self.cmbFinance,    record, 'finance_id')
        setLineEditValue(self.edtLogin,        record, 'login')
        setRBComboBoxValue(self.cmbUserRightsProfile,  record,  'userProfile_id')
        setDateEditValue(self.edtRetireDate,   record, 'retireDate')
        setCheckBoxValue(self.chkRetired,      record, 'retired')
        setCheckBoxValue(self.chkChairPerson,  record, 'chairPerson')
        setCheckBoxValue(self.chkAvailableForExternal, record, 'availableForExternal')
        setCheckBoxValue(self.chkIsHideQueue, record, 'isHideQueue')
        setCheckBoxValue(self.chkIsHideSchedule, record, 'isHideSchedule')
        setCheckBoxValue(self.chkAvailableForStand, record, 'availableForStand')
        setCheckBoxValue(self.chkAvailableForSuspendedAppointment, record, 'availableForSuspendedAppointment')
        setDateEditValue(self.edtLastAccessibleTimelineDate, record, 'lastAccessibleTimelineDate')
        setSpinBoxValue(self.edtTimelineAccessibilityDays, record, 'timelineAccessibleDays')
        setSpinBoxValue(self.edtPrimaryQuota,  record, 'primaryQuota')
        setSpinBoxValue(self.edtOwnQuota,      record, 'ownQuota')
        setSpinBoxValue(self.edtConsultancyQuota,  record, 'consultancyQuota')
        setSpinBoxValue(self.edtExternalQuota,  record, 'externalQuota')

        self.edtBirthDate.setDate(forceDate(record.value('birthDate')))

        setLineEditValue(self.edtBirthPlace, record, 'birthPlace')
        setComboBoxValue(self.cmbSex, record, 'sex')
        setLineEditValue(self.edtSNILS, record, 'SNILS')
        setLineEditValue(self.edtINN, record, 'INN')

        setComboBoxValue(self.cmbTimelinePeriod,       record, 'timelinePeriod')
        setSpinBoxValue( self.edtTimelineCustomLength, record, 'timelineCustomLength')
        setCheckBoxValue(self.chkFillRedDays,    record, 'fillRedDays')
        setComboBoxValue(self.cmbShowTypeTemplate, record, 'showTypeTemplate')

        self.setRegAddressRecord(getPersonAddress(id, 0))
        self.setLocAddressRecord(getPersonAddress(id, 1))
        self.setDocumentRecord(getPersonDocument(id))
        self.modelCombinedArea.setCurrentAreaId(self.cmbOrgStructure.value())
        self.modelEducationDocs.loadItems(id)
        self.modelOrderDocs.loadItems(id)
        if self.orderDocId:
            orderDocsIdList = self.modelOrderDocs.itemIdList()
            row = orderDocsIdList.index(self.orderDocId) if self.orderDocId in orderDocsIdList else None
            if row:
                index = self.modelOrderDocs.index(row, 5)
                self.tblOrderDocs.setCurrentIndex(index)
        self.modelPersonJobType.loadItems(id)
        self.modelTimeTable.loadItems(id, self.cmbTimelinePeriod.currentIndex(), self.edtTimelineCustomLength.value())
        self.modelPersonActivity.loadItems(id)
        self.modelPersonContacts.loadItems(id)
        self.modelIdentification.loadItems(self.itemId())
        self.modelCombinedArea.loadItems(self.itemId())
        createPerson = forceString(QtGui.qApp.db.translate('vrbPerson', 'id', forceRef(record.value('createPerson_id')), 'name'))
        modifyPerson = forceString(QtGui.qApp.db.translate('vrbPerson', 'id', forceRef(record.value('modifyPerson_id')), 'name'))
        self.lblCreatePerson.setText(u'Автор и дата создания записи: %s, %s '%(createPerson, forceString(record.value('createDatetime'))))
        self.lblModifyPerson.setText(u'Автор и дата последнего изменения записи: %s, %s'%(modifyPerson, forceString(record.value('modifyDatetime'))))
        self.on_chkHideCombinedAreaInvalid_toggled(True)
        self.setIsDirty(False)


    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
#        getLineEditValue(self.edtLastName,     record, 'lastName')
#        getLineEditValue(self.edtFirstName,    record, 'firstName')
#        getLineEditValue(self.edtPatrName,     record, 'patrName')
        record.setValue('lastName',  toVariant(nameCase(forceStringEx(self.edtLastName.text()))))
        record.setValue('firstName', toVariant(nameCase(forceStringEx(self.edtFirstName.text()))))
        record.setValue('patrName',  toVariant(nameCase(forceStringEx(self.edtPatrName.text()))))
        getLineEditValue(self.edtCode,             record, 'code')
        getLineEditValue(self.edtFederalCode,      record, 'federalCode')
        getLineEditValue(self.edtRegionalCode,     record, 'regionalCode')
        getRBComboBoxValue(self.cmbOrg,            record, 'org_id')
        getRBComboBoxValue(self.cmbOrgStructure,   record, 'orgStructure_id')
        getRBComboBoxValue(self.cmbPost,           record, 'post_id')
        getRBComboBoxValue(self.cmbSpeciality,     record, 'speciality_id')
        getLineEditValue(self.edtOffice,           record, 'office')
        getLineEditValue(self.edtOffice2,          record, 'office2')
        getLineEditValue(self.edtAcademicDegree,   record, 'academicDegree')
        getLineEditValue(self.edtMedicalCategory,   record, 'medicalCategory')
        getRBComboBoxValue(self.cmbTariffCategory, record, 'tariffCategory_id')
        getRBComboBoxValue(self.cmbFinance,        record, 'finance_id')
        if QtGui.qApp.userHasAnyRight([urEditLoginPasswordProfileUser]):
            getLineEditValue(self.edtLogin,            record, 'login')
            if self.chkChangePassword.isChecked():
                encodedPassword = unicode(self.edtPassword.text()).encode('utf8')
                hashedPassword = hashlib.md5(encodedPassword).hexdigest()
                record.setValue('password', toVariant(hashedPassword))
            elif not self.itemId():
                hashedPassword = hashlib.md5('').hexdigest()
                record.setValue('password', toVariant(hashedPassword))
            else:
                record.remove(record.indexOf('password'))
            getRBComboBoxValue(self.cmbUserRightsProfile,  record,  'userProfile_id')
        getDateEditValue(self.edtRetireDate,   record, 'retireDate')
        getCheckBoxValue(self.chkRetired,      record, 'retired')
        getCheckBoxValue(self.chkChairPerson,  record, 'chairPerson')
        getCheckBoxValue(self.chkAvailableForExternal, record, 'availableForExternal')
        getCheckBoxValue(self.chkIsHideQueue, record, 'isHideQueue')
        getCheckBoxValue(self.chkIsHideSchedule, record, 'isHideSchedule')
        getCheckBoxValue(self.chkAvailableForStand, record, 'availableForStand')
        getCheckBoxValue(self.chkAvailableForSuspendedAppointment, record, 'availableForSuspendedAppointment')
        getDateEditValue(self.edtLastAccessibleTimelineDate, record, 'lastAccessibleTimelineDate')
        getSpinBoxValue(self.edtTimelineAccessibilityDays, record, 'timelineAccessibleDays')
        getSpinBoxValue(self.edtPrimaryQuota,  record, 'primaryQuota')
        getSpinBoxValue(self.edtOwnQuota,      record, 'ownQuota')
        getSpinBoxValue(self.edtConsultancyQuota,  record, 'consultancyQuota')
        getSpinBoxValue(self.edtExternalQuota,   record, 'externalQuota')
        getDateEditValue(self.edtBirthDate,      record, 'birthDate')
        getComboBoxValue(self.cmbTimelinePeriod, record, 'timelinePeriod')
        getSpinBoxValue( self.edtTimelineCustomLength, record, 'timelineCustomLength')
        getCheckBoxValue(self.chkFillRedDays,    record, 'fillRedDays')
        getComboBoxValue(self.cmbShowTypeTemplate, record, 'showTypeTemplate')
        getLineEditValue(self.edtBirthPlace,     record, 'birthPlace')
        record.setValue('sex',       toVariant(self.cmbSex.currentIndex()))
        record.setValue('SNILS',     toVariant(forceStringEx(self.edtSNILS.text()).replace('-','').replace(' ','')))
        getLineEditValue(self.edtINN, record, 'INN')
        return record


    def getAddress(self, addressType):
        if addressType == 0:
            return { 'useKLADR'         : self.chkRegKLADR.isChecked(),
                     'KLADRCode'        : self.cmbRegCity.code(),
                     'KLADRStreetCode'  : self.cmbRegStreet.code(),
                     'number'           : forceStringEx(self.edtRegHouse.text()),
                     'corpus'           : forceStringEx(self.edtRegCorpus.text()),
                     'flat'             : forceStringEx(self.edtRegFlat.text()),
                     'freeInput'        : forceStringEx(self.edtRegFreeInput.text())}
        else:
            return { 'useKLADR'         : True,
                     'KLADRCode'        : self.cmbLocCity.code(),
                     'KLADRStreetCode'  : self.cmbLocStreet.code(),
                     'number'           : forceStringEx(self.edtLocHouse.text()),
                     'corpus'           : forceStringEx(self.edtLocCorpus.text()),
                     'flat'             : forceStringEx(self.edtLocFlat.text()),
                     'freeInput'        : ''}



    def getAddressRecord(self,  personId, addressType):
        address = self.getAddress(addressType)
        if address['useKLADR']:
            addressId = getAddressId(address)
        else:
            addressId = None
        oldAddressRecord = self.__regAddressRecord if addressType == 0 else self.__locAddressRecord

        if oldAddressRecord:
            recordChanged = addressId != forceRef(oldAddressRecord.value('address_id')) or address['freeInput'] != forceString(oldAddressRecord.value('freeInput'))
        else:
            recordChanged = True

        if recordChanged:
            record = QtGui.qApp.db.record('Person_Address')
            record.setValue('master_id',  toVariant(personId))
            record.setValue('type',       toVariant(addressType))
            record.setValue('address_id', toVariant(addressId))
            record.setValue('freeInput',  toVariant(address['freeInput']))
        else:
            record = oldAddressRecord

        return record, address, recordChanged


    def setRegAddressRecord(self, record):
        self.__regAddressRecord = record
        if record:
            addressId = forceRef(record.value('address_id'))
#            self.chkRegKLADR.setChecked(addressId is not None)
            if addressId:
                self.__regAddress = getAddress(addressId)
            else:
                self.__regAddress = None
            self.setRegAddress(self.__regAddress, forceString(record.value('freeInput')))
        else:
            self.chkRegKLADR.setChecked(False)
            self.__regAddress = None
            self.setRegAddress(self.__regAddress, '')


    def setRegAddress(self, regAddress, freeInput):
        self.chkRegKLADR.setChecked(regAddress is not None)
        self.edtRegFreeInput.setText(freeInput)
        if regAddress:
            self.cmbRegCity.setCode(regAddress.KLADRCode)
            self.cmbRegStreet.setCity(regAddress.KLADRCode)
            self.cmbRegStreet.setCode(regAddress.KLADRStreetCode)
            self.edtRegHouse.setText(regAddress.number)
            self.edtRegCorpus.setText(regAddress.corpus)
            self.edtRegFlat.setText(regAddress.flat)
        else:
            self.cmbRegCity.setCode(QtGui.qApp.defaultKLADR())
            self.cmbRegStreet.setCity(QtGui.qApp.defaultKLADR())
            self.cmbRegStreet.setCode('')
            self.edtRegHouse.setText('')
            self.edtRegCorpus.setText('')
            self.edtRegFlat.setText('')


    def setLocAddressRecord(self, record):
        self.__locAddressRecord = record
        if record:
            addressId = forceRef(record.value('address_id'))
            self.__locAddress = getAddress(addressId)
        else:
            self.__locAddress = None
        self.setLocAddress(self.__locAddress)


    def setLocAddress(self, locAddress):
        if locAddress:
            self.cmbLocCity.setCode(locAddress.KLADRCode)
            self.cmbLocStreet.setCity(locAddress.KLADRCode)
            self.cmbLocStreet.setCode(locAddress.KLADRStreetCode)
            self.edtLocHouse.setText(locAddress.number)
            self.edtLocCorpus.setText(locAddress.corpus)
            self.edtLocFlat.setText(locAddress.flat)
        else:
            self.cmbLocCity.setCode(QtGui.qApp.defaultKLADR())
            self.cmbLocStreet.setCity(QtGui.qApp.defaultKLADR())
            self.cmbLocStreet.setCode('')
            self.edtLocHouse.setText('')
            self.edtLocCorpus.setText('')
            self.edtLocFlat.setText('')


    def getDocumentRecord(self, personId):
        docTypeId = self.cmbDocType.value()
        serialLeft = forceStringEx(self.edtDocSerialLeft.text())
        serialRight = forceStringEx(self.edtDocSerialRight.text())
        serial = serialLeft + ' ' + serialRight
        number = forceStringEx(self.edtDocNumber.text())
        origin = forceStringEx(self.edtDocOrigin.text())
        date = forceDate(self.edtDocDate.date())
        if docTypeId in (0, None):
            record = None
            recordChanged = self.__documentRecord is not None
        else:
            if self.__documentRecord is not None:
                recordChanged = (
                    docTypeId != forceRef(self.__documentRecord.value('documentType_id')) or
                    serial != forceString(self.__documentRecord.value('serial')) or
                    number != forceString(self.__documentRecord.value('number')) or
                    origin != forceString(self.__documentRecord.value('origin')) or
                    date != forceDate(self.__documentRecord.value('date'))
                    )
            else:
                recordChanged = True

            if recordChanged:
                record = QtGui.qApp.db.record('Person_Document')
                record.setValue('master_id',       toVariant(personId))
                record.setValue('documentType_id', toVariant(docTypeId))
                record.setValue('serial',          toVariant(serial))
                record.setValue('number',          toVariant(number))
                record.setValue('origin',          toVariant(origin))
                record.setValue('date',             toVariant(date))
            else:
                record = self.__documentRecord

        return record, recordChanged


    def setDocumentRecord(self, record):
        self.__documentRecord = record
        if record:
            documentTypeId = forceInt(record.value('documentType_id'))
            self.cmbDocType.setValue(documentTypeId)
            documentTypeDescr = getDocumentTypeDescr(documentTypeId)
            serial = forceString(record.value('serial'))
            serialLeft, serialRight = documentTypeDescr.splitDocSerial(serial)
            self.edtDocSerialLeft.setText(serialLeft)
            self.edtDocSerialRight.setText(serialRight)
            self.edtDocNumber.setText(forceString(record.value('number')))
            self.edtDocOrigin.setText(forceString(record.value('origin')))
            self.edtDocDate.setDate(forceDate(record.value('date')))
        else:
            self.cmbDocType.setValue(None)
            self.edtDocSerialLeft.setText('')
            self.edtDocSerialRight.setText('')
            self.edtDocNumber.setText('')
            self.edtDocOrigin.setText('')
            self.edtDocDate.setDate(QDate())


    def checkDataEntered(self):
        result = True
        code = forceStringEx(self.edtCode.text())
        name = forceStringEx(self.edtLastName.text())
        # login = forceStringEx(self.edtLogin.text())
        result = result and (code or self.checkInputMessage(u'код', False, self.edtCode))
        result = result and (name or self.checkInputMessage(u'Фамилия', False, self.edtLastName))
        result = result and (isNameValid(name, True) or self.checkInputMessage(u'допустимую фамилию', False, self.edtLastName))
        result = result and (forceStringEx(self.edtFirstName.text()) or self.checkInputMessage(u'имя', False, self.edtFirstName))
        result = result and (isNameValid(self.edtFirstName.text()) or self.checkInputMessage(u'допустимое имя', False, self.edtFirstName))
        result = result and (forceStringEx(self.edtPatrName.text()) or self.checkInputMessage(u'отчество', True, self.edtPatrName))
        result = result and (isNameValid(self.edtPatrName.text()) or self.checkInputMessage(u'допустимое отчество', False, self.edtPatrName))
        # result = result and (login or self.checkInputMessage(u'регистрационное имя', True, self.edtLogin))
        # if result and login:
        #     db = QtGui.qApp.db
        #     table = db.table('Person')
        #     idList = db.getIdList(table,  'id',  table['login'].eq(login))
        #     if idList and idList != [self.itemId()]:
        #         QtGui.QMessageBox.warning(   self,
        #                                      u'Внимание!',
        #                                      u'Регистрационное имя "%s" уже занято' % login,
        #                                      QtGui.QMessageBox.Ok,
        #                                      QtGui.QMessageBox.Ok)
        #         self.edtLogin.setFocus(Qt.OtherFocusReason)
        #         result = False
        result = result and (self.cmbUserRightsProfile.value() or self.checkInputMessage(u'Профиль', True, self.cmbUserRightsProfile))

        if self.cmbSpeciality.value():
            sumQuota = self.edtPrimaryQuota.value()+self.edtOwnQuota.value()+self.edtConsultancyQuota.value()
            if self.chkAvailableForExternal.isChecked():
                sumQuota += self.edtExternalQuota.value()
            result = result and (sumQuota >= 100 or self.checkValueMessage(u'Сумма квот должна быть не менее 100%', True, self.edtPrimaryQuota))
        result = result and checkSNILSEntered(self)
        result = result and self.checkCombinedAreaPeriods()
        result = result and checkIdentification(self, self.tblIdentification)
        result = result and (not self.checkPersonOrderDocsMoving())
        return result


    def checkCombinedAreaPeriods(self):
        result = True
        self.cache = {}
        db = QtGui.qApp.db
        tableOrgStructure = db.table('OrgStructure')
        items = self.modelCombinedArea._items
        items2 = self.modelCombinedArea._items
        for row, item in enumerate(items):
            begDate = forceDate(item.value('begDate'))
            endDate = forceDate(item.value('endDate'))
            orgStructureId = forceRef(item.value('orgStructure_id'))
            periodBegDate = forceString(begDate)
            periodEndDate = forceString(endDate)
            result = result and (begDate or self.checkValueMessage(u'Укажите дату начала периода совмещения период с %s по %s'%(periodBegDate, periodEndDate), False, self.tblCombinedArea, row, item.indexOf('begDate')))
            for row2, item2 in enumerate(items2):
                if row != row2:
                    begDate2 = forceDate(item2.value('begDate'))
                    endDate2 = forceDate(item2.value('endDate'))
                    orgStructureId2 = forceRef(item2.value('orgStructure_id'))
                    periodBegDate2 = forceString(begDate2)
                    periodEndDate2 = forceString(endDate2)
                    if begDate:
                        if orgStructureId == orgStructureId2 and ((not begDate2 or begDate2 <= begDate) and (not endDate2 or endDate2 >= begDate)):
                            combinedAreaName = self.cache.get(orgStructureId, u'')
                            if not combinedAreaName and orgStructureId:
                                recordName = db.getRecordEx(tableOrgStructure, [tableOrgStructure['name']], [tableOrgStructure['id'].eq(orgStructureId), tableOrgStructure['deleted'].eq(0)])
                                combinedAreaName = forceStringEx(recordName.value('name')) if recordName else u''
                                self.cache[orgStructureId] = combinedAreaName
                            result = result and (self.checkValueMessage(u'Пересечение периода совмещения %s - %s с периодом совмещения %s - %s участок %s'%(periodBegDate, periodEndDate, periodBegDate2, periodEndDate2, combinedAreaName), False, self.tblCombinedArea, row, item.indexOf('begDate')))
                            break
                    if endDate:
                        if orgStructureId == orgStructureId2 and ((not endDate2 or endDate2 >= endDate) and (not begDate2 or begDate2 <= endDate)):
                            combinedAreaName = self.cache.get(orgStructureId, u'')
                            if not combinedAreaName and orgStructureId:
                                recordName = db.getRecordEx(tableOrgStructure, [tableOrgStructure['name']], [tableOrgStructure['id'].eq(orgStructureId), tableOrgStructure['deleted'].eq(0)])
                                combinedAreaName = forceStringEx(recordName.value('name')) if recordName else u''
                                self.cache[orgStructureId] = combinedAreaName
                            result = result and (self.checkValueMessage(u'Пересечение периода совмещения %s - %s с периодом совмещения %s - %s участок %s'%(periodBegDate, periodEndDate, periodBegDate2, periodEndDate2, combinedAreaName), False, self.tblCombinedArea, row, item.indexOf('endDate')))
                            break
        return result


    def updateSchedulePeriod(self):
        period       = self.cmbTimelinePeriod.currentIndex()
        customLength = self.edtTimelineCustomLength.value()
        self.modelTimeTable.setPeriod(period, customLength)


    def setOrderDocId(self, id):
        if id:
            self.orderDocId = id


    @pyqtSignature('int')
    def on_cmbOrg_currentIndexChanged(self, index):
        orgId = self.cmbOrg.value()
        self.cmbOrgStructure.setEnabled(bool(orgId))
        self.cmbOrgStructure.setOrgId(orgId)


    @pyqtSignature('int')
    def on_cmbOrgStructure_currentIndexChanged(self, index):
        self.modelCombinedArea.setCurrentAreaId(self.cmbOrgStructure.value())


    @pyqtSignature('int')
    def on_cmbTimelinePeriod_currentIndexChanged(self, index):
        enableCustomLength = index == 2
        self.lblTimelineCustomLength.setEnabled(enableCustomLength)
        self.edtTimelineCustomLength.setEnabled(enableCustomLength)
        self.updateSchedulePeriod()


    @pyqtSignature('int')
    def on_edtTimelineCustomLength_valueChanged(self, i):
        self.updateSchedulePeriod()


    @pyqtSignature('int')
    def on_cmbSpeciality_currentIndexChanged(self, index):
        isDoctor = bool(self.cmbSpeciality.value())
        isAvailableDoctor = isDoctor and self.chkAvailableForExternal.isChecked()
        self.chkAvailableForExternal.setEnabled(isDoctor)
        self.chkAvailableForSuspendedAppointment.setEnabled(isDoctor)
        self.edtLastAccessibleTimelineDate.setEnabled(isDoctor)
        self.edtTimelineAccessibilityDays.setEnabled(isDoctor)
        self.edtPrimaryQuota.setEnabled(isDoctor)
        self.edtOwnQuota.setEnabled(isDoctor)
        self.edtConsultancyQuota.setEnabled(isDoctor)
        self.edtExternalQuota.setEnabled(isAvailableDoctor)


    @pyqtSignature('int')
    def on_chkChangePassword_stateChanged(self, state):
        self.setIsDirty(True)


    @pyqtSignature('bool')
    def on_chkAvailableForExternal_toggled(self, checked):
        isDoctor = bool(self.cmbSpeciality.value())
        isAvailableDoctorDoctor = isDoctor and checked
        self.edtLastAccessibleTimelineDate.setEnabled(isDoctor)
        self.edtTimelineAccessibilityDays.setEnabled(isDoctor)
        self.edtExternalQuota.setEnabled(isAvailableDoctorDoctor)


    @pyqtSignature('int')
    def on_edtTimelineAccessibilityDays_valueChanged(self, value):
        self.lblTimelineAccessibilityDaysSuffix.setText(agreeNumberAndWord(value, (u'день', u'дня', u'дней')))


    @pyqtSignature('')
    def on_btnCopyPrevAddress_clicked(self):
        if CPersonEditor.prevAddress:
            reg, freeInput, loc = CPersonEditor.prevAddress
            self.setRegAddress(reg, freeInput)
            self.setLocAddress(loc)


    @pyqtSignature('bool')
    def on_chkRegKLADR_toggled(self, checked):
        self.edtRegFreeInput.setEnabled(not checked)
        self.cmbRegCity.setEnabled(checked)
        self.cmbRegStreet.setEnabled(checked)
        self.edtRegHouse.setEnabled(checked)
        self.edtRegCorpus.setEnabled(checked)
        self.edtRegFlat.setEnabled(checked)


    @pyqtSignature('int')
    def on_cmbRegCity_currentIndexChanged(self,  val):
        code = self.cmbRegCity.code()
        self.cmbRegStreet.setCity(code)


    @pyqtSignature('')
    def on_btnCopy_clicked(self):
        code = self.cmbRegCity.code()
        self.cmbLocCity.setCode(code)
        self.cmbLocStreet.setCity(code)
        self.cmbLocStreet.setCode(self.cmbRegStreet.code())
        self.edtLocHouse.setText(self.edtRegHouse.text())
        self.edtLocCorpus.setText(self.edtRegCorpus.text())
        self.edtLocFlat.setText(self.edtRegFlat.text())


    @pyqtSignature('int')
    def on_cmbLocCity_currentIndexChanged(self,  index):
        code = self.cmbLocCity.code()
        self.cmbLocStreet.setCity(code)


    @pyqtSignature('int')
    def on_cmbDocType_currentIndexChanged(self,  index):
        documentTypeId = self.cmbDocType.value()
        if documentTypeId:
            documentTypeDescr = getDocumentTypeDescr(documentTypeId)
            self.edtDocSerialLeft.setRegExp(documentTypeDescr.leftPartRegExp)
            self.edtDocSerialRight.setRegExp(documentTypeDescr.rightPartRegExp)
            self.edtDocNumber.setRegExp(documentTypeDescr.numberRegExp)
            enableDoc = True
            enableRightPart = documentTypeDescr.hasRightPart
        else:
            enableDoc = enableRightPart = False
        self.lblDocSerial.setEnabled(enableDoc)
        self.edtDocSerialLeft.setEnabled(enableDoc)
        self.edtDocSerialRight.setEnabled(enableRightPart)
        self.lblDocNumber.setEnabled(enableDoc)
        self.edtDocNumber.setEnabled(enableDoc)
        self.lblDocOrigin.setEnabled(enableDoc)
        self.edtDocOrigin.setEnabled(enableDoc)
        self.lblDocDate.setEnabled(enableDoc)
        self.edtDocDate.setEnabled(enableDoc)


    @pyqtSignature('bool')
    def on_chkHideCombinedAreaInvalid_toggled(self, checked):
        self.modelCombinedArea.setIsHideCombinedAreaInvalid(checked)
        currentDate = QDate.currentDate()
        items = self.modelCombinedArea.items()
        if checked:
            for row, item in enumerate(items):
                begDate = forceDate(item.value('begDate'))
                endDate = forceDate(item.value('endDate'))
                if not (((not begDate) or begDate <= currentDate) and ((not endDate) or endDate >= currentDate)):
                    self.tblCombinedArea.hideRow(row)
        else:
            for row, item in enumerate(items):
                self.tblCombinedArea.showRow(row)


    @pyqtSignature('bool')
    def on_chkActual_toggled(self, checked):
        currentDate = QDate.currentDate()
        items = self.modelOrderDocs.items()
        if checked:
            for row, item in enumerate(items):
                validToDate = forceDate(item.value('validToDate'))
                if (not validToDate) or validToDate > currentDate:
                    pass
                else:
                    self.tblOrderDocs.hideRow(row)
        else:
            for row, item in enumerate(items):
                self.tblOrderDocs.showRow(row)


class CEducationDocsModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Person_Education', 'id', 'master_id', parent)
        # self.setFilter('documentType_id IN (SELECT rbDocumentType.id FROM rbDocumentType LEFT JOIN rbDocumentTypeGroup ON rbDocumentTypeGroup.id = rbDocumentType.group_id WHERE rbDocumentTypeGroup.code=\'3\')')
        self.setFilter('deleted = 0')
        self.addCol(CDateInDocTableCol(u'Дата',  'date', 15, canBeEmpty=True))
        self.addCol(CRBInDocTableCol(u'Специальность', 'speciality_id', 30, 'rbSpeciality'))
        self.addCol(CInDocTableCol(u'Статус', 'status', 30))
        self.addCol(CRBInDocTableCol(u'Тип документа', 'documentType_id', 30, 'rbDocumentType', filter='group_id IN (SELECT id FROM rbDocumentTypeGroup WHERE code=\'3\')'))
        self.addCol(CInDocTableCol(u'Серия', 'serial', 8))
        self.addCol(CInDocTableCol(u'Номер', 'number', 16))
        self.addCol(CInDocTableCol(u'Выдан', 'origin', 30))
        self.addCol(CDateInDocTableCol(u'Действителен с',  'validFromDate', 15, canBeEmpty=True))
        self.addCol(CDateInDocTableCol(u'Действителен по',  'validToDate', 15, canBeEmpty=True))


class COrderDocsModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Person_Order', 'id', 'master_id', parent)
        self.setFilter('documentType_id IN (SELECT rbDocumentType.id FROM rbDocumentType LEFT JOIN rbDocumentTypeGroup ON rbDocumentTypeGroup.id = rbDocumentType.group_id WHERE rbDocumentTypeGroup.code=\'4\') or documentType_id is null')
        self.addCol(CDateInDocTableCol(u'Дата',  'date', 15))
        self.addCol(CEnumInDocTableCol(u'Тип перемещения',  'type',  15,
            [u'Приём на работу', u'Увольнение', u'Назначение на должность',
             u'Отпуск', u'Учёба', u'Командировка', u'Прикрепление к участку'])).setSortable(True)
        self.addCol(CDateInDocTableCol(u'Дата',  'documentDate', 15))
        self.addCol(CInDocTableCol(u'Номер', 'documentNumber', 8))
        self.addCol(CRBInDocTableCol(u'Тип документа', 'documentType_id', 30, 'rbDocumentType', filter='group_id IN (SELECT id FROM rbDocumentTypeGroup WHERE code=\'4\')'))
        self.addCol(CDateInDocTableCol(u'Действителен с',  'validFromDate', 15, canBeEmpty=True))
        self.addCol(CDateInDocTableCol(u'Действителен по',  'validToDate', 15, canBeEmpty=True))
        self.addCol(CRBInDocTableCol(u'Должность', 'post_id', 30, 'rbPost'))
        self.addCol(COrgStructureInDocTableCol(u'Подразделение',  'orgStructure_id',  15,  'OrgStructure'))
        self.addCol(CInDocTableCol(u'Ставка', 'salary', 15))
        self.parent = parent

    def saveItems(self, masterId):
        if self._items is not None:
            db = QtGui.qApp.db
            table = self._table
            masterId = toVariant(masterId)
            masterIdFieldName = self._masterIdFieldName
            idFieldName = self._idFieldName
            idList = []
            try:
                if len(self.parent.parent().personItems) == 0:
                    self.parent.parent().personItems.append(forceInt(masterId))
            except:
                self.parent.parent().personItems = []
                self.parent.parent().personItems.append(forceInt(masterId))
            for idx, record in enumerate(self._items):

                record.setValue(masterIdFieldName, masterId)
                if self._idxFieldName:
                    record.setValue(self._idxFieldName, toVariant(idx))
                if self._extColsPresent:
                    outRecord = self.removeExtCols(record)
                else:
                    outRecord = record
                id = db.insertOrUpdate(table, outRecord)
                if forceString(record.value('type')) == '6':
                    if forceDate(record.value('validFromDate')):
                        isHigh = forceBool(QtGui.qApp.db.getRecordEx('rbSpeciality', 'isHigh', "id = '%s'" % (forceString(self.parent.cmbSpeciality.value()))).value(0))
                        if (not forceDate(record.value('validToDate')) or (forceDate(record.value('validToDate')) >= datetime.datetime.now().date())) and isHigh:
                            self.checkArea(record)
                    else:
                        QtGui.QMessageBox.critical(None,
                                                   u'Ошибка!',
                                                   u'Не заполнена дата "Действителен с"')
                        raise UserWarning
                record.setValue(idFieldName, toVariant(id))
                idList.append(id)
                self.saveDependence(idx, id)

            filter = [table[masterIdFieldName].eq(masterId),
                      'NOT (' + table[idFieldName].inlist(idList) + ')']
            if self._filter:
                filter.append(self._filter)
            db.deleteRecord(table, filter)

    def checkArea(self, record): 
        begDate = forceDate(record.value('validFromDate')).toString('yyyy-MM-dd')
        endDate = u'"' + forceDate(record.value('validToDate')).toString('yyyy-MM-dd') + u'"' if forceDate(
            record.value('validToDate')) else '   ADDDATE(CURDATE(), 36500  ) '
        recScene = QtGui.qApp.db.getRecordEx('Person_Order', 'id, master_id',
                                             "master_id <> %(master_id)s AND type=6 and (SELECT 1 FROM Person p INNER JOIN rbSpeciality s ON p.speciality_id = s.id  WHERE p.id = Person_Order.master_id AND p.deleted=0 AND isHigh=1) AND orgStructure_id = %(orgStructure_id)s AND deleted = 0 AND ((validToDate IS NULL and validFromDate BETWEEN '%(begDate)s' AND  %(endDate)s)  OR (validToDate IS NOT NULL AND (validFromDate BETWEEN '%(begDate)s' AND  %(endDate)s or validToDate BETWEEN '%(begDate)s' AND  %(endDate)s))) AND (validToDate IS NULL OR validToDate >= CURRENT_DATE()) " % {
                                                 'master_id': forceString(record.value('master_id')),
                                                 'orgStructure_id': forceString(record.value('orgStructure_id')),
                                                 'begDate': begDate, 'endDate': endDate})
        confirmation = 1
        if recScene:
            personOrderId = forceRef(recScene.value('id'))
            personId = forceInt(recScene.value('master_id'))
            person = forceString(QtGui.qApp.db.translate('Person', 'id', personId, 'formatPersonName(id)'))
            messageBox = QtGui.QMessageBox(QtGui.QMessageBox.Warning, u'Внимание', u'Обнаружено пересечение периода прикрепления к участку\nОткрыть карточку врача ' + person + '?')
            messageBox.addButton(u'Да', QtGui.QMessageBox.YesRole)
            messageBox.addButton(u'Отмена', QtGui.QMessageBox.NoRole)
            confirmation = messageBox.exec_()
            if confirmation == 0:
                QtGui.qApp.db.rollback()
                if personId not in self.parent.parent().personItems:
                    self.parent.parent().personItems.append(personId)
                    try:
                        dialog = self.parent.parent().getItemEditor()
                    except:
                        dialog = CPersonEditor(self.parent.parent())
                    try:
                        dialog.load(personId)
                        dialog.tblMain.setCurrentIndex(dialog.tblMain.indexOf(dialog.tabMovements))
                        dialog.setOrderDocId(forceRef(recScene.value('id')))
                        if dialog.exec_():
                            pass
                    finally:
                        self.parent.parent().personItems.remove(personId)
                        dialog.deleteLater()
                else:
                    QtGui.QMessageBox.information(None,
                                               u'Внмимание!',
                                               u'Карточка врача '+person+u' открыта ранее')
            raise UserWarning

class CPersonActivityModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Person_Activity', 'id', 'master_id', parent)
        self.addCol(CRBInDocTableCol(u'Вид деятельности', 'activity_id', 30, 'rbActivity'))


class CPersonJobTypeModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Person_JobType', 'id', 'master_id', parent)
        self.addCol(CRBInDocTableCol(u'Тип работы', 'jobType_id', 30, 'rbJobType'))


#FIXME: modeldatacache - отсутствует.
class COrgStructureInDocTableCol(CInDocTableCol):
    def __init__(self, title, fieldName, width, tableName, **params):
        CInDocTableCol.__init__(self, title, fieldName, width, **params)
        self.tableName  = tableName
        self.filter     = params.get('filter', '')
        self.preferredWidth = params.get('preferredWidth', None)
        self.orgStructureIdList = []


    def setOrgStructureIdList(self, orgStructureIdList):
        self.orgStructureIdList = orgStructureIdList


    def setFilter(self, filter):
        self.filter = filter


    def toString(self, val, record):
        from Orgs.Utils import getOrgStructureName
        return toVariant(getOrgStructureName(val))


    def toStatusTip(self, val, record):
        from Orgs.Utils import getOrgStructureFullName
        return toVariant(getOrgStructureFullName(val))


    def createEditor(self, parent):
        from Orgs.OrgStructComboBoxes import COrgStructureComboBox
        editor = COrgStructureComboBox(parent)
        editor.setFilter(self.filter)
        editor.setIsValidIdList(self.orgStructureIdList)
#        editor.setPreferredWidth(self.preferredWidth)
        return editor


    def setEditorData(self, editor, value, record):
        editor.setValue(forceInt(value))


    def getEditorData(self, editor):
        return toVariant(editor.value())


class CContactInDocTableCol(CInDocTableCol):
    def __init__(self, title, fieldName, width, **params):
        CInDocTableCol.__init__(self, title, fieldName, width, **params)
        self.recordContactTypeCache = params.get('contactTypeCaches', [])
        db = QtGui.qApp.db
        table = db.table('rbContactType')
        self._phoneNumberIdList = db.getDistinctIdList('rbContactType', 'id', [table['code'].inlist([1, 2, 3])])
#        self._emailIdList = db.getDistinctIdList('rbContactType', 'id', [table['code'].inlist([4])])


    def setEditorData(self, editor, value, record):
        editor.setText(forceStringEx(value))
        contactTypeId = forceRef(record.value('contactType_id'))
        if contactTypeId and self.recordContactTypeCache:
            contactTypeRecord = self.recordContactTypeCache.get(contactTypeId) if contactTypeId else None
            if contactTypeRecord:
                regExpValidator = forceString(contactTypeRecord.value('regExpValidator'))
                if regExpValidator:
                    if contactTypeId in self._phoneNumberIdList:
                        editor.setInputMask(regExpValidator)
                    else:
                        editor.setValidator((QtGui.QRegExpValidator(QRegExp(regExpValidator), None)))


class CPersonContactsModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Person_Contact', 'id', 'master_id', parent)
        db = QtGui.qApp.db
        contactTypeCaches = CTableRecordCache(db, db.forceTable('rbContactType'), u'*', capacity=None)
        self.addCol(CRBInDocTableCol(u'Тип', 'contactType_id', 30, 'rbContactType', addNone=False))
        self.addCol(CContactInDocTableCol(u'Номер', 'contact', 30, contactTypeCaches=contactTypeCaches))
        self.addCol(CInDocTableCol(u'Примечание', 'notes', 30))


class CCombinedAreaModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Person_CombinedArea', 'id', 'master_id', parent)
        self.addCol(CDateInDocTableCol(u'Дата начала', 'begDate', 15))
        self.addCol(CDateInDocTableCol(u'Дата окончания', 'endDate', 15))
        self.addCol(COrgStructureInDocTableCol(u'Подразделение', 'orgStructure_id', 15, 'OrgStructure'))
        self.currentAreaId = None
        self.eventEditor = None
        self.isHideCombinedAreaInvalid = False


    def setEventEditor(self, eventEditor):
        self.eventEditor = eventEditor


    def setIsHideCombinedAreaInvalid(self, isHideCombinedAreaInvalid):
        self.isHideCombinedAreaInvalid = isHideCombinedAreaInvalid


    def setData(self, index, value, role=Qt.EditRole):
        result = CInDocTableModel.setData(self, index, value, role=Qt.EditRole)
        if role == Qt.EditRole:
            column = index.column()
            if column in (self.getColIndex('begDate'), self.getColIndex('endDate')) and self.eventEditor:
                self.eventEditor.on_chkHideCombinedAreaInvalid_toggled(self.isHideCombinedAreaInvalid)
        return result


    def getEmptyRecord(self):
        result = CInDocTableModel.getEmptyRecord(self)
        result.setValue('begDate', toVariant(QDate.currentDate()))
        return result


    def setCurrentAreaId(self, currentAreaId):
        filter = u''
        self.currentAreaId = currentAreaId
        column = self.getColIndex('orgStructure_id')
        db = QtGui.qApp.db
        table = db.table('OrgStructure')
        cond = [table['areaType'].gt(0), table['deleted'].eq(0)]
        if self.currentAreaId:
            cond.append(table['id'].ne(self.currentAreaId))
        orgStructureIdList = db.getDistinctIdList(table, [table['id'].name()], cond)
        if orgStructureIdList:
            extOrgStructureIdList = db.getTheseAndParents('OrgStructure', 'parent_id', orgStructureIdList)
            if extOrgStructureIdList:
                filter = table['id'].inlist(extOrgStructureIdList)
        self._cols[column].setFilter(filter)


# #########################


def getPersonAddress(id, addrType):
    return selectLatestRecord('Person_Address', id, 'type=\'%d\'' % addrType)


def getPersonDocument(id):
    filter = '''Tmp.documentType_id IN (SELECT rbDocumentType.id FROM rbDocumentType LEFT JOIN rbDocumentTypeGroup ON rbDocumentTypeGroup.id=rbDocumentType.group_id WHERE rbDocumentTypeGroup.code = '1')'''
    return selectLatestRecord('Person_Document', id, filter)


def selectLatestRecordStmt(tableName, personId, filter=''):
    if type(tableName) == tuple:
        tableName1, tableName2 = tableName
    else:
        tableName1 = tableName
        tableName2 = tableName
    pos = tableName2.find('AS Tmp')
    if pos < 0:
        tableName2 = tableName2 + ' AS Tmp'

    if filter:
        filter = ' AND ('+filter+')'
    return u'SELECT * FROM %s AS Main WHERE Main.master_id = \'%d\' AND Main.id = (SELECT MAX(Tmp.id) FROM %s WHERE Tmp.master_id =\'%d\' %s)' % (tableName1, personId, tableName2, personId, filter)


def selectLatestRecord(tableName, personId, filter=''):
    stmt = selectLatestRecordStmt(tableName, personId, filter)
    query = QtGui.qApp.db.query(stmt)
    if query.next():
        return query.record()
    else:
        return None


def getPersonContext():
    return ['personRefBooks']


def getSamePersonIdList(personId):
    # Получить список Person.id с таким же СНИЛС как у заданного, или только заданный Person.id, если СНИЛС не введен
    stmt = '''
    select Person2.id
    from Person as Person1
        inner join Person as Person2 on Person2.SNILS = Person1.SNILS
    where Person1.id = %d and length(Person1.SNILS) = 11
    ''' % personId
    query = QtGui.qApp.db.query(stmt)
    result = []
    while query.next():
        result.append(forceRef(query.value(0)))
    if not result:
        result.append(personId)
    return result