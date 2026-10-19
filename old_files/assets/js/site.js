/*
 * Торбеевские матрасы — общий скрипт всех страниц.
 * Страница сообщает о себе атрибутом <body data-page="..."> и data-pid (страница товара).
 * window.TMVO_ROOT — относительный путь к корню сайта (задаётся в каждой странице).
 */
(function () {
  const CFG = window.TMVO_CONFIG, API = window.TMVO_API, SHOP = CFG.shop, CAT = window.CATALOG, P = window.TMVO_PRICE;
  const ROOT = window.TMVO_ROOT || "";
  const PAGE = document.body.dataset.page;
  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const rub = (n) => Math.round(n).toLocaleString("ru-RU").replace(/ |,/g, " ") + " ₽";
  const url = (path) => ROOT + path + "index.html";
  const ls = {
    get(k, d) { try { const v = localStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* хранилище недоступно */ } }
  };
  const ss = {
    get(k, d) { try { const v = sessionStorage.getItem(k); return v ? JSON.parse(v) : d; } catch (e) { return d; } },
    set(k, v) { try { sessionStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* хранилище недоступно */ } },
    del(k) { try { sessionStorage.removeItem(k); } catch (e) { /* хранилище недоступно */ } }
  };
  const byId = (id) => CAT.products.find((p) => p.id === id);
  const variant = (p, w, l) => p.variants.find((v) => v.w === +w && v.l === +l);
  const fullName = (p) => (p.word && p.category !== "detskie-namatrasniki" ? p.word + " " : "") + p.name;
  const fmtDate = (d) => d.toLocaleDateString("ru-RU", { day: "numeric", month: "long" });
  const formatPhone = (p) => { const d = String(p || "").replace(/\D/g, "").slice(-10); return d.length === 10 ? `+7 (${d.slice(0, 3)}) ${d.slice(3, 6)}-${d.slice(6, 8)}-${d.slice(8)}` : p; };
  const plural = (n, a, b, c) => { const m10 = n % 10, m100 = n % 100; return m10 === 1 && m100 !== 11 ? a : m10 >= 2 && m10 <= 4 && (m100 < 10 || m100 >= 20) ? b : c; };
  const minPrice = (p, w) => Math.min(...p.variants.filter((v) => !w || v.w === w).map((v) => P.priceOf(p, v.price).price));

  const I = {
    check: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>',
    heart: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20s-7-4.4-9.2-9A5 5 0 0112 5.6 5 5 0 0121.2 11C19 15.6 12 20 12 20z"/></svg>'
  };

  /* ================= корзина и избранное ================= */
  const Cart = {
    items() { return ls.get("tmvo_cart", []).filter((x) => byId(x.product_id) && variant(byId(x.product_id), x.width, x.length)); },
    save(a) { ls.set("tmvo_cart", a); badges(); },
    add(pid, w, l, qty) {
      const a = Cart.items(); const f = a.find((x) => x.product_id === pid && x.width === w && x.length === l);
      if (f) f.qty = Math.min(20, f.qty + qty); else a.push({ product_id: pid, width: w, length: l, qty });
      Cart.save(a);
    },
    setQty(i, q) { const a = Cart.items(); if (!a[i]) return; a[i].qty = Math.max(1, Math.min(20, q)); Cart.save(a); },
    remove(i) { const a = Cart.items(); a.splice(i, 1); Cart.save(a); },
    clear() { Cart.save([]); },
    count() { return Cart.items().reduce((s, x) => s + x.qty, 0); },
    priced() {
      return Cart.items().map((it) => {
        const p = byId(it.product_id); const v = variant(p, it.width, it.length); const pr = P.priceOf(p, v.price);
        return Object.assign({}, it, { p, price: pr.price, old: pr.old, sum: pr.price * it.qty, oldSum: (pr.old || pr.price) * it.qty });
      });
    },
    total() { return Cart.priced().reduce((s, x) => s + x.sum, 0); }
  };
  const Fav = {
    all() { return ls.get("tmvo_fav", []).filter(byId); },
    has(id) { return Fav.all().includes(id); },
    toggle(id) { const a = Fav.all(); const i = a.indexOf(id); if (i >= 0) a.splice(i, 1); else a.push(id); ls.set("tmvo_fav", a); badges(); return i < 0; }
  };
  function badges() {
    $$(".cart-count").forEach((b) => { const n = Cart.count(); b.textContent = n; b.hidden = !n; });
    $$(".fav-count").forEach((b) => { const n = Fav.all().length; b.textContent = n; b.hidden = !n; });
    $$("[data-fav]").forEach((b) => { const on = Fav.has(b.dataset.fav); b.classList.toggle("on", on); b.setAttribute("aria-pressed", on); });
  }
  function toast(t) { const el = $("#toast"); el.textContent = t; el.classList.add("on"); clearTimeout(toast.t); toast.t = setTimeout(() => el.classList.remove("on"), 2400); }

  /* ================= цены в карточках (скидки зависят от даты) ================= */
  function priceHtml(p, w) {
    const vs = p.variants.filter((v) => !w || v.w === w);
    const base = Math.min(...vs.map((v) => v.price));
    const pr = P.priceOf(p, base);
    const single = p.variants.length === 1;
    const old = pr.old || (p.regular_price && p.regular_price > pr.price ? p.regular_price : null);
    return `${single ? "" : "<small>от</small> "}<b>${rub(pr.price)}</b>${old ? ` <s>${rub(old)}</s>` : ""}`;
  }
  function refreshCards(root) {
    $$("[data-card]", root).forEach((c) => {
      const p = byId(c.dataset.card); if (!p) return;
      const w = c.dataset.w ? +c.dataset.w : 0;
      const pe = $(".price", c); if (pe) pe.innerHTML = priceHtml(p, w);
      const pr = P.priceOf(p, p.min_price);
      let b = $(".promo-tag", c);
      if (pr.pct) { if (!b) { b = document.createElement("span"); b.className = "promo-tag"; $(".pic", c).appendChild(b); } b.textContent = "−" + pr.pct + "%"; }
      else if (b) b.remove();
    });
  }
  function cardHtml(p) {
    const img = p.image ? `<img src="${ROOT + p.image}" alt="${esc(fullName(p))}" loading="lazy">` : `<span class="noimg">${esc(p.name)}</span>`;
    const hard = p.specs && p.specs["Категория: Жёсткость"];
    return `<article class="card" data-card="${p.id}"><a class="pic" href="${url(p.path)}">${p.category === "sale" ? '<span class="sale-tag">Распродажа</span>' : ""}${img}</a>
      <button class="fav-btn" data-fav="${p.id}" aria-label="В избранное">${I.heart}</button>
      <div class="body"><a class="name" href="${url(p.path)}">${esc(fullName(p))}</a>
      <div class="chips">${hard ? `<span class="chip">${esc(hard.replace("Средней жесткости", "Средний").replace("Разносторонний", "Разная жёсткость"))}</span>` : ""}${p.specs && p.specs["Высота матраса"] ? `<span class="chip">${esc(p.specs["Высота матраса"])} см</span>` : ""}</div>
      <div class="price">${priceHtml(p)}</div></div></article>`;
  }

  /* ================= маска телефона, согласия ================= */
  function maskPhone(el) {
    const f = () => {
      let d = el.value.replace(/\D/g, ""); if (d[0] === "8" || d[0] === "7") d = d.slice(1); d = d.slice(0, 10);
      let o = d.length ? "+7 (" + d.slice(0, 3) : "";
      if (d.length > 3) o += ") " + d.slice(3, 6); if (d.length > 6) o += "-" + d.slice(6, 8); if (d.length > 8) o += "-" + d.slice(8, 10);
      el.value = o;
    };
    el.addEventListener("input", f); el.addEventListener("focus", () => { if (!el.value) el.value = "+7 ("; });
    el.addEventListener("blur", () => { if (el.value === "+7 (") el.value = ""; });
  }
  const consentsHtml = () => `
    <label class="cbx"><input type="checkbox" name="privacy"> <span>Соглашаюсь с <a href="${url("politika-konfidentsialnosti/")}" target="_blank">политикой обработки персональных данных</a></span></label>
    <label class="cbx"><input type="checkbox" name="personal_data"> <span>Даю <a href="${url("soglasie-na-obrabotku/")}" target="_blank">согласие на обработку персональных данных</a></span></label>
    <input class="hp" type="text" name="website" tabindex="-1" autocomplete="off" aria-hidden="true">`;
  const consentsOf = (f) => ({ privacy: f.privacy.checked, personal_data: f.personal_data.checked, versions: { privacy: CFG.documents.privacy.version, consent: CFG.documents.consent.version } });
  function guard(form, btn, extra) {
    const upd = () => { btn.disabled = !(API.normPhone(form.phone.value) && form.privacy.checked && form.personal_data.checked && (!extra || extra())); };
    form.addEventListener("input", upd); form.addEventListener("change", upd); upd();
  }

  /* ================= модальные окна ================= */
  let lastFocus = null;
  function openModal(html) {
    lastFocus = document.activeElement;
    $("#dlg").innerHTML = `<button class="x" data-close aria-label="Закрыть">×</button>` + html;
    $("#modal").classList.add("on"); document.body.style.overflow = "hidden";
    const f = $("#dlg input:not(.hp)"); if (f) setTimeout(() => f.focus(), 30);
  }
  function closeModal() { $("#modal").classList.remove("on"); document.body.style.overflow = ""; if (lastFocus && lastFocus.focus) lastFocus.focus(); }
  const done = (title, text) => `<button class="x" data-close aria-label="Закрыть">×</button><div class="done"><div class="okmark">${I.check}</div><h3 id="modal-title">${title}</h3><p class="muted">${text}</p><button class="btn block" data-close>Продолжить покупки</button></div>`;

  function quickOrder(items, source) {
    const lines = items.map((it) => { const p = byId(it.product_id); const v = variant(p, it.width, it.length); const pr = P.priceOf(p, v.price); return { p, it, sum: pr.price * it.qty }; });
    const total = lines.reduce((s, x) => s + x.sum, 0);
    openModal(`<h3 id="modal-title">Быстрый заказ</h3><p class="muted">Оставьте телефон — менеджер перезвонит, уточнит доставку и оплату.</p>
      ${lines.slice(0, 3).map((x) => `<div class="mini"><div class="pic">${x.p.image ? `<img src="${ROOT + x.p.image}" alt="">` : ""}</div><div><b>${esc(fullName(x.p))}</b><div class="muted">${x.it.width}×${x.it.length} см, ${x.it.qty} шт</div><b>${rub(x.sum)}</b></div></div>`).join("")}
      ${lines.length > 3 ? `<p class="muted">и ещё ${lines.length - 3} поз. — итого ${rub(total)}</p>` : ""}
      <form id="qform" novalidate>
        <div class="field"><label for="qphone">Телефон <span class="req">*</span></label><input class="inp" id="qphone" name="phone" type="tel" inputmode="tel" autocomplete="tel" placeholder="+7 (___) ___-__-__"></div>
        <div class="field"><label for="qname">Имя <span class="opt">— по желанию</span></label><input class="inp" id="qname" name="name" autocomplete="given-name"></div>
        ${consentsHtml()}<div class="err-msg" id="qerr" role="alert"></div>
        <button class="btn block" id="qbtn">Отправить заявку</button>
        <p class="muted small center">Перезвоним в рабочее время: ${esc(SHOP.workStart)}–${esc(SHOP.workEnd)}</p></form>`);
    const f = $("#qform"), b = $("#qbtn"); maskPhone(f.phone); guard(f, b);
    f.onsubmit = async (e) => {
      e.preventDefault(); if (f.website.value) return; b.disabled = true; b.textContent = "Отправляем…";
      try {
        const o = await API.quickOrder({ phone: f.phone.value, name: f.name.value, items, consents: consentsOf(f), source });
        if (source === "cart") Cart.clear();
        $("#dlg").innerHTML = done(`Заявка № ${o.number} принята`, `Перезвоним на ${esc(formatPhone(o.customer.phone))} в рабочее время, ${esc(SHOP.workStart)}–${esc(SHOP.workEnd)}.`);
        if (source === "cart") setTimeout(() => (location.href = url("")), 2500);
      } catch (err) { $("#qerr").textContent = err.message; b.disabled = false; b.textContent = "Отправить заявку"; }
    };
  }
  function callbackModal(title) {
    openModal(`<h3 id="modal-title">${esc(title || "Заказать звонок")}</h3><p class="muted">Перезвоним, ответим на вопросы и поможем выбрать матрас.</p>
      <form id="cform" novalidate>
        <div class="field"><label for="cphone">Телефон <span class="req">*</span></label><input class="inp" id="cphone" name="phone" type="tel" inputmode="tel" autocomplete="tel" placeholder="+7 (___) ___-__-__"></div>
        <div class="field"><label for="cname">Имя <span class="opt">— по желанию</span></label><input class="inp" id="cname" name="name" autocomplete="given-name"></div>
        ${consentsHtml()}<div class="err-msg" id="cerr" role="alert"></div>
        <button class="btn block" id="cbtn">Перезвоните мне</button></form>`);
    const f = $("#cform"), b = $("#cbtn"); maskPhone(f.phone); guard(f, b);
    f.onsubmit = async (e) => {
      e.preventDefault(); if (f.website.value) return; b.disabled = true;
      try { await API.callback({ phone: f.phone.value, name: f.name.value, consents: consentsOf(f) }); $("#dlg").innerHTML = done("Спасибо! Перезвоним", `В рабочее время, ${esc(SHOP.workStart)}–${esc(SHOP.workEnd)}.`); }
      catch (err) { $("#cerr").textContent = err.message; b.disabled = false; }
    };
  }
  // встроенная форма «Остались вопросы» (на многих страницах)
  function inlineLead(form) {
    const b = $("button", form); maskPhone(form.phone); guard(form, b);
    form.onsubmit = async (e) => {
      e.preventDefault(); if (form.website.value) return; b.disabled = true;
      try { await API.callback({ phone: form.phone.value, name: form.email ? form.email.value : "", consents: consentsOf(form) }); form.innerHTML = `<p class="lead-ok">${I.check} Спасибо! Перезвоним в рабочее время.</p>`; }
      catch (err) { b.disabled = false; toast(err.message); }
    };
  }

  /* ================= страница категории ================= */
  function initCategory() {
    const grid = $("#plist"); if (!grid) return;
    const cards = $$("[data-card]", grid);
    const st = { hard: [], spring: [], w: 0, pmin: "", pmax: "", sort: "pop", promo: false };
    const q = new URLSearchParams(location.search);
    if (q.get("hard")) st.hard = q.get("hard").split(","); if (q.get("w")) st.w = +q.get("w"); if (q.get("promo")) st.promo = true;
    $$("#filters input[data-f]").forEach((i) => { if ((st[i.dataset.f] || []).includes && st[i.dataset.f].includes(i.value)) i.checked = true; });
    $$(".wbtns button").forEach((b) => b.classList.toggle("on", +b.dataset.w === st.w));
    if ($("#fpromo")) $("#fpromo").checked = st.promo;
    const apply = () => {
      let shown = cards.filter((c) => {
        const p = byId(c.dataset.card); const s = p.specs || {};
        if (st.hard.length && !st.hard.includes(s["Категория: Жёсткость"])) return false;
        if (st.spring.length && !st.spring.includes(s["Категория: Пружины"])) return false;
        if (st.w && !p.variants.some((v) => v.w === st.w)) return false;
        if (st.promo && !P.promoActive(p)) return false;
        const pr = minPrice(p, st.w);
        if (st.pmin !== "" && pr < st.pmin) return false;
        if (st.pmax !== "" && pr > st.pmax) return false;
        return true;
      });
      cards.forEach((c) => { c.hidden = !shown.includes(c); c.dataset.w = st.w || ""; $$("a", c).forEach((a) => { const base = a.getAttribute("href").split("?")[0]; a.setAttribute("href", st.w ? base + "?w=" + st.w : base); }); });
      const key = { asc: (p) => minPrice(p, st.w), desc: (p) => -minPrice(p, st.w), name: (p) => p.name, pop: null }[st.sort];
      const ordered = key ? shown.slice().sort((a, b) => { const x = key(byId(a.dataset.card)), y = key(byId(b.dataset.card)); return x < y ? -1 : x > y ? 1 : 0; }) : cards.filter((c) => shown.includes(c));
      ordered.forEach((c) => grid.appendChild(c));
      refreshCards(grid);
      $("#fcount").textContent = `${shown.length} ${plural(shown.length, "модель", "модели", "моделей")}`;
      $("#fempty").hidden = !!shown.length;
    };
    const reset = () => { st.hard = []; st.spring = []; st.w = 0; st.pmin = ""; st.pmax = ""; st.promo = false; $$("#filters input[type=checkbox]").forEach((i) => (i.checked = false)); $$(".wbtns button").forEach((b) => b.classList.remove("on")); $("#pmin").value = ""; $("#pmax").value = ""; apply(); };
    $$("#filters input[data-f]").forEach((i) => (i.onchange = () => { const k = i.dataset.f; st[k] = $$(`#filters input[data-f=${k}]:checked`).map((x) => x.value); apply(); }));
    if ($("#fpromo")) $("#fpromo").onchange = (e) => { st.promo = e.target.checked; apply(); };
    $$(".wbtns button").forEach((b) => (b.onclick = () => { st.w = st.w === +b.dataset.w ? 0 : +b.dataset.w; $$(".wbtns button").forEach((x) => x.classList.toggle("on", +x.dataset.w === st.w)); apply(); }));
    $("#pmin").oninput = (e) => { st.pmin = e.target.value === "" ? "" : +e.target.value; apply(); };
    $("#pmax").oninput = (e) => { st.pmax = e.target.value === "" ? "" : +e.target.value; apply(); };
    $("#sort").onchange = (e) => { st.sort = e.target.value; apply(); };
    $$(".freset").forEach((b) => (b.onclick = reset));
    const fo = (on) => { $("#filters").classList.toggle("on", on); $("#fshade").classList.toggle("on", on); };
    $("#fopen").onclick = () => fo(true); $("#fclose").onclick = () => fo(false); $("#fshade").onclick = () => fo(false);
    apply();
  }

  /* ================= страница товара ================= */
  function initProduct() {
    const p = byId(document.body.dataset.pid); if (!p) return;
    const ws = [...new Set(p.variants.map((v) => v.w))];
    const lens = (w) => [...new Set(p.variants.filter((v) => v.w === w).map((v) => v.l))];
    const q = new URLSearchParams(location.search);
    let w = ws.includes(+q.get("w")) ? +q.get("w") : ws.includes(160) ? 160 : ws[Math.floor(ws.length / 2)];
    let l = lens(w).includes(+q.get("l")) ? +q.get("l") : lens(w).includes(200) ? 200 : lens(w).slice(-1)[0];
    let qty = 1;
    const draw = () => {
      $("#ws").innerHTML = ws.map((x) => `<button type="button" class="${x === w ? "on" : ""}" data-w="${x}" aria-pressed="${x === w}">${x}</button>`).join("");
      const L = lens(w); if (!L.includes(l)) l = L.includes(200) ? 200 : L.slice(-1)[0];
      $("#lsz").innerHTML = L.map((x) => `<button type="button" class="${x === l ? "on" : ""}" data-l="${x}" aria-pressed="${x === l}">${x}</button>`).join("");
      const v = variant(p, w, l); const pr = P.priceOf(p, v.price);
      const old = pr.old || (p.regular_price && p.regular_price > pr.price ? p.regular_price : null);
      $("#price").innerHTML = `${rub(pr.price * qty)}${old ? ` <s>${rub(old * qty)}</s>` : ""}`;
      $("#promo").innerHTML = pr.pct ? `<span class="promo-pill">Скидка ${pr.pct}%</span> до ${fmtDate(pr.until)} включительно` : "";
      $("#promo").hidden = !pr.pct;
      $("#sizeTxt").textContent = `Размер ${w}×${l} см${qty > 1 ? `, ${qty} шт по ${rub(pr.price)}` : ""}`;
      $("#qv").textContent = qty;
      $$("#ws button").forEach((b) => (b.onclick = () => { w = +b.dataset.w; draw(); }));
      $$("#lsz button").forEach((b) => (b.onclick = () => { l = +b.dataset.l; draw(); }));
      try { history.replaceState(null, "", "?w=" + w + "&l=" + l); } catch (e) { /* file:// */ }
    };
    $("#qm").onclick = () => { qty = Math.max(1, qty - 1); draw(); };
    $("#qp").onclick = () => { qty = Math.min(20, qty + 1); draw(); };
    $("#add").onclick = () => { Cart.add(p.id, w, l, qty); toast(`Добавлено в корзину: ${p.name} ${w}×${l}`); $("#add").textContent = "Добавлено ✓"; setTimeout(() => ($("#add").textContent = "В корзину"), 1600); };
    $("#quick").onclick = () => quickOrder([{ product_id: p.id, width: w, length: l, qty }], "product");
    draw();
    // фото: увеличение
    const g = $(".pp-gal img"); if (g) g.onclick = () => openModal(`<img src="${g.src}" alt="${esc(g.alt)}" class="zoom">`);
  }

  /* ================= корзина ================= */
  function initCart() {
    const box = $("#cart");
    const render = () => {
      const items = Cart.priced();
      if (!items.length) { box.innerHTML = `<div class="empty">Корзина пуста. <a class="link" href="${url("matrasy/")}">Перейти в каталог</a></div>`; return; }
      const total = Cart.total(), oldTotal = items.reduce((s, x) => s + x.oldSum, 0);
      box.innerHTML = `<div class="cart"><div>${items.map((x, i) => `<div class="citem"><a class="pic" href="${url(x.p.path)}?w=${x.width}&l=${x.length}">${x.p.image ? `<img src="${ROOT + x.p.image}" alt="">` : `<span class="noimg">${esc(x.p.name)}</span>`}</a>
          <div><a class="name" href="${url(x.p.path)}?w=${x.width}&l=${x.length}">${esc(fullName(x.p))}</a><div class="muted">${x.width}×${x.length} см · ${rub(x.price)}${x.old ? ` <s>${rub(x.old)}</s>` : ""}</div></div>
          <div class="r"><div class="qty"><button data-qm="${i}" aria-label="Меньше">−</button><span>${x.qty}</span><button data-qp="${i}" aria-label="Больше">+</button></div><b>${rub(x.sum)}</b><button class="del" data-del="${i}">Удалить</button></div></div>`).join("")}</div>
        <aside class="summary"><div class="sum-row"><span>Товары, ${Cart.count()} шт</span><span>${rub(oldTotal)}</span></div>
          ${oldTotal > total ? `<div class="sum-row good"><span>Скидка</span><span>−${rub(oldTotal - total)}</span></div>` : ""}
          <div class="sum-row"><span>Доставка</span><span class="muted">рассчитает менеджер</span></div>
          <div class="sum-row t"><span>Итого</span><span>${rub(total)}</span></div>
          <p class="how">Как оформить?</p>
          <label class="choice"><input type="radio" name="how" value="quick"><b>Быстро</b><small>Только телефон. Менеджер перезвонит и всё уточнит.</small></label>
          <label class="choice"><input type="radio" name="how" value="full" checked><b>Полностью</b><small>Сами укажете адрес и способ оплаты. Около 2 минут.</small></label>
          <button class="btn block" id="go">Оформить заказ</button></aside></div>`;
      $$("[data-qm]").forEach((b) => (b.onclick = () => { const i = +b.dataset.qm; Cart.setQty(i, Cart.items()[i].qty - 1); render(); }));
      $$("[data-qp]").forEach((b) => (b.onclick = () => { const i = +b.dataset.qp; Cart.setQty(i, Cart.items()[i].qty + 1); render(); }));
      $$("[data-del]").forEach((b) => (b.onclick = () => { Cart.remove(+b.dataset.del); render(); }));
      $("#go").onclick = () => { if ($("input[name=how]:checked").value === "quick") quickOrder(Cart.items(), "cart"); else location.href = url("oformlenie/"); };
    };
    render();
  }

  /* ================= оформление заказа ================= */
  const CO_KEY = "tmvo_checkout";
  const STEPS = ["Контакты", "Получатель", "Получение", "Оплата", "Проверка"];
  function initCheckout() {
    const main = $("#co"), side = $("#co-sum");
    if (!Cart.items().length) { $("#co-wrap").innerHTML = `<div class="empty">Корзина пуста. <a class="link" href="${url("matrasy/")}">Перейти в каталог</a></div>`; return; }
    const S = ss.get(CO_KEY, { step: 0, id: null, token: null, d: {} });
    const D = Object.assign({ phone: "", name: "", email: "", comment: "", delivery: (CFG.delivery.find((x) => x.enabled) || {}).id, city: "Москва", street: "", floor: "", flat: "", lift: false, payment: (CFG.payment.find((x) => x.enabled) || {}).id }, S.d);
    const save = () => { S.d = D; ss.set(CO_KEY, S); };
    side.innerHTML = Cart.priced().map((x) => `<div class="sum-row small"><span>${esc(fullName(x.p))}, ${x.width}×${x.length}${x.qty > 1 ? " × " + x.qty : ""}</span><span class="nowrap">${rub(x.sum)}</span></div>`).join("") +
      `<div class="sum-row small"><span>Доставка</span><span class="muted">рассчитает менеджер</span></div><div class="sum-row t"><span>Итого</span><span>${rub(Cart.total())}</span></div><a class="link small" href="${url("korzina/")}">Изменить корзину</a>`;
    const head = (i) => `<div class="co-steps">${STEPS.map((_, k) => `<i class="${k <= i ? "on" : ""}"></i>`).join("")}</div><div class="co-lbl">Шаг ${i + 1} из ${STEPS.length}: ${STEPS[i].toLowerCase()}</div>`;
    const nav = (back) => `<div class="err-msg" id="coerr" role="alert"></div><div class="co-nav">${back !== undefined ? `<button type="button" class="link" data-step="${back}">← Назад</button>` : "<span></span>"}<button class="btn" id="next">Продолжить</button></div>`;
    const patch = (body) => API.updateOrder(S.id, S.token, Object.assign({ items: Cart.items() }, body));
    const fail = (err) => { const e = $("#coerr"); if (e) e.textContent = err.message || "Ошибка, попробуйте ещё раз"; $$("#co button.btn").forEach((b) => (b.disabled = false)); };
    function draw() {
      const i = S.step;
      if (i === 0) {
        main.innerHTML = `${head(0)}<form id="f" novalidate><h2>Контактный телефон</h2><p class="muted">Без регистрации и SMS-кода. По этому номеру менеджер подтвердит заказ.</p>
          <div class="field"><label for="phone">Телефон <span class="req">*</span></label><input class="inp" id="phone" name="phone" type="tel" inputmode="tel" autocomplete="tel" placeholder="+7 (___) ___-__-__" value="${esc(D.phone)}"></div>
          ${consentsHtml()}${nav()}</form>`;
        const f = $("#f"); maskPhone(f.phone); if (S.id) { f.privacy.checked = true; f.personal_data.checked = true; } guard(f, $("#next"));
        f.onsubmit = async (e) => { e.preventDefault(); if (f.website.value) return; $("#next").disabled = true; D.phone = f.phone.value;
          try { if (!S.id) { const o = await API.createDraft({ phone: D.phone, items: Cart.items(), consents: consentsOf(f), source: "checkout" }); S.id = o.id; S.token = o.token; } else await patch({ phone: D.phone }); S.step = 1; save(); draw(); } catch (err) { fail(err); } };
      }
      if (i === 1) {
        main.innerHTML = `${head(1)}<form id="f" novalidate><h2>Получатель</h2>
          <div class="field"><label>Телефон</label><div class="row-inline"><input class="inp" value="${esc(D.phone)}" readonly aria-label="Телефон"><button type="button" class="link" data-step="0">Изменить</button></div></div>
          <div class="field"><label for="name">Имя <span class="req">*</span></label><input class="inp" id="name" name="name" autocomplete="given-name" value="${esc(D.name)}"></div>
          <div class="field"><label for="email">E-mail <span class="opt">— по желанию, пришлём копию заказа</span></label><input class="inp" id="email" name="email" type="email" autocomplete="email" value="${esc(D.email)}"></div>
          <div class="field"><label for="comment">Комментарий <span class="opt">— по желанию</span></label><textarea class="inp" id="comment" name="comment" placeholder="Например: позвоните после 18:00">${esc(D.comment)}</textarea></div>${nav(0)}</form>`;
        const f = $("#f"), b = $("#next"); const upd = () => { const em = f.email.value.trim(); b.disabled = f.name.value.trim().length < 2 || (em && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(em)); }; f.oninput = upd; upd();
        f.onsubmit = async (e) => { e.preventDefault(); b.disabled = true; D.name = f.name.value.trim(); D.email = f.email.value.trim(); D.comment = f.comment.value.trim();
          try { await patch({ name: D.name, email: D.email, comment: D.comment }); S.step = 2; save(); draw(); } catch (err) { fail(err); } };
      }
      if (i === 2) {
        const ms = CFG.delivery.filter((x) => x.enabled);
        main.innerHTML = `${head(2)}<form id="f" novalidate><h2>Получение</h2>${ms.map((m) => `<label class="opt-card"><input type="radio" name="dm" value="${m.id}" ${D.delivery === m.id ? "checked" : ""}><span><b>${esc(m.title)}</b><small>${esc(m.note)}</small></span></label>`).join("")}<div id="addr"></div>${nav(1)}</form>`;
        const f = $("#f"), b = $("#next");
        const upd = () => { b.disabled = D.delivery === "courier" && (!f.city || f.city.value.trim().length < 2 || f.street.value.trim().length < 5); };
        const drawAddr = () => {
          $("#addr").innerHTML = D.delivery === "courier" ? `<div class="field"><label for="city">Город или населённый пункт <span class="req">*</span></label><input class="inp" id="city" name="city" autocomplete="address-level2" value="${esc(D.city)}"></div>
            <div class="field"><label for="street">Улица и дом <span class="req">*</span></label><input class="inp" id="street" name="street" autocomplete="street-address" placeholder="Например: Ленинский проспект, д 45" value="${esc(D.street)}"></div>
            <div class="row2"><div class="field"><label for="floor">Этаж</label><input class="inp" id="floor" name="floor" inputmode="numeric" value="${esc(D.floor)}"></div><div class="field"><label for="flat">Квартира / офис</label><input class="inp" id="flat" name="flat" value="${esc(D.flat)}"></div></div>
            <label class="cbx"><input type="checkbox" name="lift" ${D.lift ? "checked" : ""}> <span>В доме есть грузовой лифт</span></label>` : `<p class="muted">Шоурум: ${esc(SHOP.address)}. Менеджер согласует время, когда заказ будет готов.</p>`;
          upd();
        };
        $$("input[name=dm]", f).forEach((r) => (r.onchange = () => { D.delivery = r.value; drawAddr(); })); f.oninput = upd; drawAddr();
        f.onsubmit = async (e) => { e.preventDefault(); b.disabled = true;
          if (D.delivery === "courier") { D.city = f.city.value.trim(); D.street = f.street.value.trim(); D.floor = f.floor.value.trim(); D.flat = f.flat.value.trim(); D.lift = f.lift.checked; }
          try { await patch({ delivery: D.delivery === "courier" ? { method: "courier", city: D.city, street: D.street, floor: D.floor, flat: D.flat, lift: D.lift } : { method: D.delivery } }); S.step = 3; save(); draw(); } catch (err) { fail(err); } };
      }
      if (i === 3) {
        const pm = CFG.payment.filter((x) => x.enabled); const gs = [...new Set(pm.map((x) => x.group))];
        if (!pm.find((x) => x.id === D.payment)) D.payment = pm[0] && pm[0].id;
        main.innerHTML = `${head(3)}<form id="f" novalidate><h2>Способ оплаты</h2>${gs.map((g) => `<div class="grp-l">${esc(g)}</div>${pm.filter((x) => x.group === g).map((m) => `<label class="opt-card"><input type="radio" name="pm" value="${m.id}" ${D.payment === m.id ? "checked" : ""}><span><b>${esc(m.title)}</b><small>${esc(m.note)}</small></span></label>`).join("")}`).join("")}${nav(2)}</form>`;
        const f = $("#f"); f.onsubmit = async (e) => { e.preventDefault(); $("#next").disabled = true; D.payment = f.pm.value; try { await patch({ payment_method: D.payment }); S.step = 4; save(); draw(); } catch (err) { fail(err); } };
      }
      if (i === 4) {
        const m = CFG.payment.find((x) => x.id === D.payment) || {}; const dm = CFG.delivery.find((x) => x.id === D.delivery) || {};
        const addr = D.delivery === "courier" ? `${D.city}, ${D.street}${D.flat ? ", кв./офис " + D.flat : ""}${D.floor ? ", этаж " + D.floor : ""}${D.lift ? ", есть грузовой лифт" : ""}` : SHOP.address;
        const rv = (h, v, s) => `<div class="rv"><div class="h"><span>${h}</span><button type="button" class="link" data-step="${s}">Изменить</button></div><div class="v">${v}</div></div>`;
        main.innerHTML = `${head(4)}<form id="f" novalidate><h2>Проверьте заказ</h2>
          ${rv("Телефон", esc(D.phone), 0)}${rv("Получатель", esc(D.name) + (D.email ? `<br><span class="muted">${esc(D.email)}</span>` : "") + (D.comment ? `<br><span class="muted">${esc(D.comment)}</span>` : ""), 1)}
          ${rv(esc(dm.title || "Получение"), esc(addr), 2)}${rv("Оплата", esc(m.title || ""), 3)}
          <label class="cbx"><input type="checkbox" name="offer"> <span>Принимаю условия <a href="${url("oferta/")}" target="_blank">публичной оферты</a></span></label>
          <label class="cbx"><input type="checkbox" name="marketing"> <span>Хочу получать новости и скидки <span class="muted">(по желанию)</span></span></label>
          <div class="err-msg" id="coerr" role="alert"></div>
          <div class="co-nav"><button type="button" class="link" data-step="3">← Назад</button><button class="btn" id="next" disabled>${m.online ? "Подтвердить и перейти к оплате" : "Подтвердить заказ"}</button></div></form>`;
        const f = $("#f"), b = $("#next"); f.onchange = () => (b.disabled = !f.offer.checked);
        f.onsubmit = async (e) => { e.preventDefault(); b.disabled = true; b.textContent = "Отправляем…";
          try {
            const o = await API.confirmOrder(S.id, S.token, { offer_accepted: true, marketing: f.marketing.checked });
            Cart.clear(); ss.del(CO_KEY);
            if (m.online) { const pay = await API.createPayment(o.id, o.token, { method: m.id }); location.href = pay.confirmation_url; return; }
            location.href = url("zakaz/") + "?id=" + encodeURIComponent(o.id) + "&t=" + encodeURIComponent(o.token) + "&new=1";
          } catch (err) { fail(err); b.textContent = m.online ? "Подтвердить и перейти к оплате" : "Подтвердить заказ"; }
        };
      }
      $$("#co [data-step]").forEach((x) => (x.onclick = () => { S.step = +x.dataset.step; save(); draw(); }));
      const h = $("#co h2"); if (h && draw.started) { h.setAttribute("tabindex", "-1"); h.focus({ preventScroll: true }); main.scrollIntoView({ block: "nearest" }); }
      draw.started = true;
    }
    draw();
  }

  /* ================= страница заказа ================= */
  const STATUS = { draft: "Оформление не завершено", new: "Принят", in_work: "В работе", awaiting_payment: "Ожидает оплаты", paid: "Оплачен", delivery: "В доставке", done: "Выполнен", canceled: "Отменён" };
  async function initOrder() {
    const el = $("#ord"); const q = new URLSearchParams(location.search);
    try {
      const o = await API.getOrder(q.get("id"), q.get("t"));
      const pm = CFG.payment.find((x) => x.id === o.payment.method) || {}; const d = o.delivery || {};
      const addr = d.method === "courier" ? `${d.city}, ${d.street}${d.flat ? ", кв./офис " + d.flat : ""}${d.floor ? ", этаж " + d.floor : ""}` : d.method === "pickup" ? "Самовывоз: " + SHOP.address : "Уточнит менеджер";
      el.innerHTML = `${q.get("new") ? `<div class="okmark">${I.check}</div><h1>Спасибо! Заказ № ${o.number} принят</h1><p class="muted lead">Менеджер позвонит на ${esc(formatPhone(o.customer.phone))}, чтобы подтвердить заказ и согласовать ${d.method === "pickup" ? "самовывоз" : "доставку"}. Рабочее время: ${esc(SHOP.workStart)}–${esc(SHOP.workEnd)}.</p>` : `<h1>Заказ № ${o.number}</h1>`}
        <p><span class="status st-${o.status}">${STATUS[o.status] || o.status}</span></p>
        <div class="box"><h3>Состав заказа</h3>${o.items.map((x) => { const p = byId(x.product_id); return `<div class="sum-row"><span>${esc(p ? fullName(p) : x.name)}, ${x.width}×${x.length} × ${x.qty}</span><span>${rub(x.sum)}</span></div>`; }).join("")}<div class="sum-row t"><span>Итого</span><span>${rub(o.total)}</span></div></div>
        <div class="box"><h3>Получение</h3><p>${esc(addr)}</p></div>
        <div class="box"><h3>Оплата</h3><p>${esc(pm.title || "Уточнит менеджер")} — ${o.payment.status === "paid" ? "оплачено" : pm.online ? "не оплачено" : "при получении"}</p>
          ${pm.online && o.payment.status !== "paid" && o.status === "awaiting_payment" ? `<button class="btn" id="pay">Оплатить ${rub(o.total)}</button>` : ""}</div>
        <p class="muted">Сохраните ссылку на эту страницу, чтобы следить за статусом. Вопросы: ${esc(SHOP.phone)}.</p><a class="btn ghost" href="${url("")}">На главную</a>`;
      const pb = $("#pay"); if (pb) pb.onclick = async () => { pb.disabled = true; const r = await API.createPayment(o.id, q.get("t"), { method: o.payment.method }); location.href = r.confirmation_url; };
    } catch (err) { el.innerHTML = `<h1>Заказ не найден</h1><p class="muted">Проверьте ссылку или позвоните нам: ${esc(SHOP.phone)}.</p>`; }
  }

  /* ================= поиск и избранное ================= */
  function initSearch() {
    const q = (new URLSearchParams(location.search).get("q") || "").trim();
    $("#sq").value = q; $("#stitle").textContent = q ? `Поиск: «${q}»` : "Поиск";
    const s = q.toLowerCase().replace(/ё/g, "е");
    const list = s ? CAT.products.filter((p) => (fullName(p) + " " + (p.specs["Состав слоев матраса / наполнители"] || "")).toLowerCase().replace(/ё/g, "е").includes(s)) : [];
    $("#sres").innerHTML = list.length ? list.map(cardHtml).join("") : `<div class="empty wide">${q ? "Ничего не нашлось." : "Введите название модели или наполнитель, например «латекс»."} <a class="link" href="${url("matrasy/")}">Открыть каталог</a></div>`;
    badges();
  }
  function initFav() {
    const list = Fav.all().map(byId);
    $("#fres").innerHTML = list.length ? list.map(cardHtml).join("") : `<div class="empty wide">В избранном пока ничего нет. Нажмите ♡ на карточке товара, чтобы сохранить его здесь.</div>`;
    badges();
  }

  /* ================= общие обработчики ================= */
  document.addEventListener("click", (e) => {
    const t = e.target;
    if (t.closest("[data-close]")) { closeModal(); return; }
    const cb = t.closest("[data-callback]"); if (cb) { e.preventDefault(); callbackModal(cb.dataset.callback); return; }
    const fv = t.closest("[data-fav]"); if (fv) { e.preventDefault(); const on = Fav.toggle(fv.dataset.fav); toast(on ? "Добавлено в избранное" : "Убрано из избранного"); if (PAGE === "favorites") initFav(); return; }
    if (t.closest("#burger")) { $("#drawer").classList.add("on"); return; }
    if (t.closest("[data-drawer-close]")) $("#drawer").classList.remove("on");
    const cat = t.closest("#catbtn"); if (cat) { const m = $("#megamenu"); const on = m.hidden; m.hidden = !on; cat.setAttribute("aria-expanded", on); return; }
    if (!t.closest("#megamenu")) { const m = $("#megamenu"); if (m && !m.hidden) { m.hidden = true; $("#catbtn").setAttribute("aria-expanded", "false"); } }
  });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") { closeModal(); $("#drawer").classList.remove("on"); const m = $("#megamenu"); if (m) m.hidden = true; } });
  window.addEventListener("storage", (e) => { if (e.key === "tmvo_cart" || e.key === "tmvo_fav") badges(); });

  if (CFG.apiMode === "mock") { const d = $("#demo"); if (d) d.hidden = false; }
  if (!ls.get("tmvo_cookie_ok", false)) {
    const c = document.createElement("div"); c.className = "cookie";
    c.innerHTML = `<span>Сайт использует файлы cookie для работы корзины и статистики. <a href="${url("politika-konfidentsialnosti/")}">Подробнее</a></span><button class="btn sm">Понятно</button>`;
    c.querySelector("button").onclick = () => { ls.set("tmvo_cookie_ok", true); c.remove(); };
    document.body.appendChild(c);
  }
  $$("form.lead-form").forEach(inlineLead);
  refreshCards(document);
  badges();
  ({ category: initCategory, product: initProduct, cart: initCart, checkout: initCheckout, order: initOrder, search: initSearch, favorites: initFav }[PAGE] || (() => {}))();
})();
