from argparse import FileType
from datetime import datetime
from doctest import _Out
from enum import Enum
from importlib.metadata import metadata
from ossaudiodev import control_labels
import string
from symbol import file_input
from typing import Dict, Generic, List, Optional, TypeVar, Union

import pydantic
import pydantic.generics
from tiled.server.pydantic_array import ArrayStructure
from tiled.structures.core import StructureFamily

from aimmdb.server.pydantic_dataframe import DataFrameStructure
from aimmdb.utils import get_element_data

structure_association = {
    StructureFamily.array: ArrayStructure,
    StructureFamily.dataframe: DataFrameStructure,
}

MetadataT = TypeVar("MetadataT")


class GenericDocument(pydantic.generics.GenericModel, Generic[MetadataT]):
    uid: Optional[str]
    structure_family: StructureFamily
    structure: Union[ArrayStructure, DataFrameStructure]
    metadata: MetadataT
    specs: List[str]
    mimetype: str
    data_blob: Optional[bytes]
    data_url: Optional[pydantic.AnyUrl]
    last_modified: Optional[datetime]

    @pydantic.root_validator(skip_on_failure=True)
    def validate_structure_matches_structure_family(cls, values):
        # actual_structure_type = cls.__annotations__["structure"]  # this is what was filled in for StructureT
        actual_structure = values.get("structure")
        # Given the structure_family, we know what the structure type should be.
        expected_structure_type = structure_association[values.get("structure_family")]
        if values.get("expected_structure_type") == StructureFamily.node:
            raise Exception(
                f"{expected_structure_type} is not currently supported as a writable structure"
            )
        elif not isinstance(actual_structure, expected_structure_type):
            raise Exception(
                "The expected structure type does not match the received structure type"
            )
        return values

    @pydantic.root_validator(skip_on_failure=True)
    def check_data_source(cls, values):
        # Making them optional and setting default values might help to meet these conditions
        # with the current data types without getting any conflicts
        # if values.get('data_blob') is None and values.get('data_url') is None:
        #     raise ValueError("Not Valid: data_blob and data_url are both None. Use one of them")
        if values.get("data_blob") is not None and values.get("data_url") is not None:
            raise ValueError(
                "Not Valid: data_blob and data_url contain values. Use just one"
            )
        return values

    @pydantic.validator("mimetype")
    def is_mime_type(cls, v):
        m_type, _, _ = v.partition("/")
        mime_type_list = set(
            [
                "application",
                "audio",
                "font",
                "example",
                "image",
                "message",
                "model",
                "multipart",
                "text",
                "video",
            ]
        )

        if m_type not in mime_type_list:
            raise ValueError(f"{m_type} is not a valid mime type")
        return v


class XDIElement(pydantic.BaseModel):
    symbol: str
    edge: str

    @pydantic.validator("symbol")
    def check_symbol(cls, s):
        symbols = get_element_data()["symbols"]
        if s not in symbols:
            raise ValueError(f"{s} not a valid element symbol")
        return s

    @pydantic.validator("edge")
    def check_edge(cls, e):
        edges = get_element_data()["edges"]
        if e not in edges:
            raise ValueError(f"{e} not a valid edge")
        return e


class MeasurementEnum(str, Enum):
    xas = "xas"
    rixs = "rixs"
    feff = "feff"


class FacilityMetadata(pydantic.BaseModel, extra=pydantic.Extra.allow):
    name: str

    @pydantic.validator("name")
    def check_name(cls, name):
        facilities = {"ALS", "APS", "NSLSII", "SSRL"}
        if name not in facilities:
            raise ValueError(f"{name} not a valid facility ({facilities})")


class BeamlineMetadata(pydantic.BaseModel, extra=pydantic.Extra.allow):
    name: str


class SampleData(pydantic.BaseModel, extra=pydantic.Extra.allow):
    uid: Optional[str]
    name: str


class ExperimentalXASMetadata(pydantic.BaseModel, extra=pydantic.Extra.allow):
    element: XDIElement
    measurement_type: MeasurementEnum = pydantic.Field("xas", const=True)
    dataset: str
    sample_id: Optional[str]
    facility: FacilityMetadata
    beamline: BeamlineMetadata

class XMUDocument(DataFrameStructure):
    FileType = xmu.dat

class FEFFatoms(pydantic.BaseModel):
    atoms_values: float

class FEFFcontrol(pydantic.BaseModel):
    control_labels: int

class FEFFexchange(pydantic.BaseModel):
    exchange_values: float

class FEFFtitle(pydantic.BaseModel):
    file_title: Optional[str]

class FEFFrpath(pydantic.BaseModel):
    rpath_value: int

class FEFFpotentials(pydantic.BaseModel):
    x: Optional[str]
    ipot: int
    Z: str
    element: int
    l_scmt: int
    l_fms: int
    FEFFpotentials = (x, ipot, Z, element, l_scmt, l_fms)
    converted_potentials = str(FEFFpotentials)

class FEFFxanes(pydantic.BaseModel):
    xanes: float

class FEFFedge(pydantic.BaseModel):
    edge: str

class FEFFscf(pydantic.BaseModel):
    scf: float

class FEFFfms(pydantic.BaseModel):
    fms: float

class FEFFS02(pydantic.BaseModel):
    S02: float

class FEFFcorehole(pydantic.BaseModel):
    corehole: str    

class FEFFcards(pydantic.BaseModel, extra=pydantic.Extra.allow):
    atoms: FEFFatoms
    control: FEFFcontrol
    exchange: FEFFexchange
    title: FEFFtitle
    rpath: FEFFrpath
    potentials: FEFFpotentials
    xanes: FEFFxanes
    edge: FEFFedge
    scf: FEFFscf
    fms: FEFFfms
    S02: FEFFS02
    corehole: FEFFcorehole

class FEFFDataframe(pydantic.BaseModel):
    file_input = xmu.dat
    omega: float
    e: float
    k: float
    mu: float
    mu0: float
    chi: float
    FEFFDataframe_inputs = (omega, e, k, mu, mu0, chi)

   #need to write validation for the Dataframe

class ExperimentalFEFFMetadata(pydantic.BaseModel, extra=pydantic.Extra.allow):
    FileType = feff.out; feff.inp
    title = feff.inp(pydantic.field("title"))
    absorbing_atom = feff.inp(pydantic.field("edge"))
    cards = feff.inp(FEFFcards)


class ChargeEnum(str, Enum):
    C = "C"
    DC = "DC"


class BatteryChargeMetadataInternal(pydantic.BaseModel):
    cycle: int
    voltage: float
    state: ChargeEnum


class BatteryChargeMetadata(pydantic.BaseModel, extra=pydantic.Extra.allow):
    charge: BatteryChargeMetadataInternal
