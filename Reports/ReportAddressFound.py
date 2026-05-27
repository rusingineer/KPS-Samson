# -*- coding: utf-8 -*-

from PyQt4 import QtGui
from PyQt4.QtCore import *

from library.Utils      import *
from library.database   import *
from Reports.Report     import CReport
from Reports.ReportBase import CReportBase, createTable
from Ui_AttachmentList import Ui_AttachmentListDialog

streetMap = {
    u'ал.': u'аллея',
    u'б-р': u'бульвар',
    u'дор': u'дорога',
    u'кв-л': u'квартал',
    u'лн.': u'линия',
    u'наб': u'набережная',
    u'пер.': u'переулок',
    u'пер': u'переулок',
    u'пл': u'площадь',
    u'пр-д': u'проезд',
    u'пр-кт': u'проспект',
    u'ш': u'шоссе',
    }

def getQuery1(orgStructure_id):
    stmt = u"""
        select t.OMS,t.ii,t.uch, t.district, t.village, t.street, t.socr,
            GROUP_CONCAT(distinct case when mod(t.house, 2) = 1 then t.korp end order by t.house SEPARATOR ',') as d1,
            GROUP_CONCAT(distinct case when mod(t.house, 2) = 0 then t.korp end order by t.house SEPARATOR ',') as d2,
            t.FIO, ifnull(t.net, 'все') as net, t.post
            from (SELECT IF(IF(IF(IFNULL(OrgStructure.bookkeeperCode, '') = '', Parent1.bookkeeperCode, OrgStructure.bookkeeperCode)='',Parent2.bookkeeperCode,
  IF(IFNULL(OrgStructure.bookkeeperCode, '') = '', Parent1.bookkeeperCode, OrgStructure.bookkeeperCode))='',Parent3.bookkeeperCode,
  IF(IF(IFNULL(OrgStructure.bookkeeperCode, '') = '', Parent1.bookkeeperCode, OrgStructure.bookkeeperCode)='',Parent2.bookkeeperCode,
  IF(IFNULL(OrgStructure.bookkeeperCode, '') = '', Parent1.bookkeeperCode, OrgStructure.bookkeeperCode)))
 AS OMS,OrgStructure.id AS ii,OrgStructure.infisInternalCode AS uch, k.NAME AS village, dis_k.NAME as district, s.NAME AS street, s.SOCR AS socr,
            CAST(ah.number as signed) as house, CONCAT(CAST(ah.number as signed), CASE when ah.corpus != '' then '/' else '' end, ah.corpus) as korp, CONCAT(p.lastName, ' ', p.firstName, ' ', p.patrName) as FIO, rbNet.name as net,
            p1.name AS post
            FROM OrgStructure            
              left join OrgStructure as Parent1 on Parent1.id = OrgStructure.parent_id
                    left join OrgStructure as Parent2 on Parent2.id = Parent1.parent_id
                    left join OrgStructure as Parent3 on Parent3.id = Parent2.parent_id
                    left join OrgStructure as Parent4 on Parent4.id = Parent3.parent_id
                    left join OrgStructure as Parent5 on Parent5.id = Parent4.parent_id
              LEFT JOIN OrgStructure_Address osa ON OrgStructure.id = osa.master_id
              LEFT JOIN AddressHouse ah ON osa.house_id = ah.id and ah.deleted = 0
              LEFT JOIN kladr.KLADR k ON ah.KLADRCode = k.CODE 
              LEFT JOIN kladr.STREET s ON ah.KLADRStreetCode = s.CODE
              LEFT JOIN kladr.KLADR dis_k ON dis_k.CODE = LEFT(CONCAT(k.parent, '0000000000000'), 13)
              LEFT JOIN Person_Order po on po.orgStructure_id = OrgStructure.id AND po.deleted = 0 and po.type = 6 AND po.documentType_id IS NOT NULL
                  and validFromDate <= now() and ((po.validToDate IS NULL OR LENGTH(po.validToDate) = 0) or po.validToDate >= now())
              LEFT JOIN Person p ON po.master_id = p.id AND p.deleted=0
              LEFT JOIN rbNet ON OrgStructure.net_id = rbNet.id
              LEFT JOIN rbPost p1 ON p.post_id = p1.id
              WHERE OrgStructure.deleted = 0 and k.NAME IS NOT NULL
              AND OrgStructure.areaType > 0
                %(str_org)s
              order by uch, village, street, house) t
              group by t.ii, t.uch, t.village, t.street, t.FIO, t.post, t.socr;
        """
    if orgStructure_id:
        str_org = 'and %(orgStructure_id)d in (OrgStructure.id, Parent1.id, Parent2.id, Parent3.id, Parent4.id, Parent5.id)' % {'orgStructure_id': orgStructure_id}
    else:
        str_org = ''
    smt=stmt % {'str_org': str_org}
    return QtGui.qApp.db.query(smt)

def getQuery():        
        stmt = u"""select sum(case when age(c.birthDate, CURDATE()) > 17 then 1 else 0 end) as cnt_adult,
            sum(case when age(c.birthDate, CURDATE()) < 18 then 1 else 0 end) as cnt_child
            from Client c
            left join ClientAttach ca on ca.id = getClientAttachIdForDate(c.id, 0, CURDATE())
            where c.deleted = 0 and ca.id is not null;"""
        db = QtGui.qApp.db
        return db.query(stmt)


class CAttachmentListDialog(QtGui.QDialog, Ui_AttachmentListDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.cmbOrgStructure.setOrgId(QtGui.qApp.currentOrgId())
        self.cmbOrgStructure.setValue(QtGui.qApp.currentOrgStructureId())

    def setTitle(self, title):
        self.setWindowTitle(title)

    def setParams(self, params):
        self.cmbOrgStructure.setValue(params.get('orgStructureId', None))

    def params(self):
        result = { 'orgStructureId': self.cmbOrgStructure.value() }
        return result


class CAddressFound(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setPayPeriodVisible(False)
        self.setTitle(u'Адресный справочник для ФОНДА')

    def getSetupDialog(self, parent):
        result = CAttachmentListDialog(parent)
        result.setTitle(self.title())
        return result



    def build(self, params):
        orgStructureId = params.get('orgStructureId', None)

        

        query = getQuery()
        query.first()
        record = query.record()
        cnt_adult = forceInt(record.value('cnt_adult'))
        cnt_child = forceInt(record.value('cnt_child'))
        firstTitle = u"""Информация о прикрепленном населении на территории зоны обслуживания  
________________________________________________________ муниципального образования ______________________________
                                                        по состоянию на _______________""" 
        secondTitle = u'\n\n\n\n\n\n\n\nТерритория обслуживания поликлиники в разрезе территориальных участков__________________________________'
        
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(firstTitle)
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        #рисуем первую табличку
        tableColumns = [
            ('25%',  [ u'Всего проживает населения на территории зоны обслуживания медицинской организации', ''], CReportBase.AlignLeft),
            ('25%',  [ u'Взрослые', ''], CReportBase.AlignRight),
            ('25%',  [ u'Дети', ''], CReportBase.AlignRight),
            ('25%',  [ u'Всего', ''], CReportBase.AlignRight)
            ]

        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 0, 2, 1)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        
        #рисуем вторую табличку
        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()
        tableColumns = [
            ('25%',  [ u'Всего населения, прикрепленного к медицинской организации'], CReportBase.AlignLeft),
            ('25%',  [ u'Взрослые'], CReportBase.AlignRight),
            ('25%',  [ u'Дети'], CReportBase.AlignRight),
            ('25%',  [ u'Всего'], CReportBase.AlignRight)
            ]
            
        table = createTable(cursor, tableColumns)
        row = table.addRow()
        table.mergeCells(0, 0, 2, 1)
        table.setText(row, 1, cnt_adult)
        table.setText(row, 2, cnt_child)
        table.setText(row, 3, cnt_adult + cnt_child)     
        
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()
        
        #рисуем третью табличку
        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(secondTitle)
        cursor.insertBlock()
        cursor.insertBlock()
        tableColumns = [
            ('5%' ,  [ u'Код структурного подразделения медицинской организации (поликлиника, амбулатория, ФАП)'], CReportBase.AlignLeft),
            ('5%' ,  [ u'Номер участка'], CReportBase.AlignLeft),
            ('10%',  [ u'Категория пациентов (дети, взрослые, все)'], CReportBase.AlignLeft),
            ('10%',  [ u'Район (район / город)'], CReportBase.AlignLeft),
            ('10%',  [ u'Населенный пункт'], CReportBase.AlignLeft),
            ('15%',  [ u'Наименование улицы'], CReportBase.AlignLeft),
            ('10%',  [ u'Номера домов по четной стороне'], CReportBase.AlignLeft),
            ('10%',  [ u'Номера домов по нечетной стороне'], CReportBase.AlignLeft),
            ('15%',  [ u'Фамилия, имя, отчество медицинского работника на участке'], CReportBase.AlignLeft),
            ('10%',  [ u'Должность'], CReportBase.AlignLeft)
            ]

        table = createTable(cursor, tableColumns)
        query = getQuery1(orgStructureId)
        OMS = None
        
        while query.next():
            record = query.record()
            d1 = forceString(record.value('d1')).replace(u'.',u'').replace(u' ',u'')
            d2 = forceString(record.value('d2')).replace(u'.',u'').replace(u' ',u'')
            uch = forceString(record.value('uch'))
            district = (forceString(record.value('district'))+u' ').replace(u'й',u'и').replace(u'ё', u'е').replace(u' ', u'').lower()
            village = (forceString(record.value('village'))+u' ').replace(u'й',u'и').replace(u'ё', u'е').replace(u' ', u'').lower()
            socr = forceString(record.value('socr'))
            if socr != u'ул':
                if socr in streetMap.keys():
                    socr = streetMap[socr]
                street = (forceString(record.value('street'))+socr+u' ').replace(u'й', u'и').replace(u' ', u'').replace(u'ё', u'е').replace(u'.', u'').lower()
            else:
                street = (forceString(record.value('street'))+u' ').replace(u'й', u'и').replace(u' ', u'').replace(u'ё', u'е').replace(u'.', u'').lower()
            net = forceString(record.value('net'))
            FIO = forceString(record.value('FIO'))
            post = forceString(record.value('post'))
            while d1 or d2 or OMS is None:
                OMS = forceString(record.value('OMS'))
                row = table.addRow()

                table.setText(row, 0, OMS)
                table.setText(row, 1, uch)

                if net == u"взрослая":
                    net = u"взрослые"
                elif net == u"детская":
                    net = u"дети"

                table.setText(row, 2, net)
                table.setText(row, 3, district)
                table.setText(row, 4, village)
                table.setText(row, 5, street)
                table.setText(row, 8, FIO)
                table.setText(row, 9, post)

                odd = u''
                if d2:
                    parts = d2.split(u',')
                    while parts:
                        candidate = parts[0] if not odd else odd + u',' + parts[0]
                        if len(candidate) <= 100:
                            odd = candidate
                            parts.pop(0)
                        else:
                            break
                    d2 = u','.join(parts)
                    table.setText(row, 6, odd)

                even = u''
                space_left = 100 - len(odd)
                if d1 and space_left > 0:
                    parts = d1.split(u',')
                    while parts:
                        candidate = parts[0] if not even else even + u',' + parts[0]
                        if len(candidate) <= space_left:
                            even = candidate
                            parts.pop(0)
                        else:
                            break
                    d1 = u','.join(parts)
                    table.setText(row, 7, even)
            OMS = None
                    
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()
        cursor.insertBlock()
        cursor.insertBlock()
        cursor.insertText("___________________________________________________                        __________________________")
        cursor.insertBlock()
        cursor.insertText(u"Ответственное лицо за прикрепленное население (ФИО)                              (подпись)")
        cursor.insertBlock()
        cursor.insertBlock()
        cursor.insertText(u"Контактный телефон:__________________________")
        return doc
