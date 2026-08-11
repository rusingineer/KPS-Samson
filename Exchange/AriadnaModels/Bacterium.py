# coding=utf-8
from Exchange.AriadnaModels.AbstractObject import AbstractObject
from Exchange.AriadnaModels.Antibiotic import Antibiotic
from Exchange.AriadnaModels.Phenotype import Phenotype
from Exchange.AriadnaModels.ResistanceMarker import ResistanceMarker


class Bacterium(AbstractObject):
    def __init__(self, jsondict=None):
        """ Initialize all valid properties."""
        self.resCode = ''  # String Обязательно Код измерения
        self.code = ''  # String Обязательно Код бактерии
        self.name = ''  # String Обязательно Название бактерии
        self.resultValue = ''  # String Обязательно Значение измерения
        self.unit = ''  # String Обязательно Единицы измерения
        self.sortCode = 0  # Integer Обязательно Поле для сортировки
        self.notes = ''  # String Обязательно Примечания к бактериям
        self.antibiotics = []  # Array Object Обязательно Антибиотики
        self.phenotypes = []
        self.resistanceMarkers = []
        super(Bacterium, self).__init__(jsondict)

    def elementProperties(self):
        """ Returns a list of tuples, one tuple for each property that should
        be serialized, as: ("name", "json_name", type, is_list, "of_many", not_optional)
        """
        js = super(Bacterium, self).elementProperties()
        js.extend([("resCode", "resCode", str, False, None, True),
                   ("code", "code", str, False, None, True),
                   ("name", "name", str, False, None, True),
                   ("resultValue", "resultValue", str, False, None, True),
                   ("unit", "unit", str, False, None, True),
                   ("sortCode", "sortCode", int, False, None, True),
                   ("notes", "notes", str, False, None, True),
                   ("antibiotics", "antibiotics", Antibiotic, True, None, True),
                   ("phenotypes", "phenotypes", Phenotype, True, None, True),
                   ("resistanceMarkers", "resistanceMarkers", ResistanceMarker, True, None, True), ])
        return js
