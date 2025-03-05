# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2020 SAMSON Group. All rights reserved.
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

from Events.EventInfo import CEventInfo
from library.DialogBase         import CConstructHelperMixin
from library.PrintInfo          import CInfoContext
from library.PrintTemplates import CPrintAction, addButtonActions, additionalCustomizePrintButton, applyTemplate
from library.TableModel         import CTableModel, CCol, CDateCol, CRefBookCol, CSumCol
from library.Utils              import forceDouble, forceInt, forceRef, forceString, formatDate

from Events.ActionInfo          import CActionInfo
from Events.ActionTypeCol       import CActionTypeCol
from Registry.Utils import getClientInfoEx
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

        self.addObject('actExpertPrint', CPrintAction(u'Сигнальный лист учета дозы рентгеновского облучения', None, self, self))
        self.addObject('actRadiationLoadAccounting', CPrintAction(u'Лист учета лучевых нагрузок', None, self, self))

        self.btnRadiationDosePrint_actions = [{'action': self.actExpertPrint, 'slot': self.on_btnRadiationDose_printByTemplate},
                                              {'action': self.actRadiationLoadAccounting, 'slot': self.on_btnRadiationLoadAccounting_printByTemplate},]


        addButtonActions(self, self.btnRadiationDosePrint, self.btnRadiationDosePrint_actions)
        additionalCustomizePrintButton(self, self.btnRadiationDosePrint, 'RadiationDose', self.btnRadiationDosePrint_actions)


        self.clientId = None
        self._onlyTotalDoseSumInfo = True
        self.setSortable(self.tblRadiationDose, lambda: self.setClientId(self.clientId))

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

    def setClientId(self, clientId):
        self.clientId = clientId

        db = QtGui.qApp.db

        tableEvent = db.table('Event')
        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        tableActionPropertyType = db.table('ActionPropertyType')

        queryTable = tableAction

        queryTable = queryTable.leftJoin(tableActionType,
                                          tableActionType['id'].eq(tableAction['actionType_id']))
        queryTable = queryTable.leftJoin(tableActionPropertyType,
                                          tableActionPropertyType['actionType_id'].eq(tableActionType['id']))
        queryTable = queryTable.leftJoin(tableEvent,
                                          tableEvent['id'].eq(tableAction['event_id']))

        cond = [tableEvent['client_id'].eq(clientId),
                tableActionPropertyType['typeName'].eq(u'Доза облучения'),
                tableAction['deleted'].eq(0)]

        orderBY = 'Action.endDate DESC'
        for key, value in self.tblRadiationDose.model().headerSortingCol.items():
            if value:
                ASC = u'ASC'
            else:
                ASC = u'DESC'
            if key == 0:
                orderBY = u'Action.endDate %s' % ASC
            elif key == 1:
                orderBY = u"(select name from ActionType where id = Action.actionType_id) %s" % ASC
            elif key == 2:
                orderBY = u'(select name from vrbPersonWithSpeciality where id = Action.person_id) %s' % ASC
            elif key == 3:
                orderBY = u'Action.amount %s' % ASC
            elif key == 4:
                orderBY = u'''(Select api.value from ActionProperty ap
                                left join ActionPropertyType apt on apt.id = ap.type_id
                                left join ActionProperty_Integer api on api.id = ap.id
                                where apt.name = 'Количество снимков' and ap.action_id = Action.id) %s''' % ASC
            elif key == 5:
                orderBY = u'''(Select apd.value from ActionProperty ap
                                left join ActionPropertyType apt on apt.id = ap.type_id
                                left join ActionProperty_Double apd on apd.id = ap.id
                                where apt.typeName = 'Доза облучения' and ap.action_id = Action.id) %s''' % ASC
            elif key == 6:
                orderBY = u'''(Select concat_ws(' | ',rbUnit.code, rbUnit.name) from ActionProperty ap
                                left join ActionPropertyType apt on apt.id = ap.type_id
                                left join ActionProperty_Double apd on apd.id = ap.id
                                left join rbUnit on rbUnit.id = apt.unit_id
                                where apt.typeName = 'Доза облучения' and ap.action_id = Action.id) %s''' % ASC

        actionIdList = db.getDistinctIdList(queryTable, tableAction['id'].name(), cond, orderBY)

        self.modelRadiationDose.setIdList(actionIdList)

        #self.updateLabelsInfo()

    def updateLabelsInfo(self):
        self.updateLabelRecordCountInfo()
        self.updateLabelActionsSumInfo()
        self.updateLabelPhotosSumInfo()
        self.updateLabelRadiationDoseInfo()


    def updateLabelRecordCountInfo(self):
        self.lblRecordCount.setText(u'Количество записей: %d'%len(self.modelRadiationDose.idList()))


    def updateLabelActionsSumInfo(self):
        self.lblActionSum.setText(u'Сумма количества действий: %.1f'%self.modelRadiationDose.actionsSum())


    def updateLabelPhotosSumInfo(self):
        self.lblPhotosSum.setText(u'Сумма количества снимков: %d'%self.modelRadiationDose.photosSum())


    def updateLabelRadiationDoseInfo(self):
        info = self.modelRadiationDose.radiationDoseSum()
        self.lblDoseSum.setRadiationDoseInfo(info)


    @pyqtSignature('int')
    def on_btnRadiationDosePrint_printByTemplate(self, templateId):
        temp = 0
        listValues = []
        for idRow, id in enumerate(self.modelRadiationDose.idList()):
            if temp == 0:
                context = CInfoContext()
                actionInfo = context.getInstance(CActionInfo, id)
                event = context.getInstance(CEventInfo, actionInfo.event.id)
            values = [
                      forceString(self.modelRadiationDose.data(self.modelRadiationDose.index(
                            idRow, self.modelRadiationDose.columnIndex(u'Дата выполнения')))),
                      forceString(self.modelRadiationDose.data(self.modelRadiationDose.index(
                            idRow, self.modelRadiationDose.columnIndex(u'Тип действия')))),
                      "%d"%forceDouble(self.modelRadiationDose.data(self.modelRadiationDose.index(
                            idRow, self.modelRadiationDose.columnIndex(u'Количество')))),
                      "%d"%self.modelRadiationDose.getPhotosAccount(id),
                      "%f"%forceDouble(self.modelRadiationDose.data(self.modelRadiationDose.index(
                            idRow, self.modelRadiationDose.columnIndex(u'Доза')))),
                      forceString(id)
                     ]# 141514
            listValues.append([values, actionInfo, event])
        data = {'rows': listValues, 'client': event.client}

        QtGui.qApp.call(self, applyTemplate, (self, templateId, data))

    @pyqtSignature('')
    def on_btnRadiationDose_printByTemplate(self):
        def formatClientInfo(clientInfo):
            return u'\n'.join([u'ФИО: %s'           % clientInfo.fullName,
                               u'Дата рождения: %s' % formatDate(clientInfo.birthDate),
                               u'Пол: %s'           % clientInfo.sex,
                               u'Код: %d'           % clientInfo.id])

        def formatRadiationDoseSumInfo(radiationDoseSumInfo):
            return '\n'.join(['%s: %f' % (key, item) for key, item in radiationDoseSumInfo.items() if key != 'total']+[u'Всего: %f'%radiationDoseSumInfo['total']])

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
                      forceString(self.modelRadiationDose.data(self.modelRadiationDose.index(
                            idRow, self.modelRadiationDose.columnIndex(u'Дата выполнения')))),
                      forceString(self.modelRadiationDose.data(self.modelRadiationDose.index(
                            idRow, self.modelRadiationDose.columnIndex(u'Тип действия')))),
                      "%d"%forceDouble(self.modelRadiationDose.data(self.modelRadiationDose.index(
                            idRow, self.modelRadiationDose.columnIndex(u'Количество')))),
                      "%d"%self.modelRadiationDose.getPhotosAccount(id),
                      "%f"%forceDouble(self.modelRadiationDose.data(self.modelRadiationDose.index(
                            idRow, self.modelRadiationDose.columnIndex(u'Доза')))),
                      forceString(self.modelRadiationDose.data(self.modelRadiationDose.index(
                            idRow, self.modelRadiationDose.columnIndex(u'Ед.из'))))
                     ]

            i = table.addRow()
            for column, value in enumerate(values):
                table.setText(i, column, value)

        i = table.addRow()
        table.setText(i, 0, u'Итого')
        table.setText(i, 3, "%d"%self.modelRadiationDose.actionsSum())
        table.setText(i, 4, "%d"%self.modelRadiationDose.photosSum())
        table.setText(i, 5, "%f"%self.modelRadiationDose.dosesSum())
        table.setText(i, 6, "%s"%self.modelRadiationDose.unitsSum())

        cursor.movePosition(QtGui.QTextCursor.End)

        result = '          '.join(['\n\n\n'+forceString(QDate.currentDate()),
                                  u'ФИО: %s' % getPersonName(QtGui.qApp.userId)])
        cursor.insertText(result)
        cursor.insertBlock()

        view = CReportViewDialog(self)
        view.setText(doc)
        view.exec_()



    @pyqtSignature('')
    def on_btnRadiationLoadAccounting_printByTemplate(self):

        def getrbServiceCode(actionId):
            stmt = """
            SELECT 
              s.code
            FROM Action a
              LEFT JOIN ActionType at ON at.id = a.actionType_id
              LEFT JOIN rbService s ON s.id = at.nomenclativeService_id
            WHERE a.id = {0}""".format(actionId)

            query = QtGui.qApp.db.query(stmt)
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
                        getrbServiceCode(id),
                        "%f"%forceDouble(self.modelRadiationDose.data(self.modelRadiationDose.index(idRow, self.modelRadiationDose.columnIndex(u'Доза'))))
                     ]

            i = table.addRow()
            for column, value in enumerate(values):
                table.setText(i, column, value)

        i = table.addRow()
        table.setText(i, 0, u'Итого:')
        table.setText(i, 1, u"   ")
        table.setText(i, 2, u"   ")
        table.setText(i, 3, "%f"%self.modelRadiationDose.dosesSum())

        cursor.movePosition(QtGui.QTextCursor.End)

        result = '          '.join(['\n\n\n'+forceString(QDate.currentDate()),
                                  u'ФИО: %s' % getPersonName(QtGui.qApp.userId)])
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
        # if value is None:
        db = QtGui.qApp.db

        tableAction = db.table('Action')
        tableActionProperty = db.table('ActionProperty')
        tableActionPropertyType = db.table('ActionPropertyType')
        tableActionPropertyDouble = db.table('ActionProperty_Double')

        queryTable = tableAction

        queryTable = queryTable.innerJoin(tableActionProperty,
                                          tableActionProperty['action_id'].eq(tableAction['id']))
        queryTable = queryTable.innerJoin(tableActionPropertyType,
                                          tableActionPropertyType['id'].eq(tableActionProperty['type_id']))
        queryTable = queryTable.innerJoin(tableActionPropertyDouble,
                                          tableActionPropertyDouble['id'].eq(tableActionProperty['id']))

        cond = [tableAction['id'].eq(actionId),
                tableActionPropertyType['typeName'].eq(u'Доза облучения')]

        record = db.getRecordEx(queryTable, tableActionPropertyDouble['value'].name(), cond)
        value = QVariant("%.9f"%forceDouble(record.value('value'))) if record else CCol.invalid
        self._cacheValues[actionId] = value

        return value


class CRadiationDoseUnitCol(CCol):
    def __init__(self, title, fields, defaultWidth):
        CCol.__init__(self, title, fields, defaultWidth, 'l')
        self._cacheValues = {}


    def format(self, values):
        actionId = forceRef(values[0])
        value = self._cacheValues.get(actionId, None)
        # if value is None:
        db = QtGui.qApp.db

        tableAction = db.table('Action')
        tableActionType = db.table('ActionType')
        tableActionPropertyType = db.table('ActionPropertyType')
        tableUnit = db.table('rbUnit')

        queryTable = tableAction

        queryTable = queryTable.innerJoin(tableActionType,
                                          tableActionType['id'].eq(tableAction['actionType_id']))
        queryTable = queryTable.innerJoin(tableActionPropertyType,
                                          tableActionPropertyType['actionType_id'].eq(tableActionType['id']))
        queryTable = queryTable.innerJoin(tableUnit,
                                          tableUnit['id'].eq(tableActionPropertyType['unit_id']))

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
        # if value is None:
        photosAccount = self._model.getPhotosAccount(actionId)
        value = QVariant("%d"%photosAccount) if photosAccount else CCol.invalid
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





def getKerContext():
    return ['tempInvalid', 'tempInvalidList']