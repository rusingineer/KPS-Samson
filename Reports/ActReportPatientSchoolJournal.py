# -*- coding: utf-8 -*-
from PyQt4 import QtGui
from PyQt4.QtCore import QDate, QDateTime

from library.Utils import forceString, forceInt, forceDate
from Reports.Report import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.Utils import dateRangeAsStr


class CactReportPatientSchoolJournalDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi()
        self.loadSchools()

    def setupUi(self):
        self.setWindowTitle(u'Параметры отчета')
        self.resize(500, 200)

        layout = QtGui.QVBoxLayout(self)

        periodGroup = QtGui.QGroupBox(u'Период', self)
        periodLayout = QtGui.QHBoxLayout(periodGroup)

        self.edtBegDate = QtGui.QDateEdit(self)
        self.edtBegDate.setCalendarPopup(True)
        self.edtBegDate.setDate(QDate.currentDate().addMonths(-1))

        self.edtEndDate = QtGui.QDateEdit(self)
        self.edtEndDate.setCalendarPopup(True)
        self.edtEndDate.setDate(QDate.currentDate())

        periodLayout.addWidget(QtGui.QLabel(u'с:'))
        periodLayout.addWidget(self.edtBegDate)
        periodLayout.addWidget(QtGui.QLabel(u'по:'))
        periodLayout.addWidget(self.edtEndDate)
        periodLayout.addStretch()
        layout.addWidget(periodGroup)

        schoolGroup = QtGui.QGroupBox(u'Школа для пациентов', self)
        schoolLayout = QtGui.QVBoxLayout(schoolGroup)

        self.cmbSchool = QtGui.QComboBox(self)
        self.cmbSchool.addItem(u'Все школы', 0)
        schoolLayout.addWidget(self.cmbSchool)
        layout.addWidget(schoolGroup)

        buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        layout.addWidget(buttonBox)

    def loadSchools(self):
        db = QtGui.qApp.db
        stmt = u"""
            SELECT id, title FROM ActionType 
            WHERE flatCode = 'schools_867' AND code != 'schools_867' AND deleted = 0
            ORDER BY title
        """
        query = db.query(stmt)
        while query.next():
            record = query.record()
            schoolId = forceInt(record.value('id'))
            schoolTitle = forceString(record.value('title'))
            self.cmbSchool.addItem(schoolTitle, schoolId)

    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate().addMonths(-1)))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        schoolId = params.get('schoolId', 0)
        index = self.cmbSchool.findData(schoolId)
        if index >= 0:
            self.cmbSchool.setCurrentIndex(index)

    def params(self):
        return {
            'begDate': self.edtBegDate.date(),
            'endDate': self.edtEndDate.date(),
            'schoolId': self.cmbSchool.itemData(self.cmbSchool.currentIndex())
        }


class CactReportPatientSchoolJournal(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Журнал регистрации пациентов, обучающихся в Школах для пациентов с хроническими неинфекционными заболеваниями')
        self.dialog = None
        self.setOrientation(QtGui.QPrinter.Landscape)

    def getSetupDialog(self, parent):
        result = CactReportPatientSchoolJournalDialog(parent)
        self.dialog = result
        return result

    def dumpParams(self, cursor, params):
        description = []
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        if begDate and endDate:
            result = dateRangeAsStr(u'за период', begDate, endDate)
            if result:
                description.append(result)
            else:
                description.append(u'%s - %s' % (begDate.toString('dd.MM.yyyy'), endDate.toString('dd.MM.yyyy')))

        schoolId = forceInt(params.get('schoolId', 0))
        if schoolId:
            db = QtGui.qApp.db
            schoolName = forceString(db.translate('ActionType', 'id', schoolId, 'title'))
            description.append(u'школа: %s' % schoolName)
        else:
            description.append(u'школа: все')

        description.append(u'отчёт составлен: ' + forceString(QDateTime.currentDateTime()))

        columns = [('100%', [], CReportBase.AlignLeft)]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()

    def getTopics(self, schoolId):
        if not schoolId:
            return []
        db = QtGui.qApp.db
        stmt = u"""
            SELECT id, valueDomain FROM ActionPropertyType 
            WHERE actiontype_id = %d AND shortName = 'school_867' AND deleted = 0
            ORDER BY id
        """ % forceInt(schoolId)
        query = db.query(stmt)
        topics = []
        while query.next():
            record = query.record()
            topics.append(forceString(record.value('valueDomain')))
        return topics

    def getData(self, params):
        db = QtGui.qApp.db
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        schoolId = params.get('schoolId', 0)
        schoolId = forceInt(schoolId)

        stmt = u"""
            SELECT 
                Event.id AS event_id,
                Client.id AS client_id,
                CONCAT(Client.lastName, ' ', Client.firstName, ' ', Client.patrName) AS fio,
                Client.birthDate AS birth_date,
                (SELECT getClientLocAddress(Client.id)) AS address,
                (SELECT getClientContacts(Client.id)) AS contacts,
                (SELECT D.MKB
                 FROM Diagnostic DG
                 INNER JOIN Diagnosis D ON D.id = DG.diagnosis_id
                 WHERE DG.event_id = Event.id 
                   AND DG.diagnosisType_id = 1
                   AND DG.deleted = 0
                 LIMIT 1) AS diagnosis,
                (SELECT D.MKB 
                 FROM Diagnostic DG
                 INNER JOIN Diagnosis D ON D.id = DG.diagnosis_id
                 WHERE DG.event_id = Event.id 
                 AND DG.diagnosisType_id = 5
                 AND DG.deleted = 0) AS concomitant,
                A.id AS action_id
            FROM Event
            INNER JOIN Client ON Client.id = Event.client_id
            INNER JOIN Action A ON A.event_id = Event.id
            INNER JOIN ActionType AT ON AT.id = A.actionType_id
            WHERE AT.flatCode = 'schools_867'
              AND Event.deleted = 0
              AND Client.deleted = 0
              AND A.deleted = 0
              AND AT.deleted = 0
        """

        if begDate:
            stmt += u" AND A.begDate >= '%s'" % begDate.toString('yyyy-MM-dd')
        if endDate:
            stmt += u" AND A.begDate <= '%s'" % endDate.toString('yyyy-MM-dd')

        if schoolId:
            stmt += u" AND AT.id = %d" % schoolId

        stmt += u" ORDER BY Client.lastName, Client.firstName"

        query = db.query(stmt)

        result = []
        current_patient = None
        current_visits = {}

        while query.next():
            record = query.record()
            client_id = forceInt(record.value('client_id'))
            print("Processing client_id:", client_id, "current_patient:", current_patient)
            fio = forceString(record.value('fio'))
            birth_date = forceDate(record.value('birth_date'))
            address = forceString(record.value('address'))
            contacts = forceString(record.value('contacts'))
            diagnosis = forceString(record.value('diagnosis'))
            concomitant = forceString(record.value('concomitant'))
            action_id = forceInt(record.value('action_id'))

            lessons = []

            date_stmt = u"""
                SELECT 
                    apd.value AS lesson_date
                FROM ActionProperty_Date apd
                INNER JOIN ActionProperty ap ON ap.id = apd.id
                INNER JOIN ActionPropertyType apt ON apt.id = ap.type_id
                WHERE ap.action_id = %d 
                  AND apt.name LIKE 'Дата занятия %%'
                  AND ap.deleted = 0
                ORDER BY apt.id
            """ % action_id
            date_query = db.query(date_stmt)

            topic_stmt = u"""
                SELECT 
                    aps.value AS lesson_topic
                FROM ActionProperty_String aps
                INNER JOIN ActionProperty ap ON aps.id = ap.id
                INNER JOIN ActionPropertyType apt ON apt.id = ap.type_id
                WHERE ap.action_id = %d 
                  AND apt.name LIKE 'Название занятия %%'
                  AND ap.deleted = 0
                ORDER BY apt.id
            """ % action_id
            topic_query = db.query(topic_stmt)

            dates = []
            while date_query.next():
                date_record = date_query.record()
                dates.append(forceDate(date_record.value('lesson_date')))

            topics_list = []
            while topic_query.next():
                topic_record = topic_query.record()
                topics_list.append(forceString(topic_record.value('lesson_topic')))

            for i in range(min(len(dates), len(topics_list))):
                lesson_date = dates[i]
                lesson_topic = topics_list[i]

                if lesson_date and lesson_topic:
                    if begDate and lesson_date < begDate:
                        continue
                    if endDate and lesson_date > endDate:
                        continue
                    lessons.append((lesson_date, lesson_topic))

            if current_patient != client_id:
                if current_patient is not None:
                    visits_list = []
                    for i in range(5):
                        visits_list.append(current_visits.get(i, u''))
                    result.append({
                        'num': len(result) + 1,
                        'fio': current_fio,
                        'birthDate': current_birth_date,
                        'address': current_address,
                        'contacts': current_contacts,
                        'diagnosis': current_diagnosis,
                        'concomitant': current_concomitant,
                        'visits': visits_list
                    })

                current_patient = client_id
                current_fio = fio
                current_birth_date = birth_date
                current_address = address
                current_contacts = contacts
                current_diagnosis = diagnosis
                current_concomitant = concomitant
                current_visits = {}

            for visit_idx, (lesson_date, lesson_topic) in enumerate(lessons[:5]):
                if lesson_topic:
                    visit_text = u'%s: %s' % (lesson_date.toString('dd.MM.yyyy'), lesson_topic)
                    current_visits[visit_idx] = visit_text

        if current_patient is not None:
            visits_list = []
            for i in range(5):
                visits_list.append(current_visits.get(i, u''))
            result.append({
                'num': len(result) + 1,
                'fio': current_fio,
                'birthDate': current_birth_date,
                'address': current_address,
                'contacts': current_contacts,
                'diagnosis': current_diagnosis,
                'concomitant': current_concomitant,
                'visits': visits_list
            })

        return result

    def build(self, params):
        doc = QtGui.QTextDocument()

        # Увеличиваем шрифт всего документа
        font = QtGui.QFont()
        font.setPointSize(9)
        doc.setDefaultFont(font)

        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()

        self.dumpParams(cursor, params)

        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()

        schoolId = params.get('schoolId', 0)
        schoolId = forceInt(schoolId)
        topics = self.getTopics(schoolId)
        topicCount = len(topics) if len(topics) <= 5 else 5

        cols = [
            ('3%', [u'№ п/п', u''], CReportBase.AlignCenter),
            ('10%', [u'ФИО', u''], CReportBase.AlignLeft),
            ('5%', [u'Дата рождения', u''], CReportBase.AlignCenter),
            ('12%', [u'Адрес', u''], CReportBase.AlignLeft),
            ('7%', [u'Телефон', u''], CReportBase.AlignLeft),
            ('8%', [u'Диагноз', u''], CReportBase.AlignLeft),
            ('8%', [u'Осложнения', u''], CReportBase.AlignLeft),
            ('8%', [u'Сопутствующие заболевания', u''], CReportBase.AlignLeft),
        ]

        for i in range(5):
            if i < topicCount:
                cols.append(('8%', [topics[i], u''], CReportBase.AlignLeft))
            else:
                cols.append(('8%', [u'', u''], CReportBase.AlignLeft))

        table = createTable(cursor, cols, headerRowCount=2)
        for col in range(len(cols)):
            table.setText(1, col, u'')

        table.mergeCells(0, 8, 1, 5)
        format = QtGui.QTextCharFormat()
        format.setFontWeight(QtGui.QFont.Bold)
        table.setText(0, 8, u'Дата проведения, тема занятия', charFormat=format, blockFormat=CReportBase.AlignCenter)

        for i in range(5):
            table.setText(1, 8 + i, forceString(i + 1), charFormat=format, blockFormat=CReportBase.AlignCenter)

        data = self.getData(params)

        if not data:
            row = table.addRow()
            table.setText(row, 1, u'Нет данных за выбранный период')
            return doc

        for record in data:
            row = table.addRow()
            table.setText(row, 0, forceString(record.get('num', '')))
            table.setText(row, 1, forceString(record.get('fio', '')))

            birthDate = record.get('birthDate')
            if birthDate:
                table.setText(row, 2, birthDate.toString('dd.MM.yyyy'))

            table.setText(row, 3, forceString(record.get('address', '')))
            table.setText(row, 4, forceString(record.get('contacts', '')))
            table.setText(row, 5, forceString(record.get('diagnosis', '')))
            table.setText(row, 6, u'')
            table.setText(row, 7, forceString(record.get('concomitant', '')))

            visits = record.get('visits', [])
            for visit_idx, visit_text in enumerate(visits[:5]):
                if visit_text:
                    table.setText(row, 8 + visit_idx, visit_text)

        return doc