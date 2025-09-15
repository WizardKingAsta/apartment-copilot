# schemas.py
from dataclasses import dataclass
from typing import Optional, TypedDict, Tuple, List

PARSE_VERSION = "apt.v1"  # move here if shown in UI/DB

@dataclass
class FloorPlan:
    plan_name: str
    beds: Optional[float] = None
    baths: Optional[float] = None
    sqft_min: Optional[int] = None
    sqft_max: Optional[int] = None
    price_min: Optional[int] = None
    price_max: Optional[int] = None
    deposit_min: Optional[int] = None
    deposit_max: Optional[int] = None
    available_units_count: Optional[int] = None
    is_renovated: bool = False
    source_url: Optional[str] = None
    scraped_at: str = ""  # fill at parse time  # ← might change if you prefer auto= today()

@dataclass
class Unit:
    unit_id: Optional[str]
    plan_name_ref: Optional[str]
    price: Optional[int] = None
    sqft: Optional[int] = None
    availability_raw: Optional[str] = None
    availability_date: Optional[str] = None
    source_url: Optional[str] = None
    scraped_at: str = ""  # fill at parse time  # ← might change for auto fill

class ParseReport(TypedDict, total=False):
    plans_found: int
    units_found: int
    noise_items: int
    date_parse_failures: int
    header_only_plans: int
    notes: List[str]

ParserResult = Tuple[List[FloorPlan], List[Unit], ParseReport]