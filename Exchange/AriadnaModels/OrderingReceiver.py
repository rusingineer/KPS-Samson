# coding=utf-8
from Exchange.AriadnaModels.AbstractObject import AbstractObject


class OrderingReceiver(AbstractObject):
    def __init__(self, jsondict=None):
        """ Initialize all valid properties."""
        self.icmid = ''  # String Обязательно Идентификатор получателя заказа
        super(OrderingReceiver, self).__init__(jsondict)

    def elementProperties(self):
        """ Returns a list of tuples, one tuple for each property that should
        be serialized, as: ("name", "json_name", type, is_list, "of_many", not_optional)
        """
        js = super(OrderingReceiver, self).elementProperties()
        js.extend([("icmid", "icmid", str, False, None, True)])
        return js
