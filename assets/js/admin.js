/*
 * Панель менеджера: заказы и заявки на звонок.
 * mock / lite — читает заказы из localStorage этого браузера (вход test / test из config.js, это не защита).
 * api — работает через сервер: /api/admin/* (TECH_SPEC.md, раздел 10).
 */
(function () {
  const CFG = window.TMVO_CONFIG, CAT = window.CATALOG, ROOT = window.TMVO_ROOT || "";
  const $ = (s, r) => (r || document).querySelector(s), $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const rub = (n) => Math.round(n || 0).toLocaleString("ru-RU").replace(/ |,/g, " ") + " ₽";
  const dt = (s) => { try { return new Date(s).toLocaleString("ru-RU", { day: "2-digit", month: "2-digit", year: "2-digit", hour: "2-digit", minute: "2-digit" }); } catch (e) { return s; } };
  const phone = (p) => { const d = String(p || "").replace(/\D/g, "").slice(-10); return d.length === 10 ? `+7 (${d.slice(0, 3)}) ${d.slice(3, 6)}-${d.slice(6, 8)}-${d.slice(8)}` : (p || "—"); };
  const ls = { get(k, d) { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (e) { return d; } }, set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* недоступно */ } } };
  const ss = { get(k) { try { return sessionStorage.getItem(k); } catch (e) { return null; } }, set(k, v) { try { sessionStorage.setItem(k, v); } catch (e) { /* недоступно */ } }, del(k) { try { sessionStorage.removeItem(k); } catch (e) { /* недоступно */ } } };
  const byId = (id) => CAT.products.find((p) => p.id === id);
  const fullName = (p) => (p.word && p.category !== "detskie-namatrasniki" ? p.word + " " : "") + p.name;

  const STATUS = [["draft", "Незавершённое оформление"], ["new", "Новый"], ["in_work", "В работе"], ["awaiting_payment", "Ожидает оплаты"], ["paid", "Оплачен"], ["delivery", "В доставке"], ["done", "Выполнен"], ["canceled", "Отменён"]];
  const SNAME = Object.fromEntries(STATUS);
  const PAY = Object.fromEntries(CFG.payment.map((p) => [p.id, p.title]));
  const DEL = Object.fromEntries(CFG.delivery.map((p) => [p.id, p.title]));
  const API_MODE = CFG.apiMode === "api";

  /* ---------- источник данных ---------- */
  const local = {
    async login(l, p) { if (l === CFG.adminDemo.login && p === CFG.adminDemo.password) return { token: "demo" }; throw new Error("Неверный логин или пароль"); },
    async orders() { return Object.values(ls.get("tmvo_mock_orders", {})).sort((a, b) => (b.created_at > a.created_at ? 1 : -1)); },
    async saveOrder(o) { const all = ls.get("tmvo_mock_orders", {}); all[o.id] = o; ls.set("tmvo_mock_orders", all); return o; },
    async callbacks() { return ls.get("tmvo_mock_callbacks", []); },
    async saveCallback(c) { const all = ls.get("tmvo_mock_callbacks", []); const i = all.findIndex((x) => x.id === c.id); if (i >= 0) all[i] = c; ls.set("tmvo_mock_callbacks", all); return c; }
  };
  async function req(method, path, body) {
    const r = await fetch(CFG.apiBase + "/admin" + path, { method, credentials: "same-origin", headers: { "Content-Type": "application/json", "Authorization": "Bearer " + (ss.get("tmvo_admin") || "") }, body: body ? JSON.stringify(body) : undefined });
    const d = await r.json().catch(() => null); if (!r.ok) throw new Error((d && d.message) || "Ошибка сервера"); return d;
  }
  const remote = {
    login: (l, p) => req("POST", "/login", { login: l, password: p }),
    orders: () => req("GET", "/orders"), saveOrder: (o) => req("PATCH", "/orders/" + encodeURIComponent(o.id), { status: o.status, manager_comment: o.manager_comment }),
    callbacks: () => req("GET", "/callbacks"), saveCallback: (c) => req("PATCH", "/callbacks/" + encodeURIComponent(c.id), { status: c.status })
  };
  const DS = API_MODE ? remote : local;

  /* ---------- вход ---------- */
  const app = $("#adm");
  function loginView(err) {
    app.innerHTML = `<div class="adm-login"><form id="lf" class="box" novalidate><img src="${ROOT}img/logo.svg" alt="Торбеевские матрасы" class="adm-logo"><h1>Вход для менеджера</h1>
      <div class="field"><label for="lg">Логин</label><input class="inp" id="lg" autocomplete="username" required></div>
      <div class="field"><label for="pw">Пароль</label><input class="inp" id="pw" type="password" autocomplete="current-password" required></div>
      <div class="err-msg" role="alert">${esc(err || "")}</div><button class="btn block">Войти</button>
      ${API_MODE ? "" : `<p class="muted small">Демо-доступ: <b>${esc(CFG.adminDemo.login)}</b> / <b>${esc(CFG.adminDemo.password)}</b>. Показываются заказы, оформленные на сайте в этом же браузере.</p>`}
      <a class="link small" href="${ROOT}index.html">← На сайт</a></form></div>`;
    $("#lg").focus();
    $("#lf").onsubmit = async (e) => { e.preventDefault(); try { const r = await DS.login($("#lg").value.trim(), $("#pw").value); ss.set("tmvo_admin", r.token); main(); } catch (er) { loginView(er.message); } };
  }

  /* ---------- основной экран ---------- */
  const st = { tab: "orders", status: "all", q: "", open: null };
  let ORDERS = [], CALLS = [];
  async function load() { [ORDERS, CALLS] = await Promise.all([DS.orders(), DS.callbacks()]); }
  async function main() {
    try { await load(); } catch (e) { ss.del("tmvo_admin"); return loginView(e.message); }
    render();
  }
  function shell(inner) {
    const newCalls = CALLS.filter((c) => c.status === "new").length;
    return `<header class="adm-top"><div class="adm-top-in"><img src="${ROOT}img/logo.svg" alt="" class="adm-logo-s"><nav>
      <button class="${st.tab === "orders" ? "on" : ""}" data-tab="orders">Заказы <span>${ORDERS.length}</span></button>
      <button class="${st.tab === "calls" ? "on" : ""}" data-tab="calls">Заявки на звонок ${newCalls ? `<span class="hot">${newCalls}</span>` : `<span>${CALLS.length}</span>`}</button></nav>
      <span class="adm-mode">${API_MODE ? "Рабочий режим" : "Демо: данные этого браузера"}</span>
      <button class="link" id="refresh">Обновить</button><button class="link" id="logout">Выйти</button></div></header><main class="adm-main">${inner}</main>`;
  }
  function render() {
    app.innerHTML = shell(st.tab === "orders" ? ordersView() : callsView());
    $$("[data-tab]").forEach((b) => (b.onclick = () => { st.tab = b.dataset.tab; st.open = null; render(); }));
    $("#logout").onclick = () => { ss.del("tmvo_admin"); loginView(); };
    $("#refresh").onclick = async () => { await load(); render(); };
    if (st.tab === "orders") bindOrders(); else bindCalls();
  }

  function ordersView() {
    const q = st.q.replace(/\D/g, "") || st.q.toLowerCase();
    const list = ORDERS.filter((o) => (st.status === "all" || o.status === st.status) &&
      (!st.q || String(o.number).includes(st.q) || String(o.customer.phone).replace(/\D/g, "").includes(q) || (o.customer.name || "").toLowerCase().includes(st.q.toLowerCase())));
    const cnt = (s) => ORDERS.filter((o) => o.status === s).length;
    const tabs = `<div class="adm-tabs"><button data-st="all" class="${st.status === "all" ? "on" : ""}">Все <span>${ORDERS.length}</span></button>${STATUS.map(([k, t]) => `<button data-st="${k}" class="${st.status === k ? "on" : ""}">${t} <span>${cnt(k)}</span></button>`).join("")}</div>`;
    if (!ORDERS.length) return `<div class="adm-empty"><h2>Заказов пока нет</h2><p>Оформите заказ на сайте в этом же браузере — быстрый или полный — и он появится здесь.</p>
      <p><a class="btn" href="${ROOT}matrasy/index.html" target="_blank">Открыть каталог</a> <button class="btn ghost" id="demoFill">Добавить 3 примера заказов</button></p></div>`;
    return `<div class="adm-head"><h1>Заказы</h1><input class="inp adm-search" id="q" type="search" placeholder="Номер, телефон или имя" value="${esc(st.q)}" aria-label="Поиск заказа"></div>${tabs}
      <div class="adm-split ${st.open ? "has-open" : ""}"><div class="adm-table-wrap"><table class="adm-table"><thead><tr><th>№</th><th>Тип</th><th>Создан</th><th>Клиент</th><th>Товары</th><th class="r">Сумма</th><th>Статус</th></tr></thead><tbody>
      ${list.map((o) => `<tr data-open="${o.id}" class="${st.open === o.id ? "sel" : ""} ${o.status === "new" ? "is-new" : ""}" tabindex="0"><td><b>${o.number}</b>${o.example ? ' <span class="ex">пример</span>' : ""}</td><td><span class="typ ${o.type}">${o.type === "quick" ? "Быстрый" : "Полный"}</span></td><td>${dt(o.created_at)}</td>
        <td>${esc(o.customer.name || "—")}<br><span class="muted">${phone(o.customer.phone)}</span></td><td>${esc(o.items[0] ? o.items[0].name + " " + o.items[0].width + "×" + o.items[0].length : "")}${o.items.length > 1 ? ` <span class="muted">+${o.items.length - 1}</span>` : ""}</td>
        <td class="r">${rub(o.total)}</td><td><span class="sb s-${o.status}">${SNAME[o.status] || o.status}</span></td></tr>`).join("") || `<tr><td colspan="7" class="muted">Ничего не найдено</td></tr>`}
      </tbody></table></div>${st.open ? orderCard(ORDERS.find((o) => o.id === st.open)) : ""}</div>`;
  }
  function orderCard(o) {
    if (!o) return "";
    const d = o.delivery || {};
    const addr = d.method === "courier" ? `${d.city || ""}, ${d.street || ""}${d.flat ? ", кв./офис " + d.flat : ""}${d.floor ? ", этаж " + d.floor : ""}${d.lift ? ", есть грузовой лифт" : ""}` : d.method ? DEL[d.method] : "не указано — уточнить по телефону";
    const c = o.consents || {};
    return `<aside class="adm-card" aria-label="Заказ ${o.number}"><div class="adm-card-h"><h2>Заказ № ${o.number}</h2><button class="link" id="close">Закрыть</button></div>
      <div class="adm-sec"><h4>Клиент</h4><p class="big"><a href="tel:${esc(o.customer.phone)}">${phone(o.customer.phone)}</a></p><p>${esc(o.customer.name || "Имя не указано")}${o.customer.email ? `<br>${esc(o.customer.email)}` : ""}</p>${o.customer.comment ? `<p class="note">${esc(o.customer.comment)}</p>` : ""}</div>
      <div class="adm-sec"><h4>Товары</h4>${o.items.map((x) => { const p = byId(x.product_id); return `<div class="row"><span>${esc(p ? fullName(p) : x.name)}, ${x.width}×${x.length} × ${x.qty}</span><b>${rub(x.sum)}</b></div>`; }).join("")}<div class="row t"><span>Итого</span><b>${rub(o.total)}</b></div></div>
      <div class="adm-sec"><h4>Получение и оплата</h4><p>${esc(addr)}</p><p>${esc(PAY[(o.payment || {}).method] || "Способ оплаты не выбран")} — ${(o.payment || {}).status === "paid" ? "оплачено" : "не оплачено"}</p></div>
      <div class="adm-sec"><h4>Обработка</h4><label class="lbl" for="ost">Статус</label><select class="inp" id="ost">${STATUS.map(([k, t]) => `<option value="${k}" ${o.status === k ? "selected" : ""}>${t}</option>`).join("")}</select>
        <label class="lbl" for="ocm">Комментарий менеджера</label><textarea class="inp" id="ocm" rows="3" placeholder="Например: доставка в субботу после 12:00">${esc(o.manager_comment || "")}</textarea>
        <button class="btn" id="osave">Сохранить</button> <span class="muted small" id="osaved"></span></div>
      <div class="adm-sec"><h4>Согласия</h4><p class="small">Политика ПДн: ${c.privacy ? "да" : "нет"}, согласие на обработку: ${c.personal_data ? "да" : "нет"}${c.versions ? ` (версии ${esc(c.versions.privacy || "—")} / ${esc(c.versions.consent || "—")})` : ""}<br>Форма: ${esc(c.form || o.type)}, ${dt(c.at || o.created_at)}${o.offer_accepted ? "<br>Оферта принята" : ""}${o.marketing ? ", согласие на рассылку" : ""}</p></div>
      <div class="adm-sec"><h4>История</h4>${(o.history || []).slice().reverse().map((h) => `<div class="hist"><span>${dt(h.at)}</span>${esc(h.text)}</div>`).join("")}</div></aside>`;
  }
  function bindOrders() {
    const q = $("#q"); if (q) q.oninput = (e) => { st.q = e.target.value; const pos = e.target.selectionStart; render(); const n = $("#q"); n.focus(); n.setSelectionRange(pos, pos); };
    $$("[data-st]").forEach((b) => (b.onclick = () => { st.status = b.dataset.st; render(); }));
    $$("[data-open]").forEach((r) => { r.onclick = () => { st.open = r.dataset.open; render(); }; r.onkeydown = (e) => { if (e.key === "Enter") { st.open = r.dataset.open; render(); } }; });
    const cl = $("#close"); if (cl) cl.onclick = () => { st.open = null; render(); };
    const sv = $("#osave"); if (sv) sv.onclick = async () => {
      const o = ORDERS.find((x) => x.id === st.open); const ns = $("#ost").value, cm = $("#ocm").value.trim();
      o.history = o.history || [];
      if (ns !== o.status) o.history.push({ at: new Date().toISOString(), text: `Статус: ${SNAME[o.status]} → ${SNAME[ns]} (менеджер)` });
      if (cm !== (o.manager_comment || "")) o.history.push({ at: new Date().toISOString(), text: "Комментарий менеджера изменён" });
      o.status = ns; o.manager_comment = cm; o.updated_at = new Date().toISOString();
      await DS.saveOrder(o); render(); const m = $("#osaved"); if (m) m.textContent = "Сохранено";
    };
    const df = $("#demoFill"); if (df) df.onclick = async () => { await demoFill(); await load(); render(); };
  }

  function callsView() {
    if (!CALLS.length) return `<div class="adm-empty"><h2>Заявок на звонок пока нет</h2><p>Отправьте форму «Заказать звонок» или «Остались вопросы» на сайте в этом же браузере.</p></div>`;
    return `<div class="adm-head"><h1>Заявки на звонок</h1></div><div class="adm-table-wrap"><table class="adm-table"><thead><tr><th>Создана</th><th>Телефон</th><th>Имя</th><th>Тема</th><th>Статус</th></tr></thead><tbody>
      ${CALLS.map((c) => `<tr class="${c.status === "new" ? "is-new" : ""}"><td>${dt(c.created_at)}</td><td><a href="tel:${esc(c.phone)}">${phone(c.phone)}</a></td><td>${esc(c.name || "—")}</td><td>${esc(c.topic || "Звонок")}</td>
        <td><label class="cbx"><input type="checkbox" data-done="${c.id}" ${c.status === "done" ? "checked" : ""}> Обработана</label></td></tr>`).join("")}</tbody></table></div>`;
  }
  function bindCalls() {
    $$("[data-done]").forEach((i) => (i.onchange = async () => { const c = CALLS.find((x) => x.id === i.dataset.done); c.status = i.checked ? "done" : "new"; await DS.saveCallback(c); render(); }));
  }

  // Примеры для показа (помечены «пример»)
  async function demoFill() {
    const pick = (id, w, l, q) => { const p = byId(id) || CAT.products[0]; const v = p.variants.find((x) => x.w === w && x.l === l) || p.variants[0]; return { product_id: p.id, name: p.name, category: p.category, width: v.w, length: v.l, qty: q, price: v.price, sum: v.price * q }; };
    const mk = (n, type, status, name, ph, items, delivery, pay, minsAgo) => {
      const at = new Date(Date.now() - minsAgo * 60000).toISOString(); const total = items.reduce((s, x) => s + x.sum, 0);
      return { id: "ex" + n, number: n, token: "example", type, status, example: true, created_at: at, updated_at: at, customer: { phone: ph, name, email: "", comment: "" }, items, total,
        delivery, payment: { method: pay, status: "not_paid" }, consents: { privacy: true, personal_data: true, versions: { privacy: "1.0", consent: "1.0" }, at, form: type }, offer_accepted: type === "full", marketing: false,
        history: [{ at, text: type === "quick" ? "Быстрый заказ с сайта (пример)" : "Заказ подтверждён покупателем (пример)" }] };
    };
    const all = ls.get("tmvo_mock_orders", {});
    [mk(901, "quick", "new", "", "+79001234567", [pick("matras-germes", 160, 200, 1)], null, null, 12),
     mk(902, "full", "new", "Ольга", "+79265551234", [pick("matras-briz", 140, 200, 1)], { method: "courier", city: "Москва", street: "Ленинский проспект, д 45", floor: "5", flat: "42", lift: true }, "cash", 55),
     mk(903, "full", "draft", "", "+79157002020", [pick("matras-zevs", 180, 200, 1)], null, null, 130)].forEach((o) => (all[o.id] = o));
    ls.set("tmvo_mock_orders", all);
  }

  if (ss.get("tmvo_admin")) main(); else loginView();
})();
