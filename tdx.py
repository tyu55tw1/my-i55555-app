# -*- coding: utf-8 -*-
"""交通部 TDX 公車資料（從「智慧交通規劃」公車 app 搬過來的精簡版）：路線、站序、即時到站。
需要 TDX 金鑰（Streamlit Secrets：TDX_CLIENT_ID、TDX_CLIENT_SECRET）。免費金鑰每分鐘只能查 5 次。"""
from __future__ import annotations

import re
import time

import core as K

TOKEN_URL = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
BASIC = "https://tdx.transportdata.tw/api/basic"
CITIES = {"臺北市": "Taipei", "新北市": "NewTaipei", "桃園市": "Taoyuan", "臺中市": "Taichung", "臺南市": "Tainan",
          "高雄市": "Kaohsiung", "基隆市": "Keelung", "新竹市": "Hsinchu", "新竹縣": "HsinchuCounty",
          "苗栗縣": "MiaoliCounty", "彰化縣": "ChanghuaCounty", "南投縣": "NantouCounty", "雲林縣": "YunlinCounty",
          "嘉義市": "Chiayi", "嘉義縣": "ChiayiCounty", "屏東縣": "PingtungCounty", "宜蘭縣": "YilanCounty",
          "花蓮縣": "HualienCounty", "臺東縣": "TaitungCounty", "金門縣": "KinmenCounty", "澎湖縣": "PenghuCounty",
          "連江縣": "LienchiangCounty", "公路客運(國道/跨縣市)": "InterCity"}
STATUS = {1: "尚未發車", 2: "交管不停靠", 3: "末班車已過", 4: "今日未營運"}


def token(cid, secret):
    r = K.NET.post(TOKEN_URL, timeout=(6, 15), data={"grant_type": "client_credentials", "client_id": cid,
                                                     "client_secret": secret})
    if r.status_code != 200:
        raise RuntimeError("TDX 金鑰不對，請檢查 Secrets 的 TDX_CLIENT_ID、TDX_CLIENT_SECRET")
    return r.json()["access_token"]


def get(tok, path, wait=60, **params):
    """查 TDX；被限流（每分鐘 5 次）時等的秒數不超過 wait 就自動等一下再查。"""
    for attempt in range(2):
        r = K.NET.get(BASIC + path, timeout=(6, 20), params={"$format": "JSON", **params},
                      headers={"authorization": f"Bearer {tok}"})
        if r.status_code == 429:
            try:
                left = int(r.headers.get("RateLimit-Reset") or r.headers.get("Retry-After") or 60)
            except ValueError:
                left = 60
            if attempt == 0 and left <= wait:
                time.sleep(left + 1)
                continue
            raise RuntimeError(f"TDX 免費金鑰每分鐘只能查 5 次，請 {left} 秒後再試")
        if r.status_code != 200:
            raise RuntimeError(f"TDX 查詢失敗(HTTP {r.status_code})")
        return r.json()
    raise RuntimeError("TDX 查詢失敗")


def zh(x):
    return ((x or {}).get("Zh_tw") or "").replace("臺", "台") if isinstance(x, dict) else str(x or "")


def _path(kind, city):
    return f"/v2/Bus/{kind}/InterCity" if city == "InterCity" else f"/v2/Bus/{kind}/City/{city}"


def _rf(route):
    return "RouteName/Zh_tw eq '" + str(route).replace("台", "臺").replace("'", "''") + "'"


def routes(tok, city):
    names = {zh(x.get("RouteName")) for x in get(tok, _path("Route", city), **{"$select": "RouteName"})}
    return sorted((n for n in names if n), key=lambda n: (not n[:1].isdigit(), len(n), n))


def stop_of_route(tok, city, route):
    """[{sub, name, dir, stops: [(StopUID, 站名)]}]，每個方向（子路線）一筆。"""
    out = []
    for r in get(tok, _path("StopOfRoute", city), **{"$filter": _rf(route)}):
        seq = [(s.get("StopUID"), zh(s.get("StopName"))) for s in r.get("Stops") or []]
        if seq:
            out.append({"sub": r.get("SubRouteUID"), "name": zh(r.get("SubRouteName")) or zh(r.get("RouteName")),
                        "dir": r.get("Direction", 0), "stops": seq})
    return out


def stops_eta(tok, city, uids):
    """這些站牌所有路線的即時到站原始資料。查 1 次。"""
    f = " or ".join(f"StopUID eq '{u}'" for u in uids)
    return get(tok, _path("EstimatedTimeOfArrival", city), **{"$filter": f})


def eta_text(e):
    """→ (樣式, 文字)：進站中、幾分、尚未發車…"""
    if not e:
        return "mute", "暫無資料"   # 收班後或還沒發車，TDX 常常整筆都沒有
    sec, stat = e.get("EstimateTime"), e.get("StopStatus", 0)
    if sec is not None and stat in (0, None):
        m = sec // 60
        return ("now", "進站中") if m <= 1 else ("soon" if m <= 5 else "", f"{m} 分")
    if e.get("NextBusTime"):
        return "mute", f"{STATUS.get(stat, '')} 下班 {str(e['NextBusTime'])[11:16]}".strip()
    return "mute", STATUS.get(stat, "—")


def headsign(name, stops):
    """「紅4 台南轉運站→奇美博物館」→ 奇美博物館；沒有箭頭就用最後一站。"""
    return re.sub(r"[((].*$", "", name.split("→")[-1]).strip() if "→" in name else (stops[-1][1] if stops else "")
