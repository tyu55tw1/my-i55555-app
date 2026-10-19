# -*- coding: utf-8 -*-
"""生活資訊資料層:停車、空品、警特報/地震/颱風/停班停課、行事曆、銀行牌告、除權息、發票 QR、分帳、換算。

全部是純函式(不依賴 Streamlit),方便測試;快取由 app.py 包裝。
"""
from __future__ import annotations

import io
import json
import math
import os
import re
import time
from datetime import date, datetime, timedelta

from bs4 import BeautifulSoup

import core as K

# ════════════════════════════════════════════════════════════════════
#  共用
# ════════════════════════════════════════════════════════════════════


def _f(v, default=None):
    try:
        x = float(str(v).replace(",", "").strip())
        return x if math.isfinite(x) else default
    except (TypeError, ValueError):
        return default


def haversine(lat1, lon1, lat2, lon2) -> float:
    """兩點距離(公里)。"""
    p = math.pi / 180
    a = (math.sin((lat2 - lat1) * p / 2) ** 2
         + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2)
    return 12742 * math.asin(math.sqrt(a))


def _secret(name: str) -> str:
    """API 金鑰:環境變數 → Streamlit secrets(沒有就回傳空字串)。"""
    v = os.environ.get(name, "")
    if not v:
        try:
            import streamlit as st
            v = st.secrets.get(name, "")  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001
            v = ""
    return v


def roc_to_date(s: str) -> date | None:
    """「115年10月15日」、「1151015」、「115/10/15」→ date。"""
    s = str(s).strip()
    if s.isdigit():
        if len(s) not in (6, 7):
            return None
        t = s.zfill(7)
        y, mo, d = int(t[:3]), int(t[3:5]), int(t[5:7])
    else:
        m = re.search(r"(\d{2,3})\D+(\d{1,2})\D+(\d{1,2})", s)
        if not m:
            return None
        y, mo, d = (int(x) for x in m.groups())
    try:
        return date(y + 1911, mo, d)
    except ValueError:
        return None


# 縣市中心座標(地震/空品最近測站、天氣城市都會用到)
COUNTY_XY = {
    "臺北市": (25.0375, 121.5637), "新北市": (25.0120, 121.4657), "基隆市": (25.1276, 121.7392),
    "桃園市": (24.9936, 121.3010), "新竹市": (24.8138, 120.9675), "新竹縣": (24.8387, 121.0177),
    "苗栗縣": (24.5602, 120.8214), "臺中市": (24.1477, 120.6736), "彰化縣": (24.0518, 120.5161),
    "南投縣": (23.9609, 120.9719), "雲林縣": (23.7092, 120.4313), "嘉義市": (23.4801, 120.4491),
    "嘉義縣": (23.4518, 120.2555), "臺南市": (22.9999, 120.2270), "高雄市": (22.6273, 120.3014),
    "屏東縣": (22.5519, 120.5487), "宜蘭縣": (24.7021, 121.7378), "花蓮縣": (23.9872, 121.6016),
    "臺東縣": (22.7583, 121.1444), "澎湖縣": (23.5711, 119.5793), "金門縣": (24.4493, 118.3767),
    "連江縣": (26.1505, 119.9499),
}

# ════════════════════════════════════════════════════════════════════
#  🅿️ 台北市停車場(臺北市政府交通局開放資料,免金鑰)
# ════════════════════════════════════════════════════════════════════
PARK_DESC_URL = "https://tcgbusfs.blob.core.windows.net/blobtcmsv/TCMSV_alldesc.json"
PARK_AVAIL_URL = "https://tcgbusfs.blob.core.windows.net/blobtcmsv/TCMSV_allavailable.json"


def _json_bytes(b: bytes):
    return json.loads(b.decode("utf-8-sig"))


def parse_parking_desc(j: dict) -> list[dict]:
    out = []
    for p in (j.get("data") or {}).get("park") or []:
        lat = lon = None
        for e in ((p.get("EntranceCoord") or {}).get("EntrancecoordInfo") or []):
            lat, lon = _f(e.get("Xcod")), _f(e.get("Ycod"))  # 網站欄位名稱 X=緯度、Y=經度
            if lat and lon:
                break
        if not (lat and 21 < lat < 27 and lon and 118 < lon < 123):
            lat = lon = None
        out.append({
            "id": p.get("id", ""), "area": p.get("area", ""), "name": p.get("name", ""),
            "address": p.get("address", ""), "tel": p.get("tel", ""), "pay": p.get("payex", ""),
            "hours": p.get("serviceTime", ""), "type": p.get("type2", ""),
            "total_car": int(_f(p.get("totalcar"), 0)), "total_motor": int(_f(p.get("totalmotor"), 0)),
            "ev": int(_f(p.get("ChargingStation"), 0)), "lat": lat, "lon": lon,
        })
    return out


def fetch_parking_desc() -> list[dict]:
    return parse_parking_desc(_json_bytes(K.http_get(PARK_DESC_URL, timeout=(6, 40)).content))


def parse_parking_avail(j: dict) -> tuple[dict, str]:
    d = j.get("data") or {}
    av = {}
    for p in d.get("park") or []:
        car, motor = _f(p.get("availablecar"), -9), _f(p.get("availablemotor"), -9)
        av[p.get("id", "")] = (int(car) if car >= 0 else None, int(motor) if motor >= 0 else None)
    upd = d.get("UPDATETIME", "")
    m = re.search(r"(\d{2}:\d{2}):\d{2}", upd)
    return av, (m.group(1) if m else upd)


def fetch_parking_avail() -> tuple[dict, str]:
    return parse_parking_avail(_json_bytes(K.http_get(PARK_AVAIL_URL, timeout=(6, 20)).content))


# ════════════════════════════════════════════════════════════════════
#  🌫️ 空氣品質(環境部 AQI;失敗改用 Open-Meteo 模式估計值)
# ════════════════════════════════════════════════════════════════════
# 政府資料開放平臺公告的公開下載連結金鑰;可在環境變數 / secrets 設 MOENV_API_KEY 換成自己的
MOENV_PUBLIC_KEY = "e8dd42e6-9b8b-43f8-991e-b3dee723a52d"
AQI_URL = "https://data.moenv.gov.tw/api/v2/aqx_p_432"

AQI_LEVELS = [  # (上限, 名稱, 顏色, 建議)
    (50, "良好", "#2e9e5b", "空氣很好,適合戶外活動。"),
    (100, "普通", "#d6a400", "極少數敏感者應考慮減少長時間戶外劇烈活動。"),
    (150, "對敏感族群不健康", "#ec7a1c", "有心臟、呼吸道疾病者、孩童與年長者應減少戶外劇烈活動。"),
    (200, "對所有族群不健康", "#d63a3a", "所有人都應減少戶外活動,外出建議戴口罩。"),
    (300, "非常不健康", "#8e44ad", "所有人應避免戶外活動,關閉門窗。"),
    (10**9, "危害", "#7a1f2b", "所有人應留在室內並減少體力消耗。"),
]


def aqi_level(aqi) -> tuple[str, str, str]:
    v = _f(aqi)
    if v is None:
        return "設備維護", "#888", "測站暫時沒有資料。"
    for hi, name, col, tip in AQI_LEVELS:
        if v <= hi:
            return name, col, tip
    return AQI_LEVELS[-1][1:]


def parse_aqi(j) -> list[dict]:
    rec = j.get("records") if isinstance(j, dict) else j
    out = []
    for r in rec or []:
        out.append({
            "site": r.get("sitename", ""), "county": r.get("county", ""), "aqi": _f(r.get("aqi")),
            "status": r.get("status", ""), "pollutant": r.get("pollutant", ""),
            "pm25": _f(r.get("pm2.5")), "pm10": _f(r.get("pm10")), "o3": _f(r.get("o3_8hr") or r.get("o3")),
            "time": r.get("publishtime", ""), "lat": _f(r.get("latitude")), "lon": _f(r.get("longitude")),
        })
    return [x for x in out if x["site"]]


def fetch_aqi() -> list[dict]:
    key = _secret("MOENV_API_KEY") or MOENV_PUBLIC_KEY
    r = K.http_get(AQI_URL, timeout=(6, 25), params={"api_key": key, "limit": 1000, "format": "JSON"})
    if "呼叫API的次數" in r.text[:200]:   # 環境部回傳文字而不是 JSON：這把金鑰今天的額度用完了
        raise RuntimeError("環境部 API 今天的呼叫次數用完了" + ("" if _secret("MOENV_API_KEY") else
                           "（目前用的是大家共用的示範金鑰，請到 Secrets 設定自己的 MOENV_API_KEY）"))
    data = parse_aqi(r.json())
    if not data:
        raise ValueError("環境部 AQI 資料為空")
    return data


def fetch_aqi_openmeteo(lat: float, lon: float) -> dict:
    r = K.http_get("https://air-quality-api.open-meteo.com/v1/air-quality", timeout=(6, 12),
                   params={"latitude": lat, "longitude": lon, "current": "us_aqi,pm2_5,pm10,ozone", "timezone": "Asia/Taipei"})
    c = r.json().get("current") or {}
    return {"aqi": _f(c.get("us_aqi")), "pm25": _f(c.get("pm2_5")), "pm10": _f(c.get("pm10")), "time": c.get("time", "")}


# ════════════════════════════════════════════════════════════════════
#  ⚠️ 警特報 / 地震 / 颱風 / 停班停課
# ════════════════════════════════════════════════════════════════════
CWA = "https://www.cwa.gov.tw"
WARN_JS = CWA + "/Data/js/warn/Warning_Content.js"
EQ_LIST = CWA + "/V8/C/E/MOD/EQ_ROW.html"
TY_JS = CWA + "/Data/js/typhoon/TY_NEWS-Data.js"
DGPA_URL = "https://www.dgpa.gov.tw/typh/daily/nds.html"

_JS_STR = r"'((?:[^'\\]|\\.)*)'"


def _js_unescape(s: str) -> str:
    return s.replace("\\n", "\n").replace("\\'", "'").replace('\\"', '"').replace("\\\\", "\\")


def parse_cwa_warnings(js: str) -> list[dict]:
    out = []
    pat = re.compile(r"'(\w+)'\s*:\s*\{\s*'C'\s*:\s*\{\s*'title'\s*:\s*" + _JS_STR + r"\s*,\s*'issued'\s*:\s*" + _JS_STR
                     + r"\s*,\s*'validto'\s*:\s*" + _JS_STR + r"\s*,\s*'content'\s*:\s*" + _JS_STR, re.S)
    for wid, title, issued, validto, content in pat.findall(js):
        text = _js_unescape(content).strip()
        text = re.sub(r"^發布時間[:：]\s*\S+\s+\S+\s*", "", text).strip()
        out.append({"id": wid, "title": _js_unescape(title), "issued": issued, "validto": validto, "content": text})
    return out


def fetch_cwa_warnings() -> list[dict]:
    return parse_cwa_warnings(K.http_get(WARN_JS, timeout=(6, 15), encoding="utf-8").text)


def parse_earthquakes(html: str) -> list[dict]:
    out = []
    for tr in BeautifulSoup(html, "html.parser").find_all("tr"):
        tds = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
        txt = " ".join(tds)
        m_t = re.search(r"(\d{2}/\d{2} \d{2}:\d{2})", txt)
        m_m = re.search(r"規模\s*([\d.]+)", txt)
        if not (m_t and m_m):
            continue
        m_p = re.search(r"地點\s*(.+?)\s*深度", txt)
        m_d = re.search(r"深度\s*([\d.]+)\s*km", txt)
        m_i = re.search(r"(\d)\s*級", txt)
        place = m_p.group(1) if m_p else ""
        short = re.search(r"\(位於(.+?)\)", place)
        a = tr.find("a", href=True)
        out.append({"no": tds[0] if tds and tds[0] != "小區域" else "", "local": bool(tds and tds[0] == "小區域"),
                    "time": m_t.group(1), "intensity": int(m_i.group(1)) if m_i else None, "mag": float(m_m.group(1)),
                    "depth": _f(m_d.group(1)) if m_d else None, "place": place, "where": short.group(1) if short else place,
                    "url": CWA + a["href"] if a and a["href"].startswith("/") else ""})
    return out


def fetch_earthquakes() -> list[dict]:
    try:
        eq = parse_earthquakes(K.http_get(EQ_LIST, timeout=(6, 15), encoding="utf-8").text)
        if eq:
            return eq
    except Exception:  # noqa: BLE001
        pass
    # 備援:USGS(只有規模 4 以上,無震度)
    r = K.http_get("https://earthquake.usgs.gov/fdsnws/event/1/query", timeout=(6, 15), params={
        "format": "geojson", "minlatitude": 21, "maxlatitude": 26.5, "minlongitude": 119, "maxlongitude": 123,
        "minmagnitude": 4, "limit": 15, "orderby": "time"})
    out = []
    for f in r.json().get("features") or []:
        p, (lon, lat, dep) = f["properties"], f["geometry"]["coordinates"][:3]
        t = datetime.fromtimestamp(p["time"] / 1000, K.TW_TZ)
        near = min(COUNTY_XY, key=lambda c: haversine(lat, lon, *COUNTY_XY[c]))
        out.append({"no": "", "local": False, "time": t.strftime("%m/%d %H:%M"), "intensity": None, "mag": p.get("mag"),
                    "depth": dep, "place": f"{near}附近(USGS)", "where": f"{near}附近", "url": p.get("url", "")})
    return out


def parse_typhoons(js: str) -> list[dict]:
    m = re.search(r"TY_LIST_1\['C'\]\s*=\s*(.+?);\s*\n", js, re.S)
    if not m:
        return []
    html = "".join(_js_unescape(x) for x in re.findall(_JS_STR, m.group(1)))
    out = []
    for panel in BeautifulSoup(html, "html.parser").select("div.panel"):
        a = panel.find("a")
        strength = a.find("span", class_="fa-red").get_text(strip=True) if a and a.find("span", class_="fa-red") else ""
        name = a.find("span", class_="fa-blue").get_text(strip=True) if a and a.find("span", class_="fa-blue") else ""
        head = a.get_text(" ", strip=True) if a else ""
        en = re.search(r"國際命名\s*(\S+)", head)
        no = re.search(r"編號第\s*(\d+)\s*號", head)
        body = panel.find(class_="panel-body")
        out.append({"name": name, "strength": strength, "en": en.group(1) if en else "", "no": no.group(1) if no else "",
                    "desc": body.get_text("", strip=True) if body else ""})
    return out


def fetch_typhoons() -> list[dict]:
    return parse_typhoons(K.http_get(TY_JS, timeout=(6, 15), encoding="utf-8").text)


def parse_closures(html: str) -> tuple[list[tuple[str, str]], str]:
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for tr in soup.find_all("tr"):
        tds = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
        if len(tds) == 2 and tds[0] and "縣市名稱" not in tds[0] and len(tds[0]) <= 12:
            rows.append((tds[0], tds[1]))
    m = re.search(r"更新時間[:：]?\s*([\d/]+\s*[\d:]+)", soup.get_text(" ", strip=True))
    return rows, (m.group(1) if m else "")


def fetch_closures() -> tuple[list[tuple[str, str]], str]:
    return parse_closures(K.http_get(DGPA_URL, timeout=(6, 15), encoding="utf-8").text)


# ════════════════════════════════════════════════════════════════════
#  📅 國定假日 / 補班(行政院人事行政總處行事曆,經 jsDelivr 鏡像)
# ════════════════════════════════════════════════════════════════════
CAL_URL = "https://cdn.jsdelivr.net/gh/ruyut/TaiwanCalendar/data/{year}.json"


def parse_calendar(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        try:
            d = datetime.strptime(str(r["date"]), "%Y%m%d").date()
        except (KeyError, ValueError):
            continue
        off = bool(r.get("isHoliday"))
        desc = (r.get("description") or "").strip()
        out.append({"date": d, "off": off, "desc": desc, "makeup": (not off) and d.weekday() >= 5})
    return sorted(out, key=lambda x: x["date"])


def fetch_calendar(year: int) -> list[dict]:
    r = K.http_get(CAL_URL.format(year=year), timeout=(6, 15))
    return parse_calendar(json.loads(r.content.decode("utf-8-sig")))


def long_weekends(days: list[dict], min_len: int = 3) -> list[dict]:
    """連續放假 ≥ min_len 天的區間(含週末)。名稱取區間內第一個節日說明。"""
    out, run = [], []
    for d in days + [{"date": None, "off": False}]:
        if d["off"]:
            run.append(d)
            continue
        if len(run) >= min_len:
            names = [x["desc"] for x in run if x.get("desc") and x["desc"] not in ("", "補假")] or [x["desc"] for x in run if x.get("desc")]
            out.append({"start": run[0]["date"], "end": run[-1]["date"], "days": len(run),
                        "name": "、".join(dict.fromkeys(n for n in names if n)) or "連假"})
        run = []
    return out


def leave_hacks(days: list[dict], max_leave: int = 2, min_gain: int = 4) -> list[dict]:
    """請假攻略:請 1~max_leave 天假,能連休幾天。只列出有國定假日參與、且連休 ≥ min_gain 的組合。"""
    idx = {d["date"]: d for d in days}
    out, seen = [], set()
    work = [d["date"] for d in days if not d["off"] and d["date"].weekday() < 5]
    for i, start in enumerate(work):
        for k in range(1, max_leave + 1):
            leave = work[i:i + k]
            if len(leave) < k or (leave[-1] - leave[0]).days != k - 1:  # 請的假要連續
                continue
            lo = leave[0] - timedelta(days=1)
            while lo in idx and idx[lo]["off"]:
                lo -= timedelta(days=1)
            hi = leave[-1] + timedelta(days=1)
            while hi in idx and idx[hi]["off"]:
                hi += timedelta(days=1)
            lo, hi = lo + timedelta(days=1), hi - timedelta(days=1)
            total = (hi - lo).days + 1
            has_holiday = any(idx[lo + timedelta(days=j)]["desc"] for j in range(total) if (lo + timedelta(days=j)) in idx)
            if total >= min_gain and has_holiday and (lo, hi) not in seen and total - k >= 3:
                seen.add((lo, hi))
                out.append({"leave": leave, "start": lo, "end": hi, "days": total, "cost": k})
    # 重疊的區間視為同一段假期;每段假期、每種請假天數只留連休最長的,且多請一天要至少多休 2 天才列出
    out.sort(key=lambda x: (x["start"], x["end"]))
    groups, cur, cur_end = [], [], None
    for x in out:
        if cur and x["start"] > cur_end:
            groups.append(cur)
            cur = []
        cur.append(x)
        cur_end = max(cur_end, x["end"]) if cur_end and len(cur) > 1 else x["end"]
    if cur:
        groups.append(cur)
    res = []
    for g in groups:
        by_cost = {}
        for x in g:
            if x["cost"] not in by_cost or x["days"] > by_cost[x["cost"]]["days"]:
                by_cost[x["cost"]] = x
        prev = 0
        for k in sorted(by_cost):
            if by_cost[k]["days"] >= prev + 2:
                res.append(by_cost[k])
                prev = by_cost[k]["days"]
    return sorted(res, key=lambda x: (x["start"], x["cost"]))


# ════════════════════════════════════════════════════════════════════
#  🏦 銀行牌告匯率(現鈔 / 即期)
# ════════════════════════════════════════════════════════════════════
FIRSTBANK_URL = "https://ibank.firstbank.com.tw/NetBank/7/0201.html?sh=none"
SINOPAC_URL = "https://mma.sinopac.com/ws/share/rate/ws_exchange.ashx"


def parse_firstbank(html: str) -> dict:
    out = {}
    for tr in BeautifulSoup(html, "html.parser").find_all("tr"):
        tds = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
        if len(tds) < 4:
            continue
        m = re.search(r"\(([A-Z]{3})\)", tds[0])
        kind = {"即期": "spot", "現鈔": "cash"}.get(tds[1].strip())
        if not (m and kind):
            continue
        buy, sell = _f(tds[2]), _f(tds[3])
        if buy and sell:
            out.setdefault(m.group(1), {})[kind] = (buy, sell)
    return out


def parse_sinopac(j, kind: str) -> dict:
    out = {}
    for blk in j if isinstance(j, list) else [j]:
        for r in blk.get("SubInfo") or []:
            code = r.get("DataValue4") or ""
            buy, sell = _f(r.get("DataValue2")), _f(r.get("DataValue3"))
            if re.fullmatch(r"[A-Z]{3}", code) and buy and sell:
                out.setdefault(code, {})[kind] = (buy, sell)
    return out


def fetch_bank_rates() -> dict:
    """回傳 {"bank": 銀行名稱, "rates": {USD: {"cash": (買, 賣), "spot": (買, 賣)}}, "time": 抓取時間}"""
    errs = []
    try:
        rates = parse_firstbank(K.http_get(FIRSTBANK_URL, timeout=(6, 15), encoding="utf-8").text)
        if len(rates) >= 5:
            return {"bank": "第一銀行", "rates": rates, "time": K.tw_now().strftime("%m/%d %H:%M")}
    except Exception as e:  # noqa: BLE001
        errs.append(e)
    rates = {}
    for typ, kind in (("CASH", "cash"), ("REMIT", "spot")):
        for code, v in parse_sinopac(K.http_get(SINOPAC_URL, timeout=(6, 15), params={"exchangeType": typ}).json(), kind).items():
            rates.setdefault(code, {}).update(v)
    if not rates:
        raise RuntimeError(f"銀行牌告都抓不到({errs[0] if errs else '無資料'})")
    return {"bank": "永豐銀行", "rates": rates, "time": K.tw_now().strftime("%m/%d %H:%M")}


# ════════════════════════════════════════════════════════════════════
#  📈 自選股報價(證交所即時,一次查多檔)/ 除權息預告
# ════════════════════════════════════════════════════════════════════
def fetch_quotes(codes: list[str]) -> dict:
    """一次查多檔(證交所一次請求太多檔會回空的,所以每 20 檔分一批)。"""
    codes = list(dict.fromkeys(c.strip().upper() for c in codes if re.fullmatch(r"[0-9A-Z]{4,8}", c.strip().upper())))
    out = {}
    for i in range(0, len(codes), 20):
        out.update(_fetch_quotes(codes[i:i + 20]))
    return out


def _fetch_quotes(codes: list[str]) -> dict:
    if not codes:
        return {}
    sess = K._mis_session
    ex_ch = "|".join(f"{m}_{c}.tw" for c in codes for m in ("tse", "otc"))
    for attempt in range(2):
        if attempt or not sess.cookies:
            try:
                K.http_get(K.MIS_HOME, session=sess, timeout=(6, 10))
            except Exception:  # noqa: BLE001
                pass
        r = K.http_get(K.MIS_API, session=sess, timeout=(6, 12), headers={"Referer": K.MIS_HOME},
                       params={"ex_ch": ex_ch, "json": "1", "delay": "0", "_": int(time.time() * 1000)})
        arr = (r.json() or {}).get("msgArray") or []
        if arr:
            break
    out = {}
    for it in arr:
        c = it.get("c")
        if c not in codes or not it.get("n"):
            continue
        price, prev = _f(it.get("z")), _f(it.get("y"))
        if price is None:  # 盤中尚未成交 → 用最佳買價/昨收
            bid = (it.get("b") or "").split("_")[0]
            price = _f(bid) or prev
        out[c] = {"code": c, "name": it["n"], "price": price, "prev": prev, "high": _f(it.get("h")), "low": _f(it.get("l")),
                  "volume": _f(it.get("v")), "time": it.get("t", ""), "market": "上市" if it.get("ex") == "tse" else "上櫃"}
    return out


TWSE_DIV = "https://www.twse.com.tw/rwd/zh/exRight/TWT48U"
TPEX_DIV = "https://www.tpex.org.tw/openapi/v1/tpex_exright_prepost"


def parse_twse_div(j: dict) -> list[dict]:
    out = []
    f = j.get("fields") or []
    for row in j.get("data") or []:
        r = dict(zip(f, row))
        d = roc_to_date(r.get("除權除息日期", ""))
        if not d:
            continue
        out.append({"date": d, "code": str(r.get("股票代號", "")).strip(), "name": str(r.get("名稱", "")).strip(),
                    "kind": r.get("除權息", ""), "cash": _f(r.get("現金股利"), 0.0), "stock": _f(r.get("無償配股率"), 0.0),
                    "market": "上市"})
    return out


def parse_tpex_div(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows or []:
        d = roc_to_date(r.get("ExRrightsExDividendDate", ""))
        if not d:
            continue
        out.append({"date": d, "code": str(r.get("SecuritiesCompanyCode", "")).strip(), "name": str(r.get("CompanyName", "")).strip(),
                    "kind": r.get("ExRrightsExDividend", "").replace("除", ""), "cash": _f(r.get("CashDividend"), 0.0),
                    "stock": _f(r.get("StockDividendRatio"), 0.0), "market": "上櫃"})
    return out


def fetch_dividends() -> list[dict]:
    out, errs = [], []
    try:
        out += parse_twse_div(K.http_get(TWSE_DIV, timeout=(6, 15), params={"response": "json"}).json())
    except Exception as e:  # noqa: BLE001
        errs.append(e)
    try:
        out += parse_tpex_div(K.http_get(TPEX_DIV, timeout=(6, 15)).json())
    except Exception as e:  # noqa: BLE001
        errs.append(e)
    if not out and errs:
        raise errs[0]
    today = K.tw_now().date()
    return sorted((x for x in out if x["date"] >= today - timedelta(days=3)), key=lambda x: (x["date"], x["code"]))


# ════════════════════════════════════════════════════════════════════
#  🧾 電子發票 QR Code
# ════════════════════════════════════════════════════════════════════
INV_QR_RE = re.compile(r"^([A-Z]{2})(\d{8})(\d{7})")


def parse_invoice_qr(text: str) -> dict | None:
    """左邊 QR:前 10 碼字軌號碼 + 7 碼民國日期(yyyMMdd)。右邊 QR 以 ** 開頭,略過。"""
    m = INV_QR_RE.match((text or "").strip())
    if not m:
        return None
    d = roc_to_date(m.group(3))
    return {"track": m.group(1), "number": m.group(2), "date": d}


def decode_qr_texts(image_bytes: bytes) -> list[str]:
    """用 OpenCV 解出圖片中所有 QR Code 文字(會嘗試放大與二值化,提高手機照片成功率)。"""
    import cv2  # 延遲載入:沒有安裝 opencv 時其他功能照常
    import numpy as np

    from PIL import Image, ImageOps
    im = ImageOps.exif_transpose(Image.open(io.BytesIO(image_bytes))).convert("L")
    im.thumbnail((1800, 1800))
    base = np.array(im)
    texts: list[str] = []
    det = cv2.QRCodeDetector()
    variants = [base]
    if max(base.shape) < 1000:
        variants.append(cv2.resize(base, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC))
    variants.append(cv2.adaptiveThreshold(base, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 5))
    for v in variants:
        try:
            ok, decoded, _, _ = det.detectAndDecodeMulti(v)
            if ok:
                texts += [t for t in decoded if t]
        except cv2.error:
            pass
        if not texts:
            try:
                t, _, _ = det.detectAndDecode(v)
                if t:
                    texts.append(t)
            except cv2.error:
                pass
        if any(parse_invoice_qr(t) for t in texts):
            break
    return list(dict.fromkeys(texts))


def invoice_period_title(d: date) -> tuple[int, int]:
    """發票日期 → (民國年, 期別結束月),例如 2026/10/03 → (115, 10)。"""
    end_m = d.month + (d.month % 2)
    return d.year - 1911, end_m


# ════════════════════════════════════════════════════════════════════
#  🍱 聚餐分帳
# ════════════════════════════════════════════════════════════════════
def settle(paid: dict[str, float], owe: dict[str, float]) -> list[tuple[str, str, int]]:
    """paid=每人實際付了多少,owe=每人應分攤多少 → 最少轉帳次數的近似解 [(誰, 給誰, 金額)]。"""
    bal = {p: round(paid.get(p, 0) - owe.get(p, 0)) for p in set(paid) | set(owe)}
    cred = sorted([[p, v] for p, v in bal.items() if v > 0], key=lambda x: -x[1])
    debt = sorted([[p, -v] for p, v in bal.items() if v < 0], key=lambda x: -x[1])
    out, i, j = [], 0, 0
    while i < len(debt) and j < len(cred):
        amt = min(debt[i][1], cred[j][1])
        if amt > 0:
            out.append((debt[i][0], cred[j][0], int(amt)))
        debt[i][1] -= amt
        cred[j][1] -= amt
        if debt[i][1] <= 0:
            i += 1
        if cred[j][1] <= 0:
            j += 1
    return out


def split_bill(members: list[str], items: list[dict], service: float = 0.0) -> dict:
    """items: [{"name", "payer", "amount", "share": [成員…]}];service=服務費比例(0.1 = 10%)。"""
    paid = {m: 0.0 for m in members}
    owe = {m: 0.0 for m in members}
    total = 0.0
    for it in items:
        amt = float(it.get("amount") or 0) * (1 + service)
        if amt <= 0 or it.get("payer") not in paid:
            continue
        share = [m for m in it.get("share") or members if m in owe] or members
        total += amt
        paid[it["payer"]] += amt
        for m in share:
            owe[m] += amt / len(share)
    return {"total": total, "paid": paid, "owe": owe, "transfers": settle(paid, owe)}


# ════════════════════════════════════════════════════════════════════
#  📐 單位換算 / BMI
# ════════════════════════════════════════════════════════════════════
UNITS = {  # 類別 → {單位: 換算成基準單位的倍數}
    "面積": {"坪": 3.305785, "平方公尺": 1, "平方公分": 1e-4, "平方英尺": 0.09290304, "公頃": 10000, "甲": 9699.17, "分(地)": 969.917},
    "重量": {"台斤": 0.6, "公斤": 1, "公克": 0.001, "台兩": 0.0375, "磅": 0.45359237, "盎司": 0.028349523},
    "長度": {"公分": 0.01, "公尺": 1, "公里": 1000, "吋": 0.0254, "呎": 0.3048, "台尺": 0.30303, "英里": 1609.344},
    "容量": {"毫升": 0.001, "公升": 1, "杯(240ml)": 0.24, "加侖(美)": 3.785411784, "液量盎司": 0.0295735},
}


def convert(value: float, cat: str, src: str, dst: str) -> float:
    if cat == "溫度":
        c = value if src == "°C" else (value - 32) * 5 / 9 if src == "°F" else value - 273.15
        return c if dst == "°C" else c * 9 / 5 + 32 if dst == "°F" else c + 273.15
    u = UNITS[cat]
    return value * u[src] / u[dst]


BMI_LEVELS = [(18.5, "過輕", "#2f7de1"), (24, "正常", "#2e9e5b"), (27, "過重", "#d6a400"),
              (30, "輕度肥胖", "#ec7a1c"), (35, "中度肥胖", "#d63a3a"), (10**9, "重度肥胖", "#8e44ad")]


def bmi_info(cm: float, kg: float) -> dict:
    m = cm / 100
    bmi = kg / (m * m)
    name, col = next((n, c) for hi, n, c in BMI_LEVELS if bmi < hi)
    return {"bmi": bmi, "level": name, "color": col, "lo": 18.5 * m * m, "hi": 24 * m * m}


def bmr(cm: float, kg: float, age: int, male: bool) -> float:
    """Mifflin-St Jeor 基礎代謝率(大卡/天)。"""
    return 10 * kg + 6.25 * cm - 5 * age + (5 if male else -161)
