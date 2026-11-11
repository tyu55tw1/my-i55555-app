# -*- coding: utf-8 -*-
"""共用 UI 工具:樣式、小元件、設定保存(瀏覽器 localStorage)、定位、並行抓取。"""
from __future__ import annotations

import hashlib
import html as _html
import json
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, wait

import streamlit as st

LOADED_AT = time.time()   # app.py 用來判斷檔案更新後要不要重新載入(雲端自動更新只重跑 app.py)

# 首頁在背景執行緒呼叫快取函式時,Streamlit 會警告缺少執行環境;這是預期行為,關掉避免洗版
logging.getLogger("streamlit.runtime.scriptrunner_utils.script_run_context").setLevel(logging.ERROR)

_esc = lambda x: _html.escape(str(x), quote=True).replace("$", "&#36;")  # noqa: E731


HOME_PAGE = None  # app.py 建好導覽後設定,用來在每頁放「回首頁」按鈕


def hero(icon, title, sub="", home=True):
    if home and HOME_PAGE is not None:
        with st.container(key="home_btn"):
            st.page_link(HOME_PAGE, label="回首頁", icon="🏠")
    st.markdown(f"<div class='hero'><span class='ico'>{icon}</span><div><h1>{title}</h1><p>{sub}</p></div></div>", unsafe_allow_html=True)


def safe(fn, *a, **k):
    try:
        return fn(*a, **k)
    except Exception as e:  # noqa: BLE001
        st.error(f"連線失敗:{type(e).__name__}:{e}")
        return None


def quiet(fn, *a, **k):
    """失敗時回傳 None、不顯示錯誤(首頁小卡片用)。"""
    try:
        return fn(*a, **k)
    except Exception:  # noqa: BLE001
        return None


def parallel(timeout=None, **jobs):
    """並行執行多個(已快取的)函式,回傳 {名稱: 結果或 None}。

    timeout:最多等幾秒;來不及的回傳 None,但會在背景繼續跑完並寫入快取,下次就有資料。
    """
    ex = ThreadPoolExecutor(max(1, min(10, len(jobs))))
    futs = {k: ex.submit(quiet, f) for k, f in jobs.items()}
    wait(futs.values(), timeout=timeout)
    ex.shutdown(wait=False)
    return {k: (f.result() if f.done() else None) for k, f in futs.items()}


def updown(diff, fmt="{:+,.2f}"):
    """台股慣例:漲紅跌綠。"""
    cls = "up" if diff > 0 else "down" if diff < 0 else "flat"
    return f"<span class='{cls}'>{fmt.format(diff)}</span>"


# ════════════════════════════════════════════════════════════════════
#  設定保存:存在瀏覽器 localStorage(每個人、每台裝置各自一份,不會混到別人)
# ════════════════════════════════════════════════════════════════════
_LS_KEY = "lifeapp.prefs.v1"
_BRIDGE_JS = """
export default function(component) {
  const { data, setStateValue } = component;
  const K = "%s";
  let cur = null;
  try { cur = window.localStorage.getItem(K); } catch (e) {}
  if (data && data.loaded) {
    if (data.reset) { try { window.localStorage.removeItem(K); } catch (e) {} }
    else if (data.save != null && data.save !== cur) { try { window.localStorage.setItem(K, data.save); } catch (e) {} }
  } else {
    setStateValue("stored", cur === null ? "" : cur);
  }
}
""" % _LS_KEY

_GEO_JS = """
export default function(component) {
  const { setTriggerValue, parentElement, data } = component;
  const btn = parentElement.querySelector("button");
  const msg = parentElement.querySelector("span");
  btn.textContent = (data && data.label) || "📍 用我的位置";
  btn.onclick = () => {
    if (!navigator.geolocation) { msg.textContent = "此瀏覽器不支援定位"; return; }
    msg.textContent = "定位中…";
    const ok = p => { msg.textContent = ""; setTriggerValue("pos", {lat: p.coords.latitude, lon: p.coords.longitude, acc: p.coords.accuracy}); };
    const fail = e => { msg.textContent = e.code === 1 ? "已拒絕定位權限,請在瀏覽器網址列允許位置存取" : "定位失敗:" + e.message; };
    // 先用 GPS(高精準);室內收不到常逾時(2026-11-11 安卓實測 Timeout expired)→ 改用網路定位(Wi-Fi/基地台)再試一次
    navigator.geolocation.getCurrentPosition(ok, e => {
      if (e.code === 1) return fail(e);
      msg.textContent = "改用網路定位…";
      navigator.geolocation.getCurrentPosition(ok, fail, {enableHighAccuracy: false, timeout: 15000, maximumAge: 300000});
    }, {enableHighAccuracy: true, timeout: 8000, maximumAge: 60000});
  };
}
"""
_GEO_CSS = """
button{font:inherit;font-weight:700;padding:.45rem .9rem;border-radius:12px;cursor:pointer;
  border:1px solid rgba(128,128,128,.35);background:rgba(128,128,128,.12);color:var(--st-text-color, inherit);min-height:2.6rem}
button:hover{border-color:#ff6b3d;color:#ff6b3d}
span{margin-left:.6rem;font-size:.85rem;opacity:.75}
"""

# 選擇畫面裡的方塊格:搜尋框邊打邊篩(在瀏覽器裡做,不用等伺服器),點一格回傳它的編號
_PICK_JS = """
export default function(component) {
  const { data, setTriggerValue, parentElement } = component;
  const root = parentElement.querySelector(".pk");
  const sig = JSON.stringify(data || {});
  if (root.dataset.sig === sig) return;
  root.dataset.sig = sig;
  root.innerHTML = "";
  const labels = (data && data.labels) || [];
  let q = null;
  if (data && data.search) {
    q = document.createElement("input");
    q.type = "search"; q.className = "q"; q.placeholder = data.ph || "打字搜尋…";
    root.appendChild(q);
  }
  const grid = document.createElement("div");
  grid.className = "g " + ((data && data.size) || "");
  const btns = labels.map((t, i) => {
    const b = document.createElement("button");
    b.type = "button"; b.textContent = t;
    if (i === data.cur) b.className = "on";
    b.onclick = () => { b.classList.add("on"); setTriggerValue("pick", i); };
    grid.appendChild(b);
    return b;
  });
  const empty = document.createElement("div");
  empty.className = "empty"; empty.textContent = "找不到符合的選項"; empty.hidden = true;
  root.appendChild(grid); root.appendChild(empty);
  if (q) q.oninput = () => {
    const s = q.value.replace(/\\s+/g, "").toLowerCase();
    let n = 0;
    btns.forEach((b, i) => { const ok = !s || labels[i].replace(/\\s+/g, "").toLowerCase().includes(s); b.hidden = !ok; if (ok) n++; });
    empty.hidden = n > 0;
  };
  const on = grid.querySelector(".on");
  if (on && labels.length > 12) setTimeout(() => on.scrollIntoView({block: "center"}), 50);
}
"""
_PICK_CSS = """
.pk{color:var(--st-text-color, inherit)}
.q{width:100%;box-sizing:border-box;font:inherit;font-size:16px;padding:.65rem .9rem;margin-bottom:.75rem;border-radius:12px;
  border:1px solid rgba(128,128,128,.45);background:rgba(128,128,128,.08);color:inherit;outline:none}
.q:focus{border-color:#ff6b3d}
.g{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.5rem}
.g.long{grid-template-columns:repeat(2,minmax(0,1fr))}
.g.xlong{grid-template-columns:minmax(0,1fr)}
@media (min-width:700px){.g{grid-template-columns:repeat(6,minmax(0,1fr))}.g.long{grid-template-columns:repeat(4,minmax(0,1fr))}
  .g.xlong{grid-template-columns:repeat(2,minmax(0,1fr))}}
button{font:inherit;font-size:1rem;font-weight:600;line-height:1.3;min-height:3.2rem;padding:.5rem .45rem;border-radius:14px;cursor:pointer;
  border:1px solid rgba(128,128,128,.35);background:rgba(128,128,128,.12);color:inherit;word-break:break-word}
button:hover{border-color:#ff6b3d;color:#ff6b3d}
button.on,button.on:hover{background:#ff6b3d;border-color:#ff6b3d;color:#fff}
button[hidden]{display:none}
.empty{opacity:.7;padding:1rem 0;text-align:center}
"""

try:
    _bridge = st.components.v2.component("lifeapp_prefs_bridge", js=_BRIDGE_JS)
    _geo = st.components.v2.component("lifeapp_geo", html="<div><button></button><span></span></div>", css=_GEO_CSS, js=_GEO_JS)
    _picker = st.components.v2.component("lifeapp_picker", html="<div class='pk'></div>", css=_PICK_CSS, js=_PICK_JS)
except Exception:  # noqa: BLE001  # 舊版 Streamlit 沒有 components.v2:設定只存在這次使用中
    _bridge = _geo = _picker = None


def prefs() -> dict:
    return st.session_state.setdefault("prefs", {})


def pref(name, default=None):
    v = prefs().get(name)
    return default if v is None else v


def remember(name, value):
    if prefs().get(name) != value:
        prefs()[name] = value


def rev() -> int:
    """設定版本號:讀入/匯入設定後 +1,讓用 key=f"xx_{rev()}" 的元件重新以設定值初始化。"""
    return st.session_state.get("prefs_rev", 0)


def replace_prefs(data: dict):
    st.session_state["prefs"] = dict(data)
    st.session_state["prefs_rev"] = rev() + 1


def prefs_ready() -> bool:
    return bool(st.session_state.get("_prefs_loaded"))


def prefs_sync():
    """放在每頁最後執行:第一次讀入瀏覽器存的設定,之後每次都把最新設定寫回瀏覽器。"""
    ss = st.session_state
    if _bridge is None:
        ss["_prefs_loaded"] = True
        return
    loaded = bool(ss.get("_prefs_loaded"))
    reset = ss.pop("_prefs_reset", False)
    res = _bridge(key="prefs_bridge", data={"loaded": loaded, "reset": reset,
                                            "save": json.dumps(prefs(), ensure_ascii=False, sort_keys=True) if loaded else None},
                  on_stored_change=lambda: None)
    if not loaded:
        raw = getattr(res, "stored", None)
        if raw is not None:
            try:
                data = json.loads(raw) if raw else {}
            except ValueError:
                data = {}
            ss["_prefs_loaded"] = True
            if data:
                merged = {**prefs(), **(data if isinstance(data, dict) else {})}
                replace_prefs(merged)
                st.rerun()


def geolocate(key="geo", label="📍 用我的位置"):
    """顯示定位按鈕;回傳 (lat, lon) 或 None。位置存在 session_state,換頁也還在。"""
    if _geo is None:
        return st.session_state.get("geo_pos")
    res = _geo(key=key, data={"label": label}, on_pos_change=lambda: None)
    pos = getattr(res, "pos", None)
    if pos and isinstance(pos, dict) and pos.get("lat") is not None:
        st.session_state["geo_pos"] = (float(pos["lat"]), float(pos["lon"]))
    return st.session_state.get("geo_pos")


# ════════════════════════════════════════════════════════════════════
#  選擇器:取代 st.selectbox(iPhone 點下拉會跳鍵盤＋長清單,很難選)
# ════════════════════════════════════════════════════════════════════
def _auto_key(prefix, label, labels):
    return prefix + hashlib.md5(json.dumps([label, labels], ensure_ascii=False).encode()).hexdigest()[:12]


def _find(opts, v):
    for i, o in enumerate(opts):
        if o == v:
            return i
    return None


def pick(label, options, index=0, key=None, format_func=str, placeholder=None, search=None,
         container=None, on_change=None, help=None):
    """用法跟 st.selectbox 一樣,回傳選到的選項(index=None 且還沒選時回傳 None)。

    畫面上是一顆顯示目前選項的按鈕,點了跳出選擇畫面(st.dialog),選項排成方塊,點一格就選好、關掉回原畫面。
    選項超過 20 個(或 search=True)時上方有搜尋框,打字即時篩選。值存在 st.session_state[key]。
    container:要放在 columns 裡就傳 c1(等同原本的 c1.selectbox)。
    """
    opts = list(options)
    labels = [str(format_func(o)) for o in opts]
    ss = st.session_state
    if key is None:
        key = _auto_key("pk_", label, labels)
    if key not in ss or (ss[key] is not None and _find(opts, ss[key]) is None) or (ss[key] is None and None not in opts and index is not None):
        ss[key] = None if index is None or not opts else opts[min(index, len(opts) - 1)]
    val = ss[key]
    cur = _find(opts, val)
    box = (container or st).container(gap=None)
    # Streamlit 的 markdown 外框有 -1rem 下邊距,這裡補回來,標籤才不會被按鈕蓋住
    box.markdown(f"<p style='font-size:.875rem;margin:0 0 calc(1rem + .3rem);line-height:1.4'>{_esc(label)}</p>", unsafe_allow_html=True)
    shown = labels[cur] if cur is not None else (placeholder or "請選擇…")
    # 按鈕文字會被當 Markdown(例如「2. 自立路」會變成編號清單只剩「自立路」),標點符號都跳脫
    shown = re.sub(r"([!-/:-@\[-`{-~])", r"\\\1", shown)
    if box.button(f"{shown}　▾", key=f"pkb_{key}", width="stretch", help=help, disabled=not opts):
        _pick_dialog(key, label, opts, labels, cur, search, on_change)
    return val


def _pick_dialog(key, label, opts, labels, cur, search, on_change):
    title = re.sub(r"[（(][^）)]*搜尋[^）)]*[）)]", "", label).strip() or "請選擇"
    many = search if search is not None else len(opts) > 20
    longest = max((len(x) for x in labels), default=0)
    size = "xlong" if longest > 14 else "long" if longest > 5 else ""

    def body():
        if _picker is None:   # 沒有 components.v2:退回一般按鈕
            for i, t in enumerate(labels):
                if st.button(t, key=f"pkf_{key}_{i}", width="stretch", type="primary" if i == cur else "secondary"):
                    _set(i)
            return
        res = _picker(key=f"pkc_{key}", data={"labels": labels, "cur": -1 if cur is None else cur, "search": bool(many),
                                               "ph": "打字搜尋…", "size": size}, on_pick_change=lambda: None)
        i = getattr(res, "pick", None)
        if isinstance(i, int) and 0 <= i < len(opts):
            _set(i)

    def _set(i):
        st.session_state[key] = opts[i]
        if on_change:
            on_change()
        st.rerun()

    st.dialog(title, width="large")(body)()


def seg(label, options, index=0, key=None, format_func=str, container=None):
    """只有 2~4 個短選項時用:直接排在頁面上的分段按鈕,回傳值跟 st.selectbox 一樣(一定有選一個)。"""
    opts = list(options)
    ss = st.session_state
    if key is None:
        key = _auto_key("sg_", label, [str(format_func(o)) for o in opts])
    last = key + "__last"
    if _find(opts, ss.get(last)) is None:
        ss[last] = opts[min(index or 0, len(opts) - 1)]
    if _find(opts, ss.get(key)) is None:
        ss[key] = ss[last]

    def keep():   # 再點一次已選的那格會變成沒選:改回原本的
        if ss.get(key) is None:
            ss[key] = ss[last]
        else:
            ss[last] = ss[key]

    v = (container or st).segmented_control(label, opts, key=key, format_func=format_func, on_change=keep)
    return ss[last] if v is None else v
