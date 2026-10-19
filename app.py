# -*- coding: utf-8 -*-
"""🧰 全方位生活助手 — Streamlit 版。  執行:streamlit run app.py"""
import io
import random
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

import pandas as pd
import base64
import json

import streamlit as st

import core as K
import life as L
import shop as S
import ui as U
import views as V
import wheel as W
import tdx as TD
from streamlit.components.v1 import html as components_html
from ui import _esc, hero, safe

st.set_page_config(page_title="全方位生活助手", page_icon="🧰", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>
:root{--soft:rgba(128,128,128,.10);--line:rgba(128,128,128,.24);--ac:#d9441a;--up:#e5484d;--down:#1f9d55}
.block-container{padding:4.6rem 1.2rem 3.5rem;max-width:1120px}
footer{visibility:hidden}
.hero{display:flex;align-items:center;gap:16px;background:linear-gradient(120deg,#ff6b3d,#ff9a5c 55%,#f5c542);padding:16px 22px;border-radius:22px;margin:4px 0 18px;color:#fff;box-shadow:0 10px 28px rgba(255,107,61,.22)}
.busfav{display:flex;justify-content:space-between;align-items:center;background:var(--soft);border:1px solid var(--line);border-radius:14px;padding:10px 14px}
.busfav .bs{opacity:.7;font-size:.85rem}.beta{font-weight:800;white-space:nowrap}.busfav .beta{font-size:1.3rem}
.beta.now{color:#ff6b3d}.beta.soon{color:#f59f00}.beta.mute{opacity:.55;font-weight:400;font-size:.85rem}
.hero h1{margin:0;font-size:1.55rem;color:#fff;padding:0}.hero p{margin:2px 0 0;opacity:.95;color:#fff}.hero .ico{font-size:2.4rem;filter:drop-shadow(0 2px 4px rgba(0,0,0,.25))}
div[data-testid=stMetric]{background:var(--soft);border:1px solid var(--line);border-radius:16px;padding:12px 16px}
div[data-testid=stMetricLabel] p{opacity:.72;font-size:.85rem}div[data-testid=stMetricValue]{font-weight:800}
div[data-testid=stVerticalBlockBorderWrapper]{border-radius:16px}
.stButton>button,.stDownloadButton>button,.stLinkButton>a{border-radius:12px;font-weight:700;min-height:2.6rem}
button[data-baseweb=tab]{font-weight:700}
div[data-testid=stPills] button,div[data-testid=stPills] [role=button]{border-radius:999px!important;font-weight:700}
.st-key-prefs_bridge{display:none}
[class*=st-key-tile_]{position:relative;margin-bottom:.7rem}
[class*=st-key-tile_] [data-testid=stMarkdownContainer],[class*=st-key-tile_] .stMarkdown{margin-bottom:0!important}
[class*=st-key-tile_] .tile{margin-bottom:0!important;height:100%}
[class*=st-key-tile_] [data-testid=stElementContainer]:has([data-testid=stPageLink]){position:absolute!important;inset:0;z-index:5;margin:0;width:100%!important;height:100%!important}
[class*=st-key-tile_] [data-testid=stPageLink],[class*=st-key-tile_] [data-testid=stPageLink]>div,[class*=st-key-tile_] [data-testid=stPageLink] a{display:block!important;width:100%!important;max-width:none!important;height:100%!important;opacity:0;margin:0!important;padding:0!important}
[class*=st-key-tile_]:hover .tile{transform:translateY(-2px);border-color:var(--ac);box-shadow:0 6px 18px rgba(0,0,0,.08)}
.tile .more{margin-top:auto;padding-top:6px;font-size:.8rem;font-weight:700;color:var(--ac)}
.st-key-home_btn{margin-bottom:-.4rem}
.st-key-home_btn a{display:inline-flex!important;width:auto!important;border:1px solid var(--line);border-radius:999px;padding:.1rem .8rem!important;background:var(--soft)}
.st-key-home_btn a:hover{border-color:var(--ac)}
.pbadge{display:inline-block;align-self:flex-start;padding:1px 8px;border-radius:7px;color:#fff;font-size:.72rem;font-weight:800}
.orig{margin-left:6px;font-size:.8rem;opacity:.55;text-decoration:line-through}.disc{margin-left:4px;padding:0 5px;border-radius:6px;background:var(--up);color:#fff;font-size:.72rem;font-weight:800}
.tag{display:inline-block;align-self:flex-start;padding:1px 7px;border-radius:7px;font-size:.72rem;font-weight:700}.tag.best{background:var(--ac);color:#fff}.tag.warn{background:rgba(214,164,0,.18);color:#b07d00}
.bestcard{display:flex;gap:16px;align-items:center;padding:14px;border-radius:18px;border:2px solid var(--ac);background:var(--soft);margin:6px 0 12px}
.bestcard img{width:130px;height:130px;object-fit:contain;border-radius:12px;background:#fff;flex:none}.bestcard .bb{min-width:0;flex:1}
.bestcard .ct{font-weight:800;line-height:1.35;margin:2px 0}.bestcard .cs{opacity:.8;font-size:.86rem}
.bestcard .go{display:inline-block;margin-top:8px;padding:.35rem 1rem;border-radius:10px;background:var(--ac);color:#fff!important;font-weight:800;text-decoration:none}
.grow{display:flex;align-items:center;gap:10px;padding:8px 4px;border-top:1px solid var(--line);color:inherit!important;text-decoration:none!important}
.grow:hover{background:var(--soft)}.grow .gt{flex:1;min-width:0;font-size:.85rem;opacity:.85;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.grow .gp{font-weight:800;white-space:nowrap}
@media(min-width:641px){[class*=st-key-geo_]{padding-top:1.75rem}.st-key-park_only{padding-top:2.2rem}}
.up{color:var(--up);font-weight:700}.down{color:var(--down);font-weight:700}.flat{opacity:.7;font-weight:700}
.pgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(168px,1fr));gap:10px;margin:8px 0 14px}
.pcard{display:flex;flex-direction:column;gap:4px;padding:10px;border-radius:14px;background:var(--soft);border:1px solid var(--line);color:inherit!important;text-decoration:none!important}
.pcard.best{border:2px solid var(--ac)}.pcard img{width:100%;aspect-ratio:1;object-fit:contain;border-radius:10px;background:#fff}
.pp{font-weight:800;font-size:1.15rem;color:var(--ac)}.pt{font-size:.82rem;line-height:1.3;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.pb{font-size:.74rem;opacity:.7}
.fcard{display:flex;gap:12px;background:var(--soft);border:1px solid var(--line);border-radius:16px;padding:12px;margin:0 0 10px}
.fcard img{width:84px;height:122px;object-fit:cover;border-radius:10px;flex:none}.fb{min-width:0;flex:1}
.ft{font-weight:800;font-size:1.05rem;line-height:1.3}.ft a{color:inherit;text-decoration:none}.fm{opacity:.75;font-size:.85rem;margin:3px 0 4px}
.lab{color:var(--ac);font-weight:800;font-size:.85rem;margin-top:6px}.tk{display:inline-block;margin-top:8px;color:var(--ac);font-weight:700;text-decoration:none}
.chip{display:inline-block;padding:4px 12px;margin:3px 5px 3px 0;border-radius:10px;background:var(--soft);border:1px solid var(--line);color:inherit;font-weight:700;font-size:.92rem}
.nrow{padding:7px 12px;margin:0 0 6px;border-radius:12px;background:var(--soft);border:1px solid var(--line)}
.nrow a{color:inherit;text-decoration:none}.nrow .fm{margin:2px 0 0}
.nlab{display:inline-block;margin-left:8px;padding:0 8px;border-radius:7px;border:1px solid var(--ac);color:var(--ac);font-size:.76rem;font-weight:700}
.chip.past{opacity:.38}.chip.next{background:var(--ac);border-color:var(--ac);color:#fff;opacity:1}
.badge{display:inline-block;padding:1px 9px;border-radius:7px;color:#fff;font-size:.78rem;font-weight:700;margin-right:6px}
.ball{display:inline-grid;place-items:center;width:38px;height:38px;border-radius:50%;background:var(--ac);color:#fff;font-weight:700;margin:3px;box-shadow:0 2px 6px rgba(217,68,26,.35)}
.ball.z{background:#2f7de1;box-shadow:0 2px 6px rgba(47,125,225,.35)}
.tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:12px;margin:4px 0 16px}
.tile{display:flex;flex-direction:column;gap:2px;padding:14px 16px;border-radius:18px;background:var(--soft);border:1px solid var(--line);color:inherit!important;text-decoration:none!important;transition:transform .12s,border-color .12s;min-height:118px}
@media(min-width:641px){.home .tile{min-height:168px}}
.tile .tv.sm{font-size:1.25rem}
.tile:hover{transform:translateY(-2px);border-color:var(--ac)}
.tile .tl{font-size:.82rem;font-weight:700;opacity:.7}.tile .tv{font-size:1.65rem;font-weight:800;line-height:1.2}.tile .ts{font-size:.85rem;opacity:.8;line-height:1.45}
.tile .row{display:flex;justify-content:space-between;gap:8px;font-size:.9rem;line-height:1.6}
.alert{display:flex;gap:10px;align-items:flex-start;padding:10px 14px;border-radius:14px;margin:0 0 8px;border:1px solid var(--line);background:var(--soft)}
.alert.red{border-color:#d63a3a;background:rgba(214,58,58,.10)}.alert.amber{border-color:#d6a400;background:rgba(214,164,0,.10)}
.alert b{display:block}.alert small{display:block;opacity:.75;line-height:1.5}
.dot{display:inline-grid;place-items:center;min-width:52px;height:52px;border-radius:50%;color:#fff;font-weight:800;font-size:1.15rem;flex:none}
.card{background:var(--soft);border:1px solid var(--line);border-radius:16px;padding:12px 14px;margin:0 0 10px}
.card .ct{font-weight:800;font-size:1.02rem}.card .cs{opacity:.75;font-size:.85rem;line-height:1.5}
.card a{color:inherit}
.bar{height:8px;border-radius:99px;background:var(--line);overflow:hidden;margin:6px 0 2px}.bar>i{display:block;height:100%;border-radius:99px}
.cal{display:grid;grid-template-columns:repeat(7,1fr);gap:4px}.cal div{min-height:58px;padding:4px 6px;border-radius:10px;background:var(--soft);font-size:.8rem;line-height:1.25}
.cal .h{background:none;min-height:0;text-align:center;font-weight:800;opacity:.7}.cal .off{background:rgba(229,72,77,.13);color:var(--up)}
.cal .today{outline:2px solid var(--ac)}.cal .mk{background:rgba(47,125,225,.14)}.cal .e{background:none}.cal b{font-size:.95rem}
.xfer{display:flex;align-items:center;gap:10px;flex-wrap:wrap;padding:10px 14px;border-radius:14px;background:var(--soft);border:1px solid var(--line);margin:0 0 8px;font-size:1.05rem}
.xfer .amt{margin-left:auto;font-weight:800;color:var(--ac);font-size:1.15rem}
.big{font-size:2.6rem;font-weight:800;line-height:1.1}
@media(max-width:640px){.fcard{padding:10px;gap:10px}.fcard img{width:62px;height:90px}.ft{font-size:1rem}
div[data-testid=stHorizontalBlock]{flex-wrap:wrap!important;gap:.5rem!important}
div[data-testid=stColumn],div[data-testid=column]{min-width:calc(50% - .5rem)!important;flex:1 1 calc(50% - .5rem)!important}
div[data-testid=stPills]>div,div[data-testid=stPills] [data-testid=stButtonGroup]{flex-wrap:nowrap!important;overflow-x:auto;-webkit-overflow-scrolling:touch;padding-bottom:4px}
div[data-testid=stPills] button{white-space:nowrap;flex:none}.block-container{padding:4rem .65rem 3rem}.hero{padding:12px 15px;border-radius:18px;gap:11px;margin-bottom:12px}.hero .ico{font-size:2rem}.hero h1{font-size:1.2rem}.hero p{font-size:.8rem}
.ball{width:31px;height:31px;font-size:.82rem;margin:2px}.chip{padding:3px 9px;font-size:.86rem}div[data-testid=stMetric]{padding:8px 11px}div[data-testid=stMetricValue]{font-size:1.35rem}
.tile .nm{display:none}.tile .tv.sm{font-size:1.02rem}.bestcard img{width:86px;height:86px}.bestcard{gap:10px;padding:10px}.tiles{grid-template-columns:1fr 1fr;gap:8px}.tile{padding:11px 12px;min-height:104px}.tile .tv{font-size:1.3rem}.cal div{min-height:46px;font-size:.7rem;padding:3px}.big{font-size:2rem}}
@media(max-width:330px){.tiles{grid-template-columns:1fr}}
@media(max-width:640px){.st-key-shop_search [data-testid=stColumn]:first-child{min-width:66%!important;flex:3 1 66%!important}.st-key-shop_search [data-testid=stColumn]:last-child{min-width:28%!important;flex:1 1 28%!important}}
</style>""", unsafe_allow_html=True)


def balls(nums, z=None):
    h = "".join(f"<span class='ball'>{n:02d}</span>" for n in nums)
    return h + (f"<b> + </b><span class='ball z'>{z:02d}</span>" if z else "")


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


def refresh_movies():
    """只清電影相關快取(含 MovieClient 內部 5 分鐘的網頁快取),不影響其他頁面與其他使用者的資料。"""
    scan.clear(); schedule.clear(); cinemas.clear()
    mc = mclient()
    with mc._lock:
        mc._cache.clear()


weather = st.cache_data(ttl=600, show_spinner="取得氣象…")(K.fetch_weather)
oil = st.cache_data(ttl=1800, show_spinner="取得牌價…")(K.fetch_oil)
stock = st.cache_data(ttl=20, show_spinner="取得報價…")(K.fetch_stock)
rates = st.cache_data(ttl=1800, show_spinner="取得匯率…")(K.fetch_rates)
invoices = st.cache_data(ttl=6 * 3600, show_spinner="取得財政部號碼…")(K.fetch_invoice_periods)   # 兩個月才開獎一次，不用常抓
bingo_draws = st.cache_data(ttl=300, show_spinner="取得賓果開獎…")(K.fetch_bingo)



@st.cache_resource
def poster_store():
    return {}


_STORE_MAX = 600  # 海報+商品圖上限,超過就刪最舊的,避免伺服器記憶體一直長


def _store_put(store, key, uri):
    store[key] = (uri, time.time())
    if len(store) > _STORE_MAX:
        for k, _ in sorted(store.items(), key=lambda kv: kv[1][1])[:len(store) - _STORE_MAX]:
            store.pop(k, None)


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
            got = dict(ex.map(lambda x: (x, _try_img(S._S, x, box, "https://www.google.com/")), todo))
        for u, uri in got.items():
            _store_put(store, u, uri)
    return {u: (store[u][0] if u in store else got.get(u)) or _PH_PROD for u in urls}


def poster_uris(shows):
    store, now = poster_store(), time.time()
    todo = [(x.film_id, x.poster) for x in shows if x.film_id not in store or (store[x.film_id][0] == _PH and now - store[x.film_id][1] > 600)]
    if todo:
        sess = mclient().session
        with ThreadPoolExecutor(8) as ex:
            got = dict(ex.map(lambda t: (t[0], _fetch_poster(sess, *t)), todo))
        for fid, uri in got.items():
            _store_put(store, fid, uri)
    return {x.film_id: store[x.film_id][0] if x.film_id in store else got.get(x.film_id, _PH) for x in shows}


@st.cache_data(ttl=600, show_spinner=False)
def compare_cached(kw, plats, good):
    return S.compare(kw, plats, good)


def _mins(t):
    """場次分鐘數;凌晨 0~5 點算當天營業日的深夜(+24h)。"""
    h, m = map(int, t.split(":"))
    return h * 60 + m + (1440 if h < 6 else 0)


def next_start(sessions, day, now):
    """尚未開演的最早場次(分鐘數);全部演完回傳極大值。"""
    return min((_mins(t) for s in sessions for t in s.times if not K.is_past(day, t, now)), default=10**6)


def sessions_html(sessions, day):
    now, h = K.tw_now(), ""
    nxt = next_start(sessions, day, now) if day == K.biz_date(now).strftime("%Y/%m/%d") else None
    for s in sessions:
        if s.label:
            h += f"<div class='lab'>{_esc(s.label)}</div>"
        for t in s.times:
            cls = "past" if K.is_past(day, t, now) else ("next" if _mins(t) == nxt else "")
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
    """轉盤存在設定(瀏覽器 localStorage)裡,重新整理也不會不見。"""
    P = U.prefs()
    if not P.get("wheels"):
        P["wheels"] = {k: [list(i) for i in v] for k, v in W.PRESETS.items()}
    return P["wheels"]


def save_wheel():
    ss = st.session_state
    items = W.parse_lines(ss.get(f"wta_{ss.get('wheel_pick')}_{U.rev()}", ""))
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
def page_movies():
    hero("🎬", "電影時刻", "全台戲院場次・已開演的場次變暗・橘色是下一場")
    c1, c2, c3 = st.columns([2, 3, 1])
    regions = list(K.REGIONS)
    r0 = U.pref("movie_region")
    region = c1.selectbox("地區", regions, index=regions.index(r0) if r0 in regions else 0, key=f"mv_region_{U.rev()}")
    U.remember("movie_region", region)
    favs = list(U.pref("fav_cinemas", []))
    mode = c2.radio("查詢方式", ["依戲院", "依電影", "⏰ 現在能看什麼"], horizontal=True)
    if c3.button("🔄 重新整理"):
        refresh_movies()
        st.rerun()
    flt = st.text_input("🔍 篩選", placeholder="輸入電影或戲院名稱").strip().casefold()
    cs = safe(cinemas, K.REGIONS[region])
    if cs:
        if mode == "依戲院":
            pool = [x for x in cs if flt in x.name.casefold()]
            if flt and not pool:
                st.caption(f"沒有戲院名稱含「{flt}」,改用片名篩選各戲院的場次")
            pool = sorted(pool or cs, key=lambda x: x.name not in favs)  # 常去的戲院排最前面
            st.caption(f"符合 {len(pool)} 間戲院" + ("・⭐ = 常去" if favs else ""))
            c = pool[st.selectbox("戲院", range(len(pool)), format_func=lambda i: ("⭐ " if pool[i].name in favs else "") + pool[i].name)]
            is_fav = c.name in favs
            if st.button("★ 取消常去" if is_fav else "⭐ 設為常去戲院", key="fav_btn",
                         help="常去的戲院會排在最前面,「現在能看什麼」也會預設只看它們"):
                U.remember("fav_cinemas", [x for x in favs if x != c.name] if is_fav else favs + [c.name])
                st.rerun()
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
                    day = labels[st.radio("日期", list(labels), horizontal=True, key="mv_day_c")]
                    shows = [s for s in day.shows if not flt or flt in s.title.casefold() or flt in c.name.casefold()]
                    now = K.tw_now()
                    shows.sort(key=lambda s: (next_start(s.sessions, day.key, now), s.title))  # 最快開演的排前面
                    live = [s for s in shows if next_start(s.sessions, day.key, now) < 10**6]
                    done = shows[len(live):]
                    st.caption(f"共 {len(shows)} 部電影・依下一場時間排序" + (f"・{len(done)} 部今天已演完" if done else ""))
                    if not shows:
                        st.info(f"這間戲院這天沒有符合「{flt}」的電影")
                    with st.expander("📋 解析到的電影清單(與官網不符時請參考)"):
                        st.write("、".join(f"{x.title}({sum(len(z.times) for z in x.sessions)}場)" for x in day.shows))
                    with st.spinner("載入海報…"):
                        uris = poster_uris(shows)
                    for sh in live:
                        st.markdown(card_html(sh.title, sh.url, film_meta(sh.rating, sh.duration),
                                              sessions_html(sh.sessions, day.key), uris[sh.film_id]), unsafe_allow_html=True)
                    if done:
                        with st.expander(f"🌙 今天已演完({len(done)} 部)"):
                            for sh in done:
                                st.markdown(card_html(sh.title, sh.url, film_meta(sh.rating, sh.duration),
                                                      sessions_html(sh.sessions, day.key), uris[sh.film_id]), unsafe_allow_html=True)
        else:
            got = safe(scan, K.REGIONS[region])
            if got:
                res, failed = got
                if failed:
                    st.warning(f"有 {len(failed)} 間戲院這次沒抓到({'、'.join(failed[:5])}{'…' if len(failed) > 5 else ''}),部分電影可能沒有顯示。按上方「🔄 重新整理」可重試。")
                cmap = {c.cid: c for c in cs}
                shorts = {d.key: d.short for s in res.values() for d in s.days}
                now = K.tw_now()
                if mode == "依電影":
                    idx = K.build_index({c.cid: res[c.cid] for c in cs if c.cid in res})
                    films = sorted(idx.values(), key=lambda f: (-len(f.by_cinema), f.title))
                    hit = [f for f in films if flt in f.title.casefold()]
                    if flt and not hit:
                        st.caption(f"沒有片名含「{flt}」的電影,顯示全部")
                    films = hit or films
                    if not films:
                        st.info("這個地區目前沒有場次資料")
                    else:
                        st.caption(f"符合 {len(films)} 部電影")
                        f = films[st.selectbox("電影", range(len(films)), format_func=lambda i: f"{films[i].title}({len(films[i].by_cinema)}間)")]
                        poster = poster_uris([f])[f.film_id]
                        meta = film_meta(f.rating, f.duration)
                        st.markdown(card_html(f"🎞️ {f.title}", f.url, meta, f"<a class='tk' href='{_esc(f.url)}' target='_blank'>📄 電影介紹</a>", poster), unsafe_allow_html=True)
                        days = sorted({d for m in f.by_cinema.values() for d in m})
                        day = st.radio("日期", days, horizontal=True, format_func=lambda k: shorts.get(k, k), key="mv_day_f") or days[0]
                        rows = [(next_start(m[day], day, now), cmap[cid].name, cid) for cid, m in f.by_cinema.items() if day in m and cid in cmap]
                        rows.sort()  # 最快能看到的戲院排前面,演完的排最後
                        st.caption(f"{len(rows)} 間戲院有上映・依下一場時間排序")
                        for _, _, cid in rows:
                            c = cmap[cid]
                            tk = f"<a class='tk' href='{_esc(c.ticket)}' target='_blank'>🎟️ 線上訂票</a>" if c.ticket else ""
                            st.markdown(card_html(c.name, c.url, _esc(c.address), sessions_html(f.by_cinema[cid][day], day), extra=tk), unsafe_allow_html=True)
                else:  # ⏰ 現在能看什麼
                    a, b = st.columns([1, 2])
                    hrs = a.select_slider("接下來幾小時", [1, 2, 3, 4, 6], 2)
                    names = sorted(cmap[cid].name for cid in res if cid in cmap)
                    pick = set(b.multiselect("只看這些戲院(不選 = 全部)", names, default=[n for n in names if n in favs], key=f"mv_pick_{region}_{U.rev()}"))
                    today, nowm = K.biz_date(now).strftime("%Y/%m/%d"), K.biz_minutes(now)
                    items = []
                    for cid, sch in res.items():
                        c = cmap.get(cid)
                        if not c or (pick and c.name not in pick):
                            continue
                        for d in sch.days:
                            if d.key != today:
                                continue
                            for sh in d.shows:
                                if flt and flt not in sh.title.casefold() and flt not in c.name.casefold():
                                    continue
                                for s in sh.sessions:
                                    for t in s.times:
                                        m = _mins(t)
                                        if not K.is_past(today, t, now) and m - nowm <= hrs * 60:
                                            items.append((m, t, sh, s.label, c))
                    items.sort(key=lambda x: (x[0], x[2].title, x[4].name))
                    if not items:
                        st.info(f"接下來 {hrs} 小時沒有符合的場次")
                    else:
                        st.caption(f"接下來 {hrs} 小時共 {len(items)} 場・{len({x[2].film_id for x in items})} 部電影")
                        h, last = "", None
                        for m, t, sh, lab, c in items[:300]:
                            if t != last:
                                wait = m - nowm
                                h += f"<div class='lab'>🕒 {t}　<small style='opacity:.7'>({'即將開演' if wait <= 0 else f'{wait} 分鐘後'})</small></div>"
                                last = t
                            end = f"・散場約 {(m + sh.duration) // 60 % 24:02d}:{(m + sh.duration) % 60:02d}" if sh.duration else ""
                            tk = f" <a href='{_esc(c.ticket)}' target='_blank'>🎟️</a>" if c.ticket else ""
                            h += (f"<div class='nrow'><a href='{_esc(sh.url)}' target='_blank'><b>{_esc(sh.title)}</b></a>"
                                  f"{'<span class=nlab>' + _esc(lab) + '</span>' if lab else ''}"
                                  f"<div class='fm'>{_esc(c.name)}{end}{tk}</div></div>")
                        st.markdown(h, unsafe_allow_html=True)
                        if len(items) > 300:
                            st.caption("場次太多,只顯示前 300 場;可用上方篩選或指定戲院縮小範圍")


CITIES = {"台北": "Taipei", "新北": "New Taipei", "桃園": "Taoyuan", "台中": "Taichung", "台南": "Tainan",
          "高雄": "Kaohsiung", "新竹": "Hsinchu", "基隆": "Keelung", "宜蘭": "Yilan", "花蓮": "Hualien", "台東": "Taitung",
          "嘉義": "Chiayi", "屏東": "Pingtung", "其他城市": ""}


def page_weather():
    hero("⛅", "天氣與空氣", "目前天氣・體感・紫外線・未來三天・空氣品質 AQI")
    t1, t2 = st.tabs(["⛅ 天氣", "🌫️ 空氣品質"])
    with t1:
        weather_view()
    with t2:
        V.aqi_view()


def weather_view():
    cities = CITIES
    c1, c2 = st.columns([1, 2])
    p0 = U.pref("city", "台北")
    pick = c1.selectbox("快速選城市", list(cities), index=list(cities).index(p0) if p0 in cities else 0, key=f"wx_city_{U.rev()}")
    q = c2.text_input("或輸入任何城市(英文名)", cities[pick] or U.pref("city_q", "Tokyo"), key=f"wx_q_{pick}_{U.rev()}").strip() or "Taipei"
    U.remember("city", pick)
    if not cities[pick]:
        U.remember("city_q", q)
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


def page_oil():
    hero("⛽", "油價", "台灣中油最新牌價與加油試算")
    d = safe(oil)
    if d:
        st.caption(f"牌價日期 {d['date']} ・ {d['src']}")
        for col, name, p, pv in zip(st.columns(4), K.OIL_NAMES, d["prices"], d["prev"] or [None] * 4):
            col.metric(name, f"{p:.1f}", f"{p - pv:+.1f}" if pv else None, delta_color="inverse")
        lit = st.number_input("加油量(公升)", 1.0, 200.0, 30.0)
        st.success("  |  ".join(f"{n.split()[0]}:{lit * p:,.0f} 元" for n, p in zip(K.OIL_NAMES, d["prices"])))



def page_stock():
    hero("📈", "股票", "自選股・持股損益・個股走勢・除權息日曆(證交所資料,Yahoo 僅備援)")
    t1, t4, t2, t3 = st.tabs(["⭐ 自選股", "💼 我的持股", "🔍 個股查詢", "📅 除權息"])
    with t1:
        V.watchlist_view()
    with t4:
        V.holdings_view()
    with t2:
        stock_detail()
    with t3:
        V.dividends_view()


def stock_detail():
    quick = {"自行輸入": "", "0050 元大台灣50": "0050", "0056 元大高股息": "0056", "00878 國泰永續高股息": "00878",
             "2330 台積電": "2330", "2317 鴻海": "2317", "2454 聯發科": "2454"}
    c1, c2, c3 = st.columns([2, 1, 2])
    qk = c1.selectbox("常用", list(quick))
    code = c2.text_input("代號", quick[qk] or "0050").strip()
    rng = c3.radio("區間", list(K.STOCK_RANGES), horizontal=True, index=1)
    auto = st.toggle("⏱️ 自動更新(30 秒)", key="stock_auto") if hasattr(st, "toggle") else False

    def stock_view():
        d = safe(stock, code, K.STOCK_RANGES[rng])
        if not d:
            return
        diff = d["price"] - d["prev"]
        st.subheader(f"{d['code']}　{d['name']}")
        watch = list(U.pref("watch", []))
        if d["code"] not in watch and st.button("⭐ 加入自選股", key=f"add_watch_{d['code']}"):
            U.remember("watch", watch + [d["code"]])
            st.session_state["prefs_rev"] = U.rev() + 1
            st.rerun()
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
        if st.button("🔄 重新整理", key="stock_refresh"):
            stock.clear()
            st.rerun()


def page_fx():
    hero("💱", "匯率", "銀行牌告(現鈔/即期,實際換匯價)・國際中間價多幣別換算")
    d = U.quiet(rates)
    t1, t2 = st.tabs(["🏦 銀行牌告(實際換匯)", "🌐 中間價換算"])
    with t1:
        V.bank_view(d["rates"] if d else None)
    with t2:
        if not d:
            d = safe(rates)
        if d:
            fx_mid_view(d)


def fx_mid_view(d):
    if d:
        st.caption("國際中間價適合估算行情;實際到銀行換錢請看「銀行牌告」。")
        c1, c2 = st.columns(2)
        amt = c1.number_input("金額", 0.0, 1e12, 1000.0)
        base = c2.selectbox("幣別", [f"{c} {n}" for c, _, n in K.FX_CURRENCIES]).split()[0]
        st.caption(f"匯率日期 {d['date']}")
        cols = st.columns(4)
        for i, (code, flag, name) in enumerate(x for x in K.FX_CURRENCIES if x[0] != base):
            v = K.fx_convert(amt, base, code, d["rates"])
            cols[i % 4].metric(f"{flag} {code} {name}", f"{v:,.0f}" if code in ("VND", "KRW") else f"{v:,.2f}",
                               f"1 {base} = {K.fx_convert(1, base, code, d['rates']):,.4f}", delta_color="off")



def page_invoice():
    hero("🧾", "統一發票對獎", "自動取得財政部最新中獎號碼,免手動輸入")
    ps = safe(invoices)
    if not ps:
        return
    t1, t2 = st.tabs(["✍️ 輸入號碼", "📷 掃描 QR Code"])
    with t2:
        V.invoice_scan_view(ps)
    with t1:
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



def page_bingo():
    hero("🎰", "賓果", "開獎統計・選號・回測・精確機率(統計無法預測下一期)")
    draws = safe(bingo_draws)
    t1, t2, t3 = st.tabs(["📊 統計與選號", "🧪 回測", "🧮 機率與期望值"])
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


BINGO_SUG = max(range(1, 11), key=lambda s: K.bingo_odds(s)["rtp"])   # 平均拿回最多的星數(9 星)
BINGO_FREQ = max(range(1, 11), key=lambda s: K.bingo_odds(s)["win"])  # 最常中獎的星數(2 星)


def lotto_suggest():
    """每種玩法一張卡片:一組建議號碼 + 單注中獎機率、頭獎機率、平均拿回。"""
    games = [("賓果", BINGO_SUG), ("今彩539", 0), ("大樂透", 0), ("威力彩", 0)]
    new = st.button("🔄 換一組號碼", key="lotto_sug_new")
    if new or "lotto_sug" not in st.session_state:
        st.session_state["lotto_sug"] = {g: K.advisor_tickets(g, s, 1)[0] for g, s in games}
    sug = st.session_state["lotto_sug"]
    row = "<div style='display:flex;justify-content:space-between;gap:8px;font-size:.88rem'><span style='opacity:.75'>{}</span><b>{}</b></div>"
    cards = []
    for g, s in games:
        r, t = K.plan_stats(g, s, 1, dp=False), sug[g]
        p = r["p_any1"]
        rows = [("中獎", f"{p * 100:.1f}%(1/{1 / p:.0f})"),
                ("頭獎" if g != "賓果" else "全中", K.fmt_prob(r["p_top1"]).split("(")[0]),
                ("平均拿回", f"{r['ev_each']:.0f} / {r['price']} 元")]
        note = ""
        if g == "賓果":
            note = (f"<div style='font-size:.78rem;opacity:.7'>想常中:改選 {BINGO_FREQ} 星,"
                    f"中獎 {K.bingo_odds(BINGO_FREQ)['win'] * 100:.0f}%</div>")
        title = f"🎰 賓果 {s} 星" if g == "賓果" else ("🎱 " + g)
        cards.append(f"<div class='tile' style='min-height:0'><span class='tl'><b>{title}</b>　{r['price']} 元</span>"
                     f"<div style='margin:4px 0'>{balls(t['nums'], t.get('second'))}</div>"
                     + "".join(row.format(a, b) for a, b in rows) + note + "</div>")
    st.markdown("<div class='tiles'>" + "".join(cards) + "</div>", unsafe_allow_html=True)
    st.caption("「中獎」= 買 1 注中任何一個獎的機率，「平均拿回」= 長期平均每注拿回多少錢。號碼只是先幫你選好,每一組號碼被開出的機率都一樣;"
               f"大樂透、威力彩用「避開大眾選號」,中頭獎時比較不用跟別人分。賓果建議 {BINGO_SUG} 星是因為長期平均拿回最多。")


def page_lotto():
    hero("🏆", "樂透選號", "大樂透・威力彩・今彩539 —— 精確機率與選號工具")
    t0, t1, t2 = st.tabs(["🎯 建議號碼", "🎲 產生號碼", "📊 機率與複式試算"])
    with t0:
        lotto_suggest()
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


def page_advisor():
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


def page_photo():
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


SORTS = {"💰 最便宜": "price", "🎯 最相關": "score", "🔥 最熱銷": "sold", "⭐ 評價最好": "rating", "💸 最貴": "price_desc"}


def _shop_pick_recent():
    v = st.session_state.get("shop_recent_pick")
    if v:
        st.session_state["shop_kw"] = v
        st.session_state["shop_recent_pick"] = None
        st.session_state["shop_show"] = 24


def _shop_watch():
    return U.prefs().setdefault("shop_watch", {})


def _shop_record(kw, sm):
    """有追蹤的關鍵字,每次查詢就記下當天最低到手價(一天一筆,保留 90 筆)。"""
    w = _shop_watch().get(kw)
    if not (w and sm):
        return
    b = sm["best"]
    entry = [K.tw_now().strftime("%Y/%m/%d"), b["price"] + (b.get("ship") or 0), S.PLATFORM_SHORT.get(b["platform"], b["platform"])]
    h = w.setdefault("hist", [])
    if h and h[-1][0] == entry[0]:
        h[-1] = entry
    else:
        h.append(entry)
    del h[:-90]


def _pbadge(p):
    return f"<span class='pbadge' style='background:{S.PLATFORM_COLOR.get(p, '#666')}'>{_esc(S.PLATFORM_SHORT.get(p, p))}</span>"


def _shop_card(i, uri, best=False):
    total = i["price"] + (i.get("ship") or 0)
    orig = f"<span class='orig'>${i['orig']:,.0f}</span><span class='disc'>-{(1 - i['price'] / i['orig']) * 100:.0f}%</span>" if i.get("orig") else ""
    meta = []
    if i.get("rating"):
        meta.append(f"⭐ {i['rating']:.1f}" + (f"({i['reviews']:,.0f})" if i.get("reviews") else ""))
    if i.get("sold_text"):
        meta.append(_esc(i["sold_text"]))
    if i.get("ship"):
        meta.append(f"🚚 運費 {i['ship']:,.0f}・到手 ${total:,.0f}")
    tags = ("<span class='tag best'>🏆 最划算</span>" if best else "") + \
           ("<span class='tag warn'>⚠️ 價格異常低,可能是配件</span>" if i.get("odd") else "") + \
           ("<span class='tag warn'>🔌 疑似配件</span>" if i.get("acc") else "")
    return (f"<a class='pcard{' best' if best else ''}' href='{_esc(i['url'])}' target='_blank'>{_pbadge(i['platform'])}"
            f"<img src='{uri}' loading='lazy'><span><span class='pp'>${i['price']:,.0f}</span>{orig}</span>"
            f"<span class='pt'>{_esc(i['title'])}</span><span class='pb'>{' ・ '.join(meta) or _esc(i['credit'])}</span>{tags}</a>")


def shop_watch_view():
    W = _shop_watch()
    if not W:
        return
    with st.expander(f"🔔 我的降價追蹤({len(W)})", expanded=True):
        if st.button("🔄 全部重新查價", key="shop_watch_refresh"):
            with st.spinner("查詢中…"):
                for kw_ in list(W):
                    items_, _ = compare_cached(kw_, tuple(S.PLATFORMS), True)
                    res_, _ = S.analyze(items_, kw_)
                    _shop_record(kw_, S.summary(res_))
        for kw_, w in list(W.items()):
            h = w.get("hist") or []
            last = h[-1] if h else None
            tgt = w.get("target") or 0
            hit = last and tgt and last[1] <= tgt
            chg = ""
            if len(h) >= 2:
                d = h[-1][1] - h[-2][1]
                chg = f"<span class='{'down' if d < 0 else 'up' if d > 0 else 'flat'}'>{'▼' if d < 0 else '▲' if d > 0 else '－'} {abs(d):,.0f}</span>"
            lo = min((x[1] for x in h), default=None)
            st.markdown(f"<div class='alert {'amber' if hit else ''}' style='margin:0'><div><b>{'🎯 ' if hit else ''}{_esc(kw_)}</b>"
                        f"<small>{'目前最低 $' + format(last[1], ',.0f') + '(' + last[2] + ',' + last[0][5:] + ')' if last else '尚未查價'} {chg}"
                        f"{'・歷史最低 $' + format(lo, ',.0f') if lo else ''}{'・目標 $' + format(tgt, ',.0f') if tgt else ''}"
                        f"{'・✅ 已達目標價!' if hit else ''}</small></div></div>", unsafe_allow_html=True)
            with st.container(horizontal=True):
                if st.button("🔍 查看", key=f"sw_go_{kw_}"):
                    st.session_state["shop_kw"] = kw_
                    st.rerun()
                if st.button("🗑️ 取消追蹤", key=f"sw_del_{kw_}"):
                    W.pop(kw_, None)
                    st.rerun()
        st.caption("每次打開比價頁或按「重新查價」時記錄當天最低到手價;網站不會在背景自動查價。")


def page_shop():
    hero("🛒", "聰明比價", "PChome・momo・Yahoo・露天同時比・蝦皮一鍵開啟・同款商品跨平台比價・降價追蹤")
    ss = st.session_state
    c1, c2 = st.container(key="shop_search").columns([5, 1])
    kw = c1.text_input("搜尋商品", key="shop_kw", placeholder="例如:羅技 M720、象印 電子鍋、iPhone 16 128G",
                       label_visibility="collapsed").strip()
    c2.button("🔍 比價", type="primary", width="stretch")
    if ss.get("shop_last_kw") != kw:  # 換關鍵字就從頭顯示
        ss["shop_last_kw"], ss["shop_show"] = kw, 24
    recent = list(U.pref("shop_recent", []))
    if recent:
        st.pills("最近搜尋", recent, key="shop_recent_pick", on_change=_shop_pick_recent, label_visibility="collapsed")
    shop_watch_view()
    with st.expander("⚙️ 平台與篩選"):
        a, b = st.columns(2)
        saved = [p for p in U.pref("shop_plats", S.PLATFORMS) if p in S.PLATFORMS] or S.PLATFORMS
        plats = a.multiselect("比價平台", S.PLATFORMS, default=saved, key=f"shop_plats_{U.rev()}")
        U.remember("shop_plats", plats)
        good = b.checkbox("只顯示信用良好賣家(露天有成交紀錄)", True)
        must = a.checkbox("標題須包含所有關鍵字(品牌中英文都算)", True)
        hide_acc = b.checkbox("隱藏配件(殼、貼、線、收納包…)", True)
        exclude = a.text_input("排除字詞(空白分隔)", placeholder="例如:福利品 二手 展示")
        p1, p2 = b.columns(2)
        pmin = p1.number_input("最低價", 0, 10_000_000, 0, step=100)
        pmax = p2.number_input("最高價(0=不限)", 0, 10_000_000, 0, step=100)
    if not kw:
        st.markdown("<div class='card'><div class='ct'>💡 怎麼用</div><div class='cs'>"
                    "・輸入<b>品牌 + 型號</b>最準,例如「羅技 M720」「象印 NL-AAF10」<br>"
                    "・「同款比價」會把不同平台的同一個型號放在一起,一眼看出哪裡最便宜<br>"
                    "・露天的價格會加上運費算「到手價」<br>・按「🔔 追蹤」可以記錄價格變化、設定目標價</div></div>", unsafe_allow_html=True)
        return
    if not plats:
        st.info("請至少選擇一個平台。")
        return
    U.remember("shop_recent", ([kw] + [x for x in recent if x != kw])[:8])
    with st.spinner("同時查詢各平台…"):
        items, status = compare_cached(kw, tuple(plats), good)
    chips = ""
    for p, (n, err) in status.items():
        chips += (f"<span class='chip' title='{_esc(err or '')}'>{_pbadge(p)} " + (f"{n} 筆" if not err else "⛔ 被擋") + "</span>")
    st.markdown(chips, unsafe_allow_html=True)
    st.link_button(f"🛍️ 到蝦皮看「{kw}」(便宜的排前面)", S.search_links(kw)["蝦皮"],
                   help="蝦皮會擋伺服器查詢,沒辦法直接一起比價,點這裡用你的瀏覽器開蝦皮的搜尋結果")
    if any(err for _, err in status.values()):
        st.caption("⛔ 被擋 = 該網站拒絕伺服器查詢,可用最下面的連結到網站自己搜尋。")
    sort = SORTS[st.segmented_control("排序", list(SORTS), default="💰 最便宜", key="shop_sort", label_visibility="collapsed") or "💰 最便宜"]
    res, dropped = S.analyze(items, kw, must, hide_acc, exclude, pmin, pmax, sort)
    sm = S.summary(res)
    if not sm:
        if items:
            st.info(f"有查到 {len(items)} 筆商品,但都被篩選掉了。可到「⚙️ 平台與篩選」取消「標題須包含所有關鍵字」或「隱藏配件」。")
        else:
            st.warning("所有平台都沒有回應(可能被網站暫時擋下)。請稍後再試,或用下方連結直接搜尋。")
        _shop_links(kw)
        return
    _shop_record(kw, sm)
    best = sm["best"]
    show_n = ss.setdefault("shop_show", 24)
    top = res[:show_n]
    with st.spinner("載入商品圖片…"):
        uris = img_uris([i.get("img", "") for i in top + [best]])

    # ── 最划算 ──
    total = best["price"] + (best.get("ship") or 0)
    save = sm["median"] - total
    st.markdown(
        f"<div class='bestcard'><img src='{uris.get(best.get('img', ''), _PH_PROD)}'><div class='bb'>"
        f"<div class='cs'>🏆 目前最划算 {_pbadge(best['platform'])}</div><div class='ct'>{_esc(best['title'])}</div>"
        f"<div class='big' style='color:var(--ac)'>${total:,.0f}</div>"
        f"<div class='cs'>{'含運費 ' + format(best['ship'], ',.0f') + ' 元・' if best.get('ship') else ''}"
        f"{'比中位數便宜 $' + format(save, ',.0f') + '(' + format(save / sm['median'] * 100, '.0f') + '%)' if save > 0 else '接近市場行情'}</div>"
        f"<a class='go' href='{_esc(best['url'])}' target='_blank'>前往購買 ↗</a></div></div>", unsafe_allow_html=True)
    odd = f"・{sm['odd']} 筆價格異常低(已排最後)" if sm["odd"] else ""
    st.markdown("<div class='tiles'>" + "".join(
        f"<div class='tile' style='min-height:0'><span class='tl'>{a}</span><span class='tv'>{b}</span></div>" for a, b in
        [("最低", f"${sm['min']:,.0f}"), ("中位數", f"${sm['median']:,.0f}"), ("最高", f"${sm['max']:,.0f}"), ("符合筆數", f"{sm['n']}")]) + "</div>",
        unsafe_allow_html=True)
    st.caption(f"已過濾 {dropped} 筆不相關或配件{odd}")
    wt = _shop_watch().get(kw)
    with st.popover("🔔 已追蹤・設定目標價" if wt else "🔔 追蹤這個商品的價格"):
        tgt = st.number_input("目標價(到這個價格以下會在首頁提醒,0 = 不設定)", 0, 10_000_000,
                              int((wt or {}).get("target") or 0), step=100, key=f"shop_tgt_{kw}")
        cc1, cc2 = st.columns(2)
        if cc1.button("💾 儲存追蹤", type="primary", key=f"shop_tgt_save_{kw}"):
            _shop_watch()[kw] = {"target": tgt, "hist": (wt or {}).get("hist") or []}
            _shop_record(kw, sm)
            st.rerun()
        if wt and cc2.button("取消追蹤", key=f"shop_tgt_del_{kw}"):
            _shop_watch().pop(kw, None)
            st.rerun()
        if wt and len(wt.get("hist") or []) >= 2:
            st.line_chart(pd.DataFrame({"最低到手價": [x[1] for x in wt["hist"]]}, index=[x[0][5:] for x in wt["hist"]]), height=160, color="#ff6b3d")

    t1, t2, t3, t4 = st.tabs(["🛍️ 商品", "🔀 同款比價", "📊 價格分布", "📋 完整清單"])
    with t1:
        st.markdown("<div class='pgrid'>" + "".join(_shop_card(i, uris.get(i.get("img", ""), _PH_PROD), i is best) for i in top) + "</div>",
                    unsafe_allow_html=True)
        if len(res) > show_n:
            if st.button(f"顯示更多(還有 {len(res) - show_n} 筆)", width="stretch"):
                ss["shop_show"] = show_n + 24
                st.rerun()
    with t2:
        groups = S.same_product_groups(res)
        if not groups:
            st.info("沒有找到在兩個以上平台都有賣的同一型號。輸入更明確的型號(例如「羅技 M720」)比較容易配對。")
        for g in groups:
            rows = ""
            for k, x in enumerate(g["items"]):
                tot = x["price"] + (x.get("ship") or 0)
                diff = "" if k == 0 else f"<span class='up'>+{tot - (g['best']['price'] + (g['best'].get('ship') or 0)):,.0f}</span>"
                rows += (f"<a class='grow' href='{_esc(x['url'])}' target='_blank'>{_pbadge(x['platform'])}"
                         f"<span class='gt'>{_esc(x['title'])}</span><span class='gp'>{'🏆 ' if k == 0 else ''}${tot:,.0f} {diff}</span></a>")
            st.markdown(f"<div class='card'><div class='ct'>{_esc(g['title'][:60])}</div>"
                        f"<div class='cs'>型號/規格:{_esc(g['key'])}・{len(g['items'])} 個平台"
                        f"{'・最多差 <b>$' + format(g['save'], ',.0f') + '</b>' if g['save'] > 0 else '・各平台同價'}</div>{rows}</div>",
                        unsafe_allow_html=True)
        st.caption("依標題中的型號/規格自動配對,同一型號的不同顏色或組合也可能被放在一起,下單前請再確認規格。")
    with t3:
        import altair as alt
        df = pd.DataFrame([{"平台": S.PLATFORM_SHORT[i["platform"]], "到手價": i["price"] + (i.get("ship") or 0), "商品": i["title"][:40],
                            "類型": "價格異常低" if i.get("odd") else "一般"} for i in res])
        doms = [S.PLATFORM_SHORT[p] for p in S.PLATFORMS]
        ch = alt.Chart(df).mark_circle(size=90, opacity=.75).encode(
            x=alt.X("到手價:Q", scale=alt.Scale(zero=False), title="到手價(NT$)"), y=alt.Y("平台:N", title=None, sort=doms),
            color=alt.Color("平台:N", scale=alt.Scale(domain=doms, range=[S.PLATFORM_COLOR[p] for p in S.PLATFORMS]), legend=None),
            shape=alt.Shape("類型:N", legend=None), tooltip=["平台", "到手價", "商品"]).properties(height=60 + 46 * df["平台"].nunique())
        rule = alt.Chart(pd.DataFrame({"x": [sm["median"]]})).mark_rule(strokeDash=[4, 4], color="#888").encode(x="x:Q")
        st.altair_chart(ch + rule, width="stretch")
        st.caption("每個點是一個商品,虛線是中位數。滑鼠移到點上可以看商品名稱。")
    with t4:
        st.dataframe(pd.DataFrame([(S.PLATFORM_SHORT[i["platform"]], i["price"] + (i.get("ship") or 0), i["price"], i.get("ship") or 0,
                                    i.get("rating"), i.get("sold_text") or "", i["score"], i["title"], i["url"]) for i in res],
                                  columns=["平台", "到手價", "售價", "運費", "評價", "銷量", "相關度", "商品名稱", "連結"]),
                     hide_index=True, width="stretch",
                     column_config={"連結": st.column_config.LinkColumn("連結", display_text="開啟 ↗"),
                                    "到手價": st.column_config.NumberColumn(format="$%d"), "售價": st.column_config.NumberColumn(format="$%d"),
                                    "相關度": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%d")})
    _shop_links(kw)


def _shop_links(kw):
    st.markdown("##### 🔗 到各平台自己搜尋")
    links = list(S.search_links(kw).items())
    for col, (name, url) in zip(st.columns(len(links)), links):
        col.link_button(f"{name} ↗", url, width="stretch")


def page_wheel():
    hero("🎡", "幸運大轉盤", "選擇困難救星:可設權重、不重複抽、音效與抽籤紀錄")
    wheels = _wheels()
    if st.session_state.get("wheel_pick") not in wheels:
        st.session_state["wheel_pick"] = next(iter(wheels))
    c1, c2 = st.columns([3, 1])
    name = c1.selectbox("選擇轉盤", list(wheels), key="wheel_pick")
    c2.button("🗑️ 刪除此轉盤", on_click=delete_wheel, disabled=len(wheels) <= 1)
    a, b = st.columns([3, 2])
    text = a.text_area("轉盤選項(每行一個;行尾加 *數字 設權重,例:拉麵*3)", "\n".join(W.to_lines(wheels[name])), height=210, key=f"wta_{name}_{U.rev()}")
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
    st.caption("💡 點轉盤或按空白鍵即可旋轉。按「儲存轉盤」後會自動存在這台裝置的瀏覽器裡;換裝置時可用「匯出 / 匯入」。")


# ═════════ 首頁 ═════════
def _next_invoice_draw(today):
    """統一發票每逢單數月 25 日開出前兩個月的號碼。回傳 (開獎日, 期別文字)。"""
    y, m = today.year, today.month
    if m % 2 == 0 or today.day > 25:
        m += 1 if m % 2 == 0 else 2
        if m > 12:
            y, m = y + 1, m - 12
    d = datetime(y, m, 25).date()
    end_m, end_y = (m - 1, y) if m > 1 else (12, y - 1)
    return d, f"{end_y - 1911}年 {end_m - 1:02d}-{end_m:02d}月"


def _tile(label, value, sub="", rows=None, value_style="", small=False):
    r = "".join(f"<div class='row'><span>{a}</span><span>{b}</span></div>" for a, b in rows or [])
    v = f"<span class='tv{' sm' if small else ''}' style='{value_style}'>{value}</span>" if value else ""
    return f"<div class='tile'><span class='tl'>{label}</span>{v}{r}<span class='ts'>{sub}</span></div>"


def _eq_recent(e, now, hours=12):
    try:
        t = datetime.strptime(f"{now.year}/{e['time']}", "%Y/%m/%d %H:%M").replace(tzinfo=now.tzinfo)
    except (ValueError, KeyError):
        return False
    return timedelta(0) <= now - t <= timedelta(hours=hours)


def page_home():
    now = K.tw_now()
    today = now.date()
    h_ = now.hour
    greet = "夜深了,早點休息 🌙" if h_ < 5 else "早安 ☀️" if h_ < 11 else "午安 🍱" if h_ < 14 else "下午好 ☕" if h_ < 18 else "晚安 🌙"
    city = U.pref("city", "台北")
    q = CITIES.get(city) or U.pref("city_q", "Taipei") or "Taipei"
    watch = list(U.pref("watch", ["0050", "2330", "00878"]))[:6]
    holds = list(U.pref("holdings", []))
    codes = tuple(dict.fromkeys(watch + [h["code"] for h in holds]))
    with st.spinner("整理今天的資訊…"):
        got = U.parallel(timeout=8, w=lambda: weather(q), aq=V.aqi, wn=V.cwa_warnings, cl=V.closures, eq=V.earthquakes,
                         bank=V.bank_rates, oil=oil, qs=lambda: V.quotes(codes), inv=invoices, cal=V.holidays_all)
    cal = got["cal"] or []
    lw = [x for x in L.long_weekends(cal) if x["end"] >= today] if cal else []
    if lw:
        n = (lw[0]["start"] - today).days
        hol = f"🎉 正在放「{lw[0]['name']}」連假" if n <= 0 else f"距離「{lw[0]['name']}」連假還有 {n} 天"
    else:
        hol = ""
    hero("🧰", greet, home=False, sub=f"{today:%Y/%m/%d}({V.WD[today.weekday()]})・民國 {today.year - 1911} 年" + (f"・{hol}" if hol else ""))

    # ── 防災提醒 ──
    alerts = []
    if got["cl"] and got["cl"][0]:
        alerts += [("red", "🏫", f"{c}:{s}") for c, s in got["cl"][0][:4]]
    for w in (got["wn"] or [])[:3]:
        alerts.append(("red" if "颱風警報" in w["title"] or "豪雨" in w["title"] else "amber", V.warn_icon(w["title"]),
                       f"{w['title']}(至 {w['validto'][5:] if w['validto'] else '—'})"))
    for e in (got["eq"] or [])[:3]:
        if (e["intensity"] or 0) >= 3 and _eq_recent(e, now):
            alerts.append(("amber", "🌏", f"{e['time']} {e['where']} 規模 {e['mag']},最大震度 {e['intensity']} 級"))
    for kw_, w in (U.pref("shop_watch", {}) or {}).items():
        h, tgt = w.get("hist") or [], w.get("target") or 0
        if h and tgt and h[-1][1] <= tgt:
            alerts.append(("amber", "🛒", f"「{kw_}」降到 ${h[-1][1]:,.0f}({h[-1][2]}),已低於目標價 ${tgt:,.0f}"))
    if alerts:
        st.markdown("".join(f"<div class='alert {c}'><span>{i}</span><div><b>{_esc(t)}</b></div></div>" for c, i, t in alerts),
                    unsafe_allow_html=True)
        st.page_link(PAGES["alerts"], label="查看防災資訊 →")
    elif got["cl"] is not None or got["wn"] is not None:
        st.caption("✅ 目前沒有停班停課與天氣警特報")

    # ── 資訊卡 ──
    tiles = []
    d = got["w"]
    if d:
        tiles.append(("weather", _tile(f"⛅ {city if CITIES.get(city) else q} 天氣", f"{d['icon']} {d['temp']}°C",
                                       f"{d['desc']}・體感 {d['feel']}°・降雨 {d['rain']}%")))
    else:
        tiles.append(("weather", _tile("⛅ 天氣", "—", "暫時無法取得")))
    aq = got["aq"]
    county = U.pref("aqi_county", "臺北市")
    sites = [x for x in aq or [] if x["county"] == county and x["aqi"] is not None]
    if sites:
        avg = sum(x["aqi"] for x in sites) / len(sites)
        name, col, _ = L.aqi_level(avg)
        tiles.append(("weather", _tile(f"🌫️ {county} 空氣", f"AQI {avg:.0f}", f"{name}・{len(sites)} 個測站平均", value_style=f"color:{col}")))
    else:   # 環境部抓不到（例如公用金鑰額度用完）：改用 Open-Meteo 的估計值，跟空氣品質頁一樣
        om = U.quiet(V.aqi_om, *L.COUNTY_XY[county]) if county in L.COUNTY_XY else None
        if om and om.get("aqi") is not None:
            name, col, _ = L.aqi_level(om["aqi"])
            tiles.append(("weather", _tile(f"🌫️ {county} 空氣", f"AQI {om['aqi']:.0f}", f"{name}・Open-Meteo 估計值",
                                           value_style=f"color:{col}")))
        else:
            tiles.append(("weather", _tile("🌫️ 空氣品質", "—", "暫時無法取得")))
    if cal:
        named = [x for x in cal if x["off"] and x["desc"] and x["date"] >= today]
        if named:
            nd = (named[0]["date"] - today).days
            tiles.append(("holidays", _tile("📅 下一個國定假日", named[0]["desc"],
                                            f"{named[0]['date'].month}/{named[0]['date'].day}({V.WD[named[0]['date'].weekday()]})・"
                                            + ("就是今天 🎉" if nd == 0 else f"還有 {nd} 天"), small=True)))
    qs = got["qs"] or {}
    if watch:
        rows = []
        for c in watch[:5]:
            x = qs.get(c)
            if x and x["price"] and x["prev"]:
                diff = x["price"] - x["prev"]
                cls = "up" if diff > 0 else "down" if diff < 0 else "flat"
                rows.append((f"{c} <span class='nm'>{_esc(x['name'][:4])}</span>", f"{x['price']:,.2f} <span class='{cls}'>{diff / x['prev'] * 100:+.2f}%</span>"))
        tiles.append(("stock", _tile("⭐ 自選股", "", "漲紅跌綠" if rows else "暫時無法取得報價", rows)))
    if holds and qs:
        _, t = V.portfolio(holds, qs)
        if t["成本"]:
            c_ = "var(--up)" if t["損益"] > 0 else "var(--down)" if t["損益"] < 0 else ""
            tiles.append(("stock", _tile("💼 持股損益", f"{t['損益']:+,.0f}",
                                         f"報酬率 {t['損益'] / t['成本'] * 100:+.2f}%・今日 {t['今日']:+,.0f}",
                                         value_style=f"color:{c_}")))
    b = got["bank"]
    if b:
        cur = U.pref("fx_cur", "USD")
        show = list(dict.fromkeys([c for c in (cur, "USD", "JPY", "EUR") if c in b["rates"]]))[:3]
        rows = [(V.fx_label(c).rsplit(" ", 1)[0], f"{(b['rates'][c].get('cash') or b['rates'][c]['spot'])[1]:g}") for c in show]
        tiles.append(("fx", _tile("💱 換外幣(現鈔賣出)", "", f"{b['bank']}牌告", rows)))
    o = got["oil"]
    if o:
        rows = []
        for n_, p_, pv in zip(K.OIL_NAMES, o["prices"], o["prev"] or [None] * 4):
            ch = f" <span class='{'up' if p_ > pv else 'down'}'>{p_ - pv:+.1f}</span>" if pv and abs(p_ - pv) >= 0.05 else ""
            rows.append((n_.replace(" 無鉛汽油", "").replace("超級", ""), f"{p_:.1f}{ch}"))
        tiles.append(("oil", _tile("⛽ 中油油價", "", f"牌價日期 {o['date']}", rows)))
    bfavs = list(U.pref("bus_favs", []))
    if bfavs and all(_tdx_keys()):
        rows = [(f"{_esc(f['route'])} <span class='nm'>{_esc(f['name'][:6])}</span>", f"<span class='beta {cls}'>{_esc(t_)}</span>")
                for f, cls, t_ in bus_fav_eta(bfavs[:4])]
        tiles.insert(0, ("bus", _tile("🚌 公車常用站", "", f"{now:%H:%M} 即時到站", rows)))
    dd, period = _next_invoice_draw(today)
    inv = got["inv"]
    latest = inv[0]["title"] if inv else ""
    tiles.append(("invoice", _tile("🧾 統一發票", f"{dd.month}/{dd.day} 開獎", f"{period}" + (f"<br>最新已開:{_esc(latest)}" if latest else ""),
                                   small=True)))
    favs = U.pref("fav_cinemas", [])
    tiles.append(("movies", _tile("🎬 電影", "現在能看什麼?", f"常去戲院 {len(favs)} 間" if favs else "可在電影頁設定常去戲院",
                                  small=True)))
    link_text = {"bus": "公車 →", "weather": "天氣・空氣 →", "holidays": "假日行事曆 →", "stock": "股票 →", "fx": "匯率 →", "oil": "油價 →",
                 "invoice": "發票對獎 →", "movies": "電影時刻 →"}
    for i in range(0, len(tiles), 4):
        for j, (col, (pg, html)) in enumerate(zip(st.columns(4), tiles[i:i + 4])):
            with col, st.container(key=f"tile_{i + j}_{pg}"):  # 整張卡片都可以點
                more = f"<span class='more'>{link_text[pg]}</span></div>"
                st.markdown("<div class='home'>" + html[:-len("</div>")] + more + "</div>", unsafe_allow_html=True)
                st.page_link(PAGES[pg], label=link_text[pg])

    st.markdown("##### 🧰 小工具")
    tools = [("split", "聚餐分帳"), ("tools", "換算・計時"), ("parking", "找停車位"), ("wheel", "幸運轉盤"), ("shop", "比價"), ("photo", "大頭照")]
    for col, (k, lab) in zip(st.columns(6), tools):
        with col:
            st.page_link(PAGES[k], label=lab)


def page_settings():
    V.page_settings({
        "電影(開眼)": lambda: f"{len(K.MovieClient().list_cinemas('a02', force=True))} 間戲院",
        "天氣": lambda: K.fetch_weather("Taipei")["desc"], "油價": lambda: K.fetch_oil()["date"],
        "股票(證交所/Yahoo)": lambda: K.fetch_stock("0050", "1mo")["src"], "匯率(中間價)": lambda: f"{len(K.fetch_rates()['rates'])} 種",
        "發票(財政部)": lambda: K.fetch_invoice_periods()[0]["title"], "賓果(pilio)": lambda: f"{len(K.fetch_bingo())} 期",
        "比價 PChome": lambda: f"{len(S.search_pchome('滑鼠'))} 筆", "比價 momo": lambda: f"{len(S.search_momo('滑鼠'))} 筆", "比價 Yahoo": lambda: f"{len(S.search_yahoo('滑鼠'))} 筆",
        "比價 露天": lambda: f"{len(S.search_ruten('滑鼠'))} 筆"})


# ═════════ 🚌 公車常用站（TDX；跟「智慧交通規劃」公車 app 同一套資料） ═════════
def _tdx_keys():
    return L._secret("TDX_CLIENT_ID"), L._secret("TDX_CLIENT_SECRET")


@st.cache_data(ttl=3000, show_spinner=False)
def _tdx_tok(cid, sec):
    return TD.token(cid, sec)


@st.cache_data(ttl=86400, show_spinner="載入路線清單…")
def bus_routes(city):
    return TD.routes(_tdx_tok(*_tdx_keys()), city)


@st.cache_data(ttl=86400, show_spinner="載入站牌…")
def bus_sor(city, route):
    return TD.stop_of_route(_tdx_tok(*_tdx_keys()), city, route)


@st.cache_data(ttl=30, show_spinner=False)
def bus_etas(city, uids):
    return TD.stops_eta(_tdx_tok(*_tdx_keys()), city, list(uids))


def bus_fav_eta(favs):
    """常用站 → [(常用站, 樣式, 文字)]；同一個縣市的站一次查完（TDX 每分鐘只能查 5 次）。"""
    by = {}
    for f in favs:
        by.setdefault(f["city"], set()).add(f["stop"])
    raw = {}
    for city, uids in by.items():
        for e in U.quiet(bus_etas, city, tuple(sorted(uids))) or []:
            raw.setdefault((e.get("StopUID"), TD.zh(e.get("RouteName"))), []).append(e)
    out = []
    for f in favs:
        cands = raw.get((f["stop"], f["route"]), [])
        e = next((c for c in cands if f.get("sub") and c.get("SubRouteUID") == f["sub"]), None) or \
            next((c for c in cands if c.get("Direction", 0) == f.get("dir", 0)), None)
        out.append((f, *TD.eta_text(e)))
    return out


def page_bus():
    hero("🚌", "公車常用站", "常搭的公車站加進來，首頁直接看到下一班幾分到（交通部 TDX 即時資料）")
    if not all(_tdx_keys()):
        st.info("要先設定 TDX 金鑰（免費）：到 Streamlit 這個 app 的 ⋮ → Settings → Secrets，加上\n\n"
                "`TDX_CLIENT_ID = \"…\"`\n\n`TDX_CLIENT_SECRET = \"…\"`\n\n跟公車 app 用同一組就可以。")
        return
    favs = list(U.pref("bus_favs", []))
    if favs:
        auto = st.toggle("自動更新（每 60 秒）", value=True, key="bus_auto")

        def show():
            for i, (f, cls, txt) in enumerate(bus_fav_eta(favs)):
                c1, c2 = st.columns([10, 1], vertical_alignment="center")
                c1.markdown(f"<div class='busfav'><div><b>🚌 {_esc(f['route'])}</b> <span class='bs'>往 {_esc(f.get('to', ''))}</span>"
                            f"<div class='bs'>{_esc(f['name'])}</div></div><div class='beta {cls}'>{_esc(txt)}</div></div>",
                            unsafe_allow_html=True)
                if c2.button("✕", key=f"busfav_rm_{i}", help="從常用移除"):
                    U.remember("bus_favs", [x for j, x in enumerate(favs) if j != i])
                    st.rerun()
            st.caption(f"{K.tw_now():%H:%M:%S} 更新")
        st.fragment(run_every=60 if auto else None)(show)()
    else:
        st.caption("還沒有常用站，從下面加。")
    st.markdown("##### ➕ 加常用站")
    names = list(TD.CITIES)
    saved = U.pref("bus_city", "臺南市")
    c1, c2 = st.columns(2)
    cname = c1.selectbox("縣市", names, index=names.index(saved) if saved in names else 0, key="bus_city_sel")
    U.remember("bus_city", cname)
    city = TD.CITIES[cname]
    rts = safe(bus_routes, city) or []
    route = c2.selectbox("路線（可以直接打字搜尋）", rts, index=None, placeholder="例如:紅4、綠幹線", key=f"bus_route_{city}")
    if not route:
        return
    subs = safe(bus_sor, city, route) or []
    if not subs:
        st.caption("查不到這條路線的站牌。")
        return
    d1, d2 = st.columns(2)
    si = d1.selectbox("方向", range(len(subs)), format_func=lambda i: subs[i]["name"], key=f"bus_dir_{city}_{route}")
    seq = subs[si]["stops"]
    ki = d2.selectbox("上車站（可以直接打字搜尋）", range(len(seq)), index=None, placeholder="選上車站",
                      format_func=lambda i: f"{i + 1}. {seq[i][1]}", key=f"bus_stop_{city}_{route}_{si}")
    if ki is None:
        return
    item = {"city": city, "route": route, "sub": subs[si]["sub"], "dir": subs[si]["dir"], "stop": seq[ki][0],
            "name": seq[ki][1], "to": TD.headsign(subs[si]["name"], seq)}
    have = any((f["stop"], f["route"], f.get("sub")) == (item["stop"], item["route"], item["sub"]) for f in favs)
    if st.button("★ 已在常用" if have else "☆ 加入常用", disabled=have, type="primary"):
        U.remember("bus_favs", favs + [item])
        st.rerun()


# ═════════ 導覽 ═════════
PAGES = {
    "home": st.Page(page_home, title="首頁", icon="🏠", default=True),
    "weather": st.Page(page_weather, title="天氣・空氣", icon="⛅", url_path="weather"),
    "alerts": st.Page(V.page_alerts, title="防災資訊", icon="⚠️", url_path="alerts"),
    "holidays": st.Page(V.page_holidays, title="假日行事曆", icon="📅", url_path="holidays"),
    "parking": st.Page(V.page_parking, title="停車", icon="🅿️", url_path="parking"),
    "bus": st.Page(page_bus, title="公車", icon="🚌", url_path="bus"),
    "stock": st.Page(page_stock, title="股票", icon="📈", url_path="stock"),
    "fx": st.Page(page_fx, title="匯率", icon="💱", url_path="fx"),
    "oil": st.Page(page_oil, title="油價", icon="⛽", url_path="oil"),
    "invoice": st.Page(page_invoice, title="發票對獎", icon="🧾", url_path="invoice"),
    "shop": st.Page(page_shop, title="比價", icon="🛒", url_path="shop"),
    "movies": st.Page(page_movies, title="電影時刻", icon="🎬", url_path="movies"),
    "wheel": st.Page(page_wheel, title="幸運轉盤", icon="🎡", url_path="wheel"),
    "bingo": st.Page(page_bingo, title="賓果", icon="🎰", url_path="bingo"),
    "lotto": st.Page(page_lotto, title="樂透", icon="🏆", url_path="lotto"),
    "advisor": st.Page(page_advisor, title="AI 下注顧問", icon="🤖", url_path="advisor"),
    "split": st.Page(V.page_split, title="聚餐分帳", icon="🍱", url_path="split"),
    "tools": st.Page(V.page_tools, title="換算・BMI・計時", icon="📐", url_path="tools"),
    "photo": st.Page(page_photo, title="大頭照", icon="📸", url_path="photo"),
    "settings": st.Page(page_settings, title="設定與診斷", icon="⚙️", url_path="settings"),
}
U.HOME_PAGE = PAGES["home"]
_G = lambda *ks: [PAGES[k] for k in ks]  # noqa: E731
nav = st.navigation({"": _G("home"), "生活": _G("weather", "alerts", "holidays", "bus", "parking"),
                     "理財": _G("stock", "fx", "oil", "invoice", "shop"),
                     "娛樂": _G("movies", "wheel", "bingo", "lotto", "advisor"),
                     "工具": _G("split", "tools", "photo", "settings")}, position="top")
nav.run()

st.divider()
st.caption("資料來源:開眼電影網・wttr.in・中央氣象署・環境部・人事行政總處・臺北市交通局・台灣中油・證交所・櫃買中心・財政部・"
           "第一銀行・pilio・exchangerate-api　|　設定只存在你的瀏覽器　|　彩券相關內容僅供參考,請理性購買")
U.prefs_sync()
