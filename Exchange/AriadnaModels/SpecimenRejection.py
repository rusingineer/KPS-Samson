# coding=utf-8
from Exchange.AriadnaModels.AbstractObject import AbstractObject


class SpecimenRejection(AbstractObject):
    def __init__(self, jsondict=None):
        """ Initialize all valid properties.
                """
        self.rejectionType = ''  # String Обязательно Причины бракеража материала(Noop, Rejected или ResultRejected)
        self.msg = ''  # String Необязательно Контейнер, описывающий место взятия материала
        super(SpecimenRejection, self).__init__(jsondict)

    def elementProperties(self):
        """ Returns a list of tuples, one tuple for each property that should
        be serialized, as: ("name", "json_name", type, is_list, "of_many", not_optional)
        """
        js = super(SpecimenRejection, self).elementProperties()
        js.extend([("rejectionType", "rejectionType", str, False, None, True),
                   ("msg", "msg", str, False, None, False)])
        return js
