from .component import FunctionalComponent
from .identified import Identified
from .measurement import Measurement
from .object import *
from .participation import Participation
from .validation import *


class Interaction(Identified):
    def __init__(self, rdf_type=SBOL_INTERACTION,
                 uri='example', interaction_type=SBO_INTERACTION):
        super().__init__(rdf_type, uri)
        self.functionalComponents = OwnedObject(self,
                                                SBOL_FUNCTIONAL_COMPONENTS,
                                                FunctionalComponent,
                                                '0', '*', [libsbol_rule_18])
        self._types = URIProperty(self, SBOL_TYPES,
                                  '1', '*', [], interaction_type)
        self.participations = OwnedObject(self, SBOL_PARTICIPATIONS,
                                          Participation,
                                          '0', '*', [])
        self.measurements = OwnedObject(self, SBOL_MEASUREMENTS,
                                        Measurement,
                                        '0', '*', [])
        # TODO hidden properties

    @property
    def types(self):
        return self._types.value

    @types.setter
    def types(self, new_types):
        self._types.set(new_types)
