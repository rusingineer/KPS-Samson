# -*- coding: utf-8 -*-

from PyQt4 import QtGui

from library.Utils import forceString, forceDate
from Reports.Report import CReport
from Reports.ReportBase import CReportBase, createTable
from Orgs.Utils import getOrgStructureDescendants

from Ui_AttachmentList import Ui_AttachmentListDialog


def getQuery(orgStructure_id):
    stmt = u"""SELECT    
          Client.lastName,
          Client.firstName,
          Client.patrName,
          case Client.sex when 1 then 'М' when 2 then 'Ж' end as sex,
          Client.birthDate,
          getClientPolicy(Client.id, 1) as policy,
          getClientDocument(Client.id) as UDL,
          if(LENGTH(Client.SNILS) = 11, concat(substr(Client.SNILS, 1, 3), '-', substr(Client.SNILS, 4, 3), '-', substr(Client.SNILS, 7, 3), ' ', substr(Client.SNILS, 9, 2)), NULL) as SNILS,
          coalesce(getClientLocAddress(Client.id), getClientRegAddress(Client.id)) as address,
          Client.id as mis_patientCode,
          IF(length(trim(OrgStructure.bookkeeperCode))=5, OrgStructure.bookkeeperCode,
                    IF(length(trim(Parent1.bookkeeperCode))=5, Parent1.bookkeeperCode,
                      IF(length(trim(Parent2.bookkeeperCode))=5, Parent2.bookkeeperCode,
                        IF(length(trim(Parent3.bookkeeperCode))=5, Parent3.bookkeeperCode,
                          IF(length(trim(Parent4.bookkeeperCode))=5, Parent4.bookkeeperCode, Parent5.bookkeeperCode))))) AS mis_lpu,
          OrgStructure.infisInternalCode as mis_attachArea,
          ClientAttach.begDate as mis_attachDate,
          soc_attachments.attach_mo as tfoms_lpu,
          soc_attachments.attach_area as tfoms_attachArea,
          soc_attachments.attach_date as tfoms_attachDate,
          case when soc_attachments.firstName is null then 'Не найден в регистре'
               when soc_attachments.attach_area != OrgStructure.infisInternalCode
                   then 'Не совпадает номер участка' 
               WHEN soc_attachments.attach_mo != IF(length(trim(OrgStructure.bookkeeperCode))=5, OrgStructure.bookkeeperCode,
                    IF(length(trim(Parent1.bookkeeperCode))=5, Parent1.bookkeeperCode,
                      IF(length(trim(Parent2.bookkeeperCode))=5, Parent2.bookkeeperCode,
                        IF(length(trim(Parent3.bookkeeperCode))=5, Parent3.bookkeeperCode,
                          IF(length(trim(Parent4.bookkeeperCode))=5, Parent4.bookkeeperCode, Parent5.bookkeeperCode))))) THEN 'Не совпадает ЛПУ прикрепления'
  end as error
        from Client
        left join ClientAttach on ClientAttach.id = 
        (select max(ca.id) from ClientAttach ca
            inner join rbAttachType on rbAttachType.id = ca.attachType_id and rbAttachType.code in ('1', '2')
            LEFT JOIN OrgStructure o ON o.id = ca.orgStructure_id
            where ca.client_id = Client.id and ca.endDate is null and ca.deleted = 0 and o.areaType > 0
        )
        LEFT JOIN OrgStructure ON OrgStructure.id = ClientAttach.orgStructure_id
        left join OrgStructure as Parent1 on Parent1.id = OrgStructure.parent_id
        left join OrgStructure as Parent2 on Parent2.id = Parent1.parent_id
        left join OrgStructure as Parent3 on Parent3.id = Parent2.parent_id
        left join OrgStructure as Parent4 on Parent4.id = Parent3.parent_id
        left join OrgStructure as Parent5 on Parent5.id = Parent4.parent_id
        left join soc_attachments on soc_attachments.lastName = Client.lastName
                                 and soc_attachments.firstName = Client.firstName
                                 AND IFNULL(Client.patrName, '') = IFNULL(soc_attachments.patrName, '')
                                 and DATE(soc_attachments.birthDate) = Client.birthDate
                                 and soc_attachments.serviceMethod = 0
        where Client.deathDate is NULL AND Client.deleted = 0 {str_org:s}
        AND ClientAttach.id is not null
 AND (soc_attachments.firstName is null 
  or soc_attachments.attach_area != OrgStructure.infisInternalCode
  or soc_attachments.attach_mo != IF(length(trim(OrgStructure.bookkeeperCode))=5, OrgStructure.bookkeeperCode,
                    IF(length(trim(Parent1.bookkeeperCode))=5, Parent1.bookkeeperCode,
                      IF(length(trim(Parent2.bookkeeperCode))=5, Parent2.bookkeeperCode,
                        IF(length(trim(Parent3.bookkeeperCode))=5, Parent3.bookkeeperCode,
                          IF(length(trim(Parent4.bookkeeperCode))=5, Parent4.bookkeeperCode, Parent5.bookkeeperCode))))))
          
  UNION
           SELECT
          soc_attachments.lastName,
          soc_attachments.firstName,
          soc_attachments.patrName,
          upper(soc_attachments.sex) as sex,
          soc_attachments.birthDate,
          concat_ws(' ', SMO.shortName,
                         concat('серия ', soc_attachments.policySerial),
                         concat('№ ', soc_attachments.policyNumber)) AS policy,
          concat_ws(' ', rbDocumentType.name,
                         soc_attachments.udlSerial,
                         soc_attachments.udlNumber) as UDL, 
          soc_attachments.snils,
          case when soc_attachments.regHouse is not null
               then concat_ws(', ', soc_attachments.regArea,
                                    soc_attachments.regCity,
                                    soc_attachments.regLocal,
                                    soc_attachments.regStreet,
                                    concat('д. ', soc_attachments.regHouse),
                                    concat('корп. ', soc_attachments.regBuilding),
                                    concat('кв. ', soc_attachments.regAppartment))
               else concat_ws(', ', soc_attachments.livArea,
                                    soc_attachments.livCity,
                                    soc_attachments.livLocal,
                                    soc_attachments.livStreet,
                                    concat('д. ', soc_attachments.livHouse),
                                    concat('корп. ', soc_attachments.livBuilding),
                                    concat('кв. ', soc_attachments.livAppartment))
               END as address,
          NULL as mis_patientCode,
          NULL AS mis_lpu,
          NULL as mis_attachArea,
          NULL as mis_attachDate,
          soc_attachments.attach_mo as tfoms_lpu,
          soc_attachments.attach_area as tfoms_attachArea,
          soc_attachments.attach_date as tfoms_attachDate,
           case when Client.id is null then 'Не найден в МИС'
               when Client.deathDate is null and ClientAttach.id is null then 'Не прикреплен в МИС' 
          /* убрана проверка отчества        when IFNULL(Client.patrName, '') <> IFNULL(soc_attachments.patrName, '') then 'Не совпадает отчество'  */
                end as error
        from soc_attachments
        LEFT JOIN OrgStructure OrgStructure ON OrgStructure.infisInternalCode = soc_attachments.attach_area AND OrgStructure.areaType > 0
        left join OrgStructure as Parent1 on Parent1.id = OrgStructure.parent_id
        left join OrgStructure as Parent2 on Parent2.id = Parent1.parent_id
        left join OrgStructure as Parent3 on Parent3.id = Parent2.parent_id
        left join OrgStructure as Parent4 on Parent4.id = Parent3.parent_id
        left join OrgStructure as Parent5 on Parent5.id = Parent4.parent_id
        left join Client on Client.lastName = soc_attachments.lastName
                        and Client.firstName = soc_attachments.firstName
                        AND IFNULL(Client.patrName, '') = IFNULL(soc_attachments.patrName, '')
                        and Client.birthDate = DATE(soc_attachments.birthDate)
                        and Client.deleted = 0
        left JOIN ClientAttach on ClientAttach.id = (SELECT MAX(CAT.id) FROM ClientAttach AS CAT
                                               LEFT JOIN rbAttachType ON rbAttachType.id=CAT.attachType_id
                                               LEFT JOIN OrgStructure o ON o.id = CAT.orgStructure_id 
                                               WHERE CAT.deleted=0
                                               AND CAT.client_id=Client.id
                                               and rbAttachType.code in ('1', '2')
                                               AND (CAT.endDate IS NULL)
                                               and o.areaType > 0
                                              )
        left join Organisation SMO ON SMO.usishCode = soc_attachments.smo AND SMO.isInsurer = 1 and SMO.head_id is null
        left join rbDocumentType ON rbDocumentType.regionalCode = soc_attachments.udlType
        where soc_attachments.serviceMethod = 0
        {str_org:s}
        and soc_attachments.attach_mo = IF(length(trim(OrgStructure.bookkeeperCode))=5, OrgStructure.bookkeeperCode,
                                IF(length(trim(Parent1.bookkeeperCode))=5, Parent1.bookkeeperCode,
                                  IF(length(trim(Parent2.bookkeeperCode))=5, Parent2.bookkeeperCode,
                                    IF(length(trim(Parent3.bookkeeperCode))=5, Parent3.bookkeeperCode,
                                      IF(length(trim(Parent4.bookkeeperCode))=5, Parent4.bookkeeperCode, Parent5.bookkeeperCode)))))
        and (Client.id is NULL or (Client.deathDate is null and ClientAttach.id is null))    
    /* убрана проверка отчества     and (Client.id is NULL or ClientAttach.id is null or (Client.id is not null and IFNULL(Client.patrName, '') <> IFNULL(soc_attachments.patrName, '')))   */ 
        order by lastName, firstName
        """
    if orgStructure_id:
        orgStructList = ','.join(forceString(id) for id in getOrgStructureDescendants(orgStructure_id))
        str_org = 'and OrgStructure.id in ({0:s})'.format(orgStructList)
    else:
        str_org = ''
    return QtGui.qApp.db.query(stmt.format(str_org=str_org))


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
        result = {'orgStructureId': self.cmbOrgStructure.value()}
        return result


class CAttachmentListReport(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setOrientation(QtGui.QPrinter.Landscape)
        self.setPayPeriodVisible(False)
        query=QtGui.qApp.db.query('select max(createDate) dt from soc_attachments where serviceMethod=0')        
        if query.first():
            syncDate = forceDate(query.record().value('dt')).toString('dd.MM.yyyy')    
                        
        self.setTitle(u'Данные о сверке прикрепленного населения на %s' %syncDate)

    def exec_(self):
        query = QtGui.qApp.db.query(u'select count(*) from soc_attachments where serviceMethod=0')
        if query.first() and query.value(0).toInt()[0] > 0:
            CReport.exec_(self)
        else:
            QtGui.QMessageBox.warning(None,
                                      u'Внимание!',
                                      u'Проведите синхронизацию с Регистром приписанного населения',
                                      QtGui.QMessageBox.Ok)

    def getSetupDialog(self, parent):
        result = CAttachmentListDialog(parent)
        result.setTitle(self.title())
        return result

    def build(self, params):
        orgStructureId = params.get('orgStructureId', None)

        query = getQuery(orgStructureId)

        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()
        self.dumpParams(cursor, params)
        cursor.insertBlock()

        tableColumns = [
            ('3%',  [u'№ п/п'], CReportBase.AlignLeft),
            ('15%', [u'ФИО пациента'], CReportBase.AlignLeft),
            ('1%',  [u'Пол'], CReportBase.AlignLeft),
            ('3%', [u'Дата рождения'], CReportBase.AlignLeft),
            ('21%', [u'Полисные данные'], CReportBase.AlignLeft),
            ('5%', [u'УДЛ'], CReportBase.AlignLeft),
            ('5%', [u'СНИЛС'], CReportBase.AlignLeft),
            ('20%', [u'Адрес'], CReportBase.AlignLeft),
            ('3%', [u'Данные МИС', u'Код пациента'], CReportBase.AlignLeft),
            ('3%', ['', u'Код ЛПУ'], CReportBase.AlignLeft),
            ('2%', ['', u'Номер участка'], CReportBase.AlignLeft),
            ('3%', ['', u'Дата прикрепления'], CReportBase.AlignLeft),
            ('3%', [u'Данные регистра', u'Код ЛПУ'], CReportBase.AlignLeft),
            ('2%', ['', u'Номер участка'], CReportBase.AlignLeft),
            ('3%', ['', u'Дата прикрепления'], CReportBase.AlignLeft),
            ('8%', [u'Ошибка сверки'], CReportBase.AlignLeft),
        ]

        table = createTable(cursor, tableColumns)
        table.mergeCells(0, 8, 1, 4)
        table.mergeCells(0, 12, 1, 3)
        for col in [0, 1, 2, 3, 4, 5, 6, 7, 11]:
            table.mergeCells(0, col, 2, 1)

        rowNumber = 0
        while query.next():
            record = query.record()
            row = table.addRow()
            rowNumber += 1

            table.setText(row, 0, rowNumber)
            table.setText(row, 1, ' '.join([forceString(record.value('lastName')),
                                 forceString(record.value('firstName')),
                                 forceString(record.value('patrName'))]))
            table.setText(row, 2, forceString(record.value('sex')))
            if not record.isNull('birthDate'):
                table.setText(row, 3, forceDate(record.value('birthDate')).toString('dd.MM.yyyy'))
            table.setText(row, 4, forceString(record.value('policy')))
            table.setText(row, 5, forceString(record.value('UDL')))
            table.setText(row, 6, forceString(record.value('SNILS')))
            table.setText(row, 7, forceString(record.value('address')))
            if not record.isNull('mis_patientCode'):
                table.setText(row, 8, forceString(record.value('mis_patientCode')))
            table.setText(row, 9, forceString(record.value('mis_lpu')))
            table.setText(row, 10, forceString(record.value('mis_attachArea')))
            if record.isNull('mis_attachDate'):
                table.setText(row, 11, forceDate(record.value('mis_attachDate')).toString('dd.MM.yyyy'))
            table.setText(row, 12, forceString(record.value('tfoms_lpu')))
            table.setText(row, 13, forceString(record.value('tfoms_attachArea')))
            if not record.isNull('tfoms_attachDate'):
                table.setText(row, 14, forceDate(record.value('tfoms_attachDate')).toString('dd.MM.yyyy'))
            table.setText(row, 15, forceString(record.value('error')))
        return doc
