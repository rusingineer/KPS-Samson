# -*- coding: utf-8 -*-
################################################################
import json
from datetime import datetime
from PyQt4 import QtGui
from library.Utils import forceString, forceInt
from Reports.Report import CReport

head = {
    'id': u'ID',
    'period': u'Период',
    'ENP': u'ЕНП',
    'smo_code': u'Код СМО',
    'smo_short_name': u'СМО (кратко)',
    'okato_territory': u'Территория СМО (ОКАТО)',
    'gender': u'Пол',
    'age': u'Возраст',
    'mo_code': u'Код МО',
    'mo_id': u'МО (OID)',
    'mo_short_name': u'МО (кратко)',
    'mo_territory': u'Территория МО',
    'branch_mo_id': u'Филиал МО',
    'structural_unit_code': u'Код структурного подразделения',
    'structural_unit_type': u'Вид структурного подразделения',
    'attachment_area_id': u'Участок прикрепления',
    'attachment_type': u'Тип прикрепления',
    'attachment_profile': u'Профиль прикрепления',
    'attachment_method': u'Способ прикрепления',
    'attachment_start_date': u'Дата начала прикрепления',
    'attachment_end_date': u'Дата окончания прикрепления',
    'doctor_id': u'Идентификатор врача',
    'doctor_attachment_start_date': u'Дата прикрепления к врачу',
    'attachment_status': u'Статус прикрепления'
}


class CReportFerlzAttachments(CReport):
    name = u'Данные прикреплений из Ферзл'

    # Словари для расшифровки значений
    areaType = {
        1: u'терапевтический',
        2: u'акушерско-гинекологический',
        3: u'стоматологический',
        4: u'СМП',
        5: u'ФАП'
    }
    attachMethod = {
        1: u'по территориальному признаку',
        2: u'по личному заявлению',
        3: u'по электронному заявлению',
        4: u'по распоряжению органов здравоохранения',
    }
    nameAttached = {
        "smo": {'name': u'Прикреплённые к данной МО и застрахованные в определенной СМО', 'value': u"Код СМО",
                'type': u''},
        "smo_okato": {'name': u'Прикреплённые к данной МО и застрахованные на своей территории', 'value': u"Код ОКАТО",
                      'type': u''},
        "smo_okato!": {'name': u'Прикреплённые к данной МО и застрахованные на чужой территории', 'value': u"Код ОКАТО",
                       'type': u''},
        "mo_f_id": {'name': u'Прикрепленные к определенному филиалу', 'value': u"oid", 'type': u''},
        "mo_dep_id": {'name': u'Прикрепленные к определенному структурному подразделению', 'value': u"oid",
                      'type': u''},
        "area_type": {'name': u'Прикрепленные к данной МО с определённым профилем', 'value': u"Профиль прикрепления",
                      'type': u'areaType'},
        "attach_method": {'name': u'Прикрепленные к данной МО определённым способом', 'value': u"Способ прикрепления",
                          'type': u'attachMethod'},
    }

    def __init__(self, parent):
        CReport.__init__(self, parent)
        self.setTitle(self.name)

    def _get_latest_period(self):
        db = QtGui.qApp.db
        sql = u"SELECT MAX(period) FROM ferzl_attachments_result"
        query = db.query(sql)
        if query.next():
            return forceString(query.record().value(0))
        return None

    def _subtract_month(self, date_str):
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            year = dt.year
            month = dt.month - 1
            if month == 0:
                month = 12
                year -= 1
            return datetime(year, month, 1).strftime('%Y-%m-%d')
        except Exception:
            return date_str

    def _get_json_header_info(self):
        db = QtGui.qApp.db
        sql = u"""
            SELECT f.CreateDateTime, f.value
            FROM ferzl_attachments f
            WHERE f.status = 'COMPLETED'
            ORDER BY f.CreateDateTime DESC
            LIMIT 1
        """
        query = db.query(sql)
        if not query.next():
            return None
        json_str = forceString(query.record().value('value'))
        try:
            data = json.loads(json_str)
        except ValueError:
            return None
        dt_str = self._subtract_month(data.get('dt', ''))
        criteries = data.get('criteries', [])
        conditions = []
        for idx, crit in enumerate(criteries, start=1):
            field = crit.get('fieldNameAttached', '')
            val = crit.get('value', '')
            meta = self.nameAttached.get(field)
            if meta is None:
                display_name = field
                display_value = val
            else:
                display_name = meta['name']
                type_ = meta['type']
                if type_ == 'areaType':
                    display_value = self.areaType.get(int(val), val)
                elif type_ == 'attachMethod':
                    display_value = self.attachMethod.get(int(val), val)
                else:
                    display_value = val
            conditions.append(u"{}. {}: {}".format(idx, display_name, display_value))
        return {'dt': dt_str, 'conditions': conditions}

    def build(self, params):
        db = QtGui.qApp.db
        period = self._get_latest_period()
        if not period:
            return u'<p style="color:red; font-size: 14pt;">Нет данных для отображения, воспользуйтесь утилитой, раздел "Импорт прикрепленного населения ФЕРЗЛ"</p>'

        count_sql = u"SELECT COUNT(*) FROM ferzl_attachments_result"
        count_query = db.query(count_sql)
        total = 0
        if count_query.next():
            total = forceInt(count_query.record().value(0))
        if total == 0:
            return u'<p style="font-size: 14pt;">Нет данных</p>'

        header_info = self._get_json_header_info()
        header_html = u""
        if header_info:
            header_html = u'<p style="font-size: 12pt;">Запрос сформирован на {dt}.</p>'.format(dt=header_info['dt'])
            header_html += u'<p style="font-size: 12pt; font-weight: bold;">Условия запроса:</p><ul style="font-size: 11pt;">'
            for cond in header_info['conditions']:
                header_html += u'<li>{}</li>'.format(cond)
            header_html += u'</ul>'
        else:
            header_html = u'<p style="font-size: 12pt; color:gray;">Данные о параметрах запроса не найдены.</p>'

        # Получаем список полей (исключаем master_id, CreateDateTime и period)
        field_query = db.query(
            u"SELECT * FROM ferzl_attachments_result WHERE period = '{period}' LIMIT 1".format(period=period))
        if not field_query.next():
            return u'<p style="color:red;">Ошибка получения структуры таблицы</p>'
        rec_first = field_query.record()
        field_names = []
        field_index_map = {}
        for i in range(rec_first.count()):
            fname = rec_first.fieldName(i)
            # ИСКЛЮЧАЕМ period (а также master_id и CreateDateTime)
            if fname not in ('master_id', 'CreateDateTime', 'period'):
                field_names.append(fname)
                field_index_map[fname] = i

        # Сборка HTML
        html_parts = []
        html_parts.append(u"""<!DOCTYPE html>
<head>{setPageSize('A4')} {setOrientation('L')} {setLeftMargin(5)} {setTopMargin(5)} {setBottomMargin(5)} {setRightMargin(5)}</head>
<body>
<p style="font-size: 14pt; font-weight: bold; text-align: center;">Данные прикреплений из Ферзл</p>
""")
        html_parts.append(header_html)
        html_parts.append(
            u'<p style="font-size: 10pt; text-align: center;">Всего записей: {total}</p>'.format(total=total))
        html_parts.append(
            u'<br/><table border="1" cellspacing="0" cellpadding="3" style="font-size: 8pt; width: 100%;"><tr>')

        # Заголовки – теперь русские
        for fname in field_names:
            header = head[str(fname)]
            html_parts.append(
                u'<th style="font-weight: bold; text-align: center;">{header}</th>'.replace(u'{header}', header))
        html_parts.append(u'</tr>')

        # Данные (первые 100)
        limit = 100
        data_query = db.query(
            u"SELECT * FROM ferzl_attachments_result WHERE period = '{period}' ORDER BY id LIMIT {limit}".format(
                period=period, limit=limit))
        data_query.setForwardOnly(True)
        while data_query.next():
            rec = data_query.record()
            html_parts.append(u'<tr>')
            for fname in field_names:
                idx = field_index_map.get(fname)
                value = forceString(rec.value(idx)) if idx is not None else u''
                html_parts.append(
                    u'<td style="text-align: center; white-space: nowrap;">{value}</td>'.replace(u'{value}', value))
            html_parts.append(u'</tr>')

        html_parts.append(u'</table></body></html>')
        return u''.join(html_parts)

    def getSetupDialog(self, parent):
        class SilentDialog(QtGui.QDialog):
            def __init__(self, parent=None):
                QtGui.QDialog.__init__(self, parent)
                self.setVisible(False)

            def setParams(self, params):
                pass

            def params(self):
                return {}

            def exec_(self):
                return QtGui.QDialog.Accepted

        return SilentDialog(parent)