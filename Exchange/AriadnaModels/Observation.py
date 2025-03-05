# coding=utf-8
from Exchange.AriadnaModels.AbstractObject import AbstractObject
from Exchange.AriadnaModels.AdditionalForm import AdditionalForm
from Exchange.AriadnaModels.Binary import Binary
from Exchange.AriadnaModels.CollectInfo import CollectInfo
from Exchange.AriadnaModels.GiveResult import GiveResult
from Exchange.AriadnaModels.ObservationDates import ObservationDates
from Exchange.AriadnaModels.Order import Order
from Exchange.AriadnaModels.OrderInfo import OrderInfo
from Exchange.AriadnaModels.OrderingInstitution import OrderingInstitution
from Exchange.AriadnaModels.OrderingReceiver import OrderingReceiver
from Exchange.AriadnaModels.OriginalOrderIdentification import OriginalOrderIdentification
from Exchange.AriadnaModels.Patient import Patient
from Exchange.AriadnaModels.Purpose import Purpose
from Exchange.AriadnaModels.ReportGroup import ReportGroup
from Exchange.AriadnaModels.ResourcePhysician import ResourcePhysician
from Exchange.AriadnaModels.ResourceReagent import ResourceReagent
from Exchange.AriadnaModels.Semd import Semd
from Exchange.AriadnaModels.Specimen import Specimen
from Exchange.AriadnaModels.SpecimenSite import SpecimenSite
from Exchange.AriadnaModels.SpecimenType import SpecimenType


class Observation(AbstractObject):
    def __init__(self, jsondict=None):
        """ Initialize all valid properties.
                """
        self.lcnUuid = None  # String Необязательно Генерируемый apiOrders идентификатор документа, который будет
        self.originalOrderIdentification = OriginalOrderIdentification()  # Object Обязательно Идентификатор документа
        self.ids = None  # Long Необязательно Идентификатор материала
        self.regDate = ''  # String Обязательно Дата регистрации
        self.visitID = None  # String Необязательно Идентификатор визита
        self.status = ''  # String Обязательно Статус материала
        self.domain = None  # String хз что
        self.observationDates = ObservationDates()  # Object Обязательно Даты выдачи и завершения
        self.order = Order()  # Object Обязательно Заказ
        self.specimenTypes = SpecimenType()  # Object Обязательно Тип материала
        self.additionalForm = None  # Object Необязательно Карта пациента
        self.specimenSites = SpecimenSite()  # Object Обязательно Материал по справочнику
        self.specimen = Specimen()  # Object Обязательно Контейнер, описывающий материал
        self.cito = False  # Boolean Необязательно Срочность заказа
        self.purposes = Purpose()  # Object Обязательно Цель исследования
        self.diagnosis = ''  # String Обязательно Диагноз
        self.collectInfo = CollectInfo()  # Object Обязательно Информация о взятии материала
        self.narrative = ''  # String Обязательно Заключение
        self.giveResult = GiveResult()  # Object Обязательно Выдача результата
        self.customerType = None  # Integer Необязательно Тип заказчика
        self.patient = Patient()  # Object Обязательно Информация о пациенте
        self.representative = None  # Object Необязательно Информация о представителе пациента
        self.orderingInstitution = OrderingInstitution()  # Object Необязательно Информация о заказчике
        self.orderingReceiver = None  # Object Необязательно Получатель заказа
        self.orderInfo = []  # Objects Обязательно Информация о заказе
        self.reports = []  # Objects Обязательно Отчеты
        self.binary = None  # Object Необязательно ЭЦП врача, организации, пдф
        self.semd = None  # Object Необязательно ЭЦП врача, организации, сэмд
        self.icmid = ''  # String Обязательно Идентификатор клиента
        self.physicians = []  # Array Object Необязательно Массив врачей
        self.reagents = []  # Array Object Необязательно Массив реагентов


        super(Observation, self).__init__(jsondict)

    def elementProperties(self):
        """ Returns a list of tuples, one tuple for each property that should
        be serialized, as: ("name", "json_name", type, is_list, "of_many", not_optional)
        """
        js = super(Observation, self).elementProperties()
        js.extend([("lcnUuid", "lcnUuid", str, False, None, False),
            ("originalOrderIdentification", "originalOrderIdentification", OriginalOrderIdentification, False, None, True),
            ("ids", "ids", unicode, False, None, False),
            ("regDate", "regDate", str, False, None, True),
            ("visitID", "visitID", int, False, None, False),
            ("status", "status", str, False, None, True),
            ("domain", "domain", str, False, None, False),
            ("observationDates", "observationDates", ObservationDates, False, None, True),
            ("order", "order", Order, False, None, True),
            ("specimenTypes", "specimenTypes", SpecimenType, False, None, True),
            ("additionalForm", "additionalForm", AdditionalForm, True, None, False),
            ("specimenSites", "specimenSites", SpecimenSite, False, None, True),
            ("specimen", "specimen", Specimen, False, None, True),
            ("cito", "cito", bool, False, None, False),
            ("purposes", "purposes", Purpose, False, None, True),
            ("diagnosis", "diagnosis", str, False, None, True),
            ("collectInfo", "collectInfo", CollectInfo, False, None, True),
            ("narrative", "narrative", str, False, None, True),
            ("giveResult", "giveResult", GiveResult, False, None, True),
            ("customerType", "customerType", int, False, None, False),
            ("patient", "patient", Patient, False, None, True),
            ("representative", "representative", Patient, False, None, False),
            ("orderingInstitution", "orderingInstitution", OrderingInstitution, False, None, False),
            ("orderingReceiver", "orderingReceiver", OrderingReceiver, False, None, False),
            ("orderInfo", "orderInfo", OrderInfo, True, None, True),
            ("reports", "reports", ReportGroup, True, None, True),
            ("binary", "binary", Binary, False, None, False),
            ("semd", "semd", Semd, False, None, False),
            ("icmid", "icmid", str, False, None, True),
            ("physicians", "physicians", ResourcePhysician, True, None, False),
            ("reagents", "reagents", ResourceReagent, True, None, False)
            ])
        return js
