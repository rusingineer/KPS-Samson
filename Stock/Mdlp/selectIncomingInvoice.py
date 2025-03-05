# -*- coding: utf-8 -*-
# Заголовок будет потом,
# сейчас это "превью"
# -------------
# Это подборка документов типа 601 (move_order_notification)
# выбор одного из них и выборка содержимого (с раскрытием sscc)


from PyQt4.QtCore import Qt, pyqtSignature,  QAbstractTableModel, QTimer, QVariant
from PyQt4 import QtGui

from library.DialogBase import CDialogBase
from library.Utils import withWaitCursor

from connection import CMdlpConnection

from Ui_MoveOrderNotifications import Ui_moveOrderNotifications


def selectIncomingInvoiceFromMdlp(widget, connection, date, sender, receiver):
    dlg = CMoveOrderNotifications(widget)
    dlg.setFilter(date, sender, receiver)
    dlg.connection = connection
    dlg.exec_()
    return dlg.getDocumentIdAndContent()

class CDocumentContentItem(object):
    def __init__(self,
                 sscc,
                 sgtin,
                 batch,
                 expirationDate,
                 sum,
                 vat
                ):
        self.sscc = sscc
        self.sgtin = sgtin
        self.batch = batch
        self.expirationDate = expirationDate
        self.sum = sum
        self.vat = vat


# Нам нужен список входящих документов,
# В списке мы хотим показать:
# - Дату (из мета-информации? из документа?)
# - Номер (из документа)
# - Источник финансирования
# - Тип договора
# - Номер договора
# - Сумму
# - отправителя (если мы сподобимся искать по нескольким отправителям и не захотим регать все площадки как организации)
# - получателя (если мы сподобимся получать на несколько receiver
# - document_id?


class CMoveOrderNotifications(Ui_moveOrderNotifications, CDialogBase):
    def __init__(self, parent=None):
        CDialogBase.__init__(self, parent)
        self.addModels('Items', CMdlpDocumensModel(self))
#        self.addObject('actLoad', QAction(self))
        self.setupUi(self)
        self.tblItems.setModel(self.modelItems)
        self.connection  = None
        self.selectedRow = None
        self.autoLoad    = True
        self.date        = None
        self.sender      = None
        self.receiver    = None


    def exec_(self):
        self.show()
        if self.autoLoad:
            QTimer.singleShot(200, self.loadData) # 0.2 сек.
        return CDialogBase.exec_(self)


    def accept(self):
        index = self.tblItems.currentIndex()
        if index.isValid():
            self.selectedRow = index.row()
        CDialogBase.accept(self)


    def setFilter(self, date, sender, receiver):
        self.date = date
        self.sender = sender
        self.receiver = receiver


    def getDocumentIdAndContent(self):
        if self.selectedRow is not None:
            item = self.modelItems.items[self.selectedRow]
            content = []
            ssccs  = []
            sgtins = []
            for sscc, sgtin, sum, vat in item.content:
                if sscc:
                    ssccs.append(sscc)
                elif sgtin:
                    sgtins.append(sgtin)
            fhs = self.connection.getSsccFullHierarchyByList(ssccs)
            # python 2.6 позволяет только так:
            mapSsccToSgtinInfos = dict( (fh.sscc, fh.sgtins)
                                         for fh in fhs
                                      )
            # python 2.7 позволяет ещё так:
            # mapSsccToSgtinInfos = { fh.sscc: fh.sgtins for fh in fhs }
            succeedSgtinInfos, failedSgtinInfos = self.connection.getSgtinsByList(sgtins)
            mapSgtinToSgtinInfos = dict( (sgtinInfo.sgtin, sgtinInfo)
                                         for sgtinInfo in succeedSgtinInfos
                                       )
            for sscc, sgtin, sum, vat in item.content:
                if sscc:
                    sgtinInfos = mapSsccToSgtinInfos.get(sscc, [])
                    for sgtinInfo in sgtinInfos:
                        content.append(CDocumentContentItem(sscc,
                                                            sgtinInfo.sgtin,
                                                            sgtinInfo.batch,
                                                            sgtinInfo.expirationDate,
                                                            sum,
                                                            vat
                                                           )
                                      )
                else:
                    sgtinInfo = mapSgtinToSgtinInfos.get(sgtin)
                    batch = ''
                    if sgtinInfo:
                        batch = sgtinInfo.batch
                        expirationDate = sgtinInfo.expirationDate
                    else:
                        expirationDate = None
                    content.append(CDocumentContentItem(sscc,
                                                        sgtin,
                                                        batch,
                                                        expirationDate,
                                                        sum,
                                                        vat
                                                       )
                                  )
            return item.documentId, content
        else:
            return None, []


#    @withExceptionLog
    @withWaitCursor
    def loadData(self):
        self.modelItems.removeAllItems()

        if self.connection is None:
            self.connection = CMdlpConnection()
        connection = self.connection

        partners = {}
        branches = {}

        def getBranchName(sysId, branchId):
            if sysId not in partners:
                tmpPartners = connection.getPartners(sysId = sysId)
                if tmpPartners:
                    partner = tmpPartners[0]
                    partners[sysId] = partner.name or sysId
                    for branch in partner.branches:
                        tmpBranchId = branch.id
                        addr = branch.asString()
                        if tmpBranchId:
                            branches[tmpBranchId] = partners[sysId] +' ' + addr
            return branches.get(branchId) or partners.get(sysId) or '%s:%s'%(sysId, branchId)


        filter = {}
        if self.date:
            filter['begDate'] = self.date.addDays(-1)
            filter['endDate'] = self.date

        docs = connection.getIncomingDocuments(count      = 100,
                                               docType    = 601,
                                               senderId   = self.sender,
                                               receiverId = self.receiver,
                                               **filter
                                              )

        for metaDoc in docs:
            documentId = metaDoc.documentId
            if self.documentAlreadyUsed(documentId):
                continue
            outerDoc = connection.getDocument(documentId)
            doc = outerDoc.move_order_notification
            if doc.turnover_type == 1:
                total   = 0.0
                content = []
                for u in doc.order_details.union:
                    content.append( (unicode(u.sscc_detail.sscc) if u.sscc_detail else None,
                                     unicode(u.sgtin),
                                     float(u.cost or 0.0),
                                     float(u.vat_value or 0.0)
                                    )
                                  )
                    total += float(u.cost or 0)
                item = CMdlpDocumentDescr(date          = unicode(doc.doc_date),
                             number        = unicode(doc.doc_num),
                             financeSource = int(doc.source),
                             contractType  = int(doc.contract_type),
                             contractNumber= unicode(doc.contract_num),
                             sum           = total,
                             sender        = getBranchName(metaDoc.senderSysId, metaDoc.senderId),
                             receiver      = getBranchName(metaDoc.sysId,       metaDoc.receiverId),
                             documentId    = documentId,
                             sessionUi     = unicode(outerDoc.session_ui),
                             content       = content
                            )
            self.modelItems.addItem(item)


    def documentAlreadyUsed(self, documentId):
        from Stock.IncomingInvoiceEditDialog import CIncomingInvoiceEditDialog

        db = QtGui.qApp.db
        table = db.table('StockMotion')
        record = db.getRecordEx(table,
                                'id',
                                 db.joinAnd([ table['deleted'].eq(0),
                                              table['type'].eq(CIncomingInvoiceEditDialog.stockDocumentType), # Накладная от поставщика
                                              table['mdplBaseDocumentUuid'].eq(documentId)
                                            ]
                                           )
                               )
        return record is not None


    @pyqtSignature('QModelIndex')
    def on_tblItems_doubleClicked(self, index):
        self.selectedRow = index.row()
        self.close()


# 0 - Дату (из мета-информации? из документа?)
# 1 - Номер (из документа)
# 2 - Источник финансирования
# 3 - Тип договора
# 4 - Номер договора
# 5 - Сумму
# 6 - отправителя (если мы сподобимся искать по нескольким отправителям и не захотим регать все площадки как организации)
# 7 - получателя (если мы сподобимся получать на несколько receiver
# 8 - document_id?

class CMdlpDocumentDescr:
    headers = ( u'Номер',
                u'Дата',
                u'Источник финансирования',
                u'Тип договора',
                u'Номер договора',
                u'Сумма',
                u'Отправитель',
                u'Получатель',
                u'Идентификатор документа',
              )

    financeSources = { 1: u'собственные средства',
                       2: u'средства федерального бюджета',
                       3: u'средства регионального бюджета',
                       4: u'средства бюджетов внебюджетных фондов',
                       5: u'смешанные средства бюджетов',
                     }

    contractTypes  = { 1: u'купли продажи',
                       2: u'комиссия',
                       3: u'агентский',
                       4: u'передача на безвозмездной основе',
                       5: u'возврат контрактному производителю',
                       6: u'государственное лекарственное обеспечение',
                       7: u'договор консигнации',
                       8: u'собственные стредства',
                     }



    def __init__(self,
                       number=None,
                       date=None,
                       financeSource=None,
                       contractType = None,
                       contractNumber = None,
                       sum = None,
                       sender = None,
                       receiver = None,
                       documentId = None,
                       sessionUi = None,
                       content = None
                ):
        self.number = number
        self.date   = date
        self.financeSource = financeSource
        self.contractType = contractType
        self.contractNumber = contractNumber
        self.sum = sum
        self.sender = sender
        self.receiver = receiver
        self.documentId = documentId
        self.sessionUi = sessionUi
        self.content = content


    @classmethod
    def columnCount(cls):
        return len(cls.headers)


    @classmethod
    def header(cls, column):
        return cls.headers[column]


    def data(self, column):
        if column == 0: return self.number
        if column == 1: return self.date
        if column == 2: return self.financeSources.get(self.financeSource) or ('{%s}' % self.financeSource)
        if column == 3: return self.contractTypes.get(self.contractType) or ('{%s}' % self.contractType)
        if column == 4: return self.contractNumber
        if column == 5: return self.sum
        if column == 6: return self.sender
        if column == 7: return self.receiver
        if column == 8: return self.documentId
        return None


class CMdlpDocumensModel(QAbstractTableModel):
    def __init__(self, parent = 0):
        QAbstractTableModel.__init__(self, parent)
        self.items = []


    def columnCount(self, parent=None):
        return CMdlpDocumentDescr.columnCount()


    def rowCount(self, parent=None):
        return len(self.items)


    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return QVariant(CMdlpDocumentDescr.header(section))


    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            row = index.row()
            column = index.column()
            return QVariant(self.items[row].data(column))
        return QVariant()


    def removeAllItems(self):
        self.items = []
        self.reset()


    def addItem(self, item):
        self.items.append(item)
        self.reset()

