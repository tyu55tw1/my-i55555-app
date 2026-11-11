# -*- coding: utf-8 -*-
"""生活小幫手頁面:🗑️ 垃圾車、🚱 停水停電、🚗 國道路況、🍱 今天吃什麼、⛽ 加油站・充電站、📒 記帳、📅 繳費提醒。
資料抓取在 daily.py;設定和記帳資料都存在瀏覽器(U.pref / U.remember)。"""
from __future__ import annotations

import os
import random
import re
from datetime import date, datetime, timedelta
from urllib.parse import quote

import pandas as pd
import streamlit as st
from streamlit.components.v1 import html as components_html

import core as K
import daily as D
import life as L
import ui as U
import wheel as W
from ui import _esc, hero

WD = D.WD
# 各縣市的鄉鎮市區(停水停電選地區用,不用打字)
TOWNS = {k: v.split() for k, v in {
    "臺北市": "中正區 大同區 中山區 松山區 大安區 萬華區 信義區 士林區 北投區 內湖區 南港區 文山區",
    "新北市": "板橋區 三重區 中和區 永和區 新莊區 新店區 樹林區 鶯歌區 三峽區 淡水區 汐止區 瑞芳區 土城區 蘆洲區 五股區 泰山區 林口區 "
              "深坑區 石碇區 坪林區 三芝區 石門區 八里區 平溪區 雙溪區 貢寮區 金山區 萬里區 烏來區",
    "基隆市": "仁愛區 信義區 中正區 中山區 安樂區 暖暖區 七堵區",
    "桃園市": "桃園區 中壢區 大溪區 楊梅區 蘆竹區 大園區 龜山區 八德區 龍潭區 平鎮區 新屋區 觀音區 復興區",
    "新竹市": "東區 北區 香山區",
    "新竹縣": "竹北市 竹東鎮 新埔鎮 關西鎮 湖口鄉 新豐鄉 芎林鄉 橫山鄉 北埔鄉 寶山鄉 峨眉鄉 尖石鄉 五峰鄉",
    "苗栗縣": "苗栗市 頭份市 苑裡鎮 通霄鎮 竹南鎮 後龍鎮 卓蘭鎮 大湖鄉 公館鄉 銅鑼鄉 南庄鄉 頭屋鄉 三義鄉 西湖鄉 造橋鄉 三灣鄉 獅潭鄉 泰安鄉",
    "臺中市": "中區 東區 南區 西區 北區 西屯區 南屯區 北屯區 豐原區 東勢區 大甲區 清水區 沙鹿區 梧棲區 后里區 神岡區 潭子區 大雅區 "
              "新社區 石岡區 外埔區 大安區 烏日區 大肚區 龍井區 霧峰區 太平區 大里區 和平區",
    "彰化縣": "彰化市 員林市 鹿港鎮 和美鎮 北斗鎮 溪湖鎮 田中鎮 二林鎮 線西鄉 伸港鄉 福興鄉 秀水鄉 花壇鄉 芬園鄉 大村鄉 埔鹽鄉 埔心鄉 "
              "永靖鄉 社頭鄉 二水鄉 田尾鄉 埤頭鄉 芳苑鄉 大城鄉 竹塘鄉 溪州鄉",
    "南投縣": "南投市 埔里鎮 草屯鎮 竹山鎮 集集鎮 名間鄉 鹿谷鄉 中寮鄉 魚池鄉 國姓鄉 水里鄉 信義鄉 仁愛鄉",
    "雲林縣": "斗六市 斗南鎮 虎尾鎮 西螺鎮 土庫鎮 北港鎮 古坑鄉 大埤鄉 莿桐鄉 林內鄉 二崙鄉 崙背鄉 麥寮鄉 東勢鄉 褒忠鄉 臺西鄉 元長鄉 "
              "四湖鄉 口湖鄉 水林鄉",
    "嘉義市": "東區 西區",
    "嘉義縣": "太保市 朴子市 布袋鎮 大林鎮 民雄鄉 溪口鄉 新港鄉 六腳鄉 東石鄉 義竹鄉 鹿草鄉 水上鄉 中埔鄉 竹崎鄉 梅山鄉 番路鄉 大埔鄉 阿里山鄉",
    "臺南市": "中西區 東區 南區 北區 安平區 安南區 永康區 歸仁區 新化區 左鎮區 玉井區 楠西區 南化區 仁德區 關廟區 龍崎區 官田區 麻豆區 "
              "佳里區 西港區 七股區 將軍區 學甲區 北門區 新營區 後壁區 白河區 東山區 六甲區 下營區 柳營區 鹽水區 善化區 大內區 山上區 "
              "新市區 安定區",
    "高雄市": "楠梓區 左營區 鼓山區 三民區 鹽埕區 前金區 新興區 苓雅區 前鎮區 旗津區 小港區 鳳山區 大寮區 鳥松區 林園區 仁武區 大樹區 "
              "大社區 岡山區 路竹區 橋頭區 梓官區 彌陀區 永安區 燕巢區 田寮區 阿蓮區 茄萣區 湖內區 旗山區 美濃區 內門區 杉林區 甲仙區 "
              "六龜區 茂林區 桃源區 那瑪夏區",
    "屏東縣": "屏東市 潮州鎮 東港鎮 恆春鎮 萬丹鄉 長治鄉 麟洛鄉 九如鄉 里港鄉 鹽埔鄉 高樹鄉 萬巒鄉 內埔鄉 竹田鄉 新埤鄉 枋寮鄉 新園鄉 "
              "崁頂鄉 林邊鄉 南州鄉 佳冬鄉 琉球鄉 車城鄉 滿州鄉 枋山鄉 三地門鄉 霧臺鄉 瑪家鄉 泰武鄉 來義鄉 春日鄉 獅子鄉 牡丹鄉",
    "宜蘭縣": "宜蘭市 羅東鎮 蘇澳鎮 頭城鎮 礁溪鄉 壯圍鄉 員山鄉 冬山鄉 五結鄉 三星鄉 大同鄉 南澳鄉",
    "花蓮縣": "花蓮市 鳳林鎮 玉里鎮 新城鄉 吉安鄉 壽豐鄉 光復鄉 豐濱鄉 瑞穗鄉 富里鄉 秀林鄉 萬榮鄉 卓溪鄉",
    "臺東縣": "臺東市 成功鎮 關山鎮 卑南鄉 大武鄉 太麻里鄉 東河鄉 長濱鄉 鹿野鄉 池上鄉 綠島鄉 延平鄉 海端鄉 達仁鄉 金峰鄉 蘭嶼鄉",
    "澎湖縣": "馬公市 湖西鄉 白沙鄉 西嶼鄉 望安鄉 七美鄉",
    "金門縣": "金城鎮 金湖鎮 金沙鎮 金寧鄉 烈嶼鄉 烏坵鄉",
    "連江縣": "南竿鄉 北竿鄉 莒光鄉 東引鄉",
}.items()}
LOADED_AT = __import__("time").time()   # app.py 用來判斷檔案更新後要不要重新載入

# ── 快取包裝 ──
garbage_c = st.cache_data(ttl=86400, show_spinner="下載垃圾車清運點(每天第一次約 10 秒)…")(D.fetch_garbage)
trucks_c = st.cache_data(ttl=60, show_spinner=False)(D.fetch_trucks)
power_c = st.cache_data(ttl=3600, show_spinner="讀取台電停電公告…")(D.fetch_power)
water_c = st.cache_data(ttl=600, show_spinner="讀取台水停水公告…")(D.fetch_water)
fw_static = st.cache_data(ttl=86400, show_spinner="讀取國道路段…")(D.fetch_freeway_static)
fw_live = st.cache_data(ttl=60, show_spinner="讀取即時路況…")(D.fetch_freeway_live)
geocode_c = st.cache_data(ttl=86400, show_spinner="查地址…")(D.geocode)
food_c = st.cache_data(ttl=86400, show_spinner="搜尋附近的店(OpenStreetMap,第一次約 10~30 秒)…")(D.fetch_food)
cpc_c = st.cache_data(ttl=86400, show_spinner="讀取中油加油站…")(D.fetch_cpc)
fuel_osm_c = st.cache_data(ttl=86400, show_spinner="搜尋其他加油站與充電站(OpenStreetMap,約 10~20 秒)…")(D.fetch_fuel_osm)
oil_c = st.cache_data(ttl=1800, show_spinner=False)(K.fetch_oil)
closures_c = st.cache_data(ttl=300, show_spinner=False)(L.fetch_closures)


def _md(d: date) -> str:
    return f"{d.month}/{d.day}({WD[d.weekday()]})"


def _when(d: date, today: date) -> str:
    n = (d - today).days
    return "今天" if n == 0 else "明天" if n == 1 else "後天" if n == 2 else _md(d)


def _gmap(name, lat, lon) -> str:
    return f"https://www.google.com/maps/search/?api=1&query={quote(str(name))}%20{lat:.6f},{lon:.6f}"


def _nav(lat, lon) -> str:
    return f"https://www.google.com/maps/dir/?api=1&destination={lat:.6f},{lon:.6f}"


HOME_CHIP = "🏠 家"


def home_road() -> str:
    """從「我家」的說明文字抓出路名,抓不到回傳 ""。
    說明有兩種:地圖查到的「🏠 我家(中華路, 甲頂里, 永康區, 臺南市, …)」、或「…台南市永康區中華路一段 100 號…」。"""
    home = U.pref("home_loc")
    s = str(home[2]) if home and len(home) > 2 else ""
    for part in re.split(r"[,，()（）\s]+", s):
        part = re.sub(r"^[一-鿿]{2,3}?[市縣](?=.)", "", part)
        part = re.sub(r"^[一-鿿]{1,3}?[區鄉鎮市](?=.)", "", part)
        m = re.match(r"([一-鿿]{1,8}?(?:路|街|大道)(?:[一二三四五六七八九十]段)?)", part)
        if m:
            return m.group(1)
    return ""


def where(key: str) -> tuple[float, float, str] | None:
    """選位置:輸入的地址 > 定位 > 存的「我家」。回傳 (lat, lon, 說明)。"""
    home = U.pref("home_loc")
    c1, c2 = st.columns([1, 2], vertical_alignment="bottom")
    with c1:
        pos = U.geolocate(f"geo_{key}", "📍 用我的位置")
    q = U.chip_text("或選地址、地標", f"addr_{key}", recent_field="addr", record=False, container=c2,
                    top=[(HOME_CHIP, HOME_CHIP)] if home else (), empty_label="✖ 不填(用定位或我家)",
                    placeholder="例如:台南市永康區中華路、台南火車站", text_btn="⌨️ 打地址或地標")
    loc = None
    if q == HOME_CHIP and home:
        loc = tuple(home)
    elif q:
        g = U.quiet(geocode_c, q)
        if g:
            loc = g
            U.recent_add("addr", q)
        else:
            st.caption("⚠️ 找不到這個地址,換個寫法試試(例如加上縣市、改用路名或地標)")
    if loc is None and pos:
        loc = (pos[0], pos[1], "目前位置")
    if loc is None and home:
        loc = tuple(home)
    if loc:
        a, b = st.columns([4, 1], vertical_alignment="center")
        a.caption(f"📍 {_esc(loc[2][:70])}")
        if not str(loc[2]).startswith("🏠") and b.button("🏠 設為我家", key=f"home_{key}", help="之後不用定位,打開就查這裡"):
            U.remember("home_loc", [loc[0], loc[1], "🏠 我家(" + str(loc[2])[:40] + ")"])
            st.rerun()
    else:
        st.info("按「📍 用我的位置」或輸入地址。按「🏠 設為我家」後,之後打開就直接查。")
    return loc


def _map(rows, me=None, zoom=15, height=300):
    pts = [{"lat": r["lat"], "lon": r["lon"], "color": r.get("color", "#d9441a"), "size": 14} for r in rows]
    if me:
        pts.append({"lat": me[0], "lon": me[1], "color": "#1f6feb", "size": 30})
    if pts:
        st.map(pd.DataFrame(pts), color="color", size="size", zoom=zoom, height=height)


# ════════════════════════════════════════════════════════════════════
#  🗑️ 垃圾車
# ════════════════════════════════════════════════════════════════════
GARBAGE_CITIES = ["臺南市", "臺北市", "新北市", "臺中市"]


def stop_days(city) -> set:
    """颱風等停班日 → 垃圾車停收的日子(抓不到公告就當沒有)。"""
    got = U.safe(closures_c) if city else None
    return D.garbage_stop_days(city, got[0], K.tw_now().date()) if got else set()


def garbage_next_text(p, now, city=None) -> tuple[str, str]:
    """→ (下一次的文字, 今天收不收的徽章)。city 有給就會參考停班公告(颱風天停收)。"""
    today = now.date()
    stop = stop_days(city or p.get("city") or U.pref("garbage_city", "臺南市"))
    nv = D.next_visit(p, now, stop)
    when = f"{_when(nv[0], today)} {nv[1]}" if nv else "—"
    wd = today.weekday()
    g_today = wd in set(p.get("garbage") or range(7))
    r_today = wd in set(p.get("recycle") or [])
    if today in stop and g_today:
        badge = "<b style='color:#d63a3a'>⛔ 今天停收(停班)</b>"
    else:
        badge = ("<b style='color:#1f9d55'>今天有收</b>" + ("・♻️ 回收" if r_today else "")) if g_today else "<b style='color:#d63a3a'>今天不收</b>"
    if today + timedelta(days=1) in stop and (today + timedelta(days=1)).weekday() in set(p.get("garbage") or range(7)):
        badge += "・<b style='color:#d63a3a'>明天停收</b>"
    return when, badge


def _gcard(p, now, dist=None, city=None):
    when, badge = garbage_next_text(p, now, city)
    food = f"・🍲 廚餘 {D.days_text(p['food'])}" if p.get("food") else ""
    d = f"{dist * 1000:.0f} 公尺・" if dist is not None else ""
    memo = f"・{_esc(p['memo'])}" if p.get("memo") else ""
    return (f"<div class='card'><div class='ct'>🕒 {p['time'] or '—'}　{_esc(p['name'])}</div>"
            f"<div class='cs'>{d}{_esc(p['area'])} {_esc(p.get('village', ''))}・路線 {_esc(p['route'])}{memo}</div>"
            f"<div class='cs'>下一次:<b>{when}</b>・{badge}</div>"
            f"<div class='cs'>🗑️ 垃圾 {D.days_text(p['garbage'])}・♻️ 回收 {D.days_text(p['recycle'])}{food}</div></div>")


def page_garbage():
    hero("🗑️", "垃圾車", "附近清運點幾點來・今天收不收・新北／台中看車子現在在哪")
    now = K.tw_now()
    fav = U.pref("garbage_fav")
    if fav:
        st.markdown("**⭐ 我的清運點**")
        st.markdown(_gcard(fav, now), unsafe_allow_html=True)
        if st.button("移除我的清運點", key="gfav_rm"):
            U.remember("garbage_fav", None)
            st.rerun()
    saved = U.pref("garbage_city", "臺南市")
    city = st.segmented_control("縣市", GARBAGE_CITIES, default=saved if saved in GARBAGE_CITIES else "臺南市",
                                key=f"g_city_{U.rev()}") or saved
    U.remember("garbage_city", city)
    stop = stop_days(city)
    if now.date() in stop:
        st.warning(f"⛔ {city}今天停止上班(人事總處公告),垃圾車通常停收,恢復收運以環保局公告為準。")
    elif now.date() + timedelta(days=1) in stop:
        st.warning(f"⛔ {city}明天停止上班,垃圾車明天通常停收。")
    loc = where("garbage")
    if city in D.GARBAGE_SRC:
        radius = st.select_slider("找多遠的清運點", [200, 300, 500, 800, 1200], 500, format_func=lambda m: f"{m} 公尺")
        if loc:
            pts = U.safe(garbage_c, city)
            if pts:
                near = D.near_points(pts, loc[0], loc[1], radius / 1000, limit=40)
                if not near:
                    st.info(f"{radius} 公尺內沒有{city}的清運點。確認縣市選對了,或把距離放大。")
                else:
                    st.caption(f"附近 {len(near)} 個清運點,依距離排序。" + ("台北市週日、週三停收。" if city == "臺北市" else ""))
                    _map([{**p, "color": "#d9441a"} for p in near], loc, zoom=16)
                    for i, p in enumerate(near):
                        a, b = st.columns([6, 1], vertical_alignment="center")
                        a.markdown(_gcard(p, now, p["dist"], city), unsafe_allow_html=True)
                        if b.button("⭐", key=f"gfav_{i}", help="設成我的清運點(首頁會顯示下一次幾點來)"):
                            U.remember("garbage_fav", {k: p[k] for k in ("name", "area", "village", "route", "time", "garbage",
                                                                         "recycle", "food", "memo", "lat", "lon")} | {"city": city})
                            st.rerun()
    else:
        st.caption("台中市沒有公開清運點時刻表,只能看垃圾車現在的位置。")
    if city in D.TRUCK_SRC:
        st.markdown("##### 🚛 現在在路上的垃圾車")
        trucks = U.safe(trucks_c, city) or []
        nn = now.replace(tzinfo=None)
        fresh = [t for t in trucks if nn - t["time"] <= timedelta(minutes=30)]
        if loc:
            fresh = sorted(({**t, "dist": L.haversine(loc[0], loc[1], t["lat"], t["lon"])} for t in fresh), key=lambda t: t["dist"])
            fresh = [t for t in fresh if t["dist"] <= 3]
        if not fresh:
            st.caption("附近 3 公里內目前沒有出勤中的垃圾車(收運時間外就不會有)。" if loc else "目前沒有出勤中的垃圾車。")
        else:
            _map([{**t, "color": "#1f9d55"} for t in fresh[:60]], loc, zoom=14)
            for t in fresh[:15]:
                d = f"{t['dist']:.1f} 公里・" if "dist" in t else ""
                st.markdown(f"<div class='card'><div class='ct'>🚛 {_esc(t['car'])}</div><div class='cs'>{d}{_esc(t['where'])}"
                            f"・{t['time']:%H:%M} 回報</div></div>", unsafe_allow_html=True)
    st.caption("資料來源:臺南市政府、臺北市政府、新北市政府、臺中市政府資料開放平台。時刻為表定時間,實際以現場為準。")


# ════════════════════════════════════════════════════════════════════
#  🚱 停水・停電
# ════════════════════════════════════════════════════════════════════
def outage_args():
    """首頁用:我設定的地區(要在主執行緒讀設定,背景執行緒讀不到)。"""
    return U.pref("out_county"), U.pref("out_district", ""), U.pref("out_kw", "")


def outage_for(today: date, county, district="", kw="", days: int = 2):
    """這個地區今天起幾天內的停電、停水。回傳 (停電, 停水) 或 None(沒設定地區)。"""
    if not county:
        return None
    pw = U.quiet(power_c, today) or []
    wt = U.quiet(water_c) or []
    end = today + timedelta(days=days)
    p = [g for g in D.power_for(pw, county, district, kw, now=K.tw_now()) if g["date"] <= end]
    w = [x for x in D.water_for(wt, county, district, kw, now=datetime.combine(today, datetime.min.time()))
         if x["start"] and x["start"].date() <= end]
    return p, w


def page_outage():
    hero("🚱", "停水・停電", "台電計畫性停電・台灣自來水停水公告(每天更新)")
    today = K.tw_now().date()
    c1, c2, c3 = st.columns([1.2, 1, 1.4])
    saved = U.pref("out_county", "臺南市")
    county = U.pick("縣市", D.COUNTIES, index=D.COUNTIES.index(saved) if saved in D.COUNTIES else 13, key=f"out_c_{U.rev()}", container=c1)
    towns = [""] + TOWNS.get(county, [])
    sd = U.pref("out_district", "")
    sd = sd if sd in towns else next((t for t in towns if t and sd and D.tw(t).startswith(D.tw(sd))), "")
    district = U.pick("鄉鎮市區", towns, index=towns.index(sd), key=f"out_d_{county}_{U.rev()}", container=c2,
                      format_func=lambda t: t or "全部(整個縣市)")
    road = home_road()
    kw = U.chip_text("路名或里名(可空白)", f"out_k_{U.rev()}", value=U.pref("out_kw", ""), container=c3, recent_field="out_kw",
                     top=[(f"🏠 家附近:{road}", road)] if road else (), empty_label="✖ 不限路名",
                     placeholder="例如:中華路", text_btn="⌨️ 打路名或里名")
    for k, v in (("out_county", county), ("out_district", district), ("out_kw", kw)):
        U.remember(k, v)
    st.caption("設定好之後,首頁會在你這區有停水、停電時提醒你(今天起兩天內)。")
    t1, t2 = st.tabs(["⚡ 停電", "💧 停水"])
    with t1:
        pw = U.safe(power_c, today)
        if pw is not None:
            rows = D.power_for(pw, county, district, kw, now=K.tw_now())
            if not rows:
                st.success(f"✅ {county}{district}{(' ' + kw) if kw else ''}:目前沒有計畫性停電公告")
            for g in rows[:80]:
                hot = (g["date"] - today).days <= 1
                st.markdown(f"<div class='alert {'amber' if hot else ''}'><span>⚡</span><div><b>{_when(g['date'], today)} "
                            f"{g['start']}~{g['end']}</b>・{_esc(g['work'])}<br><span class='cs'>{_esc('、'.join(g['areas'])[:300])}</span>"
                            f"<br><span class='cs' style='opacity:.6'>{_esc(g['office'])}・查詢電話 1911</span></div></div>",
                            unsafe_allow_html=True)
            if len(rows) > 80:
                st.caption(f"只列前 80 筆(共 {len(rows)} 筆),填上鄉鎮市區或路名可以縮小範圍。")
    with t2:
        if D.tw(county) == "台北市":
            st.info("臺北市(和新北市部分地區)的自來水是「臺北自來水事業處」供水,停水公告請看北水處網站。")
            st.link_button("北水處停水公告", "https://webs.water.gov.taipei/wateroff/")
        wt = U.safe(water_c)
        if wt is not None:
            rows = D.water_for(wt, county, district, kw, now=datetime.combine(today, datetime.min.time()))
            if not rows:
                st.success(f"✅ {county}{district}:目前沒有台水停水公告")
            for w in rows:
                t = f"{w['start']:%m/%d %H:%M}~{w['end']:%m/%d %H:%M}" if w["start"] and w["end"] else "—"
                st.markdown(f"<div class='alert amber'><span>💧</span><div><b>{t}</b>・{_esc(w['type'])}・影響 {_esc(w['homes'])} 戶"
                            f"<br><span class='cs'>{_esc(w['area'])}</span>"
                            + (f"<br><span class='cs'>降壓:{_esc(w['low'])}</span>" if w["low"] else "")
                            + f"<br><span class='cs' style='opacity:.6'>原因:{_esc(w['reason'])}・{_esc(w['office'])} ☎ {_esc(w['tel'])}</span></div></div>",
                            unsafe_allow_html=True)
    st.caption("資料來源:台灣電力公司、台灣自來水公司開放資料。")


# ════════════════════════════════════════════════════════════════════
#  🚗 國道路況
# ════════════════════════════════════════════════════════════════════
def _road_order(r):
    import re
    m = re.search(r"\d+", r)
    return (not r.startswith("國道"), int(m.group()) if m else 99, r)


def page_freeway():
    hero("🚗", "國道路況", "這段路現在開多久・哪裡塞・事故施工(高公局 1968,每分鐘更新)")
    sec = U.safe(fw_static)
    if not sec:
        return
    live, events = U.quiet(fw_live) or ({}, [])
    roads = sorted({s["road"] for s in sec.values()}, key=_road_order)
    c1, c2 = st.columns(2)
    pr = U.pref("fw_road", "國道1號")
    road = U.pick("國道", roads, index=roads.index(pr) if pr in roads else 0, key=f"fw_r_{U.rev()}", container=c1)
    dirs = sorted({s["dir"] for s in sec.values() if s["road"] == road}, key="SNEW".find)
    pd_ = U.pref("fw_dir", "N")
    d = U.seg("方向", dirs, index=dirs.index(pd_) if pd_ in dirs else 0, format_func=lambda x: D.DIR_NAME.get(x, x),
              key=f"fw_d_{road}_{U.rev()}", container=c2)
    segs = D.route_sections(sec, road, d)
    if not segs:
        st.info("這個方向沒有路段資料")
        return
    names = [segs[0]["start"]] + [s["end"] for s in segs]
    c3, c4 = st.columns(2)
    pf, pt = U.pref("fw_from"), U.pref("fw_to")
    i = U.pick("從", range(len(names) - 1), index=names.index(pf) if pf in names[:-1] else 0, container=c3,
               format_func=lambda k: names[k], key=f"fw_f_{road}_{d}_{U.rev()}")
    j = U.pick("到", range(i + 1, len(names)), format_func=lambda k: names[k], container=c4,
               index=(names.index(pt) - i - 1) if pt in names[i + 1:] else len(names) - i - 2, key=f"fw_t_{road}_{d}_{i}_{U.rev()}")
    for k, v in (("fw_road", road), ("fw_dir", d), ("fw_from", names[i]), ("fw_to", names[j])):
        U.remember(k, v)
    part = segs[i:j]
    tr = D.trip(part, live)
    a, b, c, e = st.columns(4)
    a.metric("現在開過去約", f"{tr['min']:.0f} 分" if tr["min"] < 90 else f"{tr['min'] / 60:.1f} 小時")
    b.metric("平均時速", f"{tr['speed']:.0f} km/h")
    c.metric("距離", f"{tr['km']:.0f} 公里")
    e.metric("慢的路段", f"{len(tr['slow'])} 段")
    lo, hi = min(min(s["km0"], s["km1"]) for s in part), max(max(s["km0"], s["km1"]) for s in part)
    dname = D.DIR_NAME.get(d, "")
    evs = [x for x in events if x["road"] == road and (not x["dir"] or dname in x["dir"] or "雙向" in x["dir"])
           and lo - 0.5 <= x["km0"] <= hi + 0.5]
    def ev_html(x):
        col = "red" if x["type"] == "1" or "事故" in x["title"] else "amber"
        return (f"<div class='alert {col}'><span>{'🚨' if col == 'red' else '🚧'}</span><div><b>{_esc(x['desc'] or x['title'])}</b>"
                f"<br><span class='cs'>{_esc(x['impact'])}・{x['time'][5:]}</span></div></div>")
    evs.sort(key=lambda x: (not (x["type"] == "1" or "事故" in x["title"]), x["km0"]))
    st.markdown("".join(ev_html(x) for x in evs[:4]), unsafe_allow_html=True)
    if len(evs) > 4:
        with st.expander(f"還有 {len(evs) - 4} 則施工、管制"):
            st.markdown("".join(ev_html(x) for x in evs[4:]), unsafe_allow_html=True)
    if not evs:
        st.caption("✅ 這段路目前沒有事故、施工通報")
    h = ""
    for s in part:
        lv = live.get(s["id"]) or {}
        v = lv.get("speed", -1)
        col = D.speed_color(v, s["limit"])
        w = max(4, min(100, v / max(s["limit"], 1) * 100)) if v >= 0 else 100
        h += (f"<div style='display:flex;align-items:center;gap:8px;margin:3px 0;font-size:.88rem'>"
              f"<span style='flex:0 0 46%;overflow:hidden;white-space:nowrap;text-overflow:ellipsis'>{_esc(s['start'])} → {_esc(s['end'])}</span>"
              f"<span style='flex:1;height:10px;border-radius:6px;background:var(--soft)'><i style='display:block;height:100%;width:{w:.0f}%;"
              f"border-radius:6px;background:{col}'></i></span><b style='flex:0 0 64px;text-align:right;color:{col}'>"
              f"{v if v >= 0 else '—'} km/h</b></div>")
    st.markdown("##### 各路段即時車速")
    st.markdown(h, unsafe_allow_html=True)
    st.caption("綠 順暢・黃 車多・橘 壅塞・紅 嚴重壅塞。行車時間以即時速度估算,沒有資料的路段用速限估。")
    if st.button("🔄 更新路況"):
        fw_live.clear()
        st.rerun()
    st.caption("資料來源:交通部高速公路局交通資料庫(1968)。")


# ════════════════════════════════════════════════════════════════════
#  🍱 今天吃什麼
# ════════════════════════════════════════════════════════════════════
def page_food():
    hero("🍱", "今天吃什麼", "找附近的店,轉盤幫你選(店家資料來自 OpenStreetMap,可能不齊)")
    loc = where("food")
    if not loc:
        return
    c1, c2 = st.columns(2)
    radii = [300, 500, 800, 1200, 2000, 5000, 8000]
    pr = U.pref("food_r", 800)
    radius = c1.select_slider("範圍", radii, pr if pr in radii else 800, format_func=lambda m: f"{m} 公尺" if m < 1000 else f"{m / 1000:g} 公里")
    U.remember("food_r", radius)
    n = c2.slider("轉盤放幾家", 4, 16, 10)
    kinds = st.pills("種類", list(D.FOOD_KIND), default=["restaurant", "fast_food", "cafe", "food_court"],
                     format_func=D.FOOD_KIND.get, selection_mode="multi")
    mine = [x.strip() for x in U.pref("food_mine", []) if str(x).strip()]
    with st.expander(f"⭐ 我常吃的店({len(mine)})— 自己加的店每次都會放上轉盤"):
        txt = st.text_area("每行一家", "\n".join(mine), height=120, placeholder="例如:\n巷口麵店\n阿嬤便當\n樓下早餐店",
                           key=f"food_mine_{U.rev()}")
        if st.button("💾 儲存", key="food_mine_save"):
            U.remember("food_mine", [x.strip()[:30] for x in txt.splitlines() if x.strip()][:40])
            st.session_state.pop("food_sig", None)
            st.rerun()
    block = set(U.pref("food_block", []))

    def nearby(r_):
        rows_ = food_c(round(loc[0], 3), round(loc[1], 3), r_)
        rows_ = [r for r in rows_ if r["kind"] in (kinds or list(D.FOOD_KIND)) and r["name"] not in block]
        seen = set()
        return [r for r in rows_ if not (r["name"] in seen or seen.add(r["name"]))]   # 同名分店只留最近的

    try:
        used, rows = radius, nearby(radius)
        for bigger in (2000, 5000, 8000):   # 附近登錄的店太少(郊區常見):自動放大範圍
            if len(rows) >= 8 or bigger <= used:
                continue
            used, rows = bigger, nearby(bigger)
    except Exception as e:  # noqa: BLE001
        st.warning(f"😵 {e}")
        rows, used = [], radius
    gsearch = f"https://www.google.com/maps/search/{quote('餐廳')}/@{loc[0]:.6f},{loc[1]:.6f},15z"
    if used > radius:
        st.info(f"附近 {radius} 公尺內登錄的店家太少,已自動放大到 {used / 1000:g} 公里。"
                "郊區在 OpenStreetMap 上的店家常常不齊,可以在上面「⭐ 我常吃的店」自己加。")
    mine_rows = [{"name": m, "kind": "mine", "dist": None, "lat": None, "lon": None, "cuisine": "", "hours": ""}
                 for m in mine if m not in block]
    pool_all = mine_rows + [r for r in rows if r["name"] not in set(mine)]
    if not pool_all:
        st.info("這附近找不到店家資料。可以在「⭐ 我常吃的店」自己加,或用 Google 地圖找。")
        st.link_button("🗺️ 用 Google 地圖找附近餐廳", gsearch)
        return
    sig = (round(loc[0], 3), round(loc[1], 3), radius, tuple(sorted(kinds or [])), n, tuple(mine))
    again = st.button("🔄 換一批店", key="food_new")
    if st.session_state.get("food_sig") != sig or again:
        st.session_state["food_sig"] = sig
        others = [r for r in pool_all if r["kind"] != "mine"]
        random.shuffle(others)
        st.session_state["food_pick"] = [r["name"] for r in (mine_rows + others)[:max(n, len(mine_rows))]]
    want = st.session_state.get("food_pick", [])
    by_name = {r["name"]: r for r in pool_all}
    picked = [by_name[x] for x in want if x in by_name]
    st.caption(f"找到 {len(rows)} 家" + (f"+ 我常吃的 {len(mine_rows)} 家" if mine_rows else "") +
               f",轉盤上放 {len(picked)} 家。點轉盤就會轉。")
    components_html(W.wheel_html([(r["name"], 1) for r in picked]), height=760, scrolling=True)
    st.link_button("🗺️ 用 Google 地圖找附近餐廳(店家比較齊)", gsearch)
    st.markdown("##### 轉盤上的店")
    for i, r in enumerate(picked):
        a, b = st.columns([6, 1], vertical_alignment="center")
        if r["kind"] == "mine":
            link = f"https://www.google.com/maps/search/{quote(r['name'])}/@{loc[0]:.6f},{loc[1]:.6f},15z"
            a.markdown(f"<div class='card'><div class='ct'>{_esc(r['name'])}</div><div class='cs'>⭐ 我常吃的　"
                       f"<a href='{link}' target='_blank'>🗺️ 地圖・評價</a></div></div>", unsafe_allow_html=True)
        else:
            extra = "・".join(x for x in (D.cuisine_zh(r["cuisine"]), D.hours_zh(r["hours"]) and "🕒 " + D.hours_zh(r["hours"])) if x)
            dist = f"{r['dist'] * 1000:.0f} 公尺" if r["dist"] < 1 else f"{r['dist']:.1f} 公里"
            a.markdown(f"<div class='card'><div class='ct'>{_esc(r['name'])}</div><div class='cs'>{D.FOOD_KIND.get(r['kind'], '')}"
                       f"・{dist}{('・' + _esc(extra)) if extra else ''}　"
                       f"<a href='{_gmap(r['name'], r['lat'], r['lon'])}' target='_blank'>🗺️ 地圖・評價</a></div></div>",
                       unsafe_allow_html=True)
        if b.button("🚫", key=f"food_blk_{i}", help="不想吃這家,以後不放上轉盤"):
            U.remember("food_block", sorted(block | {r["name"]}))
            st.session_state.pop("food_sig", None)
            st.rerun()
    if block:
        with st.expander(f"🚫 不想吃的店({len(block)})"):
            keep = st.multiselect("取消勾選就會放回轉盤", sorted(block), default=sorted(block), key=f"food_bl_{len(block)}")
            if set(keep) != block:
                U.remember("food_block", sorted(keep))
                st.rerun()
    st.caption("店家資料:© OpenStreetMap 貢獻者。營業時間不一定準,出發前可以點「地圖・評價」確認。")


# ════════════════════════════════════════════════════════════════════
#  ⛽ 加油站・充電站
# ════════════════════════════════════════════════════════════════════
def page_fuel():
    hero("⛽", "加油站・充電站", "離我最近的中油(營業時間、自助)・其他品牌和電動車充電站")
    o = U.quiet(oil_c)
    if o:
        st.markdown("".join(f"<span class='chip'>{n.split()[0]} {p:.1f}</span>" for n, p in zip(K.OIL_NAMES, o["prices"]))
                    + f"<span class='cs' style='opacity:.7'>　中油牌價 {o['date']}</span>", unsafe_allow_html=True)
    loc = where("fuel")
    if not loc:
        return
    radius = st.select_slider("範圍", [1000, 2000, 3000, 5000, 8000], 3000, format_func=lambda m: f"{m / 1000:g} 公里")
    mode = st.segmented_control("要找", ["⛽ 加油站", "🔌 充電站"], default="⛽ 加油站", key="fuel_mode") or "⛽ 加油站"
    if mode == "⛽ 加油站":
        cpc = U.safe(cpc_c) or []
        rows = []
        for s in cpc:
            if abs(s["lat"] - loc[0]) < 0.1 and abs(s["lon"] - loc[1]) < 0.1:
                dist = L.haversine(loc[0], loc[1], s["lat"], s["lon"])
                if dist <= radius / 1000:
                    rows.append({**s, "dist": dist})
        if st.toggle("也找台塑、全國等其他品牌(OpenStreetMap,較慢)", key="fuel_osm"):
            for x in U.quiet(fuel_osm_c, round(loc[0], 3), round(loc[1], 3), radius) or []:
                tg = x["tags"]
                if tg.get("amenity") != "fuel":
                    continue
                brand = tg.get("brand") or tg.get("operator") or ""
                if "中油" in brand or "CPC" in brand.upper():
                    continue
                rows.append({"name": x["name"] or brand or "加油站", "brand": brand, "lat": x["lat"], "lon": x["lon"],
                             "addr": tg.get("addr:full") or tg.get("addr:street", ""), "tel": tg.get("phone", ""),
                             "hours": tg.get("opening_hours", ""), "fuels": [], "self": tg.get("self_service") == "yes",
                             "open": True, "kind": "", "dist": x["dist"]})
        rows.sort(key=lambda r: r["dist"])
        if not rows:
            st.info("範圍內沒有找到加油站,把範圍放大試試。")
        else:
            _map([{**r, "color": "#1f9d55" if r["brand"] == "中油" else "#d6a400"} for r in rows[:60]], loc, zoom=13)
            for r in rows[:25]:
                tags = "・".join(x for x in ("/".join(r["fuels"]), "💳 自助" if r["self"] else "", r["hours"] and f"🕒 {r['hours']}") if x)
                closed = "" if r["open"] else "・<b style='color:#d63a3a'>暫停營業</b>"
                st.markdown(f"<div class='card'><div class='ct'>⛽ {_esc(r['name'])}</div><div class='cs'>{r['dist']:.1f} 公里{closed}"
                            f"{('・' + _esc(tags)) if tags else ''}</div><div class='cs'>📍 {_esc(r['addr'])}　"
                            f"<a href='{_nav(r['lat'], r['lon'])}' target='_blank'>🧭 導航</a></div></div>", unsafe_allow_html=True)
    else:
        try:
            rows = [x for x in fuel_osm_c(round(loc[0], 3), round(loc[1], 3), radius)
                    if x["tags"].get("amenity") == "charging_station"]
        except Exception as e:  # noqa: BLE001
            st.warning(f"😵 {e}")
            rows = None
        if rows is None:
            pass
        elif not rows:
            st.info("範圍內沒有找到充電站(OpenStreetMap 資料可能不齊,也可以用 Plugshare 或各家充電 app 查)。")
        else:
            swap = lambda r: "gogoro" in (r["name"] + str(r["tags"].get("brand", "")) + str(r["tags"].get("operator", ""))).lower()  # noqa: E731
            kind = st.radio("類型", ["🚗 汽車充電", "🛵 機車換電(Gogoro)"], horizontal=True, key="ev_kind")
            rows = [r for r in rows if swap(r) == kind.startswith("🛵")]
            _map([{**r, "color": "#1f6feb"} for r in rows[:60]], loc, zoom=13)
            if not rows:
                st.info("範圍內沒有找到這一類,把範圍放大或換另一類看看。")
            for r in rows[:25]:
                tg = r["tags"]
                sockets = "、".join(k.split(":")[1].upper() for k in tg if k.startswith("socket:") and k.count(":") == 1)
                op = tg.get("operator") or tg.get("brand") or ""
                info = "・".join(x for x in ("" if op == r["name"] else op, sockets and f"🔌 {sockets}",
                                             not swap(r) and tg.get("capacity") and f"{tg['capacity']} 個車位",
                                             D.hours_zh(tg.get("opening_hours", ""))) if x)
                icon = "🛵" if swap(r) else "🔌"
                st.markdown(f"<div class='card'><div class='ct'>{icon} {_esc(r['name'] or '充電站')}</div><div class='cs'>{r['dist']:.1f} 公里"
                            f"{('・' + _esc(info)) if info else ''}　<a href='{_nav(r['lat'], r['lon'])}' target='_blank'>🧭 導航</a>"
                            f"</div></div>", unsafe_allow_html=True)
    st.caption("資料來源:台灣中油開放資料、© OpenStreetMap 貢獻者。")


# ════════════════════════════════════════════════════════════════════
#  📒 記帳
# ════════════════════════════════════════════════════════════════════
def ledger() -> list[dict]:
    return list(U.pref("ledger", []))


def month_total(rows, ym: str) -> float:
    return sum(float(x.get("amt") or 0) for x in rows if str(x.get("d", "")).startswith(ym))


def _add_entry(e: dict):
    rows = ledger()
    if e.get("inv") and any(x.get("inv") == e["inv"] for x in rows):
        return False
    rows.append(e)
    rows.sort(key=lambda x: x.get("d", ""))
    U.remember("ledger", rows)
    return True


LEDGER_AMOUNTS = [50, 80, 100, 120, 150, 200, 300, 500, 1000]
NOTE_CATS = {"早餐": "🍱 餐飲", "午餐": "🍱 餐飲", "晚餐": "🍱 餐飲", "宵夜": "🍱 餐飲", "飲料": "🍱 餐飲", "咖啡": "🍱 餐飲", "零食": "🍱 餐飲",
             "交通": "🚌 交通", "加油": "🚌 交通", "停車": "🚌 交通", "捷運公車": "🚌 交通", "計程車": "🚌 交通", "日用品": "🛒 日用",
             "超市": "🛒 日用", "全聯": "🛒 日用", "藥局": "💊 醫療", "看醫生": "💊 醫療", "電影": "🎮 娛樂", "衣服": "👕 服飾",
             "水電瓦斯": "💡 帳單", "電話費": "💡 帳單", "紅包禮金": "🎁 人情"}
NOTE_PRESETS = list(NOTE_CATS)
DUE_NAMES = ["驗車", "駕照到期", "護照到期", "身分證換發", "繳稅", "保險", "繳費", "房租", "信用卡", "電話費", "水電費", "停車月租",
             "健檢", "牙醫洗牙", "機車保養", "汽車保養", "寵物疫苗", "會員續約"]


SUB_PRESETS = [("Netflix", 390), ("Spotify", 149), ("YouTube Premium", 199), ("Disney+", 270), ("iCloud+ 50GB", 30),
               ("ChatGPT Plus", 650), ("手機月租", 499), ("健身房", 1000)]


def page_ledger():
    hero("📒", "記帳", "手打或掃發票・每月分類圓餅圖・訂閱固定支出(資料只存在這台裝置的瀏覽器)")
    today = K.tw_now().date()
    t1, t2, t3, t4 = st.tabs(["✍️ 記一筆", "📷 掃發票", "📊 每月統計", "🔁 訂閱"])
    with t1:
        ss = st.session_state
        if "led_msg" in ss:
            st.success(ss.pop("led_msg"))
        a, b = st.columns(2)
        d = a.date_input("日期", today, key="led_d")
        amt = U.amount_pick("金額", "led_amt", 0, 10_000_000, None, LEDGER_AMOUNTS, unit="元", container=b, placeholder="點一下輸入金額")
        if ss.get("_led_cat_next") in D.CATS:
            ss["led_cat"] = ss.pop("_led_cat_next")
        ss.setdefault("led_cat", D.CATS[0])
        cat = st.pills("類別", D.CATS, key="led_cat")

        def note_cat():   # 點「早餐」「加油」這類常用備註,類別也跟著換(下次重跑、類別方塊建立前才套用)
            c = NOTE_CATS.get(ss.get("led_note"))
            if c in D.CATS:
                ss["_led_cat_next"] = c

        note = U.chip_text("備註(可空白)", "led_note", NOTE_PRESETS, placeholder="例如:午餐便當", empty_label="✖ 不寫備註",
                           text_ph="例如:午餐便當", on_change=note_cat)
        if st.button("➕ 記下來", type="primary", key="led_add"):
            if not amt:
                st.warning("請輸入金額")
            else:
                _add_entry({"d": d.isoformat(), "amt": int(amt), "cat": cat or D.CATS[-1], "note": note.strip()})
                ss["led_msg"] = f"已記下 {cat or D.CATS[-1]} {amt:,} 元" + (f"({note})" if note else "")
                for k in ("led_amt", "led_note"):
                    ss.pop(k, None)
                st.rerun()
        rows = ledger()
        ym = today.strftime("%Y-%m")
        st.caption(f"這個月已經花 {month_total(rows, ym):,.0f} 元・今天 {sum(float(x['amt']) for x in rows if x['d'] == today.isoformat()):,.0f} 元")
    with t2:
        st.caption("拍電子發票(左邊那個 QR Code 要清楚),會自動讀出日期、金額、店家統編。也會自動放進「發票對獎」。")
        use_cam = st.toggle("用相機拍", key="led_cam")
        f = st.camera_input("拍發票") if use_cam else st.file_uploader("上傳發票照片", ["jpg", "jpeg", "png", "webp"], key="led_up")
        if f:
            texts = U.quiet(L.decode_qr_texts, f.getvalue()) or []
            found = [x for x in (D.parse_invoice_money(t) for t in texts) if x]
            if not found:
                st.warning("讀不到發票 QR Code。請拍近一點、對焦清楚,只拍左邊那個 QR Code 也可以。")
            for k, x in enumerate(found):
                with st.container(border=True):
                    st.markdown(f"**{x['inv']}**　{x['date'] or '—'}　**{x['amount']:,} 元**　賣方統編 {x['seller']}"
                                + (f"　品項:{_esc(x['item'])}" if x["item"] else ""))
                    cat = U.pick("類別", D.CATS, key=f"led_qc_{k}")
                    if st.button("➕ 加入記帳", key=f"led_qa_{k}", type="primary"):
                        ok = _add_entry({"d": (x["date"] or today).isoformat(), "amt": x["amount"], "cat": cat,
                                         "note": x["item"], "inv": x["inv"]})
                        st.success("已加入記帳") if ok else st.info("這張發票已經記過了")
    with t3:
        rows = ledger()
        months = sorted({x["d"][:7] for x in rows} | {today.strftime("%Y-%m")}, reverse=True)
        ym = U.pick("月份", months)
        mrows = [x for x in rows if x["d"].startswith(ym)]
        subs = list(U.pref("subs", []))
        fixed = D.month_sub_cost(subs)
        tot = sum(float(x["amt"]) for x in mrows)
        y, m = map(int, ym.split("-"))
        ndays = (today.day if (y, m) == (today.year, today.month) else (date(y + m // 12, m % 12 + 1, 1) - timedelta(days=1)).day)
        a, b, c = st.columns(3)
        a.metric("這個月花了", f"{tot:,.0f} 元", f"{len(mrows)} 筆", delta_color="off")
        b.metric("平均一天", f"{tot / max(ndays, 1):,.0f} 元")
        c.metric("訂閱固定支出", f"{fixed:,.0f} 元/月")
        if mrows:
            import altair as alt
            df = pd.DataFrame(mrows).groupby("cat", as_index=False)["amt"].sum().sort_values("amt", ascending=False)
            df.columns = ["類別", "金額"]
            ch = alt.Chart(df).mark_arc(innerRadius=55).encode(theta="金額:Q", color=alt.Color("類別:N", sort=list(df["類別"])),
                                                               tooltip=["類別", alt.Tooltip("金額:Q", format=",")])
            a, b = st.columns([1, 1])
            a.altair_chart(ch, use_container_width=True)
            b.dataframe(df.assign(比例=(df["金額"] / tot * 100).round(1).astype(str) + "%"), hide_index=True, use_container_width=True)
        st.markdown("##### 明細(可以直接改,刪除:勾選列再按垃圾桶)")
        edf = pd.DataFrame([{"日期": date.fromisoformat(x["d"]), "金額": int(x["amt"]), "類別": x.get("cat", ""),
                             "備註": x.get("note", ""), "發票": x.get("inv", "")} for x in mrows],
                           columns=["日期", "金額", "類別", "備註", "發票"])
        ed = st.data_editor(edf, num_rows="dynamic", hide_index=True, use_container_width=True, key=f"led_ed_{ym}",
                            column_config={"日期": st.column_config.DateColumn(format="MM/DD"),
                                           "金額": st.column_config.NumberColumn(min_value=0, step=1),
                                           "類別": st.column_config.SelectboxColumn(options=D.CATS)})
        if st.button("💾 儲存修改", key="led_save"):
            keep = [x for x in rows if not x["d"].startswith(ym)]
            for r in ed.to_dict("records"):
                if pd.isna(r.get("金額")) or pd.isna(r.get("日期")):
                    continue
                dd = r["日期"] if isinstance(r["日期"], date) else pd.to_datetime(r["日期"]).date()
                keep.append({"d": dd.isoformat(), "amt": int(r["金額"]), "cat": r.get("類別") or D.CATS[-1],
                             "note": "" if pd.isna(r.get("備註")) else str(r.get("備註") or ""),
                             **({"inv": str(r["發票"])} if r.get("發票") and not pd.isna(r.get("發票")) else {})})
            U.remember("ledger", sorted(keep, key=lambda x: x["d"]))
            st.success("已儲存")
            st.rerun()
        if rows:
            st.download_button("⬇️ 匯出全部記帳(CSV,可用 Excel 開)",
                               pd.DataFrame(rows).rename(columns={"d": "日期", "amt": "金額", "cat": "類別", "note": "備註", "inv": "發票"})
                               .to_csv(index=False).encode("utf-8-sig"), "記帳.csv", "text/csv")
    with t4:
        subs = list(U.pref("subs", []))
        a, b = st.columns(2)
        a.metric("每月固定", f"{D.month_sub_cost(subs):,.0f} 元")
        b.metric("一年下來", f"{D.month_sub_cost(subs) * 12:,.0f} 元")
        p = U.pick("快速加入", [None] + SUB_PRESETS, format_func=lambda x: "選常見的訂閱…" if x is None else f"{x[0]}({x[1]} 元/月)")
        if p and st.button("➕ 加入", key="sub_add"):
            U.remember("subs", subs + [{"name": p[0], "amt": p[1], "cycle": "每月", "day": today.day, "month": 1}])
            st.rerun()
        sdf = pd.DataFrame([{"名稱": s["name"], "金額": float(s.get("amt") or 0), "週期": s.get("cycle", "每月"),
                             "扣款日": int(s.get("day") or 1), "月份(年繳)": int(s.get("month") or 1)} for s in subs],
                           columns=["名稱", "金額", "週期", "扣款日", "月份(年繳)"])
        ed = st.data_editor(sdf, num_rows="dynamic", hide_index=True, use_container_width=True, key="sub_ed",
                            column_config={"週期": st.column_config.SelectboxColumn(options=["每月", "每年"]),
                                           "扣款日": st.column_config.NumberColumn(min_value=1, max_value=31, step=1),
                                           "月份(年繳)": st.column_config.NumberColumn(min_value=1, max_value=12, step=1),
                                           "金額": st.column_config.NumberColumn(min_value=0, step=1)})
        if st.button("💾 儲存訂閱", key="sub_save"):
            out = []
            for r in ed.to_dict("records"):
                if not r.get("名稱") or pd.isna(r.get("名稱")):
                    continue
                out.append({"name": str(r["名稱"]), "amt": 0 if pd.isna(r.get("金額")) else float(r["金額"]),
                            "cycle": r.get("週期") or "每月", "day": 1 if pd.isna(r.get("扣款日")) else int(r["扣款日"]),
                            "month": 1 if pd.isna(r.get("月份(年繳)")) else int(r["月份(年繳)"])})
            U.remember("subs", out)
            st.success("已儲存")
            st.rerun()
        st.caption("扣款日會出現在「📅 繳費提醒」裡。")


# ════════════════════════════════════════════════════════════════════
#  📅 繳費・到期提醒
# ════════════════════════════════════════════════════════════════════
def due_items(today: date, with_subs: bool = True) -> list[dict]:
    """所有提醒(含訂閱扣款),算好下一次日期、剩幾天,依日期排序。"""
    out = []
    for k, it in enumerate(U.pref("dues", []) or []):
        d = D.next_due(it, today)
        if d and it.get("paid") == d.isoformat():
            if it.get("kind") == "單次":
                continue
            d = D.next_due(it, d + timedelta(days=1))
        if d:
            out.append({**it, "due": d, "left": (d - today).days, "idx": k})
    if with_subs:
        for s in U.pref("subs", []) or []:
            it = {"name": f"🔁 {s['name']} 扣款 {float(s.get('amt') or 0):,.0f} 元", "kind": s.get("cycle", "每月"),
                  "day": s.get("day", 1), "month": s.get("month", 1), "before": 2}
            d = D.next_due(it, today)
            if d:
                out.append({**it, "due": d, "left": (d - today).days, "idx": None})
    return sorted(out, key=lambda x: x["due"])


def due_color(x) -> str:
    before = int(x.get("before") or 3)
    return "red" if x["left"] < 0 or x["left"] <= min(before, 3) else "amber" if x["left"] <= before else ""


def due_text(x) -> str:
    n = x["left"]
    return f"已過期 {-n} 天" if n < 0 else "就是今天" if n == 0 else f"還剩 {n} 天"


def page_dues():
    hero("📅", "繳費・到期提醒", "繳費、稅金、驗車、證件到期:首頁會顯示剩幾天,快到期變紅色")
    today = K.tw_now().date()
    dues = list(U.pref("dues", []))
    items = due_items(today, st.toggle("一起顯示訂閱扣款日", True, key="due_subs"))
    if not items:
        st.info("還沒有提醒。用下面「新增」加入,或從常見項目快速加入。")
    for x in items:
        c = due_color(x)
        a, b = st.columns([6, 1], vertical_alignment="center")
        a.markdown(f"<div class='alert {c}'><span>{'⏰' if c else '📅'}</span><div><b>{_esc(x['name'])}</b>・{due_text(x)}"
                   f"<br><span class='cs'>{_md(x['due'])}・{x['kind']}{('・' + _esc(x.get('note', ''))) if x.get('note') else ''}</span></div></div>",
                   unsafe_allow_html=True)
        if x["idx"] is not None and b.button("✅", key=f"due_paid_{x['idx']}", help="這期已經繳了/辦好了"):
            dues[x["idx"]] = {**dues[x["idx"]], "paid": x["due"].isoformat()}
            U.remember("dues", dues)
            st.rerun()
    st.divider()
    st.markdown("##### ➕ 新增提醒")
    p = U.pick("常見項目", [None] + D.DUE_PRESETS, format_func=lambda x: "選常見的…(也可以直接在下面自己填)" if x is None else f"{x[0]}:{x[5]}")
    if p and st.button("➕ 加入這個", key="due_preset"):
        U.remember("dues", dues + [{"name": p[0], "kind": p[1], "month": p[2] or 1, "day": p[3], "before": p[4], "note": p[5]}])
        st.rerun()
    with st.container(border=True):
        a, b = st.columns(2)
        name = U.chip_text("名稱", "due_name", DUE_NAMES, placeholder="例如:驗車、駕照到期、護照到期", container=a,
                           text_ph="例如:驗車、駕照到期")
        kind = b.radio("多久一次", ["單次", "每月", "每年"], horizontal=True, key="due_kind")
        c1, c2, c3 = st.columns(3)
        dd = c1.date_input("日期(單次/每年用這個日期)", today + timedelta(days=30), key="due_dd")
        day = U.amount_pick("每月幾號(每月用)", "due_day", 1, 31, 15, [1, 5, 10, 15, 20, 25, 28, 31], container=c2,
                            preset_label=lambda x: f"{x} 號")
        before = U.amount_pick("提早幾天提醒", "due_before", 0, 60, 7, [0, 1, 2, 3, 5, 7, 10, 14, 30], unit="天", container=c3)
        note = U.chip_text("備註(可空白)", "due_note", placeholder="例如:記得帶行照", empty_label="✖ 不寫備註")
        if st.button("➕ 新增", type="primary", key="due_add"):
            if not name.strip():
                st.warning("請填名稱")
            else:
                it = {"name": name.strip(), "kind": kind, "before": int(before), "note": note.strip()}
                it |= {"date": dd.isoformat()} if kind == "單次" else {"day": int(day)} if kind == "每月" else {"month": dd.month, "day": dd.day}
                U.remember("dues", dues + [it])
                for k in ("due_name", "due_note", "due_day", "due_before", "due_dd"):
                    st.session_state.pop(k, None)
                st.rerun()
    if dues:
        with st.expander("✏️ 修改 / 刪除(改完按儲存)"):
            st.caption("每月:填「日」。每年:填「月」和「日」。單次:填「單次日期」。刪除:勾選最左邊再按垃圾桶。")
            df = pd.DataFrame([{"名稱": it.get("name", ""), "多久一次": it.get("kind", "單次"), "月": int(it.get("month") or 1),
                                "日": int(it.get("day") or 1),
                                "單次日期": date.fromisoformat(it["date"]) if it.get("date") else None,
                                "提早幾天": int(it.get("before") or 3), "備註": it.get("note", "")} for it in dues])
            ed = st.data_editor(df, num_rows="dynamic", hide_index=True, use_container_width=True, key="due_ed",
                                column_config={"多久一次": st.column_config.SelectboxColumn(options=["單次", "每月", "每年"]),
                                               "月": st.column_config.NumberColumn(min_value=1, max_value=12, step=1),
                                               "日": st.column_config.NumberColumn(min_value=1, max_value=31, step=1),
                                               "單次日期": st.column_config.DateColumn(format="YYYY/MM/DD"),
                                               "提早幾天": st.column_config.NumberColumn(min_value=0, max_value=60, step=1)})
            if st.button("💾 儲存修改", key="due_save"):
                def num(v, d):
                    return d if v is None or pd.isna(v) else int(v)
                out = []
                for r in ed.to_dict("records"):
                    if not r.get("名稱") or pd.isna(r.get("名稱")):
                        continue
                    it = {"name": str(r["名稱"]), "kind": r.get("多久一次") or "單次", "month": num(r.get("月"), 1),
                          "day": num(r.get("日"), 1), "before": num(r.get("提早幾天"), 3),
                          "note": "" if pd.isna(r.get("備註")) else str(r.get("備註") or "")}
                    sd = r.get("單次日期")
                    if sd is not None and not pd.isna(sd):
                        it["date"] = (sd if isinstance(sd, date) else pd.to_datetime(sd).date()).isoformat()
                    if it["kind"] == "單次" and "date" not in it:
                        continue
                    old = next((o for o in dues if o.get("name") == it["name"]), {})
                    if old.get("paid"):
                        it["paid"] = old["paid"]
                    out.append(it)
                U.remember("dues", out)
                st.success("已儲存")
                st.rerun()
    st.caption("提醒只會在打開網頁時看到(網頁沒辦法主動推播到手機)。")


# ════════════════════════════════════════════════════════════════════
#  📚 漫畫:書櫃(static/comic.html)+ 追更清單
# ════════════════════════════════════════════════════════════════════
feed_c = st.cache_data(ttl=1800, show_spinner=False)(D.fetch_feed)
READER_HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "comic.html")


def comic_news(follows) -> list[tuple[dict, dict]]:
    """首頁用:有新話的作品 [(追蹤項目, 最新一話)]。"""
    out = []
    for f in follows:
        feed = U.quiet(feed_c, f["rss"])
        if feed and feed["items"] and feed["items"][0]["link"] != f.get("seen"):
            out.append((f, feed["items"][0]))
    return out


def page_comics():
    hero("📚", "漫畫", "線上看正版漫畫・WEBTOON 追更提醒・手機漫畫書櫃")
    st.markdown("##### 🌐 線上看漫畫(正版、免費)")
    sites = [("💚 LINE WEBTOON", "https://www.webtoons.com/zh-hant/", "中文條漫,也有咒術迴戰、鏈鋸人等日漫官方中文版"),
             ("🔴 MANGA Plus", "https://mangaplus.shueisha.co.jp/updates", "集英社官方,JUMP 作品最新話免費(英文等外文)"),
             ("🟠 少年 JUMP+", "https://shonenjumpplus.com/", "日文,很多免費連載"),
             ("📗 台南市圖電子書", "https://tnml.ebook.hyread.com.tw/", "HyRead,用台南市圖借書證免費借中文漫畫")]
    for i in range(0, len(sites), 2):
        for col, (name, url, note) in zip(st.columns(2), sites[i:i + 2]):
            with col:
                st.link_button(name, url, use_container_width=True)
                st.caption(note)
    st.caption("手機上有裝這些 App 的話,點了通常會直接用 App 打開。")
    st.divider()
    st.markdown("##### 📖 我的漫畫書櫃(手機裡的漫畫檔)")
    st.caption("選手機裡的 CBZ、ZIP、PDF 或一堆圖片加進書櫃,會記住看到哪一頁。點封面就全螢幕看:條漫往下滑,"
               "日漫點左邊翻下一頁,點中間叫出選單(換模式、跳頁、調暗),按 ← 回書櫃。漫畫只存在這支手機的瀏覽器裡,不會上傳。")
    with open(READER_HTML, encoding="utf-8") as fh:
        components_html(fh.read(), height=560, scrolling=False)
    st.divider()
    st.markdown("##### 🔔 追更清單")
    follows = list(U.pref("comic_follow", []))
    with st.form("comic_add", clear_on_submit=True):
        link = st.text_input("貼上 LINE WEBTOON 作品網址", placeholder="例如:https://www.webtoons.com/zh-hant/action/xxx/list?title_no=1234")
        if st.form_submit_button("➕ 追這部", type="primary") and link.strip():
            try:
                rss = D.feed_url(link)
                feed = feed_c(rss)
                if any(f["rss"] == rss for f in follows):
                    st.info("這部已經在追了")
                else:
                    latest = feed["items"][0]["link"] if feed["items"] else ""
                    follows.append({"rss": rss, "title": feed["title"], "link": feed["link"], "seen": latest})
                    U.remember("comic_follow", follows)
                    st.success(f"開始追「{feed['title']}」,出新話會在這裡和首頁提醒你")
            except Exception as e:  # noqa: BLE001
                st.warning(f"加不進來:{e}")
    st.caption("怎麼拿網址:在 WEBTOON App 或網站打開作品 → 分享 → 複製連結,貼到上面。其他有 RSS 的漫畫網站也可以貼 RSS 網址。")
    if not follows:
        st.info("還沒有追任何作品。")
        return
    if st.button("🔄 檢查更新", key="comic_refresh"):
        feed_c.clear()
    now = K.tw_now()
    for k, f in enumerate(follows):
        feed = U.quiet(feed_c, f["rss"])
        with st.container(border=True):
            if not feed:
                st.markdown(f"**{_esc(f['title'])}**　<span style='opacity:.6'>暫時讀不到更新</span>", unsafe_allow_html=True)
            else:
                items = feed["items"]
                new = [it for it in items if it["link"] != f.get("seen")]
                try:
                    n_new = items.index(next(it for it in items if it["link"] == f.get("seen")))
                except StopIteration:
                    n_new = len(new) if f.get("seen") else 0
                a, b = st.columns([1, 4], vertical_alignment="center")
                if feed["cover"]:
                    a.image(feed["cover"], width=72)
                top = items[0] if items else None
                when = ""
                if top and top["date"]:
                    days = (now.date() - top["date"].date()).days
                    when = "今天" if days == 0 else "昨天" if days == 1 else f"{days} 天前"
                badge = f"<b style='color:#ff6b3d'>🆕 {n_new} 話新的</b>　" if n_new else ""
                b.markdown(f"**{_esc(feed['title'])}**<br>{badge}最新:{_esc(top['title']) if top else '—'}"
                           f"<span style='opacity:.6'>　{when}</span>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            if feed and feed["items"]:
                c1.link_button("📖 看最新", feed["items"][0]["link"])
                if feed["items"][0]["link"] != f.get("seen") and c2.button("✓ 看過了", key=f"comic_seen_{k}"):
                    follows[k] = {**f, "seen": feed["items"][0]["link"]}
                    U.remember("comic_follow", follows)
                    st.rerun()
            if c3.button("🗑️ 不追了", key=f"comic_rm_{k}"):
                U.remember("comic_follow", follows[:k] + follows[k + 1:])
                st.rerun()
    st.caption("每 30 分鐘最多檢查一次。點「看最新」會在 WEBTOON 官方網頁或 App 打開,作者也有收入。")
