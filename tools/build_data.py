"""
Сборка данных каталога для сайта.

Источники (все — Excel-выгрузки магазина):
  --catalog  Catalog_<версия>_<ддммгг>.xlsx            — характеристики, структура каталога
  --site     tekushie_ceni_i_tavari_s_sayta.xlsx        — адреса страниц, фото, описания, цены по размерам
  --promo    import_sale_<гггг.мм.дд>.xlsx              — скидки (правила корзины Битрикс)
  --photos   папка с фото товаров (<хеш>_min.jpg или <id>.jpg)

Результат: data/catalog.json, data/catalog.js и img/products/<id>.jpg

  python tools/build_data.py --catalog Catalog_60_250826.xlsx --site tekushie.xlsx \
      --promo import_sale_2026.10.18.xlsx --photos photos/
"""
import argparse, json, os, re, shutil
from datetime import datetime
import openpyxl

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser()
ap.add_argument("--catalog", required=True)
ap.add_argument("--site", required=True)
ap.add_argument("--promo")
ap.add_argument("--photos", nargs="*", default=[])
ap.add_argument("--price", choices=["site", "list"], default="list",
                help="list — цены из каталога Catalog_XX (по умолчанию), site — цены текущего сайта («Цена базовая»)")
args = ap.parse_args()

TR = dict(zip("абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
              ["a","b","v","g","d","e","e","zh","z","i","y","k","l","m","n","o","p","r","s","t","u","f","h","ts","ch","sh","sch","","y","","e","yu","ya"]))
def slug(s): return re.sub(r"[^a-z0-9]+", "-", "".join(TR.get(c, c) for c in str(s).lower())).strip("-")
def txt(v):
    if v is None: return ""
    if isinstance(v, float) and v.is_integer(): v = int(v)
    return str(v).strip()
ALIAS = {"AQUA": "АКВА", "HYGIENIC BABY": "ДЕТСКИЙ ГИГИЕНИЧЕСКИЙ", "AQUA BABY": "ДЕТСКИЙ АКВА", "ХБ ЛЮКС": "ХБЛЮКС"}
def key(s):
    s = str(s or "").upper().replace("Ё", "Е")
    s = re.sub(r"^(РАСПРОДАЖА\s+)?(ТОНКИЙ\s+МАТРАС|ДЕТСКИЙ\s+МАТРАС|МАТРАС|НАМАТРАСНИК)\s+", "", s.strip())
    s = re.sub(r"\s*H-\d+\s*$", "", s)
    s = ALIAS.get(s, s)
    s = re.sub(r"\(.*?\)", "", s)
    return re.sub(r"[^0-9A-ZА-Я]", "", s)
def size(s):
    m = re.findall(r"\d+", str(s)); return (int(m[0]), int(m[1])) if len(m) >= 2 else None

CATS = [  # id, название, лист цен, лист характеристик, URL раздела, слово для полного названия
    ("matrasy", "Матрасы", "Матрасы", "Х_Матрасы", "matrasy/", "Матрас"),
    ("toppery", "Топперы", "Топперы", "Х_Топперы", "matrasy/toppery/", "Тонкий матрас"),
    ("namatrasniki", "Наматрасники", "Наматрасники", "Х_Наматрасники", "namatrasniki/", "Наматрасник"),
    ("detskie-matrasy", "Детские матрасы", "Матрасы_Детские", "Х_Матрасы_Детские", "matrasy/detskie/", "Детский матрас"),
    ("detskie-namatrasniki", "Детские наматрасники", "Наматрасники_Детские", "Х_Наматрасники_Детские", "namatrasniki/detskie/", "Наматрасник"),
]

# ---------- 1. Каталог: структура, характеристики, розничный прайс ----------
wb = openpyxl.load_workbook(args.catalog, data_only=True)
products, cats = [], []
for cid, cname, psheet, hsheet, curl, word in CATS:
    cats.append({"id": cid, "name": cname, "url": curl})
    ws = wb[psheet]; started = False; cur = None; prices = {}; order = []
    for r in ws.iter_rows(values_only=True):
        if r[0] == "Название": started = True; continue
        if not started: continue
        if r[0] is not None and r[1] is None and r[3] is None: continue
        if r[0] is not None: cur = txt(r[0])
        if cur and r[1] is not None and r[3] is not None:
            if cur not in prices: prices[cur] = []; order.append(cur)
            for L in [x.strip() for x in str(r[2]).split(",") if x.strip()]:
                prices[cur].append({"w": int(r[1]), "l": int(float(L)), "list": int(r[3])})
    rows = list(wb[hsheet].iter_rows(values_only=True)); H = [txt(x) for x in rows[3]]
    chars = {}
    for r in rows[4:]:
        if not r[0]: break
        chars[key(r[0])] = {H[i]: txt(r[i]) for i in range(1, len(H)) if H[i]}
    for name in order:
        products.append({"id": slug(name), "name": name.title() if name.isupper() else name, "category": cid, "word": word,
                         "variants": sorted(prices[name], key=lambda v: (v["w"], v["l"])),
                         "specs": chars.get(key(name), {})})

by_key = {}
for p in products: by_key.setdefault(key(p["name"]), []).append(p)

# ---------- 2. Выгрузка сайта: адреса, фото, описания, цены по размерам ----------
ws_site = openpyxl.load_workbook(args.site, read_only=True, data_only=True)
def rows(sheet):
    it = ws_site[sheet].iter_rows(values_only=True); hdr = [str(h or "") for h in next(it)]
    for r in it:
        if r and r[0]: yield dict(zip(hdr, r))
def clean(d):
    d = str(d or "").strip(); return "" if d.startswith("—") else d
site_prices = {}
for sh in ("Матрасы - цены по размерам", "Наматрасники-цены по разм.(12)"):
    for r in rows(sh):
        sz = size(r["Размер"])
        if sz and r.get("Цена базовая (руб)"):
            site_prices.setdefault(key(r["Название"]), {})[sz] = int(float(r["Цена базовая (руб)"]))
unmatched_site = []
for sh in ("Матрасы (78)", "Наматрасники (12)"):
    for r in rows(sh):
        ps = by_key.get(key(r["Название"]))
        if not ps: unmatched_site.append(r["Название"]); continue
        for p in ps:
            url = (r.get("URL (базовый)") or "").strip()
            path = re.sub(r"^https?://[^/]+/", "", url).strip("/")
            if path: p["id"] = path.split("/")[-1]; p["path"] = path + "/"
            p["photo_hash"] = os.path.splitext((r.get("Основное фото") or "").split("/")[-1])[0]
            sp = site_prices.get(key(r["Название"]), {})
            if sp and args.price == "site":
                listed = {(v["w"], v["l"]): v["list"] for v in p["variants"]}
                p["variants"] = [{"w": w, "l": l, "site": pr, "list": listed.get((w, l))} for (w, l), pr in sorted(sp.items())]

for p in products:
    p.setdefault("path", f'{dict((c[0], c[4]) for c in CATS)[p["category"]]}{p["id"]}/')
    for v in p["variants"]:
        v["price"] = v.get("site") if args.price == "site" and v.get("site") else (v.get("list") or v.get("site"))
        v.pop("site", None); v.pop("list", None)
    p["variants"] = [v for v in p["variants"] if v["price"]]
    p["min_price"] = min(v["price"] for v in p["variants"])

# ---------- 3. Распродажа: штучные позиции ----------
cats.append({"id": "sale", "name": "Распродажа", "url": "sale/"})
for r in rows("Распродажа (8)"):
    w, l = size(r["Размер (фиксированный)"])
    base = (by_key.get(key(r["Название"])) or [None])[0]
    url = (r.get("URL (базовый)") or "").strip(); path = re.sub(r"^https?://[^/]+/", "", url).strip("/") + "/"
    pid = path.strip("/").split("/")[-1]
    if any(p["id"] == pid for p in products): continue
    price = int(float(r["Цена сейчас (руб)"]))
    nm = re.sub(r"^(Распродажа\s+)?(Тонкий матрас|Матрас)\s+", "", str(r["Название"])).strip()
    nm = re.sub(r"\s*h-\d+$", "", nm, flags=re.I).title()
    regular = base and next((v["price"] for v in base["variants"] if (v["w"], v["l"]) == (w, l)), None)
    products.append({"id": pid, "path": path, "name": nm, "category": "sale",
                     "word": base["word"] if base else "Матрас", "variants": [{"w": w, "l": l, "price": price}],
                     "min_price": price, "regular_price": regular if regular and regular > price else None,
                     "photo_hash": os.path.splitext((r.get("Основное фото") or "").split("/")[-1])[0],
                     "specs": dict(base["specs"]) if base else {}, "base_id": base["id"] if base else None})

# ---------- 4. Скидки из выгрузки правил корзины ----------
promo_unmatched = []
if args.promo:
    by_slug = {p["id"]: p for p in products}
    wsp = openpyxl.load_workbook(args.promo, read_only=True, data_only=True).worksheets[0]
    it = wsp.iter_rows(values_only=True); hdr = [str(h or "") for h in next(it)]
    for r in it:
        d = dict(zip(hdr, r))
        code = str(d.get("Внешний код правила корзины") or "").strip()
        if not code or not str(d.get("ID Элемента") or "").isdigit(): continue  # служебные строки (формулы)
        if str(d.get("Активность")).upper() != "Y": continue
        p = by_slug.get(code) or next((x for x in products if x["id"].endswith(code)), None)
        if not p: promo_unmatched.append(d["Название"]); continue
        def dt(v): return datetime.strptime(str(v)[:10], "%Y-%m-%d").date().isoformat()
        p["promo"] = {"pct": int(float(d["Процент скидки"])), "from": dt(d["Дата начала активности"]), "to": dt(d["Дата окончания активности"])}

# ---------- 5. Фото ----------
img_dir = os.path.join(ROOT, "img", "products"); os.makedirs(img_dir, exist_ok=True)
pool = {}
for d in args.photos:
    for f in os.listdir(d):
        if f.lower().endswith(".jpg"): pool[re.sub(r"_min$", "", os.path.splitext(f)[0])] = os.path.join(d, f)
EXTRA = {"matras-gertsog": "gtngknm3vi"}  # фото найдено по карточке на странице каталога сайта
for p in products:
    src = pool.get(p["id"]) or pool.get(p.get("photo_hash", "")) or pool.get(slug(p["name"])) or \
          next((v for k, v in pool.items() if EXTRA.get(p["id"]) and k.startswith(EXTRA[p["id"]])), None) or \
          (p.get("base_id") and (pool.get(p["base_id"]) or os.path.exists(os.path.join(img_dir, p["base_id"] + ".jpg")) and os.path.join(img_dir, p["base_id"] + ".jpg"))) or None
    dst = os.path.join(img_dir, p["id"] + ".jpg")
    if src and os.path.abspath(src) != os.path.abspath(dst):
        try:
            from PIL import Image
            im = Image.open(src).convert("RGB"); im.thumbnail((1200, 1200)); im.save(dst, quality=80, optimize=True, progressive=True)
        except ImportError:
            shutil.copy(src, dst)
    p["image"] = f"img/products/{p['id']}.jpg" if os.path.exists(dst) else ""
    p.pop("photo_hash", None)

out = {"built": datetime.now().strftime("%Y-%m-%d"), "price_source": args.price, "categories": cats, "products": products}
os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, "data", "catalog.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
open(os.path.join(ROOT, "data", "catalog.js"), "w", encoding="utf-8").write("window.CATALOG=" + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n")

ids = [p["id"] for p in products]; assert len(ids) == len(set(ids)), "повтор id"
print("товаров:", len(products), "| с фото:", sum(1 for p in products if p["image"]),
      "| со скидкой:", sum(1 for p in products if p.get("promo")))
print("без адреса на старом сайте:", [p["name"] for p in products if "/" not in p["path"].strip("/")])
print("строки сайта без пары в каталоге:", unmatched_site)
print("скидки без товара:", promo_unmatched)
