# coding=utf-8
from Exchange.AriadnaModels.AbstractObject import AbstractObject


class Phenotype(AbstractObject):
    def __init__(self, jsondict=None):
        """ Initialize all valid properties."""
        self.id = ''
        self.inputDate = ''
        self.name = ''
        self.nameShort = ''
        self.sortCode = ''
        self.value = ''
        super(Phenotype, self).__init__(jsondict)

    def elementProperties(self):
        """ Returns a list of tuples, one tuple for each property that should
        be serialized, as: ("name", "json_name", type, is_list, "of_many", not_optional)
        """
        js = super(Phenotype, self).elementProperties()
        js.extend([("id", "id", str, False, None, True),
                   ("inputDate", "inputDate", str, False, None, True),
                   ("name", "name", str, False, None, True),
                   ("nameShort", "nameShort", str, False, None, True),
                   ("sortCode", "sortCode", str, False, None, True),
                   ("value", "value", str, False, None, True), ])
        return js
