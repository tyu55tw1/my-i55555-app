# -*- coding: utf-8 -*-
"""每天會用到的生活資料(都免金鑰):垃圾車、停水停電、國道路況、附近店家/加油站/充電站、
記帳(發票 QR 金額)與繳費提醒的日期計算。這裡只放抓資料與計算,畫面在 daily_views.py。"""
from __future__ import annotations

import calendar
import csv
import html
import io
import json
import re
import xml.etree.ElementTree as ET
import zipfile
from datetime import date, datetime, timedelta

import core as K
import life as L

import time as _time

LOADED_AT = _time.time()   # app.py 用來判斷檔案更新後要不要重新載入
UA = {"User-Agent": "lifeapp/1.0 (personal use)"}
WD = "一二三四五六日"
COUNTIES = list(L.COUNTY_XY)


def tw(s) -> str:
    """臺 → 台,方便比對(各機關寫法不一)。"""
    return str(s or "").replace("臺", "台").strip()


def _get(url, timeout=(6, 40), **kw):
    r = K.NET.get(url, timeout=timeout, headers=UA, **kw)
    r.raise_for_status()
    return r


def _days(text) -> set[int]:
    """「一、二、四、六」→ {0, 1, 3, 5}(星期一 = 0)。"""
    return {WD.index(c) for c in str(text or "") if c in WD}


def _hm(t) -> str:
    t = re.sub(r"\D", "", str(t or ""))
    return f"{int(t[:-2]):02d}:{t[-2:]}" if len(t) in (3, 4) else ""


# ════════════════════════════════════════════════════════════════════
#  🗑️ 垃圾車
# ════════════════════════════════════════════════════════════════════
GARBAGE_SRC = {
    "臺南市": "https://data.tainan.gov.tw/Resource/84df8cd6-8741-41ed-919c-5105a28ecd6d?handler=GoJson",
    "臺北市": "https://data.taipei/api/dataset/6bb3304b-4f46-4bb0-8cd1-60c66dcd1cae/resource/a6e90031-7ec4-4089-afb5-361a4efe7202/download",
    "新北市": "https://data.ntpc.gov.tw/api/datasets/edc3ad26-8ae7-4916-a00b-bc6048d19bf8/csv/file",
}
TRUCK_SRC = {
    "新北市": "https://data.ntpc.gov.tw/api/datasets/28AB4122-60E1-4065-98E5-ABCCB69AACA6/json?size=1000",
    "臺中市": "https://newdatacenter.taichung.gov.tw/api/v1/no-auth/resource.download?rid=c923ad20-2ec6-43b9-b3ab-54527e99f7bc",
}
TAIPEI_DAYS = {0, 1, 3, 4, 5}   # 台北市:週日、週三不收


def parse_tainan_garbage(page: str) -> list[dict]:
    """台南的資料包在網頁的 <pre> 裡(HTML 跳脫過的 JSON)。"""
    m = re.search(r'<pre v-show="sourceType === type\.json">(.*?)</pre>', page, re.S)
    if not m:
        raise RuntimeError("台南垃圾車資料格式變了")
    out = []
    for x in json.loads(html.unescape(m.group(1))):
        try:
            lat, lon = float(x["LATITUDE"]), float(x["LONGITUDE"])
        except (TypeError, ValueError, KeyError):
            continue
        out.append({"area": x.get("AREA", ""), "village": x.get("VILLAGE", ""), "route": str(x.get("ROUTEID", "")),
                    "order": x.get("ROUTEORDER") or 0, "name": x.get("POINTNAME", ""), "time": _hm(x.get("TIME")),
                    "lat": lat, "lon": lon, "garbage": sorted(_days(x.get("WORKDAY") or x.get("WORDDAY"))),
                    "recycle": sorted(_days(x.get("RECYCLEDAY"))), "food": None, "memo": ""})
    return out


def parse_taipei_garbage(text: str) -> list[dict]:
    out = []
    for x in csv.DictReader(io.StringIO(text)):
        try:
            lat, lon = float(x["緯度"]), float(x["經度"])
        except (TypeError, ValueError, KeyError):
            continue
        out.append({"area": x.get("行政區", ""), "village": x.get("里別", ""), "route": f"{x.get('路線', '')} {x.get('車次', '')}".strip(),
                    "order": 0, "name": x.get("地點", ""), "time": _hm(x.get("抵達時間")), "lat": lat, "lon": lon,
                    "garbage": sorted(TAIPEI_DAYS), "recycle": sorted(TAIPEI_DAYS), "food": sorted(TAIPEI_DAYS),
                    "memo": f"停留到 {_hm(x.get('離開時間'))}" if x.get("離開時間") else ""})
    return out


def parse_ntpc_garbage(text: str) -> list[dict]:
    en = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    out = []
    for x in csv.DictReader(io.StringIO(text)):
        try:
            lat, lon = float(x["latitude"]), float(x["longitude"])
        except (TypeError, ValueError, KeyError):
            continue
        days = lambda k: [i for i, d in enumerate(en) if (x.get(f"{k}{d}") or "").upper() == "Y"]  # noqa: E731
        out.append({"area": x.get("city", ""), "village": x.get("village", ""), "route": x.get("linename", ""),
                    "order": int(x.get("rank") or 0), "name": x.get("name", ""), "time": _hm(x.get("time")),
                    "lat": lat, "lon": lon, "garbage": days("garbage"), "recycle": days("recycling"),
                    "food": days("foodscraps"), "memo": x.get("memo", "")})
    return out


def fetch_garbage(city: str) -> list[dict]:
    r = _get(GARBAGE_SRC[city], timeout=(8, 90))
    if city == "臺南市":
        return parse_tainan_garbage(r.content.decode("utf-8", "replace"))
    text = r.content.decode("utf-8-sig", "replace")
    return parse_taipei_garbage(text) if city == "臺北市" else parse_ntpc_garbage(text)


def near_points(points: list[dict], lat: float, lon: float, radius_km: float = 0.6, limit: int = 30) -> list[dict]:
    out = []
    for p in points:
        if abs(p["lat"] - lat) > 0.05 or abs(p["lon"] - lon) > 0.05:
            continue
        d = L.haversine(lat, lon, p["lat"], p["lon"])
        if d <= radius_km:
            out.append({**p, "dist": d})
    out.sort(key=lambda p: p["dist"])
    return out[:limit]


def next_visit(p: dict, now: datetime) -> tuple[date, str] | None:
    """這個清運點下一次收垃圾的日子和時間(今天已經過了就找之後的)。"""
    if not p.get("time"):
        return None
    days = set(p.get("garbage") or range(7))
    for off in range(8):
        d = now.date() + timedelta(days=off)
        if d.weekday() in days and (off or p["time"] >= f"{now:%H:%M}"):
            return d, p["time"]
    return None


def days_text(days) -> str:
    days = sorted(days or [])
    return "每天" if len(days) == 7 else ("、".join(WD[d] for d in days) if days else "—")


def parse_trucks(city: str, rows: list[dict]) -> list[dict]:
    out = []
    for x in rows:
        try:
            if city == "臺中市":
                lat, lon, t = float(x["Y"]), float(x["X"]), datetime.strptime(x["time"], "%Y%m%dT%H%M%S")
            else:
                lat, lon, t = float(x["latitude"]), float(x["longitude"]), datetime.strptime(x["time"], "%Y/%m/%d %H:%M:%S")
        except (KeyError, TypeError, ValueError):
            continue
        out.append({"car": x.get("car", ""), "line": x.get("lineid", ""), "where": x.get("location", ""),
                    "lat": lat, "lon": lon, "time": t})
    return out


def fetch_trucks(city: str) -> list[dict]:
    return parse_trucks(city, _get(TRUCK_SRC[city], timeout=(6, 30)).json())


# ════════════════════════════════════════════════════════════════════
#  🚱 停水・停電
# ════════════════════════════════════════════════════════════════════
POWER_URL = "https://service.taipower.com.tw/data/opendata/apply/file/d077004/001.zip"
WATER_URL = "https://web.water.gov.tw/wateroffapi/openData/export/json"
_SPAN = re.compile(r"(\d{4})/(\d{1,2})/(\d{1,2})\s*(\d{1,2}:\d{2})\s*~\s*(\d{1,2}:\d{2})")


def parse_power_zip(data: bytes, today: date) -> list[dict]:
    """台電計畫性停電:每個區處一個 CSV。同一工作(請求號數 + 時段)的停電範圍合在一起。只留今天以後的。"""
    groups: dict[tuple, dict] = {}
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for n in z.namelist():
            if not re.fullmatch(r"\d+\.csv", n):
                continue
            for row in csv.reader(io.StringIO(z.read(n).decode("utf-8-sig", "replace"))):
                if len(row) < 6 or row[0] == "營業區處":
                    continue
                for span in (row[3], row[4]):
                    m = _SPAN.search(span or "")
                    if not m:
                        continue
                    d = date(int(m[1]), int(m[2]), int(m[3]))
                    if d < today:
                        continue
                    g = groups.setdefault((row[1], d, m[4], m[5]), {"office": row[0], "id": row[1], "work": row[2], "date": d,
                                                                    "start": m[4], "end": m[5], "areas": []})
                    if row[5] and row[5] not in g["areas"]:
                        g["areas"].append(row[5])
    return sorted(groups.values(), key=lambda g: (g["date"], g["start"]))


def fetch_power(today: date) -> list[dict]:
    return parse_power_zip(_get(POWER_URL, timeout=(8, 60)).content, today)


def parse_water(rows: list[dict]) -> list[dict]:
    def dt(s):
        try:
            return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
        except (TypeError, ValueError):
            return None
    out = []
    for x in rows:
        nn = lambda v: "" if v in (None, "null", "[]") else str(v).strip("[]")  # noqa: E731
        out.append({"id": x.get("案件編號", ""), "start": dt(x.get("案件日期時間")), "end": dt(x.get("恢復日期時間")),
                    "type": x.get("案件類型", ""), "county": x.get("影響縣市", ""), "district": x.get("影響行政區", ""),
                    "area": nn(x.get("停水地區")), "reason": nn(x.get("停水原因")), "low": nn(x.get("降壓地區")),
                    "homes": x.get("影響戶數", ""), "tel": x.get("連絡電話", ""), "office": x.get("場所", "")})
    return sorted(out, key=lambda w: w["start"] or datetime.max)


def fetch_water() -> list[dict]:
    return parse_water(_get(WATER_URL, timeout=(6, 30)).json())


def match_place(text: str, county: str, district: str, keyword: str = "") -> bool:
    t = tw(text)
    return (not county or tw(county) in t or tw(county)[:2] in t[:4]) and (not district or tw(district) in t) and \
        (not keyword or tw(keyword) in t)


def power_for(rows, county, district, keyword="", now: datetime | None = None):
    out = []
    for g in rows:
        if now and g["date"] == now.date() and g["end"] < f"{now:%H:%M}":
            continue   # 今天已經結束的
        areas = [a for a in g["areas"] if match_place(a, county, district, keyword)]
        if areas:
            out.append({**g, "areas": areas})
    return out


def water_for(rows, county, district, keyword="", now: datetime | None = None):
    out = []
    for w in rows:
        if now and w["end"] and w["end"] < now:
            continue
        place = f"{w['county']}{w['district']}{w['area']}{w['low']}"
        if tw(county) == tw(w["county"]) and (not district or tw(district) in tw(w["district"]) + tw(w["area"])) and \
                (not keyword or tw(keyword) in tw(place)):
            out.append(w)
    return out


# ════════════════════════════════════════════════════════════════════
#  🚗 國道路況(高公局 1968 公開檔案,免金鑰,每分鐘更新)
# ════════════════════════════════════════════════════════════════════
FREEWAY = "https://tisvcloud.freeway.gov.tw/history/motc20/"
DIR_NAME = {"N": "北向", "S": "南向", "E": "東向", "W": "西向"}
_CN = {"一": "1", "二": "2", "三": "3", "四": "4", "五": "5", "六": "6", "七": "7", "八": "8", "九": "9", "十": "10"}


def _xml(content: bytes):
    root = ET.fromstring(content)
    for e in root.iter():
        e.tag = e.tag.split("}")[-1]
    return root


def _t(e, path, default=""):
    x = e.find(path)
    return x.text.strip() if x is not None and x.text else default


def km(s) -> float:
    m = re.match(r"\s*(\d+)K\+?(\d+)?", str(s or ""))
    return int(m[1]) + int(m[2] or 0) / 1000 if m else 0.0


def road_key(name: str) -> str:
    """「國道一號」「國道1號」→ 國道1號;國道3甲 這類保留原樣。"""
    s = str(name or "").strip()
    m = re.match(r"國道([一二三四五六七八九十]+)(.*)$", s)
    if m:
        n = m[1]
        v = 10 + int(_CN.get(n[1:], "0")) if n.startswith("十") and len(n) > 1 else int(_CN.get(n, "0"))
        return f"國道{v}{m[2]}"
    return s


def parse_sections(content: bytes) -> dict[str, dict]:
    out = {}
    for s in _xml(content).iter("Section"):
        sid = _t(s, "SectionID")
        if not sid:
            continue
        out[sid] = {"id": sid, "name": _t(s, "SectionName"), "road": road_key(_t(s, "RoadName")),
                    "dir": _t(s, "RoadDirection"), "start": _t(s, "RoadSection/Start"), "end": _t(s, "RoadSection/End"),
                    "km0": km(_t(s, "SectionMile/StartKM")), "km1": km(_t(s, "SectionMile/EndKM")),
                    "length": float(_t(s, "SectionLength", "0") or 0), "limit": int(_t(s, "SpeedLimit", "0") or 0)}
    return out


def parse_live(content: bytes) -> dict[str, dict]:
    out = {}
    for x in _xml(content).iter("LiveTraffic"):
        sid = _t(x, "SectionID")
        try:
            out[sid] = {"speed": int(_t(x, "TravelSpeed", "-1")), "time": int(_t(x, "TravelTime", "-1")),
                        "level": _t(x, "CongestionLevel")}
        except ValueError:
            continue
    return out


def parse_events(content: bytes) -> list[dict]:
    out = []
    for e in _xml(content).iter("LiveEvent"):
        fe = e.find("Location/FreeExpressHighway")
        out.append({"title": _t(e, "EventTitle"), "desc": _t(e, "Description"), "type": _t(e, "EventType"),
                    "road": road_key(_t(fe, "Road")) if fe is not None else "",
                    "dir": _t(fe, "Direction") if fe is not None else "",
                    "km0": km(_t(fe, "StartKM")) if fe is not None else 0, "km1": km(_t(fe, "EndKM")) if fe is not None else 0,
                    "impact": _t(e, "Impact/Description"), "lanes": _t(e, "Impact/BlockedLanes"),
                    "time": _t(e, "PublishTime")[:16].replace("T", " ")})
    return out


def fetch_freeway_static() -> dict[str, dict]:
    return parse_sections(_get(FREEWAY + "Section.xml").content)


def fetch_freeway_live() -> tuple[dict, list[dict]]:
    return parse_live(_get(FREEWAY + "LiveTraffic.xml").content), parse_events(_get(FREEWAY + "LiveEvents.xml").content)


def route_sections(sections: dict, road: str, d: str) -> list[dict]:
    """某條國道某方向的路段,依行車順序排好(往北/往西是里程變小)。"""
    rows = [s for s in sections.values() if s["road"] == road and s["dir"] == d]
    return sorted(rows, key=lambda s: s["km0"], reverse=d in ("N", "W"))


def speed_color(v, limit=100) -> str:
    if v is None or v < 0:
        return "#888888"
    return "#1f9d55" if v >= min(80, limit * .8) else "#d6a400" if v >= 60 else "#ee7d1a" if v >= 40 else "#d63a3a"


def trip(segs: list[dict], live: dict) -> dict:
    """一段路的行車時間(有即時資料的用即時,沒有的用速限估)、平均速度、塞車的路段。"""
    total_s, total_km, slow = 0.0, 0.0, []
    for s in segs:
        lv = live.get(s["id"]) or {}
        t = lv.get("time", -1)
        if t is None or t <= 0:
            t = s["length"] / max(s["limit"] or 90, 1) * 3600
        total_s += t
        total_km += s["length"]
        if 0 <= lv.get("speed", -1) < 60:
            slow.append((s, lv["speed"]))
    return {"min": total_s / 60, "km": total_km, "speed": total_km / (total_s / 3600) if total_s else 0, "slow": slow}


# ════════════════════════════════════════════════════════════════════
#  📍 位置:地址轉座標、附近的店 / 加油站 / 充電站
# ════════════════════════════════════════════════════════════════════
def geocode(q: str) -> tuple[float, float, str] | None:
    r = _get("https://nominatim.openstreetmap.org/search", timeout=(6, 20),
             params={"format": "json", "countrycodes": "tw", "limit": 1, "accept-language": "zh-TW", "q": q})
    j = r.json()
    if not j:
        return None
    return float(j[0]["lat"]), float(j[0]["lon"]), j[0].get("display_name", q)


OVERPASS = ["https://overpass-api.de/api/interpreter", "https://maps.mail.ru/osm/tools/overpass/api/interpreter"]
FOOD_KIND = {"restaurant": "🍽️ 餐廳", "fast_food": "🍔 速食小吃", "cafe": "☕ 咖啡早午餐", "food_court": "🏬 美食街",
             "ice_cream": "🍦 冰品", "bar": "🍺 酒吧"}
PHRASE = {"restaurant": "restaurant", "fast_food": "fast food", "cafe": "cafe", "food_court": "food court",
          "ice_cream": "ice cream", "bar": "bar", "fuel": "fuel", "charging_station": "charging station"}


def _overpass(lat, lon, radius, kinds) -> list[dict]:
    q = (f'[out:json][timeout:10];(nwr["amenity"~"^({"|".join(kinds)})$"](around:{radius},{lat:.5f},{lon:.5f}););'
         f'out center 300;')
    for url in OVERPASS:
        try:
            r = K.NET.post(url, data={"data": q}, timeout=(4, 10), headers=UA)
        except Exception:  # noqa: BLE001
            continue
        if r.status_code != 200 or not r.text.lstrip().startswith("{"):
            continue
        out = []
        for e in r.json().get("elements", []):
            tg = e.get("tags") or {}
            la, lo = e.get("lat") or (e.get("center") or {}).get("lat"), e.get("lon") or (e.get("center") or {}).get("lon")
            if la is not None:
                out.append({"id": f"{e.get('type')}{e.get('id')}", "name": tg.get("name:zh") or tg.get("name") or "",
                            "tags": tg, "lat": la, "lon": lo})
        return out
    return None


def _nominatim(lat, lon, radius, kinds) -> list[dict]:
    """Overpass 滿載時的備案:Nominatim 依種類查方框內的地點(每次最多 50 筆,滿了就切四塊再查)。"""
    import math
    import time
    dlat = radius / 111000
    dlon = radius / (111000 * max(math.cos(math.radians(lat)), .2))
    out, last = {}, [0.0]

    def ask(kind, la0, lo0, la1, lo1, depth=0):
        wait = 1.05 - (time.time() - last[0])   # Nominatim 規定每秒最多 1 次
        if wait > 0:
            time.sleep(wait)
        last[0] = time.time()
        r = _get("https://nominatim.openstreetmap.org/search", timeout=(6, 20),
                 params={"q": f"[{PHRASE[kind]}]", "format": "jsonv2", "viewbox": f"{lo0},{la1},{lo1},{la0}", "bounded": 1,
                         "limit": 50, "extratags": 1, "accept-language": "zh-TW"})
        j = r.json()
        for x in j:
            tg = {"amenity": x.get("type", kind), **(x.get("extratags") or {})}
            out[f"{x.get('osm_type')}{x.get('osm_id')}"] = {"id": f"{x.get('osm_type')}{x.get('osm_id')}", "name": x.get("name") or "",
                                                            "tags": tg, "lat": float(x["lat"]), "lon": float(x["lon"])}
        if len(j) >= 50 and depth == 0:   # 太多了查不完:切成四塊各查一次
            mla, mlo = (la0 + la1) / 2, (lo0 + lo1) / 2
            for a, b, c, d in ((la0, lo0, mla, mlo), (la0, mlo, mla, lo1), (mla, lo0, la1, mlo), (mla, mlo, la1, lo1)):
                ask(kind, a, b, c, d, 1)

    for k in kinds:
        ask(k, lat + dlat, lon - dlon, lat - dlat, lon + dlon)
    return list(out.values())


def _photon(lat, lon, radius, kinds) -> list[dict] | None:
    """Photon(komoot,OpenStreetMap 資料):依種類找附近的點,每種最多 50 筆。雲端伺服器上最不容易被擋。"""
    out = {}
    for k in kinds:
        r = K.NET.get("https://photon.komoot.io/reverse", timeout=(5, 15), headers=UA,
                      params={"lat": f"{lat:.5f}", "lon": f"{lon:.5f}", "radius": max(radius / 1000, .1), "limit": 50,
                              "osm_tag": f"amenity:{k}", "lang": "default"})
        if r.status_code != 200:
            return None
        for f in r.json().get("features", []):
            pr, (lo, la) = f.get("properties") or {}, f["geometry"]["coordinates"]
            addr = f"{pr.get('street', '')}{pr.get('housenumber', '')}"
            out[f"{pr.get('osm_type')}{pr.get('osm_id')}"] = {
                "id": f"{pr.get('osm_type')}{pr.get('osm_id')}", "name": pr.get("name") or "", "lat": la, "lon": lo,
                "tags": {"amenity": pr.get("osm_value", k), **({"addr:street": addr} if addr else {})}}
    return list(out.values())


def pois(lat: float, lon: float, radius: int, kinds: list[str]) -> list[dict]:
    """附近某些種類的地點(OpenStreetMap)。依序試 Photon → Overpass → Nominatim,哪個能用就用哪個。依距離排序。"""
    rows, errs = None, []
    for fn in (_photon, _overpass, _nominatim):
        try:
            rows = fn(lat, lon, radius, kinds)
        except Exception as e:  # noqa: BLE001
            errs.append(type(e).__name__)
            rows = None
        if rows is not None:
            break
    if rows is None:
        raise RuntimeError("店家資料的伺服器現在都太忙,等一兩分鐘再重新整理")
    out = []
    for r in rows:
        r["dist"] = L.haversine(lat, lon, r["lat"], r["lon"])
        if r["dist"] <= radius / 1000 * 1.05:
            out.append(r)
    return sorted(out, key=lambda x: x["dist"])


CUISINE_ZH = {"chinese": "中式", "taiwanese": "台式", "regional": "在地小吃", "noodle": "麵食", "breakfast": "早餐",
              "bubble_tea": "手搖飲", "tea": "茶飲", "coffee_shop": "咖啡", "coffee": "咖啡", "japanese": "日式", "ramen": "拉麵",
              "sushi": "壽司", "korean": "韓式", "thai": "泰式", "vietnamese": "越南", "malay": "馬來", "indian": "印度",
              "italian": "義式", "pizza": "披薩", "burger": "漢堡", "american": "美式", "western": "西式", "steak_house": "牛排",
              "chicken": "雞肉", "fried_chicken": "炸雞", "hot_pot": "火鍋", "barbecue": "燒烤", "dumpling": "水餃",
              "seafood": "海鮮", "vegetarian": "素食", "vegan": "全素", "dessert": "甜點", "ice_cream": "冰品", "bakery": "麵包",
              "sandwich": "三明治", "rice": "飯類", "beef_noodle": "牛肉麵", "lunch_box": "便當", "bento": "便當",
              "fast_food": "速食", "cafe": "咖啡", "soup": "湯品", "porridge": "粥", "curry": "咖哩", "brunch": "早午餐"}


def cuisine_zh(text: str) -> str:
    """OpenStreetMap 的料理種類(英文、分號分隔)→ 中文;看不懂的英文就不顯示。"""
    out = []
    for c in re.split(r"[;,]", str(text or "")):
        c = c.strip()
        z = CUISINE_ZH.get(c.lower()) or (c if c and not re.fullmatch(r"[A-Za-z_ -]+", c) else "")
        if z and z not in out:
            out.append(z)
    return "、".join(out)


def hours_zh(text: str) -> str:
    """OpenStreetMap 營業時間「Mo-Fr 11:00-20:00; Sa off」→「一-五 11:00-20:00;六 休」。"""
    t = str(text or "")
    for en, zh in (("Mo", "一"), ("Tu", "二"), ("We", "三"), ("Th", "四"), ("Fr", "五"), ("Sa", "六"), ("Su", "日"),
                   ("PH", "國定假日"), ("off", "休"), ("closed", "休"), ("24/7", "24 小時")):
        t = t.replace(en, zh)
    return t.replace("; ", ";").replace(", ", "、")


def fetch_food(lat, lon, radius) -> list[dict]:
    rows = [r for r in pois(lat, lon, radius, list(FOOD_KIND)) if r["name"]]
    for r in rows:
        r["kind"] = r["tags"].get("amenity", "")
        r["cuisine"] = r["tags"].get("cuisine", "")
        r["hours"] = r["tags"].get("opening_hours", "")
    return rows


CPC_URL = "https://vipmbr.cpc.com.tw/openData/getStationInfo"


def parse_cpc(rows: list[dict]) -> list[dict]:
    out = []
    for x in rows:
        try:
            lat, lon = float(x["緯度"]), float(x["經度"])
        except (KeyError, TypeError, ValueError):
            continue
        fuels = [n for k, n in (("無鉛92", "92"), ("無鉛95", "95"), ("無鉛98", "98"), ("超柴", "柴油")) if x.get(k) == 1]
        out.append({"name": "中油 " + str(x.get("站名", "")), "brand": "中油", "lat": lat, "lon": lon,
                    "addr": f"{x.get('縣市', '')}{x.get('鄉鎮區', '')}{x.get('地址', '')}", "tel": x.get("電話", ""),
                    "hours": x.get("營業時間", ""), "fuels": fuels, "self": bool(x.get("刷卡自助") or x.get("自助柴油站")),
                    "open": str(x.get("營業中", "1")) == "1", "kind": x.get("類別", "")})
    return out


def fetch_cpc() -> list[dict]:
    return parse_cpc(_get(CPC_URL, timeout=(8, 60)).json())


def fetch_fuel_osm(lat, lon, radius) -> list[dict]:
    """中油以外的加油站(台塑、全國…)和充電站,來自 OpenStreetMap。"""
    return pois(lat, lon, radius, ["fuel", "charging_station"])


# ════════════════════════════════════════════════════════════════════
#  📒 記帳 / 📅 繳費提醒
# ════════════════════════════════════════════════════════════════════
CATS = ["🍱 餐飲", "🛒 日用", "🚌 交通", "🎮 娛樂", "👕 服飾", "🏠 居家", "💊 醫療", "📚 學習", "🎁 人情", "💡 帳單", "📦 其他"]


def parse_invoice_money(text: str) -> dict | None:
    """電子發票左邊 QR:號碼(10) 日期(7) 隨機碼(4) 未稅額(8 hex) 總額(8 hex) 買方(8) 賣方統編(8) 加密(24) 後面是品項。"""
    t = (text or "").strip()
    m = re.match(r"^([A-Z]{2}\d{8})(\d{7})(\d{4})([0-9A-Fa-f]{8})([0-9A-Fa-f]{8})(\d{8})(\d{8})", t)
    if not m:
        return None
    d = L.roc_to_date(m[2])
    total = int(m[5], 16)
    item = ""
    try:   # 品項:「:**********:筆數:總筆數:編碼:品名:數量:單價…」,編碼 1 = UTF-8 才看得懂
        f = t[77:].split(":")
        if len(f) > 5 and f[4] == "1":
            item = f[5].strip()
    except IndexError:
        pass
    return {"inv": m[1], "date": d, "amount": total, "seller": m[7], "item": item}


def _clamp_day(y, m, d):
    return date(y, m, min(max(int(d or 1), 1), calendar.monthrange(y, m)[1]))


def next_due(item: dict, today: date) -> date | None:
    """提醒項目下一次的日期。kind:每月(day)、每年(month, day)、單次(date)。"""
    k = item.get("kind")
    try:
        if k == "每月":
            d = _clamp_day(today.year, today.month, item["day"])
            if d < today:
                y, m = (today.year + (today.month == 12), today.month % 12 + 1)
                d = _clamp_day(y, m, item["day"])
            return d
        if k == "每年":
            d = _clamp_day(today.year, int(item["month"]), item["day"])
            return d if d >= today else _clamp_day(today.year + 1, int(item["month"]), item["day"])
        if k == "單次":
            return date.fromisoformat(item["date"])
    except (KeyError, TypeError, ValueError):
        return None
    return None


DUE_PRESETS = [   # (名稱, 種類, 月, 日, 提早幾天, 說明)
    ("🚗 汽機車牌照稅", "每年", 4, 30, 14, "每年 4/1~4/30 繳納"),
    ("⛽ 汽機車燃料費", "每年", 7, 31, 14, "每年 7/1~7/31 繳納(自用小客車、機車)"),
    ("🏠 房屋稅", "每年", 5, 31, 14, "每年 5/1~5/31"),
    ("🌳 地價稅", "每年", 11, 30, 14, "每年 11/1~11/30"),
    ("🧾 綜合所得稅", "每年", 5, 31, 14, "每年 5 月申報"),
    ("💳 信用卡帳單", "每月", 0, 15, 3, "日期改成你的繳款截止日"),
    ("💧 水費", "每月", 0, 20, 3, "兩個月一期,日期改成帳單上的"),
    ("⚡ 電費", "每月", 0, 20, 3, "日期改成帳單上的"),
    ("🔥 瓦斯費", "每月", 0, 20, 3, "日期改成帳單上的"),
    ("📱 手機費", "每月", 0, 10, 3, "日期改成帳單上的"),
]


def month_sub_cost(subs: list[dict]) -> float:
    """訂閱每月平均要花多少(年繳的除以 12)。"""
    return sum(float(s.get("amt") or 0) / (12 if s.get("cycle") == "每年" else 1) for s in subs)


# ════════════════════════════════════════════════════════════════════
#  📚 漫畫追更(LINE WEBTOON 每部作品都有公開的 RSS;其他網站有 RSS 也可以)
# ════════════════════════════════════════════════════════════════════
def feed_url(link: str) -> str:
    """WEBTOON 作品頁 / 某一話的網址 → 這部作品的 RSS 網址;其他網址原樣當作 RSS。"""
    from urllib.parse import parse_qs, urlparse
    u = urlparse(link.strip())
    if "webtoons.com" not in u.netloc:
        return link.strip()
    tn = (parse_qs(u.query).get("title_no") or [""])[0]
    parts = [p for p in u.path.split("/") if p]
    if not tn or len(parts) < 3:
        raise ValueError("看不懂這個 WEBTOON 網址,請貼作品的目錄頁(網址裡有 title_no=)")
    return f"https://www.webtoons.com/{parts[0]}/{parts[1]}/{parts[2]}/rss?title_no={tn}"


def _rss_date(s: str):
    """「週三, 29 7月 2026 13:00:21 GMT」或英文「Wed, 29 Jul 2026 13:00:21 GMT」→ 台灣時間 datetime。"""
    from email.utils import parsedate_to_datetime
    try:
        d = parsedate_to_datetime(s)
    except (TypeError, ValueError):
        m = re.search(r"(\d{1,2})\s+(\d{1,2})月\s+(\d{4})\s+(\d{1,2}):(\d{2})", s or "")
        if not m:
            return None
        from datetime import timezone
        d = datetime(int(m[3]), int(m[2]), int(m[1]), int(m[4]), int(m[5]), tzinfo=timezone.utc)
    return d.astimezone(K.TW_TZ) if d.tzinfo else d


def fetch_feed(url: str) -> dict:
    r = K.NET.get(url, timeout=(6, 20), headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True)
    r.raise_for_status()
    root = _xml(r.content)
    ch = root.find("channel")
    if ch is None:
        raise RuntimeError("這個網址不是漫畫的更新資料(RSS)")
    items = [{"title": _t(it, "title"), "link": _t(it, "link"), "date": _rss_date(_t(it, "pubDate"))}
             for it in ch.findall("item")[:8]]
    return {"title": _t(ch, "title"), "link": _t(ch, "link"), "cover": _t(ch, "image/url"), "items": items}
