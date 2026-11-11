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

# 「打字改點選」的選擇畫面:分區方塊(最近用過/常用…)＋搜尋框＋點了才出現的打字欄＋大按鈕數字鍵盤。
# 全部在瀏覽器裡處理(按數字不用等伺服器),選好才回傳 "v:值"
_CHOOSE_JS = """
export default function(component) {
  const { data, setTriggerValue, parentElement } = component;
  const root = parentElement.querySelector(".ch");
  const sig = JSON.stringify(data || {});
  if (root.dataset.sig === sig) return;
  root.dataset.sig = sig;
  root.innerHTML = "";
  const d = data || {};
  const send = v => setTriggerValue("pick", "v:" + String(v));
  const mk = (tag, cls, txt) => { const e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
  const btn = (cls, txt, fn) => { const b = mk("button", cls, txt); b.type = "button"; b.onclick = fn; return b; };
  let q = null;
  if (d.search) { q = mk("input", "q"); q.type = "search"; q.placeholder = d.ph || "打字搜尋…"; root.appendChild(q); }
  const all = [], secs = [];
  (d.sections || []).forEach(s => {
    const box = mk("div", "sec");
    if (s.t) box.appendChild(mk("div", "st", s.t));
    const g = mk("div", "g " + (s.size || ""));
    (s.items || []).forEach(it => {
      const b = btn(it[1] === d.cur ? "on" : "", it[0], () => { b.classList.add("on"); send(it[1]); });
      g.appendChild(b);
      all.push([b, (it[0] + " " + it[1] + " " + (it[2] || "")).replace(/\\s+/g, "").toLowerCase(), box]);
    });
    box.appendChild(g); root.appendChild(box); secs.push(box);
  });
  const empty = mk("div", "empty", "找不到符合的選項"); empty.hidden = true; root.appendChild(empty);
  if (q) q.oninput = () => {
    const s = q.value.replace(/\\s+/g, "").toLowerCase();
    const seen = new Set(); let n = 0;
    all.forEach(([b, t, box]) => { const ok = !s || t.includes(s); b.hidden = !ok; if (ok) { n++; seen.add(box); } });
    secs.forEach(box => { box.hidden = !!s && !seen.has(box); });
    empty.hidden = n > 0 || !all.length;
  };
  if (d.text) {   // 自己打字:有 btn 的話要先點那顆才出現打字欄(避免一打開就跳鍵盤)
    const t = d.text, wrap = mk("div", "sec tx");
    if (t.t) wrap.appendChild(mk("div", "st", t.t));
    const row = mk("div", "row"), inp = mk("input", "q");
    inp.type = "text"; inp.placeholder = t.ph || ""; inp.value = t.init || ""; inp.enterKeyHint = "done";
    const go = () => { const v = inp.value.trim(); if (v) send(v); };
    inp.onkeydown = e => { if (e.key === "Enter") go(); };
    row.append(inp, btn("ok", t.ok || "確定", go));
    if (t.btn) {
      const open = btn("more", t.btn, () => { open.hidden = true; row.hidden = false; inp.focus(); });
      row.hidden = true; wrap.appendChild(open);
    }
    wrap.appendChild(row); root.appendChild(wrap);
  }
  if (d.pad) {    // 數字鍵盤:打開時顯示目前的值,第一個數字會蓋掉它
    const p = d.pad, wrap = mk("div", "sec pad");
    if (p.t) wrap.appendChild(mk("div", "st", p.t));
    let s = p.init || "", fresh = true;
    const disp = mk("div", "disp"), msg = mk("div", "msg");
    const fmt = x => { const [i, f] = x.split("."); return i.replace(/\\B(?=(\\d{3})+(?!\\d))/g, ",") + (f !== undefined ? "." + f : ""); };
    const show = () => { disp.textContent = (s ? fmt(s) : "0") + (p.unit ? " " + p.unit : ""); disp.classList.toggle("ph", !s || fresh); msg.textContent = ""; };
    const press = k => {
      if (k === "⌫") s = fresh ? "" : s.slice(0, -1);
      else if (k === "清除") s = "";
      else if (k === ".") { if (fresh) s = ""; if (!s.includes(".")) s = (s || "0") + "."; }
      else { if (fresh) s = ""; s = (s === "0" ? "" : s) + k; if (/^0+$/.test(s)) s = "0"; if (s.length > 15) s = s.slice(0, 15); }
      fresh = false; show();
    };
    const kp = mk("div", "kp");
    ["1", "2", "3", "4", "5", "6", "7", "8", "9", "00", "0", p.dec ? "." : "⌫"].forEach(k => kp.appendChild(btn("", k, () => press(k))));
    const bot = mk("div", "kp bot");
    bot.appendChild(btn("clr", "清除", () => press("清除")));
    if (p.dec) bot.appendChild(btn("", "⌫", () => press("⌫")));
    const ok = btn("ok" + (p.dec ? "" : " w2"), "確定", () => {
      const v = Number(s);
      if (!s || isNaN(v)) { msg.textContent = "請先按數字"; return; }
      if (p.min != null && v < p.min) { msg.textContent = "最少 " + p.min; return; }
      if (p.max != null && v > p.max) { msg.textContent = "最多 " + p.max.toLocaleString(); return; }
      send(s.replace(/\\.$/, ""));
    });
    bot.appendChild(ok);
    wrap.append(disp, msg, kp, bot); root.appendChild(wrap); show();
  }
}
"""
_CHOOSE_CSS = _PICK_CSS.replace(".pk{", ".ch{") + """
.sec{margin-bottom:1rem}.sec[hidden]{display:none}
.st{font-size:.85rem;opacity:.75;margin:0 0 .4rem}
.row{display:flex;gap:.5rem}.row[hidden]{display:none}.row .q{margin:0;flex:1}
button.ok{background:#ff6b3d;border-color:#ff6b3d;color:#fff;padding:.5rem 1.1rem}
button.ok:hover{color:#fff;filter:brightness(1.08)}
button.more{width:100%}
.pad{max-width:420px;margin-left:auto;margin-right:auto}
.disp{font-size:2rem;font-weight:700;text-align:right;padding:.4rem .8rem;border-radius:14px;background:rgba(128,128,128,.10);
  border:1px solid rgba(128,128,128,.35);min-height:3rem;line-height:3rem;overflow:hidden;white-space:nowrap}
.disp.ph{opacity:.55}
.msg{color:#e5484d;font-size:.9rem;min-height:1.3rem;padding:.15rem .2rem}
.kp{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.5rem;margin-bottom:.5rem}
.kp button{font-size:1.45rem;min-height:3.2rem;padding:.3rem}
.kp.bot button{font-size:1.1rem}.kp .w2{grid-column:span 2}
"""

try:
    _bridge = st.components.v2.component("lifeapp_prefs_bridge", js=_BRIDGE_JS)
    _geo = st.components.v2.component("lifeapp_geo", html="<div><button></button><span></span></div>", css=_GEO_CSS, js=_GEO_JS)
    _picker = st.components.v2.component("lifeapp_picker", html="<div class='pk'></div>", css=_PICK_CSS, js=_PICK_JS)
    _chooser = st.components.v2.component("lifeapp_chooser", html="<div class='ch'></div>", css=_CHOOSE_CSS, js=_CHOOSE_JS)
except Exception:  # noqa: BLE001  # 舊版 Streamlit 沒有 components.v2:設定只存在這次使用中
    _bridge = _geo = _picker = _chooser = None


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


# ════════════════════════════════════════════════════════════════════
#  打字改點選:取代 text_input / number_input(iPhone 點打字欄會跳鍵盤)
#  常用、最近用過的排成方塊,點一下就填好;真的要打字才打字。值都存在 st.session_state[key]。
# ════════════════════════════════════════════════════════════════════
def recent(field) -> list:
    """這個欄位最近用過的值(新的在前)。存在設定裡,會跟其他設定一起搬家、同步。"""
    r = pref("recent", {})
    v = r.get(field) if isinstance(r, dict) else None
    return list(v) if isinstance(v, list) else []


def recent_add(field, value, n=8):
    if value is None or value == "":
        return
    r = pref("recent", {})
    r = dict(r) if isinstance(r, dict) else {}
    new = ([value] + [x for x in r.get(field) or [] if x != value])[:n]
    if r.get(field) != new:
        r[field] = new
        remember("recent", r)


def recent_pills(field, target_key, label="最近搜尋", on_pick=None):
    """打字欄下面的「最近搜尋」方塊:點一下把值填進 target_key 那個打字欄。"""
    items = [x for x in recent(field) if isinstance(x, str) and x]
    if not items:
        return
    pk = f"rp_{target_key}"

    def go():
        v = st.session_state.get(pk)
        if v:
            st.session_state[target_key] = v
            st.session_state[pk] = None
            if on_pick:
                on_pick()

    st.pills(label, items, key=pk, on_change=go, label_visibility="collapsed")


def _field_btn(box, label, shown, key, help=None, disabled=False):
    """標籤＋顯示目前值的大按鈕(跟 pick 同樣子),回傳有沒有被按。"""
    box.markdown(f"<p style='font-size:.875rem;margin:0 0 calc(1rem + .3rem);line-height:1.4'>{_esc(label)}</p>", unsafe_allow_html=True)
    shown = re.sub(r"([!-/:-@\[-`{-~])", r"\\\1", str(shown))
    return box.button(f"{shown}　▾", key=f"pkb_{key}", width="stretch", help=help, disabled=disabled)


def _size(labels):
    longest = max((len(str(x)) for x in labels), default=0)
    return "xlong" if longest > 14 else "long" if longest > 5 else ""


def _sec(title, items):
    """items:字串,或 (顯示文字, 值[, 額外搜尋字]) → 選擇畫面的一個分區(沒有項目回傳 None)。"""
    out = []
    for it in items:
        it = (it, it) if not isinstance(it, (list, tuple)) else it
        out.append([str(it[0]), str(it[1])] + ([str(it[2])] if len(it) > 2 else []))
    return {"t": title, "items": out, "size": _size(x[0] for x in out)} if out else None


def _choose(key, title, data, done):
    """跳出選擇畫面;選好呼叫 done(字串),關掉回原畫面。"""
    def body():
        res = _chooser(key=f"chc_{key}", data=data, on_pick_change=lambda: None)
        v = getattr(res, "pick", None)
        if isinstance(v, str) and v.startswith("v:"):
            done(v[2:])
            st.rerun()

    st.dialog(title, width="large")(body)()


def _num_raw(v) -> str:
    if v is None:
        return ""
    f = float(v)
    return str(int(f)) if f.is_integer() and abs(f) < 1e15 else repr(f)


def _num_show(v) -> str:
    f = float(v)
    return f"{int(f):,}" if f.is_integer() else f"{f:,.6f}".rstrip("0").rstrip(".")


def amount_pick(label, key, min_value=0, max_value=None, value=None, presets=(), step=None, unit="", container=None,
                recent_field=None, placeholder="點一下輸入", help=None, on_change=None, preset_label=None):
    """取代 number_input:點了跳出「常用金額方塊＋最近用過＋大按鈕數字鍵盤」,不叫出手機鍵盤。

    回傳值型別照原本 number_input:min/max/value/step 有一個是 float 就回 float,否則回 int;還沒填(value=None)回傳 None。
    presets:常用數字;preset_label:常用方塊的顯示文字(預設「數字＋單位」)。
    """
    is_float = any(isinstance(x, float) for x in (min_value, max_value, value, step))
    cast = (lambda s: float(s)) if is_float else (lambda s: int(round(float(s))))
    ss = st.session_state
    if key not in ss:
        ss[key] = None if value is None else cast(value)
    val = ss[key]
    box = (container or st).container(gap=None)
    if _chooser is None:   # 沒有 components.v2:退回原本的數字欄
        return box.number_input(label, min_value, max_value, value=val, step=step, key=f"{key}__ni", help=help)
    rf = recent_field or key
    show = preset_label or (lambda x: _num_show(x) + (f" {unit}" if unit else ""))
    if _field_btn(box, label, placeholder if val is None else show(val), key, help):
        ok = lambda x: isinstance(x, (int, float)) and (min_value is None or x >= min_value) and (max_value is None or x <= max_value)  # noqa: E731
        rec = [x for x in recent(rf) if ok(x)]
        secs = [_sec("🕘 最近用過", [(show(x), _num_raw(x)) for x in rec]),
                _sec("常用", [(show(x), _num_raw(x)) for x in presets if ok(x)])]
        secs = [{**s, "size": ""} for s in secs if s]   # 數字短:一列 3 格(電腦 6 格),鍵盤才不會被擠到下面
        data = {"sections": secs, "cur": _num_raw(val) if val is not None else None,
                "pad": {"t": "或用數字鍵盤輸入", "init": _num_raw(val), "dec": is_float, "min": min_value, "max": max_value, "unit": unit}}

        def done(s):
            v = cast(s)
            if min_value is not None:
                v = max(v, min_value)
            if max_value is not None:
                v = min(v, max_value)
            ss[key] = v
            recent_add(rf, v)
            if on_change:
                on_change()

        _choose(key, label, data, done)
    return val


def chip_text(label, key, presets=(), placeholder="", container=None, value="", recent_field=None, sections=(),
              empty_label=None, text_ph=None, text_btn=None, record=True, search=None, format_func=None, help=None,
              on_change=None, title=None, clean=None, top=()):
    """取代 text_input:點了跳出「最前面幾格＋最近用過＋分區＋常用方塊＋自己打字」,回傳字串(跟 text_input 一樣,沒填是 "")。

    top:最前面幾格 [(顯示, 值), …](例:🏠 家);empty_label:最前面多一格「清空」(值 "")。
    sections:最近用過後面的分區 [(標題, [(顯示, 值), …]), …]。
    text_btn:有給的話打字欄要先點這格才出現。record=False:不自動記最近用過(呼叫的地方自己確認有效再 recent_add)。
    format_func:按鈕上怎麼顯示目前的值;clean:選好的值先整理過(例如轉大寫)再存。
    """
    ss = st.session_state
    if key not in ss:
        ss[key] = value or ""
    val = ss[key] or ""
    box = (container or st).container(gap=None)
    if _chooser is None:
        return box.text_input(label, value=val, key=f"{key}__ti", placeholder=placeholder, help=help).strip()
    rf = recent_field or key
    shown = (format_func(val) if format_func else val) if val else (placeholder or empty_label or "點一下選擇…")
    if _field_btn(box, label, shown, key, help):
        rec = [x for x in recent(rf) if isinstance(x, str) and x]
        secs = [_sec(None, ([(empty_label, "")] if empty_label else []) + list(top))]
        secs += [_sec("🕘 最近用過", [((format_func(x) if format_func else x), x) for x in rec])]
        secs += [_sec(t, its) for t, its in sections] + [_sec("常用", presets)]
        secs = [s for s in secs if s]
        n = sum(len(s["items"]) for s in secs)
        data = {"sections": secs, "cur": val, "search": bool(search if search is not None else n > 24),
                "ph": "打字搜尋…", "text": {"t": None if text_btn else "自己打字", "ph": text_ph or placeholder,
                                          "init": val, "btn": text_btn, "ok": "確定"}}

        def done(s):
            ss[key] = clean(s.strip()) if clean else s.strip()
            if record:
                recent_add(rf, ss[key])
            if on_change:
                on_change()

        _choose(key, title or re.sub(r"[（(].*?[）)]", "", label).strip() or label, data, done)
    return val


# 世界城市(天氣用):顯示中文,背後用英文名查 wttr.in
WORLD_CITIES = {
    "🇯🇵 日本": [("東京", "Tokyo"), ("大阪", "Osaka"), ("京都", "Kyoto"), ("札幌", "Sapporo"), ("福岡", "Fukuoka"), ("名古屋", "Nagoya"),
               ("沖繩那霸", "Naha"), ("橫濱", "Yokohama"), ("神戶", "Kobe"), ("奈良", "Nara"), ("廣島", "Hiroshima"), ("仙台", "Sendai"),
               ("函館", "Hakodate"), ("金澤", "Kanazawa"), ("箱根", "Hakone"), ("鹿兒島", "Kagoshima")],
    "🇰🇷 韓國": [("首爾", "Seoul"), ("釜山", "Busan"), ("濟州", "Jeju"), ("仁川", "Incheon"), ("大邱", "Daegu")],
    "🇨🇳 港澳中國": [("香港", "Hong Kong"), ("澳門", "Macau"), ("上海", "Shanghai"), ("北京", "Beijing"), ("廈門", "Xiamen"),
                 ("廣州", "Guangzhou"), ("深圳", "Shenzhen"), ("成都", "Chengdu")],
    "🌴 東南亞": [("曼谷", "Bangkok"), ("清邁", "Chiang Mai"), ("普吉島", "Phuket"), ("新加坡", "Singapore"), ("吉隆坡", "Kuala Lumpur"),
              ("檳城", "Penang"), ("峇里島", "Bali"), ("雅加達", "Jakarta"), ("胡志明市", "Ho Chi Minh City"), ("河內", "Hanoi"),
              ("峴港", "Da Nang"), ("馬尼拉", "Manila"), ("宿霧", "Cebu"), ("長灘島", "Boracay"), ("金邊", "Phnom Penh"), ("暹粒", "Siem Reap")],
    "🌏 亞洲其他": [("杜拜", "Dubai"), ("伊斯坦堡", "Istanbul"), ("新德里", "New Delhi"), ("孟買", "Mumbai"), ("加德滿都", "Kathmandu"),
                ("馬爾地夫", "Male"), ("烏蘭巴托", "Ulaanbaatar")],
    "🇪🇺 歐洲": [("倫敦", "London"), ("巴黎", "Paris"), ("羅馬", "Rome"), ("米蘭", "Milan"), ("威尼斯", "Venice"), ("佛羅倫斯", "Florence"),
              ("巴塞隆納", "Barcelona"), ("馬德里", "Madrid"), ("里斯本", "Lisbon"), ("柏林", "Berlin"), ("慕尼黑", "Munich"),
              ("法蘭克福", "Frankfurt"), ("阿姆斯特丹", "Amsterdam"), ("布魯塞爾", "Brussels"), ("蘇黎世", "Zurich"), ("維也納", "Vienna"),
              ("布拉格", "Prague"), ("布達佩斯", "Budapest"), ("哥本哈根", "Copenhagen"), ("斯德哥爾摩", "Stockholm"), ("赫爾辛基", "Helsinki"),
              ("奧斯陸", "Oslo"), ("雷克雅維克", "Reykjavik"), ("愛丁堡", "Edinburgh"), ("都柏林", "Dublin"), ("雅典", "Athens"),
              ("聖托里尼", "Santorini"), ("莫斯科", "Moscow")],
    "🇺🇸 美洲": [("紐約", "New York"), ("洛杉磯", "Los Angeles"), ("舊金山", "San Francisco"), ("西雅圖", "Seattle"), ("拉斯維加斯", "Las Vegas"),
              ("芝加哥", "Chicago"), ("波士頓", "Boston"), ("華盛頓", "Washington DC"), ("邁阿密", "Miami"), ("夏威夷檀香山", "Honolulu"),
              ("關島", "Guam"), ("溫哥華", "Vancouver"), ("多倫多", "Toronto"), ("墨西哥城", "Mexico City"), ("聖保羅", "Sao Paulo"),
              ("布宜諾斯艾利斯", "Buenos Aires")],
    "🦘 大洋洲・非洲": [("雪梨", "Sydney"), ("墨爾本", "Melbourne"), ("布里斯本", "Brisbane"), ("伯斯", "Perth"), ("奧克蘭", "Auckland"),
                  ("皇后鎮", "Queenstown"), ("開羅", "Cairo"), ("開普敦", "Cape Town")],
}
CITY_ZH = {en: zh for g in WORLD_CITIES.values() for zh, en in g}


def city_zh(en: str) -> str:
    return CITY_ZH.get(en, en)


def city_pick(label, key, value="Tokyo", container=None, on_change=None, help=None):
    """世界城市方塊(分區、中英都能搜、最上面最近用過、最後可以打英文),回傳英文城市名。"""
    return chip_text(label, key, value=value, container=container, recent_field="wx_city", search=True, format_func=city_zh,
                     sections=[(g, [(zh, en) for zh, en in cs]) for g, cs in WORLD_CITIES.items()],
                     text_btn="⌨️ 其他城市(打英文)", text_ph="英文城市名,例如 Vancouver", on_change=on_change, help=help,
                     title="選城市")


# 熱門 ETF/個股(股票代號方塊用)
STOCKS = {
    "📊 熱門 ETF": [("0050", "元大台灣50"), ("006208", "富邦台50"), ("0056", "元大高股息"), ("00878", "國泰永續高股息"),
                 ("00919", "群益台灣精選高息"), ("00929", "復華台灣科技優息"), ("00713", "元大台灣高息低波"), ("00940", "元大台灣價值高息"),
                 ("0052", "富邦科技"), ("00692", "富邦公司治理"), ("00850", "元大臺灣ESG永續"), ("00881", "國泰台灣5G+"),
                 ("00679B", "元大美債20年"), ("00687B", "國泰20年美債"), ("00646", "元大S&P500"), ("00662", "富邦NASDAQ")],
    "🏭 熱門個股": [("2330", "台積電"), ("2317", "鴻海"), ("2454", "聯發科"), ("2308", "台達電"), ("2382", "廣達"), ("3711", "日月光投控"),
                 ("2303", "聯電"), ("2412", "中華電"), ("2881", "富邦金"), ("2882", "國泰金"), ("2891", "中信金"), ("2886", "兆豐金"),
                 ("2884", "玉山金"), ("2892", "第一金"), ("5880", "合庫金"), ("2002", "中鋼"), ("1301", "台塑"), ("2603", "長榮"),
                 ("2609", "陽明"), ("3008", "大立光"), ("2357", "華碩"), ("2379", "瑞昱"), ("3034", "聯詠"), ("2345", "智邦"),
                 ("3231", "緯創"), ("2356", "英業達"), ("6669", "緯穎"), ("1216", "統一"), ("2912", "統一超"), ("2207", "和泰車")],
}
STOCK_NAMES = {c: n for g in STOCKS.values() for c, n in g}


def stock_label(code: str) -> str:
    return f"{code} {STOCK_NAMES[code]}" if code in STOCK_NAMES else code


def stock_pick(label, key, value="0050", container=None, empty_label=None, on_change=None, help=None):
    """股票代號方塊(熱門 ETF/個股、自選股、最近用過,可搜尋代號或名稱,可自己打代號),回傳代號字串。"""
    watch = [c for c in pref("watch", []) if isinstance(c, str)]
    secs = ([("⭐ 自選股", [(stock_label(c), c) for c in watch])] if watch else []) + \
           [(g, [(f"{c} {n}", c) for c, n in cs]) for g, cs in STOCKS.items()]
    return chip_text(label, key, value=value, container=container, recent_field="stock_code", search=True, sections=secs,
                     format_func=stock_label, empty_label=empty_label, text_btn="⌨️ 自己打代號", text_ph="股票代號,例如 2330、00878",
                     on_change=on_change, help=help, title="選股票", clean=lambda s: s.upper().replace(" ", ""))
