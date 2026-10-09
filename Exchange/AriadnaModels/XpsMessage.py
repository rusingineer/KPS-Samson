# coding=utf-8
from Exchange.AriadnaModels.AbstractObject import AbstractObject


class XpsMessage(AbstractObject):
    def __init__(self, jsondict=None):
        """ Initialize all valid properties."""
        self.antibioticList = ''
        self.bacteriaCode = ''
        self.message = ''
        self.sortCode = ''
        self.title = ''
        super(XpsMessage, self).__init__(jsondict)

    def elementProperties(self):
        """ Returns a list of tuples, one tuple for each property that should
        be serialized, as: ("name", "json_name", type, is_list, "of_many", not_optional)
        """
        js = super(XpsMessage, self).elementProperties()
        js.extend(
            [("antibioticList", "antibioticList", str, False, None, True),
             ("bacteriaCode", "bacteriaCode", str, False, None, True),
             ("message", "message", str, False, None, True),
             ("sortCode", "sortCode", str, False, None, True),
             ("title", "title", str, False, None, True), ])
        return js
