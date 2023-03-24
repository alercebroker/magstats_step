import dataclasses
from typing import Union, List


@dataclasses.dataclass
class AlerceObject:
    aid: str
    oid: List[str] = dataclasses.field(default_factory=list)
    tid: List[str] = dataclasses.field(default_factory=list)
    meanra: Union[float, None] = None
    sigmara: Union[float, None] = None
    meandec: Union[float, None] = None
    sigmadec: Union[float, None] = None
    firstmjd: Union[float, None] = None
    lastmjd: Union[float, None] = None
    ndet: Union[int, None] = None
    corrected: bool = False
    stellar: bool = False
    magstats: List[dict] = dataclasses.field(default_factory=list)

    def as_dict(self):
        return dataclasses.asdict(self)


def alerce_object_factory(raw_object_info: dict) -> AlerceObject:
    if "aid" not in raw_object_info:
        raise ValueError("AID not provided")

    return AlerceObject(raw_object_info["aid"])