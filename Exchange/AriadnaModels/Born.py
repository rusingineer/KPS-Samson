# coding=utf-8
from Exchange.AriadnaModels.AbstractObject import AbstractObject
from Exchange.AriadnaModels.BirthDate import BirthDate


class Born(AbstractObject):
    def __init__(self, jsondict=None):
        """ Initialize all valid properties.
                """
        self.birthDate = None  # String Обязательно Контейнер, в котором содержится информация о рождении
        super(Born, self).__init__(jsondict)

    def elementProperties(self):
        """ Returns a list of tuples, one tuple for each property that should
        be serialized, as: ("name", "json_name", type, is_list, "of_many", not_optional)
        """
        js = super(Born, self).elementProperties()
        js.extend([("birthDate", "birthDate", BirthDate, False, None, False)])
        return js
