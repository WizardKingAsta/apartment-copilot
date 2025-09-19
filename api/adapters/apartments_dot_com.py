"""
apartments.py — Apartments.com parser (Diffbot 'items' → FloorPlan/Unit)

- Handles three shapes you shared (E1/E2/E3):
  * Plan headers & prose-like unit rows (E1)
  * Plan headers + 'Unit' rows with aux keys (E2)
  * Table scaffold: columns emitted as separate items (E3)

Input:
    items: List[dict]  # Diffbot 'items' array for a listing page
    source_url: Optional[str]  # listing URL

Output (ParserResult):
    (plans: List[FloorPlan], units: List[Unit], report: ParseReport)
"""

from typing import Any, Dict, List, Optional, Tuple
from datetime import date, datetime
import re

    # If apartments.py sits next to schemas.py
from adapters.schema import FloorPlan, Unit, ParseReport, ParserResult, PARSE_VERSION  # type: ignore

__all__ = ["parse_apartments_items"]

# ---------------- Domain constants & regex ----------------

NORMALIZE_MAP = {
    "–": "-",
    "\u00a0": " ",
    "square feet": "sq ft",
    "Square Feet": "sq ft",
    "Sq Ft": "sq ft",
    "SQ FT": "sq ft",
    "availibility": "availability",
}

IGNORE_PHRASES = [
    "View More",
    "Apply Now",
    "Tour Floor Plan",
    "View Floor Plan Details",
    "View",
    "Unit Details",
]

GENERIC_TITLES = {
    "Unit",
    "Base Price",
    "Sq Ft",
    "Availability",
    "Unit Details",
    "Pricing & Floor Plans",
    "filter results by bedrooms",
    "Cost Calculator:",
}

RE_MULTI_SPACE = re.compile(r"\s+")

# ⚠️ These patterns drive most extraction; you’ll likely tweak them as you see more pages.
RE_PRICE_RANGE = re.compile(r"\$?\s*(\d[\d,]+)\s*(?:-\s*\$?\s*([\d,]+))?")  # ⚠️ may overmatch prices in text
RE_SQFT_RANGE = re.compile(r"(?<!\$)\s*([\d,]{3,5})\s*(?:-\s*([\d,]{3,4}))?\s*sq\s*ft", re.I)  # ⚠️ adjust if 5-digit sqft appears
RE_BEDS = re.compile(r"(Studio)|(\d+(?:\.\d+)?)\s*Bed", re.I)
RE_BATHS = re.compile(r"(\d+(?:\.\d+)?)\s*Bath", re.I)
RE_DEPOSIT = re.compile(r"\$([\d,]+)\s*Deposit", re.I)
RE_AVAIL_COUNT = re.compile(r"\b(\d+)\s+Available units?\b", re.I)
# \b or (?:^|\\b)
RE_UNIT_ID = re.compile(r"(?:^|\b)Unit\s+([A-Za-z0-9\-]+)\b", re.I)
RE_AVAIL = re.compile(r"\bavailability\s+([A-Za-z]{3,9}\s+\d{1,2}(?:,\s*\d{4})?|Now|Waitlist)\b", re.I)  # ⚠️ 'availability' token may be missing on some pages

# ---------------- Normalization helpers ----------------

def normalize_text(s: Optional[str]) -> str:
    if not s:
        return ""
    for k, v in NORMALIZE_MAP.items():
        s = s.replace(k, v)
    for phrase in IGNORE_PHRASES:
        s = s.replace(phrase, " ")
    s = RE_MULTI_SPACE.sub(" ", s)
    return s.strip()

def make_blob(item: Dict[str, Any]) -> str:
    # Concatenate likely fields in priority order (covers E1/E2/E3)
    parts: List[str] = []
    for key in [
        "mortar-wrapper",
        "summary",
        "unitColumn",
        "pricingColumn",
        "sqftColumn",
        "availableColumnInnerContainer",
        "availableColumn",
        "title", "btn" #added for 2000 post case to classify as unit if it is "send message"
    ]:
     
        val = item.get(key)
        if isinstance(val, str) and val.strip():
            parts.append(val)
    return normalize_text(" ".join(parts))

# ---------------- Classification ----------------

def is_plan_header(item: Dict[str, Any], blob: str) -> bool:
    #print("plan Header:"+blob)
    title = (item.get("title") or "").strip()
    if title and title not in GENERIC_TITLES:
        if RE_AVAIL_COUNT.search(title):
            return True
        if any(p.search(blob) for p in (RE_PRICE_RANGE, RE_SQFT_RANGE, RE_BEDS, RE_BATHS)):
            return True
    if any(p.search(blob) for p in (RE_BEDS, RE_BATHS)) and any(p.search(blob) for p in (RE_PRICE_RANGE, RE_SQFT_RANGE)):
        return True
    return False

def is_unit_row(item: Dict[str, Any], blob: str) -> bool:
    title = (item.get("title") or "").strip()
    if title == "Unit" or item.get("unitColumn"):
        return True
    if RE_UNIT_ID.search(blob):
       # print("unit:" + blob)
        return True
    has_price = "price" in blob or "$" in blob
    has_sqft = "sq ft" in blob
    if has_price and has_sqft and "availability" in blob:
        return True
    if "Send Message" in blob or "send message" in blob: #added to broaden definition of a unit, send message usually means its a unit not floor plan
        return True
    return False

def classify_item(item: Dict[str, Any], blob: str) -> str:
    # ⚠️ Order matters; unit detection first prevents mislabeling row fragments as plans.
    #print("classify:"+blob)
    if is_unit_row(item, blob):
        return "unit_row"
    if is_plan_header(item, blob):
        return "plan_header"
    return "noise"

# ---------------- Field extraction ----------------

def _to_int(s: Optional[str]) -> Optional[int]:
    if not s:
        return None
    #Remove comma and dollar sign if money vals ar epassed in
    s = s.replace(",", "")
    s = s.replace("$","")

    #remove trailing sq ft if the square feet val was paaed in
    s = s.replace("sq ft","")

    #remove deposit if the value passed in was deposit
    s = s.replace("Deposit","")

    return int(s)

def _beds_from_blob(blob: str) -> Optional[float]:
    m = RE_BEDS.search(blob)
    if not m:
        return None
    if m.group(1):  # Studio
        return 0.0
    return float(m.group(2))

def _baths_from_blob(blob: str) -> Optional[float]:
    m = RE_BATHS.search(blob)
    return float(m.group(1)) if m else None

def _range_from_regex(pattern: re.Pattern, blob: str) -> Tuple[Optional[int], Optional[int]]:
    m = pattern.search(blob)

    if not m:
        return (None, None)
    #split match object into usable array on -
   
    arr = m.group(0).split("-")
    
    lo = _to_int(arr[0])#_to_int(m.group(1))
    hi = lo
    if len(arr)>1:
        hi = _to_int(arr[1])
    return (lo, hi)

def _plan_name_from(title: str, blob: str) -> str:
    
    if title and title not in GENERIC_TITLES and not RE_AVAIL_COUNT.search(title):
        return title.strip()
    m = re.search(r"^(.*?)(?:\s*\$|\s*\d+\s*Bed|\s*Studio\b)", blob, re.I)
    candidate = (m.group(1) if m else blob).strip(" -:|")
    #Studio case fpr maa
    if not candidate and m and m.group(0):
        candidate = m.group(0)
    return candidate[:80] if candidate else "Unnamed Plan"

def _parse_date_maybe(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    s = s.strip()
    # RFC-like header from E2
    for fmt in ("%a, %d %b %Y %H:%M:%S %Z", "%a, %d %b %Y %H:%M:%S GMT"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except Exception:
            pass
    # “Sep 12”
    try:
        dt = datetime.strptime(s, "%b %d")
        assumed = date(date.today().year, dt.month, dt.day)
        return assumed.isoformat()
    except Exception:
        return None

def extract_plan(item: Dict[str, Any], blob: str, source_url: Optional[str]) -> FloorPlan:
    #print("In extract" + blob)
    title = (item.get("title") or "").strip()
    plan_name = _plan_name_from(title, blob)
    price_min, price_max = _range_from_regex(RE_PRICE_RANGE, blob)
    sqft_min, sqft_max = _range_from_regex(RE_SQFT_RANGE, blob)
    beds = _beds_from_blob(blob)
    baths = _baths_from_blob(blob)
    dep_min, dep_max = _range_from_regex(RE_DEPOSIT, blob)
    avail_count = None
    m = RE_AVAIL_COUNT.search(title) or RE_AVAIL_COUNT.search(blob)
    if m:
        avail_count = int(m.group(1))
    is_renovated = "renovated" in plan_name.lower() or "renovated" in blob.lower()
    return FloorPlan(
        plan_name=plan_name,
        beds=beds,
        baths=baths,
        sqft_min=sqft_min,
        sqft_max=sqft_max,
        price_min=price_min,
        price_max=price_max,
        deposit_min=dep_min,
        deposit_max=dep_max,
        available_units_count=avail_count,
        is_renovated=is_renovated,
        source_url=source_url,
        scraped_at=date.today().isoformat(),
    )
#function to parse dict item to see if there are multiple units, and split them to individual units
def split_unit(blob: str)-> str:
    #find all matches with unit x price, this appears once per unit so we can use it to split da 
    matches = re.finditer(r"Unit\s*[\w\-]+\s*price\s*", blob, re.I)
    markers = []
    #loop through iterator obj and save all starting indexes for unit matches
    for match in matches:
        markers.append(match.start())

    #if there are no markers then this is a one off, meaning only one unit in the list so return it
    if not markers:
        return [blob]
    units = []
    #loop through all starting markers
    for i in range(len(markers)):
        #if first unit capture begnining to it for floor plan
        if i == 0 and markers[i]!=0:
            units.append(blob[0:markers[i]])
        #if there is an unit after this one add substring of this unit start to that unit start to the list of units
        elif i+1< len(markers):
            units.append(blob[markers[i]:markers[i+1]])
        else: #if last unit take substring from start of unit to end of blob
            units.append(blob[markers[i]::])
    return units

def extract_unit(item: Dict[str, Any], blob: str, current_plan: Optional[str], source_url: Optional[str]) -> Unit:
    avail_hint = (item.get("availableColumnInnerContainer") or item.get("availableColumn") or "").strip()
    date_hdr = (item.get("date") or "").strip()

    unit_id = None
    mid = RE_UNIT_ID.search(blob)

    name_holder =""
     #if no name found extract begning of blob until dollar sign
    loc = re.search(r"\s*\$([\d,]+)",blob)
    if loc:
        name_holder = blob[0:loc.start()]
    #print("NAME:"+name_holder)
   
    if mid:
        unit_id = mid.group(1)
    else:
        unit_id = name_holder
        

    # Prefer explicit "price $X", else first $N
    price = None
    mp = re.search(r"price\s*\$([\d,]+)", blob, re.I) or re.search(r"\$([\d,]+)", blob)
    if mp:
        price = _to_int(mp.group(1))

    # try for patterns where "sq ft" comes before numbers
    ms = re.search(r"\s*sq\s*ft\s*([\d,]{3,5})", blob, re.I) or re.search(r"square feet\s*(\d{3,4})", blob, re.I)

    #if that returns none then check for second pattern
    if not ms:
        #check for pattern where "sq ft" comes after numbers, and do not look after $ to skip prices
        ms = re.search(r"(?<!\$)([\d,]{3,5})\s*sq\s*ft", blob, re.I) or re.search(r"square feet\s*(\d{3,4})", blob, re.I)
    sqft = _to_int(ms.group(1)) if ms else None

    # availability
    ma = RE_AVAIL.search(blob)
    availability_raw = None
    availability_date = None
    if ma:
        availability_raw = ma.group(1)
    elif avail_hint:
        availability_raw = avail_hint
    elif date_hdr:
        availability_raw = date_hdr
    if availability_raw:
        availability_date = _parse_date_maybe(availability_raw)
        if availability_raw.lower() == "now":
            availability_date = date.today().isoformat()

   

    return Unit(
        unit_id=unit_id,
        plan_name_ref=current_plan,
        price=price,
        sqft=sqft,
        availability_raw=availability_raw,
        availability_date=availability_date,
        source_url=source_url,
        scraped_at=date.today().isoformat(),
    )

# ---------------- Reconciliation ----------------

def widen_plan_ranges_with_unit(plan: FloorPlan, unit: Unit) -> None:
    if unit.price is not None:
        if plan.price_min is None or unit.price < plan.price_min:
            plan.price_min = unit.price
        if plan.price_max is None or unit.price > plan.price_max:
            plan.price_max = unit.price
    if unit.sqft is not None:
        if plan.sqft_min is None or unit.sqft < plan.sqft_min:
            plan.sqft_min = unit.sqft
        if plan.sqft_max is None or unit.sqft > plan.sqft_max:
            plan.sqft_max = unit.sqft

# ---------------- Entrypoint ----------------
#Expects the items in list to be dicts of string key and any value ex: {"summary":"unit 120"}
def parse_apartments_items(items: List[Dict[str, Any]], source_url: Optional[str] = None) -> ParserResult:
    plans: List[FloorPlan] = []
    units: List[Unit] = []
    report: ParseReport = {
        "plans_found": 0,
        "units_found": 0,
        "noise_items": 0,
        "date_parse_failures": 0,
        "header_only_plans": 0,
        "notes": [f"parser={PARSE_VERSION}"],
    }

     #SDet used to dedupe before sending out units
    dedupe_units = set()

    current_plan_name: Optional[str] = None
    last_plan_obj: Optional[FloorPlan] = None
    #Loops over all items in json, key point
    for item in items:
        #Call to make a blob on the info in the item
        #print("\n ITEM:")
        #print(item)

        blob = make_blob(item)
        if not blob:
            report["noise_items"] += 1
            continue

        kind = classify_item(item, blob)
        if kind == "plan_header":
            plan = extract_plan(item, blob, source_url)
            plans.append(plan)
            report["plans_found"] += 1
            current_plan_name = plan.plan_name
            last_plan_obj = plan

        elif kind == "unit_row":
            split_units = split_unit(blob)
            #if the length of units is more than 1 assume the first item is floor plan info
            if  is_plan_header(item,split_units[0]) and len(split_units)>1 and "Send Message" not in split_units[0]:
                #extract plan from the first item
                plan = extract_plan(item, split_units[0], source_url)
                plans.append(plan)
                report["plans_found"] += 1
                current_plan_name = plan.plan_name
                last_plan_obj = plan
                #remove first item so that we dont have a floor plan unit entry
                split_units = split_units[1::]

            for split_unit_blob in split_units:
                unit = extract_unit(item, split_unit_blob, current_plan_name, source_url)
                if unit.unit_id not in dedupe_units:
                    units.append(unit)
                    dedupe_units.add(unit.unit_id)
                report["units_found"] += 1
            current_plan_name = None
            #if last_plan_obj:
                #widen_plan_ranges_with_unit(last_plan_obj, unit)
            if not last_plan_obj:#else:
                # ⚠️ Fallback: unit before any plan header — synthesize a plan once for this block.
                if current_plan_name is None:
                    current_plan_name = "Unnamed Plan (inferred)"  # ⚠️ may cause duplicates across pages if not deduped later
                    synth = FloorPlan(plan_name=current_plan_name, source_url=source_url, scraped_at=date.today().isoformat())
                    plans.append(synth)
                    report["plans_found"] += 1
                    last_plan_obj = synth
                #if last_plan_obj:
                    #widen_plan_ranges_with_unit(last_plan_obj, unit)

        else:
            report["noise_items"] += 1
            title = (item.get("title") or "").strip()
            if title in GENERIC_TITLES:
                report["notes"].append(f"table_scaffold:{title}")

    # Post-pass: header-only plans metric
    plan_names_with_units = {u.plan_name_ref for u in units if u.plan_name_ref}
    for p in plans:
        if p.plan_name not in plan_names_with_units and p.available_units_count:
            report["header_only_plans"] = report.get("header_only_plans", 0) + 1

    # TODO: deduplicate plans/units across repeated fragments or pagination
    # TODO: validate required fields before persisting

    return plans, units, report