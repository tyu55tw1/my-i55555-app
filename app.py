# -*- coding: utf-8 -*-
"""🧰 全方位生活助手 — Streamlit 版。  執行:streamlit run app.py"""
import io
import random
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import pandas as pd
import base64
import html as _html
import json
import time

import streamlit as st

import core as K
import shop as S
import wheel as W
from streamlit.components.v1 import html as components_html

st.set_page_config(page_title="全方位生活助手", page_icon="🧰", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>
:root{--soft:rgba(128,128,128,.11);--line:rgba(128,128,128,.28);--ac:#d9441a}
.block-container{padding:1.1rem 1.2rem 3.5rem;max-width:1100px}
section[data-testid=stSidebar],[data-testid=stSidebarCollapsedControl],[data-testid=collapsedControl]{display:none}
header[data-testid=stHeader]{background:transparent}footer{visibility:hidden}
.topbar{display:flex;align-items:center;gap:10px;margin:0 0 4px;font-size:1.2rem;font-weight:800}
.topbar small{font-weight:500;opacity:.55;font-size:.78rem}
.hero{display:flex;align-items:center;gap:16px;background:linear-gradient(120deg,#ff6b3d,#ff9a5c 55%,#f5c542);padding:18px 24px;border-radius:22px;margin:10px 0 18px;color:#fff;box-shadow:0 10px 28px rgba(255,107,61,.28)}
.hero h1{margin:0;font-size:1.65rem;color:#fff;padding:0}.hero p{margin:2px 0 0;opacity:.95;color:#fff}.hero .ico{font-size:2.6rem;filter:drop-shadow(0 2px 4px rgba(0,0,0,.25))}
div[data-testid=stMetric]{background:var(--soft);border:1px solid var(--line);border-radius:16px;padding:12px 16px}
div[data-testid=stMetricLabel] p{opacity:.72;font-size:.85rem}div[data-testid=stMetricValue]{font-weight:800}
div[data-testid=stVerticalBlockBorderWrapper]{border-radius:16px}
.stButton>button,.stDownloadButton>button,.stLinkButton>a{border-radius:12px;font-weight:700;min-height:2.6rem}
button[data-baseweb=tab]{font-weight:700}
div[data-testid=stPills] button,div[data-testid=stPills] [role=button]{border-radius:999px!important;font-weight:700}
.pgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(168px,1fr));gap:10px;margin:8px 0 14px}
.pcard{display:flex;flex-direction:column;gap:4px;padding:10px;border-radius:14px;background:var(--soft);border:1px solid var(--line);color:inherit!important;text-decoration:none!important}
.pcard.best{border:2px solid var(--ac)}.pcard img{width:100%;aspect-ratio:1;object-fit:contain;border-radius:10px;background:#fff}
.pp{font-weight:800;font-size:1.15rem;color:var(--ac)}.pt{font-size:.82rem;line-height:1.3;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.pb{font-size:.74rem;opacity:.7}
.fcard{display:flex;gap:12px;background:var(--soft);border:1px solid var(--line);border-radius:16px;padding:12px;margin:0 0 10px}
.fcard img{width:84px;height:122px;object-fit:cover;border-radius:10px;flex:none}.fb{min-width:0;flex:1}
.ft{font-weight:800;font-size:1.05rem;line-height:1.3}.ft a{color:inherit;text-decoration:none}.fm{opacity:.75;font-size:.85rem;margin:3px 0 4px}
.lab{color:var(--ac);font-weight:800;font-size:.85rem;margin-top:6px}.tk{display:inline-block;margin-top:8px;color:var(--ac);font-weight:700;text-decoration:none}
.chip{display:inline-block;padding:4px 12px;margin:3px 5px 3px 0;border-radius:10px;background:var(--soft);border:1px solid var(--line);color:inherit;font-weight:700;font-size:.92rem}
.chip.past{opacity:.38}.chip.next{background:var(--ac);border-color:var(--ac);color:#fff;opacity:1}
.badge{display:inline-block;padding:1px 9px;border-radius:7px;color:#fff;font-size:.78rem;font-weight:700;margin-right:6px}
.ball{display:inline-grid;place-items:center;width:38px;height:38px;border-radius:50%;background:var(--ac);color:#fff;font-weight:700;margin:3px;box-shadow:0 2px 6px rgba(217,68,26,.35)}
.ball.z{background:#2f7de1;box-shadow:0 2px 6px rgba(47,125,225,.35)}
@media(max-width:640px){.fcard{padding:10px;gap:10px}.fcard img{width:62px;height:90px}.ft{font-size:1rem}
div[data-testid=stHorizontalBlock]{flex-wrap:wrap!important;gap:.5rem!important}
div[data-testid=stColumn],div[data-testid=column]{min-width:calc(50% - .5rem)!important;flex:1 1 calc(50% - .5rem)!important}
div[data-testid=stPills]>div,div[data-testid=stPills] [data-testid=stButtonGroup]{flex-wrap:nowrap!important;overflow-x:auto;-webkit-overflow-scrolling:touch;padding-bottom:4px}
div[data-testid=stPills] button{white-space:nowrap;flex:none}.block-container{padding:.7rem .65rem 3rem}.hero{padding:13px 15px;border-radius:18px;gap:11px}.hero .ico{font-size:2rem}.hero h1{font-size:1.2rem}.hero p{font-size:.8rem}
.ball{width:31px;height:31px;font-size:.82rem;margin:2px}.chip{padding:3px 9px;font-size:.86rem}div[data-testid=stMetric]{padding:8px 11px}div[data-testid=stMetricValue]{font-size:1.35rem}.topbar small{display:none}}
</style>""", unsafe_allow_html=True)

PAGES = ["🎬 電影時刻", "⛅ 天氣", "⛽ 油價", "📈 股票", "💱 匯率", "🧾 發票對獎", "🎰 賓果", "🏆 樂透", "🤖 AI 下注顧問", "📸 大頭照", "🛒 比價", "🎡 幸運轉盤", "🔧 連線診斷"]
st.markdown("<div class='topbar'>🧰 全方位生活助手 <small>電影・天氣・油價・股票・匯率・發票・賓果・樂透</small></div>", unsafe_allow_html=True)
_cur = st.session_state.get("pg", PAGES[0])
if hasattr(st, "pills"):
    page = st.pills("功能", PAGES, default=_cur, label_visibility="collapsed", key="nav_pills") or _cur
else:
    page = st.radio("功能", PAGES, index=PAGES.index(_cur), horizontal=True, label_visibility="collapsed")
st.session_state["pg"] = page


_esc = lambda x: _html.escape(str(x), quote=True).replace("$", "&#36;")


def hero(icon, title, sub=""):
    st.markdown(f"<div class='hero'><span class='ico'>{icon}</span><div><h1>{title}</h1><p>{sub}</p></div></div>", unsafe_allow_html=True)


def balls(nums, z=None):
    h = "".join(f"<span class='ball'>{n:02d}</span>" for n in nums)
    return h + (f"<b> + </b><span class='ball z'>{z:02d}</span>" if z else "")


def safe(fn, *a, **k):
    try:
        return fn(*a, **k)
    except Exception as e:  # noqa: BLE001
        st.error(f"連線失敗:{type(e).__name__}:{e}")
        return None


# ── 快取包裝(避免重複請求外部網站) ──
@st.cache_resource
def mclient():
    return K.MovieClient(ttl=300)


@st.cache_data(ttl=300, show_spinner="讀取戲院清單…")
def cinemas(code):
    return mclient().list_cinemas(code)


@st.cache_data(ttl=300, show_spinner="讀取場次…")
def schedule(cid, area, name):
    return mclient().get_schedule(K.Cinema(cid, area, name))


@st.cache_data(ttl=300, show_spinner="掃描各戲院場次(第一次約需數秒)…")
def scan(code):
    cs = cinemas(code)

    def one(c):
        try:
            return c.cid, schedule(c.cid, c.area, c.name)
        except Exception:  # noqa: BLE001
            return c.cid, None

    with ThreadPoolExecutor(4) as ex:  # 並行太高會被網站限流,導致部分戲院抓不到
        res = dict(ex.map(one, cs))
    for c in cs:  # 失敗的再逐間重試一次
        if res.get(c.cid) is None:
            time.sleep(0.5)
            res[c.cid] = one(c)[1]
    return {k: v for k, v in res.items() if v}, [c.name for c in cs if not res.get(c.cid)]


weather = st.cache_data(ttl=600, show_spinner="取得氣象…")(K.fetch_weather)
oil = st.cache_data(ttl=1800, show_spinner="取得牌價…")(K.fetch_oil)
stock = st.cache_data(ttl=20, show_spinner="取得報價…")(K.fetch_stock)
rates = st.cache_data(ttl=1800, show_spinner="取得匯率…")(K.fetch_rates)
invoices = st.cache_data(ttl=3600, show_spinner="取得財政部號碼…")(K.fetch_invoice_periods)
bingo_draws = st.cache_data(ttl=300, show_spinner="取得賓果開獎…")(K.fetch_bingo)



@st.cache_resource
def poster_store():
    return {}


_PH = "data:image/svg+xml;base64," + base64.b64encode(
    "<svg xmlns='http://www.w3.org/2000/svg' width='84' height='122'><rect width='100%' height='100%' rx='10' fill='#8884'/>"
    "<text x='50%' y='56%' font-size='34' text-anchor='middle'>🎬</text></svg>".encode()).decode()


def _img_uri(content, box):
    im = K.Image.open(io.BytesIO(content)).convert("RGB")
    im.thumbnail(box)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=78)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def _try_img(sess, url, box, referer):
    try:
        r = K.http_get(url, session=sess, timeout=(4, 8), headers={"Referer": referer})
        return _img_uri(r.content, box) if len(r.content) >= 500 else ""
    except Exception:  # noqa: BLE001
        return ""


def _poster_from_page(sess, fid):
    """標準海報網址都抓不到時(例如特殊片、重映片),讀電影介紹頁,取出官方海報網址。"""
    try:
        r = K.http_get(f"{K.BASE}/movie/{fid}/", session=sess, timeout=(4, 8), headers={"Referer": K.BASE + "/"})
        soup = K.BeautifulSoup(r.text, "html.parser")
        og = soup.find("meta", attrs={"property": "og:image"})
        cands = [og.get("content")] if og and og.get("content") else []
        for i in soup.find_all("img"):
            src = i.get("src") or i.get("data-src") or ""
            if fid in src or K.re.search(r"/photo\d*/", src):
                cands.append(src)
        return [K.urljoin(K.BASE, c) for c in cands if c]
    except Exception:  # noqa: BLE001
        return []


def _fetch_poster(sess, fid, url):
    cands = []
    if url:
        cands.append(("https:" + url) if url.startswith("//") else url.replace("http://", "https://", 1))
    for sz in ("pl", "pm"):
        for ext in ("jpg", "png"):
            cands.append(f"{K.BASE}/photo101/{fid}/{sz}_{fid}.{ext}")
    for u in dict.fromkeys(cands):  # ① 頁面給的網址 → ② 標準海報網址
        uri = _try_img(sess, u, (168, 244), K.BASE + "/")
        if uri:
            return uri
    for u in dict.fromkeys(_poster_from_page(sess, fid)[:3]):  # ③ 讀電影介紹頁找海報
        uri = _try_img(sess, u, (168, 244), K.BASE + "/")
        if uri:
            return uri
    return _PH


_PH_PROD = "data:image/svg+xml;base64," + base64.b64encode(
    "<svg xmlns='http://www.w3.org/2000/svg' width='200' height='200'><rect width='100%' height='100%' fill='#8883'/>"
    "<text x='50%' y='58%' font-size='64' text-anchor='middle'>🛍️</text></svg>".encode()).decode()


def img_uris(urls, box=(240, 240)):
    """商品圖:伺服器端抓取並內嵌(避免防盜連結),失敗 10 分鐘後重試。"""
    store, now = poster_store(), time.time()
    urls = [u for u in dict.fromkeys(urls) if u]
    todo = [u for u in urls if u not in store or (not store[u][0] and now - store[u][1] > 600)]
    if todo:
        with ThreadPoolExecutor(8) as ex:
            for u, uri in ex.map(lambda x: (x, _try_img(S._S, x, box, "https://www.google.com/")), todo):
                store[u] = (uri, time.time())
    return {u: store[u][0] or _PH_PROD for u in urls}


def poster_uris(shows):
    store, now = poster_store(), time.time()
    todo = [(x.film_id, x.poster) for x in shows if x.film_id not in store or (store[x.film_id][0] == _PH and now - store[x.film_id][1] > 600)]
    if todo:
        sess = mclient().session
        with ThreadPoolExecutor(8) as ex:
            for fid, uri in ex.map(lambda t: (t[0], _fetch_poster(sess, *t)), todo):
                store[fid] = (uri, time.time())
    return {x.film_id: store[x.film_id][0] for x in shows}


@st.cache_data(ttl=600, show_spinner=False)
def compare_cached(kw, plats, good):
    return S.compare(kw, plats, good)


def sessions_html(sessions, day):
    now, first, h = K.tw_now(), True, ""
    for s in sessions:
        if s.label:
            h += f"<div class='lab'>{_esc(s.label)}</div>"
        for t in s.times:
            past = K.is_past(day, t, now)
            cls = "past" if past else ("next" if first and day == now.strftime("%Y/%m/%d") else "")
            first = first and (past or cls == "")
            h += f"<span class='chip {cls}'>{t}</span>"
    return h


def card_html(title, url, meta, body, poster="", extra=""):
    img = f"<img src='{_esc(poster)}' loading='lazy'>" if poster else ""
    return (f"<div class='fcard'>{img}<div class='fb'><div class='ft'><a href='{_esc(url)}' target='_blank'>{_esc(title)}</a></div>"
            f"<div class='fm'>{meta}</div>{body}{extra}</div></div>")


def film_meta(rating, dur):
    name, col = K.RATINGS.get(rating, ("", "#444"))
    return (f"<span class='badge' style='background:{col}'>{name}</span>" if name else "") + (f"⏱ {dur} 分" if dur else "")



def _wheels():
    return st.session_state.setdefault("wheels", {k: list(v) for k, v in W.PRESETS.items()})


def save_wheel():
    ss = st.session_state
    items = W.parse_lines(ss.get(f"wta_{ss.get('wheel_pick')}", ""))
    name = (ss.get("wheel_new") or "").strip()[:20]
    if name and items:
        _wheels()[name] = items
        ss["wheel_pick"] = name
        ss["wheel_msg"] = f"✅ 已儲存「{name}」({len(items)} 個選項)"
    else:
        ss["wheel_msg"] = "⚠️ 請輸入轉盤名稱,並至少一個選項"


def delete_wheel():
    ss, w = st.session_state, _wheels()
    if len(w) > 1:
        w.pop(ss.get("wheel_pick"), None)
        ss["wheel_pick"] = next(iter(w))
        ss["wheel_msg"] = "🗑️ 已刪除"


def import_wheels():
    ss, f = st.session_state, st.session_state.get("wheel_up")
    try:
        data = json.loads(f.getvalue().decode("utf-8"))
        n = 0
        for name, items in data.items():
            parsed = [(str(i[0]), float(i[1])) if isinstance(i, (list, tuple)) else (str(i), 1.0) for i in items][:60]
            if parsed:
                _wheels()[str(name)[:20]] = parsed
                n += 1
        ss["wheel_msg"] = f"✅ 已匯入 {n} 個轉盤"
    except Exception as e:  # noqa: BLE001
        ss["wheel_msg"] = f"⚠️ 匯入失敗:{type(e).__name__}"


# ═════════ 各頁 ═════════
if page == PAGES[0]:
    hero("🎬", "電影時刻", "全台戲院場次・已開演的場次變暗・橘色是下一場")
    c1, c2, c3 = st.columns([2, 2, 1])
    region = c1.selectbox("地區", list(K.REGIONS))
    mode = c2.radio("查詢方式", ["依戲院", "依電影"], horizontal=True)
    if c3.button("🔄 重新整理"):
        st.cache_data.clear()
        st.rerun()
    flt = st.text_input("🔍 篩選", placeholder="輸入電影或戲院名稱").strip().casefold()
    cs = safe(cinemas, K.REGIONS[region])
    if cs:
        if mode == "依戲院":
            pool = [x for x in cs if flt in x.name.casefold()] or cs
            st.caption(f"符合 {len(pool)} 間戲院")
            c = pool[st.selectbox("戲院", range(len(pool)), format_func=lambda i: pool[i].name)]
            b1, b2, b3 = st.columns(3)
            if c.site:
                b1.link_button("🌐 官方網站", c.site)
            if c.ticket:
                b2.link_button("🎟️ 線上訂票", c.ticket)
            b3.link_button("📄 開眼頁面", c.url)
            sch = safe(schedule, c.cid, c.area, c.name)
            if sch:
                st.caption(f"📍 {c.address}　☎ {c.phone}　・網站更新:{sch.updated or '—'}")
                if not sch.days:
                    st.info("這間戲院目前沒有場次資料(可能整修或網站尚未更新)")
                else:
                    labels = {d.short: d for d in sch.days}
                    day = labels[st.radio("日期", list(labels), horizontal=True)]
                    shows = [s for s in day.shows if not flt or flt in s.title.casefold() or flt in c.name.casefold()]
                    st.caption(f"共 {len(shows)} 部電影")
                    with st.expander("📋 解析到的電影清單(與官網不符時請參考)"):
                        st.write("、".join(f"{x.title}({sum(len(z.times) for z in x.sessions)}場)" for x in day.shows))
                    with st.spinner("載入海報…"):
                        uris = poster_uris(shows)
                    for sh in shows:
                        st.markdown(card_html(sh.title, sh.url, film_meta(sh.rating, sh.duration),
                                              sessions_html(sh.sessions, day.key), uris[sh.film_id]), unsafe_allow_html=True)
        else:
            got = safe(scan, K.REGIONS[region])
            if got:
                res, failed = got
                if failed:
                    st.warning(f"有 {len(failed)} 間戲院這次沒抓到({'、'.join(failed[:5])}{'…' if len(failed) > 5 else ''}),部分電影可能沒有顯示。按上方「🔄 重新整理」可重試。")
                idx = K.build_index({c.cid: res[c.cid] for c in cs if c.cid in res})
                films = sorted(idx.values(), key=lambda f: (-len(f.by_cinema), f.title))
                films = [f for f in films if flt in f.title.casefold()] or films
                st.caption(f"符合 {len(films)} 部電影")
                f = films[st.selectbox("電影", range(len(films)), format_func=lambda i: f"{films[i].title}({len(films[i].by_cinema)}間)")]
                meta = " ・ ".join(x for x in (f"片長 {f.duration} 分" if f.duration else "", K.RATINGS.get(f.rating, ("",))[0]) if x)
                st.subheader(f"🎞️ {f.title}")
                st.caption(meta)
                st.link_button("📄 電影介紹", f.url)
                days = sorted({d for m in f.by_cinema.values() for d in m})
                day = st.radio("日期", days, horizontal=True)
                cmap = {c.cid: c for c in cs}
                for cid, m in f.by_cinema.items():
                    if day in m and cid in cmap:
                        c = cmap[cid]
                        tk = f"<a class='tk' href='{_esc(c.ticket)}' target='_blank'>🎟️ 線上訂票</a>" if c.ticket else ""
                        st.markdown(card_html(c.name, c.url, _esc(c.address), sessions_html(m[day], day), extra=tk), unsafe_allow_html=True)
elif page == PAGES[1]:
    hero("⛅", "天氣", "目前天氣・體感・紫外線・未來三天與穿衣建議")
    cities = {"台北": "Taipei", "新北": "New Taipei", "桃園": "Taoyuan", "台中": "Taichung", "台南": "Tainan",
              "高雄": "Kaohsiung", "新竹": "Hsinchu", "花蓮": "Hualien", "其他城市": ""}
    c1, c2 = st.columns([1, 2])
    pick = c1.selectbox("快速選城市", list(cities))
    q = c2.text_input("或輸入任何城市(英文名)", cities[pick] or "Tokyo").strip() or "Taipei"
    d = safe(weather, q)
    if d:
        place = pick if cities[pick] else K.AREA_ZH.get(q, d["area"] or q)  # 常用城市一律顯示中文名
        st.subheader(f"{d['icon']} {place}・{d['desc']}")
        a, b, c, e = st.columns(4)
        a.metric("🌡️ 氣溫", f"{d['temp']}°C"); b.metric("🥵 體感", f"{d['feel']}°C")
        c.metric("☔ 今日降雨機率", f"{d['rain']}%"); e.metric("💧 濕度", f"{d['humid']}%")
        a, b, c = st.columns(3)
        a.metric("💨 風速", f"{d['wind']} km/h"); b.metric("🧴 紫外線指數", d["uv"]); c.metric("👁️ 能見度", f"{d['vis']} km")
        st.info(K.clothing_advice(K._to_int(d["feel"]), d["rain"], K._to_int(d["uv"])))
        st.markdown("##### 未來三天")
        for col, day in zip(st.columns(max(len(d["days"]), 1)), d["days"]):
            with col.container(border=True):
                st.markdown(f"**{day['icon']} {day['label']}**")
                st.metric("溫度", f"{day['lo']}° ~ {day['hi']}°", f"☔ {day['rain']}%", delta_color="off")
                st.caption(day["desc"])
elif page == PAGES[2]:
    hero("⛽", "油價", "台灣中油最新牌價與加油試算")
    d = safe(oil)
    if d:
        st.caption(f"牌價日期 {d['date']} ・ {d['src']}")
        for col, name, p, pv in zip(st.columns(4), K.OIL_NAMES, d["prices"], d["prev"] or [None] * 4):
            col.metric(name, f"{p:.1f}", f"{p - pv:+.1f}" if pv else None, delta_color="inverse")
        lit = st.number_input("加油量(公升)", 1.0, 200.0, 30.0)
        st.success("  |  ".join(f"{n.split()[0]}:{lit * p:,.0f} 元" for n, p in zip(K.OIL_NAMES, d["prices"])))

elif page == PAGES[3]:
    hero("📈", "股票", "收盤價以臺灣證券交易所為準(即時+日成交),Yahoo 僅備援")
    quick = {"自行輸入": "", "0050 元大台灣50": "0050", "0056 元大高股息": "0056", "00878 國泰永續高股息": "00878",
             "2330 台積電": "2330", "2317 鴻海": "2317", "2454 聯發科": "2454"}
    c1, c2, c3 = st.columns([2, 1, 2])
    qk = c1.selectbox("常用", list(quick))
    code = c2.text_input("代號", quick[qk] or "0050").strip()
    rng = c3.radio("區間", list(K.STOCK_RANGES), horizontal=True, index=1)
    auto = st.toggle("⏱️ 自動更新(30 秒)") if hasattr(st, "toggle") else False

    def stock_view():
        d = safe(stock, code, K.STOCK_RANGES[rng])
        if not d:
            return
        diff = d["price"] - d["prev"]
        st.subheader(f"{d['code']}　{d['name']}")
        a, b, c, e = st.columns(4)
        a.metric("成交 / 收盤", f"{d['price']:,.2f}", f"{diff:+.2f} ({diff / d['prev'] * 100:+.2f}%)" if d["prev"] else None, delta_color="inverse")
        b.metric("今日高 / 低", f"{d['high'] or '--'} / {d['low'] or '--'}")
        c.metric("成交量(張)", f"{d['volume']:,.0f}" if d["volume"] else "--")
        e.metric("昨收", f"{d['prev']:,.2f}")
        a, b = st.columns(2)
        a.metric("52 週高", f"{d['hi52']:,.2f}" if d["hi52"] else "--"); b.metric("52 週低", f"{d['lo52']:,.2f}" if d["lo52"] else "--")
        st.caption(f"📡 {d['src']}　・資料時間 {d['asof'] or '—'}　・查詢 {K.tw_now():%H:%M:%S}")
        if len(d["values"]) > 1:
            st.line_chart(pd.DataFrame({"收盤價": d["values"]}, index=d["labels"]), color="#ff6b3d")

    if auto and hasattr(st, "fragment"):
        st.fragment(run_every=30)(stock_view)()
    else:
        stock_view()
        if st.button("🔄 重新整理"):
            st.cache_data.clear()
            st.rerun()
elif page == PAGES[4]:
    hero("💱", "匯率", "多幣別即時換算")
    d = safe(rates)
    if d:
        c1, c2 = st.columns(2)
        amt = c1.number_input("金額", 0.0, 1e12, 1000.0)
        base = c2.selectbox("幣別", [f"{c} {n}" for c, _, n in K.FX_CURRENCIES]).split()[0]
        st.caption(f"匯率日期 {d['date']}")
        cols = st.columns(4)
        for i, (code, flag, name) in enumerate(x for x in K.FX_CURRENCIES if x[0] != base):
            v = K.fx_convert(amt, base, code, d["rates"])
            cols[i % 4].metric(f"{flag} {code} {name}", f"{v:,.0f}" if code in ("VND", "KRW") else f"{v:,.2f}",
                               f"1 {base} = {K.fx_convert(1, base, code, d['rates']):,.4f}", delta_color="off")

elif page == PAGES[5]:
    hero("🧾", "統一發票對獎", "自動取得財政部最新中獎號碼,免手動輸入")
    ps = safe(invoices)
    if ps:
        p = ps[st.selectbox("期別", range(len(ps)), format_func=lambda i: ps[i]["title"])]
        st.caption(f"領獎期間 {p['claim_start']} ~ {p['claim_end']}" + ("  ⚠️ 已過期" if K.tw_now().date().isoformat() > p["claim_end"] else ""))
        a, b = st.columns(2)
        a.metric("特別獎 1,000萬", p["special"][0]); b.metric("特獎 200萬", p["grand"][0])
        st.metric("頭獎 20萬", "   ".join(p["first"]))
        extra = p["extra"] + K.split_numbers(st.text_input("增開六獎(網站未列出時可補,3 碼)", ""), 3)
        txt = st.text_area("輸入發票號碼(每行一張,8 碼或末 3 碼)", height=120)
        toks = [t for t in K.re.split(r"[\s,;、]+", txt.strip()) if K.re.sub(r"\D", "", t)]
        if toks:
            rows = [(K.re.sub(r"\D", "", t), *(lambda r: (("🎉 " if r["ok"] else "") + r["prize"], r["amount"] or "", r["note"]))(
                K.check_invoice(t, p["special"], p["grand"], p["first"], extra))) for t in toks]
            st.dataframe(pd.DataFrame(rows, columns=["號碼", "結果", "獎金", "說明"]), hide_index=True)

elif page == PAGES[6]:
    hero("🎰", "賓果", "開獎統計・選號・回測・精確機率(統計無法預測下一期)")
    draws = safe(bingo_draws)
    t1, t2, t3 = st.tabs(["📊 統計與選號", "🧪 回測", "🧮 機率與期望值"])
    stars = 3
    with t1:
        if draws:
            c1, c2, c3 = st.columns(3)
            P = c1.slider("統計期數", 5, len(draws), min(50, len(draws)))
            stars = c2.slider("星數", 1, 10, 3)
            pick_mode = c3.radio("選號方式", ["策略自動", "手動選號"], horizontal=True)
            fr = K.bingo_freq(draws, P)
            rank = sorted(range(1, 81), key=lambda n: (-fr.get(n, 0), n))
            om = K.bingo_omission(draws)
            st.bar_chart(pd.DataFrame({"次數": [fr.get(n, 0) for n in range(1, 81)]}, index=[f"{n:02d}" for n in range(1, 81)]), color="#ff6b3d")
            h1, h2, h3 = st.columns(3)
            h1.markdown("**🔥 熱門前 10**<br>" + balls(rank[:10]), unsafe_allow_html=True)
            h2.markdown("**❄️ 冷門前 10**<br>" + balls(sorted(rank[-10:])), unsafe_allow_html=True)
            h3.markdown("**⏳ 遺漏最久前 10**<br>" + balls(sorted(sorted(om, key=lambda n: (-om[n], n))[:10])), unsafe_allow_html=True)
            if pick_mode == "策略自動":
                strategies = {"🔥 追擊熱門": "hot", "❄️ 抄底冷門": "cold", "⚖️ 冷熱平衡": "mix", "⏳ 遺漏最久": "omit", "🎲 完全隨機": "random"}
                picks = K.bingo_pick(draws, strategies[st.selectbox("選號策略", list(strategies))], stars, P)
            else:
                picks = sorted(st.multiselect(f"選號盤(最多 {stars} 個)", list(range(1, 81)), max_selections=stars, format_func=lambda n: f"{n:02d}"))
            st.markdown("**你的號碼**<br>" + (balls(picks) if picks else "尚未選號"), unsafe_allow_html=True)
            st.session_state["bingo_picks"] = picks
    with t2:
        picks = st.session_state.get("bingo_picks", [])
        if draws and picks:
            N = st.select_slider("回測最近幾期", [10, 20, 50, 100], 20)
            bt = K.bingo_backtest(draws, picks, min(N, len(draws)))
            a, b, c, d = st.columns(4)
            a.metric("回測期數", bt["n"]); b.metric("平均命中", f"{bt['avg']:.2f}")
            c.metric("命中過半", f"{bt['win_rate']:.0f}%"); d.metric("亂選的理論平均", f"{bt['expect']:.2f}")
            st.caption("若平均命中和「亂選的理論平均」相差不大,代表該選號方式沒有比亂選好。")
            st.bar_chart(pd.DataFrame({"命中數": [len(r["命中"]) for r in bt["rows"]]}, index=[str(r["期數"]) for r in bt["rows"]]), color="#4aa3ff")
            st.dataframe(pd.DataFrame([(r["期數"], len(r["命中"]), " ".join(f"{n:02d}" for n in r["命中"]) or "—", "🎉" if r["贏"] else "", " ".join(f"{n:02d}" for n in r["號碼"])) for r in bt["rows"]],
                                      columns=["期數", "命中數", "命中號碼", "過半", "開獎號碼"]), hide_index=True)
        else:
            st.info("請先在「統計與選號」載入資料並選好號碼")
    with t3:
        s = st.slider("星數 ", 1, 10, 9)
        m = st.select_slider("加倍 ", [1, 2, 3, 4, 5, 10, 20, 50], 1)
        o = K.bingo_odds(s)
        ev = sum(r["p"] * min(r["prize"] * m, K.bingo_cap(s, r["hits"])) for r in o["rows"] if r["prize"])
        a, b, c = st.columns(3)
        a.metric("總中獎率", f"1/{1 / o['win']:.2f}"); b.metric("每期成本", f"{25 * m} 元"); c.metric("期望回收率", f"{ev / (25 * m) * 100:.1f}%")
        st.dataframe(pd.DataFrame([(f"中 {r['hits']} 個", K.fmt_prob(r["p"]), f"{min(r['prize'] * m, K.bingo_cap(s, r['hits'])):,}" if r["prize"] else "—") for r in o["rows"]], columns=["命中", "機率", "獎金(元)"]), hide_index=True)
        st.markdown("**各星數比較(不加倍)**")
        st.dataframe(pd.DataFrame([(f"{n} 星", f"1/{1 / K.bingo_odds(n)['win']:.2f}", f"{K.bingo_odds(n)['rtp'] * 100:.1f}%") for n in range(1, 11)], columns=["星數", "總中獎率", "回收率"]), hide_index=True)
        if draws:
            u = K.bingo_uniformity(draws)
            if u:
                st.caption(f"🔬 隨機性檢定(最近 {len(draws)} 期):χ²={u[0]:.1f},p≈{u[1]:.2f} —— " + ("看不出任何號碼比較容易開出,熱門/冷門只是隨機波動。" if u[1] >= .05 else "p 值偏低,但同時檢驗 80 個號碼偶有低 p 值,對預測下一期仍無幫助。"))
    st.caption("⚠️ 每期開獎互相獨立,熱門/冷門/遺漏值都無法預測下一期,請理性遊玩。")
elif page == PAGES[7]:
    hero("🏆", "樂透選號", "大樂透・威力彩・今彩539 —— 精確機率與選號工具")
    t1, t2 = st.tabs(["🎲 產生號碼", "📊 機率與複式試算"])
    notes = {"anti": "不提高中獎機率,只避開生日號、連號、等差直線,中浮動獎金時較不易分獎。", "random": "每組號碼被開出的機率完全相同。", "structure": "和值/AC值/奇偶等只是民間說法,統計上沒有優勢。"}
    with t1:
        c1, c2, c3 = st.columns(3)
        kind = c1.selectbox("彩種", list(K.LOTTO_RULES))
        n = c2.slider("注數", 1, 10, 5)
        mode = c3.selectbox("選號方式", list(K.LOTTO_MODES), format_func=K.LOTTO_MODES.get)
        st.caption("ℹ️ " + notes[mode])
        hot = st.checkbox("威力彩第二區參考近期熱門號(需連網)") if kind == "威力彩" else False
        if st.button("🎲 產生號碼", type="primary"):
            z = None
            if hot:
                try:
                    z = K.hot_second_zone(K.fetch_lotto_history(kind, 2))
                except Exception:  # noqa: BLE001
                    st.caption("(無法取得近期開獎,第二區改為隨機)")
            ts = K.generate_tickets(kind, n, mode=mode)
            lines = [f"【{kind}】"]
            for i, t in enumerate(ts, 1):
                s2 = (z or random.randint(1, 8)) if kind == "威力彩" else None
                with st.container(border=True):
                    st.markdown(f"**第 {i} 注**　" + balls(t["nums"], s2), unsafe_allow_html=True)
                    st.caption(f"和值 {t['sum']}　AC {t['ac']}　奇偶 {sum(x % 2 for x in t['nums'])}:{len(t['nums']) - sum(x % 2 for x in t['nums'])}")
                lines.append(f"第{i}注: " + " ".join(f"{x:02d}" for x in t["nums"]) + (f" + {s2:02d}" if s2 else ""))
            st.success(f"共 {len(ts)} 注,合計 {len(ts) * K.LOTTO_PRICE[kind]:,} 元")
            st.code("\n".join(lines), language=None)
    with t2:
        kind2 = st.selectbox("彩種 ", list(K.LOTTO_RULES))
        o = K.lotto_odds(kind2)
        a, b, c = st.columns(3)
        a.metric("單注價格", f"{o['price']} 元"); b.metric("頭獎機率", f"1/{1 / o['rows'][0][2]:,.0f}"); c.metric("任一獎機率", f"1/{1 / o['any']:.1f}")
        st.dataframe(pd.DataFrame([(a_, b_, K.fmt_prob(p), f"{1 / p:,.0f}") for a_, b_, p in o["rows"]], columns=["獎項", "對中條件", "機率", "約 1/x"]), hide_index=True)
        st.markdown("**複式 / 包牌試算**")
        pk = K.LOTTO_RULES[kind2]["pick"]
        k = st.slider("選幾個號碼", pk, pk + 8, pk + 2)
        w = K.lotto_wheel(kind2, k)
        a, b, c = st.columns(3)
        a.metric("共幾注", f"{w['combos']:,}"); b.metric("花費", f"{w['cost']:,} 元"); c.metric("頭獎機率", f"1/{1 / w['p']:,.0f}")
        st.caption("複式只是一次買很多注:花費增加幾倍,機率就增加幾倍,每一塊錢的中獎機率完全沒有變好。")
    st.caption("⚠️ 每期開獎皆為獨立隨機事件,沒有任何選號方法能提高中獎機率,請理性購買。")
elif page == PAGES[8]:
    hero("🤖", "AI 下注顧問", "依預算算出最合理的方案、號碼與完整勝算(含賓果加倍)")
    c1, c2 = st.columns(2)
    bud = c1.select_slider("預算(元)", [100, 200, 300, 500, 1000, 2000, 5000, 10000], 500)
    goal = c2.selectbox("目標", list(K.GOAL_LABELS), format_func=K.GOAL_LABELS.get)
    c3, c4 = st.columns(2)
    game = c3.selectbox("玩法", ["AI", "賓果", "今彩539", "大樂透", "威力彩"], format_func=lambda x: "AI 幫我選" if x == "AI" else x)
    mult = c4.selectbox("賓果加倍(2~50 倍)", ["AI", 1, 2, 3, 4, 5, 10, 20, 50], format_func=lambda x: "AI 決定" if x == "AI" else ("不加倍" if x == 1 else f"{x} 倍"))
    try:
        r = K.advisor_plan(bud, goal, game, mult)
    except ValueError as e:
        r = None
        st.warning(str(e))
    if r is None and game != "AI" and mult == "AI":
        st.info("預算不夠買這個玩法(賓果 25、今彩539/大樂透 50、威力彩 100 元)")
    if r:
        b, rows = r
        bingo = b["game"] == "賓果"
        u = "期" if bingo else "注"
        st.warning(f"先說結論:所有彩券長期都是虧錢。這份方案花 {b['cost']:,} 元,平均只拿回約 {b['ev_total']:,.0f} 元(回收率 {b['rtp'] * 100:.1f}%),平均虧 {b['loss']:,.0f} 元。它是你的預算與目標下數學上最合理的做法,但不能讓你賺錢。")
        with st.container(border=True):
            st.subheader(f"🤖 我的建議:{b['name']}")
            st.caption(f"目標:{K.GOAL_LABELS[goal]}　・預算 {bud:,} 元 → {b['n']} {u} × {b['price']:,} 元 = {b['cost']:,} 元" + (f"(剩 {bud - b['cost']:,} 元不用買)" if bud > b["cost"] else ""))
            ts = K.advisor_tickets(b["game"], b["stars"], b["n"])
            lines = [f"【AI 下注方案】{b['name']} {b['n']}{u} = {b['cost']} 元"]
            if bingo:
                st.markdown(f"**買法**:固定這組 {b['stars']} 個號碼;投注單選「{b['stars']} 星」," + (f"倍數選「{b['mult']} 倍」" if b["mult"] > 1 else "不加倍") + f";連續買 {b['n']} 期,每期 {b['price']:,} 元。不選超級獎號與猜大小。")
                st.markdown(balls(ts[0]["nums"]), unsafe_allow_html=True)
                lines.append("號碼:" + " ".join(f"{x:02d}" for x in ts[0]["nums"]))
                if b["n"] > K.BINGO_MAX_PERIODS:
                    full, rest = divmod(b["n"], K.BINGO_MAX_PERIODS)
                    st.info(f"⚠️ 每張投注單最多連買 12 期,{b['n']} 期要分 {b['slips']} 張:" + " + ".join([str(K.BINGO_MAX_PERIODS)] * full + ([str(rest)] if rest else [])) + " 期。")
                st.caption("號碼本身不影響勝算,固定同一組只是方便操作。")
            else:
                st.markdown(f"**買法**:到投注站(或網路)選「{b['game']}」,依下列號碼劃記,每注 {b['price']} 元。")
                for i, t in enumerate(ts, 1):
                    if i <= 20:
                        st.markdown(f"第 {i} 注　" + balls(t["nums"], t.get("second")), unsafe_allow_html=True)
                    lines.append(f"第{i}注: " + " ".join(f"{x:02d}" for x in t["nums"]) + (f" + {t['second']:02d}" if t.get("second") else ""))
            st.code("\n".join(lines), language=None)
        st.markdown("##### 📊 這份方案的勝算")
        a, c, d, e = st.columns(4)
        a.metric(f"單{u}中獎機率", K.fmt_prob(b["p_any1"]).split("(")[0]); c.metric(f"至少中一次({b['n']}{u})", f"{b['p_any'] * 100:.1f}%")
        d.metric("整份「淨賺」機率", f"{b['p_gain'] * 100:.2f}%"); e.metric("「回本以上」機率", f"{b['p_even'] * 100:.2f}%")
        a, c, d, e = st.columns(4)
        a.metric("平均拿回", f"{b['ev_total']:,.0f} 元"); c.metric("平均虧損", f"{b['loss']:,.0f} 元")
        d.metric("全中" if bingo else "中頭獎", K.fmt_prob(b["p_top"]).split("(")[0]); e.metric("最高獎金", f"{b['top_prize']:,} 元")
        if b["game"] in ("大樂透", "威力彩"):
            st.caption("※ 頭~肆獎為浮動獎金:平均拿回以官方總獎金率估算,淨賺機率假設中浮動獎即賺錢,屬估計值。")
        st.markdown("##### 🎯 各獎項機率")
        if bingo:
            tiers = [(f"中 {x['hits']} 個", K.fmt_prob(x["p"]), f"{min(x['prize'] * b['mult'], K.bingo_cap(b['stars'], x['hits'])):,}", f"{(1 - (1 - x['p']) ** b['n']) * 100:.1f}%") for x in K.bingo_odds(b["stars"])["rows"] if x["prize"]]
        else:
            fx = K.LOTTO_FIXED[b["game"]]
            tiers = [(f"{n_} {c_}", K.fmt_prob(p), f"{fx[n_]:,}" if n_ in fx else "浮動", f"{(1 - (1 - p) ** b['n']) * 100:.2f}%") for n_, c_, p in K.lotto_odds(b["game"])["rows"]]
        st.dataframe(pd.DataFrame(tiers, columns=["獎項", "單注機率", "獎金(元)", f"買 {b['n']} {u}至少中一次"]), hide_index=True)
        if len(b["mult_rows"]) > 1:
            st.markdown(f"##### ✖️ 加倍比較({b['stars']} 星,同樣 {bud:,} 元)")
            st.caption("加倍不會改變平均拿回,只改變結果有多集中:倍數越高,期數越少、單期輸贏越大。")
            st.dataframe(pd.DataFrame([(("★ " if x["mult"] == b["mult"] else "") + ("不加倍" if x["mult"] == 1 else f"{x['mult']} 倍"), f"{x['price']:,}", x["n"], f"{x['p_gain'] * 100:.2f}%", f"{x['p_even'] * 100:.2f}%", f"{x['p_any'] * 100:.1f}%", f"{x['ev_total']:,.0f}", f"{x['top_prize']:,}") for x in b["mult_rows"]],
                                      columns=["倍數", "每期成本", "期數", "淨賺機率", "回本以上", "至少中一次", "平均拿回", "單期最高獎"]), hide_index=True)
        st.markdown(f"##### ⚖️ 同樣 {bud:,} 元,各玩法比較")
        st.dataframe(pd.DataFrame([(("★ " if x["name"] == b["name"] else "") + x["name"], f"{x['n']}{'期' if x['game'] == '賓果' else '注'} / {x['cost']:,}", f"{x['p_any'] * 100:.1f}%", f"{x['p_gain'] * 100:.2f}%", f"{x['ev_total']:,.0f}", f"{x['rtp'] * 100:.1f}%", K.fmt_prob(x["p_top"]).split("(")[0]) for x in rows],
                                  columns=["玩法", "注數 / 花費", "至少中獎", "淨賺機率", "平均拿回", "回收率", "頭獎 / 全中"]), hide_index=True)
        st.markdown("##### 💬 為什麼這樣建議")
        for t in K.advisor_reasons(b, goal, game, rows):
            st.write("• " + t)
        with st.expander("🛡️ 自我控管"):
            st.write("• 預算花完就停,不要「追損」加碼——前面輸了不會讓之後的機率變好。\n\n• 加倍會放大單期輸贏,請確認你能接受一次輸掉整個倍數。\n\n• 不要用生活費、借來的錢下注。\n\n• 沒有任何方案或「AI」能預測開獎;這裡提供的是精確機率與較合理的下注方式。")
    st.caption("⚠️ 開獎為獨立隨機事件,沒有任何方法能提高中獎機率,請只用輸掉也無妨的錢。")
elif page == PAGES[9]:
    hero("📸", "大頭照", "自動轉正・置中裁切不變形・可輸出 4×6 吋整張排版")
    f = st.file_uploader("上傳照片(jpg / png / webp / bmp)", ["jpg", "jpeg", "png", "webp", "bmp"])
    if f:
        c0, c1, c2 = st.columns([2, 1, 1])
        size = K.PHOTO_SIZES[c0.selectbox("尺寸", list(K.PHOTO_SIZES), index=1)]
        cx, cy = c1.slider("左右", 0.0, 1.0, 0.5), c2.slider("上下(小=偏上)", 0.0, 1.0, 0.4)
        d1, d2 = st.columns(2)
        sheet = d1.checkbox("排滿 4×6 吋相紙(可直接沖印)")
        fmt = d2.radio("格式", ["JPG", "PNG"], horizontal=True)
        img = K.flatten_rgb(K.ImageOps.exif_transpose(K.Image.open(f)))
        out = K.crop_photo(img, size, cx, cy)
        info = f"單張 {size[0]}×{size[1]} px"
        if sheet:
            out, cnt = K.make_sheet(out)
            info = f"相紙 {out.width}×{out.height} px,共 {cnt} 張"
        st.image(out)
        st.caption(info + "　・300 dpi")
        buf = io.BytesIO()
        out.save(buf, "PNG" if fmt == "PNG" else "JPEG", **({} if fmt == "PNG" else {"quality": 95}), dpi=(300, 300))
        st.download_button(f"💾 下載 {fmt}", buf.getvalue(), f"photo.{fmt.lower()}", f"image/{'png' if fmt == 'PNG' else 'jpeg'}", type="primary")
elif page == PAGES[10]:
    hero("🛒", "各大電商比價", "PChome・momo・蝦皮同時查詢;預設只顯示信用良好的賣家")
    c1, c2 = st.columns([4, 1])
    kw = c1.text_input("搜尋商品", placeholder="例如:iPhone 16、羅技滑鼠、洗衣精").strip()
    c2.button("🔍 比價", type="primary")
    with st.expander("⚙️ 進階篩選"):
        a, b = st.columns(2)
        plats = a.multiselect("比價平台", S.PLATFORMS, default=S.PLATFORMS)
        good = b.checkbox("只顯示信用良好賣家(蝦皮商城/高評價)", True)
        must = a.checkbox("標題須包含所有關鍵字(過濾不相關配件)", True)
        sort = b.radio("排序", ["價格由低到高", "價格由高到低"], horizontal=True)
        pmin = a.number_input("最低價", 0, 10_000_000, 0, step=100)
        pmax = b.number_input("最高價(0 = 不限)", 0, 10_000_000, 0, step=100)
    if kw and plats:
        with st.spinner("同時查詢各平台…"):
            items, status = compare_cached(kw, tuple(plats), good)
        for col, (p, (n, err)) in zip(st.columns(len(status)), status.items()):
            col.metric(p, f"{n} 筆" if not err else "無法查詢", None if not err else "⚠️ 見下方說明", delta_color="off")
        for p, (n, err) in status.items():
            if err:
                st.caption(f"⚠️ {p}:{err[:110]}　→ 可改用下方「到各平台自己搜尋」")
        res = S.refine(items, kw, must, pmin, pmax, "desc" if "高到低" in sort else "asc")
        sm = S.summary(res)
        if sm:
            a, b, c, d = st.columns(4)
            a.metric("💰 最低價", f"{sm['min']:,.0f}", sm["best"]["platform"], delta_color="off")
            b.metric("平均價", f"{sm['avg']:,.0f}"); c.metric("中位數", f"{sm['median']:,.0f}"); d.metric("符合筆數", sm["n"])
            st.success(f"最便宜:{sm['best']['platform']}・{sm['best']['title'][:48]}")
            st.link_button("前往最低價商品 ↗", sm["best"]["url"])
            top = res[:12]
            with st.spinner("載入商品圖片…"):
                uris = img_uris([i.get("img", "") for i in top])
            st.markdown("<div class='pgrid'>" + "".join(
                f"<a class='pcard{' best' if i is sm['best'] else ''}' href='{_esc(i['url'])}' target='_blank'>"
                f"<img src='{uris.get(i.get('img', ''), _PH_PROD)}' loading='lazy'><span class='pp'>${i['price']:,.0f}</span>"
                f"<span class='pt'>{_esc(i['title'])}</span><span class='pb'>{_esc(i['platform'])}・{_esc(i['credit'])}</span></a>"
                for i in top) + "</div>", unsafe_allow_html=True)
            with st.expander(f"📋 完整清單({len(res)} 筆)"):
                st.dataframe(pd.DataFrame([(i["platform"], i["price"], i["credit"], i["title"], i["url"]) for i in res],
                                          columns=["平台", "價格(NT$)", "信用", "商品名稱", "連結"]), hide_index=True,
                             column_config={"連結": st.column_config.LinkColumn("商品連結", display_text="開啟 ↗"),
                                            "價格(NT$)": st.column_config.NumberColumn(format="%d")})
            by = {}
            for i in res:
                by[i["platform"]] = min(by.get(i["platform"], 1e12), i["price"])
            st.bar_chart(pd.DataFrame({"各平台最低價": by}), color="#d9441a")
        elif items:
            st.info("有查到商品,但都被篩選條件排除了。可取消「標題須包含所有關鍵字」或放寬價格範圍。")
        else:
            st.warning("所有平台都沒有回應(可能被網站暫時擋下)。請稍後再試,或使用下方連結直接搜尋。")
        st.markdown("##### 🔗 到各平台自己搜尋(已排序低價)")
        links = S.search_links(kw)
        names = list(links.items())
        for row in (names[:3], names[3:]):
            for col, (name, url) in zip(st.columns(3), row):
                col.link_button(f"{name} ↗", url)
    else:
        st.info("輸入想買的商品名稱,就會同時比較各平台價格。" if not kw else "請至少選擇一個平台。")

elif page == PAGES[11]:
    hero("🎡", "幸運大轉盤", "選擇困難救星:可設權重、不重複抽、音效與抽籤紀錄")
    wheels = _wheels()
    if st.session_state.get("wheel_pick") not in wheels:
        st.session_state["wheel_pick"] = next(iter(wheels))
    c1, c2 = st.columns([3, 1])
    name = c1.selectbox("選擇轉盤", list(wheels), key="wheel_pick")
    c2.button("🗑️ 刪除此轉盤", on_click=delete_wheel, disabled=len(wheels) <= 1)
    a, b = st.columns([3, 2])
    text = a.text_area("轉盤選項(每行一個;行尾加 *數字 設權重,例:拉麵*3)", "\n".join(W.to_lines(wheels[name])), height=210, key=f"wta_{name}")
    items = W.parse_lines(text)
    b.text_input("另存為(轉盤名稱)", value=name, key="wheel_new")
    b.button("💾 儲存轉盤", on_click=save_wheel, type="primary")
    b.download_button("⬇️ 匯出全部轉盤", json.dumps({k: [list(i) for i in v] for k, v in wheels.items()}, ensure_ascii=False, indent=1).encode("utf-8"),
                      "wheels.json", "application/json")
    b.file_uploader("⬆️ 匯入轉盤(.json)", ["json"], key="wheel_up", on_change=import_wheels)
    msg = st.session_state.pop("wheel_msg", "")
    if msg:
        st.info(msg)
    if len(items) >= 2:
        total = sum(w for _, w in items)
        st.caption("目前機率:" + "　".join(f"{n} {w / total * 100:.0f}%" for n, w in items[:12]) + ("…" if len(items) > 12 else ""))
    components_html(W.wheel_html(items), height=760, scrolling=True)
    st.caption("💡 點轉盤或按空白鍵即可旋轉。轉盤存在目前這次使用中,要永久保存請按「匯出」,下次再「匯入」。")

else:
    hero("🔧", "連線診斷", "確認伺服器能否連到各資料來源(部署後若某項失敗,可能是該網站擋海外 IP)")
    if st.button("開始測試", type="primary"):
        tests = {"電影(開眼)": lambda: f"{len(K.MovieClient().list_cinemas('a02', force=True))} 間戲院",
                 "天氣": lambda: K.fetch_weather("Taipei")["desc"], "油價": lambda: K.fetch_oil()["date"],
                 "股票(證交所/Yahoo)": lambda: K.fetch_stock("0050", "1mo")["src"], "匯率": lambda: f"{len(K.fetch_rates()['rates'])} 種",
                 "發票(財政部)": lambda: K.fetch_invoice_periods()[0]["title"], "賓果(pilio)": lambda: f"{len(K.fetch_bingo())} 期",
                 "比價 PChome": lambda: f"{len(S.search_pchome('滑鼠'))} 筆", "比價 momo": lambda: f"{len(S.search_momo('滑鼠'))} 筆",
                 "比價 蝦皮(常被擋)": lambda: f"{len(S.search_shopee('滑鼠'))} 筆"}
        for name, fn in tests.items():
            try:
                st.success(f"✅ {name}:{fn()}")
            except Exception as e:  # noqa: BLE001
                st.error(f"❌ {name}:{type(e).__name__}: {e}")

st.divider()
st.caption("資料來源:開眼電影網・wttr.in・台灣中油・證交所・財政部・pilio・exchangerate-api　|　彩券相關內容僅供參考,請理性購買")
