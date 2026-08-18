import json
from functools import lru_cache
from pathlib import Path

ADDRESS_DIR = Path(__file__).resolve().parent / "static" / "address"


def _load_json(name):
    path = ADDRESS_DIR / name
    if not path.is_file():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def address_index():
    provinces = {
        item["id"]: item["name_th"]
        for item in _load_json("provinces.json")
        if not item.get("deleted_at")
    }
    districts = {
        item["id"]: item
        for item in _load_json("districts.json")
        if not item.get("deleted_at")
    }
    by_zip = {}
    for item in _load_json("sub_districts.json"):
        if item.get("deleted_at"):
            continue
        zip_code = str(item.get("zip_code") or "").strip()
        if not zip_code:
            continue
        district = districts.get(item.get("district_id")) or {}
        province_name = provinces.get(district.get("province_id"), "")
        row = {
            "tambon": item.get("name_th") or "",
            "amphure": district.get("name_th") or "",
            "province": province_name,
        }
        by_zip.setdefault(zip_code, [])
        if row not in by_zip[zip_code]:
            by_zip[zip_code].append(row)
    return by_zip


def lookup_zip(zip_code):
    code = str(zip_code or "").strip()
    if not code:
        return []
    return address_index().get(code, [])
