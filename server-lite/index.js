/*
 * Этап 1 «без базы»: функция-посредник между сайтом и Telegram менеджеров.
 * Платформа: Yandex Cloud Functions (среда Node.js 18+) — серверы в России.
 * Подходит и для любого другого хостинга функций: нужна точка входа handler(event).
 *
 * Переменные окружения функции:
 *   BOT_TOKEN       — токен бота от @BotFather
 *   CHAT_ID         — id чата/группы менеджеров (бот должен быть добавлен в группу)
 *   ALLOWED_ORIGIN  — адрес сайта, например https://tmvo.ru (или https://<логин>.github.io)
 *
 * Сайт: в assets/js/config.js поставить apiMode: "lite" и liteEndpoint: "<адрес функции>".
 */
const STATUS_TEXT = { quick_order: "🟠 Быстрый заказ", order: "🟢 Новый заказ", lead: "⚪ Начато оформление (есть телефон)", callback: "📞 Заказать звонок" };

function cors(origin) {
  const allowed = process.env.ALLOWED_ORIGIN || "*";
  return { "Access-Control-Allow-Origin": allowed === "*" ? "*" : (origin === allowed ? origin : allowed),
           "Access-Control-Allow-Methods": "POST, OPTIONS", "Access-Control-Allow-Headers": "Content-Type", "Content-Type": "application/json; charset=utf-8" };
}
const rub = (n) => Math.round(n || 0).toLocaleString("ru-RU") + " ₽";
const phone = (p) => { const d = String(p || "").replace(/\D/g, "").slice(-10); return d.length === 10 ? `+7 (${d.slice(0, 3)}) ${d.slice(3, 6)}-${d.slice(6, 8)}-${d.slice(8)}` : null; };
const clip = (s, n) => String(s || "").replace(/[<>]/g, "").slice(0, n);

function format(b) {
  const head = STATUS_TEXT[b.event] || "Заявка с сайта";
  if (b.event === "callback") {
    return `${head}\nТелефон: ${phone(b.phone)}\n${b.name ? "Имя: " + clip(b.name, 100) + "\n" : ""}Тема: ${clip(b.topic || "звонок", 100)}\nСогласие на обработку ПДн: да`;
  }
  const o = b.order || {}; const c = o.customer || {}; const d = o.delivery || {};
  const items = (o.items || []).slice(0, 20).map((x) => `• ${clip(x.name, 60)} ${x.width}×${x.length} × ${x.qty} — ${rub(x.sum)}`).join("\n");
  const addr = d.method === "courier" ? `Доставка: ${clip(d.city, 80)}, ${clip(d.street, 150)}${d.flat ? ", кв. " + clip(d.flat, 10) : ""}${d.floor ? ", эт. " + clip(d.floor, 5) : ""}${d.lift ? ", лифт" : ""}`
             : d.method === "pickup" ? "Самовывоз из шоурума" : "Получение: уточнить";
  return [`${head} № ${o.number || "—"}`, `Телефон: ${phone(c.phone)}`, c.name ? `Имя: ${clip(c.name, 100)}` : "", c.email ? `E-mail: ${clip(c.email, 100)}` : "",
          items, `Итого по ценам сайта: ${rub(o.total)} (проверить по прайсу)`, b.event === "order" ? addr : "", b.event === "order" && o.payment ? `Оплата: ${clip(o.payment.method, 30)}` : "",
          c.comment ? `Комментарий: ${clip(c.comment, 500)}` : "", "Согласие на обработку ПДн: да"].filter(Boolean).join("\n");
}

module.exports.handler = async function (event) {
  const origin = (event.headers || {}).Origin || (event.headers || {}).origin || "";
  if (event.httpMethod === "OPTIONS") return { statusCode: 204, headers: cors(origin), body: "" };
  let b; try { b = JSON.parse(event.isBase64Encoded ? Buffer.from(event.body, "base64").toString("utf8") : event.body || "{}"); } catch (e) { return { statusCode: 400, headers: cors(origin), body: '{"error":"bad_json"}' }; }
  const ph = b.event === "callback" ? b.phone : ((b.order || {}).customer || {}).phone;
  if (!STATUS_TEXT[b.event] || !phone(ph)) return { statusCode: 400, headers: cors(origin), body: '{"error":"bad_request"}' };
  const r = await fetch(`https://api.telegram.org/bot${process.env.BOT_TOKEN}/sendMessage`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ chat_id: process.env.CHAT_ID, text: format(b), disable_web_page_preview: true })
  });
  if (!r.ok) return { statusCode: 502, headers: cors(origin), body: '{"error":"telegram_failed"}' };
  return { statusCode: 200, headers: cors(origin), body: '{"ok":true}' };
};
