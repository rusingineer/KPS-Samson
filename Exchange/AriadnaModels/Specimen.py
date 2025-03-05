# coding=utf-8
from Exchange.AriadnaModels.AbstractObject import AbstractObject
from Exchange.AriadnaModels.SpecimenRejection import SpecimenRejection
from Exchange.AriadnaModels.SpecimenSite import SpecimenSite
from Exchange.AriadnaModels.SpecimenType import SpecimenType


class Specimen(AbstractObject):
    def __init__(self, jsondict=None):
        """ Initialize all valid properties.
                """
        self.rejections = []  # Array Object Обязательно Причины бракеража материала
        self.specimenSite = None  # Object Необязательно Контейнер, описывающий место взятия материала
        self.specimenType = None  # Object Необязательно Контейнер, описывающий тип материал
        super(Specimen, self).__init__(jsondict)

    def elementProperties(self):
        """ Returns a list of tuples, one tuple for each property that should
        be serialized, as: ("name", "json_name", type, is_list, "of_many", not_optional)
        """
        js = super(Specimen, self).elementProperties()
        js.extend([("rejections", "rejections", SpecimenRejection, True, None, True),
                   ("specimenSite", "specimenSite", SpecimenSite, False, None, False),
                   ("specimenType", "specimenType", SpecimenType, False, None, False)])
        return js
