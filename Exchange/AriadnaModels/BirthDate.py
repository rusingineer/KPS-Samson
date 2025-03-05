# coding=utf-8
from Exchange.AriadnaModels.AbstractObject import AbstractObject


class BirthDate(AbstractObject):
    def __init__(self, jsondict=None):
        """ Initialize all valid properties.
                """
        self.bDate = ''  # String Обязательно Дата рождения в строковом представлении
        self.bTime = ''  # String Обязательно Время рождения в строковом представлении
        super(BirthDate, self).__init__(jsondict)

    def elementProperties(self):
        """ Returns a list of tuples, one tuple for each property that should
        be serialized, as: ("name", "json_name", type, is_list, "of_many", not_optional)
        """
        js = super(BirthDate, self).elementProperties()
        js.extend([("bDate", "bDate", str, False, None, True),
                   ("bTime", "bTime", str, False, None, True), ])
        return js
