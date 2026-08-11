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

import hashlib
from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QObject, pyqtSignature, SIGNAL, QVariant

from library.InDocTable          import CInDocTableModel
from library.database import CDatabaseException, CTableRecordCache
from library.interchange import  getLineEditValue, setLineEditValue, getTextEditValue, setTextEditValue
from library.ItemsListDialog     import CItemsListDialog, CItemEditorBaseDialog
from library.TableModel          import CTextCol
from library.Utils               import (
                                          addDotsEx,
                                          forceInt,
                                          forceRef,
                                          forceString,
                                          toVariant,
                                          trim,
                                        )
from library.PrintTemplates      import (
                                          getPrintButton,
                                          applyTemplate,
                                          CPrintAction,
                                          getPrintTemplates,
                                        )

from Orgs.PersonComboBoxEx import CPersonFindInDocTableCol, CPersonComboBoxEx
from Reports.ReportBase          import CReportBase, createTable
from Reports.ReportView          import CReportViewDialog

from Users.Tables import tblLogin

from Ui_LoginListDialog          import Ui_LoginListDialog
from RefBooks.Login.Ui_LoginEditor import Ui_ItemEditorDialog


class CLoginListDialog(Ui_LoginListDialog, CItemsListDialog):
    def __init__(self, parent):
        CItemsListDialog.__init__(self, parent, [
            CTextCol(u'Регистрационное имя', ['login'], 20),
            CTextCol(u'Примечание', ['note'], 20),
            ], tblLogin,
            ['login'])
        self.setWindowTitleEx(u'Учетные записи пользователей')

        QObject.connect(self.tblItems.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.setSort)
        templates = getPrintTemplates('loginRefBooks')
        if not templates:
            self.btnPrint.setId(-1)
        else:
            for template in templates:
                action = CPrintAction(template.name, template.id, self.btnPrint, self.btnPrint)
                self.btnPrint.addAction(action)
            self.btnPrint.menu().addSeparator()
            self.btnPrint.addAction(CPrintAction(u'Список "Учетные записи пользователей"', -1, self.btnPrint, self.btnPrint))
        self.btnPrint.setEnabled(True)
        self.tblItems.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.tblItems.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.order = None

        self.buttonBox.addButton(self.btnDelete, QtGui.QDialogButtonBox.ActionRole)
        self.btnFilter.setVisible(False)
        self.btnSelect.setVisible(False)


    def preSetupUi(self):
        self.addObject('btnPrint',  getPrintButton(self, '', u'Печать F6'))
        self.addObject('btnNew',    QtGui.QPushButton(u'Вставка F9', self))
        self.addObject('btnEdit',   QtGui.QPushButton(u'Правка F4', self))
        self.addObject('btnDelete', QtGui.QPushButton(u'Удалить', self))
        self.addObject('btnFilter', QtGui.QPushButton(u'Фильтр', self))
        self.addObject('btnSelect', QtGui.QPushButton(u'Выбор', self))


    @pyqtSignature('')
    def on_btnPrint_clicked(self):
        pass


    def getItemEditor(self):
        return CLoginEditor(self)

    def select(self, props):
        db = QtGui.qApp.db
        table = self.model.table()
        cond = [table['deleted'].eq(0)]

        if self.chkLastname.isChecked() or self.chkName.isChecked() \
                or self.chkSurname.isChecked() or self.chkSnils.isChecked():
            tablePerson = db.table('Person')
            tableLogin_Person = db.table('Login_Person').alias('lp')

            table = table.leftJoin(tableLogin_Person, tableLogin_Person['master_id'].eq(table['id']))
            table = table.leftJoin(tablePerson, tableLogin_Person['person_id'].eq(tablePerson['id']))
            cond.append(tablePerson['deleted'].eq(0))

        if self.chkLogin.isChecked():
            login = trim(self.edtLogin.text())
            cond.append(table['login'].like(addDotsEx(login)))

        if self.chkLastname.isChecked():
            lastname = trim(self.edtLastname.text())
            cond.append(tablePerson['lastName'].like(addDotsEx(lastname)))

        if self.chkName.isChecked():
            name = trim(self.edtName.text())
            cond.append(tablePerson['firstName'].like(addDotsEx(name)))

        if self.chkSurname.isChecked():
            surname = trim(self.edtSurname.text())
            cond.append(tablePerson['patrName'].like(addDotsEx(surname)))

        if self.chkSnils.isChecked():
            sninls = trim(self.edtSnils.text())
            cond.append(tablePerson['SNILS'].like(addDotsEx(sninls)))

        return QtGui.qApp.db.getDistinctIdList(table, '%s.id' % tblLogin, where=cond, order=self.order)


    @pyqtSignature('int')
    def on_chkLogin_stateChanged(self, state):
        self.renewListAndSetTo(self.currentItemId())

    @pyqtSignature('int')
    def on_chkLastname_stateChanged(self, state):
        self.renewListAndSetTo(self.currentItemId())

    @pyqtSignature('int')
    def on_chkName_stateChanged(self, state):
        self.renewListAndSetTo(self.currentItemId())

    @pyqtSignature('int')
    def on_chkSurname_stateChanged(self, state):
        self.renewListAndSetTo(self.currentItemId())

    @pyqtSignature('int')
    def on_chkSnils_stateChanged(self, state):
        self.renewListAndSetTo(self.currentItemId())


    @pyqtSignature('QString')
    def on_edtLogin_textChanged(self, text):
        if self.chkLogin.isChecked():
            self.renewListAndSetTo(self.currentItemId())

    @pyqtSignature('QString')
    def on_edtLastname_textChanged(self, text):
        if self.chkLastname.isChecked():
            self.renewListAndSetTo(self.currentItemId())

    @pyqtSignature('QString')
    def on_edtName_textChanged(self, text):
        if self.chkName.isChecked():
            self.renewListAndSetTo(self.currentItemId())

    @pyqtSignature('QString')
    def on_edtSurname_textChanged(self, text):
        if self.chkSurname.isChecked():
            self.renewListAndSetTo(self.currentItemId())

    @pyqtSignature('QString')
    def on_edtSnils_textChanged(self, text):
        if self.chkSnils.isChecked():
            self.renewListAndSetTo(self.currentItemId())


    @pyqtSignature('int')
    def on_btnPrint_printByTemplate(self, templateId):
        tbl = self.tblItems
        model = tbl.model()
        if templateId == -1:
            doc = QtGui.QTextDocument()
            cursor = QtGui.QTextCursor(doc)
            cursor.setCharFormat(CReportBase.ReportTitle)
            cursor.insertText(u'Учетные записи пользователей\n')
            cursor.insertBlock()
            cursor.setCharFormat(CReportBase.ReportBody)

            if self.chkLogin.isChecked():
                cursor.insertText(u'Регистрационное имя: %s\n' % self.edtLogin.text())
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
                    colAlignment = Qt.AlignHorizontal_Mask & forceInt(col.alignment())
                    colFormat = QtGui.QTextBlockFormat()
                    colFormat.setAlignment(Qt.AlignmentFlag(colAlignment))
                    tableColumns.append((widthInPercents, [forceString(col.title())], colFormat))
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
            login = u''
            if self.chkLogin.isChecked():
                login = trim(self.edtLogin.text())
            data = {'login': login}
            QtGui.qApp.call(self, applyTemplate, (self, templateId, data))


    def setSort(self, col):
        name = self.model.cols()[col].fields()[0]
        self.order = self.model.table().tableName + '.' + name
        header = self.tblItems.horizontalHeader()
        header.setSortIndicatorShown(True)
        header.setSortIndicator(col, Qt.AscendingOrder)
        self.renewListAndSetTo(self.currentItemId())


    @pyqtSignature('')
    def on_btnDelete_clicked(self):
        selectedRowList = self.tblItems.selectedRowList()
        if QtGui.QMessageBox.question(self, u'Подтверждение удаления',
                                      u'Вы уверены что хотите удалить выделенные строки?(количество строк: %d) ' % len(selectedRowList),
                                      QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                      QtGui.QMessageBox.No
                                      ) == QtGui.QMessageBox.Yes:
            for row in selectedRowList[::-1]:  # удаляем в обратном порядке, чтобы избежать сдвигов
                try:
                    self.model.removeRow(row)
                except CDatabaseException as e:
                    dbText = e.sqlError.databaseText()
                    message = u'Невозможно удалить строки, ошибка бд: %s' % dbText
                    if e.sqlError.type() == 2 and 'foreign key constraint fails' in dbText:
                        message = u'Невозможно удалить строки, данные используются'
                    QtGui.QMessageBox.critical(self, u'Внимание!', message)

            self.model.setIdList(self.select({}))


class CLoginEditor(Ui_ItemEditorDialog, CItemEditorBaseDialog):

    def __init__(self,  parent):
        CItemEditorBaseDialog.__init__(self, parent, tblLogin)
        self.addModels('Person', CPersonModel(self))
        self.setupUi(self)
        self.setWindowTitleEx(u'Учетная запись пользователя')
        self.chkChangePassword.setChecked(False)
        self.edtPassword.setEnabled(False)
        self.setModels(self.tblPerson, self.modelPerson, self.selectionModelPerson)
        self.tblPerson.addPopupDelRow()
        self.setupDirtyCather()


    def destroy(self):
        pass


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        _id = self.itemId()
        setLineEditValue(self.edtLogin, record, 'login')
        setTextEditValue(self.edtNote, record, 'note')
        self.modelPerson.loadItems(_id)
        createPerson = forceString(QtGui.qApp.db.translate('vrbPerson', 'id', forceRef(record.value('createPerson_id')), 'name'))
        modifyPerson = forceString(QtGui.qApp.db.translate('vrbPerson', 'id', forceRef(record.value('modifyPerson_id')), 'name'))
        self.lblPersonId.setText(u'id в базе данных: %d' % _id)
        self.lblCreatePerson.setText(u'Автор и дата создания записи: %s, %s ' % (createPerson, forceString(record.value('createDatetime'))))
        self.lblModifyPerson.setText(u'Автор и дата последнего изменения записи: %s, %s' % (modifyPerson, forceString(record.value('modifyDatetime'))))
        self.setIsDirty(False)


    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        getLineEditValue(self.edtLogin, record, 'login')
        if self.chkChangePassword.isChecked():
            encodedPassword = unicode(self.edtPassword.text()).encode('utf8')
            hashedPassword = hashlib.md5(encodedPassword).hexdigest()
            record.setValue('password', toVariant(hashedPassword))
        elif not self.itemId():
            hashedPassword = hashlib.md5('').hexdigest()
            record.setValue('password', toVariant(hashedPassword))
        else:
            record.remove(record.indexOf('password'))
        getTextEditValue(self.edtNote, record, 'note')
        return record


    def checkDataEntered(self):
        login = self.edtLogin.text().simplified()
        result = login or self.checkInputMessage(u'Регистрационное имя', False, self.edtLogin)
        if result and login:
            db = QtGui.qApp.db
            table = db.table(tblLogin)
            idList = db.getIdList(table, 'id', [table['login'].eq(login), table['deleted'].eq(0)])
            if idList and idList != [self.itemId()]:
                QtGui.QMessageBox.warning(self,
                                          u'Внимание!',
                                          u'Регистрационное имя "%s" уже занято' % login,
                                          QtGui.QMessageBox.Ok,
                                          QtGui.QMessageBox.Ok)
                self.edtLogin.setFocus(Qt.OtherFocusReason)
                result = False
        return result


    def saveInternals(self, _id):
        self.modelPerson.saveItems(_id)


    @pyqtSignature('int')
    def on_chkChangePassword_stateChanged(self, state):
        self.setIsDirty(True)


class CPersonModel(CInDocTableModel):
    class CLocPersonFindInDocTableCol(CPersonFindInDocTableCol):
        def __init__(self, title, fieldName, width, tableName, **params):
            CPersonFindInDocTableCol.__init__(self, title, fieldName, width, tableName, **params)

        def createEditor(self, parent):
            editor = CPersonComboBoxEx(parent)
            editor.setOrgStructureId(self.orgStructureId)
            editor.setDate(self.date)
            editor.setChkSpecialityDefaultStatus(False)
            return editor

        def toString(self, val, record):
            if forceRef(val):
                if not hasattr(QtGui.qApp, '_recordsCache_vrbPersonWithSpecialityAndPost'):
                    QtGui.qApp._recordsCache_vrbPersonWithSpecialityAndPost = CTableRecordCache(QtGui.qApp.db,
                                                                                                  'vrbPersonWithSpecialityAndPost')
                name = QtGui.qApp._recordsCache_vrbPersonWithSpecialityAndPost.get(val).value('name')
                code = QtGui.qApp._recordsCache_vrbPersonWithSpecialityAndPost.get(val).value('code')

                return QVariant(forceString(code.toPyObject()) + u', ' + forceString(name.toPyObject()))
            else:
                return None

    def __init__(self, parent):
        CInDocTableModel.__init__(self, 'Login_Person', 'id', 'master_id', parent)
        self.addCol(CPersonModel.CLocPersonFindInDocTableCol(u'Сотрудник', 'person_id', 20, 'vrbPersonWithSpecialityAndPost'))
