"""
Marine Database APIs package.

This package contains API implementations for various marine taxonomic
and biodiversity databases used in the SHARK4R Python client.
"""

from .algaebase_api import AlgaeBaseApi
from .base_api import BaseMarineAPI
from .dyntaxa_api import DyntaxaApi
from .freshwater_ecology_api import FreshwaterEcologyApi
from .ioc_hab_api import IocHabApi
from .ioc_toxins_api import IocToxinsApi
from .nordic_microalgae_api import NordicMicroalgaeApi
from .obis_api import ObisApi
from .plankton_toolbox_api import PlanktonToolboxApi
from .shark_api import SharkApi
from .worms_api import WormsApi
from .trait_lookup import TraitLookup, get_trait_lookup

# Backwards compatibility aliases (deprecated)
SHARKAPI = SharkApi
DyntaxaAPI = DyntaxaApi
WoRMSAPI = WormsApi
AlgaeBaseAPI = AlgaeBaseApi
IOCHABAPI = IocHabApi
IOCToxinsAPI = IocToxinsApi
OBISAPI = ObisApi
NordicMicroalgaeAPI = NordicMicroalgaeApi
PlanktonToolboxAPI = PlanktonToolboxApi
FreshwaterEcologyAPI = FreshwaterEcologyApi

__all__ = [
    "BaseMarineAPI",
    # New standardized names
    "SharkApi",
    "DyntaxaApi",
    "WormsApi",
    "AlgaeBaseApi",
    "IocHabApi",
    "IocToxinsApi",
    "ObisApi",
    "NordicMicroalgaeApi",
    "PlanktonToolboxApi",
    "FreshwaterEcologyApi",
    # Trait lookup
    "TraitLookup",
    "get_trait_lookup",
    # Deprecated aliases for backwards compatibility
    "SHARKAPI",
    "DyntaxaAPI",
    "WoRMSAPI",
    "AlgaeBaseAPI",
    "IOCHABAPI",
    "IOCToxinsAPI",
    "OBISAPI",
    "NordicMicroalgaeAPI",
    "PlanktonToolboxAPI",
    "FreshwaterEcologyAPI",
]
