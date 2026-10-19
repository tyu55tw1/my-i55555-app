# -*- coding: utf-8 -*-
"""共用 UI 工具:樣式、小元件、設定保存(瀏覽器 localStorage)、定位、並行抓取。"""
from __future__ import annotations

import html as _html
import json
import logging
from concurrent.futures import ThreadPoolExecutor, wait

import streamlit as st

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
    navigator.geolocation.getCurrentPosition(
      p => { msg.textContent = ""; setTriggerValue("pos", {lat: p.coords.latitude, lon: p.coords.longitude, acc: p.coords.accuracy}); },
      e => { msg.textContent = e.code === 1 ? "已拒絕定位權限,請在瀏覽器網址列允許位置存取" : "定位失敗:" + e.message; },
      {enableHighAccuracy: true, timeout: 12000, maximumAge: 60000});
  };
}
"""
_GEO_CSS = """
button{font:inherit;font-weight:700;padding:.45rem .9rem;border-radius:12px;cursor:pointer;
  border:1px solid rgba(128,128,128,.35);background:rgba(128,128,128,.12);color:var(--st-text-color, inherit);min-height:2.6rem}
button:hover{border-color:#ff6b3d;color:#ff6b3d}
span{margin-left:.6rem;font-size:.85rem;opacity:.75}
"""

try:
    _bridge = st.components.v2.component("lifeapp_prefs_bridge", js=_BRIDGE_JS)
    _geo = st.components.v2.component("lifeapp_geo", html="<div><button></button><span></span></div>", css=_GEO_CSS, js=_GEO_JS)
except Exception:  # noqa: BLE001  # 舊版 Streamlit 沒有 components.v2:設定只存在這次使用中
    _bridge = _geo = None


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
