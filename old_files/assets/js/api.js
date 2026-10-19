/*
 * Слой работы с сервером. Интерфейс одинаковый для режимов "mock" и "api".
 * Контракт запросов и ответов описан в TECH_SPEC.md, раздел 5.
 */
(function () {
  const CFG = window.TMVO_CONFIG;
  const LS_ORDERS = "tmvo_mock_orders";
  const LS_SEQ = "tmvo_mock_seq";

  function lsGet(k, d) { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (e) { return d; } }
  function lsSet(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* хранилище недоступно — макет работает до перезагрузки */ } }
  const memory = { orders: null };
  function loadOrders() { if (memory.orders) return memory.orders; memory.orders = lsGet(LS_ORDERS, {}); return memory.orders; }
  function saveOrders() { lsSet(LS_ORDERS, memory.orders); }
  const delay = (ms) => new Promise((r) => setTimeout(r, ms));
  const token = () => Math.random().toString(36).slice(2) + Math.random().toString(36).slice(2);
  const now = () => new Date().toISOString();

  /* ---------- общие проверки (сервер обязан делать то же самое) ---------- */
  function normPhone(p) {
    let d = String(p || "").replace(/\D/g, "");
    if (d.length === 11 && (d[0] === "7" || d[0] === "8")) d = d.slice(1);
    return d.length === 10 ? "+7" + d : null;
  }
  function checkConsents(c) {
    if (!c || c.privacy !== true || c.personal_data !== true) throw apiError("consent_required", "Нужно согласие на обработку персональных данных");
  }
  function apiError(code, message) { const e = new Error(message); e.code = code; return e; }

  /* ---------- цены и скидки (одна функция для всего сайта; сервер обязан считать так же) ---------- */
  function today() { const d = new Date(); return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0"); }
  function promoActive(p, day) { const pr = p && p.promo; day = day || today(); return !!(pr && pr.from <= day && day < pr.to); }
  function priceOf(p, base, day) {
    if (!promoActive(p, day)) return { price: base, old: null, pct: 0, until: null };
    const r = CFG.promoRoundTo || 1;
    const price = Math.ceil(base * (1 - p.promo.pct / 100) / r) * r;
    const until = new Date(p.promo.to + "T00:00:00"); until.setDate(until.getDate() - 1);
    return { price, old: base, pct: p.promo.pct, until };
  }
  window.TMVO_PRICE = { priceOf, promoActive, today };

  // Цена всегда пересчитывается по каталогу — цене из браузера не доверяем.
  function priceItems(items) {
    const cat = window.CATALOG;
    if (!items || !items.length) throw apiError("empty_cart", "Корзина пуста");
    const out = items.map((it) => {
      const p = cat.products.find((x) => x.id === it.product_id);
      if (!p) throw apiError("bad_item", "Товар не найден");
      const v = p.variants.find((x) => x.w === +it.width && x.l === +it.length);
      if (!v) throw apiError("bad_item", "Размер не найден");
      const qty = Math.max(1, Math.min(20, parseInt(it.qty, 10) || 1));
      const pr = priceOf(p, v.price);
      return { product_id: p.id, name: p.name, category: p.category, width: v.w, length: v.l, qty, price: pr.price, old_price: pr.old, discount_pct: pr.pct, sum: pr.price * qty };
    });
    return { items: out, total: out.reduce((s, x) => s + x.sum, 0) };
  }
  function publicOrder(o) { const c = JSON.parse(JSON.stringify(o)); delete c.history; return c; }
  function nextNumber() { const n = lsGet(LS_SEQ, 1000) + 1; lsSet(LS_SEQ, n); return n; }
  function newOrder(type, status, body) {
    const priced = priceItems(body.items);
    const n = nextNumber();
    const o = {
      id: "o" + n, number: n, token: token(), type, status,
      created_at: now(), updated_at: now(),
      customer: { phone: normPhone(body.phone), name: (body.name || "").trim(), email: "", comment: "" },
      items: priced.items, total: priced.total,
      delivery: null, payment: { method: null, status: "not_paid" },
      consents: { privacy: true, personal_data: true, versions: { privacy: CFG.documents.privacy.version, consent: CFG.documents.consent.version }, at: now(), form: body.source || type },
      offer_accepted: false, marketing: false,
      history: [{ at: now(), text: type === "quick" ? "Быстрый заказ с сайта" : "Начато оформление (есть телефон)" }]
    };
    return o;
  }
  function getOwned(id, tk) {
    const o = loadOrders()[id];
    if (!o || o.token !== tk) throw apiError("not_found", "Заказ не найден");
    return o;
  }

  const mock = {
    async getCatalog() { return window.CATALOG; },

    async quickOrder(body) {
      await delay(350);
      if (!normPhone(body.phone)) throw apiError("bad_phone", "Проверьте номер телефона");
      checkConsents(body.consents);
      const o = newOrder("quick", "new", body);
      loadOrders()[o.id] = o; saveOrders();
      return publicOrder(o);
    },

    async callback(body) {
      await delay(300);
      if (!normPhone(body.phone)) throw apiError("bad_phone", "Проверьте номер телефона");
      checkConsents(body.consents);
      return { ok: true };
    },

    async createDraft(body) {
      await delay(300);
      if (!normPhone(body.phone)) throw apiError("bad_phone", "Проверьте номер телефона");
      checkConsents(body.consents);
      const o = newOrder("full", "draft", body);
      loadOrders()[o.id] = o; saveOrders();
      return publicOrder(o);
    },

    async updateOrder(id, tk, patch) {
      await delay(200);
      const o = getOwned(id, tk);
      if (o.status !== "draft") throw apiError("locked", "Заказ уже подтверждён");
      if (patch.phone !== undefined) { const p = normPhone(patch.phone); if (!p) throw apiError("bad_phone", "Проверьте номер телефона"); o.customer.phone = p; }
      ["name", "email", "comment"].forEach((k) => { if (patch[k] !== undefined) o.customer[k] = String(patch[k]).trim(); });
      if (patch.items) { const pr = priceItems(patch.items); o.items = pr.items; o.total = pr.total; }
      if (patch.delivery) {
        const m = CFG.delivery.find((d) => d.id === patch.delivery.method && d.enabled);
        if (!m) throw apiError("bad_delivery", "Способ получения недоступен");
        o.delivery = Object.assign({}, patch.delivery);
      }
      if (patch.payment_method) {
        const m = CFG.payment.find((p) => p.id === patch.payment_method && p.enabled);
        if (!m) throw apiError("bad_payment", "Способ оплаты недоступен");
        o.payment.method = m.id;
      }
      o.updated_at = now(); saveOrders();
      return publicOrder(o);
    },

    async confirmOrder(id, tk, body) {
      await delay(400);
      const o = getOwned(id, tk);
      if (o.status !== "draft") return publicOrder(o);
      if (!body || body.offer_accepted !== true) throw apiError("offer_required", "Нужно принять условия оферты");
      if (!o.customer.name) throw apiError("bad_name", "Укажите имя");
      if (!o.delivery) throw apiError("bad_delivery", "Укажите способ получения");
      if (!o.payment.method) throw apiError("bad_payment", "Выберите способ оплаты");
      const pm = CFG.payment.find((p) => p.id === o.payment.method);
      o.offer_accepted = true; o.marketing = !!body.marketing;
      o.status = pm && pm.online ? "awaiting_payment" : "new";
      o.history.push({ at: now(), text: "Заказ подтверждён покупателем" });
      o.updated_at = now(); saveOrders();
      return publicOrder(o);
    },

    async getOrder(id, tk) { await delay(150); return publicOrder(getOwned(id, tk)); },

    // Онлайн-оплата: в макете имитируется. Сервер должен создать платёж в ЮKassa и вернуть confirmation_url.
    async createPayment(id, tk) {
      await delay(400);
      const o = getOwned(id, tk);
      return { payment_id: "mock_" + o.number, confirmation_url: (window.TMVO_ROOT || "") + "zakaz/index.html?id=" + o.id + "&t=" + o.token };
    }
  };

  /* ---------- рабочий режим: запросы на сервер ---------- */
  async function req(method, path, body) {
    const r = await fetch(CFG.apiBase + path, {
      method, credentials: "same-origin",
      headers: body ? { "Content-Type": "application/json", "Accept": "application/json" } : { "Accept": "application/json" },
      body: body ? JSON.stringify(body) : undefined
    });
    let data = null; try { data = await r.json(); } catch (e) { /* пустой ответ */ }
    if (!r.ok) throw apiError((data && data.error) || "http_" + r.status, (data && data.message) || "Ошибка сервера, попробуйте ещё раз");
    return data;
  }
  const real = {
    getCatalog: () => window.CATALOG ? Promise.resolve(window.CATALOG) : req("GET", "/catalog"),
    quickOrder: (b) => req("POST", "/orders/quick", b),
    callback: (b) => req("POST", "/callback", b),
    createDraft: (b) => req("POST", "/orders", b),
    updateOrder: (id, tk, p) => req("PATCH", "/orders/" + encodeURIComponent(id) + "?token=" + encodeURIComponent(tk), p),
    confirmOrder: (id, tk, b) => req("POST", "/orders/" + encodeURIComponent(id) + "/confirm?token=" + encodeURIComponent(tk), b),
    getOrder: (id, tk) => req("GET", "/orders/" + encodeURIComponent(id) + "?token=" + encodeURIComponent(tk)),
    createPayment: (id, tk, b) => req("POST", "/orders/" + encodeURIComponent(id) + "/payment?token=" + encodeURIComponent(tk), b || {})
  };

  window.TMVO_API = CFG.apiMode === "api" ? real : mock;
  window.TMVO_API.normPhone = normPhone;
})();
