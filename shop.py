# -*- coding: utf-8 -*-
"""🛒 比價模組:PChome 24h / momo / 蝦皮。各平台獨立,任一平台失敗不影響其他平台。"""
import re
import statistics
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

from core import UA, make_session

_S = make_session(retries=1)
_H = {"User-Agent": UA, "Accept": "application/json, text/plain, */*", "Accept-Language": "zh-TW,zh;q=0.9"}
PLATFORMS = ["PChome 24h", "momo 購物網", "蝦皮購物"]


def _get(url, **kw):
    return _S.get(url, timeout=(5, 12), **kw)


def _post(url, **kw):
    return _S.post(url, timeout=(5, 12), **kw)


def to_price(v):
    """'1,290(原價…)' / '$1290' / 1290 → 1290.0;無法解析回傳 None。"""
    m = re.search(r"\d[\d,]*(?:\.\d+)?", str(v if v is not None else "").split("(")[0])
    return float(m.group().replace(",", "")) if m else None


def search_pchome(kw, limit=40):
    last = None
    for url in ("https://ecshweb.pchome.com.tw/search/v4.3/all/results", "https://ecshweb.pchome.com.tw/search/v3.3/all/results"):
        try:  # 新舊兩版欄位大小寫不同,都支援
            r = _get(url, params={"q": kw, "page": 1, "sort": "rnk/dc"}, headers=_H)
            r.raise_for_status()
            j = r.json()
            out = []
            for p in (j.get("Prods") or j.get("prods") or [])[:limit]:
                name, pid = p.get("Name") or p.get("name"), p.get("Id") or p.get("id")
                price = to_price(p.get("Price") if p.get("Price") is not None else p.get("price"))
                if name and pid and price:
                    pic = p.get("PicS") or p.get("picS") or p.get("PicB") or p.get("picB") or ""
                    img = ("https://img.pchome.com.tw/cs" + pic) if pic.startswith("/") else pic
                    out.append(dict(platform="PChome 24h", title=name, price=price, url=f"https://24h.pchome.com.tw/prod/{pid}",
                                    credit="✅ 官方直營", sold=None, img=img))
            if out:
                return out
        except Exception as e:  # noqa: BLE001
            last = e
    if last:
        raise last
    return []


def search_momo(kw, limit=40):
    payload = {"host": "momoshop", "flag": "searchEngine",
               "data": {"searchValue": kw, "curPage": "1", "priceS": "0", "priceE": "9999999", "searchType": "1"}}
    r = _post("https://apisearch.momoshop.com.tw/momoSearchCloud/moec/textSearch", json=payload,
              headers={**_H, "Content-Type": "application/json", "Origin": "https://www.momoshop.com.tw",
                       "Referer": "https://www.momoshop.com.tw/"})
    r.raise_for_status()
    out = []
    for g in (((r.json() or {}).get("rtnSearchData") or {}).get("goodsInfoList") or [])[:limit]:
        name, code, price = g.get("goodsName"), g.get("goodsCode"), to_price(g.get("goodsPrice"))
        if name and code and price:
            img = g.get("imgUrl") or g.get("goodsImgUrl") or ""
            out.append(dict(platform="momo 購物網", title=name, price=price, img=img if img.startswith("http") else "",
                            url=f"https://www.momoshop.com.tw/goods/GoodsDetail.jsp?i_code={code}", credit="✅ momo 平台", sold=None))
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
            out.append(dict(platform="蝦皮購物", title=b["name"], price=price, credit=credit, sold=sold,
                            img=f"https://down-tw.img.susercontent.com/file/{b['image']}" if b.get("image") else "",
                            url=f"https://shopee.tw/product/{b.get('shopid')}/{b['itemid']}"))
        if len(out) >= limit:
            break
    return out


def compare(kw, platforms=tuple(PLATFORMS), good_only=True):
    """回傳 (所有商品, {平台: (筆數, 錯誤訊息或None)})。各平台同時查詢。"""
    fns = {"PChome 24h": search_pchome, "momo 購物網": search_momo, "蝦皮購物": lambda k: search_shopee(k, good_only=good_only)}

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


def refine(items, kw, must_all=True, pmin=0, pmax=0, sort="asc"):
    """篩選:標題需含全部關鍵字(濾掉不相關配件)、價格區間、排序。"""
    toks = [t for t in re.split(r"\s+", kw.strip().casefold()) if t]
    out = [i for i in items if (not must_all or all(t in i["title"].casefold() for t in toks))
           and i["price"] >= (pmin or 0) and (not pmax or i["price"] <= pmax)]
    return sorted(out, key=lambda x: x["price"], reverse=(sort == "desc"))


def summary(items):
    if not items:
        return None
    prices = [i["price"] for i in items]
    best = min(items, key=lambda i: i["price"])
    return {"min": best["price"], "best": best, "avg": statistics.mean(prices), "median": statistics.median(prices), "n": len(items)}


def search_links(kw):
    q = urllib.parse.quote(kw)
    return {"PChome": f"https://24h.pchome.com.tw/search/?q={q}", "momo": f"https://www.momoshop.com.tw/search/searchShop.jsp?keyword={q}",
            "蝦皮": f"https://shopee.tw/search?keyword={q}&sortBy=price&order=asc", "蝦皮商城": f"https://shopee.tw/mall/search?keyword={q}",
            "Yahoo購物": f"https://tw.buy.yahoo.com/search/product?p={q}", "露天": f"https://www.ruten.com.tw/find/?q={q}"}
