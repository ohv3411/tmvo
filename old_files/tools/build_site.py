"""
Генератор статического сайта «Торбеевские матрасы».
Берёт data/catalog.json (см. tools/build_data.py) и создаёт все HTML-страницы в корне проекта.

    python tools/build_site.py

Ссылки относительные и с явным index.html — сайт работает на GitHub Pages (в т.ч. в подпапке репозитория)
и при открытии файлов с диска. Для рабочего сервера с «чистыми» адресами поставьте CLEAN_URLS = True.
"""
import html, json, os, re
from datetime import date, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAT = json.load(open(os.path.join(ROOT, "data", "catalog.json"), encoding="utf-8"))
CLEAN_URLS = False
NOINDEX = True           # демо-копия: не индексировать, чтобы не дублировать tmvo.ru в поиске
SITE_URL = "https://tmvo.ru/"
TODAY = date.today().isoformat()

SHOP = dict(name="Торбеевские матрасы", phone="8 (495) 150-30-90", phone_href="+74951503090",
            mphone="+7 (985) 800-00-29", mphone_href="+79858000029", messengers="Viber, WhatsApp, Telegram, MAX",
            email="info@tmvo.ru", hours="Ежедневно с 10:00 до 20:00",
            address="Московская обл., Люберецкий р-н, пос. Торбеево, д. 48", address_short="пос. Торбеево, д. 48",
            seller="ИП Геворгян Р. А.", inn="342102450670", ogrnip="323508100652805", okpo="2027978788",
            bank="ПАО Сбербанк", bik="044525225", rs="40802810140000186299", ks="30101810400000000225")
MAP_Q = "Московская область, Люберецкий район, посёлок Торбеево, 48"

e = lambda s: html.escape(str(s if s is not None else ""), quote=True)
def rub(n): return f"{int(round(n)):,}".replace(",", " ") + " ₽"
P = CAT["products"]; BY = {p["id"]: p for p in P}
CATS = {c["id"]: c for c in CAT["categories"]}
def full(p): return (p.get("word") + " " if p.get("word") and p["category"] != "detskie-namatrasniki" else "") + p["name"]
def plural(n, a, b, c):
    m10, m100 = n % 10, n % 100
    return a if m10 == 1 and m100 != 11 else b if 2 <= m10 <= 4 and not 10 <= m100 < 20 else c
def promo_on(p, day=TODAY): pr = p.get("promo"); return bool(pr and pr["from"] <= day < pr["to"])
def promo_price(p, base):
    if not promo_on(p): return base, None
    import math; return int(math.ceil(base * (1 - p["promo"]["pct"] / 100) / 10) * 10), base
def ru_date(iso, minus=0):
    from datetime import timedelta
    d = datetime.strptime(iso, "%Y-%m-%d").date() - timedelta(days=minus)
    return f"{d.day} {['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря'][d.month-1]}"

# ---------------------------------------------------------------- макет
class Page:
    def __init__(self, path):
        self.path = path.strip("/") + "/" if path.strip("/") else ""
        self.depth = self.path.count("/")
        self.root = "../" * self.depth
    def u(self, target):
        target = target.strip("/") + "/" if target.strip("/") else ""
        q = ""
        if "?" in target: target, q = target.split("?", 1); target = target.strip("/") + "/"; q = "?" + q.rstrip("/")
        return self.root + target + ("" if CLEAN_URLS else "index.html") + q
    def a(self, rel): return self.root + rel

NAV_MAT = [("Все матрасы", "matrasy/"), ("Мягкие", "matrasy/?hard=Мягкий"), ("Средней жёсткости", "matrasy/?hard=Средней жесткости"),
           ("Жёсткие", "matrasy/?hard=Жесткий"), ("Разная жёсткость сторон", "matrasy/?hard=Разносторонний"),
           ("Со скидкой", "matrasy/?promo=1"), ("Топперы (тонкие матрасы)", "matrasy/toppery/")]
NAV_SIZES = [("140 × 200", "matrasy/?w=140"), ("160 × 200", "matrasy/?w=160"), ("180 × 200", "matrasy/?w=180"), ("90 × 200", "matrasy/?w=90"), ("200 × 200", "matrasy/?w=200")]
NAV_OTHER = [("Наматрасники", "namatrasniki/"), ("Детские матрасы", "matrasy/detskie/"), ("Детские наматрасники", "namatrasniki/detskie/"), ("Распродажа", "sale/"), ("Акции", "akcii/")]
NAV_BUY = [("Доставка и оплата", "dostavka-i-oplata/"), ("Гарантия", "garantiya/"), ("Уход за матрасом", "uhod-za-matrasom/"), ("Отзывы", "otzyvy/"), ("Блог о здоровом сне", "blog/")]
NAV_ABOUT = [("О фабрике", "o-kompanii/"), ("Партнёрам", "partneram/"), ("Контакты", "kontakty/")]

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
    "phone": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 4h4l2 5-2.5 1.5a11 11 0 005 5L15 13l5 2v4a2 2 0 01-2 2A16 16 0 013 6a2 2 0 012-2z"/></svg>',
}

def layout(pg, *, title, desc, body, page_type="info", pid="", crumbs=None, lead=True):
    links = lambda items: "".join(f'<a href="{pg.u(h)}">{e(t)}</a>' for t, h in items)
    crumbs_html = ""
    if crumbs:
        parts = [f'<a href="{pg.u("")}">Главная</a>'] + [f'<a href="{pg.u(h)}">{e(t)}</a>' if h else f'<span aria-current="page">{e(t)}</span>' for t, h in crumbs]
        crumbs_html = f'<nav class="crumbs wrap" aria-label="Навигация">{" / ".join(parts)}</nav>'
    lead_html = f'''<section class="lead-sec"><div class="wrap lead-in"><div><h2>Остались вопросы — мы поможем</h2><p>Оставьте телефон, и мы перезвоним: подскажем модель, размер и сроки изготовления.</p></div>
      <form class="lead-form" novalidate><label class="sr" for="lp-{pg.depth}">Телефон</label><input class="inp" id="lp-{pg.depth}" name="phone" type="tel" inputmode="tel" autocomplete="tel" placeholder="+7 (___) ___-__-__">
      <button class="btn" disabled>Проконсультироваться</button>
      <label class="cbx"><input type="checkbox" name="privacy"> <span>Соглашаюсь с <a href="{pg.u("politika-konfidentsialnosti/")}">политикой обработки персональных данных</a></span></label>
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
<div class="demo" id="demo" hidden><b>Демо-версия.</b> Заказы не отправляются в магазин и сохраняются только в этом браузере.</div>
<div class="topbar"><div class="wrap topbar-in">
  <a href="{pg.u("kontakty/")}">{ICON["pin"]} {e(SHOP["address_short"])}</a><span>{e(SHOP["hours"])}</span>
  <span class="tb-msg">{e(SHOP["mphone"])} — {e(SHOP["messengers"])}</span>
  <nav class="tb-links" aria-label="Покупателям"><a href="{pg.u("dostavka-i-oplata/")}">Доставка и оплата</a><a href="{pg.u("garantiya/")}">Гарантия</a><a href="{pg.u("otzyvy/")}">Отзывы</a><a href="{pg.u("kontakty/")}">Контакты</a></nav>
</div></div>
<header class="hdr"><div class="wrap hdr-in">
  <button class="icon-btn burger" id="burger" aria-label="Открыть меню">{ICON["menu"]}</button>
  <a class="logo" href="{pg.u("")}" aria-label="{e(SHOP["name"])} — на главную"><img src="{pg.a("img/logo.svg")}" alt="{e(SHOP["name"])}" width="132" height="46"></a>
  <button class="btn catbtn" id="catbtn" aria-expanded="false" aria-controls="megamenu">{ICON["grid"]} Каталог</button>
  <nav class="nav" aria-label="Разделы"><a href="{pg.u("akcii/")}" class="nav-hot">Акции</a><a href="{pg.u("matrasy/")}">Матрасы</a><a href="{pg.u("namatrasniki/")}">Наматрасники</a><a href="{pg.u("matrasy/detskie/")}">Детям</a><a href="{pg.u("sale/")}" class="nav-sale">Распродажа</a></nav>
  <form class="search" action="{pg.u("poisk/")}" role="search"><label class="sr" for="q">Поиск</label>{ICON["search"]}<input id="q" name="q" type="search" placeholder="Поиск по каталогу" autocomplete="off"></form>
  <span class="spacer"></span>
  <a class="icon-btn search-btn" href="{pg.u("poisk/")}" aria-label="Поиск">{ICON["search"]}</a>
  <div class="hdr-tel"><a href="tel:{SHOP["phone_href"]}">{e(SHOP["phone"])}</a><small><button class="link" data-callback>Заказать звонок</button></small></div>
  <a class="icon-btn" href="{pg.u("izbrannoe/")}" aria-label="Избранное">{ICON["heart"]}<span class="badge fav-count" hidden></span></a>
  <a class="icon-btn" href="{pg.u("korzina/")}" aria-label="Корзина">{ICON["cart"]}<span class="badge cart-count" hidden></span></a>
</div>
<div class="megamenu" id="megamenu" hidden><div class="wrap mm-in">
  <div><h4>Матрасы</h4>{links(NAV_MAT)}</div><div><h4>По размеру</h4>{links(NAV_SIZES)}</div>
  <div><h4>Ещё в каталоге</h4>{links(NAV_OTHER)}</div><div><h4>Покупателям</h4>{links(NAV_BUY)}{links(NAV_ABOUT)}</div>
</div></div></header>
<div class="drawer" id="drawer"><div class="shade" data-drawer-close></div><nav class="panel" aria-label="Меню">
  <img src="{pg.a("img/logo.svg")}" alt="" class="dlogo">
  <form class="search" action="{pg.u("poisk/")}" role="search">{ICON["search"]}<input name="q" type="search" placeholder="Поиск по каталогу" aria-label="Поиск"></form>
  <h4>Каталог</h4>{links(NAV_MAT[:1] + NAV_OTHER)}<h4>Покупателям</h4>{links(NAV_BUY + NAV_ABOUT)}
  <div class="dfoot"><a href="tel:{SHOP["phone_href"]}" class="dtel">{e(SHOP["phone"])}</a><span class="muted">{e(SHOP["hours"])}</span></div>
</nav></div>
{crumbs_html}
<main id="main" tabindex="-1">
{body}
</main>
{lead_html}
<footer class="ftr"><div class="wrap"><div class="ftr-grid">
  <div><img src="{pg.a("img/logo.svg")}" alt="{e(SHOP["name"])}" class="flogo"><p>Фабрика матрасов в Подмосковье: матрасы, топперы и наматрасники для взрослых и детей.</p>
    <a class="tel" href="tel:{SHOP["phone_href"]}">{e(SHOP["phone"])}</a><span>Бесплатный звонок по РФ</span>
    <a href="tel:{SHOP["mphone_href"]}">{e(SHOP["mphone"])}</a><span>{e(SHOP["messengers"])}</span><a href="mailto:{SHOP["email"]}">{e(SHOP["email"])}</a></div>
  <div><h4>Каталог</h4>{links(NAV_MAT[:1] + NAV_OTHER)}</div>
  <div><h4>Покупателям</h4>{links(NAV_BUY)}</div>
  <div><h4>О фабрике</h4>{links(NAV_ABOUT)}<p class="faddr">{e(SHOP["address"])}<br>Шоурум: {e(SHOP["hours"].lower())}</p></div>
</div>
<div class="legal"><span>© {date.today().year} {e(SHOP["name"])}. {e(SHOP["seller"])}, ИНН {SHOP["inn"]}, ОГРНИП {SHOP["ogrnip"]}.</span>
  <span><a href="{pg.u("politika-konfidentsialnosti/")}">Политика обработки персональных данных</a> · <a href="{pg.u("soglasie-na-obrabotku/")}">Согласие на обработку данных</a> · <a href="{pg.u("oferta/")}">Публичная оферта</a></span></div>
</div></footer>
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

# ---------------------------------------------------------------- общие блоки
def hard_label(p):
    return {"Средней жесткости": "Средний", "Разносторонний": "Разная жёсткость", "Жесткий": "Жёсткий"}.get(p["specs"].get("Категория: Жёсткость", ""), p["specs"].get("Категория: Жёсткость", ""))
def price_html(p):
    base = p["min_price"]; price, old = promo_price(p, base)
    old = old or p.get("regular_price")
    return f'{"" if len(p["variants"]) == 1 else "<small>от</small> "}<b>{rub(price)}</b>{f" <s>{rub(old)}</s>" if old else ""}'
def card(pg, p):
    img = f'<img src="{pg.a(p["image"])}" alt="{e(full(p))}" loading="lazy">' if p.get("image") else f'<span class="noimg">{e(p["name"])}</span>'
    tags = ('<span class="sale-tag">Распродажа</span>' if p["category"] == "sale" else "") + (f'<span class="promo-tag">−{p["promo"]["pct"]}%</span>' if promo_on(p) else "")
    chips = (f'<span class="chip">{e(hard_label(p))}</span>' if hard_label(p) else "") + (f'<span class="chip">{e(p["specs"]["Высота матраса"])} см</span>' if p["specs"].get("Высота матраса") else "")
    size = f' <small>· {p["variants"][0]["w"]}×{p["variants"][0]["l"]}</small>' if len(p["variants"]) == 1 else ""
    return f'''<article class="card" data-card="{p["id"]}"><a class="pic" href="{pg.u(p["path"])}">{tags}{img}</a>
      <button class="fav-btn" data-fav="{p["id"]}" aria-label="В избранное">{ICON["heart"]}</button>
      <div class="body"><a class="name" href="{pg.u(p["path"])}">{e(full(p))}</a><div class="chips">{chips}</div>
      <div class="price">{price_html(p)}</div>{f'<div class="muted small">Размер {p["variants"][0]["w"]}×{p["variants"][0]["l"]} см</div>' if len(p["variants"]) == 1 else ""}</div></article>'''
def grid(pg, items): return '<div class="grid">' + "".join(card(pg, p) for p in items) + "</div>"
def sec(title, inner, sub="", link=None, cls=""):
    return f'''<section class="sec {cls}"><div class="wrap"><div class="sec-h"><div><h2>{title}</h2>{f'<p class="muted">{sub}</p>' if sub else ""}</div>{f'<a class="link" href="{link[1]}">{link[0]}</a>' if link else ""}</div>{inner}</div></section>'''
def prose(pg, title, html_body, crumbs, desc, aside=""):
    return layout(pg, title=f"{title} — {SHOP['name']}", desc=desc, crumbs=crumbs,
                  body=f'<div class="wrap page-grid"><article class="prose"><h1>{e(title)}</h1>{html_body}</article>{aside}</div>')
def aside_help(pg):
    return f'''<aside class="help-box"><h3>Нужна помощь с выбором?</h3><p>Позвоните или напишите — подскажем модель, размер и сроки.</p>
      <a class="tel" href="tel:{SHOP["phone_href"]}">{e(SHOP["phone"])}</a><p class="muted small">{e(SHOP["mphone"])} — {e(SHOP["messengers"])}<br>{e(SHOP["hours"])}</p>
      <button class="btn block" data-callback>Заказать звонок</button></aside>'''

REVIEWS = [  # отзывы с главной страницы tmvo.ru (имя, дата, текст)
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

BLOG = [
 ("kak-vybrat-matras", "Как выбрать матрас", "img/site/life1.jpg",
  "Пять вопросов, которые стоит задать себе до покупки: размер, жёсткость, тип основы, наполнители и чехол.",
  """<p>Матрас покупают на 10–15 лет, поэтому выбирать его стоит не по картинке, а по нескольким понятным признакам. Начните с размера, затем определитесь с жёсткостью и конструкцией.</p>
<h2>1. Размер</h2><p>Измерьте спальное место кровати изнутри рамы — матрас должен совпадать с ним по ширине и длине. Длина матраса должна быть на 15–20 см больше роста самого высокого из спящих. Стандартные длины — 190, 195 и 200 см; если нужен другой размер, мы изготовим матрас <a href="{root}matrasy/{ix}">по вашим меркам</a>.</p>
<h2>2. Жёсткость</h2><p>Жёсткость подбирают по весу и привычной позе сна. Подробно — в статье <a href="{root}blog/kak-vybrat-zhestkost-matrasa/{ix}">«Как выбрать жёсткость матраса»</a>. Если двое спящих сильно различаются по весу, посмотрите модели с допустимой разницей в весе — она указана в характеристиках каждого матраса.</p>
<h2>3. Пружинный или беспружинный</h2><p><b>Пружинные</b> матрасы с блоком независимых пружин хорошо подстраиваются под изгибы тела: каждая пружина работает отдельно. Чем больше пружин на квадратный метр, тем точнее поддержка. <b>Беспружинные</b> собирают из слоёв латекса, кокосовой койры и пенополиуретана — они тише, не боятся точечной нагрузки и подходят для диванов.</p>
<h2>4. Наполнители</h2><ul><li><b>Кокосовая койра</b> — жёсткий натуральный слой, хорошо проветривается.</li><li><b>Натуральный латекс</b> — упругий и долговечный, быстро восстанавливает форму.</li><li><b>Пенополиуретан</b> — практичная прослойка, задаёт мягкость.</li><li><b>Холлофайбер</b> — мягкий слой под чехлом.</li></ul>
<h2>5. Чехол</h2><p>Хлопковый жаккард и трикотаж приятны телу и пропускают воздух. Съёмный чехол удобнее в уходе — его можно заказать дополнительно.</p>
<p>Если сомневаетесь — <a href="{root}kontakty/{ix}">приезжайте в шоурум</a> в Торбеево и полежите на матрасах сами или позвоните нам: подскажем модель под ваш вес и кровать.</p>"""),
 ("kak-vybrat-zhestkost-matrasa", "Как выбрать жёсткость матраса", "img/site/life2.jpg",
  "Мягкий, средний или жёсткий: как подобрать жёсткость по весу, возрасту и позе сна.",
  """<p>Правильная жёсткость — та, при которой позвоночник во сне остаётся ровным: плечи и таз немного погружаются, а поясница получает поддержку.</p>
<h2>Мягкие матрасы</h2><p>Подходят людям с небольшим весом, тем, кто спит на боку, и пожилым людям — мягкий верхний слой снимает давление с плеч и бёдер. <a href="{root}matrasy/{ix}?hard=Мягкий">Посмотреть мягкие матрасы</a>.</p>
<h2>Средней жёсткости</h2><p>Универсальный вариант для большинства взрослых со средним весом, особенно если вы меняете позу за ночь. <a href="{root}matrasy/{ix}?hard=Средней жесткости">Матрасы средней жёсткости</a>.</p>
<h2>Жёсткие</h2><p>Нужны людям с большим весом, тем, кто спит на животе или спине, и подросткам — жёсткие слои кокоса не дают телу провисать. <a href="{root}matrasy/{ix}?hard=Жесткий">Жёсткие матрасы</a>.</p>
<h2>Разная жёсткость сторон</h2><p>Матрасы с разной жёсткостью сторон позволяют выбрать подходящую сторону и перевернуть матрас, если со временем захочется жёстче или мягче. <a href="{root}matrasy/{ix}?hard=Разносторонний">Матрасы с разной жёсткостью сторон</a>.</p>
<h2>Как читать шкалу</h2><p>В карточке каждой модели жёсткость верха и низа показана по шкале от 1 до 10: 1–3 — мягко, 4–6 — средне, 7–10 — жёстко. Там же указана максимальная нагрузка на спальное место.</p>"""),
 ("kak-vybrat-matras-dlya-rebenka", "Как выбрать матрас для ребёнка", "img/site/life3.jpg",
  "Детский матрас должен быть ровным, упругим и безопасным: на что смотреть родителям.",
  """<p>Позвоночник ребёнка ещё формируется, поэтому детский матрас должен быть ровным и достаточно упругим, а материалы — натуральными и гипоаллергенными.</p>
<h2>Для малышей</h2><p>Для детской кроватки выбирают беспружинные матрасы с кокосовым слоем: они плотные и хорошо проветриваются. Размер — строго по внутренним размерам кроватки, без зазоров по краям.</p>
<h2>Для дошкольников и школьников</h2><p>С 3–4 лет можно переходить на модели средней жёсткости с комбинированным наполнением: кокос плюс латекс или холлофайбер. Двусторонние модели с разной жёсткостью сторон «растут» вместе с ребёнком.</p>
<h2>Для подростков</h2><p>В период активного роста подойдут модели с блоком независимых пружин и жёсткими слоями — они поддерживают спину при увеличении веса.</p>
<h2>Защита</h2><p>Непромокаемый наматрасник продлит жизнь матраса и упростит уход. Смотрите <a href="{root}namatrasniki/detskie/{ix}">детские наматрасники</a> и <a href="{root}matrasy/detskie/{ix}">детские матрасы</a>.</p>"""),
]

# ---------------------------------------------------------------- страницы
def build_home():
    pg = Page("")
    promo_items = [p for p in P if p.get("promo") and p.get("image") and p["category"] != "sale"]
    promo_items.sort(key=lambda p: -p["promo"]["pct"])
    best = promo_items[:8]
    sale = [p for p in P if p["category"] == "sale"]
    hero_p = BY.get("matras-imperator") or P[0]
    pcts = [p["promo"]["pct"] for p in P if p.get("promo")]
    pfrom = min(p["promo"]["from"] for p in P if p.get("promo")) if pcts else None
    pto = max(p["promo"]["to"] for p in P if p.get("promo")) if pcts else None
    regular = [p for p in P if p["category"] != "sale"]
    cat_tiles = "".join(
        f'''<a class="cat" href="{pg.u(c["url"])}"><div class="pic">{(lambda pp: f'<img src="{pg.a(pp["image"])}" alt="" loading="lazy">' if pp and pp.get("image") else "")(next((x for x in P if x["category"] == c["id"] and x.get("image")), None))}</div>
        <b>{e(c["name"])}</b><span class="muted">{(n := sum(1 for x in P if x["category"] == c["id"]))} {plural(n, "модель", "модели", "моделей")}, <span class="nowrap">от {rub(min(promo_price(x, x["min_price"])[0] for x in P if x["category"] == c["id"]))}</span></span></a>'''
        for c in CAT["categories"])
    hard = [("Мягкий", "Мягкие", [1, 2]), ("Средней жесткости", "Средней жёсткости", [1, 2, 3]), ("Жесткий", "Жёсткие", [1, 2, 3, 4, 5]), ("Разносторонний", "Разная жёсткость сторон", [1, 5])]
    hard_html = '<div class="hard-pick">' + "".join(
        f'<a href="{pg.u("matrasy/?hard=" + k)}"><b>{t}</b><div class="scale">{"".join(f"<i class={chr(34)}{"on" if i in on else ""}{chr(34)}></i>" for i in range(1, 6))}</div><span class="muted small">{sum(1 for p in P if p["category"] == "matrasy" and p["specs"].get("Категория: Жёсткость") == k)} моделей</span></a>'
        for k, t, on in hard) + "</div>"
    body = f'''
<section class="hero"><div class="wrap hero-in">
  <div><p class="eyebrow">Производство фабрики «Торбеевские матрасы»</p><h1>Эргономичные матрасы и изделия для комфортного сна</h1>
    <p class="hero-sub">{len(regular)} моделей матрасов, топперов и наматрасников для взрослых и детей. Делаем сами в Подмосковье, доставляем по Москве, области и всей России.</p>
    <div class="hero-cta"><a class="btn" href="{pg.u("matrasy/")}">Выбрать матрас</a><button class="btn ghost-light" data-callback="Консультация">Проконсультироваться</button></div>
    <div class="facts"><div><b>{len(regular)}</b>моделей</div><div><b>18 месяцев</b>гарантия на матрасы</div><div><b>Любой размер</b>изготовим на заказ</div></div></div>
  <div class="hero-img"><img src="{pg.a("img/site/hero.jpg")}" alt="Спальня с матрасом" class="hero-photo">
    <a class="hero-badge" href="{pg.u(hero_p["path"])}"><img src="{pg.a(hero_p["image"])}" alt=""><div><b>{e(full(hero_p))}</b><span class="price">{price_html(hero_p)}</span></div></a></div>
</div></section>

<section class="promo-strip"><div class="wrap promo-in">
  <a href="{pg.u("akcii/")}" class="promo-card hot"><b>Скидки до {max(pcts) if pcts else 0}% на {len(pcts)} {plural(len(pcts), "модель", "модели", "моделей")}</b><span>{f"с {ru_date(pfrom)} по {ru_date(pto, 1)}" if pfrom else ""}</span></a>
  <a href="{pg.u("akcii/")}" class="promo-card"><b>Подарок-сюрприз от нашей команды</b><span>Подробности — у менеджера</span></a>
  <a href="{pg.u("sale/")}" class="promo-card"><b>Распродажа: {len(sale)} {plural(len(sale), "позиция", "позиции", "позиций")} в наличии</b><span>Штучные матрасы по сниженной цене</span></a>
</div></section>

{sec("Почему выбирают нас", why())}
{sec("Каталог", f'<div class="cats">{cat_tiles}</div>')}
{sec("Подобрать по жёсткости", hard_html, cls="tight")}
{sec("Лучшие предложения", grid(pg, best), sub="Модели со скидкой в период акции", link=("Все акции", pg.u("akcii/")), cls="tight") if best else ""}
{sec("Распродажа", grid(pg, sale[:4]), sub="Штучные позиции в наличии, один размер. Количество ограничено.", link=("Все предложения", pg.u("sale/")), cls="tight")}

<section class="sec made"><div class="wrap made-in">
  <div class="made-pic"><img src="{pg.a("img/site/fabric.jpg")}" alt="Стёганый жаккард с логотипом фабрики" loading="lazy"><img src="{pg.a("img/site/quilt.jpg")}" alt="Матрас в фирменном чехле" loading="lazy"></div>
  <div><h2>Делаем сами, в Подмосковье</h2><p class="muted big">Каждый матрас собираем на своём производстве в пос. Торбеево: независимые пружинные блоки, натуральный латекс, кокосовая койра, чехлы из хлопкового жаккарда и трикотажа.</p>
    <ul class="made-list"><li><b>{sum(1 for p in P if p["category"] == "matrasy")} моделей матрасов</b><span>от мягких до жёстких, с пружинами и без</span></li>
    <li><b>Нестандартные размеры</b><span>изготовим по вашим меркам и с нужными наполнителями</span></li>
    <li><b>Шоурум в Торбеево</b><span>приезжайте полежать на матрасах — {e(SHOP["hours"].lower())}</span></li></ul>
    <a class="link" href="{pg.u("o-kompanii/")}">О фабрике</a></div></div></section>

{sec("Награды", awards(pg), sub="Дипломы выставок и конкурсов отечественных производителей.", cls="tight")}
{sec("Отзывы о нашем магазине", review_cards(REVIEWS[:6]), sub="Отзывы покупателей с сайта tmvo.ru", link=("Все отзывы", pg.u("otzyvy/")), cls="tight")}
{sec("Статьи о здоровом сне", '<div class="blog-grid">' + "".join(f'<a class="post" href="{pg.u("blog/" + s + "/")}"><img src="{pg.a(img)}" alt="" loading="lazy"><b>{e(t)}</b><span class="muted">{e(d)}</span></a>' for s, t, img, d, _ in BLOG) + "</div>", link=("Читать блог", pg.u("blog/")), cls="tight")}

<section class="sec seo"><div class="wrap prose narrow"><h2>Анатомические матрасы</h2>
<p>Анатомическими называют матрасы, которые в той или иной степени повторяют физиологические изгибы лежащего на них человека. Основная цель — разгрузить позвоночник и расслабить мышцы всего тела, обеспечив полноценный отдых.</p>
<p>Анатомические матрасы не являются лечебным оборудованием, но их профилактический эффект для здоровья спины трудно переоценить. Пружинные матрасы выполняются на блоке независимых или связанных между собой пружин. В качестве наполнителя, перераспределяющего нагрузку, используются кокосовая койра, латекс, пенополиуретан, холлофайбер.</p>
<p>Интернет-магазин фабрики «Торбеевские матрасы» предлагает изделия для крепкого сна и полноценного отдыха: <a href="{pg.u("matrasy/")}">матрасы</a>, <a href="{pg.u("matrasy/toppery/")}">топперы</a>, <a href="{pg.u("namatrasniki/")}">наматрасники</a> и <a href="{pg.u("matrasy/detskie/")}">детские модели</a>.</p></div></section>'''
    write(pg, layout(pg, title="Торбеевские матрасы — производство матрасов и товаров для сна в Москве и МО",
                     desc="Фабрика «Торбеевские матрасы»: пружинные и беспружинные матрасы, топперы, наматрасники, детские модели. Собственное производство в Подмосковье, доставка по России.",
                     body=body, page_type="home"))

CAT_TEXT = {
 "matrasy": ("Матрасы", "Для полноценного и здорового сна важно выбрать качественный матрас. Все модели — собственного производства фабрики в Подмосковье, гарантия 18 месяцев.",
  """<h2>Какие бывают матрасы</h2><p><b>Пружинные</b> — на блоке независимых пружин: каждая пружина в отдельном чехле и работает сама по себе. Чем больше пружин на квадратный метр, тем точнее матрас повторяет изгибы тела.</p>
<p><b>Беспружинные</b> — из слоёв натуральных и искусственных материалов. Отличаются упругостью, не скрипят и не боятся точечной нагрузки.</p>
<p><b>С разной жёсткостью сторон</b> — одна сторона мягче, другая жёстче: матрас можно перевернуть под свои ощущения.</p>
<h2>Наполнители</h2><ul><li><b>Латекс</b> — натуральный материал из сока гевеи: прочный, упругий, быстро восстанавливает форму.</li><li><b>Кокосовое волокно</b> — жёсткий, долговечный и влагостойкий слой; обычно сочетается с другими наполнителями.</li><li><b>Пенополиуретан</b> — практичная гипоаллергенная прослойка.</li></ul>
<p>Чтобы заказать матрас, выберите модель и размер и оформите заказ на сайте или позвоните нам — менеджер поможет с выбором. Доставляем по Москве, области и всем регионам России.</p>"""),
 "toppery": ("Топперы (тонкие матрасы)", "Тонкие матрасы высотой от 7 см — для выравнивания дивана, дачи или как дополнительный слой на основной матрас.", ""),
 "namatrasniki": ("Наматрасники", "Защитные, непромокаемые и анатомические наматрасники — продлевают жизнь матраса и добавляют комфорта.", ""),
 "detskie-matrasy": ("Детские матрасы", "Матрасы для детских кроваток и подростковых кроватей из натуральных гипоаллергенных материалов.", ""),
 "detskie-namatrasniki": ("Детские наматрасники", "Непромокаемые и гигиенические наматрасники для детских матрасов.", ""),
 "sale": ("Распродажа", "Штучные матрасы в наличии по сниженной цене. Один размер, количество ограничено — наличие подтвердит менеджер.", ""),
}
def build_category(c):
    pg = Page(c["url"]); items = [p for p in P if p["category"] == c["id"]]
    items.sort(key=lambda p: (not p.get("image"), not promo_on(p)))
    title, intro, seo = CAT_TEXT[c["id"]]
    count = lambda fn: sum(1 for p in items if fn(p))
    hard_opts = [("Мягкий", "Мягкие"), ("Средней жесткости", "Средней жёсткости"), ("Жесткий", "Жёсткие"), ("Разносторонний", "Разная жёсткость сторон")]
    widths = sorted({v["w"] for p in items for v in p["variants"]})
    fl = f'''<aside class="filters" id="filters" aria-label="Фильтры"><div class="f-head"><h3>Фильтры</h3><button class="link" id="fclose">Готово</button></div>
      <label class="fopt hot"><input type="checkbox" id="fpromo"> Только со скидкой<span class="n">{count(lambda p: p.get("promo"))}</span></label>
      <h4>Жёсткость</h4>{"".join(f'<label class="fopt"><input type="checkbox" data-f="hard" value="{e(k)}">{t}<span class="n">{count(lambda p, k=k: p["specs"].get("Категория: Жёсткость") == k)}</span></label>' for k, t in hard_opts if count(lambda p, k=k: p["specs"].get("Категория: Жёсткость") == k))}
      {f'<h4>Пружины</h4>' + "".join(f'<label class="fopt"><input type="checkbox" data-f="spring" value="{s}">{s}<span class="n">{count(lambda p, s=s: p["specs"].get("Категория: Пружины") == s)}</span></label>' for s in ["С пружинами", "Без пружин"] if count(lambda p, s=s: p["specs"].get("Категория: Пружины") == s)) if count(lambda p: p["specs"].get("Категория: Пружины") == "С пружинами") else ""}
      <h4>Ширина, см</h4><div class="wbtns">{"".join(f'<button type="button" data-w="{w}">{w}</button>' for w in widths)}</div>
      <h4>Цена, ₽</h4><div class="prange"><input type="number" inputmode="numeric" placeholder="от" id="pmin" aria-label="Цена от"><input type="number" inputmode="numeric" placeholder="до" id="pmax" aria-label="Цена до"></div>
      <button class="link freset">Сбросить фильтры</button></aside>'''
    sub_links = ""
    if c["id"] == "matrasy":
        sub_links = '<div class="sublinks">' + "".join(f'<a href="{pg.u(h)}">{t}</a>' for t, h in [("Топперы", "matrasy/toppery/"), ("Детские", "matrasy/detskie/"), ("Распродажа", "sale/"), ("160 × 200", "matrasy/?w=160"), ("140 × 200", "matrasy/?w=140"), ("Со скидкой", "matrasy/?promo=1")]) + "</div>"
    body = f'''<div class="wrap"><div class="cat-head"><h1>{e(title)}</h1><p class="muted">{e(intro)}</p>{sub_links}</div>
  <div class="cat-layout">{fl}<div class="cat-main"><div class="toolbar"><span class="muted" id="fcount">{len(items)} {plural(len(items), "модель", "модели", "моделей")}</span>
    <div class="tb-right"><button class="btn ghost sm f-open" id="fopen">Фильтры</button><label class="sr" for="sort">Сортировка</label>
    <select id="sort"><option value="pop">Сначала популярные</option><option value="asc">Сначала дешевле</option><option value="desc">Сначала дороже</option><option value="name">По названию</option></select></div></div>
    <div class="grid" id="plist">{"".join(card(pg, p) for p in items)}</div>
    <div class="empty" id="fempty" hidden>Ничего не найдено. <button class="link freset">Сбросить фильтры</button></div></div></div>
  {f'<div class="prose narrow seo-text">{seo}</div>' if seo else ""}</div><div class="f-shade" id="fshade"></div>'''
    crumbs = [("Матрасы", "matrasy/"), (title, None)] if c["url"].startswith("matrasy/") and c["id"] != "matrasy" else \
             [("Наматрасники", "namatrasniki/"), (title, None)] if c["id"] == "detskie-namatrasniki" else [(title, None)]
    write(pg, layout(pg, title=f"{title} — купить в Москве по выгодной цене | {SHOP['name']}", desc=intro, body=body, page_type="category", crumbs=crumbs))

SPEC_GROUPS = [("Жёсткость", ["Жесткость верх", "Жесткость низ", "Разносторонний"]),
               ("Конструкция", ["Пружинный блок", "construction", "Кол-во пружин на спальное место", "Кол-во пружин на м²", "Состав слоев матраса / наполнители", "Анатомический эффект"]),
               ("Чехол", ["Материал чехла", "Съемный чехол"]),
               ("Размеры и вес", ["Высота матраса", "Вес изделия для 160×200, кг", "Нестандартные размеры"]),
               ("Нагрузка", ["Вес на спальное место", "Допустимая разница в весе"]),
               ("Упаковка и гарантия", ["Упаковка", "Гарантия", "Срок службы"])]
SPEC_LABEL = {"Жесткость верх": "Жёсткость: верх", "Жесткость низ": "Жёсткость: низ", "Разносторонний": "Стороны разной жёсткости", "construction": "Плотность пружин",
              "Состав слоев матраса / наполнители": "Наполнители", "Высота матраса": "Высота", "Вес изделия для 160×200, кг": "Вес (160×200)",
              "Вес на спальное место": "Нагрузка на спальное место", "Допустимая разница в весе": "Допустимая разница в весе партнёров", "Нестандартные размеры": "Нестандартные размеры"}
def spec_val(p, k):
    s = p["specs"]
    if k == "construction":
        v = p.get("construction", ""); return v if v and v not in ("Беспружинный", "— не указано —") and "(" in v else ""
    v = s.get(k, "")
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
    pg = Page(p["path"]); c = CATS[p["category"]]
    groups = [(g, [(SPEC_LABEL.get(k, k), spec_val(p, k)) for k in keys]) for g, keys in SPEC_GROUPS]
    groups = [(g, [(l, v) for l, v in rows if v]) for g, rows in groups]; groups = [g for g in groups if g[1]]
    related = [x for x in P if x["category"] == p["category"] and x["id"] != p["id"] and x["specs"].get("Категория: Жёсткость") == p["specs"].get("Категория: Жёсткость")]
    related.sort(key=lambda x: (not x.get("image"), abs(x["min_price"] - p["min_price"])))
    chips = [hard_label(p), p["specs"].get("Категория: Пружины"), f'Высота {p["specs"]["Высота матраса"]} см' if p["specs"].get("Высота матраса") else "",
             "Двусторонний" if p["specs"].get("Категория: Двухсторонний") == "Да" and "namatras" not in p["category"] else ""]
    warranty = p["specs"].get("Гарантия", "")
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
  {f'<section class="specs"><h2>О модели</h2><p class="desc">{e(p["description"])}</p></section>' if p.get("description") else ""}
  {f'<section class="specs"><h2>Характеристики</h2><div class="spec-grid">' + "".join(f'<div class="spec-blk"><h3>{g}</h3>' + "".join(f'<div class="spec-row"><span>{e(l)}</span><span>{v}</span></div>' for l, v in rows) + "</div>" for g, rows in groups) + "</div></section>" if groups else ""}
  {f'<section class="sec tight"><div class="sec-h"><h2>Похожие модели</h2></div>{grid(pg, related[:4])}</section>' if related else ""}
</div>'''
    crumbs = [(c["name"], c["url"]), (p["name"], None)]
    if c["id"] in ("toppery", "detskie-matrasy"): crumbs = [("Матрасы", "matrasy/")] + crumbs
    if c["id"] == "detskie-namatrasniki": crumbs = [("Наматрасники", "namatrasniki/")] + crumbs
    write(pg, layout(pg, title=f"{full(p)} — купить, цена от {rub(promo_price(p, p['min_price'])[0])} | {SHOP['name']}",
                     desc=(p.get("description") or f"{full(p)}: характеристики, размеры и цены.")[:160], body=body, page_type="product", pid=p["id"], crumbs=crumbs))

def build_akcii():
    pg = Page("akcii/")
    pr = [p for p in P if p.get("promo")]
    by_end = {}
    for p in pr: by_end.setdefault((p["promo"]["from"], p["promo"]["to"]), []).append(p)
    blocks = ""
    for (f, t), items in sorted(by_end.items(), key=lambda x: x[0]):
        items.sort(key=lambda p: (not p.get("image"), -p["promo"]["pct"]))
        blocks += f'<h2 class="promo-h">Скидки с {ru_date(f)} по {ru_date(t, 1)} включительно <span class="muted">· {len(items)} {plural(len(items), "модель", "модели", "моделей")}</span></h2>' + grid(pg, items)
    body = f'''<div class="wrap"><div class="cat-head"><h1>Акции</h1><p class="muted">Цены со скидкой показываются в каталоге и в корзине автоматически в период акции.</p></div>
  <div class="promo-big">
    <div class="promo-card hot"><b>Скидки до {max(p["promo"]["pct"] for p in pr)}%</b><span>на {len(pr)} {plural(len(pr), "модель", "модели", "моделей")} матрасов и наматрасников</span></div>
    <div class="promo-card"><b>Подарок-сюрприз от нашей команды</b><span>Условия и подарок уточняйте у менеджера при заказе.</span><button class="btn sm" data-callback="Узнать о подарке">Узнать подробности</button></div>
    <a class="promo-card" href="{pg.u("sale/")}"><b>Распродажа</b><span>Штучные матрасы в наличии по сниженной цене</span></a></div>
  {blocks}</div>'''
    write(pg, layout(pg, title=f"Акции и скидки — {SHOP['name']}", desc="Действующие скидки на матрасы и наматрасники фабрики «Торбеевские матрасы».", body=body, page_type="category-static", crumbs=[("Акции", None)]))

def build_simple(path, ptype, title, inner, crumbs, lead=False, desc=""):
    pg = Page(path); write(pg, layout(pg, title=f"{title} — {SHOP['name']}", desc=desc or title, body=inner(pg), page_type=ptype, crumbs=crumbs, lead=lead))

def build_info_pages():
    # Доставка и оплата
    def dost(pg): return f'''<p class="lead">Доставляем по Москве, Московской области и во все регионы России. Можно забрать заказ самостоятельно из шоурума фабрики.</p>
<h2>Доставка курьером</h2><ul><li>Москва и Московская область — нашим транспортом, в заранее согласованный день и время.</li><li>Регионы России — транспортными компаниями до терминала или до двери.</li><li>Подъём на этаж и занос в квартиру — по договорённости.</li></ul>
<p>Стоимость доставки зависит от адреса и размера заказа — её рассчитает менеджер при подтверждении заказа.</p>
<h2>Самовывоз</h2><p>Шоурум и склад: {e(SHOP["address"])}. {e(SHOP["hours"])}. Пожалуйста, предупредите о визите заранее — менеджер сообщит, когда заказ будет готов. <a href="{pg.u("kontakty/")}">Схема проезда</a>.</p>
<h2>Сроки изготовления</h2><p>Матрасы делаются на нашем производстве. Срок изготовления зависит от модели и размера — менеджер назовёт его при подтверждении заказа. Модели из раздела <a href="{pg.u("sale/")}">«Распродажа»</a> есть в наличии.</p>
<h2>Оплата</h2><ul><li><b>Наличными</b> — курьеру при получении или в шоуруме.</li><li><b>Банковской картой</b> — МИР, Visa, MasterCard при получении.</li><li><b>Для организаций</b> — по счёту, свяжитесь с менеджером.</li></ul>
<p class="muted">Оплата онлайн на сайте (СБП, банковская карта) будет доступна позже.</p>
<h2>Возврат и обмен</h2><p>Возврат и обмен — в соответствии с Законом РФ «О защите прав потребителей». Товар надлежащего качества, купленный дистанционно, можно вернуть в течение 7 дней после получения, если сохранены его товарный вид и потребительские свойства (ст. 26.1). Это правило не распространяется на матрасы, изготовленные по индивидуальным размерам покупателя.</p>
<p>Если обнаружен производственный дефект — позвоните нам: заменим товар или вернём деньги. Подробнее — на странице <a href="{pg.u("garantiya/")}">«Гарантия»</a>.</p>
<p class="ph-note">Условия доставки и возврата составлены по данным сайта и закона. Перед запуском их нужно сверить с фактическими условиями магазина.</p>'''
    build_simple("dostavka-i-oplata/", "info", "Доставка и оплата", lambda pg: f'<div class="wrap page-grid"><article class="prose"><h1>Доставка и оплата</h1>{dost(pg)}</article>{aside_help(pg)}</div>', [("Доставка и оплата", None)], lead=True,
                 desc="Доставка матрасов по Москве, МО и России, самовывоз из шоурума в Торбеево, оплата наличными и картой при получении.")
    def gar(pg): return f'''<p class="lead">На матрасы и топперы — гарантия 18 месяцев, на наматрасники — 14 дней. Срок гарантии каждой модели указан в её характеристиках.</p>
<h2>Что входит в гарантию</h2><p>Производственные дефекты: нарушение целостности пружинного блока, расхождение швов, отслоение слоёв наполнителя, деформация, не связанная с неправильной эксплуатацией.</p>
<h2>Что не является гарантийным случаем</h2><ul><li>механические повреждения, порезы, прожоги, следы жидкостей;</li><li>деформация из-за неподходящего основания (например, ламели с большим расстоянием или прогнувшееся дно);</li><li>естественное уплотнение верхних мягких слоёв в первые месяцы использования;</li><li>использование не по назначению: прыжки, сгибание, сидение на краю.</li></ul>
<h2>Как обратиться</h2><p>Позвоните по телефону {e(SHOP["phone"])} или напишите на {e(SHOP["email"])}: опишите проблему, приложите фото и номер заказа. Мы ответим и, если дефект подтвердится, заменим товар или вернём деньги.</p>
<p>Чтобы матрас прослужил дольше, следуйте <a href="{pg.u("uhod-za-matrasom/")}">рекомендациям по уходу</a>.</p>
<p class="ph-note">Перечень гарантийных случаев нужно сверить с гарантийным талоном фабрики.</p>'''
    build_simple("garantiya/", "info", "Гарантия", lambda pg: f'<div class="wrap page-grid"><article class="prose"><h1>Гарантия</h1>{gar(pg)}</article>{aside_help(pg)}</div>', [("Гарантия", None)], lead=True,
                 desc="Гарантия 18 месяцев на матрасы фабрики «Торбеевские матрасы»: что входит в гарантию и как обратиться.")
    def uhod(pg): return '''<p class="lead">Несколько простых правил помогут матрасу сохранить форму и свойства на весь срок службы.</p>
<h2>После покупки</h2><ul><li>Снимите упаковочную плёнку и дайте матрасу проветриться несколько часов.</li><li>Положите матрас на ровное основание: сплошное или с ламелями, расстояние между ними — не больше ширины ламели.</li></ul>
<h2>Каждый день</h2><ul><li>Используйте наматрасник — он защищает чехол от загрязнений и влаги.</li><li>Проветривайте спальню: наполнителям нужен воздух.</li><li>Не прыгайте на матрасе и не сидите долго на одном краю.</li></ul>
<h2>Раз в 3 месяца</h2><ul><li>Поворачивайте матрас «голова — ноги», а двусторонний — переворачивайте, чтобы нагрузка распределялась равномерно.</li><li>Пропылесосьте поверхность мягкой насадкой.</li></ul>
<h2>Чистка</h2><p>Пятна удаляйте сразу, мягкой влажной губкой с нейтральным мылом, не замачивая матрас. Не используйте отбеливатели и паровые очистители. Съёмный чехол стирайте по рекомендациям на ярлыке.</p>
<h2>Хранение и перевозка</h2><p>Храните и перевозите матрас горизонтально или на боку, в упаковке. Не сгибайте и не скручивайте пружинные матрасы.</p>'''
    build_simple("uhod-za-matrasom/", "info", "Уход за матрасом", lambda pg: f'<div class="wrap page-grid"><article class="prose"><h1>Уход за матрасом</h1>{uhod(pg)}</article>{aside_help(pg)}</div>', [("Уход за матрасом", None)], lead=True)
    def about(pg): return f'''<div class="wrap"><div class="about-hero"><div><h1>О фабрике «Торбеевские матрасы»</h1>
<p class="lead">Мы производим матрасы, топперы и наматрасники в Подмосковье, в посёлке Торбеево. Сами разрабатываем модели, собираем их на своём производстве и продаём напрямую — без посредников.</p>
<div class="why compact">{"".join(f'<div>{ICON[i]}<b>{t}</b><p>{d}</p></div>' for i, t, d in WHY)}</div></div>
<img src="{pg.a("img/site/fabric2.jpg")}" alt="Фирменный жаккард фабрики" class="about-img"></div>
<section class="sec tight"><h2>Что мы делаем</h2><div class="stats"><div><b>{sum(1 for p in P if p["category"] == "matrasy")}</b>моделей взрослых матрасов</div><div><b>{sum(1 for p in P if p["category"] == "toppery")}</b>топперов</div><div><b>{sum(1 for p in P if "namatras" in p["category"])}</b>наматрасников</div><div><b>{sum(1 for p in P if p["category"] == "detskie-matrasy")}</b>детских моделей</div></div>
<p class="prose">Используем блоки независимых пружин разной плотности, натуральный латекс, латексированную кокосовую койру, холлофайбер и пенополиуретан. Чехлы — из хлопкового жаккарда и трикотажа. Изготавливаем матрасы нестандартных размеров по меркам покупателя.</p></section>
<section class="sec tight"><h2>Награды</h2>{awards(pg)}</section>
<section class="sec tight"><h2>Шоурум</h2><p class="prose">Приезжайте, чтобы полежать на матрасах и выбрать подходящую жёсткость: {e(SHOP["address"])}. {e(SHOP["hours"])}. <a href="{pg.u("kontakty/")}">Как добраться</a>.</p></section></div>'''
    build_simple("o-kompanii/", "info", "О фабрике", about, [("О фабрике", None)], lead=True, desc="Фабрика «Торбеевские матрасы»: собственное производство матрасов в Подмосковье, награды, шоурум.")
    def partners(pg): return f'''<div class="wrap page-grid"><article class="prose"><h1>Партнёрам</h1>
<p class="lead">Приглашаем к сотрудничеству мебельные магазины, производителей мебели, гостиницы, санатории, детские и медицинские учреждения.</p>
<h2>Что предлагаем</h2><ul><li>Матрасы, топперы и наматрасники собственного производства — весь ассортимент каталога.</li><li>Изготовление по вашим размерам и техническому заданию, в том числе крупными партиями.</li><li>Индивидуальные условия для оптовых покупателей.</li><li>Доставку по Москве, области и регионам России.</li></ul>
<h2>Как начать</h2><p>Напишите на <b>{e(SHOP["email"])}</b> или позвоните {e(SHOP["phone"])}: расскажите о вашей компании и объёмах — подготовим предложение.</p>
<button class="btn" data-callback="Сотрудничество">Оставить заявку</button></article>{aside_help(pg)}</div>'''
    build_simple("partneram/", "info", "Партнёрам", partners, [("Партнёрам", None)], lead=False)
    def contacts(pg): return f'''<div class="wrap"><h1 class="page-h1">Контакты</h1><div class="contacts">
<div class="box"><h3>Связаться с нами</h3><dl class="kv"><dt>Телефон</dt><dd><a href="tel:{SHOP["phone_href"]}">{e(SHOP["phone"])}</a><small>Бесплатный звонок по РФ</small></dd>
<dt>Мессенджеры</dt><dd><a href="tel:{SHOP["mphone_href"]}">{e(SHOP["mphone"])}</a><small>{e(SHOP["messengers"])}</small></dd>
<dt>Отдел продаж</dt><dd><a href="mailto:{SHOP["email"]}">{e(SHOP["email"])}</a></dd><dt>Время работы</dt><dd>{e(SHOP["hours"])}<small>Принимаем заказы и консультируем без выходных</small></dd>
<dt>Адрес шоурума</dt><dd>{e(SHOP["address"])}</dd></dl><button class="btn" data-callback>Заказать звонок</button></div>
<div class="map"><iframe src="https://yandex.ru/map-widget/v1/?mode=search&amp;text={e(MAP_Q)}&amp;z=15" title="Шоурум на Яндекс Картах" loading="lazy" allowfullscreen></iframe>
<a class="link" href="https://yandex.ru/maps/?mode=search&amp;text={e(MAP_Q)}" target="_blank" rel="noopener">Открыть в Яндекс Картах ↗</a></div></div>
<div class="box req"><h3>Реквизиты</h3><dl class="kv"><dt>Продавец</dt><dd>{e(SHOP["seller"])}</dd><dt>ИНН</dt><dd>{SHOP["inn"]}</dd><dt>ОГРНИП</dt><dd>{SHOP["ogrnip"]}</dd><dt>ОКПО</dt><dd>{SHOP["okpo"]}</dd><dt>Банк</dt><dd>{e(SHOP["bank"])}</dd><dt>БИК</dt><dd>{SHOP["bik"]}</dd><dt>Р/с</dt><dd>{SHOP["rs"]}</dd><dt>Корр/с</dt><dd>{SHOP["ks"]}</dd></dl></div></div>'''
    build_simple("kontakty/", "contacts", "Контакты", contacts, [("Контакты", None)], lead=True, desc=f"Контакты фабрики «Торбеевские матрасы»: {SHOP['phone']}, {SHOP['address']}.")
    build_simple("otzyvy/", "info", "Отзывы", lambda pg: f'<div class="wrap"><h1 class="page-h1">Отзывы покупателей</h1><p class="muted">Отзывы с сайта tmvo.ru.</p>{review_cards(REVIEWS)}</div>', [("Отзывы", None)], lead=True)
    # Блог
    def blog_index(pg): return '<div class="wrap"><h1 class="page-h1">Блог о здоровом сне</h1><div class="blog-grid">' + "".join(f'<a class="post" href="{pg.u("blog/" + s + "/")}"><img src="{pg.a(img)}" alt="" loading="lazy"><b>{e(t)}</b><span class="muted">{e(d)}</span></a>' for s, t, img, d, _ in BLOG) + "</div></div>"
    build_simple("blog/", "info", "Блог о здоровом сне", blog_index, [("Блог", None)], lead=True)
    for s, t, img, d, txt in BLOG:
        def post(pg, t=t, img=img, txt=txt):
            body = txt.replace("{root}", pg.root).replace("{ix}", "" if CLEAN_URLS else "index.html")
            return f'<div class="wrap page-grid"><article class="prose"><h1>{e(t)}</h1><img src="{pg.a(img)}" alt="" class="post-img">{body}</article>{aside_help(pg)}</div>'
        build_simple(f"blog/{s}/", "info", t, post, [("Блог", "blog/"), (t, None)], lead=True, desc=d)
    # Документы
    for path, key, extra in [("politika-konfidentsialnosti/", "Политика обработки персональных данных", "Документ определяет, какие персональные данные собирает сайт (телефон, имя, e-mail, адрес доставки), с какой целью (оформление и доставка заказов, ответы на обращения), как они хранятся и как отозвать согласие."),
                             ("soglasie-na-obrabotku/", "Согласие на обработку персональных данных", "Текст согласия: перечень данных, цели обработки, действия с данными, срок действия согласия и порядок его отзыва."),
                             ("oferta/", "Публичная оферта", "Условия продажи товаров дистанционным способом: оформление заказа, цены, доставка, оплата, возврат и обмен, гарантия.")]:
        build_simple(path, "info", key, lambda pg, key=key, extra=extra: f'''<div class="wrap page-grid"><article class="prose"><h1>{e(key)}</h1><p class="muted">Версия 1.0</p>
<p class="ph-note">Здесь будет утверждённый текст документа. Его готовит магазин и согласует с юристом. При изменении текста нужно увеличить номер версии в assets/js/config.js — он сохраняется вместе с согласием покупателя.</p>
<p>{e(extra)}</p><p>Оператор / продавец: {e(SHOP["seller"])}, ИНН {SHOP["inn"]}, ОГРНИП {SHOP["ogrnip"]}. Адрес: {e(SHOP["address"])}. Контакты: {e(SHOP["email"])}, {e(SHOP["phone"])}.</p></article></div>''', [(key, None)])

def build_shop_pages():
    build_simple("korzina/", "cart", "Корзина", lambda pg: '<div class="wrap"><h1 class="page-h1">Корзина</h1><div id="cart"><p class="muted">Загружаем корзину…</p></div></div>', [("Корзина", None)])
    build_simple("oformlenie/", "checkout", "Оформление заказа", lambda pg: '<div class="wrap" id="co-wrap"><h1 class="page-h1">Оформление заказа</h1><div class="co"><div class="co-main" id="co"></div><aside class="summary" id="co-sum"></aside></div></div>', [("Корзина", "korzina/"), ("Оформление", None)])
    build_simple("zakaz/", "order", "Заказ", lambda pg: '<div class="wrap"><div class="order" id="ord"><p class="muted">Загружаем заказ…</p></div></div>', [("Заказ", None)])
    build_simple("poisk/", "search", "Поиск", lambda pg: f'<div class="wrap"><h1 class="page-h1" id="stitle">Поиск</h1><form class="search big" action="{pg.u("poisk/")}" role="search">{ICON["search"]}<input id="sq" name="q" type="search" aria-label="Поиск по каталогу" placeholder="Название модели или наполнитель"></form><div class="grid" id="sres"></div></div>', [("Поиск", None)])
    build_simple("izbrannoe/", "favorites", "Избранное", lambda pg: '<div class="wrap"><h1 class="page-h1">Избранное</h1><div class="grid" id="fres"></div></div>', [("Избранное", None)])

def build_meta():
    nf = '''<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Страница не найдена — Торбеевские матрасы</title>
<style>body{margin:0;font-family:system-ui,sans-serif;background:#F4F5F7;color:#1D2330;display:grid;place-items:center;min-height:100vh;padding:16px;text-align:center}a{color:#A9532A;font-weight:600}</style></head>
<body><div><h1>Страница не найдена</h1><p>Возможно, ссылка устарела.</p><p><a id="home" href="./">На главную</a></p></div>
<script>(function(){var p=location.pathname.split("/");var root=location.hostname.endsWith("github.io")&&p[1]?"/"+p[1]+"/":"/";document.getElementById("home").href=root+"index.html";})();</script></body></html>'''
    open(os.path.join(ROOT, "404.html"), "w", encoding="utf-8").write(nf)
    open(os.path.join(ROOT, "robots.txt"), "w").write("User-agent: *\nDisallow: /\n" if NOINDEX else f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n")
    urls = "".join(f"<url><loc>{SITE_URL}{p}</loc></url>" for p in PAGES)
    open(os.path.join(ROOT, "sitemap.xml"), "w").write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    open(os.path.join(ROOT, ".nojekyll"), "w").write("")

if __name__ == "__main__":
    build_home()
    for c in CAT["categories"]: build_category(c)
    for p in P: build_product(p)
    build_akcii(); build_info_pages(); build_shop_pages(); build_meta()
    print("страниц:", len(PAGES))
