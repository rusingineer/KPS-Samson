# coding=utf-8
from Exchange.AriadnaModels.AbstractObject import AbstractObject


class OriginalOrderIdentification(AbstractObject):
    def __init__(self, jsondict=None):
        """ Initialize all valid properties.
                """
        self.id = 0  # Long Обязательно Идентификатора заказа в ЛИС
        self.materialId = None  # Long Необязательно Идентификатор исследования (материал)
        self.resultId = None  # Long Необязательно Идентификатор результата
        self.orderid = ''  # String Обязательно Номер заказа в ЛИС
        self.extId = ''  # String Обязательно Идентификатор заказа в МИС. Должен быть уникальным для каждого заказа

        super(OriginalOrderIdentification, self).__init__(jsondict)

    def elementProperties(self):
        """ Returns a list of tuples, one tuple for each property that should
        be serialized, as: ("name", "json_name", type, is_list, "of_many", not_optional)
        """
        js = super(OriginalOrderIdentification, self).elementProperties()
        js.extend([("id", "id", int, False, None, True),
                   ("materialId", "materialId", int, False, None, False),
                   ("resultId", "resultId", int, False, None, False),
                   ("orderid", "orderid", str, False, None, True),
                   ("extId", "extId", str, False, None, True)
                   ])
        return js
