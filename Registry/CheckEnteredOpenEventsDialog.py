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

from PyQt4         import QtGui
from PyQt4.QtCore  import Qt, QObject, QVariant, pyqtSignature, SIGNAL

from library.crbcombobox import CRBComboBox
from library.DialogBase  import CDialogBase
from library.TableModel  import CCol, CDateTimeFixedCol, CEnumCol, CRefBookCol, CTableModel, CTextCol 
from library.Utils       import forceRef
from Registry.Utils      import getClientBanner

from Ui_CheckEnteredOpenEventsDialog import Ui_CheckEnteredOpenEventsDialog


class CICDCol(CCol):
    def __init__(self, title, fields, defaultWidth, alignment):
        CCol.__init__(self, title, fields, defaultWidth, alignment)
        self.valuesCache = {}
    def format(self, values):
        id = forceRef(values[0])
        val = self.valuesCache.get(id)
        if val:
            return val
        else:
            stmt = 'SELECT Diagnosis.MKB from Diagnostic INNER JOIN Diagnosis ON Diagnosis.id=Diagnostic.diagnosis_id WHERE Diagnosis.id = (SELECT MAX(diagnosis_id) FROM Diagnostic WHERE event_id=%d AND deleted=0) AND Diagnosis.deleted=0' % id
            query = QtGui.qApp.db.query(stmt)
            if query.first():
                val = query.value(0)
            else:
                val = QVariant()
            self.valuesCache[id] = val
            return val

# WTF? что это значит?
class CCheckEnteredOpenEvents(CDialogBase, Ui_CheckEnteredOpenEventsDialog):
    def __init__(self, parent, eventIdList = [], clientId = None, date= None):
        CDialogBase.__init__(self, parent)
        self.setupUi(self)
        self.btnResult = None # WTF? btnResult это вовсе не кнопка
        self.resultEventId = None
        self.eventIdList = eventIdList
        self.clientId = clientId
        self.date = date
        self.setup( [
            CDateTimeFixedCol(u'Дата начала', ['setDate'],  10),
            CRefBookCol(u'Тип', ['eventType_id'], 'EventType', 40),
            CRefBookCol(u'МЭС',  ['MES_id'], 'mes.MES', 15, CRBComboBox.showCode),
            CICDCol(u'МКБ', ['id'], 5, 'l'),
            CRefBookCol(u'Врач назначивший', ['setPerson_id'], 'vrbPersonWithSpeciality', 15),
            CRefBookCol(u'Врач выполнивший', ['execPerson_id'], 'vrbPersonWithSpeciality', 15),
            CEnumCol(u'Порядок', ['order'], [u'не определен', u'плановый', u'экстренный', u'самотёком', u'принудительный', u'внутренний перевод', u'неотложная'], 5),
            CTextCol(u'Примечания',     ['note'], 6)
            ], 'Event', ['id'])
        self.setWindowTitleEx(u'Открытые события')


    def setup(self, cols, tableName, order):
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        self.props = {}
        self.order = order
        self.model = CTableModel(self, cols, tableName)
        self.model.setIdList(self.eventIdList)
        self.tblOpenEvents.setModel(self.model)
        if self.eventIdList:
            self.tblOpenEvents.selectRow(0)
        if self.clientId:
            self.txtClientInfoEventsBrowser.setHtml(getClientBanner(self.clientId, self.date))
        else:
            self.txtClientInfoEventsBrowser.setText('')
        self.btnClose.setFocus(Qt.TabFocusReason)
        QObject.connect(self.tblOpenEvents.horizontalHeader(), SIGNAL('sectionClicked(int)'), self.setSort)


    def currentItemId(self):
        return self.tblOpenEvents.currentItemId()


    def select(self):
        table = self.model.table()
        return QtGui.qApp.db.getIdList(table.name(), 'id', table['id'].inlist(self.eventIdList), self.order)


    def renewList(self):
        idList = self.select()
        self.tblOpenEvents.setIdList(idList)


    @pyqtSignature('')
    def on_btnClose_clicked(self):
        self.resultEventId = None
        self.btnResult = 0
        self.close()


    @pyqtSignature('')
    def on_btnOpen_clicked(self):
        event_id = self.currentItemId()
        self.resultEventId = event_id if event_id else None
        self.btnResult = 2
        self.close()


    @pyqtSignature('')
    def on_btnReverse_clicked(self):
        self.resultEventId = None
        self.btnResult = 1
        self.close()


    @pyqtSignature('')
    def on_btnCreate_clicked(self):
        self.resultEventId = None
        self.btnResult = 3
        self.close()


    def setSort(self, col):
        name = self.model.cols()[col].fields()[0]
        self.order = name
        header=self.tblOpenEvents.horizontalHeader()
        header.setSortIndicatorShown(True)
        header.setSortIndicator(col, Qt.AscendingOrder)
        self.renewList()


    def destroy(self):
        pass
