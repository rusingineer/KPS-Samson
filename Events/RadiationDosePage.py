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

from PyQt4 import QtGui
from PyQt4.QtCore import QDate, QVariant, pyqtSignature, QObject, SIGNAL, Qt
from PyQt4.QtGui import QTextBlockFormat

from library.DialogBase         import CConstructHelperMixin
from library.PrintInfo          import CInfoContext, CDateInfo
from library.PrintTemplates     import getPrintTemplates, CPrintAction, applyTemplate
from library.TableModel         import CTableModel, CCol, CDateCol, CRefBookCol, CSumCol
from library.Utils              import forceDouble, forceInt, forceRef, forceString, forceDate, formatDate

from Events.ActionInfo          import CActionInfo
from Events.ActionTypeCol       import CActionTypeCol
from Registry.Utils             import getClientInfoEx, CClientInfo
from Reports.ReportBase         import CReportBase, createTable
from Reports.ReportView         import CReportViewDialog


from Events.Ui_RadiationDosePage       import Ui_RadiationDosePage

def getPersonName(personId):
    db = QtGui.qApp.db
    query = db.query("SELECT CONCAT_WS(' ', lastName, firstName, patrName) FROM Person WHERE id = %d" % personId)
    if query.next():
        return forceString(query.value(0))
    return str()


class CRadiationDosePage(QtGui.QWidget, Ui_RadiationDosePage, CConstructHelperMixin):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setupUi(self)
        self.addModels('RadiationDose',  CRadiationDoseModel(self))
        self.setModels(self.tblRadiationDose, self.modelRadiationDose, self.selectionModelRadiationDose)

        self.clientId = None
        self._onlyTotalDoseSumInfo = True
        self.btnRadiationDosePrintIsLoaded = False
        header = self.tblRadiationDose.horizontalHeader()
        header.setSortIndicatorShown(True)
        header.setClickable(True)
        QObject.connect(header, SIGNAL('sectionClicked(int)'), self.onHeaderTblRadiationDoseClicked)


    def showEvent(self, event):
        if not self.btnRadiationDosePrintIsLoaded:
            mnuPrint = QtGui.QMenu()
            printSignalSheetAction = mnuPrint.addAction(u'Сигнальный лист')
            printRadiationLoadAccountingAction = mnuPrint.addAction(u'Лист учета лучевых нагрузок')
            mnuPrint.addSeparator()
            for template in getPrintTemplates('radiationDose'):
                mnuPrint.addAction(CPrintAction(template.name, template.id, None, self, self.on_btnRadiationDosePrint_printByTemplate))
            printSignalSheetAction.triggered.connect(self._printSignalSheetReport)
            printRadiationLoadAccountingAction.triggered.connect(self._printRadiationLoadAccountingReport)
            self.btnRadiationDosePrint.setMenu(mnuPrint)
            self.btnRadiationDosePrintIsLoaded = True
        QtGui.QWidget.showEvent(self, event)


    def onHeaderTblRadiationDoseClicked(self, col):
        headerSortingCol = self.modelRadiationDose.headerSortingCol.get(col, False)
        self.modelRadiationDose.headerSortingCol = {}
        self.modelRadiationDose.headerSortingCol[col] = not headerSortingCol
        self.modelRadiationDose.sortDataModel()
        self.tblRadiationDose.horizontalHeader().setSortIndicator(col, Qt.DescendingOrder if not headerSortingCol else Qt.AscendingOrder)


    def setClientId(self, clientId):
        self.clientId = clientId

        db = QtGui.qApp.db

        tableEvent = db.table('Event')
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        tableActionPropertyType = db.table('ActionPropertyType')

        queryTable = tableAction
        queryTable = queryTable.leftJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
        queryTable = queryTable.leftJoin(tableActionPropertyType, tableActionPropertyType['actionType_id'].eq(tableActionType['id']))
        queryTable = queryTable.leftJoin(tableEvent, tableEvent['id'].eq(tableAction['event_id']))

        cond = [tableEvent['client_id'].eq(clientId),
                tableActionPropertyType['typeName'].eq(u'Доза облучения'),
                tableAction['deleted'].eq(0)]

        actionIdList = db.getIdList(queryTable, tableAction['id'].name(), cond)

        self.modelRadiationDose.setIdList(actionIdList)

        self.updateLabelsInfo()


    def updateLabelsInfo(self):
        self.updateLabelRecordCountInfo()
        self.updateLabelActionsSumInfo()
        self.updateLabelPhotosSumInfo()
        self.updateLabelRadiationDoseInfo()


    def updateLabelRecordCountInfo(self):
        self.lblRecordCount.setText(u'Количество записей: %d' % len(self.modelRadiationDose.idList()))


    def updateLabelActionsSumInfo(self):
        self.lblActionSum.setText(u'Сумма количества действий: %.1f' % self.modelRadiationDose.actionsSum())


    def updateLabelPhotosSumInfo(self):
        self.lblPhotosSum.setText(u'Сумма количества снимков: %d' % self.modelRadiationDose.photosSum())


    def updateLabelRadiationDoseInfo(self):
        info = self.modelRadiationDose.radiationDoseSum()
        self.lblDoseSum.setRadiationDoseInfo(info)


    @pyqtSignature('int')
    def on_btnRadiationDosePrint_printByTemplate(self, templateId):
        context = CInfoContext()
        clientInfo = CClientInfo(context, self.clientId)
        items = []
        for row in xrange(self.modelRadiationDose.rowCount()):
            items.append({
                'date': CDateInfo(forceDate(self.modelRadiationDose.data(self.modelRadiationDose.index(row, 0)))),
                'actionType': forceString(self.modelRadiationDose.data(self.modelRadiationDose.index(row, 1))),
                'person': forceString(self.modelRadiationDose.data(self.modelRadiationDose.index(row, 2))),
                'amount': forceDouble(self.modelRadiationDose.data(self.modelRadiationDose.index(row, 3))),
                'photosCount': forceDouble(self.modelRadiationDose.data(self.modelRadiationDose.index(row, 4))),
                'radiationDose': forceDouble(self.modelRadiationDose.data(self.modelRadiationDose.index(row, 5))),
                'radiationDoseUnit': forceString(self.modelRadiationDose.data(self.modelRadiationDose.index(row, 6))),
            })
        data = {
            'client': clientInfo,
            'items': items,
        }
        QtGui.qApp.call(self, applyTemplate, (self, templateId, data))


    @pyqtSignature('')
    def _printSignalSheetReport(self):
        def formatClientInfo(info):
            return u'\n'.join([u'ФИО: %s'           % info.fullName,
                               u'Дата рождения: %s' % formatDate(info.birthDate),
                               u'Пол: %s'           % info.sex,
                               u'Код: %d'           % info.id])

        doc    = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Сигнальный лист учета дозы рентгеновского облучения')
        cursor.setCharFormat(CReportBase.TableBody)
        cursor.insertBlock()
        clientInfo = getClientInfoEx(self.clientId)
        cursor.insertText(formatClientInfo(clientInfo))
        cursor.insertBlock()

        tableColumns = [
            ('2%', [u'№' ], CReportBase.AlignLeft),
            ('10%', [u'Дата' ], CReportBase.AlignLeft),
            ('20%', [u'Вид рентгенологического исследования'], CReportBase.AlignLeft),
            ('10%', [u'Количество'], CReportBase.AlignRight),
            ('10%', [u'Количество снимков'], CReportBase.AlignRight),
            ('15%', [u'Суммарная доза облучения'], CReportBase.AlignRight),
            ('10%', [u'Единица измерения'], CReportBase.AlignRight),
        ]
        table = createTable(cursor, tableColumns)

        for idRow, id in enumerate(self.modelRadiationDose.idList()):
            values = [idRow+1,
                      forceString(self.modelRadiationDose.data(self.modelRadiationDose.index(idRow, self.modelRadiationDose.columnIndex(u'Дата выполнения')))),
                      forceString(self.modelRadiationDose.data(self.modelRadiationDose.index(idRow, self.modelRadiationDose.columnIndex(u'Тип действия')))),
                      "%d" % forceDouble(self.modelRadiationDose.data(self.modelRadiationDose.index(idRow, self.modelRadiationDose.columnIndex(u'Количество')))),
                      "%d" % self.modelRadiationDose.getPhotosAccount(id),
                      "%f" % forceDouble(self.modelRadiationDose.data(self.modelRadiationDose.index(idRow, self.modelRadiationDose.columnIndex(u'Доза')))),
                      forceString(self.modelRadiationDose.data(self.modelRadiationDose.index(idRow, self.modelRadiationDose.columnIndex(u'Ед.из'))))
                     ]

            i = table.addRow()
            for column, value in enumerate(values):
                table.setText(i, column, value)

        i = table.addRow()
        table.setText(i, 0, u'Итого')
        table.setText(i, 3, "%d" % self.modelRadiationDose.actionsSum())
        table.setText(i, 4, "%d" % self.modelRadiationDose.photosSum())
        table.setText(i, 5, "%f" % self.modelRadiationDose.dosesSum())
        table.setText(i, 6, "%s" % self.modelRadiationDose.unitsSum())

        cursor.movePosition(QtGui.QTextCursor.End)

        result = '          '.join(['\n\n\n' + forceString(QDate.currentDate()), u'ФИО: %s' % getPersonName(QtGui.qApp.userId)])
        cursor.insertText(result)
        cursor.insertBlock()

        view = CReportViewDialog(self)
        view.setText(doc)
        view.exec_()


    def _printRadiationLoadAccountingReport(self):

        def getServiceCode(actionId):
            stmt = """
            SELECT 
              s.code
            FROM Action a
              LEFT JOIN ActionType at ON at.id = a.actionType_id
              LEFT JOIN rbService s ON s.id = at.nomenclativeService_id
            WHERE a.id = {0}""".format(actionId)

            query = QtGui.qApp.db.query(stmt)
            code = ''
            if query.next():
                code = forceString(query.value(0))
            return code


        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        blockFormat = QTextBlockFormat()
        blockFormat.setAlignment(Qt.AlignCenter)
        cursor.setBlockFormat(blockFormat)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(u'Лист учета лучевой нагрузки')
        cursor.setCharFormat(CReportBase.TableBody)
        cursor.insertBlock()

        tableColumns = [
            ('10%', [u'Дата'], CReportBase.AlignLeft),
            ('50%', [u'Наименование рентгенологического исследования, исследования с помощью радионуклидов, метода радиационной терапии, метода лечения с помощью лучевого воздействия, иного метода диагностики или лечения, сопровождающегося лучевой нагрузкой'], CReportBase.AlignLeft),
            ('20%', [u'Код по номенклатуре медицинских услуг'], CReportBase.AlignRight),
            ('20%', [u'Величина лучевой нагрузки (доза), милизиверт (м3в)'], CReportBase.AlignRight),
        ]
        table = createTable(cursor, tableColumns)

        for idRow, id in enumerate(self.modelRadiationDose.idList()):
            values = [
                        forceString(self.modelRadiationDose.data(self.modelRadiationDose.index(idRow, self.modelRadiationDose.columnIndex(u'Дата выполнения')))),
                        forceString(self.modelRadiationDose.data(self.modelRadiationDose.index(idRow, self.modelRadiationDose.columnIndex(u'Тип действия')))).split("|")[1],
                        getServiceCode(id),
                        "%f" % forceDouble(self.modelRadiationDose.data(self.modelRadiationDose.index(idRow, self.modelRadiationDose.columnIndex(u'Доза'))))
                     ]

            i = table.addRow()
            for column, value in enumerate(values):
                table.setText(i, column, value)

        i = table.addRow()
        table.setText(i, 0, u'Итого:')
        table.setText(i, 1, u"   ")
        table.setText(i, 2, u"   ")
        table.setText(i, 3, "%f" % self.modelRadiationDose.dosesSum())

        cursor.movePosition(QtGui.QTextCursor.End)

        result = '          '.join(['\n\n\n' + forceString(QDate.currentDate()), u'ФИО: %s' % getPersonName(QtGui.qApp.userId)])
        cursor.insertText(result)
        cursor.insertBlock()

        view = CReportViewDialog(self)
        view.setText(doc)
        view.exec_()

# #######################################################

class CRadiationDoseCol(CCol):
    def __init__(self, title, fields, defaultWidth):
        CCol.__init__(self, title, fields, defaultWidth, 'l')
        self._cacheValues = {}


    def format(self, values):
        actionId = forceRef(values[0])
        value = self._cacheValues.get(actionId, None)
        if value is None:
            db = QtGui.qApp.db

            tableAction = db.table('Action')
            tableActionProperty = db.table('ActionProperty')
            tableActionPropertyType = db.table('ActionPropertyType')
            tableActionPropertyDouble = db.table('ActionProperty_Double')

            queryTable = tableAction
            queryTable = queryTable.innerJoin(tableActionProperty, tableActionProperty['action_id'].eq(tableAction['id']))
            queryTable = queryTable.innerJoin(tableActionPropertyType, tableActionPropertyType['id'].eq(tableActionProperty['type_id']))
            queryTable = queryTable.innerJoin(tableActionPropertyDouble, tableActionPropertyDouble['id'].eq(tableActionProperty['id']))

            cond = [tableAction['id'].eq(actionId),
                    tableActionPropertyType['typeName'].eq(u'Доза облучения')]

            record = db.getRecordEx(queryTable, tableActionPropertyDouble['value'].name(), cond)
            value = QVariant("%.9f" % forceDouble(record.value('value'))) if record else CCol.invalid
            self._cacheValues[actionId] = value

        return value


class CRadiationDoseUnitCol(CCol):
    def __init__(self, title, fields, defaultWidth):
        CCol.__init__(self, title, fields, defaultWidth, 'l')
        self._cacheValues = {}


    def format(self, values):
        actionId = forceRef(values[0])
        value = self._cacheValues.get(actionId, None)
        if value is None:
            db = QtGui.qApp.db

            tableAction = db.table('Action')
            tableActionType = db.table('ActionType')
            tableActionPropertyType = db.table('ActionPropertyType')
            tableUnit = db.table('rbUnit')

            queryTable = tableAction
            queryTable = queryTable.innerJoin(tableActionType, tableActionType['id'].eq(tableAction['actionType_id']))
            queryTable = queryTable.innerJoin(tableActionPropertyType, tableActionPropertyType['actionType_id'].eq(tableActionType['id']))
            queryTable = queryTable.innerJoin(tableUnit, tableUnit['id'].eq(tableActionPropertyType['unit_id']))

            cond = [tableAction['id'].eq(actionId),
                    tableActionPropertyType['typeName'].eq(u'Доза облучения')]

            record = db.getRecordEx(queryTable, [tableUnit['name'].name(), tableUnit['code'].name()], cond)
            value = QVariant(' | '.join([
                                         forceString(record.value('code')),
                                         forceString(record.value('name'))
                                        ]
                                       )
                            ) if record else CCol.invalid
            self._cacheValues[actionId] = value

        return value


class CPhotosAccountCol(CCol):
    def __init__(self, model, title, fields, defaultWidth):
        CCol.__init__(self, title, fields, defaultWidth, 'r')
        self._model = model
        self._cacheValues = {}

    def format(self, values):
        actionId = forceRef(values[0])
        value = self._cacheValues.get(actionId, None)
        if value is None:
            photosAccount = self._model.getPhotosAccount(actionId)
            value = QVariant("%d" % photosAccount) if photosAccount else CCol.invalid
            self._cacheValues[actionId] = value
        return value


class CRadiationDoseModel(CTableModel):
    def __init__(self, parent):
        CTableModel.__init__(self, parent)
        self._columnNames = []
        self.addColumn(CDateCol(u'Дата выполнения', ['endDate'], 20))
        self.addColumn(CActionTypeCol(u'Тип действия', 30, 2))
        self.addColumn(CRefBookCol(u'Исполнитель', ['person_id'], 'vrbPersonWithSpeciality', 30))
        self.addColumn(CSumCol(u'Количество', ['amount'], 14))
        self.addColumn(CPhotosAccountCol(self, u'Кол.-во снимков', ['id'], 14))
        self.addColumn(CRadiationDoseCol(u'Доза', ['id'], 10))
        self.addColumn(CRadiationDoseUnitCol(u'Ед.из', ['id'], 12))
        self.setTable('Action', recordCacheCapacity=None)
        self.context = CInfoContext()
        self.headerSortingCol = {}


    def addColumn(self, col):
        self._columnNames.append(forceString(col.title()))
        CTableModel.addColumn(self, col)

    def columnIndex(self, columnTitle):
        return self._columnNames.index(columnTitle)

    def getAction(self, id):
        return self.context.getInstance(CActionInfo, id)

    def getPhotosAccount(self, id):
        currentAction = self.getAction(id)
        photosString = currentAction[u"Количество снимков"].value if currentAction.__contains__(u"Количество снимков") else "0"
        try:
            return forceInt(photosString)
        except:
            return 0

    def actionsSum(self):
        result = 0
        for id in self._idList:
            result += forceDouble(self.getRecordById(id).value('amount'))
        return result

    def photosSum(self):
        result = 0
        for id in self._idList:
            result += self.getPhotosAccount(id)
        return result

    def unitsSum(self):
        radiationDoseUnitColumnIndex = self.columnIndex(u'Ед.из')
        result = []
        for row in xrange(self.rowCount()):
            unit = forceString(self.data(self.index(row, radiationDoseUnitColumnIndex)))
            result.append(unit)
        result = set(result)
        result = ', '.join(value for value in result)
        return result

    def dosesSum(self):
        radiationDoseColumnIndex = self.columnIndex(u'Доза')
        result = 0.00
        for row in xrange(self.rowCount()):
            radiationDose = forceDouble(self.data(self.index(row, radiationDoseColumnIndex)))
            result += radiationDose
        return result

    def radiationDoseSum(self):
        radiationDoseColumnIndex = self.columnIndex(u'Доза')
        radiationDoseUnitColumnIndex = self.columnIndex(u'Ед.из')
        result = {'total':0}
        for row in xrange(self.rowCount()):
            unit = forceString(self.data(self.index(row, radiationDoseUnitColumnIndex)))
            radiationDose = forceDouble(self.data(self.index(row, radiationDoseColumnIndex)))
            result['total'] += radiationDose
            if not unit in result.keys():
                result[unit] = radiationDose
            else:
                result[unit] += radiationDose
        return result
