# -*- coding: utf-8 -*-
"""🎡 幸運轉盤:前端動畫(Canvas)。先用加密等級亂數『依權重決定贏家』,再把轉盤轉到該扇形,所以機率精確、不受動畫影響。"""
import json
import re

PRESETS = {
    "🍱 晚餐吃什麼": [("拉麵", 1), ("滷肉飯", 1), ("麥當勞", 1), ("火鍋", 1), ("水餃", 1), ("壽司", 1), ("吃土", 0.3)],
    "🥤 飲料喝什麼": [("珍珠奶茶", 1), ("拿鐵", 1), ("紅茶", 1), ("多多綠", 1), ("氣泡水", 1)],
    "🎬 看什麼類型": [("動作", 1), ("喜劇", 1), ("愛情", 1), ("動畫", 1), ("驚悚", 1), ("科幻", 1)],
    "🧹 今天誰負責": [("我", 1), ("你", 1), ("他", 1), ("她", 1)],
}


def parse_lines(text):
    """每行一個選項;行尾 *數字 為權重(預設 1)。例:拉麵*3"""
    out = []
    for line in (text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^(.*?)\s*[*×xX]\s*(\d+(?:\.\d+)?)$", line)
        name, w = (m.group(1).strip(), float(m.group(2))) if m and m.group(1).strip() else (line, 1.0)
        out.append((name[:30], min(max(w, 0.1), 100.0)))
    return out[:60]


def to_lines(items):
    return [n if abs(w - 1) < 1e-9 else f"{n}*{w:g}" for n, w in items]


_PURE = r"""
function sliceAt(list, deg){const T=list.reduce((a,x)=>a+x.w,0);const th=((360-(((deg%360)+360)%360))%360)/360*T;let acc=0;for(let i=0;i<list.length;i++){acc+=list[i].w;if(th<acc)return i}return list.length-1}
function pickWinner(list, r){const T=list.reduce((a,x)=>a+x.w,0);let t=r*T,acc=0;for(let i=0;i<list.length;i++){acc+=list[i].w;if(t<acc)return i}return list.length-1}
function targetFor(list, win, A, r1, r2){const T=list.reduce((a,x)=>a+x.w,0);let s=0;for(let i=0;i<win;i++)s+=list[i].w;const lo=s/T*360,hi=(s+list[win].w)/T*360;const off=lo+(0.12+0.76*r1)*(hi-lo);const base=(((A%360)+360)%360);const delta=(((360-off)-base)%360+360)%360;return A+delta+360*(5+Math.floor(r2*3))}
"""

_HTML = r"""<!DOCTYPE html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{box-sizing:border-box}body{margin:0;padding:6px;font-family:system-ui,"Noto Sans TC","PingFang TC","Microsoft JhengHei",sans-serif;background:transparent}
.box{background:#fff;color:#1b2030;border-radius:24px;padding:16px;box-shadow:0 10px 30px rgba(0,0,0,.16);display:flex;gap:20px;flex-wrap:wrap;justify-content:center;align-items:flex-start}
.ww{position:relative;flex:1 1 300px;max-width:470px;padding-top:14px}canvas{width:100%;display:block;cursor:pointer;touch-action:manipulation}
.ptr{position:absolute;left:50%;top:0;transform:translateX(-50%);width:0;height:0;border-left:15px solid transparent;border-right:15px solid transparent;border-top:34px solid #e5484d;filter:drop-shadow(0 3px 3px rgba(0,0,0,.35));z-index:2}
.side{flex:1 1 230px;min-width:210px;display:flex;flex-direction:column;gap:10px}
#res{font-size:1.55rem;font-weight:800;text-align:center;padding:14px 10px;border-radius:16px;background:linear-gradient(120deg,#fff1e8,#fff8e1);min-height:76px;display:grid;place-items:center;line-height:1.3;word-break:break-all}
#res.pop{animation:pop .5s ease}@keyframes pop{0%{transform:scale(.7)}60%{transform:scale(1.08)}100%{transform:scale(1)}}
button{font:700 1rem inherit;border:0;border-radius:14px;padding:13px;cursor:pointer;color:#fff;background:linear-gradient(135deg,#d9441a,#ff9a5c);min-height:48px}
button.g{background:#eef0f5;color:#1b2030;font-size:.9rem;padding:9px;min-height:38px}button:disabled{opacity:.55;cursor:default}
label{font-size:.9rem;display:flex;align-items:center;gap:8px;cursor:pointer;min-height:30px}
#hist{font-size:.88rem;max-height:150px;overflow:auto;padding-left:20px;margin:0;color:#444}#hist li{margin:2px 0}
h4{margin:2px 0;font-size:.9rem;color:#667085}
</style></head><body><div class="box">
<div class="ww"><div class="ptr"></div><canvas id="cv"></canvas></div>
<div class="side"><div id="res">準備好了嗎?</div><button id="spin">🎰 開始旋轉</button>
<label><input type="checkbox" id="snd" checked> 🔊 轉動音效</label><label><input type="checkbox" id="rm"> 🗑️ 抽中後從轉盤移除(不重複抽)</label>
<button class="g" id="reset">↺ 重設轉盤與紀錄</button><h4>📜 抽籤紀錄</h4><ol id="hist"></ol></div></div>
<script>
/*PURE*/__PURE__/*END*/
const ITEMS=__DATA__;
let list=ITEMS.map(([t,w])=>({t:t,w:Math.max(+w||1,0.1)})),angle=0,spinning=false,lastIdx=-1;
const cv=document.getElementById('cv'),ctx=cv.getContext('2d'),$=id=>document.getElementById(id);
const rnd=()=>{const a=new Uint32Array(1);crypto.getRandomValues(a);return a[0]/4294967296};
let AC=null;function tick(){if(!$('snd').checked)return;try{AC=AC||new (window.AudioContext||window.webkitAudioContext)();const o=AC.createOscillator(),g=AC.createGain();o.frequency.value=900;g.gain.value=.05;o.connect(g);g.connect(AC.destination);o.start();o.stop(AC.currentTime+.04)}catch(e){}}
function color(i){return 'hsl('+((i*137.508)%360)+' 72% 62%)'}
function fit(){const w=Math.min(cv.parentElement.clientWidth,470),d=window.devicePixelRatio||1;cv.width=w*d;cv.height=w*d;cv.style.height=w+'px';draw()}
function draw(){const W=cv.width,c=W/2,R=c-W*.02;ctx.clearRect(0,0,W,W);
if(!list.length){ctx.fillStyle='#667085';ctx.font='700 '+W/16+'px sans-serif';ctx.textAlign='center';ctx.fillText('請先加入選項',c,c);return}
const T=list.reduce((a,x)=>a+x.w,0);let a0=-Math.PI/2+angle*Math.PI/180;
list.forEach((it,i)=>{const sw=it.w/T*2*Math.PI;ctx.beginPath();ctx.moveTo(c,c);ctx.arc(c,c,R,a0,a0+sw);ctx.closePath();ctx.fillStyle=color(i);ctx.fill();ctx.lineWidth=W/170;ctx.strokeStyle='#fff';ctx.stroke();
ctx.save();ctx.translate(c,c);ctx.rotate(a0+sw/2);ctx.textAlign='right';ctx.textBaseline='middle';ctx.fillStyle='#1b2030';
const n=list.length,fs=Math.max(W/(n>14?38:n>9?28:n>6?22:18),11);ctx.font='700 '+fs+'px system-ui,"Noto Sans TC","Microsoft JhengHei",sans-serif';
let t=it.t;const mx=R*.68;while(ctx.measureText(t).width>mx&&t.length>1)t=t.slice(0,-1);if(t!==it.t)t+='…';ctx.fillText(t,R-W/32,0);ctx.restore();a0+=sw});
ctx.beginPath();ctx.arc(c,c,W/15,0,7);ctx.fillStyle='#fff';ctx.fill();ctx.lineWidth=W/90;ctx.strokeStyle='#e5484d';ctx.stroke()}
function spin(){if(spinning||list.length<2){if(list.length<2)$('res').textContent='至少需要 2 個選項';return}
spinning=true;$('spin').disabled=true;$('res').classList.remove('pop');$('res').textContent='🎲 命運旋轉中…';
const win=pickWinner(list,rnd()),from=angle,to=targetFor(list,win,angle,rnd(),rnd()),dur=4600+rnd()*1600,t0=performance.now();lastIdx=sliceAt(list,from);
(function step(now){const p=Math.min((now-t0)/dur,1),e=1-Math.pow(1-p,4);angle=from+(to-from)*e;const ix=sliceAt(list,angle);if(ix!==lastIdx){lastIdx=ix;tick()}draw();
if(p<1){requestAnimationFrame(step)}else{angle=to%360;spinning=false;$('spin').disabled=false;finish(win)}})(t0)}
function finish(win){const w=list[win].t;$('res').textContent='🎉 '+w;$('res').classList.add('pop');const li=document.createElement('li');li.textContent=w;$('hist').prepend(li);
if($('rm').checked){list.splice(win,1);setTimeout(draw,700)}}
$('spin').onclick=spin;cv.onclick=spin;document.addEventListener('keydown',e=>{if(e.code==='Space'){e.preventDefault();spin()}});
$('reset').onclick=()=>{if(spinning)return;list=ITEMS.map(([t,w])=>({t:t,w:Math.max(+w||1,0.1)}));angle=0;$('hist').innerHTML='';$('res').textContent='準備好了嗎?';draw()};
window.addEventListener('resize',fit);fit();
</script></body></html>"""


def wheel_html(items):
    data = json.dumps([[n, w] for n, w in items], ensure_ascii=False).replace("</", "<\\/")
    return _HTML.replace("__PURE__", _PURE).replace("__DATA__", data)


def pure_js():
    return _PURE
