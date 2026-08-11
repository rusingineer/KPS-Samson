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
from PyQt4.QtCore import Qt, QDate, QDateTime, QModelIndex, pyqtSignature, SIGNAL


from library.DialogBase    import CConstructHelperMixin, CDialogBase
from library.Utils         import forceRef, forceString, pyDate, toVariant, forceDate
from Events.EventFeedModel import CFeedModel
from RefBooks.Menu.List    import CGetRBMenu
from Registry.Utils        import getClientString
from Reports.ReportBase    import CReportBase, createTable
from Reports.ReportView    import CReportViewDialog

from Events.Ui_EventFeedPage import Ui_EventFeedPage


class CEventFeedPage(QtGui.QWidget, CConstructHelperMixin, Ui_EventFeedPage):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.clientId = None
        self.setupUi(self)

        self.addModels('ClientFeed', CFeedModel(self, 0))
        self.addModels('PatronFeed', CFeedModel(self, 1))
        self.tblClientFeed.setModel(self.modelClientFeed)
        self.tblPatronFeed.setModel(self.modelPatronFeed)

        self.tblClientFeed.addPopupDuplicateSelectRows()
        self.tblClientFeed.addPopupSeparator()
        self.tblClientFeed.addMoveRow()
        self.tblClientFeed.addPopupSeparator()
        self.tblClientFeed.addPopupSelectRowsByData()
        self.tblClientFeed.addPopupSelectAllRow()
        self.tblClientFeed.addPopupClearSelectionRow()
        self.tblClientFeed.addPopupSeparator()
        self.tblClientFeed.addPopupDelRow()

        self.tblPatronFeed.addPopupDuplicateSelectRows()
        self.tblPatronFeed.addPopupSeparator()
        self.tblPatronFeed.addMoveRow()
        self.tblPatronFeed.addPopupSeparator()
        self.tblPatronFeed.addPopupSelectRowsByData()
        self.tblPatronFeed.addPopupSelectAllRow()
        self.tblPatronFeed.addPopupClearSelectionRow()
        self.tblPatronFeed.addPopupSeparator()
        self.tblPatronFeed.addPopupDelRow()

        self.contractId = None
        self.financeId = None
        self.patronId = None
        self.isHospitalBed = False


    def getFilterWihtAge(self, id, date, filterDiet):
        if date:
            db = QtGui.qApp.db
            filterDiet.append(u'''(SELECT isSexAndAgeSuitable(0, (SELECT MAX(Client.birthDate) FROM Client WHERE Client.id = %s AND Client.deleted = 0), 0, rbDiet.age, %s))'''%(id, db.formatDate(date)))
            return filterDiet
        return filterDiet


    def setFilterDiet(self, begDate=None, endDate=None):
#        filter = []
        filterClient = []
        filterPatron = []
        db = QtGui.qApp.db
        tableRBDiet = db.table('rbDiet')
        if begDate:
            filterClient.append(db.joinOr([tableRBDiet['endDate'].isNull(), tableRBDiet['endDate'].ge(begDate)]))
            filterPatron.append(db.joinOr([tableRBDiet['endDate'].isNull(), tableRBDiet['endDate'].ge(begDate)]))
        if endDate:
            filterClient.append(db.joinOr([tableRBDiet['begDate'].isNull(), tableRBDiet['begDate'].le(endDate)]))
            filterPatron.append(db.joinOr([tableRBDiet['begDate'].isNull(), tableRBDiet['begDate'].le(endDate)]))
        date = begDate if begDate else (endDate if endDate else None)
        if self.clientId:
            filterClient = self.getFilterWihtAge(self.clientId, date, filterClient)
        filterDietClient = db.joinAnd(filterClient)
        self.modelClientFeed.modelRBDiet.setTable('rbDiet', filter=filterDietClient)
        if self.patronId:
            filterPatron = self.getFilterWihtAge(self.patronId, date, filterPatron)
        filterDietPatron = db.joinAnd(filterPatron)
        self.modelPatronFeed.modelRBDiet.setTable('rbDiet', filter=filterDietPatron)


    def setClientId(self, clientId):
        self.clientId = clientId
        self.tblPatronFeed.patronItemDelegate.setClientId(self.clientId)
        self.modelClientFeed.loadClientRelation(self.clientId)
        self.modelPatronFeed.loadClientRelation(self.clientId)


    def setPatronId(self, patronId):
        self.patronId = patronId
        self.modelPatronFeed.setPatronId(self.patronId)


    def setFinanceId(self, financeId):
        self.financeId = financeId
        self.modelClientFeed.setFinanceId(self.financeId)
        self.modelPatronFeed.setFinanceId(self.financeId)


    def setContractId(self, contractId):
        self.contractId = contractId
        self.financeId = None
        if contractId:
            db = QtGui.qApp.db
            table = db.table('Contract')
            record = db.getRecordEx(table, [table['finance_id']], [table['id'].eq(contractId)])
            self.financeId = forceRef(record.value('finance_id')) if record else None
        self.modelClientFeed.setFinanceId(self.financeId)
        self.modelPatronFeed.setFinanceId(self.financeId)


    def destroy(self):
        self.tblClientFeed.setModel(None)
        del self.modelClientFeed
        self.tblPatronFeed.setModel(None)
        del self.modelPatronFeed


    def prepare(self):
        self.load(None)


    def load(self, eventId):
        db = QtGui.qApp.db
        tableEvent = db.table('Event')
        tableClient = db.table('Client')
        table = tableClient.innerJoin(tableEvent, tableEvent['relative_id'].eq(tableClient['id']))
        record = db.getRecordEx(table, ['''CONCAT_WS(' ', Client.lastName, Client.firstName,
Client.patrName, CAST( Client.id AS CHAR)) AS patronName'''], [tableEvent['deleted'].eq(0), tableEvent['id'].eq(eventId)])
        patronName = forceString(record.value('patronName')) if record else u'не определен'
        self.lblPatronName.setText(u'Основное лицо по уходу: ' + patronName)
        self.modelClientFeed.loadHeader()
        refusalClientCol = self.modelClientFeed.columnCount()-1
        featuresClientCol = self.modelClientFeed.columnCount()-2
        self.tblClientFeed.setItemDelegateForColumn(0, self.tblClientFeed.dateEditItemDelegate)
        self.tblClientFeed.setItemDelegateForColumn(featuresClientCol, self.tblClientFeed.featuresToEatDelegate)
        self.tblClientFeed.setItemDelegateForColumn(refusalClientCol, self.tblClientFeed.refusalToEatDelegate)
        self.tblClientFeed.setItemDelegateForColumn(1, self.tblClientFeed.financeItemDelegate)
        for column in range(2, self.modelClientFeed.columnCount()-2):
            self.tblClientFeed.setItemDelegateForColumn(column, self.tblClientFeed.dietItemDelegate)
        self.modelClientFeed.loadData(eventId, 0)
        self.modelPatronFeed.loadHeader()
        refusalPatronCol = self.modelPatronFeed.columnCount()-1
        featuresPatronCol = self.modelPatronFeed.columnCount()-2
        self.tblPatronFeed.setItemDelegateForColumn(0, self.tblPatronFeed.dateEditItemDelegate)
        self.tblPatronFeed.setItemDelegateForColumn(featuresPatronCol, self.tblPatronFeed.featuresToEatDelegate)
        self.tblPatronFeed.setItemDelegateForColumn(refusalPatronCol, self.tblPatronFeed.refusalToEatDelegate)
        self.tblPatronFeed.setItemDelegateForColumn(1, self.tblPatronFeed.financeItemDelegate)
        self.tblPatronFeed.setItemDelegateForColumn(2, self.tblPatronFeed.patronItemDelegate)
        for column in range(3, self.modelPatronFeed.columnCount()-2):
            self.tblPatronFeed.setItemDelegateForColumn(column, self.tblPatronFeed.dietItemDelegate)
        self.modelPatronFeed.loadData(eventId, 1)


    def save(self, eventId):
        feedIdList = []
        feedIdList = self.modelClientFeed.saveData(eventId, 0, feedIdList)
        feedIdList = self.modelPatronFeed.saveData(eventId, 1, feedIdList)
        db = QtGui.qApp.db
        table = db.table('Event_Feed')
        masterId = toVariant(eventId)
        filter = [table['event_id'].eq(masterId),
          ' ('+table['id'].notInlist(feedIdList)+')']
        db.deleteRecord(table, filter)


    @pyqtSignature('QModelIndex')
    def on_tblClientFeed_clicked(self, index):
        row = index.row()
        column = index.column()
        date = self.modelClientFeed.dates[row]
        header = self.modelClientFeed.headers[column]
        if header[0] and (date, header[0]) in self.modelClientFeed.items.keys():
            item = self.modelClientFeed.items.get((date, header[0]), None)
            record = item[1] if (item and len(item) == 2) else None
            if record:
                createDatetime = forceString(record.value('createDatetime'))
                createPerson = forceString(QtGui.qApp.db.translate('vrbPerson', 'id', forceRef(record.value('createPerson_id')), 'name'))
                modifyDatetime = forceString(record.value('modifyDatetime'))
                modifyPerson = forceString(QtGui.qApp.db.translate('vrbPerson', 'id', forceRef(record.value('modifyPerson_id')), 'name'))
                self.lblCreatePerson.setText(u'Автор: ' + createPerson)
                self.lblModifyPerson.setText(u' Изменил: ' + modifyPerson)
                self.lblCreateDate.setText(createDatetime)
                self.lblModifyDate.setText(modifyDatetime)
            else:
                self.lblCreatePerson.setText('')
                self.lblModifyPerson.setText('')
                self.lblCreateDate.setText('')
                self.lblModifyDate.setText('')


    @pyqtSignature('QModelIndex')
    def on_tblPatronFeed_clicked(self, index):
        row = index.row()
        column = index.column()
        date = self.modelPatronFeed.dates[row]
        header = self.modelPatronFeed.headers[column]
        if header[0] and (date, header[0]) in self.modelPatronFeed.items.keys():
            item = self.modelPatronFeed.items.get((date, header[0]), None)
            record = item[1] if (item and len(item) == 2) else None
            if record:
                createDatetime = forceString(record.value('createDatetime'))
                createPerson = forceString(QtGui.qApp.db.translate('vrbPerson', 'id', forceRef(record.value('createPerson_id')), 'name'))
                modifyDatetime = forceString(record.value('modifyDatetime'))
                modifyPerson = forceString(QtGui.qApp.db.translate('vrbPerson', 'id', forceRef(record.value('modifyPerson_id')), 'name'))
                self.lblCreatePerson.setText(u'Автор: ' + createPerson)
                self.lblModifyPerson.setText(u' Изменил: ' + modifyPerson)
                self.lblCreateDate.setText(createDatetime)
                self.lblModifyDate.setText(modifyDatetime)
            else:
                self.lblCreatePerson.setText('')
                self.lblModifyPerson.setText('')
                self.lblCreateDate.setText('')
                self.lblModifyDate.setText('')


    @pyqtSignature('QModelIndex')
    def on_tblClientFeed_doubleClicked (self, index):
        refusalClientCol = self.modelClientFeed.columnCount()-1
        featuresClientCol = self.modelClientFeed.columnCount()-2
        row = index.row()
        column = index.column()
        date = self.modelClientFeed.dates[row]
        if column not in [featuresClientCol, refusalClientCol, 1]:
            self.tblClientFeed.dietItemDelegate.setFilter(forceDate(date), self.clientId)


    @pyqtSignature('QModelIndex')
    def on_tblPatronFeed_doubleClicked (self, index):
        refusalPatronCol = self.modelPatronFeed.columnCount()-1
        featuresPatronCol = self.modelPatronFeed.columnCount()-2
        row = index.row()
        column = index.column()
        date = self.modelPatronFeed.dates[row]
        if column not in [featuresPatronCol, refusalPatronCol, 1, 2]:
            self.tblPatronFeed.dietItemDelegate.setFilter(forceDate(date), self.patronId)


    @pyqtSignature('')
    def on_btnGetMenu_clicked(self):
        widgetIndex = self.tabWidget.currentIndex()
        if widgetIndex == 0:
            modelFeed = self.modelClientFeed
            typeFeed = 0
            dialog = CGetRBMenu(self, self.financeId, self.clientId)
        else:
            modelFeed = self.modelPatronFeed
            typeFeed = 1
            dialog = CGetRBMenu(self, self.financeId, self.patronId)
        id = dialog.exec_()
        if id:
            begDate = dialog.edtBegDate.date()
            endDate = dialog.edtEndDate.date()
            if begDate and endDate and begDate <= endDate:
                db = QtGui.qApp.db
                records = db.getRecordList('rbMenu_Content', '*', 'master_id = %d' % (id))
                if records:
                    if dialog.chkUpdate.isChecked():
                        nextDate = begDate
                        while nextDate <= endDate:
                            for row, dat in enumerate(modelFeed.dates):
                                if modelFeed.dates[row] == pyDate(nextDate):
                                    modelFeed.removeRow(row)
                            nextDate = nextDate.addDays(1)
                    nextDate = begDate
                    while nextDate <= endDate:
                        if dialog.chkUpdate.isChecked() or (not dialog.chkUpdate.isChecked() and (pyDate(nextDate) not in modelFeed.dates)):
                            for record in records:
                                mealTimeId = forceRef(record.value('mealTime_id'))
#                                menuId = forceRef(record.value('master_id'))
#                                financeId = None
#                                if menuId:
#                                    tableRBMenu = db.table('rbMenu')
#                                    recordMenu = db.getRecordEx('rbMenu', [tableRBMenu['finance_id']], [tableRBMenu['id'].eq(menuId)])
#                                    if recordMenu:
#                                        financeId = forceRef(recordMenu.value('finance_id'))
                                if mealTimeId:
                                    newRecord = modelFeed.getEmptyRecord()
                                    newRecord.setValue('diet_id', toVariant(record.value('diet_id')))
                                    newRecord.setValue('date', toVariant(nextDate))
                                    newRecord.setValue('mealTime_id', toVariant(mealTimeId))
                                    newRecord.setValue('finance_id', toVariant(dialog.cmbFinance.value()))
                                    newRecord.setValue('refusalToEat', toVariant(dialog.chkRefusalToEat.isChecked()))
                                    newRecord.setValue('featuresToEat', toVariant(dialog.edtFeaturesToEat.text()))
                                    newRecord.setValue('typeFeed', toVariant(typeFeed))
                                    if typeFeed:
                                        newRecord.setValue('patron_id', toVariant(self.patronId))
                                    pyNewDate = pyDate(nextDate)
                                    modelFeed.items[(pyNewDate, mealTimeId)] = (forceRef(newRecord.value('diet_id')), newRecord)
                            vCnt = len(modelFeed.dates)-1
                            vIndex = QModelIndex()
                            modelFeed.beginInsertRows(vIndex, vCnt, vCnt)
                            modelFeed.insertRows(vCnt, 1, vIndex)
                            modelFeed.dates.insert(vCnt, pyNewDate)
                            modelFeed.endInsertRows()
                        nextDate = nextDate.addDays(1)
                    maxDates = []
                    datNones = 0
                    for dat in modelFeed.dates:
                        if dat:
                            maxDates.append(dat)
                        else:
                            datNones += 1
                    maxDates.sort()
                    for datNone in range(0, datNones):
                        maxDates.append(pyDate(QDate()))
                    modelFeed.dates = maxDates
            modelFeed.reset()
#            if widgetIndex == 0:
#                self.modelClientFeed = modelFeed
#            else:
#                self.modelPatronFeed = modelFeed


    @pyqtSignature('int')
    def on_tabWidget_currentChanged(self, index):
        if index == 1 and self.isHospitalBed:
            self.btnGetMenu.setEnabled(bool(self.patronId))
        else:
            self.btnGetMenu.setEnabled(True)


    @pyqtSignature('')
    def on_btnFeedPrint_clicked(self):
        widgetIndex = self.tabWidget.currentIndex()
        if widgetIndex == 0:
            model = self.modelClientFeed
        else:
            model = self.modelPatronFeed
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Питание\n')
        cursor.insertBlock()
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertText(u'Пациент: %s' % (getClientString(self.clientId)))
        cursor.insertText(u'\nОтчёт составлен: ' + forceString(QDateTime.currentDateTime()))
        cursor.insertBlock()
        colWidths  = [ self.tblClientFeed.columnWidth(i) for i in xrange(model.columnCount()-1) ]
        colWidths.insert(0,10)
        totalWidth = sum(colWidths)
        tableColumns = []
        iColNumber = False
        for iCol, colWidth in enumerate(colWidths):
            widthInPercents = str(max(1, colWidth*90/totalWidth))+'%'
            if iColNumber == False:
                tableColumns.append((widthInPercents, [u'№'], CReportBase.AlignRight))
                iColNumber = True
            headers = model.headers
            tableColumns.append((widthInPercents, [forceString(headers[iCol][1])], CReportBase.AlignLeft))
        table = createTable(cursor, tableColumns)
        for iModelRow in xrange(model.rowCount() - 1):
            iTableRow = table.addRow()
            table.setText(iTableRow, 0, iModelRow+1)
            for iModelCol in xrange(model.columnCount()):
                index = model.createIndex(iModelRow, iModelCol)
                text = forceString(model.data(index))
                table.setText(iTableRow, iModelCol+1, text)
        html = doc.toHtml('utf-8')
        view = CReportViewDialog(self)
        view.setText(html)
        view.exec_()


# ####################################################################

# WFT? Это - не страница.должно быть сделано отдельным модулем. избавьте меня от самописных setupUi!!!!

class CFeedPageDialog(CDialogBase):
    def __init__(self, parent=None):
        CDialogBase.__init__(self, parent)
        self.eventId = None
        self.setupUi()
        self.setupDirtyCather()
        self.setWindowTitle(u'Питание')


    def setupUi(self):
        self.vLayout = QtGui.QVBoxLayout(self)
        self.vLayout.setContentsMargins(4, 4, 4, 4)
        self.vLayout.setSpacing(4)
        self.feedWidget = CEventFeedPage(self)
        if self.feedWidget.layout():
            self.feedWidget.layout().setContentsMargins(4, 4, 4, 4)
        self.vLayout.addWidget(self.feedWidget)
        self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok, Qt.Horizontal, self)
        self.vLayout.addWidget(self.buttonBox)
        self.connect(self.buttonBox, SIGNAL('accepted()'), self.accept)
        self.connect(self.buttonBox, SIGNAL('rejected()'),  self.reject)


    def loadData(self, eventId):
        self.feedWidget.isHospitalBed = True
        self.eventId = eventId
        financeId = None
        patronId = None
        if self.eventId:
            db = QtGui.qApp.db
            table = db.table('Event')
            tableContract = db.table('Contract')
            record = db.getRecordEx(table.leftJoin(tableContract, tableContract['id'].eq(table['contract_id'])), [tableContract['finance_id'], table['relative_id']], [table['id'].eq(self.eventId)])
            if record:
                financeId = forceRef(record.value('finance_id'))
                patronId = forceRef(record.value('relative_id'))
        self.feedWidget.setPatronId(patronId)
        self.feedWidget.setFinanceId(financeId)
        self.feedWidget.load(eventId)


    def saveData(self):
        self.feedWidget.save(self.eventId)
        return True


    def setClientId(self, clientId):
        self.feedWidget.setClientId(clientId)


    def setEnablePatronTab(self, flag):
        self.feedWidget.tabPatronFeed.setEnabled(flag)


    def destroy(self):
        pass


