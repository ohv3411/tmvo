"""
Генератор статического сайта «Торбеевские матрасы» (версия 3).
Берёт data/catalog.json (см. tools/build_data.py) и создаёт все HTML-страницы в корне проекта.

    python tools/build_site.py

Ссылки относительные и с явным index.html — сайт работает на GitHub Pages (в т.ч. в подпапке репозитория)
и при открытии файлов с диска. Для рабочего сервера с «чистыми» адресами поставьте CLEAN_URLS = True.
"""
import html, json, math, os, re
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT = json.load(open(os.path.join(ROOT, "data", "catalog.json"), encoding="utf-8"))
CLEAN_URLS = False
NOINDEX = True           # демо: не индексировать поисковиками
SITE_URL = "https://tmvo.ru/"
TODAY = date.today().isoformat()

SHOP = dict(name="Торбеевские матрасы", phone="8 (495) 150-30-90", phone_href="+74951503090",
            mphone="+7 (985) 800-00-29", mphone_href="+79858000029", tg="https://t.me/+79858000029",
            email="info@tmvo.ru", hours="Ежедневно с 10:00 до 20:00",
            address="Московская обл., Люберецкий р-н, пос. Торбеево, д. 48", address_short="пос. Торбеево, д. 48",
            seller="ИП Геворгян Р. А.", inn="342102450670", ogrnip="323508100652805", okpo="2027978788",
            bank="ПАО Сбербанк", bik="044525225", rs="40802810140000186299", ks="30101810400000000225")
MAP_Q = "Московская область, Люберецкий район, посёлок Торбеево, 48"

e = lambda s: html.escape(str(s if s is not None else ""), quote=True)
def rub(n): return f"{int(round(n)):,}".replace(",", " ") + " ₽"
P = CAT["products"]; BY = {p["id"]: p for p in P}
CATS = CAT["categories"]
def full(p): return (p.get("word") + " " if p.get("word") and p["category"] != "detskie-namatrasniki" else "") + p["name"]
def plural(n, a, b, c):
    m10, m100 = n % 10, n % 100
    return a if m10 == 1 and m100 != 11 else b if 2 <= m10 <= 4 and not 10 <= m100 < 20 else c
def promo_on(p, day=TODAY): pr = p.get("promo"); return bool(pr and pr["from"] <= day < pr["to"])
def promo_price(p, base):
    if not promo_on(p): return base, None
    return int(math.ceil(base * (1 - p["promo"]["pct"] / 100) / 10) * 10), base
HAS_PROMO = any(p.get("promo") for p in P)
def sides(p): return [x.strip() for x in (p["specs"].get("Категория: Жёсткость") or "").split(";") if x.strip()]
SHORT = {"Мягкий": "Мягкий", "Средней жесткости": "Средний", "Жесткий": "Жёсткий"}
def hard_label(p): return " / ".join(SHORT.get(s, s) for s in sides(p))
def count_label(n): return f"{n} {plural(n, 'модель', 'модели', 'моделей')}"

# ---------------------------------------------------------------- макет
class Page:
    def __init__(self, path):
        self.path = path.strip("/") + "/" if path.strip("/") else ""
        self.depth = self.path.count("/")
        self.root = "../" * self.depth
    def u(self, target):
        q = ""
        if "?" in target: target, q = target.split("?", 1); q = "?" + q
        target = target.strip("/") + "/" if target.strip("/") else ""
        return self.root + target + ("" if CLEAN_URLS else "index.html") + q
    def a(self, rel): return self.root + rel

ICON = {
    "search": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>',
    "cart": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 4h2l2.2 11h11l2-8H6.2"/><circle cx="9" cy="19.5" r="1.5"/><circle cx="17" cy="19.5" r="1.5"/></svg>',
    "heart": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20s-7-4.4-9.2-9A5 5 0 0112 5.6 5 5 0 0121.2 11C19 15.6 12 20 12 20z"/></svg>',
    "menu": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 7h16M4 12h16M4 17h16"/></svg>',
    "grid": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="4" width="6" height="6" rx="1"/><rect x="14" y="4" width="6" height="6" rx="1"/><rect x="4" y="14" width="6" height="6" rx="1"/><rect x="14" y="14" width="6" height="6" rx="1"/></svg>',
    "truck": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h11v10H3zM14 10h4l3 3v3h-7"/><circle cx="7" cy="18" r="1.8"/><circle cx="17" cy="18" r="1.8"/></svg>',
    "wallet": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="6" width="18" height="13" rx="2"/><path d="M16 12.5h2M3 9h18"/></svg>',
    "shield": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3l8 3v6c0 4.5-3.4 8-8 9-4.6-1-8-4.5-8-9V6z"/><path d="M8.5 12l2.5 2.5 4.5-5"/></svg>',
    "factory": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 20V10l5 3V10l5 3V6h4v14z"/><path d="M3 20h18"/></svg>',
    "ruler": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="8" width="20" height="8" rx="1.5"/><path d="M6 8v3M10 8v4M14 8v3M18 8v4"/></svg>',
    "scale": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 4v16M5 8h14M5 8l-3 7h6zM19 8l-3 7h6z"/></svg>',
    "pin": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 21s-7-6.2-7-11.5A7 7 0 0119 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/></svg>',
    "tg": '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M21.4 4.3L2.9 11.4c-1.2.5-1.2 1.2-.2 1.5l4.7 1.5 1.8 5.6c.2.6.1.9.8.9.5 0 .7-.2 1-.5l2.3-2.2 4.8 3.5c.9.5 1.5.2 1.7-.8l3.1-14.7c.3-1.3-.5-1.9-1.5-1.4zM8.6 14.1l9.6-6.1c.5-.3.9-.1.5.2l-8.2 7.4-.3 3.4z"/></svg>',
    "max": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M4 18V6l8 8 8-8v12"/></svg>',
    "up": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M6 14l6-6 6 6"/></svg>',
}

def cat_links(pg, cls=""):
    return "".join(f'<a href="{pg.u(c["url"])}" class="{cls}">{e(c["name"])}<span>{sum(1 for p in P if p["category"] == c["id"])}</span></a>' for c in CATS)
INFO = [("Распродажа", "sale/"), ("Доставка и оплата", "dostavka-i-oplata/"), ("Гарантия", "garantiya/"), ("Отзывы", "otzyvy/"), ("Контакты", "kontakty/")]
def messengers(pg):
    return f'''<span class="msg"><a href="{SHOP["tg"]}" target="_blank" rel="noopener" aria-label="Telegram">{ICON["tg"]}</a><a href="tel:{SHOP["mphone_href"]}" aria-label="MAX">{ICON["max"]}</a></span>'''

def layout(pg, *, title, desc, body, page_type="info", pid="", crumbs=None, lead=True):
    links = lambda items: "".join(f'<a href="{pg.u(h)}">{e(t)}</a>' for t, h in items)
    crumbs_html = ""
    if crumbs:
        parts = [f'<a href="{pg.u("")}">Главная</a>'] + [f'<a href="{pg.u(h)}">{e(t)}</a>' if h else f'<span aria-current="page">{e(t)}</span>' for t, h in crumbs]
        crumbs_html = f'<nav class="crumbs wrap" aria-label="Навигация">{" / ".join(parts)}</nav>'
    mm = "".join(
        f'''<a class="mm-item" href="{pg.u(c["url"])}">{(lambda pp: f'<img src="{pg.a(pp["image"])}" alt="" loading="lazy">' if pp else '<span class="mm-noimg"></span>')(next((x for x in P if x["category"] == c["id"] and x.get("image")), None))}
        <span><b>{e(c["name"])}</b><small>{count_label(sum(1 for p in P if p["category"] == c["id"]))}</small></span></a>''' for c in CATS)
    lead_html = f'''<section class="lead-sec"><div class="wrap lead-in"><div><h2>Остались вопросы — мы поможем</h2><p>Оставьте телефон, и мы перезвоним: подскажем модель, размер и сроки изготовления.</p></div>
      <form class="lead-form" novalidate><label class="sr" for="lp-{pg.depth}">Телефон</label><input class="inp" id="lp-{pg.depth}" name="phone" type="tel" inputmode="tel" autocomplete="tel" placeholder="+7 (___) ___-__-__">
      <button class="btn" disabled>Проконсультироваться</button>
      <label class="cbx"><input type="checkbox" name="privacy"> <span>Соглашаюсь с <a href="{pg.u("politika-konfidentsialnosti/")}">политикой конфиденциальности</a></span></label>
      <label class="cbx"><input type="checkbox" name="personal_data"> <span>Даю <a href="{pg.u("soglasie-na-obrabotku/")}">согласие на обработку персональных данных</a></span></label>
      <input class="hp" type="text" name="website" tabindex="-1" autocomplete="off" aria-hidden="true"></form></div></section>''' if lead else ""
    return f'''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
{'<meta name="robots" content="noindex, nofollow">' if NOINDEX else ''}
<link rel="icon" href="{pg.a("img/logo.svg")}" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Onest:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{pg.a("assets/css/style.css")}">
</head>
<body data-page="{page_type}"{f' data-pid="{e(pid)}"' if pid else ""}>
<a class="skip" href="#main">К содержимому</a>
<div class="topbar"><div class="wrap topbar-in">
  <a href="{pg.u("kontakty/")}">{ICON["pin"]} {e(SHOP["address_short"])}</a><span class="tb-hours">{e(SHOP["hours"])}</span>
  <span class="tb-msg">{e(SHOP["mphone"])} — Telegram, MAX {messengers(pg)}</span>
</div></div>
<header class="hdr"><div class="wrap hdr-in">
  <button class="icon-btn burger" id="burger" aria-label="Открыть меню">{ICON["menu"]}</button>
  <a class="logo" href="{pg.u("")}" aria-label="{e(SHOP["name"])} — на главную"><img src="{pg.a("img/logo.svg")}" alt="{e(SHOP["name"])}" width="132" height="46"></a>
  <button class="btn catbtn" id="catbtn" aria-expanded="false" aria-controls="megamenu">{ICON["grid"]} Каталог</button>
  <nav class="nav" aria-label="Разделы">{"".join(f'<a href="{pg.u(h)}"{" class=" + chr(34) + "nav-sale" + chr(34) if h == "sale/" else ""}>{t}</a>' for t, h in INFO)}</nav>
  <span class="spacer"></span>
  <a class="icon-btn search-btn" href="{pg.u("poisk/")}" aria-label="Поиск">{ICON["search"]}</a>
  <div class="hdr-tel"><a href="tel:{SHOP["phone_href"]}">{e(SHOP["phone"])}</a><small><button class="link" data-callback>Заказать звонок</button></small></div>
  <a class="icon-btn" href="{pg.u("izbrannoe/")}" aria-label="Избранное">{ICON["heart"]}<span class="badge fav-count" hidden></span></a>
  <a class="icon-btn" href="{pg.u("korzina/")}" aria-label="Корзина">{ICON["cart"]}<span class="badge cart-count" hidden></span></a>
</div>
<div class="megamenu" id="megamenu" hidden><div class="wrap"><div class="mm-grid">{mm}</div>
  <form class="search mm-search" action="{pg.u("poisk/")}" role="search">{ICON["search"]}<input name="q" type="search" placeholder="Поиск по каталогу" aria-label="Поиск по каталогу"></form></div></div></header>
<div class="drawer" id="drawer"><div class="shade" data-drawer-close></div><nav class="panel" aria-label="Меню">
  <img src="{pg.a("img/logo.svg")}" alt="" class="dlogo">
  <form class="search" action="{pg.u("poisk/")}" role="search">{ICON["search"]}<input name="q" type="search" placeholder="Поиск по каталогу" aria-label="Поиск"></form>
  <h4>Каталог</h4>{cat_links(pg)}<h4>Покупателям</h4>{links(INFO)}
  <div class="dfoot"><a href="tel:{SHOP["phone_href"]}" class="dtel">{e(SHOP["phone"])}</a><span class="muted">{e(SHOP["hours"])}</span><span class="muted">{e(SHOP["mphone"])} — Telegram, MAX</span></div>
</nav></div>
{crumbs_html}
<main id="main" tabindex="-1">
{body}
</main>
{lead_html}
<footer class="ftr"><div class="wrap"><div class="ftr-grid">
  <div><img src="{pg.a("img/logo.svg")}" alt="{e(SHOP["name"])}" class="flogo"><p>Фабрика матрасов в Подмосковье: матрасы, топперы и наматрасники для взрослых и детей.</p></div>
  <div><h4>Каталог</h4>{"".join(f'<a href="{pg.u(c["url"])}">{e(c["name"])}</a>' for c in CATS)}</div>
  <div><h4>Покупателям</h4>{links(INFO[:4])}</div>
  <div><h4>Контакты</h4><a class="tel" href="tel:{SHOP["phone_href"]}">{e(SHOP["phone"])}</a><span>Бесплатный звонок по РФ</span>
    <a href="tel:{SHOP["mphone_href"]}">{e(SHOP["mphone"])}</a><span>Telegram, MAX</span><div class="fmsg">{messengers(pg)}</div>
    <a href="mailto:{SHOP["email"]}">{e(SHOP["email"])}</a><p class="faddr">{e(SHOP["address"])}<br>{e(SHOP["hours"])}</p><a href="{pg.u("kontakty/")}">Все контакты и реквизиты</a></div>
</div>
<div class="legal"><span>© {date.today().year} {e(SHOP["name"])}. {e(SHOP["seller"])}, ИНН {SHOP["inn"]}, ОГРНИП {SHOP["ogrnip"]}.</span>
  <span><a href="{pg.u("politika-konfidentsialnosti/")}">Политика конфиденциальности</a> · <a href="{pg.u("soglasie-na-obrabotku/")}">Согласие на обработку данных</a> · <a href="{pg.u("oferta/")}">Публичная оферта</a></span></div>
</div></footer>
<button class="totop" id="totop" aria-label="Наверх" hidden>{ICON["up"]}</button>
<div class="modal" id="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title"><div class="shade" data-close></div><div class="dlg" id="dlg"></div></div>
<div class="toast" id="toast" role="status" aria-live="polite"></div>
<script>window.TMVO_ROOT = "{pg.root}";</script>
<script src="{pg.a("assets/js/config.js")}"></script>
<script src="{pg.a("data/catalog.js")}"></script>
<script src="{pg.a("assets/js/api.js")}"></script>
<script src="{pg.a("assets/js/site.js")}"></script>
</body>
</html>
'''

PAGES = []
def write(pg, content):
    out = os.path.join(ROOT, pg.path, "index.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(content); PAGES.append(pg.path)

# ---------------------------------------------------------------- блоки
def price_html(p):
    price, old = promo_price(p, p["min_price"]); old = old or p.get("regular_price")
    return f'{"" if len(p["variants"]) == 1 else "<small>от</small> "}<b>{rub(price)}</b>{f" <s>{rub(old)}</s>" if old else ""}'
def card(pg, p):
    img = f'<img src="{pg.a(p["image"])}" alt="{e(full(p))}" loading="lazy">' if p.get("image") else f'<span class="noimg">{e(p["name"])}</span>'
    tags = ('<span class="sale-tag">Распродажа</span>' if p["category"] == "sale" else "") + (f'<span class="promo-tag">−{p["promo"]["pct"]}%</span>' if promo_on(p) else "")
    chips = (f'<span class="chip">{e(hard_label(p))}</span>' if hard_label(p) else "") + (f'<span class="chip">{e(p["specs"]["Высота матраса"])} см</span>' if p["specs"].get("Высота матраса") else "")
    size = f'<div class="muted small">Размер {p["variants"][0]["w"]}×{p["variants"][0]["l"]} см</div>' if len(p["variants"]) == 1 else ""
    return f'''<article class="card" data-card="{p["id"]}"><a class="pic" href="{pg.u(p["path"])}">{tags}{img}</a>
      <button class="fav-btn" data-fav="{p["id"]}" aria-label="В избранное">{ICON["heart"]}</button>
      <div class="body"><a class="name" href="{pg.u(p["path"])}">{e(full(p))}</a><div class="chips">{chips}</div>
      <div class="price">{price_html(p)}</div>{size}
      <button type="button" class="btn ghost sm quick-btn" data-quick="{p["id"]}">Быстрый заказ</button></div></article>'''
def grid(pg, items): return '<div class="grid">' + "".join(card(pg, p) for p in items) + "</div>"
def sec(title, inner, sub="", link=None, cls=""):
    return f'''<section class="sec {cls}"><div class="wrap"><div class="sec-h"><div><h2>{title}</h2>{f'<p class="muted">{sub}</p>' if sub else ""}</div>{f'<a class="link" href="{link[1]}">{link[0]}</a>' if link else ""}</div>{inner}</div></section>'''
def aside_help(pg):
    return f'''<aside class="help-box"><h3>Нужна помощь с выбором?</h3><p>Позвоните или напишите — подскажем модель, размер и сроки.</p>
      <a class="tel" href="tel:{SHOP["phone_href"]}">{e(SHOP["phone"])}</a><p class="muted small">{e(SHOP["mphone"])} — Telegram, MAX<br>{e(SHOP["hours"])}</p>
      <button class="btn block" data-callback>Заказать звонок</button></aside>'''

REVIEWS = [
    ("Анна В.", "26.06.2026", "Только плюсы, порядка 10 лет покупаю у них, а ещё и дети стали покупать там же."),
    ("Ирина Александровна", "26.02.2026", "Заказывали матрас. Качество на уровне. Персонал компетентный, вежливый. Срок выполнения заказа выдерживается. Доставка в удобный заранее оговоренный день и час. Рекомендую!"),
    ("Екатерина", "18.07.2022", "Пользуемся 4 года, всё отлично, очень довольны качеством. Брали двусторонний матрас, в итоге спим на жёсткой стороне, спина не болит."),
    ("Евгений Матвеев", "07.07.2022", "Отличное качество. Купили себе, детям и соседям. Все очень довольны. Быстрая доставка. Радуют скидки. Большой выбор наполнения и обтяжной ткани матраца."),
    ("Юлия Волкова", "04.07.2022", "Отличные матрасы! Особенно император люкс. Очень нравится!!! Спасибо отдельное Борису, который занимается доставкой!"),
    ("Антон Тихонов", "26.04.2022", "Хорошее соотношение цены и качества, пользуюсь год, пока доволен."),
    ("Евгений", "23.03.2022", "Отличные матрасы! Отличный персонал! Доставили вовремя. Покупал матрас по совету знакомых и остался очень доволен! Советую выбирать данную компанию!"),
    ("Валерий П.", "25.02.2022", "Хочу поблагодарить производителей этой компании. Отличные матрасы выпускает эта фабрика. Купил у них с доставкой один матрас девять лет назад, он и сейчас как новенький. Купил дорогой зима-лето с кокосовой койрой. Очень тепло лежать на нём. Были матрасы других производителей (более дешёвые), но они через пару лет проминались очень сильно, даже форму не держали. Теперь только у них буду покупать."),
    ("Дарья Шишкина", "13.02.2022", "Хороший выбор матрасов, цены доступные, радуют сроки, так как своё производство, матрас делают за 2–3 дня, заказала, оформили быстро, доставили и занесли в дом, уже неделю сплю и радуюсь, очень удобно. Персонал вежливый и грамотный, ничего не навязывают."),
    ("Любовь С.", "02.02.2022", "Отличная работа, девушки-консультанты всё объяснили, посоветовали и помогли с выбором. Производство и доставка в срок. Для владельцев диванов «аккордеон» просто спасение: сменили наполнение — и диван как новый. Всё отлажено, чётко и в сроки, спасибо!"),
]
def review_cards(items): return '<div class="reviews">' + "".join(f'<figure class="review"><blockquote>{e(t)}</blockquote><figcaption><b>{e(n)}</b><span>{d}</span></figcaption></figure>' for n, d, t in items) + "</div>"
AWARDS = [("award1", "Сертификат I степени «За высокие потребительские качества» — за модель матраса «Монарх»"),
          ("award2", "Диплом «За высокий уровень качества продукции», Москва, 2013"),
          ("award3", "Диплом участника 24-й международной выставки «Мебель-2012», ЦВК «Экспоцентр»"),
          ("award4", "Грамота Всероссийского смотра-конкурса отечественных производителей — за модельный ряд детских матрасов")]
def awards(pg): return '<div class="awards">' + "".join(f'<figure><img src="{pg.a(f"img/site/{a}.jpg")}" alt="{e(t)}" loading="lazy"><figcaption>{e(t)}</figcaption></figure>' for a, t in AWARDS) + "</div>"
WHY = [("factory", "Собственное производство", "Мы — производитель: не арендуем помещения и не нанимаем подрядчиков, поэтому вы не переплачиваете за логистику."),
       ("shield", "Гарантия на все товары", "Если товар не соответствует заявленным качествам, заменим его или вернём деньги."),
       ("ruler", "Матрасы на заказ", "Изготовим модель по вашим размерам и с нужными наполнителями."),
       ("scale", "Цена и качество", "Комбинируя материалы и технологии, мы добились выгодного соотношения цены и качества.")]
def why(): return '<div class="why">' + "".join(f'<div>{ICON[i]}<b>{t}</b><p>{d}</p></div>' for i, t, d in WHY) + "</div>"

HARD_OPTS = [("Мягкий", "Мягкие"), ("Средней жесткости", "Средней жёсткости"), ("Жесткий", "Жёсткие"), ("raz", "Разная жёсткость сторон")]
def hard_match(p, k): return p["specs"].get("Категория: Разносторонний") == "Да" if k == "raz" else k in sides(p)

# ---------------------------------------------------------------- страницы
def build_home():
    pg = Page("")
    regular = [p for p in P if p["category"] != "sale"]
    sale = [p for p in P if p["category"] == "sale"]
    popular = [BY[i] for i in ["matras-imperator", "matras-iris", "matras-zevs", "matras-lotos", "matras-germes", "matras-virtuoz", "matras-afrodita", "matras-sultan"] if i in BY]
    cat_tiles = "".join(
        f'''<a class="cat" href="{pg.u(c["url"])}"><div class="pic">{(lambda pp: f'<img src="{pg.a(pp["image"])}" alt="" loading="lazy">' if pp else "")(next((x for x in P if x["category"] == c["id"] and x.get("image")), None))}</div>
        <b>{e(c["name"])}</b><span class="muted">{count_label(sum(1 for x in P if x["category"] == c["id"]))}, <span class="nowrap">от {rub(min(promo_price(x, x["min_price"])[0] for x in P if x["category"] == c["id"]))}</span></span></a>''' for c in CATS)
    bars = {"Мягкий": [1, 2], "Средней жесткости": [1, 2, 3], "Жесткий": [1, 2, 3, 4, 5], "raz": [1, 5]}
    hard_html = '<div class="hard-pick">' + "".join(
        f'<a href="{pg.u("matrasy/?hard=" + k)}"><b>{t}</b><div class="scale">{"".join(f"<i class={chr(34)}{"on" if i in bars[k] else ""}{chr(34)}></i>" for i in range(1, 6))}</div><span class="muted small">{count_label(sum(1 for p in P if p["category"] == "matrasy" and hard_match(p, k)))}</span></a>'
        for k, t in HARD_OPTS) + "</div>"
    body = f'''
<section class="hero2"><img src="{pg.a("img/site/hero.jpg")}" srcset="{pg.a("img/site/hero-m.jpg")} 1000w, {pg.a("img/site/hero.jpg")} 1920w" sizes="100vw" alt="Спальня с матрасом" class="hero2-img">
  <div class="wrap hero2-in"><div class="hero2-card">
    <p class="eyebrow">Производство фабрики «Торбеевские матрасы»</p><h1>Эргономичные матрасы и изделия для комфортного сна</h1>
    <p class="hero-sub">{len(regular)} моделей матрасов, топперов и наматрасников для взрослых и детей. Делаем сами в Подмосковье, доставляем по Москве, области и всей России.</p>
    <div class="hero-cta"><a class="btn" href="{pg.u("matrasy/")}">Выбрать матрас</a><button class="btn ghost" data-callback="Консультация">Проконсультироваться</button></div>
  </div></div></section>
<section class="facts-strip"><div class="wrap facts2"><div><b>{len(regular)}</b><span>моделей</span></div><div><b>18 месяцев</b><span>гарантия на матрасы</span></div><div><b>Любой размер</b><span>изготовим на заказ</span></div><div><b>Шоурум</b><span>пос. Торбеево, ежедневно 10–20</span></div></div></section>
{sec("Каталог", f'<div class="cats">{cat_tiles}</div>')}
{sec("Подобрать по жёсткости", hard_html, cls="tight")}
{sec("Популярные модели", grid(pg, popular), link=("Все матрасы", pg.u("matrasy/")), cls="tight")}
{sec("Распродажа", grid(pg, sale[:4]), sub="Штучные позиции в наличии, один размер. Количество ограничено.", link=("Все предложения", pg.u("sale/")), cls="tight") if sale else ""}
{sec("Почему выбирают нас", why(), cls="tight")}
<section class="sec made"><div class="wrap made-in">
  <div class="made-pic"><img src="{pg.a("img/site/fabric.jpg")}" alt="Стёганый жаккард с логотипом фабрики" loading="lazy"><img src="{pg.a("img/site/quilt.jpg")}" alt="Матрас в фирменном чехле" loading="lazy"></div>
  <div><h2>Делаем сами, в Подмосковье</h2><p class="muted big">Каждый матрас собираем на своём производстве в пос. Торбеево: независимые пружинные блоки, натуральный латекс, кокосовая койра, чехлы из хлопкового жаккарда и трикотажа.</p>
    <ul class="made-list"><li><b>{count_label(sum(1 for p in P if p["category"] == "matrasy"))} матрасов</b><span>от мягких до жёстких, с пружинами и без</span></li>
    <li><b>Нестандартные размеры</b><span>изготовим по вашим меркам и с нужными наполнителями</span></li>
    <li><b>Шоурум в Торбеево</b><span>приезжайте полежать на матрасах — {e(SHOP["hours"].lower())}</span></li></ul></div></div></section>
{sec("Награды", awards(pg), sub="Дипломы выставок и конкурсов отечественных производителей.", cls="tight")}
{sec("Отзывы покупателей", review_cards(REVIEWS[:6]), link=("Все отзывы", pg.u("otzyvy/")), cls="tight")}
<section class="sec seo"><div class="wrap prose narrow"><h2>Анатомические матрасы</h2>
<p>Анатомическими называют матрасы, которые в той или иной степени повторяют физиологические изгибы лежащего на них человека. Основная цель — разгрузить позвоночник и расслабить мышцы всего тела, обеспечив полноценный отдых.</p>
<p>Анатомические матрасы не являются лечебным оборудованием, но их профилактический эффект для здоровья спины трудно переоценить. Пружинные матрасы выполняются на блоке независимых пружин. В качестве наполнителя, перераспределяющего нагрузку, используются кокосовая койра, латекс, пенополиуретан, холлофайбер.</p></div></section>'''
    write(pg, layout(pg, title="Торбеевские матрасы — производство матрасов и товаров для сна в Москве и МО",
                     desc="Фабрика «Торбеевские матрасы»: пружинные и беспружинные матрасы, топперы, наматрасники, детские модели. Собственное производство в Подмосковье, доставка по России.",
                     body=body, page_type="home"))

CAT_TEXT = {
 "matrasy": ("Матрасы", "Пружинные и беспружинные матрасы собственного производства. Гарантия 18 месяцев."),
 "toppery": ("Топперы (тонкие матрасы)", "Тонкие матрасы — для выравнивания дивана, дачи или как дополнительный слой на основной матрас."),
 "namatrasniki": ("Наматрасники", "Защитные, непромокаемые и анатомические наматрасники."),
 "detskie-matrasy": ("Детские матрасы", "Матрасы для детских кроваток и подростковых кроватей."),
 "detskie-namatrasniki": ("Детские наматрасники", "Непромокаемые и гигиенические наматрасники для детских матрасов."),
 "sale": ("Распродажа", "Штучные матрасы в наличии по сниженной цене. Один размер, количество ограничено — наличие подтвердит менеджер."),
}
def build_category(c):
    pg = Page(c["url"]); items = [p for p in P if p["category"] == c["id"]]
    items.sort(key=lambda p: (not p.get("image"), p["name"]))
    title, intro = CAT_TEXT[c["id"]]
    cnt = lambda fn: sum(1 for p in items if fn(p))
    widths = sorted({v["w"] for p in items for v in p["variants"]})
    hard = "".join(f'<label class="fopt"><input type="checkbox" data-f="hard" value="{k}">{t}<span class="n">{cnt(lambda p, k=k: hard_match(p, k))}</span></label>' for k, t in HARD_OPTS if cnt(lambda p, k=k: hard_match(p, k)))
    springs = "".join(f'<label class="fopt"><input type="checkbox" data-f="spring" value="{s}">{s}<span class="n">{cnt(lambda p, s=s: p["specs"].get("Категория: Пружины") == s)}</span></label>' for s in ["С пружинами", "Без пружин"] if cnt(lambda p, s=s: p["specs"].get("Категория: Пружины") == s))
    fl = f'''<aside class="filters" id="filters" aria-label="Фильтры"><div class="f-head"><h3>Фильтры</h3><button class="link" id="fclose">Готово</button></div>
      {f'<label class="fopt hot"><input type="checkbox" id="fpromo"> Только со скидкой</label>' if HAS_PROMO else ""}
      {f"<h4>Жёсткость</h4>{hard}" if hard else ""}{f"<h4>Пружины</h4>{springs}" if cnt(lambda p: p["specs"].get("Категория: Пружины") == "С пружинами") else ""}
      <h4>Ширина, см</h4><div class="wbtns">{"".join(f'<button type="button" data-w="{w}">{w}</button>' for w in widths)}</div>
      <h4>Цена, ₽</h4><div class="prange"><input type="number" inputmode="numeric" placeholder="от" id="pmin" aria-label="Цена от"><input type="number" inputmode="numeric" placeholder="до" id="pmax" aria-label="Цена до"></div>
      <button class="link freset">Сбросить фильтры</button></aside>'''
    other = '<div class="sublinks">' + "".join(f'<a href="{pg.u(x["url"])}"{" aria-current=" + chr(34) + "page" + chr(34) if x["id"] == c["id"] else ""}>{e(x["name"])}</a>' for x in CATS) + "</div>"
    body = f'''<div class="wrap"><div class="cat-head"><h1>{e(title)}</h1><p class="muted">{e(intro)}</p>{other}</div>
  <div class="cat-layout">{fl}<div class="cat-main"><div class="toolbar"><span class="muted" id="fcount">{count_label(len(items))}</span>
    <div class="tb-right"><button class="btn ghost sm f-open" id="fopen">Фильтры</button><label class="sr" for="sort">Сортировка</label>
    <select id="sort"><option value="pop">Сначала с фото</option><option value="asc">Сначала дешевле</option><option value="desc">Сначала дороже</option><option value="name">По названию</option></select></div></div>
    <div class="grid" id="plist">{"".join(card(pg, p) for p in items)}</div>
    <div class="empty" id="fempty" hidden>Ничего не найдено. <button class="link freset">Сбросить фильтры</button></div></div></div></div><div class="f-shade" id="fshade"></div>'''
    write(pg, layout(pg, title=f"{title} — купить в Москве | {SHOP['name']}", desc=intro, body=body, page_type="category", crumbs=[("Каталог", None), (title, None)]))

SPEC_GROUPS = [("Жёсткость", ["Жесткость верх", "Жесткость низ", "Разносторонний"]),
               ("Конструкция", ["Пружинный блок", "Кол-во пружин на спальное место", "Кол-во пружин на м²", "Состав слоев матраса / наполнители", "Анатомический эффект"]),
               ("Чехол", ["Материал чехла", "Съемный чехол"]),
               ("Размеры и вес", ["Высота матраса", "Вес изделия для 160×200, кг", "Нестандартные размеры"]),
               ("Нагрузка", ["Вес на спальное место", "Допустимая разница в весе"]),
               ("Упаковка и гарантия", ["Упаковка", "Гарантия", "Срок службы"])]
SPEC_LABEL = {"Жесткость верх": "Жёсткость: верх", "Жесткость низ": "Жёсткость: низ", "Разносторонний": "Стороны разной жёсткости",
              "Состав слоев матраса / наполнители": "Наполнители", "Высота матраса": "Высота", "Вес изделия для 160×200, кг": "Вес (160×200)",
              "Вес на спальное место": "Нагрузка на спальное место", "Допустимая разница в весе": "Допустимая разница в весе партнёров", "Нестандартные размеры": "Нестандартные размеры"}
def spec_val(p, k):
    s = p["specs"]; v = str(s.get(k, "") or "")
    if not v or (v == "Без пружин" and k != "Пружинный блок"): return ""
    if k in ("Жесткость верх", "Жесткость низ"):
        n = int(float(s.get(k + " шкала 1-10") or 0))
        return f'<span class="hardbar"><span>{e(v.replace("Жесткий", "Жёсткий"))}</span><span class="scale" aria-label="{n} из 10">{"".join(f"<i class={chr(34)}{"on" if i < n else ""}{chr(34)}></i>" for i in range(10))}</span></span>'
    if k == "Состав слоев матраса / наполнители": v = v.replace("Жеский", "Жёсткий").replace("Жесткий", "Жёсткий")
    if k == "Высота матраса": return e(v) + " см"
    if k == "Вес изделия для 160×200, кг": return e(v) + " кг"
    if k == "Вес на спальное место": return "до " + e(v) + " кг"
    if k == "Допустимая разница в весе": return e(v.replace("плюс", "до")) + " кг"
    if k == "Гарантия": return (e(v.replace(".", ",")) + " года") if re.fullmatch(r"\d+([.,]\d+)?", v) else e(v)
    if k == "Упаковка" and "ПЭТ" in v: return "В ПЭТ-плёнке"
    return e(v)

def build_product(p):
    pg = Page(p["path"]); c = next(x for x in CATS if x["id"] == p["category"])
    groups = [(g, [(SPEC_LABEL.get(k, k), spec_val(p, k)) for k in keys]) for g, keys in SPEC_GROUPS]
    groups = [(g, [(l, v) for l, v in rows if v]) for g, rows in groups]; groups = [g for g in groups if g[1]]
    related = [x for x in P if x["category"] == p["category"] and x["id"] != p["id"] and set(sides(x)) & set(sides(p))]
    related.sort(key=lambda x: (not x.get("image"), abs(x["min_price"] - p["min_price"])))
    chips = [hard_label(p), p["specs"].get("Категория: Пружины"), f'Высота {p["specs"]["Высота матраса"]} см' if p["specs"].get("Высота матраса") else "",
             "Двусторонний" if p["specs"].get("Категория: Двухсторонний") == "Да" and "namatras" not in p["category"] else ""]
    warranty = str(p["specs"].get("Гарантия", "") or "")
    gal = f'<img src="{pg.a(p["image"])}" alt="{e(full(p))}">' if p.get("image") else f'<div class="noimg big">{e(p["name"])}<small>Фото скоро появится</small></div>'
    sale_note = f'<p class="sale-note">Штучная позиция со склада, только размер {p["variants"][0]["w"]}×{p["variants"][0]["l"]} см. Наличие подтвердит менеджер.</p>' if p["category"] == "sale" else ""
    body = f'''<div class="wrap"><div class="pp">
  <div><div class="pp-gal">{'<span class="sale-tag">Распродажа</span>' if p["category"] == "sale" else ""}{gal}</div></div>
  <div class="pp-info"><h1>{e(full(p))}</h1>
    <div class="chips">{"".join(f'<span class="chip">{e(x)}</span>' for x in chips if x)}</div>
    <span class="lbl" id="lw">Ширина, см</span><div class="sizes" id="ws" role="group" aria-labelledby="lw"></div>
    <span class="lbl" id="ll">Длина, см</span><div class="sizes" id="lsz" role="group" aria-labelledby="ll"></div>
    <div class="pp-price" id="price">{price_html(p)}</div><div class="promo-line" id="promo" hidden></div><div class="muted" id="sizeTxt"></div>{sale_note}
    <div class="qty-row"><span class="lbl">Количество</span><div class="qty"><button type="button" id="qm" aria-label="Меньше">−</button><span id="qv">1</span><button type="button" id="qp" aria-label="Больше">+</button></div>
      <button class="fav-btn inline" data-fav="{p["id"]}" aria-label="В избранное">{ICON["heart"]}</button></div>
    <div class="pp-actions"><button class="btn" id="add">В корзину</button><button class="btn ghost" id="quick">Быстрый заказ</button></div>
    <p class="muted small">Быстрый заказ — оставьте только телефон, менеджер перезвонит.</p>
    <div class="perks"><div class="perk">{ICON["truck"]}<div><b>Доставка по Москве, МО и России</b>Стоимость и время согласует менеджер. Самовывоз из шоурума в Торбеево.</div></div>
      <div class="perk">{ICON["wallet"]}<div><b>Оплата при получении</b>Наличными или картой.</div></div>
      {f'<div class="perk">{ICON["shield"]}<div><b>Гарантия {spec_val(p, "Гарантия")}</b>{("Срок службы " + e(p["specs"]["Срок службы"])) if p["specs"].get("Срок службы") else ""}</div></div>' if warranty and warranty != "0" else ""}
      <div class="perk">{ICON["ruler"]}<div><b>Нужен другой размер?</b>Изготовим по вашим меркам — <button class="link" data-callback="Нестандартный размер">оставьте заявку</button>.</div></div></div>
  </div></div>
  {f'<section class="specs"><h2>Характеристики</h2><div class="spec-grid">' + "".join(f'<div class="spec-blk"><h3>{g}</h3>' + "".join(f'<div class="spec-row"><span>{e(l)}</span><span>{v}</span></div>' for l, v in rows) + "</div>" for g, rows in groups) + "</div></section>" if groups else ""}
  {f'<section class="sec tight"><div class="sec-h"><h2>Похожие модели</h2></div>{grid(pg, related[:4])}</section>' if related else ""}
</div>'''
    write(pg, layout(pg, title=f"{full(p)} — купить, цена от {rub(promo_price(p, p['min_price'])[0])} | {SHOP['name']}",
                     desc=f"{full(p)}: характеристики, размеры и цены. Производство фабрики «Торбеевские матрасы».", body=body, page_type="product", pid=p["id"],
                     crumbs=[(c["name"], c["url"]), (p["name"], None)]))

def build_simple(path, ptype, title, inner, crumbs, lead=False, desc=""):
    pg = Page(path); write(pg, layout(pg, title=f"{title} — {SHOP['name']}", desc=desc or title, body=inner(pg), page_type=ptype, crumbs=crumbs, lead=lead))

POLICY = """<p>Настоящая Политика обработки персональных данных (далее — Политика) разработана в соответствии с Федеральным законом РФ №152-ФЗ «О персональных данных» и определяет порядок обработки персональных данных и меры по обеспечению их безопасности.</p>
<h2>1. Оператор персональных данных</h2><p>Оператор: ИП Геворгян Рубен Андрикович<br>ИНН: 342102450670<br>ОГРНИП: 323508100652805<br>Адрес: Люберецкий р-н, пос. Торбеево, д.50, стр. 1<br>Email: <a href="mailto:info@tmvo.ru">info@tmvo.ru</a></p>
<h2>2. Персональные данные, которые обрабатываются</h2><ul><li>ФИО</li><li>Номер телефона</li><li>Email</li><li>IP-адрес</li><li>Данные файлов cookie</li><li>Иные данные, предоставленные пользователем</li></ul>
<h2>3. Цели обработки персональных данных</h2><ul><li>Обработка заявок и обратной связи</li><li>Заключение и исполнение договоров</li><li>Информирование пользователя</li><li>Маркетинговые и рекламные рассылки (при согласии)</li><li>Аналитика и улучшение работы сайта</li></ul>
<h2>4. Правовые основания обработки</h2><p>Обработка осуществляется на основании:</p><ul><li>согласия субъекта персональных данных</li><li>необходимости исполнения договора</li><li>требований законодательства РФ</li></ul>
<h2>5. Порядок обработки и хранения</h2><p>Персональные данные обрабатываются с использованием автоматизированных и неавтоматизированных средств. Срок хранения данных — до достижения целей обработки либо до отзыва согласия пользователем.</p>
<h2>6. Передача третьим лицам</h2><p>Персональные данные могут передаваться третьим лицам:</p><ul><li>хостинг-провайдерам</li><li>сервисам аналитики</li><li>CRM-системам</li><li>сервисам рассылок</li></ul>
<h2>7. Трансграничная передача</h2><p>В случае использования зарубежных сервисов персональные данные могут передаваться за пределы РФ в соответствии с законодательством.</p>
<h2>8. Права субъекта персональных данных</h2><p>Пользователь имеет право:</p><ul><li>получить информацию о своих данных</li><li>требовать их уточнения или удаления</li><li>отозвать согласие на обработку</li></ul>
<h2>9. Отзыв согласия</h2><p>Отзыв согласия осуществляется путем направления запроса на email: <a href="mailto:info@tmvo.ru">info@tmvo.ru</a></p>
<h2>10. Меры защиты</h2><p>Оператор принимает необходимые организационные и технические меры для защиты персональных данных.</p>
<h2>11. Заключительные положения</h2><p>Политика может быть изменена без предварительного уведомления. Актуальная версия размещена на сайте.</p>"""

def build_info_pages():
    def dost(pg): return f'''<p class="lead">Доставляем по Москве, Московской области и во все регионы России. Можно забрать заказ самостоятельно из шоурума фабрики.</p>
<h2>Доставка курьером</h2><ul><li>Москва и Московская область — нашим транспортом, в заранее согласованный день и время.</li><li>Регионы России — транспортными компаниями до терминала или до двери.</li><li>Подъём на этаж и занос в квартиру — по договорённости.</li></ul>
<p>Стоимость доставки зависит от адреса и размера заказа — её рассчитает менеджер при подтверждении заказа.</p>
<h2>Самовывоз</h2><p>Шоурум и склад: {e(SHOP["address"])}. {e(SHOP["hours"])}. Пожалуйста, предупредите о визите заранее — менеджер сообщит, когда заказ будет готов. <a href="{pg.u("kontakty/")}">Схема проезда</a>.</p>
<h2>Сроки изготовления</h2><p>Матрасы делаются на нашем производстве. Срок изготовления зависит от модели и размера — менеджер назовёт его при подтверждении заказа. Модели из раздела <a href="{pg.u("sale/")}">«Распродажа»</a> есть в наличии.</p>
<h2>Оплата</h2><ul><li><b>Наличными</b> — курьеру при получении или в шоуруме.</li><li><b>Банковской картой</b> — МИР, Visa, MasterCard при получении.</li><li><b>Для организаций</b> — по счёту, свяжитесь с менеджером.</li></ul>
<h2>Возврат и обмен</h2><p>Возврат и обмен — в соответствии с Законом РФ «О защите прав потребителей». Товар надлежащего качества, купленный дистанционно, можно вернуть в течение 7 дней после получения, если сохранены его товарный вид и потребительские свойства (ст. 26.1). Это правило не распространяется на матрасы, изготовленные по индивидуальным размерам покупателя.</p>
<p>Если обнаружен производственный дефект — позвоните нам: заменим товар или вернём деньги. Подробнее — на странице <a href="{pg.u("garantiya/")}">«Гарантия»</a>.</p>'''
    build_simple("dostavka-i-oplata/", "info", "Доставка и оплата", lambda pg: f'<div class="wrap page-grid"><article class="prose"><h1>Доставка и оплата</h1>{dost(pg)}</article>{aside_help(pg)}</div>', [("Доставка и оплата", None)], lead=True,
                 desc="Доставка матрасов по Москве, МО и России, самовывоз из шоурума в Торбеево, оплата наличными и картой при получении.")
    def gar(pg): return f'''<p class="lead">На матрасы и топперы — гарантия 18 месяцев, на наматрасники — 14 дней. Срок гарантии каждой модели указан в её характеристиках.</p>
<h2>Что входит в гарантию</h2><p>Производственные дефекты: нарушение целостности пружинного блока, расхождение швов, отслоение слоёв наполнителя, деформация, не связанная с неправильной эксплуатацией.</p>
<h2>Что не является гарантийным случаем</h2><ul><li>механические повреждения, порезы, прожоги, следы жидкостей;</li><li>деформация из-за неподходящего основания (например, ламели с большим расстоянием или прогнувшееся дно);</li><li>естественное уплотнение верхних мягких слоёв в первые месяцы использования;</li><li>использование не по назначению: прыжки, сгибание, сидение на краю.</li></ul>
<h2>Как сохранить матрас</h2><ul><li>Кладите матрас на ровное основание: сплошное или с ламелями, расстояние между ними — не больше ширины ламели.</li><li>Раз в 3 месяца поворачивайте матрас «голова — ноги», двусторонний — переворачивайте.</li><li>Используйте наматрасник и не сгибайте пружинные матрасы при перевозке.</li></ul>
<h2>Как обратиться</h2><p>Позвоните по телефону {e(SHOP["phone"])} или напишите на {e(SHOP["email"])}: опишите проблему, приложите фото и номер заказа. Мы ответим и, если дефект подтвердится, заменим товар или вернём деньги.</p>'''
    build_simple("garantiya/", "info", "Гарантия", lambda pg: f'<div class="wrap page-grid"><article class="prose"><h1>Гарантия</h1>{gar(pg)}</article>{aside_help(pg)}</div>', [("Гарантия", None)], lead=True,
                 desc="Гарантия 18 месяцев на матрасы фабрики «Торбеевские матрасы».")
    def contacts(pg): return f'''<div class="wrap"><h1 class="page-h1">Контакты</h1><div class="contacts">
<div class="box"><h3>Связаться с нами</h3><dl class="kv"><dt>Телефон</dt><dd><a href="tel:{SHOP["phone_href"]}">{e(SHOP["phone"])}</a><small>Бесплатный звонок по РФ</small></dd>
<dt>Мессенджеры</dt><dd><a href="tel:{SHOP["mphone_href"]}">{e(SHOP["mphone"])}</a><small>Telegram, MAX</small><span class="msg big-msg"><a href="{SHOP["tg"]}" target="_blank" rel="noopener">{ICON["tg"]} Telegram</a><a href="tel:{SHOP["mphone_href"]}">{ICON["max"]} MAX</a></span></dd>
<dt>Отдел продаж</dt><dd><a href="mailto:{SHOP["email"]}">{e(SHOP["email"])}</a></dd><dt>Время работы</dt><dd>{e(SHOP["hours"])}<small>Принимаем заказы и консультируем без выходных</small></dd>
<dt>Адрес шоурума</dt><dd>{e(SHOP["address"])}</dd></dl><button class="btn" data-callback>Заказать звонок</button></div>
<div class="map"><iframe src="https://yandex.ru/map-widget/v1/?mode=search&amp;text={e(MAP_Q)}&amp;z=15" title="Шоурум на Яндекс Картах" loading="lazy" allowfullscreen></iframe>
<a class="link" href="https://yandex.ru/maps/?mode=search&amp;text={e(MAP_Q)}" target="_blank" rel="noopener">Открыть в Яндекс Картах ↗</a></div></div>
<div class="box req"><h3>Реквизиты</h3><dl class="kv"><dt>Продавец</dt><dd>{e(SHOP["seller"])}</dd><dt>ИНН</dt><dd>{SHOP["inn"]}</dd><dt>ОГРНИП</dt><dd>{SHOP["ogrnip"]}</dd><dt>ОКПО</dt><dd>{SHOP["okpo"]}</dd><dt>Банк</dt><dd>{e(SHOP["bank"])}</dd><dt>БИК</dt><dd>{SHOP["bik"]}</dd><dt>Р/с</dt><dd>{SHOP["rs"]}</dd><dt>Корр/с</dt><dd>{SHOP["ks"]}</dd></dl></div></div>'''
    build_simple("kontakty/", "contacts", "Контакты", contacts, [("Контакты", None)], lead=True, desc=f"Контакты фабрики «Торбеевские матрасы»: {SHOP['phone']}, {SHOP['address']}.")
    build_simple("otzyvy/", "info", "Отзывы", lambda pg: f'<div class="wrap"><h1 class="page-h1">Отзывы покупателей</h1>{review_cards(REVIEWS)}</div>', [("Отзывы", None)], lead=True)
    build_simple("politika-konfidentsialnosti/", "info", "Политика конфиденциальности", lambda pg: f'<div class="wrap page-grid"><article class="prose"><h1>Политика конфиденциальности</h1>{POLICY}</article></div>', [("Политика конфиденциальности", None)])
    for path, key, extra in [("soglasie-na-obrabotku/", "Согласие на обработку персональных данных", "Текст согласия: перечень данных, цели обработки, действия с данными, срок действия согласия и порядок его отзыва."),
                             ("oferta/", "Публичная оферта", "Условия продажи товаров дистанционным способом: оформление заказа, цены, доставка, оплата, возврат и обмен, гарантия.")]:
        build_simple(path, "info", key, lambda pg, key=key, extra=extra: f'''<div class="wrap page-grid"><article class="prose"><h1>{e(key)}</h1>
<p class="ph-note">Здесь будет утверждённый текст документа. При изменении текста увеличьте номер версии в assets/js/config.js — он сохраняется вместе с согласием покупателя.</p>
<p>{e(extra)}</p><p>Продавец: {e(SHOP["seller"])}, ИНН {SHOP["inn"]}, ОГРНИП {SHOP["ogrnip"]}. Контакты: {e(SHOP["email"])}, {e(SHOP["phone"])}.</p></article></div>''', [(key, None)])

def build_shop_pages():
    build_simple("korzina/", "cart", "Корзина", lambda pg: '<div class="wrap"><h1 class="page-h1">Корзина</h1><div id="cart"><p class="muted">Загружаем корзину…</p></div></div>', [("Корзина", None)])
    build_simple("oformlenie/", "checkout", "Оформление заказа", lambda pg: '<div class="wrap" id="co-wrap"><h1 class="page-h1">Оформление заказа</h1><div class="co"><div class="co-main" id="co"></div><aside class="summary" id="co-sum"></aside></div></div>', [("Корзина", "korzina/"), ("Оформление", None)])
    build_simple("zakaz/", "order", "Заказ", lambda pg: '<div class="wrap"><div class="order" id="ord"><p class="muted">Загружаем заказ…</p></div></div>', [("Заказ", None)])
    build_simple("poisk/", "search", "Поиск", lambda pg: f'<div class="wrap"><h1 class="page-h1" id="stitle">Поиск</h1><form class="search big" action="{pg.u("poisk/")}" role="search">{ICON["search"]}<input id="sq" name="q" type="search" aria-label="Поиск по каталогу" placeholder="Название модели или наполнитель"></form><div class="grid" id="sres"></div></div>', [("Поиск", None)])
    build_simple("izbrannoe/", "favorites", "Избранное", lambda pg: '<div class="wrap"><h1 class="page-h1">Избранное</h1><div class="grid" id="fres"></div></div>', [("Избранное", None)])

def build_admin():
    pg = Page("admin/")
    page = f'''<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Заказы — панель менеджера</title><meta name="robots" content="noindex, nofollow">
<link rel="icon" href="{pg.a("img/logo.svg")}" type="image/svg+xml">
<link href="https://fonts.googleapis.com/css2?family=Onest:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{pg.a("assets/css/style.css")}"><link rel="stylesheet" href="{pg.a("assets/css/admin.css")}"></head>
<body data-page="admin"><div id="adm"></div>
<script>window.TMVO_ROOT = "{pg.root}";</script>
<script src="{pg.a("assets/js/config.js")}"></script><script src="{pg.a("data/catalog.js")}"></script>
<script src="{pg.a("assets/js/api.js")}"></script><script src="{pg.a("assets/js/admin.js")}"></script></body></html>'''
    os.makedirs(os.path.join(ROOT, "admin"), exist_ok=True)
    open(os.path.join(ROOT, "admin", "index.html"), "w", encoding="utf-8").write(page)

def build_meta():
    nf = '''<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Страница не найдена — Торбеевские матрасы</title>
<style>body{margin:0;font-family:system-ui,sans-serif;background:#F4F5F7;color:#1D2330;display:grid;place-items:center;min-height:100vh;padding:16px;text-align:center}a{color:#A9532A;font-weight:600}</style></head>
<body><div><h1>Страница не найдена</h1><p>Возможно, ссылка устарела.</p><p><a id="home" href="./">На главную</a></p></div>
<script>(function(){var p=location.pathname.split("/");var root=location.hostname.endsWith("github.io")&&p[1]?"/"+p[1]+"/":"/";document.getElementById("home").href=root+"index.html";})();</script></body></html>'''
    open(os.path.join(ROOT, "404.html"), "w", encoding="utf-8").write(nf)
    open(os.path.join(ROOT, "robots.txt"), "w").write("User-agent: *\nDisallow: /\n" if NOINDEX else f"User-agent: *\nAllow: /\nDisallow: /admin/\nSitemap: {SITE_URL}sitemap.xml\n")
    urls = "".join(f"<url><loc>{SITE_URL}{p}</loc></url>" for p in PAGES)
    open(os.path.join(ROOT, "sitemap.xml"), "w").write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    open(os.path.join(ROOT, ".nojekyll"), "w").write("")

if __name__ == "__main__":
    build_home()
    for c in CATS: build_category(c)
    for p in P: build_product(p)
    build_info_pages(); build_shop_pages(); build_admin(); build_meta()
    print("страниц:", len(PAGES) + 1, "(включая админку)")
