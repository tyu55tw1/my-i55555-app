# -*- coding: utf-8 -*-
"""新增的生活頁面:防災資訊、停車、假日、分帳、換算工具、設定,以及股票/匯率/發票/天氣的新分頁。"""
from __future__ import annotations

import json
import math
import re
from datetime import date, timedelta

import pandas as pd
import streamlit as st
from streamlit.components.v1 import html as components_html

import core as K
import life as L
import ui as U
from ui import _esc, hero, safe

WD = "一二三四五六日"


def _md(d: date) -> str:
    return f"{d.month}/{d.day} ({WD[d.weekday()]})"


# ── 快取包裝 ──
parking_desc = st.cache_data(ttl=86400, show_spinner="讀取停車場資料…")(L.fetch_parking_desc)
parking_avail = st.cache_data(ttl=60, show_spinner=False)(L.fetch_parking_avail)
aqi = st.cache_data(ttl=600, show_spinner="取得空氣品質…")(L.fetch_aqi)
aqi_om = st.cache_data(ttl=600, show_spinner="取得空氣品質…")(L.fetch_aqi_openmeteo)
cwa_warnings = st.cache_data(ttl=300, show_spinner=False)(L.fetch_cwa_warnings)
earthquakes = st.cache_data(ttl=300, show_spinner=False)(L.fetch_earthquakes)
typhoons = st.cache_data(ttl=600, show_spinner=False)(L.fetch_typhoons)
closures = st.cache_data(ttl=300, show_spinner=False)(L.fetch_closures)
calendar = st.cache_data(ttl=86400, show_spinner="讀取行事曆…")(L.fetch_calendar)
bank_rates = st.cache_data(ttl=600, show_spinner="取得銀行牌告…")(L.fetch_bank_rates)
dividends = st.cache_data(ttl=3600, show_spinner="取得除權息預告…")(L.fetch_dividends)
quotes = st.cache_data(ttl=20, show_spinner=False)(lambda codes: L.fetch_quotes(list(codes)))


def holidays_all() -> list[dict]:
    """今年 + 明年行事曆(明年還沒公告就只有今年)。"""
    y = K.tw_now().year
    out = []
    for yy in (y, y + 1):
        cal = U.quiet(calendar, yy)
        if cal:
            out += cal
    return out


# ════════════════════════════════════════════════════════════════════
#  ⚠️ 防災資訊
# ════════════════════════════════════════════════════════════════════
WARN_ICON = [("颱風", "🌀"), ("豪雨", "🌧️"), ("大雨", "🌧️"), ("雷雨", "⛈️"), ("強風", "💨"), ("低溫", "🥶"),
             ("高溫", "🥵"), ("濃霧", "🌫️"), ("長浪", "🌊"), ("海上", "🚢"), ("地震", "🌏")]


def warn_icon(title):
    return next((i for k, i in WARN_ICON if k in title), "📢")


def eq_color(i):
    return "#888" if i is None else "#5b8def" if i <= 2 else "#d6a400" if i == 3 else "#ec7a1c" if i == 4 else "#d63a3a"


def page_alerts():
    hero("⚠️", "防災資訊", "停班停課・颱風・天氣警特報・最新地震")
    if st.button("🔄 重新整理"):
        for f in (closures, typhoons, cwa_warnings, earthquakes):
            f.clear()
        st.rerun()
    with st.spinner("取得最新防災資訊…"):
        got = U.parallel(cl=closures, ty=typhoons, wn=cwa_warnings, eq=earthquakes)

    st.markdown("#### 🏫 停班停課")
    cl = got["cl"]
    if cl is None:
        st.warning("暫時連不上人事行政總處,請直接查看官網。")
    elif not cl[0]:
        st.success("目前全台沒有停班停課訊息。")
    else:
        h = ""
        for county, status in cl[0]:
            cls = "red" if re.search(r"停止(上班|上課)", status) else "amber"
            h += f"<div class='alert {cls}'><div><b>{_esc(county)}</b>{_esc(status)}</div></div>"
        st.markdown(h, unsafe_allow_html=True)
    st.link_button("人事行政總處停班停課公告 ↗", L.DGPA_URL)

    st.markdown("#### 📢 天氣警特報")
    wn = got["wn"]
    if wn is None:
        st.warning("暫時連不上中央氣象署。")
    elif not wn:
        st.success("目前沒有生效中的天氣警特報。")
    else:
        for w in wn:
            red = any(k in w["title"] for k in ("颱風警報", "豪雨", "海上陸上"))
            with st.container(border=True):
                st.markdown(f"**{warn_icon(w['title'])} {w['title']}**　" + (":red[重要]" if red else ""))
                st.caption(f"發布 {w['issued']}　・有效至 {w['validto'] or '—'}")
                st.write(w["content"][:400] + ("…" if len(w["content"]) > 400 else ""))

    st.markdown("#### 🌀 颱風")
    ty = got["ty"]
    if ty is None:
        st.caption("暫時無法取得颱風資料")
    elif not ty:
        st.success("目前西北太平洋沒有颱風。")
    else:
        st.caption("以下是目前西北太平洋上的颱風,不一定會影響台灣;有沒有發布警報請看上方「天氣警特報」。")
        for t in ty:
            st.markdown(f"<div class='card'><div class='ct'>🌀 {_esc(t['strength'])} {_esc(t['name'])}"
                        f"<small style='opacity:.7'>　{_esc(t['en'])}・第 {_esc(t['no'])} 號</small></div>"
                        f"<div class='cs'>{_esc(t['desc'])}</div></div>", unsafe_allow_html=True)
    st.link_button("氣象署颱風消息 ↗", "https://www.cwa.gov.tw/V8/C/P/Typhoon/TY_NEWS.html")

    st.markdown("#### 🌏 最近地震")
    eq = got["eq"]
    if not eq:
        st.caption("暫時無法取得地震資料")
    else:
        only = st.toggle("只看有編號的顯著有感地震", False)
        h = ""
        for e in [x for x in eq if not only or x["no"]][:12]:
            lv = f"{e['intensity']}級" if e["intensity"] is not None else "—"
            tag = f"第 {e['no']} 號" if e["no"] else ("小區域" if e["local"] else "")
            link = f" <a href='{_esc(e['url'])}' target='_blank'>詳情 ↗</a>" if e["url"] else ""
            h += (f"<div class='alert'><span class='dot' style='background:{eq_color(e['intensity'])}'>{lv}</span>"
                  f"<div><b>{_esc(e['where'])}　規模 {e['mag']}</b><small>{_esc(e['time'])}　深度 {e['depth'] or '—'} km　{tag}{link}</small>"
                  f"<small>{_esc(e['place'])}</small></div></div>")
        st.markdown(h, unsafe_allow_html=True)
        st.caption("震度為全台最大震度。資料來源:中央氣象署(連不上時改用 USGS,只有規模 4 以上)")


# ════════════════════════════════════════════════════════════════════
#  🌫️ 空氣品質(天氣頁的分頁)
# ════════════════════════════════════════════════════════════════════
def aqi_dot(v, size=52):
    name, col, _ = L.aqi_level(v)
    txt = "—" if v is None else f"{v:.0f}"
    return f"<span class='dot' style='background:{col};min-width:{size}px;height:{size}px'>{txt}</span>"


def aqi_card(x, extra="", tip=False):
    name, col, tip_ = L.aqi_level(x["aqi"])
    tip = f"<small>{tip_}</small>" if tip else ""
    pm = f"PM2.5 {x['pm25']:.0f}" if x.get("pm25") is not None else "PM2.5 —"
    main = f"・主要:{_esc(x['pollutant'])}" if x.get("pollutant") else ""
    return (f"<div class='alert'>{aqi_dot(x['aqi'])}<div><b>{_esc(x['site'])} <span style='color:{col}'>{name}</span>{extra}</b>"
            f"<small>{pm} μg/m³{main}</small>{tip}</div></div>")


def aqi_view():
    data = U.quiet(aqi)
    if not data:
        st.info("環境部測站資料暫時連不上,改用 Open-Meteo 模式估計值(美國 AQI 標準,僅供參考)。")
        cs = list(L.COUNTY_XY)
        c = st.selectbox("縣市", cs, key="aqi_fallback_c")
        d = safe(aqi_om, *L.COUNTY_XY[c])
        if d:
            st.markdown(aqi_card({"site": c, "aqi": d["aqi"], "pm25": d["pm25"]}, tip=True), unsafe_allow_html=True)
        return
    order = {c: i for i, c in enumerate(L.COUNTY_XY)}
    counties = sorted({x["county"] for x in data}, key=lambda c: order.get(c, 99))
    saved = U.pref("aqi_county", "臺北市")
    c1, c2 = st.columns([2, 1])
    county = c1.selectbox("縣市", counties, index=counties.index(saved) if saved in counties else 0, key=f"aqi_county_{U.rev()}")
    U.remember("aqi_county", county)
    with c2:
        pos = U.geolocate("geo_aqi", "📍 離我最近的測站")
    if pos:
        near = sorted((x for x in data if x["lat"]), key=lambda x: L.haversine(*pos, x["lat"], x["lon"]))[:3]
        st.markdown("**📍 離你最近的測站**", unsafe_allow_html=True)
        st.markdown("".join(aqi_card(x, f"<small style='display:inline;opacity:.7'>　{L.haversine(*pos, x['lat'], x['lon']):.1f} 公里・{_esc(x['county'])}</small>", tip=i == 0)
                            for i, x in enumerate(near)), unsafe_allow_html=True)
    sites = sorted((x for x in data if x["county"] == county), key=lambda x: -(x["aqi"] or 0))
    st.markdown(f"**{county}・{len(sites)} 個測站**")
    if sites and sites[0]["aqi"] is not None:
        name, col, tip = L.aqi_level(sites[0]["aqi"])
        st.markdown(f"<div class='alert' style='border-color:{col}'><span>💡</span><div><b>最高的測站為「{name}」</b><small>{tip}</small></div></div>",
                    unsafe_allow_html=True)
    st.markdown("<div class='tiles'>" + "".join(f"<div>{aqi_card(x)}</div>" for x in sites) + "</div>", unsafe_allow_html=True)
    lv = {}
    for x in data:
        n = L.aqi_level(x["aqi"])[0]
        lv[n] = lv.get(n, 0) + 1
    st.caption(f"全台 {len(data)} 站:" + "・".join(f"{k} {v}" for k, v in lv.items()) + f"　｜　發布時間 {data[0]['time']}　｜　資料來源:環境部")


# ════════════════════════════════════════════════════════════════════
#  🅿️ 停車
# ════════════════════════════════════════════════════════════════════
def page_parking():
    hero("🅿️", "台北市停車場", "即時剩餘車位(臺北市交通局,約每分鐘更新)・可用定位找最近的")
    desc = safe(parking_desc)
    if not desc:
        return
    avail, upd = U.quiet(parking_avail) or ({}, "")
    areas = ["全部"] + sorted({p["area"] for p in desc if p["area"]})
    saved = U.pref("park_area", "全部")
    c1, c2, c3 = st.columns([1.2, 2, 1.3])
    area = c1.selectbox("行政區", areas, index=areas.index(saved) if saved in areas else 0, key=f"park_area_{U.rev()}")
    U.remember("park_area", area)
    q = c2.text_input("🔍 搜尋名稱或地址", placeholder="例如:市府、南京東路、101").strip()
    kind = c3.radio("車種", ["汽車", "機車"], horizontal=True)
    c4, c5, c6 = st.columns([1.3, 1.3, 1.4])
    with c4:
        pos = U.geolocate("geo_park", "📍 找我附近")
    only = c5.toggle("只顯示有空位", True, key="park_only")
    sorts = (["距離最近"] if pos else []) + ["空位最多", "名稱"]
    sort = c6.selectbox("排序", sorts)
    ki = 0 if kind == "汽車" else 1
    rows = []
    for p in desc:
        total = p["total_car"] if ki == 0 else p["total_motor"]
        if total <= 0 or (area != "全部" and p["area"] != area):
            continue
        if q and q not in p["name"] and q not in p["address"]:
            continue
        a = avail.get(p["id"], (None, None))[ki]
        if only and not a:
            continue
        dist = L.haversine(*pos, p["lat"], p["lon"]) if pos and p["lat"] else None
        if pos and sort == "距離最近" and dist is None:
            continue
        rows.append((p, a, total, dist))
    key = {"距離最近": lambda r: r[3], "空位最多": lambda r: -(r[1] or -1), "名稱": lambda r: r[0]["name"]}[sort]
    rows.sort(key=key)
    st.caption(f"符合 {len(rows)} 個停車場　・即時資料 {upd or '—'}" + ("　・只計算有座標的停車場" if sort == "距離最近" else ""))
    if not rows:
        st.info("沒有符合條件的停車場,可以取消「只顯示有空位」或換個行政區。")
        return
    pts = [r for r in rows[:400] if r[0]["lat"]]
    if pts:
        def col(a, t):
            if a is None:
                return "#888888"
            return "#1f9d55" if a >= max(5, t * .2) else "#d6a400" if a > 0 else "#d63a3a"
        st.map(pd.DataFrame({"lat": [r[0]["lat"] for r in pts], "lon": [r[0]["lon"] for r in pts],
                             "color": [col(r[1], r[2]) for r in pts]}), color="color", size=28, height=320,
               zoom=15 if pos and sort == "距離最近" else 12)
    h = ""
    for p, a, total, dist in rows[:40]:
        pct = 0 if a is None else min(100, a / total * 100)
        colr = "#888" if a is None else "#1f9d55" if pct >= 20 or a >= 30 else "#d6a400" if a > 0 else "#d63a3a"
        num = "無即時資料" if a is None else f"剩 <b style='color:{colr}'>{a}</b> / {total} 位"
        d = f"・{dist:.1f} 公里" if dist is not None else ""
        nav = (f"<a href='https://www.google.com/maps/dir/?api=1&destination={p['lat']},{p['lon']}' target='_blank'>🧭 導航</a>"
               if p["lat"] else f"<a href='https://www.google.com/maps/search/?api=1&query={_esc(p['name'])}' target='_blank'>🧭 地圖</a>")
        ev = "・⚡ 充電樁" if p["ev"] else ""
        h += (f"<div class='card'><div class='ct'>{_esc(p['name'])}</div>"
              f"<div class='cs'>{_esc(p['area'])}{d}{ev}・{num}</div>"
              f"<div class='bar'><i style='width:{pct:.0f}%;background:{colr}'></i></div>"
              f"<div class='cs'>📍 {_esc(p['address'])}　{nav}</div>"
              f"<details><summary class='cs'>💰 收費與營業時間</summary><div class='cs'>{_esc(p['pay'] or '—')}<br>🕒 {_esc(p['hours'] or '—')}　☎ {_esc(p['tel'] or '—')}</div></details></div>")
    st.markdown(h, unsafe_allow_html=True)
    if len(rows) > 40:
        st.caption(f"只列出前 40 個(共 {len(rows)} 個),可用搜尋或行政區縮小範圍")
    st.caption("目前只有台北市(含市府委外與部分民營停車場)。其他縣市需要交通部 TDX 金鑰才能取得。")


# ════════════════════════════════════════════════════════════════════
#  📅 假日行事曆
# ════════════════════════════════════════════════════════════════════
def _range_txt(a: date, b: date) -> str:
    return _md(a) if a == b else f"{_md(a)} – {_md(b)}"


def month_grid(days_idx: dict, y: int, m: int, today: date) -> str:
    first = date(y, m, 1)
    nxt = date(y + (m == 12), m % 12 + 1, 1)
    h = "<div class='cal'>" + "".join(f"<div class='h'>{w}</div>" for w in WD)
    h += "<div class='e'></div>" * first.weekday()
    d = first
    while d < nxt:
        info = days_idx.get(d)
        cls = []
        if info and info["off"]:
            cls.append("off")
        if info and info["makeup"]:
            cls.append("mk")
        if d == today:
            cls.append("today")
        desc = info["desc"] if info else ""
        if info and info["makeup"]:
            desc = desc or "補班"
        h += f"<div class='{' '.join(cls)}'><b>{d.day}</b><br>{_esc(desc)}</div>"
        d += timedelta(days=1)
    return h + "</div>"


def page_holidays():
    hero("📅", "假日行事曆", "國定假日・連假倒數・補班日・請假攻略")
    days = holidays_all()
    if not days:
        st.error("行事曆暫時取得失敗,請稍後再試。")
        return
    today = K.tw_now().date()
    lw = [x for x in L.long_weekends(days) if x["end"] >= today]
    named = [d for d in days if d["off"] and d["desc"] and d["date"] >= today]
    makeups = [d for d in days if d["makeup"] and d["date"] >= today]
    if lw:
        x = lw[0]
        n = (x["start"] - today).days
        if n <= 0:
            big, sub = "🎉 放假中", f"「{x['name']}」連假到 {_md(x['end'])},共 {x['days']} 天"
        else:
            big, sub = f"還有 {n} 天", f"下一個連假:「{x['name']}」{_range_txt(x['start'], x['end'])},連休 {x['days']} 天"
        st.markdown(f"<div class='card' style='text-align:center;padding:20px'><div class='cs'>距離下個連假</div>"
                    f"<div class='big' style='color:var(--ac)'>{big}</div><div class='cs' style='font-size:1rem'>{_esc(sub)}</div></div>",
                    unsafe_allow_html=True)
    nd = (named[0]["date"] - today).days if named else None
    st.markdown("<div class='tiles'>"
                f"<div class='tile' style='min-height:0'><span class='tl'>下一個國定假日</span><span class='tv' style='font-size:1.25rem'>{_esc(named[0]['desc']) if named else '—'}</span>"
                f"<span class='ts'>{(_md(named[0]['date']) + '・' + ('就是今天' if nd == 0 else f'還有 {nd} 天')) if named else ''}</span></div>"
                f"<div class='tile' style='min-height:0'><span class='tl'>{today.year} 年剩下的連假</span><span class='tv'>{sum(1 for x in lw if x['start'].year == today.year)} 個</span>"
                f"<span class='ts'>連續放假 3 天以上</span></div>"
                f"<div class='tile' style='min-height:0'><span class='tl'>接下來的補班日</span><span class='tv'>{f'{len(makeups)} 天' if makeups else '沒有 🎉'}</span>"
                f"<span class='ts'>{_md(makeups[0]['date']) + ' 要上班' if makeups else '不用補班'}</span></div></div>", unsafe_allow_html=True)
    t1, t2, t3, t4 = st.tabs(["🗓️ 月曆", "🏖️ 連假", "💡 請假攻略", "📋 全部假日"])
    idx = {d["date"]: d for d in days}
    with t1:
        months = sorted({d["date"].strftime("%Y/%m") for d in days})
        cur = today.strftime("%Y/%m")
        ym = st.select_slider("月份", months, value=cur if cur in months else months[0])
        y_, m_ = (int(v) for v in ym.split("/"))
        st.markdown(month_grid(idx, y_, m_, today), unsafe_allow_html=True)
        st.caption("紅色 = 放假　藍色 = 補班　外框 = 今天")
    with t2:
        if not lw:
            st.info("今年已經沒有連假了")
        for x in lw:
            n = (x["start"] - today).days
            cd = "放假中 🎉" if n <= 0 else f"還有 {n} 天"
            st.markdown(f"<div class='card'><div class='ct'>🏖️ {_esc(x['name'])}　<span style='color:var(--ac)'>{x['days']} 天</span></div>"
                        f"<div class='cs'>{_range_txt(x['start'], x['end'])}　・{cd}</div></div>", unsafe_allow_html=True)
    with t3:
        hacks = [x for x in L.leave_hacks(days) if x["leave"][0] > today]
        st.caption("請少少幾天假,接上國定假日與週末變成長假。")
        if not hacks:
            st.info("接下來沒有特別划算的請假組合")
        for x in hacks:
            names = "、".join(dict.fromkeys(idx[x["start"] + timedelta(days=i)]["desc"] for i in range(x["days"])
                                          if (x["start"] + timedelta(days=i)) in idx and idx[x["start"] + timedelta(days=i)]["desc"]))
            lv = "、".join(_md(d) for d in x["leave"])
            st.markdown(f"<div class='card'><div class='ct'>請 {x['cost']} 天 → 連休 <span style='color:var(--ac)'>{x['days']} 天</span></div>"
                        f"<div class='cs'>請假:{lv}<br>連休:{_range_txt(x['start'], x['end'])}　({_esc(names)})</div></div>", unsafe_allow_html=True)
    with t4:
        rows = [(d["date"].strftime("%Y/%m/%d"), WD[d["date"].weekday()], d["desc"], (d["date"] - today).days) for d in named]
        rows += [(d["date"].strftime("%Y/%m/%d"), WD[d["date"].weekday()], (d["desc"] or "補班") + " 🔵", (d["date"] - today).days) for d in makeups]
        rows.sort()
        st.dataframe(pd.DataFrame(rows, columns=["日期", "星期", "假日", "倒數(天)"]), hide_index=True, width="stretch")
    st.caption("資料來源:行政院人事行政總處辦公日曆表(TaiwanCalendar 整理)")


# ════════════════════════════════════════════════════════════════════
#  🍱 聚餐分帳
# ════════════════════════════════════════════════════════════════════
def page_split():
    hero("🍱", "聚餐分帳", "誰付了多少、誰要給誰錢,一次算清楚")
    t1, t2 = st.tabs(["🧾 詳細分帳", "⚡ 快速平分"])
    with t2:
        c1, c2, c3 = st.columns(3)
        total = c1.number_input("總金額", 0, 10_000_000, 1200, step=100)
        n = c2.number_input("人數", 1, 100, 4)
        svc = c3.checkbox("加一成服務費", key="quick_svc")
        amt = total * (1.1 if svc else 1)
        each = math.ceil(amt / n)
        st.markdown(f"<div class='card' style='text-align:center'><div class='cs'>每人</div><div class='big' style='color:var(--ac)'>NT$ {each:,}</div>"
                    f"<div class='cs'>合計 {amt:,.0f} 元 ÷ {n} 人(無條件進位,多收 {each * n - amt:,.0f} 元)</div></div>", unsafe_allow_html=True)
    with t1:
        txt = st.text_input("👥 成員(用空白或逗號分隔)", " ".join(U.pref("split_members", ["我", "小明", "小華"])), key=f"split_m_{U.rev()}")
        members = list(dict.fromkeys(m for m in re.split(r"[\s,，、]+", txt.strip()) if m))[:20]
        if len(members) < 2:
            st.info("請至少輸入兩位成員")
            return
        U.remember("split_members", members)
        svc = st.checkbox("每筆加 10% 服務費", key="split_svc")
        if "split_df" not in st.session_state:
            st.session_state["split_df"] = pd.DataFrame([{"項目": "晚餐", "付款人": members[0], "金額": 1200, "分攤者": []},
                                                         {"項目": "飲料", "付款人": members[1], "金額": 300, "分攤者": []}])
        st.caption("每一列是一筆支出。「分攤者」留空 = 全部人平分;只有部分人吃的就選那幾個人。點表格最下面可以新增一列。")
        df = st.data_editor(st.session_state["split_df"], num_rows="dynamic", hide_index=True, width="stretch", key="split_editor",
                            column_config={"項目": st.column_config.TextColumn("項目"),
                                           "付款人": st.column_config.SelectboxColumn("付款人", options=members, required=True),
                                           "金額": st.column_config.NumberColumn("金額", min_value=0, step=1, format="%d"),
                                           "分攤者": st.column_config.MultiselectColumn("分攤者(空白=全部)", options=members)})
        items = []
        for _, r in df.iterrows():
            share = r.get("分攤者")
            share = list(share) if isinstance(share, (list, tuple)) else []
            try:
                amt = float(r.get("金額") or 0)
            except (TypeError, ValueError):
                amt = 0.0
            if amt > 0 and r.get("付款人") in members:
                items.append({"name": r.get("項目") or "", "payer": r["付款人"], "amount": amt, "share": share})
        if not items:
            st.info("輸入至少一筆支出")
            return
        res = L.split_bill(members, items, 0.1 if svc else 0)
        st.markdown(f"##### 💸 要怎麼轉帳(總計 NT$ {res['total']:,.0f})")
        if not res["transfers"]:
            st.success("大家剛好付平,不用轉帳 🎉")
        st.markdown("".join(f"<div class='xfer'><b>{_esc(a)}</b> ➜ <b>{_esc(b)}</b><span class='amt'>NT$ {v:,}</span></div>"
                            for a, b, v in res["transfers"]), unsafe_allow_html=True)
        with st.expander("每個人的明細"):
            st.dataframe(pd.DataFrame([(m, round(res["paid"][m]), round(res["owe"][m]), round(res["paid"][m] - res["owe"][m])) for m in members],
                                      columns=["成員", "已付", "應付", "差額(+收 / -付)"]), hide_index=True, width="stretch")
        text = f"🍱 分帳結果(總計 ${res['total']:,.0f})\n" + "\n".join(f"{a} → {b}:${v:,}" for a, b, v in res["transfers"])
        st.caption("複製貼到 LINE 群組:")
        st.code(text, language=None)


# ════════════════════════════════════════════════════════════════════
#  📐 換算・BMI・計時
# ════════════════════════════════════════════════════════════════════
TIMER_HTML = r"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
:root{color-scheme:light dark;--ac:#ff6b3d}
body{margin:0;font-family:system-ui,-apple-system,"Noto Sans TC",sans-serif;background:transparent;color:CanvasText}
.wrap{display:flex;flex-direction:column;align-items:center;gap:12px;padding:6px}
.tabs button,.pre button,.ctl button{font:inherit;font-weight:700;border-radius:12px;border:1px solid rgba(128,128,128,.35);background:rgba(128,128,128,.12);color:inherit;padding:.45rem .9rem;cursor:pointer}
.tabs button.on{background:var(--ac);border-color:var(--ac);color:#fff}
.ring{position:relative;width:210px;height:210px}.ring svg{transform:rotate(-90deg)}
.t{position:absolute;inset:0;display:grid;place-items:center;font-size:2.7rem;font-weight:800;font-variant-numeric:tabular-nums}
.pre,.ctl{display:flex;flex-wrap:wrap;gap:8px;justify-content:center}
.ctl button.go{background:var(--ac);border-color:var(--ac);color:#fff;min-width:96px}
input{width:64px;font:inherit;font-size:1.1rem;text-align:center;padding:.35rem;border-radius:10px;border:1px solid rgba(128,128,128,.4);background:transparent;color:inherit}
.laps{max-height:90px;overflow:auto;font-size:.9rem;opacity:.85;text-align:center}
.done{animation:fl .5s 6 alternate}@keyframes fl{to{color:var(--ac)}}
</style></head><body><div class="wrap">
<div class="tabs"><button id="m1" class="on">⏳ 倒數計時</button> <button id="m2">⏱️ 碼表</button></div>
<div class="ring"><svg width="210" height="210"><circle cx="105" cy="105" r="95" stroke="rgba(128,128,128,.2)" stroke-width="12" fill="none"/>
<circle id="arc" cx="105" cy="105" r="95" stroke="#ff6b3d" stroke-width="12" fill="none" stroke-linecap="round" stroke-dasharray="597" stroke-dashoffset="0"/></svg>
<div class="t" id="t">03:00</div></div>
<div class="pre" id="pre"><button data-s="180">🍜 泡麵 3 分</button><button data-s="480">🥚 水煮蛋 8 分</button><button data-s="1500">🍅 番茄鐘 25 分</button><button data-s="300">🧘 休息 5 分</button>
<span><input id="mm" type="number" min="0" max="999" value="3"> 分 <input id="ss" type="number" min="0" max="59" value="0"> 秒</span></div>
<div class="ctl"><button class="go" id="go">▶ 開始</button><button id="lap" style="display:none">🏁 計圈</button><button id="rs">↺ 重設</button></div>
<div class="laps" id="laps"></div></div>
<script>
let mode=1,total=180,left=180,run=false,t0=0,base=0,timer=null,laps=[];
const $=id=>document.getElementById(id),C=597;
const fmt=s=>{s=Math.max(0,s);const h=Math.floor(s/3600),m=Math.floor(s%3600/60),x=Math.floor(s%60);return (h?h+":":"")+String(m).padStart(2,"0")+":"+String(x).padStart(2,"0")};
const fmtms=ms=>fmt(ms/1000)+"."+String(Math.floor(ms%1000/100));
function beep(){try{const a=new (window.AudioContext||window.webkitAudioContext)();[0,.35,.7,1.05].forEach(d=>{const o=a.createOscillator(),g=a.createGain();o.frequency.value=880;o.connect(g);g.connect(a.destination);g.gain.setValueAtTime(.25,a.currentTime+d);g.gain.exponentialRampToValueAtTime(.001,a.currentTime+d+.3);o.start(a.currentTime+d);o.stop(a.currentTime+d+.3)})}catch(e){} if(navigator.vibrate)navigator.vibrate([300,150,300,150,300]);}
function draw(){if(mode==1){$("t").textContent=fmt(Math.ceil(left));$("arc").style.strokeDashoffset=C*(1-(total?left/total:0));}
 else{const ms=base+(run?Date.now()-t0:0);$("t").textContent=fmtms(ms);$("arc").style.strokeDashoffset=C*(1-((ms/1000)%60)/60);}}
function tick(){if(mode==1){left=total-(base+(Date.now()-t0))/1000;if(left<=0){left=0;stop();$("t").classList.add("done");beep();document.title="⏰ 時間到!";}}draw();}
function start(){if(mode==1&&left<=0)return;run=true;t0=Date.now();timer=setInterval(tick,100);$("go").textContent="⏸ 暫停";$("t").classList.remove("done");}
function stop(){if(run)base+=Date.now()-t0;run=false;clearInterval(timer);$("go").textContent="▶ 開始";draw();}
function reset(){stop();base=0;laps=[];$("laps").innerHTML="";if(mode==1){total=(+$("mm").value||0)*60+(+$("ss").value||0);left=total;}draw();}
$("go").onclick=()=>run?stop():start();$("rs").onclick=reset;
$("lap").onclick=()=>{if(!run)return;laps.unshift(base+Date.now()-t0);$("laps").innerHTML=laps.map((l,i)=>"第 "+(laps.length-i)+" 圈 "+fmtms(l)).join("<br>");};
document.querySelectorAll("#pre button").forEach(b=>b.onclick=()=>{const s=+b.dataset.s;$("mm").value=Math.floor(s/60);$("ss").value=s%60;reset();start();});
["mm","ss"].forEach(i=>$(i).onchange=reset);
$("m1").onclick=()=>{mode=1;$("m1").className="on";$("m2").className="";$("pre").style.display="";$("lap").style.display="none";reset();};
$("m2").onclick=()=>{mode=2;$("m2").className="on";$("m1").className="";$("pre").style.display="none";$("lap").style.display="";reset();};
draw();
</script></body></html>"""


def page_tools():
    hero("📐", "換算・BMI・計時", "坪數、台斤、溫度換算,BMI 與每日熱量,倒數計時與碼表")
    t1, t2, t3 = st.tabs(["📐 單位換算", "⚖️ BMI・熱量", "⏱️ 計時器"])
    with t1:
        cats = list(L.UNITS) + ["溫度"]
        cat = st.pills("類別", cats, default="面積", key="conv_cat") or "面積"
        units = ["°C", "°F", "K"] if cat == "溫度" else list(L.UNITS[cat])
        c1, c2 = st.columns([1, 1])
        defaults = {"面積": 30.0, "重量": 1.0, "長度": 170.0, "容量": 1.0, "溫度": 25.0}
        v = c1.number_input("數值", value=defaults[cat], step=1.0, key=f"conv_v_{cat}", format="%.4g")
        src = c2.selectbox("單位", units, key=f"conv_u_{cat}")
        tiles = ""
        for u in units:
            if u == src:
                continue
            r = L.convert(v, cat, src, u)
            txt = f"{r:,.4f}".rstrip("0").rstrip(".") if abs(r) < 1e6 else f"{r:,.0f}"
            tiles += f"<div class='tile' style='min-height:0'><span class='tl'>{_esc(u)}</span><span class='tv'>{txt}</span></div>"
        st.markdown(f"<div class='tiles'>{tiles}</div>", unsafe_allow_html=True)
        st.caption("1 坪 ≈ 3.3058 平方公尺・1 台斤 = 600 公克 = 16 台兩・1 甲 ≈ 2934 坪")
    with t2:
        b = U.pref("bmi", {"cm": 170, "kg": 65, "age": 30, "male": True})
        r_ = U.rev()
        c1, c2, c3, c4 = st.columns(4)
        cm = c1.number_input("身高(公分)", 100.0, 230.0, float(b.get("cm", 170)), step=1.0, key=f"bmi_cm_{r_}")
        kg = c2.number_input("體重(公斤)", 20.0, 250.0, float(b.get("kg", 65)), step=0.5, key=f"bmi_kg_{r_}")
        age = c3.number_input("年齡", 10, 100, int(b.get("age", 30)), key=f"bmi_age_{r_}")
        male = c4.radio("性別", ["男", "女"], index=0 if b.get("male", True) else 1, horizontal=True, key=f"bmi_sex_{r_}") == "男"
        U.remember("bmi", {"cm": cm, "kg": kg, "age": age, "male": male})
        info = L.bmi_info(cm, kg)
        base = L.bmr(cm, kg, age, male)
        acts = {"久坐(幾乎不運動)": 1.2, "輕度(每週運動 1~3 天)": 1.375, "中度(每週 3~5 天)": 1.55, "高度(每週 6~7 天)": 1.725}
        act = st.selectbox("活動量", list(acts), index=1)
        tdee = base * acts[act]
        st.markdown(
            f"<div class='tiles'><div class='tile'><span class='tl'>BMI</span><span class='tv' style='color:{info['color']}'>{info['bmi']:.1f}</span>"
            f"<span class='ts'>{info['level']}(標準 18.5 ~ 24)</span></div>"
            f"<div class='tile'><span class='tl'>健康體重範圍</span><span class='tv'>{info['lo']:.1f} ~ {info['hi']:.1f}</span><span class='ts'>公斤</span></div>"
            f"<div class='tile'><span class='tl'>基礎代謝 BMR</span><span class='tv'>{base:,.0f}</span><span class='ts'>大卡/天(躺著不動也會消耗)</span></div>"
            f"<div class='tile'><span class='tl'>每日消耗 TDEE</span><span class='tv'>{tdee:,.0f}</span><span class='ts'>想減重約吃 {tdee - 500:,.0f} 大卡/天</span></div></div>",
            unsafe_allow_html=True)
        st.caption("BMI 分級依衛福部國健署成人標準;熱量為 Mifflin-St Jeor 公式估算,僅供參考。")
    with t3:
        components_html(TIMER_HTML, height=470)
        st.caption("時間到會發出嗶聲(手機會震動)。請保持這個頁面開著;切到別的頁面計時會停止。")


# ════════════════════════════════════════════════════════════════════
#  📈 自選股 / 除權息(股票頁的分頁)
# ════════════════════════════════════════════════════════════════════
CODE_RE = re.compile(r"[0-9A-Z]{4,8}")


def watchlist_view():
    codes = U.pref("watch", ["0050", "2330", "00878"])
    opts = list(dict.fromkeys(codes + list(K.STOCK_ZH)))
    sel = st.multiselect("⭐ 自選股(可直接輸入代號後按 Enter 新增)", opts, default=[c for c in codes if c in opts], accept_new_options=True,
                         format_func=lambda c: f"{c} {K.STOCK_ZH.get(c, '')}".strip(), key=f"watch_{U.rev()}", max_selections=30)
    sel = list(dict.fromkeys(c.strip().upper() for c in sel if CODE_RE.fullmatch(c.strip().upper())))
    U.remember("watch", sel)
    if not sel:
        st.info("加入幾檔常看的股票吧!")
        return
    auto = st.toggle("⏱️ 盤中自動更新(30 秒)", key="watch_auto")

    def show():
        q = U.quiet(quotes, tuple(sel)) or {}
        h = ""
        for c in sel:
            x = q.get(c)
            if not x:
                h += f"<div class='tile'><span class='tl'>{c}</span><span class='ts'>查不到報價</span></div>"
                continue
            diff = (x["price"] or 0) - (x["prev"] or 0) if x["price"] and x["prev"] else 0
            pct = diff / x["prev"] * 100 if x["prev"] else 0
            cls = "up" if diff > 0 else "down" if diff < 0 else "flat"
            arrow = "▲" if diff > 0 else "▼" if diff < 0 else ""
            vol = f"・量 {x['volume']:,.0f} 張" if x["volume"] else ""
            hl = f"高 {x['high']:,.2f}・低 {x['low']:,.2f}" if x["high"] and x["low"] else ""
            h += (f"<div class='tile'><span class='tl'>{_esc(x['code'])} {_esc(x['name'])}・{x['market']}</span>"
                  f"<span class='tv {cls}'>{x['price']:,.2f}</span>"
                  f"<span class='ts {cls}'>{arrow} {diff:+,.2f}({pct:+.2f}%)</span><span class='ts'>{hl}{vol}</span></div>")
        st.markdown(f"<div class='tiles'>{h}</div>", unsafe_allow_html=True)
        tm = max((x["time"] for x in q.values()), default="")
        st.caption(f"📡 證交所基本市況報導　・資料時間 {tm or '—'}　・查詢 {K.tw_now():%H:%M:%S}　・漲紅跌綠")

    if auto:
        st.fragment(run_every=30)(show)()
    else:
        show()


def dividends_view():
    dv = safe(dividends)
    if dv is None:
        return
    today = K.tw_now().date()
    watch = set(U.pref("watch", []))
    c1, c2, c3 = st.columns([1.2, 1.2, 2])
    only = c1.toggle("只看自選股", False)
    span = c2.selectbox("期間", ["未來 7 天", "未來 30 天", "全部"], index=1)
    q = c3.text_input("🔍 代號或名稱", key="div_q").strip()
    lim = {"未來 7 天": 7, "未來 30 天": 30, "全部": 9999}[span]
    rows = [x for x in dv if (x["date"] - today).days <= lim and (not only or x["code"] in watch)
            and (not q or q in x["code"] or q in x["name"])]
    mine = [x for x in dv if x["code"] in watch and x["date"] >= today]
    if mine:
        st.markdown("".join(
            f"<div class='alert amber'><div><b>⭐ {_esc(x['code'])} {_esc(x['name'])}　{_md(x['date'])} 除{_esc(x['kind'])}</b>"
            f"<small>{'現金股利 ' + format(x['cash'], '.4g') + ' 元' if x['cash'] else ''}{'・每張配 ' + format(x['stock'] * 1000, '.4g') + ' 股' if x['stock'] else ''}"
            f"　・{'今天' if x['date'] == today else '還有 ' + str((x['date'] - today).days) + ' 天'}</small></div></div>" for x in mine[:6]),
            unsafe_allow_html=True)
    if not rows:
        st.info("這段期間沒有符合的除權息資料")
        return
    px = U.quiet(quotes, tuple(dict.fromkeys(x["code"] for x in rows[:80]))) or {}
    table = []
    for x in rows:
        p = (px.get(x["code"]) or {}).get("price")
        yld = f"{x['cash'] / p * 100:.2f}%" if p and x["cash"] else ""
        n = (x["date"] - today).days
        table.append((x["date"].strftime("%m/%d") + f" ({WD[x['date'].weekday()]})", "已除" if n < 0 else "今天" if n == 0 else f"{n} 天",
                      ("⭐ " if x["code"] in watch else "") + x["code"], x["name"], x["market"], "除" + x["kind"],
                      f"{x['cash']:.4g}" if x["cash"] else "", f"{x['stock'] * 1000:.4g}" if x["stock"] else "", f"{p:,.2f}" if p else "", yld))
    st.dataframe(pd.DataFrame(table, columns=["除權息日", "倒數", "代號", "名稱", "市場", "類型", "現金股利(元)", "每張配股(股)", "股價", "單次殖利率"]),
                 hide_index=True, width="stretch")
    st.caption("資料來源:證交所除權除息預告表、櫃買中心。殖利率 = 這次現金股利 ÷ 目前股價(只算這一次,不是年化)。")


# ════════════════════════════════════════════════════════════════════
#  🏦 銀行牌告(匯率頁的分頁)
# ════════════════════════════════════════════════════════════════════
FX_NAMES = {c: (f, n) for c, f, n in K.FX_CURRENCIES}
FX_NAMES.update({"CHF": ("🇨🇭", "瑞士法郎"), "CAD": ("🇨🇦", "加拿大幣"), "NZD": ("🇳🇿", "紐西蘭幣"), "SEK": ("🇸🇪", "瑞典克朗"),
                 "ZAR": ("🇿🇦", "南非幣"), "MYR": ("🇲🇾", "馬來幣"), "PHP": ("🇵🇭", "菲律賓披索"), "IDR": ("🇮🇩", "印尼盾"),
                 "MXN": ("🇲🇽", "墨西哥披索"), "DKK": ("🇩🇰", "丹麥克朗"), "TRY": ("🇹🇷", "土耳其里拉"), "INR": ("🇮🇳", "印度盧比")})


def fx_label(c):
    f, n = FX_NAMES.get(c, ("💱", ""))
    return f"{f} {c} {n}".strip()


def bank_view(mid: dict | None):
    b = safe(bank_rates)
    if not b:
        return
    rates = b["rates"]
    order = {c: i for i, (c, _, _) in enumerate(K.FX_CURRENCIES)}
    codes = sorted(rates, key=lambda c: (order.get(c, 99), c))
    saved = U.pref("fx_cur", "USD")
    r_ = U.rev()
    c1, c2, c3 = st.columns([1.4, 1.6, 1.2])
    cur = c1.selectbox("幣別", codes, index=codes.index(saved) if saved in codes else 0, format_func=fx_label, key=f"bank_cur_{r_}")
    U.remember("fx_cur", cur)
    buying = c2.radio("我要", ["買外幣(台幣換外幣)", "賣外幣(外幣換回台幣)"], key="bank_dir").startswith("買")
    kinds = [k for k in ("cash", "spot") if k in rates[cur]]
    kind = c3.radio("類型", kinds, format_func=lambda k: "💵 現鈔" if k == "cash" else "🏦 即期(帳戶)", horizontal=True, key="bank_kind")
    bid, ask = rates[cur][kind]
    rate = ask if buying else bid
    c4, c5 = st.columns(2)
    amt = c4.number_input(f"外幣金額({cur})", 0.0, 1e12, 1000.0, step=100.0, key="bank_amt")
    twd = amt * rate
    m = 1 / mid[cur] if mid and mid.get(cur) else None
    gap = f"比中間價多付約 NT$ {twd - amt * m:,.0f}({(rate / m - 1) * 100:+.2f}%)" if m and buying else (
        f"比中間價少拿約 NT$ {amt * m - twd:,.0f}({(rate / m - 1) * 100:+.2f}%)" if m else "")
    c4.markdown(f"<div class='card'><div class='cs'>{'需要準備' if buying else '可以換回'}</div><div class='big' style='color:var(--ac)'>NT$ {twd:,.0f}</div>"
                f"<div class='cs'>匯率 {rate:g}(銀行{'賣出' if buying else '買入'}價)<br>{gap}</div></div>", unsafe_allow_html=True)
    ntd = c5.number_input("或:我有台幣(NT$)", 0.0, 1e12, 10000.0, step=1000.0, key="bank_twd")
    c5.markdown(f"<div class='card'><div class='cs'>{'可以換到' if buying else '需要賣出'}</div><div class='big'>{ntd / rate:,.2f} <small>{cur}</small></div>"
                f"<div class='cs'>以同一個匯率 {rate:g} 計算</div></div>", unsafe_allow_html=True)
    st.markdown("##### 全部幣別牌告")
    tbl = [(fx_label(c), *(rates[c].get("cash") or (None, None)), *(rates[c].get("spot") or (None, None))) for c in codes]
    st.dataframe(pd.DataFrame(tbl, columns=["幣別", "現鈔買入", "現鈔賣出", "即期買入", "即期賣出"]), hide_index=True, width="stretch")
    st.caption(f"📡 {b['bank']}牌告　・查詢 {b['time']}　・「買入」是銀行跟你買(你賣外幣),「賣出」是銀行賣給你(你買外幣)。"
               "臺灣銀行網站有防機器人驗證,這裡改用其他公股/大型銀行,各行庫牌告差距通常很小。")


# ════════════════════════════════════════════════════════════════════
#  🧾 發票 QR 掃描(發票頁的分頁)
# ════════════════════════════════════════════════════════════════════
def _check_scanned(inv, ps):
    roc, m_end = L.invoice_period_title(inv["date"]) if inv["date"] else (None, None)
    p = next((x for x in ps if x.get("roc") == roc and x.get("m_end") == m_end), None)
    period = f"{roc}年{m_end - 1:02d}-{m_end:02d}月" if roc else "?"
    if not p:
        newest = max(((x.get("roc"), x.get("m_end")) for x in ps), default=(0, 0))
        if roc and (roc, m_end) > newest:
            draw = date(roc + 1911 + (m_end == 12), (m_end % 12) + 1, 25)
            return period, "⏳ 尚未開獎", "", f"{draw.month}/{draw.day} 開獎"
        return period, "—", "", "期別太舊,已不在財政部清單"
    r = K.check_invoice(inv["number"], p["special"], p["grand"], p["first"], p["extra"])
    expired = K.tw_now().date().isoformat() > p["claim_end"]
    return period, ("🎉 " if r["ok"] else "") + r["prize"], f"{r['amount']:,}" if isinstance(r["amount"], (int, float)) and r["amount"] else (r["amount"] or ""), r["note"] + ("(已過領獎期限)" if r["ok"] and expired else "")


def invoice_scan_view(ps):
    ss = st.session_state
    scanned = ss.setdefault("inv_scanned", {})
    n = ss.setdefault("inv_cam_n", 0)
    st.caption("對準電子發票**左邊**的 QR Code 拍照(兩個一起拍也可以)。會自動讀出號碼和日期,對到正確的期別。")
    c1, c2 = st.columns(2)
    with c1:
        cam_on = st.toggle("📷 開啟相機掃描", key="inv_cam_on", help="開啟後瀏覽器會詢問是否允許使用相機")
        shot = st.camera_input("對準發票左邊的 QR Code 後按下拍照", key=f"inv_cam_{n}") if cam_on else None
    ups = c2.file_uploader("🖼️ 或上傳發票照片(可多選)", ["jpg", "jpeg", "png", "webp"], accept_multiple_files=True, key="inv_up")
    done = ss.setdefault("inv_done_files", set())
    imgs = ([("cam", shot)] if shot else []) + [(f"up_{f.file_id}", f) for f in ups or []]
    fails = 0
    for fid, f in imgs:
        if fid != "cam" and fid in done:
            continue
        done.add(fid)
        try:
            texts = L.decode_qr_texts(f.getvalue())
        except ImportError:
            st.error("伺服器沒有安裝 opencv-python-headless,無法解析 QR Code。")
            return
        found = [x for x in (L.parse_invoice_qr(t) for t in texts) if x]
        if not found:
            fails += 1
        for x in found:
            scanned[x["track"] + x["number"]] = x
    if shot:  # 拍完一張就換新的相機元件,方便連續拍
        ss["inv_cam_n"] = n + 1
        if not fails:
            st.rerun()
    if fails:
        st.warning("有照片沒讀到發票 QR Code:請拍近一點、對焦清楚、避免反光,或只拍左邊那個 QR Code。")
    if not scanned:
        st.info("還沒有掃描到發票")
        return
    rows = []
    for k, inv in reversed(list(scanned.items())):
        period, res, amt, note = _check_scanned(inv, ps)
        rows.append((inv["track"] + "-" + inv["number"], inv["date"].strftime("%Y/%m/%d") if inv["date"] else "", period, res, amt, note))
    wins = [r for r in rows if r[3].startswith("🎉")]
    if wins:
        st.balloons()
        st.success(f"中獎 {len(wins)} 張!" + "、".join(f"{r[0]} {r[3][2:]}" for r in wins))
    st.dataframe(pd.DataFrame(rows, columns=["發票號碼", "日期", "期別", "結果", "獎金", "說明"]), hide_index=True, width="stretch")
    st.caption(f"已掃描 {len(scanned)} 張(重複的會自動略過)")
    if st.button("🗑️ 清除清單"):
        ss["inv_scanned"] = {}
        ss["inv_done_files"] = set()
        st.rerun()


# ════════════════════════════════════════════════════════════════════
#  ⚙️ 設定與診斷
# ════════════════════════════════════════════════════════════════════
def _import_prefs():
    f = st.session_state.get("prefs_up")
    if not f:
        return
    try:
        data = json.loads(f.getvalue().decode("utf-8"))
        if not isinstance(data, dict):
            raise ValueError
        U.replace_prefs({**U.prefs(), **data})
        st.session_state["prefs_msg"] = f"✅ 已匯入 {len(data)} 項設定"
    except Exception:  # noqa: BLE001
        st.session_state["prefs_msg"] = "⚠️ 檔案格式不正確"


def _reset_prefs():
    U.replace_prefs({})
    st.session_state["_prefs_reset"] = True
    st.session_state.pop("wheels", None)
    st.session_state["prefs_msg"] = "🗑️ 已清除這台裝置上的所有設定"


def page_settings(extra_tests: dict):
    hero("⚙️", "設定與診斷", "備份/還原你的設定・檢查各資料來源是否正常")
    P = U.prefs()
    st.markdown("#### 💾 我的設定")
    st.write("自選股、轉盤、常去戲院、預設城市等設定會**自動存在這台裝置的瀏覽器裡**,重新整理或關掉再開都還在,也不會被別人看到。"
             "換手機或換瀏覽器時,先在舊裝置「匯出」,再到新裝置「匯入」即可。")
    summ = [("⭐ 自選股", f"{len(P.get('watch') or [])} 檔"), ("🎡 轉盤", f"{len(P.get('wheels') or {})} 個"),
            ("🎬 常去戲院", f"{len(P.get('fav_cinemas') or [])} 間"), ("⛅ 預設城市", P.get("city") or "—"),
            ("🌫️ 空品縣市", P.get("aqi_county") or "—"), ("🅿️ 停車行政區", P.get("park_area") or "—")]
    st.markdown("<div class='tiles'>" + "".join(f"<div class='tile' style='min-height:0'><span class='tl'>{a}</span><span class='tv' style='font-size:1.2rem'>{_esc(b)}</span></div>"
                                                for a, b in summ) + "</div>", unsafe_allow_html=True)
    if not U.prefs_ready():
        st.caption("⏳ 正在讀取瀏覽器中的設定…")
    c1, c2, c3 = st.columns(3)
    c1.download_button("⬇️ 匯出設定", json.dumps(P, ensure_ascii=False, indent=1).encode("utf-8"), "生活助手設定.json", "application/json")
    c2.file_uploader("⬆️ 匯入設定", ["json"], key="prefs_up", on_change=_import_prefs, label_visibility="collapsed")
    c3.button("🗑️ 清除所有設定", on_click=_reset_prefs)
    msg = st.session_state.pop("prefs_msg", "")
    if msg:
        st.info(msg)
    with st.expander("🔑 進階:API 金鑰(選填)"):
        st.write("空氣品質預設使用政府資料開放平臺公告的公開下載連結。若想用自己的金鑰,"
                 "可在環境變數或 `.streamlit/secrets.toml` 設定 `MOENV_API_KEY`(到環境部資料開放平臺免費申請)。")

    st.markdown("#### 🔧 連線診斷")
    st.caption("確認伺服器能否連到各資料來源(部署到國外主機時,有些台灣網站會擋海外 IP)")
    if st.button("開始測試", type="primary"):
        tests = {**extra_tests,
                 "停車(台北市)": lambda: f"{len(L.fetch_parking_avail()[0])} 筆即時",
                 "空氣品質(環境部)": lambda: f"{len(L.fetch_aqi())} 站",
                 "警特報(氣象署)": lambda: f"{len(L.fetch_cwa_warnings())} 則",
                 "地震(氣象署)": lambda: f"{len(L.fetch_earthquakes())} 筆",
                 "颱風(氣象署)": lambda: f"{len(L.fetch_typhoons())} 個",
                 "停班停課(人事總處)": lambda: f"{len(L.fetch_closures()[0])} 則",
                 "行事曆": lambda: f"{len(L.fetch_calendar(K.tw_now().year))} 天",
                 "銀行牌告": lambda: L.fetch_bank_rates()["bank"],
                 "自選股報價(證交所)": lambda: f"{len(L.fetch_quotes(['0050', '2330']))} 檔",
                 "除權息預告": lambda: f"{len(L.fetch_dividends())} 筆"}
        prog = st.progress(0.0)
        for i, (name, fn) in enumerate(tests.items(), 1):
            try:
                st.success(f"✅ {name}:{fn()}")
            except Exception as e:  # noqa: BLE001
                st.error(f"❌ {name}:{type(e).__name__}: {str(e)[:150]}")
            prog.progress(i / len(tests))
        try:
            import cv2  # noqa: F401
            st.success("✅ 發票 QR 解碼(OpenCV)已安裝")
        except ImportError:
            st.error("❌ 沒有安裝 opencv-python-headless,發票掃描無法使用")
