# coding=utf-8
from Exchange.AriadnaModels.AbstractObject import AbstractObject


class ResistanceMarker(AbstractObject):
    def __init__(self, jsondict=None):
        """ Initialize all valid properties."""
        self.id = ''
        self.markDate = ''
        self.name = ''
        self.sortCode = ''
        super(ResistanceMarker, self).__init__(jsondict)

    def elementProperties(self):
        """ Returns a list of tuples, one tuple for each property that should
        be serialized, as: ("name", "json_name", type, is_list, "of_many", not_optional)
        """
        js = super(ResistanceMarker, self).elementProperties()
        js.extend([("id", "id", str, False, None, True),
                   ("markDate", "markDate", str, False, None, True),
                   ("name", "name", str, False, None, True),
                   ("sortCode", "sortCode", str, False, None, True), ])
        return js
