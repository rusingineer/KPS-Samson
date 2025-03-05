# coding=utf-8
from Exchange.AriadnaModels.AbstractObject import AbstractObject


class CollectInfo(AbstractObject):
    def __init__(self, jsondict=None):
        """ Initialize all valid properties.
                """
        self.collectDate = None  # String Необязательно Дата взятия материала
        self.collectorID = ''  # String Обязательно Взявший материал, табельный номер
        self.collector = ''  # String Обязательно Взявший материал
        self.deliveryDate = None  # String Необязательно Дата доставки
        super(CollectInfo, self).__init__(jsondict)

    def elementProperties(self):
        """ Returns a list of tuples, one tuple for each property that should
        be serialized, as: ("name", "json_name", type, is_list, "of_many", not_optional)
        """
        js = super(CollectInfo, self).elementProperties()
        js.extend([("collectDate", "collectDate", str, False, None, False),
                   ("collectorID", "collectorID", str, False, None, True),
                   ("collector", "collector", str, False, None, True),
                   ("deliveryDate", "deliveryDate", str, False, None, False)])
        return js
