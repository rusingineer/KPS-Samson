# -*- coding: utf-8 -*-
from PyQt4 import QtGui
from PyQt4.QtCore import QDate, QDateTime

from library.Utils import forceString, forceInt
from Reports.Report import CReport
from Reports.ReportBase import CReportBase, createTable
from Reports.Utils import dateRangeAsStr


class CactReportMonthlySchoolJournalDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi()

    def setupUi(self):
        self.setWindowTitle(u'Параметры отчета')
        self.resize(400, 150)

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

        ageGroup = QtGui.QGroupBox(u'Возрастная группа', self)
        ageLayout = QtGui.QHBoxLayout(ageGroup)
        self.chkChildren = QtGui.QCheckBox(u'По детям (пр.2499)', self)
        self.chkAdults = QtGui.QCheckBox(u'По взрослым (пр. 867)', self)
        ageLayout.addWidget(self.chkChildren)
        ageLayout.addWidget(self.chkAdults)
        ageLayout.addStretch()
        layout.addWidget(ageGroup)

        buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        layout.addWidget(buttonBox)

    def setParams(self, params):
        self.edtBegDate.setDate(params.get('begDate', QDate.currentDate().addMonths(-1)))
        self.edtEndDate.setDate(params.get('endDate', QDate.currentDate()))
        self.chkChildren.setChecked(params.get('children', False))
        self.chkAdults.setChecked(params.get('adults', False))

    def params(self):
        return {
            'begDate': self.edtBegDate.date(),
            'endDate': self.edtEndDate.date(),
            'children': self.chkChildren.isChecked(),
            'adults': self.chkAdults.isChecked(),
        }


class CactReportMonthlySchoolJournal(CReport):
    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(u'Ежемесячный отчет о работе школ для пациентов с хроническими неинфекционными заболеваниями')
        self.dialog = None
        self.setOrientation(QtGui.QPrinter.Landscape)

    def getSetupDialog(self, parent):
        result = CactReportMonthlySchoolJournalDialog(parent)
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

        if params.get('children', False):
            description.append(u'возрастная группа: дети (пр.2499)')
        if params.get('adults', False):
            description.append(u'возрастная группа: взрослые (пр. 867)')

        description.append(u'отчёт составлен: ' + forceString(QDateTime.currentDateTime()))

        columns = [('100%', [], CReportBase.AlignLeft)]
        table = createTable(cursor, columns, headerRowCount=len(description), border=0, cellPadding=2, cellSpacing=0)
        for i, row in enumerate(description):
            table.setText(i, 0, row)
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertBlock()

    def getSchools(self, children=False, adults=False):
        db = QtGui.qApp.db

        # Формируем условие по flatCode в зависимости от выбранной возрастной группы
        if children and not adults:
            flatCode_condition = "flatCode = 'schools_2499'"
        elif adults and not children:
            flatCode_condition = "flatCode = 'schools_867'"
        else:
            flatCode_condition = "flatCode IN ('schools_867', 'schools_2499')"

        stmt = u"""
            SELECT id, title FROM ActionType 
            WHERE %s AND code NOT IN ('schools_867', 'schools_2499') AND deleted = 0
            ORDER BY title
        """ % flatCode_condition
        query = db.query(stmt)
        schools = []
        while query.next():
            record = query.record()
            schools.append({
                'id': forceInt(record.value('id')),
                'title': forceString(record.value('title'))
            })
        return schools

    def getData(self, params):
        db = QtGui.qApp.db
        begDate = params.get('begDate', QDate())
        endDate = params.get('endDate', QDate())
        children = params.get('children', False)
        adults = params.get('adults', False)

        schools = self.getSchools(children, adults)
        if not schools:
            return {}

        school_ids = [str(s['id']) for s in schools]
        school_ids_str = ','.join(school_ids)

        stmt = u"""
            SELECT 
                A.actionType_id AS school_id,
                COUNT(DISTINCT A.id) AS schools_count,
                COUNT(DISTINCT CASE 
                    WHEN APT.name = 'Пациент закончил обучение по данной программе.' AND APB.value = 1 
                    THEN A.event_id 
                END) AS total_completed,
                COUNT(DISTINCT CASE 
                    WHEN APT.name = 'Пациент закончил обучение по данной программе.' AND APB.value = 1 AND C.sex = 1
                    THEN A.event_id 
                END) AS men_completed,
                COUNT(DISTINCT CASE 
                    WHEN APT.name = 'Пациент закончил обучение по данной программе.' AND APB.value = 1 AND C.sex = 2
                    THEN A.event_id 
                END) AS women_completed,
                COUNT(DISTINCT A.event_id) AS age_total,
                COUNT(DISTINCT CASE 
                    WHEN (C.sex = 1 AND TIMESTAMPDIFF(YEAR, C.birthDate, CURDATE()) BETWEEN 18 AND 63)
                         OR (C.sex = 2 AND TIMESTAMPDIFF(YEAR, C.birthDate, CURDATE()) BETWEEN 18 AND 60)
                    THEN A.event_id 
                END) AS working_age,
                COUNT(DISTINCT CASE 
                    WHEN (C.sex = 1 AND TIMESTAMPDIFF(YEAR, C.birthDate, CURDATE()) > 63)
                         OR (C.sex = 2 AND TIMESTAMPDIFF(YEAR, C.birthDate, CURDATE()) > 60)
                    THEN A.event_id 
                END) AS retirement_age,
                MAX(AT.title) AS school_title
            FROM Action A
            LEFT JOIN Event E ON E.id = A.event_id
            LEFT JOIN Client C ON C.id = E.client_id
            LEFT JOIN ActionProperty AP ON AP.action_id = A.id AND AP.deleted = 0
            LEFT JOIN ActionPropertyType APT ON APT.id = AP.type_id
            LEFT JOIN ActionProperty_Boolean APB ON APB.id = AP.id
            LEFT JOIN ActionType AT ON AT.id = A.actionType_id
            WHERE A.actionType_id IN (%s)
              AND A.deleted = 0
              AND A.begDate >= '%s'
              AND A.begDate <= '%s'            
        """ % (school_ids_str, begDate.toString('yyyy-MM-dd'), endDate.toString('yyyy-MM-dd'))

        if children and not adults:
            stmt += u" AND TIMESTAMPDIFF(YEAR, C.birthDate, CURDATE()) < 18"
        elif adults and not children:
            stmt += u" AND TIMESTAMPDIFF(YEAR, C.birthDate, CURDATE()) >= 18"

        stmt += u" GROUP BY A.actionType_id"

        query = db.query(stmt)

        result = {}
        while query.next():
            record = query.record()
            school_id = forceInt(record.value('school_id'))
            school_title = forceString(record.value('school_title'))

            total_completed = forceInt(record.value('total_completed'))

            first_time = 0
            repeat = 0
            if u'первичный' in school_title.lower():
                first_time = total_completed
            elif u'поддерживающий' in school_title.lower():
                repeat = total_completed
            else:
                first_time = total_completed

            result[school_id] = {
                'schools_count': forceInt(record.value('schools_count')),
                'total_completed': total_completed,
                'men_completed': forceInt(record.value('men_completed')),
                'women_completed': forceInt(record.value('women_completed')),
                'total_completed2': total_completed,
                'first_time': first_time,
                'repeat': repeat,
                'age_total': forceInt(record.value('age_total')),
                'working_age': forceInt(record.value('working_age')),
                'retirement_age': forceInt(record.value('retirement_age')),
            }

        return result

    def build(self, params):
        doc = QtGui.QTextDocument()
        cursor = QtGui.QTextCursor(doc)

        cursor.setCharFormat(CReportBase.ReportTitle)
        cursor.insertText(self.title())
        cursor.insertBlock()

        self.dumpParams(cursor, params)

        cursor.setCharFormat(CReportBase.ReportBody)
        cursor.insertBlock()

        children = params.get('children', False)
        adults = params.get('adults', False)
        schools = self.getSchools(children, adults)
        data = self.getData(params)

        school_count = len(schools)

        if school_count > 0:
            school_width = max(4, min(10, int(70 / school_count)))
            total_school_width = school_width * school_count
            remaining = 100 - total_school_width
            first_col_width = int(remaining * 0.2)
            second_col_width = remaining - first_col_width

            cols = [
                (str(first_col_width) + '%', [u'№ п/п'], CReportBase.AlignCenter),
                (str(second_col_width) + '%', [u'Показатель'], CReportBase.AlignLeft),
            ]

            for school in schools:
                cols.append((str(school_width) + '%', [school['title']], CReportBase.AlignLeft))
        else:
            cols = [
                ('5%', [u'№ п/п'], CReportBase.AlignCenter),
                ('25%', [u'Показатель'], CReportBase.AlignLeft),
                ('70%', [u''], CReportBase.AlignLeft),
            ]

        table = createTable(cursor, cols)

        # Жирный шрифт
        bold_format = QtGui.QTextCharFormat()
        bold_format.setFontWeight(QtGui.QFont.Bold)

        indicator_groups = [
            (u'Количество проведенных Школ для пациентов с ХНИЗ', 'schools_count', 1),
            (u'Общее число обученных пациентов (полностью завершены все занятия)', 'total_completed', 3, [
                (u'   мужчин', 'men_completed'),
                (u'   женщин', 'women_completed'),
            ]),
            (u'Число обученных пациентов (полностью завершены все занятия)', 'total_completed2', 3, [
                (u'   впервые', 'first_time'),
                (u'   повторно', 'repeat'),
            ]),
            (u'Возрастной состав пациентов', 'age_total', 3, [
                (u'   трудоспособного возраста', 'working_age'),
                (u'   старше трудоспособного возраста', 'retirement_age'),
            ]),
        ]

        current_idx = 1
        for item in indicator_groups:
            if len(item) == 3:
                group_name, main_key, row_span = item
                sub_items = None
            else:
                group_name, main_key, row_span, sub_items = item

            start_row = table.addRow()
            table.setText(start_row, 0, forceString(current_idx))
            table.setText(start_row, 1, group_name, charFormat=bold_format)  # жирный

            if schools:
                for col_idx, school in enumerate(schools):
                    school_id = school['id']
                    value = data.get(school_id, {}).get(main_key, 0) if data else 0
                    table.setText(start_row, 2 + col_idx, forceString(value), charFormat=bold_format)  # жирный
            else:
                if current_idx == 1:
                    table.setText(start_row, 2, u'Нет данных о школах')

            current_idx += 1

            if sub_items:
                first_row = start_row
                for sub_name, sub_key in sub_items:
                    row = table.addRow()
                    table.setText(row, 0, u'')
                    table.setText(row, 1, sub_name)

                    if schools:
                        for col_idx, school in enumerate(schools):
                            school_id = school['id']
                            value = data.get(school_id, {}).get(sub_key, 0) if data else 0
                            table.setText(row, 2 + col_idx, forceString(value))
                    else:
                        table.setText(row, 2, u'')

                table.mergeCells(first_row, 0, row_span, 1)

        return doc
