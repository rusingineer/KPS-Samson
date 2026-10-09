# coding=utf-8
from Exchange.AriadnaModels.AbstractObject import AbstractObject
from Exchange.AriadnaModels.Bacterium import Bacterium
from Exchange.AriadnaModels.Equipment import Equipment
from Exchange.AriadnaModels.Measurement import Measurement
from Exchange.AriadnaModels.Norm import Norm
from Exchange.AriadnaModels.Operator import Operator
from Exchange.AriadnaModels.Protocol import Protocol
from Exchange.AriadnaModels.ResearchTable import ResearchTable
from Exchange.AriadnaModels.ResourceRef import ResourceRef
from Exchange.AriadnaModels.Verifier import Verifier
from Exchange.AriadnaModels.XpsMessage import XpsMessage


class Result(AbstractObject):
    def __init__(self, jsondict=None):
        """ Initialize all valid properties."""
        self.seqNo = 0  # Integer Обязательно Номер строки в отчете
        self.resTable = ResearchTable()  # Object Обязательно Вид исследования
        self.equipment = None  # Object Необязательно Серийный и инвентарный номер лабораторного оборудования, на котором было произведено измерение
        self.measurement = Measurement()  # Object Обязательно Измерение
        self.pathology = ''  # String Обязательно Отметка патологии
        self.headerMark = ''  # String Обязательно Метка заголовка
        self.resultText = ''  # String Обязательно Полный текст значения измерения
        self.resultValue = ''  # String Обязательно Значение измерения
        self.codesetID = ''  # String Обязательно Используемый кодовый набор, ID
        self.unit = ''  # String Обязательно Единицы измерения
        self.norm = Norm()  # Object Обязательно Нормы
        self.repLevel = None  # Integer Необязательно Уровень вложенности в отчете
        self.finishDate = None  # String Необязательно Дата завершения измерения
        self.resCount = None  # Integer Необязательно Количество полученных результатов
        self.resCode = ''  # String Обязательно Код измерения
        self.requested = None  # Boolean Необязательно Результат был заказан
        self.reportFormat = ''  # String Обязательно Имя формата отчета
        self.srvdepCode = None  # String Необязательно Код услуги
        self.verifier = Verifier()  # Object Обязательно Ответственное лицо
        self.verifierRef = None  # Object Необязательно Объект в котором содержится ссылка на врача из массива врачей, который заверил результат
        self.operatorRef = None  # Object Необязательно Объект в котором содержиться сслыка на врача из массива врачей, который провел исследование
        self.reagentRef = None  # Object Необязательно Объект в котором содержиться сслыка на реагент из массива реагентов для данного исследования
        self.operator = Operator()  # Object Обязательно Работник, заносящий результаты
        self.description = ''  # String Обязательно Примечания к норме
        self.notes = ''  # String Обязательно Примечания к результатам
        self.bacteria = []  # Array Object Обязательно Бактерии
        self.protocol = None  # Array Object Необязательно Протокол
        self.mbioType = None  # String Необязательно Тип микроорганизма
        self.unitCode = None  # String Необязательно Код единицы измерения
        self.xpsMessages = [] # Array Object Необязательно Сообщения экспертной системы
        super(Result, self).__init__(jsondict)

    def elementProperties(self):
        """ Returns a list of tuples, one tuple for each property that should
        be serialized, as: ("name", "json_name", type, is_list, "of_many", not_optional)
        """
        js = super(Result, self).elementProperties()
        js.extend(
            [("seqNo", "seqNo", int, False, None, True),
             ("resTable", "resTable", ResearchTable, False, None, True),
             ("equipment", "equipment", Equipment, False, None, False),
             ("measurement", "measurement", Measurement, False, None, True),
             ("pathology", "pathology", str, False, None, True),
             ("headerMark", "headerMark", str, False, None, True),
             ("resultText", "resultText", str, False, None, True),
             ("resultValue", "resultValue", str, False, None, True),
             ("codesetID", "codesetID", str, False, None, True),
             ("unit", "unit", str, False, None, True),
             ("norm", "norm", Norm, False, None, True),
             ("repLevel", "repLevel", int, False, None, False),
             ("finishDate", "finishDate", str, False, None, False),
             ("resCount", "resCount", int, False, None, False),
             ("resCode", "resCode", str, False, None, True),
             ("requested", "requested", bool, False, None, False),
             ("reportFormat", "reportFormat", str, False, None, True),
             ("srvdepCode", "srvdepCode", str, False, None, False),
             ("verifier", "verifier", Verifier, False, None, True),
             ("verifierRef", "verifierRef", ResourceRef, False, None, False),
             ("operatorRef", "operatorRef", ResourceRef, False, None, False),
             ("reagentRef", "reagentRef", ResourceRef, False, None, False),
             ("operator", "operator", Operator, False, None, True),
             ("description", "description", str, False, None, True),
             ("notes", "notes", str, False, None, True),
             ("bacteria", "bacteria", Bacterium, True, None, True),
             ("protocol", "protocol", Protocol, True, None, False),
             ("mbioType", "mbioType", str, False, None, False),
             ("unitCode", "unitCode", str, False, None, False),
             ("xpsMessages", "xpsMessages", XpsMessage, True, None, False), ])
        return js
