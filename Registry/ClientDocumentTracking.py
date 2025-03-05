# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2017 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import Qt, QDate, QObject, QTime, pyqtSignature, SIGNAL

from library.Counter import CCounterController
from library.crbcombobox                    import CRBComboBox
from library.database import CDatabaseException
from library.InDocTable                     import CInDocTableModel, CDateInDocTableCol, CInDocTableCol, CRBInDocTableCol, CRecordListModel, CTimeInDocTableCol
from library.interchange                    import getDateEditValue, getLineEditValue, getRBComboBoxValue, setDateEditValue, setLineEditValue, setRBComboBoxValue
from library.ItemsListDialog                import CItemsSplitListDialogEx, CItemEditorBaseDialog
from library.TableModel                     import CTableModel, CDateCol, CRefBookCol, CTextCol, CTimeCol
from library.Utils import forceBool, forceDate, forceInt, forceString, forceStringEx, getPref, getPrefBool, getPrefRef, \
    getPrefString, toVariant, forceTime, forceRef, exceptionToUnicode, setPref
from library.PrintInfo                      import CInfo, CDateInfo, CTimeInfo
from Orgs.PersonComboBoxEx                  import CPersonFindInDocTableCol
from Registry.BatchRegistrationLocationCard import  CSetParamsBatchRegistrationLocationCard
from Registry.Ui_BatchRegLocationCardDialog import Ui_BatchRegLocationCardDialog
from Reports.ReportView                     import CReportViewDialog
from Reports.ReportBase           import CReportBase, createTable
from Users.Rights import urEditLocationCard, urCanDeleteClientDocumentTracking

from Registry.Ui_ClientDocumentTrackingEditor import Ui_ItemEditorDialog


tableClientDocumentTracking = 'Client_DocumentTracking'
tableClientDocumentTrackingItem = 'Client_DocumentTrackingItem'
rbDocumentTypeForTracking = 'rbDocumentTypeForTracking'
rbDocumentTypeLocation = 'rbDocumentTypeLocation'


class CClientDocumentTrackingList(CItemsSplitListDialogEx):
    def __init__(self, parent, forSelect=False, uniqueCode=True):
        CItemsSplitListDialogEx.__init__(self, parent,
            tableClientDocumentTracking,
            [
            CRefBookCol(u'Вид документа', ['documentTypeForTracking_id'], rbDocumentTypeForTracking, 20, showFields=CRBComboBox.showName),
            CTextCol(u'Номер документа',                 ['documentNumber'], 20),
            CDateCol(u'Дата документа',        ['documentDate'], 20),
            ],
            ['documentDate'],
            tableClientDocumentTrackingItem,
            [
            CRefBookCol(u'Место нахождения', ['documentLocation_id'], rbDocumentTypeLocation, 20, showFields=CRBComboBox.showName),
            CDateCol(u'Дата передачи', ['documentLocationDate'],  20),
            CTimeCol(u'Время передачи', ['documentLocationTime'],  20),
            CRefBookCol(u'Ответственный', ['person_id'], 'vrbPersonWithSpeciality', 20),
            CTextCol(u'Примечание', ['note'], 20),
            ],
            'master_id', 'documentLocation_id', forSelect=forSelect)
        self.setWindowTitleEx(u'Журнал хранения учетных документов')
        self.tblItems.addPopupRecordProperies()
        self.btnNew.setEnabled(QtGui.qApp.userHasAnyRight([urEditLocationCard]))
        self.btnEdit.setEnabled(QtGui.qApp.userHasAnyRight([urEditLocationCard]))
        self.order = "documentDate desc"
        self.subOrder = 'documentLocationDate DESC, documentLocationTime DESC'


    def setSubSort(self, col):
        name = self.subModel.cols()[col].fields()[0]
        if name in ['documentLocationDate', 'documentLocationTime']:
            self.subOrder = 'documentLocationDate {ASC}, documentLocationTime {ASC}'
        else:
            self.subOrder = name + ' {ASC}'
        header=self.tblItemGroups.horizontalHeader()
        header.setSortIndicatorShown(True)
        self.isAscendingSub = not self.isAscendingSub
        header.setSortIndicator(col, Qt.AscendingOrder if self.isAscendingSub else Qt.DescendingOrder)
        if self.isAscendingSub:
            self.subOrder = self.subOrder.format(ASC='ASC')
        else:
            self.subOrder = self.subOrder.format(ASC='DESC')
        self.renewSubListAndSetTo(self.tblItemGroups.currentItemId())


    def preSetupUi(self):
        self.addObject('btnPrint',  QtGui.QPushButton(u'Печать F6', self))
        self.addObject('btnNew',  QtGui.QPushButton(u'Вставка F9', self))
        self.addObject('btnEdit',  QtGui.QPushButton(u'Правка F4', self))


    def postSetupUi(self):
        self.buttonBox.addButton(self.btnEdit, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnNew, QtGui.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.btnPrint, QtGui.QDialogButtonBox.ActionRole)


    def setup(self, cols, tableName, order, forSelect=False, filterClass=None):
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.forSelect = forSelect
        self.filterClass = filterClass
        self.props = {}
        self.order = order
        self.addModels('', CTableModel(self, cols))
        self.model.idFieldName = self.idFieldName
        self.model.setTable(tableName)
        self.setModels(self.tblItems, self.model, self.selectionModel)
        self.btnEdit.setDefault(not self.forSelect)
        self.tblItems.setFocus(Qt.OtherFocusReason)

        self.btnNew.setShortcut(Qt.Key_F9)
        self.btnEdit.setShortcut(Qt.Key_F4)
        self.btnPrint.setShortcut(Qt.Key_F6)
        QObject.connect(
            self.tblItems.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.setSort)
        self.connect(self.tblItems.popupMenu(), SIGNAL('aboutToShow()'), self.aboutToShow)


    def setPopupMenu(self):
        self.addPopupAction('actSelectAllRow', u'Выделить все строки', self.selectAllRowTblItem)
        self.addPopupAction('actClearSelectionRow', u'Снять выделение', self.clearSelectionRow)
        self.addPopupAction('actDelSelectedRows', u'Удалить выделенные строки', self.delSelectedRows)
        self.addPopupAction('actDuplicate', u'Дублировать', self.duplicateCurrentRow)
        self.addPopupAction('actUpdateRow', u'Редактировать', self.updateCurrentRow)


    def delSelectedRows(self):
        selectedRowList = self.tblItems.selectedRowList()
        if QtGui.QMessageBox.question(self, u'Подтверждение удаления',
                                    u'Вы уверены что хотите удалить выделенные строки?(количество строк: %d)'% len(selectedRowList),
                                    QtGui.QMessageBox.Yes|QtGui.QMessageBox.No,
                                    QtGui.QMessageBox.No
                                    ) == QtGui.QMessageBox.Yes:
            for row in selectedRowList[::-1]: # удаляем в обратном порядке, чтобы избежать сдвигов
                try:
                    self.model.removeRow(row)
                except CDatabaseException:
                    pass
        self.model.setIdList(self.select({}))
        self.renewSubListAndSetTo()


    def aboutToShow(self):
        currentIndex = self.tblItems.currentIndex() >= 0
        editLocationCard = QtGui.qApp.userHasRight(urEditLocationCard)
        deleteDocumentTracking = QtGui.qApp.userHasRight(urCanDeleteClientDocumentTracking)
        self.actSelectAllRow.setEnabled(currentIndex and editLocationCard)
        self.actClearSelectionRow.setEnabled(currentIndex and editLocationCard)
        self.actDelSelectedRows.setEnabled(currentIndex and editLocationCard and deleteDocumentTracking)
        self.actDuplicate.setEnabled(currentIndex and editLocationCard)
        self.actUpdateRow.setEnabled(currentIndex and editLocationCard)


    def updateCurrentRow(self):
        self.on_tblItems_doubleClicked(self.tblItems.currentIndex())


    def select(self, props={}):
        table = self.model.table()
        return QtGui.qApp.db.getIdList(table.name(), 'id', [table['deleted'].eq(0), 'client_id=%i'%self.forSelect], self.order)


    def getItemEditor(self):
        return CClientDocumentTrackingEditor(self, self.forSelect)


    @pyqtSignature('QModelIndex')
    def on_tblItems_doubleClicked(self, index):
        if QtGui.qApp.userHasAnyRight([urEditLocationCard]):
            self.on_btnEdit_clicked()


    @pyqtSignature('')
    def on_btnPrint_clicked(self):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Журнал хранения учетных документов')
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)

        tableColumns = [
            ('5%',   [u'№'],                    CReportBase.AlignRight),
            ('25%',  [u'Место нахождения'],     CReportBase.AlignRight),
            ('20%',  [u'Дата передачи'],        CReportBase.AlignRight),
            ('10%',  [u'Время передачи'],       CReportBase.AlignRight),
            ('25%',  [u'Ответственный'],        CReportBase.AlignRight),
            ('15%',  [u'Примечание'],           CReportBase.AlignRight),
            ]
        
        printIdList = []
        for selected in self.tblItems.selectedRowList():
            printIdList.append(self.model._idList[selected])
        db = QtGui.qApp.db
        queryTable  = db.table(unicode(tableClientDocumentTracking))
        tableClient = db.table('Client')
        tablerbDTFT = db.table(unicode(rbDocumentTypeForTracking))
        queryTable  = queryTable.leftJoin(tableClient, queryTable['client_id'].eq(tableClient['id']))
        queryTable  = queryTable.leftJoin(tablerbDTFT, queryTable['documentTypeForTracking_id'].eq(tablerbDTFT['id']))
        cond = [queryTable['client_id'].eq(self.forSelect), queryTable['id'].inlist(printIdList)]
        
        records = db.getRecordList(queryTable,
                                   [
                                    queryTable['id'],
                                    tablerbDTFT['name'].alias('documentType'), 
                                    queryTable['documentNumber'], 
                                    queryTable['documentDate'],
                                    u'''CONCAT(Client.lastName,' ',Client.firstName,' ',Client.patrName) as clientName'''
                                   ],
                                   cond)
        for record in records:
            description = []
            description.append(u'Вид документа: ' + forceString(record.value('documentType')))
            description.append(u'Номер документа: ' + forceString(record.value('documentNumber')))
            description.append(u'ФИО пациента: ' + forceString(record.value('clientName')))
            description.append(u'Дата создания: ' +forceDate(record.value('documentDate')).toString(u'dd.MM.yyyy'))
            documentId = forceInt(record.value('id'))
            
            columns = [ ('100%', [], CReportBase.AlignLeft) ]
            table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
            for i, row in enumerate(description):
                table.setText(i, 0, row)
            cursor.movePosition(QtGui.QTextCursor.End)
            cursor.insertBlock()
            cursor.insertBlock()
            
            tableCDTI   = db.table(unicode(tableClientDocumentTrackingItem))
            tablerbDTL  = db.table(unicode(rbDocumentTypeLocation))
            tablePerson = db.table('vrbPersonWithSpeciality') 
            tableCDTI   = tableCDTI.leftJoin(tablerbDTL,  tableCDTI['documentLocation_id'].eq(tablerbDTL['id']))
            tableCDTI   = tableCDTI.leftJoin(tablePerson, tableCDTI['person_id'].eq(tablePerson['id']))
            
            elements = db.getRecordList(tableCDTI,
                                        [tablerbDTL['name'].alias('location'),
                                        tableCDTI['documentLocationDate'],
                                        tableCDTI['documentLocationTime'],
                                        tablePerson['name'].alias('PersonName'),
                                        tableCDTI['note']],
                                        tableCDTI['master_id'].eq(documentId))
            
            tableElem = createTable(cursor, tableColumns)

            for elem in elements:
                documentLocation     = forceString(elem.value('location'))
                documentLocationDate = forceDate(elem.value('documentLocationDate')).toString(u'dd.MM.yyyy')
                documentLocationTime = forceTime(elem.value('documentLocationTime')).toString(u'hh:mm:ss')
                personName           = forceString(elem.value('PersonName'))
                note = forceString(elem.value('note'))
                
                j = tableElem.addRow()
                tableElem.setText(j, 0, j)
                tableElem.setText(j, 1, documentLocation)
                tableElem.setText(j, 2, documentLocationDate)
                tableElem.setText(j, 3, documentLocationTime)
                tableElem.setText(j, 4, personName)
                tableElem.setText(j, 5, note)
            cursor.movePosition(QtGui.QTextCursor.End)
            cursor.insertBlock()
            cursor.insertBlock()
        view = CReportViewDialog(self)
        view.setText(doc)
        view.exec_()


class CClientDocumentTrackingEditor(CItemEditorBaseDialog, Ui_ItemEditorDialog):
    def __init__(self,  parent, clientId):
        CItemEditorBaseDialog.__init__(self, parent, tableClientDocumentTracking)
        self.setupUi(self)
        self.preferences = 'BatchRegLocatCardParams'
        prefs = getPref(QtGui.qApp.preferences.reportPrefs, self.preferences, {})
        self.documentTypeForTrackingId = getPrefRef(prefs, 'documentTypeForTrackingId', None)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.setWindowTitleEx(u'Документ')
        self.cmbDocumentType.setTable(rbDocumentTypeForTracking, True)
        self.cmbDocumentType.setValue(self.documentTypeForTrackingId)
        self.addModels('DocumentLocationHistory', CDocumentLocationHistoryModel(self))
        self.setModels(self.tblDocumentLocationHistory, self.modelDocumentLocationHistory, self.selectionModelDocumentLocationHistory)
        self.clientId = clientId
        self.setupDirtyCather()
        self.__sortColumn = None
        self.__sortAscending = False
        self.tblDocumentLocationHistory.addPopupDelRow()
        self.connect(self.tblDocumentLocationHistory.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.on_sortByColumn)
        self.cmbDocumentType.currentIndexChanged.connect(self.cmbDocumentTypeChange)
        # self.edtDocumentNumber.setReadOnly(True)
        self.record = None
        self.cmbDocumentTypeChange()


    def saveDefaultParams(self, params):
        prefs = {}
        for param, value in params.iteritems():
            setPref(prefs, param, value)
        setPref(QtGui.qApp.preferences.reportPrefs, self.preferences, prefs)


    def cmbDocumentTypeChange(self):
        db = QtGui.qApp.db
        docType = self.cmbDocumentType.value()
        self.edtDocumentNumber.setReadOnly(True)
        if not self.record:
            if forceRef(docType):
                tableRbDocumentTypeForTracking = db.table('rbDocumentTypeForTracking')
                rec = db.getRecordEx(tableRbDocumentTypeForTracking, tableRbDocumentTypeForTracking['counter_id'],
                                     tableRbDocumentTypeForTracking['id'].eq(docType))
                counterId = forceRef(rec.value('counter_id'))
                if counterId:
                    date = self.edtDocumentDate.date()
                    counterController = QtGui.qApp.counterController()
                    if not counterController:
                        QtGui.qApp.setCounterController(CCounterController(self))
                    try:
                        number = QtGui.qApp.getDocumentNumber(self.clientId, counterId, date)
                        self.edtDocumentNumber.setText(number)
                    except Exception, e:
                        QtGui.QMessageBox.critical(QtGui.qApp.mainWindow,
                                                   u'Внимание!',
                                                   u'Произошла ошибка при получении значения счетчика\n%s' % e,
                                                   QtGui.QMessageBox.Ok)
                    finally:
                        if not counterController:
                            QtGui.qApp.setCounterController(None)
                else:
                    self.edtDocumentNumber.clear()
                    self.edtDocumentNumber.setReadOnly(False)
            else:
                self.edtDocumentNumber.clear()


    def on_sortByColumn(self, logicalIndex):
        currentIndex = self.tblDocumentLocationHistory.currentIndex()
        currentItem = self.tblDocumentLocationHistory.currentItem()
        model = self.tblDocumentLocationHistory.model()
        if isinstance(model, CRecordListModel):
            header=self.tblDocumentLocationHistory.horizontalHeader()
            if model.cols()[logicalIndex].sortable():
                if self.__sortColumn == logicalIndex:
                    self.__sortAscending = not self.__sortAscending
                else:
                    self.__sortColumn = logicalIndex
                    self.__sortAscending = True
                header.setSortIndicatorShown(True)
                header.setSortIndicator(self.__sortColumn, Qt.AscendingOrder if self.__sortAscending else Qt.DescendingOrder)
                model.sortData(logicalIndex, self.__sortAscending)
            elif self.__sortColumn is not None:
                header.setSortIndicator(self.__sortColumn, Qt.AscendingOrder if self.__sortAscending else Qt.DescendingOrder)
            else:
                header.setSortIndicatorShown(False)
        if currentItem:
            newRow = model.items().index(currentItem)
            self.tblDocumentLocationHistory.setCurrentIndex(model.index(newRow, currentIndex.column()))
        else:
            self.tblDocumentLocationHistory.setCurrentIndex(model.index(0, 0))


    def setRecord(self, record):
        CItemEditorBaseDialog.setRecord(self, record)
        self.record = record
        setRBComboBoxValue(self.cmbDocumentType, record, 'documentTypeForTracking_id')
        setLineEditValue(self.edtDocumentNumber, record, 'documentNumber')
        setDateEditValue(self.edtDocumentDate, record, 'documentDate')
        self.modelDocumentLocationHistory.loadItems(self.itemId())


    def getRecord(self):
        record = CItemEditorBaseDialog.getRecord(self)
        record.setValue('client_id',  toVariant(self.clientId))
        getRBComboBoxValue(self.cmbDocumentType, record, 'documentTypeForTracking_id')
        getLineEditValue(self.edtDocumentNumber, record, 'documentNumber')
        getDateEditValue(self.edtDocumentDate, record, 'documentDate')
        return record


    def saveInternals(self, id):
        param = {}
        self.modelDocumentLocationHistory.saveItems(id)
        param['documentTypeForTrackingId'] = self.cmbDocumentType.value()
        self.saveDefaultParams(param)


    def checkDataEntered(self):
        result = True
        documentType    = forceStringEx(self.cmbDocumentType.value())
        for row, item in enumerate(self.modelDocumentLocationHistory._items):
            documentLocation = forceBool(item.value('documentLocation_id'))
            result = result and (documentLocation or self.checkInputMessage(u'Место нахождения документа', False, self.tblDocumentLocationHistory, row, 0))
        result = result and (documentType or self.checkInputMessage(u'Вид документа', False, self.cmbDocumentType))
        return result


    def setEdtDocumentNumber(self, counterId):
        if counterId:
            date = self.edtDocumentDate.date()
            counterController = QtGui.qApp.counterController()
            if not counterController:
                QtGui.qApp.setCounterController(CCounterController(self))
            try:
                number = QtGui.qApp.getDocumentNumber(self.clientId, counterId, date)
                self.edtDocumentNumber.setText(number)
            except Exception, e:
                QtGui.QMessageBox.critical(QtGui.qApp.mainWindow,
                                           u'Внимание!',
                                           u'Произошла ошибка при получении значения счетчика\n%s' % e,
                                           QtGui.QMessageBox.Ok)
            finally:
                if not counterController:
                    QtGui.qApp.setCounterController(None)
        else:
            self.edtDocumentNumber.clear()
            self.edtDocumentNumber.setReadOnly(False)


class CDocumentLocationHistoryModel(CInDocTableModel):
    def __init__(self, parent):
        CInDocTableModel.__init__(self, tableClientDocumentTrackingItem, 'id', 'master_id', parent)
        self.addCol(CRBInDocTableCol(u'Место нахождения', 'documentLocation_id', 20, rbDocumentTypeLocation, showFields=CRBComboBox.showName).setSortable(True))
        self.addCol(CDateInDocTableCol(u'Дата передачи', 'documentLocationDate',  50).setSortable(True))
        self.addCol(CTimeInDocTableCol(u'Время передачи', 'documentLocationTime',  10).setSortable(True))
        self.addCol(CPersonFindInDocTableCol(u'Ответственный', 'person_id', 20, 'Person'))
        self.addCol(CInDocTableCol(u'Примечание', 'note', 10).setSortable(True))

    def getEmptyRecord(self):
        record = CInDocTableModel.getEmptyRecord(self)
        record.setValue('documentLocationDate',  toVariant(QDate.currentDate()))
        record.setValue('documentLocationTime',  toVariant(QTime.currentTime()))
        record.setValue('person_id',  toVariant(QtGui.qApp.userId))
        return record


class CDocumentLocationGroupEditor(CSetParamsBatchRegistrationLocationCard, Ui_BatchRegLocationCardDialog):
    def __init__(self, parent, eventIdList):
        CSetParamsBatchRegistrationLocationCard.__init__(self, parent)
        self.btnStart.setText(u'OK')
        self.eventIdList = eventIdList
        self.preferences = 'BatchRegLocatCardParams'
        self.cmbPerson.setValue(QtGui.qApp.userId)
        self.params = self.getDefaultParams()

    def setParams(self):
        CSetParamsBatchRegistrationLocationCard.setParams(self)
        self.btnStart.setVisible(True)
        self.btnRetry.setVisible(False)

    def getDefaultParams(self):
        result = {}
        prefs = getPref(QtGui.qApp.preferences.reportPrefs, self.preferences, {})
        result['numberPreferences'] = getPref(prefs, 'numberPreferences', 0)
        result['documentTypeForTrackingId'] = getPrefRef(prefs, 'documentTypeForTrackingId', None)
        result['documentLocationId'] = getPrefRef(prefs, 'documentLocationId', None)
        result['personId']  = getPrefRef(prefs, 'personId', None)
        result['notesPage'] = getPrefString(prefs, 'notesPage', '')
        result['BatchRegLocatCardProcess'] = getPrefBool(prefs, 'BatchRegLocatCardProcess', False)
        return result

    def saveParams(self, batchRegLocatCardProcess = True):
        localParams = self.getParams(batchRegLocatCardProcess)
        self.saveDefaultParams(localParams)

    def getParams(self, batchRegLocatCardProcess = True):
        result = {}
        result['BatchRegLocatCardProcess'] = batchRegLocatCardProcess
        result['numberPreferences'] = self.cmbDocumentNumber.currentIndex()
        result['documentTypeForTrackingId'] = self.cmbDocumentTypeForTracking.value()
        result['documentLocationId'] = self.cmbDocumentLocation.value()
        result['personId'] = self.cmbPerson.value()
        result['notesPage'] = self.edtNotesPage.toPlainText()
        return result


    @pyqtSignature('')
    def on_btnStart_clicked(self):
        if self.checkDataEntered():
            self.save()
            self.saveParams(False)
            self.close()

    @pyqtSignature('')
    def on_btnClose_clicked(self):
        self.close()

    def save(self):
        self.params = self.getParams()
        if self.eventIdList:
            for eventData in self.eventIdList:
                eventId = eventData[0]
                db = QtGui.qApp.db
                clientId, setDate, externalId = self.getEventData(eventId)
                if self.params['numberPreferences']==2:
                    record = self.getRecord(clientId, setDate, externalId)
                else:
                    record = self.getRecord(clientId, setDate, None)
                if record:
                    try:
                        db.transaction()
                        try:
                            id = db.insertOrUpdate('Client_DocumentTracking', record)
                            recordItem = self.getRecordItem(id)
                            db.insertRecord('Client_DocumentTrackingItem', recordItem)
                            db.commit()
                        except:
                            db.rollback()
                            raise
                    except Exception as e:
                        QtGui.qApp.logCurrentException()
                        QtGui.QMessageBox.critical( self,
                                                    u'',
                                                    exceptionToUnicode(e),
                                                    QtGui.QMessageBox.Close)
        return None


    def getEventData(self, eventId):
        clientId = None
        setDate = None
        externalId = None
        if eventId:
            db = QtGui.qApp.db
            table = db.table('Event')
            record = db.getRecordEx(table, 'client_id, setDate, externalId', [table['deleted'].eq(0), table['id'].eq(eventId)])
            clientId = forceInt(record.value('client_id'))
            setDate = forceDate(record.value('setDate'))
            externalId = forceString(record.value('externalId'))
        return clientId, setDate, externalId

    def getRecord(self, clientId, setDate, externalId=None):
        db = QtGui.qApp.db
        table = db.table('Client_DocumentTracking')
        rbTable = db.table('rbDocumentTypeForTracking')
        docType = self.params.get('documentTypeForTrackingId', None)
        cond = [table['deleted'].eq(0), table['client_id'].eq(clientId), table['documentDate'].ge(setDate), table['documentTypeForTracking_id'].ge(docType)]
        if externalId:
            cond.append(table['documentNumber'].eq(externalId))
        if self.params['numberPreferences']==1:
            cond.append(table['documentNumber'].eq(clientId))
        self.record = db.getRecordEx(table.innerJoin(rbTable, table['documentTypeForTracking_id'].eq(rbTable['id'])), 'Client_DocumentTracking.*', cond, 'Client_DocumentTracking.id DESC')
        if not self.record:
            numberPreferences = self.params.get('numberPreferences', None)
            db = QtGui.qApp.db
            self.record = db.record('Client_DocumentTracking')
            self.record.setValue('client_id', toVariant(clientId))
            self.record.setValue('documentTypeForTracking_id', toVariant(self.params.get('documentTypeForTrackingId', None)))
            self.record.setValue('documentDate', toVariant(QDate.currentDate()))
            if numberPreferences==1:
                self.record.setValue('documentNumber', toVariant(clientId))
            elif numberPreferences==2:
                self.record.setValue('documentNumber', toVariant(externalId))
            else:
                self.record.setValue('documentNumber', toVariant(None))
            return self.record
        return self.record

    def getRecordItem(self, masterId):
        if masterId:
            db = QtGui.qApp.db
            record = db.record('Client_DocumentTrackingItem')
            record.setValue('master_id', toVariant(masterId))
            record.setValue('documentLocation_id', toVariant(self.params.get('documentLocationId', None)))
            record.setValue('documentLocationDate', toVariant(QDate.currentDate()))
            record.setValue('documentLocationTime', toVariant(QTime.currentTime()))
            record.setValue('person_id', toVariant(self.params.get('personId', None)))
            record.setValue('note', toVariant(self.params.get('notesPage', None)))
            return record
        return None


class CDocumentLocationInfo(CInfo):
    def __init__(self, context, clientId, externalId):
        CInfo.__init__(self, context)
        self._clientId = clientId
        self._externalId = externalId
        self._location = u''
        self._docDate = u''
        self._docTime = u''
        self._note = u''
        self._person = u''
        

    def getDocumentLocationInfo(self, clientId, externalId):
        cond = []
        db = QtGui.qApp.db
        queryTable = db.table('Client_DocumentTracking')
        tableItems= db.table('Client_DocumentTrackingItem')
        tableRbDocType = db.table('rbDocumentTypeForTracking')
        tableRbLocation = db.table('rbDocumentTypeLocation')
        tablePerson = db.table('vrbPerson')
        queryTable = queryTable.leftJoin(tableItems, queryTable['id'].eq(tableItems['master_id']))
        queryTable = queryTable.leftJoin(tableRbDocType, queryTable['documentTypeForTracking_id'].eq(tableRbDocType['id']))
        queryTable = queryTable.leftJoin(tableRbLocation, tableItems['documentLocation_id'].eq(tableRbLocation['id']))
        queryTable = queryTable.leftJoin(tablePerson, tableItems['person_id'].eq(tablePerson['id']))
        cond.append(queryTable['client_id'].eq(self._clientId))
        cond.append(tableRbDocType['showInClientInfo'].eq(1))
        cond.append(queryTable['documentNumber'].eq(self._externalId))
        record = db.getRecordEx(queryTable, ['rbDocumentTypeLocation.name as location, Client_DocumentTrackingItem.documentLocationDate as docDate, Client_DocumentTrackingItem.documentLocationTime as docTime, Client_DocumentTrackingItem.note as note, vrbPerson.name as person'], cond,  ['Client_DocumentTrackingItem.documentLocationDate DESC, Client_DocumentTrackingItem.documentLocationTime DESC'])
        return record

    def _load(self):
        if self._clientId:
            record = self.getDocumentLocationInfo(self._clientId, self._externalId)
            if record:
                self._location = forceString(record.value('location'))
                self._docDate = CDateInfo(forceDate(record.value('docDate')))
                self._docTime = CTimeInfo(forceTime(record.value('docTime')))
                self._note = forceString(record.value('note'))
                self._person = forceString(record.value('person'))
                return True
        return False

    location = property(lambda self: self.load()._location)
    docDate = property(lambda self: self.load()._docDate)
    docTime = property(lambda self: self.load()._docTime)
    note = property(lambda self: self.load()._note)
    person = property(lambda self: self.load()._person)
