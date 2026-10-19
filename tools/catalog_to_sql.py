"""
Этап 2: превращает data/catalog.json в SQL для загрузки в базу (db/schema.sql).
    python tools/catalog_to_sql.py > db/catalog_data.sql
    psql -d tmvo -f db/schema.sql && psql -d tmvo -f db/catalog_data.sql
"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = json.load(open(os.path.join(ROOT, "data", "catalog.json"), encoding="utf-8"))
q = lambda v: "NULL" if v is None or v == "" else "'" + str(v).replace("'", "''") + "'"
def num(v):
    try: return str(float(str(v).replace(",", ".")))
    except ValueError: return "NULL"
out = ["BEGIN;", "TRUNCATE product_images, product_variants, promotions, products, categories CASCADE;"]
for i, c in enumerate(C["categories"]):
    out.append(f"INSERT INTO categories (id, name, url, sort) VALUES ({q(c['id'])}, {q(c['name'])}, {q(c['url'])}, {i});")
for p in sorted(C["products"], key=lambda p: p.get("base_id") is not None):
    s = p["specs"]
    out.append("INSERT INTO products (id, category_id, name, word, path, hardness_top, hardness_bottom, is_two_sided, has_springs, height_cm, specs, base_product_id, regular_price) VALUES (" + ", ".join([
        q(p["id"]), q(p["category"]), q(p["name"]), q(p.get("word", "")), q(p["path"]), q(s.get("Жесткость верх")), q(s.get("Жесткость низ")),
        "true" if s.get("Категория: Двухсторонний") == "Да" else "false", "true" if s.get("Категория: Пружины") == "С пружинами" else "false",
        num(s.get("Высота матраса")) if s.get("Высота матраса") else "NULL", q(json.dumps(s, ensure_ascii=False)) + "::jsonb",
        q(p.get("base_id")), str(p["regular_price"]) if p.get("regular_price") else "NULL"]) + ");")
    for v in p["variants"]:
        out.append(f"INSERT INTO product_variants (product_id, width_cm, length_cm, price, in_stock) VALUES ({q(p['id'])}, {v['w']}, {v['l']}, {v['price']}, {'1' if p['category'] == 'sale' else 'NULL'});")
    if p.get("image"):
        out.append(f"INSERT INTO product_images (product_id, file, is_main) VALUES ({q(p['id'])}, {q(p['image'])}, true);")
    if p.get("promo"):
        pr = p["promo"]; out.append(f"INSERT INTO promotions (product_id, percent, starts_on, ends_on) VALUES ({q(p['id'])}, {pr['pct']}, {q(pr['from'])}, {q(pr['to'])});")
out.append("COMMIT;")
print("\n".join(out))
