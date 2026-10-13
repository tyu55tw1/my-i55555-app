# -*- coding: utf-8 -*-
"""🛒 比價模組:PChome 24h / momo / Yahoo購物中心 / 露天 / 蝦皮。

各平台獨立查詢,任一平台失敗不影響其他平台。
另有「智慧篩選」(相關度、配件與異常低價偵測)與「同款比價」(把不同平台的同一個商品放在一起比)。
"""
import json
import re
import statistics
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

from core import UA, make_session

_S = make_session(retries=1)
_H = {"User-Agent": UA, "Accept": "application/json, text/plain, */*", "Accept-Language": "zh-TW,zh;q=0.9"}
PLATFORMS = ["PChome 24h", "momo 購物網", "Yahoo購物中心", "露天拍賣", "蝦皮購物"]
PLATFORM_COLOR = {"PChome 24h": "#e3002b", "momo 購物網": "#d6006f", "Yahoo購物中心": "#6001d2", "露天拍賣": "#1c6fd1", "蝦皮購物": "#ee4d2d"}
PLATFORM_SHORT = {"PChome 24h": "PChome", "momo 購物網": "momo", "Yahoo購物中心": "Yahoo", "露天拍賣": "露天", "蝦皮購物": "蝦皮"}


def _get(url, **kw):
    return _S.get(url, timeout=(5, 12), **kw)


def _post(url, **kw):
    return _S.post(url, timeout=(5, 12), **kw)


def to_price(v):
    """'1,290(原價…)' / '$1290' / 1290 → 1290.0;無法解析回傳 None。"""
    m = re.search(r"\d[\d,]*(?:\.\d+)?", str(v if v is not None else "").split("(")[0])
    return float(m.group().replace(",", "")) if m else None


def _num(v):
    try:
        return float(str(v).replace(",", "").strip("() "))
    except (TypeError, ValueError):
        return None


def _item(platform, title, price, url, img="", credit="", sold=None, rating=None, reviews=None, orig=None, ship=None, sold_text=""):
    return dict(platform=platform, title=title, price=price, url=url, img=img or "", credit=credit, sold=sold,
                sold_text=sold_text or (f"已售 {sold:,.0f}" if sold else ""), rating=rating, reviews=reviews,
                orig=orig if orig and orig > price else None, ship=ship)


# ════════════════════════════════════════════════════════════════════
#  各平台
# ════════════════════════════════════════════════════════════════════
def search_pchome(kw, limit=40):
    last = None
    for url in ("https://ecshweb.pchome.com.tw/search/v4.3/all/results", "https://ecshweb.pchome.com.tw/search/v3.3/all/results"):
        try:  # 新舊兩版欄位大小寫不同,都支援
            r = _get(url, params={"q": kw, "page": 1, "sort": "rnk/dc"}, headers=_H)
            r.raise_for_status()
            j = r.json()
            out = []
            for p in (j.get("Prods") or j.get("prods") or [])[:limit]:
                g = lambda k: p.get(k) if p.get(k) is not None else p.get(k[0].lower() + k[1:])  # noqa: E731
                name, pid, price = g("Name"), g("Id"), to_price(g("Price"))
                if name and pid and price:
                    pic = g("PicS") or g("PicB") or ""
                    img = ("https://img.pchome.com.tw/cs" + pic) if pic.startswith("/") else pic
                    out.append(_item("PChome 24h", name, price, f"https://24h.pchome.com.tw/prod/{pid}", img, "✅ 官方直營",
                                     rating=_num(g("ratingValue")), reviews=_num(g("reviewCount")), orig=to_price(g("OriginPrice"))))
            if out:
                return out
        except Exception as e:  # noqa: BLE001
            last = e
    if last:
        raise last
    return []


def search_momo(kw, limit=40):
    """momo 的搜尋 API 會擋伺服器,改讀搜尋頁裡內嵌的商品資料。"""
    r = _get("https://www.momoshop.com.tw/search/searchShop.jsp", params={"keyword": kw},
             headers={"User-Agent": UA, "Accept-Language": "zh-TW,zh;q=0.9", "Referer": "https://www.momoshop.com.tw/"})
    r.raise_for_status()
    t = r.text.replace('\\"', '"')
    i = t.find('"goodsInfoList":[')
    if i < 0:
        raise RuntimeError("momo 頁面沒有商品資料(可能被擋)")
    goods, _ = json.JSONDecoder().raw_decode(t[i + len('"goodsInfoList":'):])
    out = []
    for g in goods[:limit]:
        name, code = g.get("goodsName"), g.get("goodsCode")
        price = to_price(g.get("SALE_PRICE")) or to_price(str(g.get("goodsPrice", "")).replace("$", ""))
        if not (name and code and price):
            continue
        orig = to_price(((g.get("marketPriceModel") or {}).get("basePrice") or {}).get("price"))
        sales = (g.get("totalSalesInfo") or {}).get("text", "") if isinstance(g.get("totalSalesInfo"), dict) else ""
        img = g.get("imgUrl") or ""
        out.append(_item("momo 購物網", name, price, f"https://www.momoshop.com.tw/goods/GoodsDetail.jsp?i_code={code}",
                         img if img.startswith("http") else "", "✅ momo 平台", rating=_num(g.get("rating")),
                         reviews=_num(g.get("ratingTimes")), orig=orig, sold_text=sales.replace("總銷量", "已售 ")))
    return out


def search_yahoo(kw, limit=40):
    """Yahoo購物中心:讀搜尋頁裡內嵌的商品 JSON。"""
    r = _get("https://tw.buy.yahoo.com/search/product", params={"p": kw}, headers={"User-Agent": UA, "Accept-Language": "zh-TW"})
    r.raise_for_status()
    dec, seen, out = json.JSONDecoder(), set(), []
    for m in re.finditer(r'\{"ec_property"', r.text):
        try:
            o, _ = dec.raw_decode(r.text[m.start():])
        except ValueError:
            continue
        pid, title, price = o.get("ec_productid"), o.get("ec_title"), _num(o.get("ec_price"))
        if not (pid and title and price) or pid in seen:
            continue
        seen.add(pid)
        store = o.get("ec_storename") or ""
        out.append(_item("Yahoo購物中心", title, price, o.get("ec_item_url") or f"https://tw.buy.yahoo.com/gdsale/gdinfo.asp?gdid={pid}",
                         o.get("ec_image"), "✅ Yahoo 自營" if store == "自營" else f"🏬 {store or '商店'}",
                         sold=_num(o.get("ec_total_sales_count")) or None, rating=_num(o.get("ec_quality_rating")),
                         reviews=_num(o.get("ec_rating_count")), orig=_num(o.get("ec_listprice"))))
        if len(out) >= limit:
            break
    if not out:
        raise RuntimeError("Yahoo 頁面沒有商品資料")
    return out


def search_ruten(kw, limit=30, good_only=True):
    """露天:先搜尋商品編號,再一次取回明細(含運費、銷量)。信用良好 = 有 10 筆以上成交紀錄。"""
    r = _get("https://rtapi.ruten.com.tw/api/search/v3/index.php/core/prod", headers=_H,
             params={"q": kw, "type": "direct", "sort": "rnk/dc", "offset": 1, "limit": 60})
    r.raise_for_status()
    ids = [x["Id"] for x in (r.json().get("Rows") or []) if x.get("Id")]
    if not ids:
        return []
    r = _get("https://rtapi.ruten.com.tw/api/prod/v2/index.php/prod", headers=_H, params={"id": ",".join(ids[:60])})
    r.raise_for_status()
    out = []
    for p in r.json() or []:
        rng = p.get("PriceRange") or []
        price = _num(rng[0]) if rng else None
        sold = _num(p.get("SoldQty")) or 0
        if not (p.get("ProdName") and price) or p.get("StockStatus") == 0:
            continue
        if good_only and sold < 10:
            continue
        img = p.get("Image") or ""
        out.append(_item("露天拍賣", p["ProdName"], price, f"https://www.ruten.com.tw/item/show?{p['ProdId']}",
                         ("https://gcs.rimg.com.tw" + img) if img.startswith("/") else img, f"🛍️ 露天賣家・已售 {sold:,.0f}",
                         sold=sold or None, ship=_num(p.get("ShippingCost"))))
        if len(out) >= limit:
            break
    return out


def search_shopee(kw, limit=40, good_only=True):
    """蝦皮需登入驗證與防機器人檢查,伺服器端常被拒絕;成功時只保留『蝦皮商城/優選或評價 4.8 以上且有銷量』的賣家。"""
    r = _get("https://shopee.tw/api/v4/search/search_items", headers={
        **_H, "Referer": "https://shopee.tw/search?keyword=" + urllib.parse.quote(kw), "x-api-source": "pc",
        "x-requested-with": "XMLHttpRequest"},
        params={"by": "relevancy", "keyword": kw, "limit": 60, "newest": 0, "order": "desc",
                "page_type": "search", "scenario": "PAGE_GLOBAL_SEARCH", "version": 2})
    if r.status_code != 200:
        raise RuntimeError(f"蝦皮拒絕伺服器查詢(HTTP {r.status_code})")
    j = r.json()
    if j.get("error") or not j.get("items"):
        raise RuntimeError("蝦皮需要登入驗證才能查詢")
    out = []
    for it in j["items"]:
        b = it.get("item_basic") or {}
        price = to_price((b.get("price") or 0) / 100000)
        stars = ((b.get("item_rating") or {}).get("rating_star")) or 0
        sold = b.get("historical_sold") or 0
        official = bool(b.get("shopee_verified") or b.get("is_official_shop"))
        good = official or (stars >= 4.8 and sold >= 50)
        if good_only and not good:
            continue
        if b.get("name") and price and b.get("itemid"):
            credit = "🏅 蝦皮商城" if official else f"⭐ 評價 {stars:.1f}・已售 {sold}"
            out.append(_item("蝦皮購物", b["name"], price, f"https://shopee.tw/product/{b.get('shopid')}/{b['itemid']}",
                             f"https://down-tw.img.susercontent.com/file/{b['image']}" if b.get("image") else "", credit,
                             sold=sold or None, rating=stars or None, orig=to_price((b.get("price_before_discount") or 0) / 100000)))
        if len(out) >= limit:
            break
    return out


def compare(kw, platforms=tuple(PLATFORMS), good_only=True):
    """回傳 (所有商品, {平台: (筆數, 錯誤訊息或None)})。各平台同時查詢。"""
    fns = {"PChome 24h": search_pchome, "momo 購物網": search_momo, "Yahoo購物中心": search_yahoo,
           "露天拍賣": lambda k: search_ruten(k, good_only=good_only), "蝦皮購物": lambda k: search_shopee(k, good_only=good_only)}

    def run(p):
        try:
            return p, fns[p](kw), None
        except Exception as e:  # noqa: BLE001
            return p, [], f"{type(e).__name__}: {e}"

    items, status = [], {}
    with ThreadPoolExecutor(max(len(platforms), 1)) as ex:
        for p, res, err in ex.map(run, platforms):
            items += res
            status[p] = (len(res), err)
    return items, status


# ════════════════════════════════════════════════════════════════════
#  智慧篩選
# ════════════════════════════════════════════════════════════════════
ACCESSORY_WORDS = ["保護殼", "手機殼", "保護套", "皮套", "殼", "保護貼", "玻璃貼", "鋼化", "膜", "充電線", "傳輸線", "轉接頭", "充電器",
                   "支架", "腳架", "滑鼠墊", "鼠墊", "收納", "包", "替換", "配件", "適用", "相容", "副廠", "貼紙", "掛繩", "清潔",
                   "耗材", "濾網", "刷頭", "墨水", "碳粉", "腕托", "按鍵帽", "鍵帽",
                   "專用", "內鍋", "內膽", "鍋蓋", "上蓋", "零件", "濾芯", "電池", "吸頭", "集塵", "延長管", "替芯", "補充"]


ALIASES = [("羅技", "logitech"), ("蘋果", "apple"), ("任天堂", "nintendo"), ("三星", "samsung"), ("索尼", "sony"), ("小米", "xiaomi", "mi"),
           ("華碩", "asus"), ("宏碁", "acer"), ("微軟", "microsoft"), ("戴森", "dyson"), ("飛利浦", "philips"), ("松下", "panasonic", "國際牌"),
           ("日立", "hitachi"), ("象印", "zojirushi"), ("虎牌", "tiger"), ("膳魔師", "thermos"), ("聲寶", "sampo"), ("大同", "tatung"),
           ("惠普", "hp"), ("聯想", "lenovo"), ("技嘉", "gigabyte"), ("微星", "msi"), ("雷蛇", "razer"), ("海盜船", "corsair")]
_ALIAS = {w: set(g) for g in ALIASES for w in g}


def _toks(s):
    return [t for t in re.split(r"\s+", s.strip().casefold()) if t]


def _has(tok, title):
    """關鍵字在標題中(品牌中英文都算)。"""
    return any(a in title for a in _ALIAS.get(tok, {tok}))


def relevance(item, kw):
    """0~100:關鍵字命中越多越高;標題出現配件字(而關鍵字沒有)扣分。"""
    title = item["title"].casefold()
    toks = _toks(kw)
    hit = sum(1 for t in toks if _has(t, title)) / max(len(toks), 1)
    acc = [w for w in ACCESSORY_WORDS if w in title and w not in kw]
    score = hit * 80 + (20 if not acc else 0) - 10 * len(acc)
    return max(0, min(100, score)), acc


def analyze(items, kw, must_all=True, hide_acc=True, exclude="", pmin=0, pmax=0, sort="price"):
    """加上相關度 / 配件標記 / 異常低價標記,並篩選排序。回傳 (結果, 被濾掉的筆數)。"""
    ex = [w for w in re.split(r"[\s,，、]+", exclude.casefold()) if w]
    toks = _toks(kw)
    out, dropped = [], 0
    for i in items:
        it = dict(i)
        it["score"], it["acc"] = relevance(it, kw)
        t = it["title"].casefold()
        ok = (not must_all or all(_has(x, t) for x in toks)) and not any(w in t for w in ex) \
            and it["price"] >= (pmin or 0) and (not pmax or it["price"] <= pmax) and not (hide_acc and it["acc"])
        if ok:
            out.append(it)
        else:
            dropped += 1
    if len(out) >= 4:  # 比中位數低很多的通常是配件、單品零件或不同規格
        med = statistics.median(x["price"] for x in out)
        for it in out:
            it["odd"] = it["price"] < med * 0.35
    total = lambda x: x["price"] + (x["ship"] or 0)  # noqa: E731
    keys = {"price": lambda x: (x.get("odd", False), total(x)), "price_desc": lambda x: -total(x),
            "score": lambda x: (-x["score"], total(x)), "sold": lambda x: (-(x["sold"] or 0), total(x)),
            "rating": lambda x: (-((x["rating"] or 0) * min(1, (x["reviews"] or 0) / 20)), total(x))}
    out.sort(key=keys.get(sort, keys["price"]))
    return out, dropped


def refine(items, kw, must_all=True, pmin=0, pmax=0, sort="asc"):
    """(舊介面)篩選:標題需含全部關鍵字、價格區間、排序。"""
    res, _ = analyze(items, kw, must_all, False, "", pmin, pmax, "price_desc" if sort == "desc" else "price")
    return res


def summary(items):
    good = [i for i in items if not i.get("odd")] or items
    if not good:
        return None
    prices = [i["price"] for i in good]
    best = min(good, key=lambda i: i["price"] + (i.get("ship") or 0))
    return {"min": best["price"], "best": best, "avg": statistics.mean(prices), "median": statistics.median(prices),
            "max": max(prices), "n": len(items), "odd": sum(1 for i in items if i.get("odd"))}


# ════════════════════════════════════════════════════════════════════
#  同款比價:用型號 / 規格(含數字的字詞)判斷是不是同一個商品
# ════════════════════════════════════════════════════════════════════
_VARIANT = {"pro", "max", "plus", "mini", "ultra", "lite", "air", "se", "fe", "oled", "slim", "neo", "edge", "fold", "flip"}
_COND = ["福利品", "福利機", "二手", "整新", "展示機", "中古", "九成新", "近新"]
_NOISE = re.compile(r"^(\d{1,2}(入|件|個|組|色|款|天|期|年|月|h|小時)|24h|\d{4}|\d+%|\d+折|\d+元|\d+送\d+)$")


_UNIT = re.compile(r"^\d+(\.\d+)?(g|gb|tb|ml|l|kg|w|mah|吋|寸|cm|mm|hz|人份|公升|入|件|組|片|包|罐|瓶|盒)$")
_CODE = re.compile(r"^(?=.*[a-z])(?=.*\d)[a-z0-9][a-z0-9\-+.]{3,}$")


def model_key(title):
    """商品「身分證」:有型號(如 M720、NL-AAF10)就用型號;沒有就用規格數字(如 16、128G)。

    另外把 Pro/Max/Plus 等版本字、福利品/二手等狀態加進去,避免不同版本被當成同一個商品。"""
    low = title.casefold()
    t = re.sub(r"【[^】]*】", " ", low)  # 【品牌】、【限時】這類括號通常是行銷字
    t = re.sub(r"[^\w+\-.]", " ", t)
    words = [x.strip(".-+") for x in t.split()]
    nums = {x for x in words if re.search(r"\d", x) and len(x) >= 2 and not _NOISE.match(x)}
    codes = {x for x in nums if _CODE.match(x) and not _UNIT.match(x)}
    toks = codes or nums
    if not toks:
        return frozenset()
    toks = set(toks) | {x for x in words if x in _VARIANT}
    toks |= {"(" + c + ")" for c in _COND if c in title}  # 福利品/二手 跟全新品分開
    return frozenset(toks)


def same_product_groups(items, min_platforms=2, limit=8):
    """回傳 [{key, items(各平台最低一筆), best, worst, save}],依「平台數多、價差大」排序。"""
    groups = {}
    for it in items:
        if it.get("odd") or it.get("acc"):
            continue
        k = model_key(it["title"])
        if k:
            groups.setdefault(k, []).append(it)
    out = []
    for k, its in groups.items():
        per = {}
        for it in its:
            if it["platform"] not in per or it["price"] < per[it["platform"]]["price"]:
                per[it["platform"]] = it
        if len(per) < min_platforms:
            continue
        lst = sorted(per.values(), key=lambda x: x["price"] + (x["ship"] or 0))
        out.append({"key": " ".join(sorted(k)).upper(), "items": lst, "best": lst[0], "save": (lst[-1]["price"] - lst[0]["price"]),
                    "title": min((x["title"] for x in lst), key=len)})
    out.sort(key=lambda g: (-len(g["items"]), -g["save"]))
    return out[:limit]


def search_links(kw):
    q = urllib.parse.quote(kw)
    return {"PChome": f"https://24h.pchome.com.tw/search/?q={q}", "momo": f"https://www.momoshop.com.tw/search/searchShop.jsp?keyword={q}",
            "蝦皮": f"https://shopee.tw/search?keyword={q}&sortBy=price&order=asc", "蝦皮商城": f"https://shopee.tw/mall/search?keyword={q}",
            "Yahoo購物": f"https://tw.buy.yahoo.com/search/product?p={q}", "露天": f"https://www.ruten.com.tw/find/?q={q}"}
