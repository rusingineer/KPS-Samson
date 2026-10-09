# -*- coding: utf-8 -*-

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import *

from Orgs.Utils import getOrgStructureFullName
from Ui_s11main import _fromUtf8
from library.DateEdit import CDateEdit
from library.Utils      import *
from library.database   import *
from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable

from Ui_AttachmentList import Ui_AttachmentListDialog

def getQuery(orgStructure_id, createBegDate,createEndDate, attachBegDate, attachEndDate):
    db = QtGui.qApp.db
    stmt = u"""
        select
          rbPolicyKind.name as policyType,
          soc_attachments.policySerial,
          soc_attachments.policyNumber,
          soc_attachments.lastName,
          soc_attachments.firstName,
          soc_attachments.patrName,
          upper(soc_attachments.sex) as sex,
          soc_attachments.birthDate,
          soc_attachments.attach_area,
          soc_attachments.attach_date,
          (SELECT OrgStructure_mo.name FROM OrgStructure as OrgStructure_mo WHERE OrgStructure_mo.bookkeeperCode = soc_attachments.attach_mo AND OrgStructure_mo.deleted = 0 LIMIT 1) as attach_mo,
          soc_attachments.createDate,
          soc_attachments.client_id,
          soc_attachments.deAttachType
        from soc_attachments
            %(org_join)s
            left join rbPolicyKind on rbPolicyKind.regionalCode = soc_attachments.policyType
        where soc_attachments.serviceMethod = 1
        %(createDate)s
        %(attachDate)s
        
        order by lastName, firstName
        """
    if orgStructure_id:
        query = QtGui.qApp.db.query("select areaType from OrgStructure where id = %d" % orgStructure_id)
        query.first()
        areaType = query.value(0).toInt()[0]
        if areaType == 0:
            org_join = u"""
                inner join (select OrgStructure.id, OrgStructure.bookkeeperCode
                            from OrgStructure
                              left join OrgStructure as Parent1 on Parent1.id = OrgStructure.parent_id
                              left join OrgStructure as Parent2 on Parent2.id = Parent1.parent_id
                              left join OrgStructure as Parent3 on Parent3.id = Parent2.parent_id
                              left join OrgStructure as Parent4 on Parent4.id = Parent3.parent_id
                              left join OrgStructure as Parent5 on Parent5.id = Parent4.parent_id
                            where %d in (OrgStructure.id, Parent1.id, Parent2.id, Parent3.id, Parent4.id, Parent5.id) limit 1
                           ) as OrgStructure on OrgStructure.bookkeeperCode = soc_attachments.attach_mo
                """ % orgStructure_id
        else:
            org_join = u"""
                inner join (select OrgStructure.id, OrgStructure.infisInternalCode
                           from OrgStructure
                             left join OrgStructure as Parent1 on Parent1.id = OrgStructure.parent_id
                             left join OrgStructure as Parent2 on Parent2.id = Parent1.parent_id
                             left join OrgStructure as Parent3 on Parent3.id = Parent2.parent_id
                             left join OrgStructure as Parent4 on Parent4.id = Parent3.parent_id
                             left join OrgStructure as Parent5 on Parent5.id = Parent4.parent_id
                           where %d in (OrgStructure.id, Parent1.id, Parent2.id, Parent3.id, Parent4.id, Parent5.id) limit 1
                          ) as OrgStructure on OrgStructure.infisInternalCode = soc_attachments.attach_area
                """ % orgStructure_id
    else:
        org_join = u''
    if createBegDate or createEndDate:
        if createBegDate:
            createStr = u' and DATE(soc_attachments.createDate) >= {createBegDate} '.format(createBegDate=db.formatDate(createBegDate))
        if createEndDate:
            createStr = u' and DATE(soc_attachments.createDate) <= {createEndDate} '.format(createEndDate=db.formatDate(createEndDate))
    else:
        createStr = u''
    if attachBegDate or attachEndDate:
        if attachBegDate:
            attachStr = u'  and DATE(soc_attachments.attach_date) >= {attachBegDate}'.format(attachBegDate=db.formatDate(attachBegDate))
        if attachEndDate:
            attachStr = u' and DATE(soc_attachments.attach_date) <= {attachEndDate} '.format(attachEndDate=db.formatDate(attachEndDate))
    else:
        attachStr = u''

    stmt = stmt % {'org_join': org_join,
                    'createDate' : createStr,
                    'attachDate' : attachStr
                   }
    return QtGui.qApp.db.query(stmt)


class CDeAttachmentListDialog(QtGui.QDialog, Ui_AttachmentListDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)

        self.resize(326, 140)
        self.newLayout = QtGui.QGridLayout()

        self.horizontalCreateLayout = QtGui.QHBoxLayout()
        self.lblCreateBegin = QtGui.QLabel(u'Дата получения данных c',self)
        self.lblCreateBegin.setMinimumSize(QtCore.QSize(125, 0))
        self.horizontalCreateLayout.addWidget(self.lblCreateBegin)
        self.edtCreateBegDate = CDateEdit(self)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.edtCreateBegDate.sizePolicy().hasHeightForWidth())
        self.edtCreateBegDate.setSizePolicy(sizePolicy)
        self.edtCreateBegDate.setMinimumSize(QtCore.QSize(83, 0))
        self.edtCreateBegDate.setCalendarPopup(True)
        self.horizontalCreateLayout.addWidget(self.edtCreateBegDate)
        self.lblCreateEnd = QtGui.QLabel(u' по ',self)
        self.horizontalCreateLayout.addWidget(self.lblCreateEnd)
        self.edtCreateEndDate = CDateEdit(self)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.edtCreateEndDate.sizePolicy().hasHeightForWidth())
        self.edtCreateEndDate.setSizePolicy(sizePolicy)
        self.edtCreateEndDate.setMinimumSize(QtCore.QSize(83, 0))
        self.edtCreateEndDate.setCalendarPopup(True)
        self.horizontalCreateLayout.addWidget(self.edtCreateEndDate)
        spacerItem = QtGui.QSpacerItem(30, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalCreateLayout.addItem(spacerItem)

        self.newLayout.addLayout(self.horizontalCreateLayout, 0, 0, 1, 2)

        self.horizontalAttachLayout = QtGui.QHBoxLayout()
        self.lblAttachBegin = QtGui.QLabel(u'Дата открепления с',self)
        self.lblAttachBegin.setMinimumSize(QtCore.QSize(125, 0))
        self.horizontalAttachLayout.addWidget(self.lblAttachBegin)
        self.edtAttachBegDate = CDateEdit(self)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.edtAttachBegDate.sizePolicy().hasHeightForWidth())
        self.edtAttachBegDate.setSizePolicy(sizePolicy)
        self.edtAttachBegDate.setMinimumSize(QtCore.QSize(83, 0))
        self.edtAttachBegDate.setCalendarPopup(True)
        self.horizontalAttachLayout.addWidget(self.edtAttachBegDate)
        self.lblAttachEnd = QtGui.QLabel(u' по ', self)
        self.horizontalAttachLayout.addWidget(self.lblAttachEnd)
        self.edtAttachEndDate = CDateEdit(self)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.edtAttachEndDate.sizePolicy().hasHeightForWidth())
        self.edtAttachEndDate.setSizePolicy(sizePolicy)
        self.edtAttachEndDate.setMinimumSize(QtCore.QSize(83, 0))
        self.edtAttachEndDate.setCalendarPopup(True)
        self.horizontalAttachLayout.addWidget(self.edtAttachEndDate)
        spacerItem1 = QtGui.QSpacerItem(30, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalAttachLayout.addItem(spacerItem1)
        self.newLayout.addLayout(self.horizontalAttachLayout, 1, 0, 1, 2)

        self.gridLayout.addLayout(self.newLayout, 1, 0, 1, 2)

        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())

    def setTitle(self, title):
        self.setWindowTitle(title)

    def setParams(self, params):
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))
        self.edtCreateBegDate.setDate(params.get('createBegDate', None))
        self.edtCreateEndDate.setDate(params.get('createEndDate', None))
        self.edtAttachBegDate.setDate(params.get('attachBegDate', None))
        self.edtAttachEndDate.setDate(params.get('attachEndDate', None))

    def params(self):
        result = { 'orgStructureId': self.cmbOrgStructure.value(),
                   'createBegDate': self.edtCreateBegDate.date(),
                   'createEndDate': self.edtCreateEndDate.date(),
                   'attachBegDate': self.edtAttachBegDate.date(),
                   'attachEndDate': self.edtAttachEndDate.date() }
        return result


class CDeAttachmentListReport(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setPayPeriodVisible(False)
        self.setTitle(u'Список открепившихся граждан')

    def exec_(self):
        query = QtGui.qApp.db.query(u'select count(*) from soc_attachments')
        if query.first() and query.value(0).toInt()[0] > 0:
            CReport.exec_(self)
        else:
            QtGui.QMessageBox.warning(None,
                                      u'Внимание!',
                                      u'Проведите синхронизацию с Регистром приписанного населения',
                                      QtGui.QMessageBox.Ok)


    def getSetupDialog(self, parent):
        result = CDeAttachmentListDialog(parent)
        result.setTitle(self.title())
        return result

    def dumpParams(self, cursor, params):
        description = []
        orgStructureId = params.get('orgStructureId', None)
        if orgStructureId:
            description.append(u'подразделение: ' + getOrgStructureFullName(orgStructureId))
        else:
            description.append(u'подразделение: ЛПУ')
        createBegDate = params.get('createBegDate', QDate())
        createEndDate = params.get('createEndDate', QDate())
        attachBegDate = params.get('attachBegDate', QDate())
        attachEndDate = params.get('attachEndDate', QDate())
        if createBegDate or createEndDate:
            descr = u'Дата получения данных в периоде : '
            if createBegDate:
                descr = descr + u'с '+ forceString(createBegDate)
            if createEndDate:
                descr = descr + u' по ' + forceString(createEndDate)
            description.append(descr)
        if attachBegDate or attachEndDate:
            descr = u'Дата открепления в периоде : '
            if attachBegDate:
                descr = descr + u'с '+ forceString(attachBegDate)
            if attachEndDate:
                descr = descr + u' по ' + forceString(attachEndDate)
            description.append(descr)

        description.append(u'отчёт составлен: '+forceString(QDateTime.currentDateTime()))
        columns = [('100%', [], CReportBase.AlignLeft)]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()


    def build(self, params):
        orgStructureId = params.get('orgStructureId', None)
        createBegDate = params.get('createBegDate', QDate())
        createEndDate = params.get('createEndDate', QDate())
        attachBegDate = params.get('attachBegDate', QDate())
        attachEndDate = params.get('attachEndDate', QDate())

        query = getQuery(orgStructureId,createBegDate,createEndDate, attachBegDate,attachEndDate)

        # now text
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        underlinedChars = QtGui.QTextCharFormat()
        underlinedChars.setFontUnderline(True)

        columns = [('3%', [], CReportBase.AlignLeft),('2%', [], CReportBase.AlignCenter),('95%', [], CReportBase.AlignLeft)]
        table = createTable(cursor, columns, headerRowCount=6, border=0, cellPadding=2, cellSpacing=0)

        table.mergeCells(0, 0, 1, 3)
        table.setText(0, 0, u'Коды причин открепления:', charFormat=underlinedChars)
        table.setText(1, 0, u'2')
        table.setText(1, 1, u'-')
        table.setText(1, 2, u'cмерть')
        table.setText(2, 0, u'11')
        table.setText(2, 1, u'-')
        table.setText(2, 2, u'cмена МО в связи с возрастом (18 лет)')
        table.setText(3, 0, u'12')
        table.setText(3, 1, u'-')
        table.setText(3, 2, u'поступило уведомление о выборе МО на территории другого субъекта РФ')
        table.setText(4, 0, u'13')
        table.setText(4, 1, u'-')
        table.setText(4, 2, u'прекращено страхование в КК')
        table.setText(5, 0, u'14')
        table.setText(5, 1, u'-')
        table.setText(5, 2, u'дубль в базе прикрепленного населения ТФОМС КК. Требуется проверить актуальное прикрепление.')

        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()

        tableColumns = [
            ('5%',  [u'№ п/п'], CReportBase.AlignLeft),
            ('15%', [u'ФИО пациента'], CReportBase.AlignLeft),
            ('10%', [u'Код пациента'], CReportBase.AlignLeft),
            ('5%',  [u'Пол'], CReportBase.AlignLeft),
            ('5%', [u'Дата рождения'], CReportBase.AlignLeft),
            ('10%', [u'Тип полиса'], CReportBase.AlignLeft),
            ('5%', [u'Серия полиса'], CReportBase.AlignLeft),
            ('10%', [u'Номер полиса'], CReportBase.AlignLeft),
            ('15%', [u'МО'], CReportBase.AlignLeft),
            ('5%', [u'Участок'], CReportBase.AlignLeft),
            ('5%', [u'Дата открепления'], CReportBase.AlignLeft),
            ('5%', [u'Дата получения данных из сервиса'], CReportBase.AlignCenter),
            ('5%', [u'Код причины открепления'], CReportBase.AlignCenter),
        ]

        table = createTable(cursor, tableColumns)

        rowNumber = 0

        while query.next():
            record = query.record()
            row = table.addRow()
            rowNumber += 1

            table.setText(row, 0, rowNumber)
            fullName = ' '.join([forceString(record.value('lastName')),
                                 forceString(record.value('firstName')),
                                 forceString(record.value('patrName'))])
            table.setText(row, 1, fullName)
            if  forceInt(record.value('client_id'))>0:
                table.setHtml(row, 2,u"<a href='karta_" + forceString(record.value('client_id')) + u"'><span style='color: rgb(FF, FF, FF);'>" + forceString(record.value('client_id')) + "</span></a>")
            table.setText(row, 3, forceString(record.value('sex')))
            table.setText(row, 4, '' if record.isNull('birthDate') else forceDate(record.value('birthDate')).toString('dd.MM.yyyy'))
            table.setText(row, 5, forceString(record.value('policyType')))
            table.setText(row, 6, forceString(record.value('policySerial')))
            table.setText(row, 7, forceString(record.value('policyNumber')))
            table.setText(row, 8, forceString(record.value('attach_mo')))
            table.setText(row, 9, forceString(record.value('attach_area')))
            table.setText(row, 10, '' if record.isNull('attach_date') else forceDate(record.value('attach_date')).toString('dd.MM.yyyy'))
            table.setText(row, 11, '' if record.isNull('createDate') else forceDate(record.value('createDate')).toString('dd.MM.yyyy'))
            table.setText(row, 12, '' if record.isNull('deAttachType') else forceString(record.value('deAttachType')))
        return doc