# coding=utf-8
from Exchange.AriadnaModels.AbstractObject import AbstractObject


class AddressFias(AbstractObject):
    def __init__(self, jsondict=None):
        """ Initialize all valid properties.
                """
        self.type = None            # String Необязательно Тип адреса пациента, возможны только два вида registry, actual
        self.country_code = None    # String Необязательно Код страны
        self.country = None         # String Необязательно Страна
        self.region_code = None     # String Необязательно Регион
        self.region = None          # String Необязательно Регион
        self.area_code = None       # String Необязательно Район
        self.area = None            # String Необязательно Район
        self.city_code = None       # String Необязательно Город
        self.city = None            # String Необязательно Город
        self.area_city_code = None  # String Необязательно Населенный пункт
        self.area_city = None       # String Необязательно Населенный пункт
        self.slave_city_code = None # String Необязательно Подчиненный город
        self.slave_city = None      # String Необязательно Подчиненный город
        self.street = None          # String Необязательно Улица
        self.house = None           # String Необязательно Дом
        self.korp = None            # String Необязательно Корпус
        self.flat = None            # String Необязательно Квартира
        self.string = None          # String Необязательно строка с полным адресом
        self.aoGuid = None          # String Необязательно гуид идентификатор адреса пациента
        self.houseGuid = None       # String Необязательно гуид идентификатор адреса пациента


        super(AddressFias, self).__init__(jsondict)

    def elementProperties(self):
        """ Returns a list of tuples, one tuple for each property that should
        be serialized, as: ("name", "json_name", type, is_list, "of_many", not_optional)
        """
        js = super(AddressFias, self).elementProperties()
        js.extend([("type", "type", str, False, None, False),
                   ("country_code", "country_code", str, False, None, False),
                   ("country", "country", str, False, None, False),
                   ("region_code", "region_code", str, False, None, False),
                   ("region", "region", str, False, None, False),
                   ("area_code", "area_code", str, False, None, False),
                   ("area", "area", str, False, None, False),
                   ("city_code", "city_code", str, False, None, False),
                   ("city", "city", str, False, None, False),
                   ("area_city_code", "area_city_code", str, False, None, False),
                   ("area_city", "area_city", str, False, None, False),
                   ("slave_city_code", "slave_city_code", str, False, None, False),
                   ("slave_city", "slave_city", str, False, None, False),
                   ("street", "street", str, False, None, False),
                   ("house", "house", str, False, None, False),
                   ("korp", "korp", str, False, None, False),
                   ("flat", "flat", str, False, None, False),
                   ("string", "string", str, False, None, False),
                   ("aoGuid", "aoGuid", str, False, None, False),
                   ("houseGuid", "houseGuid", str, False, None, False),
                   ])
        return js
