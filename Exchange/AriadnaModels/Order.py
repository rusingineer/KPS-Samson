# coding=utf-8
from Exchange.AriadnaModels.AbstractObject import AbstractObject


class Order(AbstractObject):
    def __init__(self, jsondict=None):
        """ Initialize all valid properties.
                """
        self.id = ''  # String Обязательно Номер направления
        self.date = ''  # String Обязательно Дата заказа
        self.hisId = ''  # String Обязательно Идентификатор заказа в МИС. Должен быть уникальным для каждого заказа
        self.medHistory = ''  # String Необязательно Номер истории болезни
        self.commentSpecimen = None  # String Необязательно Комментарий к материалу
        super(Order, self).__init__(jsondict)

    def elementProperties(self):
        """ Returns a list of tuples, one tuple for each property that should
        be serialized, as: ("name", "json_name", type, is_list, "of_many", not_optional)
        """
        js = super(Order, self).elementProperties()
        js.extend([("id", "id", str, False, None, True),
                   ("date", "date", str, False, None, True),
                   ("hisId", "hisId", str, False, None, True),
                   ("medHistory", "medHistory", str, False, None, False),
                   ("commentSpecimen", "commentSpecimen", str, False, None, False)])
        return js
