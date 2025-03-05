# coding=utf-8
from Exchange.AriadnaModels.AbstractObject import AbstractObject


class AdditionalForm(AbstractObject):
    def __init__(self, jsondict=None):
        """ Initialize all valid properties.
                """
        self.code = ''  # String Обязательно Идентификатор (код), определяющий дополнительное поле
        self.type = ''  # String Обязательно Тип, определяющий формат передаваемых в данном поле данных
        self.valueId = ''  # String Необязательно Идентификатор (код или id) записи из выпадающего списка
        self.value = ''  # String Обязательно Значение передаваемого поля
        super(AdditionalForm, self).__init__(jsondict)

    def elementProperties(self):
        """ Returns a list of tuples, one tuple for each property that should
        be serialized, as: ("name", "json_name", type, is_list, "of_many", not_optional)
        """
        js = super(AdditionalForm, self).elementProperties()
        js.extend([("code", "code", str, False, None, True),
                   ("type", "type", str, False, None, True),
                   ("valueId", "valueId", str, False, None, False),
                   ("value", "value", str, False, None, True), ])
        return js
