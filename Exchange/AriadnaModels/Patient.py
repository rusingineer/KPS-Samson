# coding=utf-8
from Exchange.AriadnaModels.AbstractObject import AbstractObject
from Exchange.AriadnaModels.AdditionalForm import AdditionalForm
from Exchange.AriadnaModels.Born import Born
from Exchange.AriadnaModels.Condition import Condition
from Exchange.AriadnaModels.ContactPoint import ContactPoint
from Exchange.AriadnaModels.ExternalIdentification import ExternalIdentification
from Exchange.AriadnaModels.Identification import Identification
from Exchange.AriadnaModels.Insurance import Insurance
from Exchange.AriadnaModels.Province import Province


class Patient(AbstractObject):
    def __init__(self, jsondict=None):
        self.id = ''  # String Обязательно Идентификатор пациента
        # Array Object Необязательно Массив содержащий в себе данные удостоверяющие личность
        # пациента(объекты SNILS,PASSPORT, INTERNATIONALPASSPORT, BIRTHCERTIFICATE, CERTIFICATE)
        self.identifications = []
        self.snils = ''  # String Необязательно СНИЛС
        self.regCode = ''  # String Обязательно Регистрационный код
        self.givenName = ''  # String Обязательно Имя
        self.familyName = ''  # String Обязательно Фамилия
        self.middleName = ''  # String Обязательно Отчество
        self.address = ''  # String Обязательно Адрес
        self.province = Province()  # Object Обязательно Область
        self.email = ''  # String Обязательно Электронная почта
        self.phoneNumber = ''  # String Необязательно Номер телефона пациента
        # Array Object Необязательно Массив содержащий в себе контактные данные (EMAIL, PHONE, CELLULAR)
        self.telecom = []
        self.additionalForm = None  # Array Objects Необязательно Карта пациента
        self.gender = ''  # String Обязательно Пол Допустимые значения: M-"Male" F-"Female" O-"Other" U-"Unknown"
        self.birthDate = None  # String Обязательно Дата рождения
        self.born = None  # Object Необязательно Контейнер, в котором содержится информация о рождении
        self.workPlace = ''  # String Обязательно Место работы
        self.externalID = ''  # String Обязательно Внешний идентификатор пациента
        self.markID = ''  # String Обязательно Специальная отметка, ID
        self.mark = ''  # String Обязательно Специальная отметка
        self.notes = ''  # String Обязательно Примечание
        self.regDate = None  # String Необязательно Дата регистрации
        self.insurance = Insurance()  # Object Необязательно Страховая информация
        self.externalIdentification = []  # Array Object Обязательно Внешние идентификаторы
        self.conditions = []  # Array Object Обязательно Состояние

        super(Patient, self).__init__(jsondict)

    def elementProperties(self):
        """ Returns a list of tuples, one tuple for each property that should
        be serialized, as: ("name", "json_name", type, is_list, "of_many", not_optional)
        """
        js = super(Patient, self).elementProperties()
        js.extend([("id", "id", str, False, None, True),
                   ("identifications", "identifications", Identification, True, None, False),
                   ("snils", "snils", str, False, None, False),
                   ("regCode", "regCode", str, False, None, True),
                   ("givenName", "givenName", str, False, None, True),
                   ("familyName", "familyName", str, False, None, True),
                   ("middleName", "middleName", str, False, None, True),
                   ("address", "address", str, False, None, True),
                   ("province", "province", Province, False, None, True),
                   ("email", "email", str, False, None, True),
                   ("phoneNumber", "phoneNumber", str, False, None, False),
                   ("telecom", "telecom", ContactPoint, True, None, False),
                   ("additionalForm", "additionalForm", AdditionalForm, True, None, False),
                   ("gender", "gender", str, False, None, True),
                   ("birthDate", "birthDate", str, False, None, False),
                   ("born", "born", Born, False, None, False),
                   ("workPlace", "workPlace", str, False, None, True),
                   ("externalID", "externalID", str, False, None, True),
                   ("markID", "markID", str, False, None, True),
                   ("mark", "mark", str, False, None, True),
                   ("notes", "notes", str, False, None, True),
                   ("regDate", "regDate", str, False, None, False),
                   ("insurance", "insurance", Insurance, False, None, False),
                   ("externalIdentification", "externalIdentification", ExternalIdentification, True, None, True),
                   ("conditions", "conditions", Condition, True, None, True), ])
        return js
